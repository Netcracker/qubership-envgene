from typing import Optional, Dict, List, Any
from models import PayloadEntry, RotationResult, ParameterReference, CredMap
from utils.search_utils import get_ns_content, get_app_content, resolve_param, search_yaml_files
from utils.cred_utils import extract_credential
from utils.error_constants import  *
import envgenehelper.logger as logger
from envgenehelper.errors import ValidationError, ReferenceError

def process_entry_in_payload(
    entry: PayloadEntry,
    env: str,
    cluster_name: str,
    shared_cred_content: Dict[str, Any],
    env_cred_content: Dict[str, Any],
    entity_files_map: Dict[str, Dict[str, Any]],
    processed_cred_and_files: Dict[str, List[CredMap]]
) -> Optional[RotationResult]:

    if entry.application and entry.context == "pipeline":
        raise ValidationError(ErrorMessages.INVALID_CONTEXT.format(param_key=entry.parameter_key), error_code=ErrorCodes.INVALID_INPUT_CODE)


    logger.info(f"Processing namespace={entry.namespace}, application={entry.application}, param_key={entry.parameter_key}, context={entry.context}")
    #Get target application or namespace file
    if entry.application:
        target = get_app_content(entity_files_map, entry.namespace, entry.application, env)
    else:
        target = get_ns_content(entity_files_map, entry.namespace, env)

    if not target:
        raise ReferenceError(ErrorMessages.ENTITY_FILE_NOT_FOUND.format(param_key=entry.parameter_key), error_code=ErrorCodes.FILE_NOT_FOUND_CODE)

    target_file, target_yaml = target
    param_type = resolve_param(entry.context)
    if param_type not in target_yaml:
        raise ValidationError(ErrorMessages.MISSING_CONTEXT.format(context=entry.context, target_file=target_file, param_key=entry.parameter_key), error_code=ErrorCodes.INVALID_INPUT_CODE)

    sub_content = target_yaml[param_type]
    value_to_search, cred_id, cred_field = extract_credential(entry.parameter_key, sub_content)

    if cred_field not in {"username", "password", "secret"}:
        raise ValidationError(ErrorMessages.INVALID_CRED_FIELD.format(cred_field=entry.credential_field), ErrorCodes.INVALID_CONFIG_CODE)

    if not value_to_search or not cred_id:
        raise ReferenceError(ErrorMessages.MISSING_CRED.format(target_file=target_file, context=entry.context), error_code=ErrorCodes.INVALID_INPUT_CODE)


    shared_match_files = [k for k, v in shared_cred_content.items() if cred_id in v]
    env_cred_files = [k for k, v in env_cred_content.items() if cred_id in v]

    #Constructing map for file updation
    all_cred_files = shared_match_files + env_cred_files
    for cred_file in all_cred_files:
        shared_content = shared_cred_content.get(cred_file) or env_cred_content.get(cred_file)
        cred_map = CredMap(
            cred_id=cred_id,
            cred_field=cred_field,
            param_value=entry.parameter_value,
            shared_content=shared_content
        )
        processed_cred_and_files.setdefault(cred_file, []).append(cred_map)

    # Collect affected parameters
    affected = search_yaml_files(
        value_to_search,
        entity_files_map,
        cred_id,
        cluster_name,
        shared_match_files,
        env_cred_files,
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
                cred_field=cred_field
            ),
            affected_parameters=affected
        )
    logger.info(f"No affected parameters found for the given target key {entry.parameter_key}")
    return None