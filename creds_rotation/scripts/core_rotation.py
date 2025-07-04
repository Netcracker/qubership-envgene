from typing import Optional, Dict, List, Any
from models import PayloadEntry, RotationResult, ParameterReference, CredMap
from utils.search_utils import get_ns_content, get_app_content, resolve_param, search_yaml_files
from utils.cred_utils import extract_credential
import envgenehelper.logger as logger


def process_entry_in_payload(
    entry: PayloadEntry,
    env: str,
    shared_cred_content: Dict[str, Any],
    env_cred_content: Dict[str, Any],
    ns_files_map: Dict[str, Dict[str, Any]],
    processed_cred_and_files: Dict[str, List[CredMap]]
) -> Optional[RotationResult]:

    if entry.application and entry.context == "pipeline":
        raise ValueError(f"Invalid context 'pipeline' for  param {entry.parameter_key}")

    logger.info(f"Processing namespace={entry.namespace}, application={entry.application}, param_key={entry.parameter_key}, context={entry.context}")
    #Get target application or namespace file
    if entry.application:
        target = get_app_content(ns_files_map, entry.namespace, entry.application)
    else:
        target = get_ns_content(ns_files_map, entry.namespace)

    if not target:
        raise ValueError(f"ERROR: Target File not found for parameter key {entry.parameter_key}")

    target_file, target_yaml = target
    param_type = resolve_param(entry.context)
    if param_type not in target_yaml:
        raise ValueError(f"Context '{entry.context}' not found in target yaml for key {entry.parameter_key}")

    sub_content = target_yaml[param_type]
    try:
        value_to_search, cred_id = extract_credential(entry.parameter_key, sub_content, entry.credential_field)
    except Exception as e:
        raise Exception(f"ERROR: Failed to extract credential for key {entry.parameter_key}. Error {e}")

    if not value_to_search or not cred_id:
        raise Exception(f"ERROR: credential '{cred_id}' missing in target file")


    shared_match_files = [k for k, v in shared_cred_content.items() if cred_id in v]
    env_cred_file = next((k for k, v in env_cred_content.items() if cred_id in v), "")

    #Constructing map for file updation
    all_cred_files = shared_match_files + ([env_cred_file] if env_cred_file else [])
    for cred_file in all_cred_files:
        shared_content = shared_cred_content.get(cred_file) or env_cred_content.get(cred_file)
        cred_map = CredMap(
            cred_id=cred_id,
            param_value=entry.parameter_value,
            cred_field=entry.credential_field,
            shared_content=shared_content
        )
        processed_cred_and_files.setdefault(cred_file, []).append(cred_map)

    # Collect affected parameters
    affected = search_yaml_files(
        value_to_search,
        ns_files_map,
        cred_id,
        env,
        shared_match_files,
        env_cred_file,
        entry.parameter_key,
        param_type,
        target_file
    )
    logger.info(f"✅ Processed param {entry.parameter_key}, affected count = {len(affected)}")
    if affected:
        return RotationResult(
            target_parameter=ParameterReference(
                environment=env,
                namespace=entry.namespace,
                application=str(entry.application or ""),
                context=entry.context,
                parameter_key=entry.parameter_key,
                cred_field=entry.credential_field
            ),
            affected_parameters=affected
        )
    logger.info(f"No affected parameters found for the given target key {entry.parameter_key}")
    return None