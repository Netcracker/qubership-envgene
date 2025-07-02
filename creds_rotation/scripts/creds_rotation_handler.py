import os
import re
import time
import timeit
import yaml
import asyncio
import aiofiles
import copy

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path, PurePath
from functools import lru_cache
from typing import Any, Dict, List, Optional,  Tuple

from envgenehelper import (
    crypt,
    getenv_with_error,
    openYaml,
    getEnvDefinition,
    dump_as_yaml_format,
    writeYamlToFile
)

try:
    from yaml import CSafeLoader as SafeLoader
except ImportError:
    from yaml import SafeLoader

# Internal modules

import envgenehelper.logger as logger

# Custom dataclasses
from models import (
    PayloadEntry,
    RotationResult,
    ParameterReference,
    CredMap,
    AffectedParameter
)



CONTEXT_MAP = {
    "deployment": "deployParameters",
    "pipeline": "technicalConfigurationParameters", 
    "runtime": "e2eParameters"
}

REVERSE_CONTEXT_MAP = {
    "deployparameters": "deployment",
    "technicalconfigurationparameters": "pipeline",
    "e2eparameters": "runtime"
}
async def read_yaml_file(path: str) -> tuple[str, dict]:
    try:
        async with aiofiles.open(path, mode='r') as f:
            content = await f.read()
        data = yaml.safe_load(content)
        return path, data
    except Exception as e:
        print(f"❌ Failed to read {path}: {e}")
        return path, None


async def load_yaml_files_parallel(paths: List[str]) -> Dict[str, dict]:
    tasks = [read_yaml_file(path) for path in paths]
    results = await asyncio.gather(*tasks)
    return {path: content for path, content in results if content is not None}

def get_app_and_ns(filename: str, content: dict) -> Tuple[str, Optional[str]]:
    if filename.endswith(("namespace.yml", "namespace.yaml")):
        return '', content.get('name', '')
    
    filepath = PurePath(filename)
    parent_dir = filepath.parent.parent
    ns_file_yaml = parent_dir / "namespace.yaml"
    ns_file_yml = parent_dir / "namespace.yml"

    try:
        ns_content = get_content_form_file(ns_file_yml)
    except Exception:
        try:
            ns_content = get_content_form_file(ns_file_yaml)
        except Exception as e:
            raise Exception(f"Failed to load namespace file from {parent_dir}: {e}")
    return content.get('name', ''), ns_content.get('name','')


def get_affected_param_map(
    cred_id: str,
    env: str,
    shared_cred_files: list,
    env_cred_files: list,
    filename: str,
    content: dict,
    matches: dict
) -> list[AffectedParameter]:
    result = []
    app, namespace = get_app_and_ns(filename, content)

    for context, param_keys in matches.items():
        for key in param_keys:
            affected = AffectedParameter(
                environment=env,
                namespace=namespace,
                application=app,
                context=resolve_context(context),
                parameter_key=key,
                cred_filepath=env_cred_files,
                shared_cred_filepath=shared_cred_files,
                cred_id=cred_id
            )
            result.append(affected)

    return result


def find_in_yaml(data: dict, search_pattern: str, is_target: bool, target_key: str, target_context: str) -> Dict[str, List[str]]:
    matches = {}
    for context in CONTEXT_MAP.values():
        params = data.get(context, {})
        if params and search_pattern in str(params):
            affected_params = find_matching_keys(params, search_pattern, is_target, context, target_key, target_context)
            if affected_params:
                matches[context] = affected_params
    return matches

def find_matching_keys(data: dict, search_pattern: str, is_target: bool,
                       context: str, target_key: str, target_context: str) -> list[str]:
    results: List[str] = []

    def recurse(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                recurse(v, path + [k])
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
               if path:
                    base_path = path[:-1]
                    last_key_with_index = f"{path[-1]}[{idx}]"
                    recurse(item, base_path + [last_key_with_index])
               else:
                    recurse(item, [f"[{idx}]"])
        elif isinstance(obj, str) and search_pattern in obj:
            final_key = ".".join(path)
            if  is_target and context == target_context and final_key == target_key:
                logger.debug("skipping target param")
            else:
                results.append(final_key)
    recurse(data, [])
    return results

def extract_credential(target_key: str, yaml_content: Dict[str, Any], cred_field: str) -> Tuple[Optional[str], Optional[str]]:
    pattern  = re.compile(r"\$\{creds\.get\([\"']([^\"']+)[\"']\)\.(" + re.escape(cred_field) + r")\}")
    if  target_key in yaml_content:
         value = yaml_content.get(target_key)
    elif "." in target_key:
        value = get_nested_target_key(yaml_content, target_key)
    else:
        raise KeyError(f"Key '{target_key}' not found in content specified")

    if not isinstance(value, str):
        raise ValueError(f"Expected string but got {type(value)} for target_key: {target_key}")

    match = pattern.search(value)
    if match:
        return match.group(0), match.group(1)
    return None, None

def get_nested_target_key(yaml_data: dict, path: str) -> str:
    current = yaml_data

    for part in path.split('.'):
        key, index = part, None

        if '[' in part:
            match = re.fullmatch(r'(.*?)\[(\d+)\]', part)
            if not match:
                raise ValueError(f"Invalid path segment: {part}")
            key, index = match.group(1), int(match.group(2))

        if not isinstance(current, dict) or key not in current:
            raise KeyError(f"Missing key: {key} in {current}")
        current = current[key]

        if index is not None:
            if not isinstance(current, list):
                raise TypeError(f"Expected list at {key}[{index}], got {type(current)}")
            if index >= len(current):
                raise IndexError(f"Index {index} out of bounds for key: {key}")
            current = current[index]

    return current


@lru_cache(maxsize=None)
def resolve_param(context: str) -> str:
    return CONTEXT_MAP.get(context.lower(), "")

@lru_cache(maxsize=None)
def resolve_context(context: str) -> str:
    return REVERSE_CONTEXT_MAP.get(context.lower(), "")
#############################################################
####change it to ryaml later
def write_yaml_to_file(file_path: str, contents: Any) -> None:
    logger.debug(f"Writing YAML to file: {file_path}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        yaml.safe_dump(contents, f, sort_keys=False)

def resolve_yaml_file(lookup_path: str) -> str | None:
    if lookup_path.exists():
        return str(lookup_path)
    if lookup_path.suffix == '.yml':
        alt_path = lookup_path.with_suffix('.yaml')
        if alt_path and alt_path.exists():
            return str(alt_path)
    return None


def load_entries_from_file(file_path: str):
    data = openYaml(file_path)
    return data.get("rotation_items", [])


def get_content_form_file(file: str) -> Any:
        try:
            with open(file, "r", encoding="utf-8") as f:
                return yaml.load(f, Loader=SafeLoader)
        except Exception as e:
            raise Exception(f"Failed to load str(file): {e}")


def search_yaml_files(search_string: str, ns_files_map: Dict[str, Dict[str, Any]], cred_id: str, env: str, shared_cred_files: List[str], env_cred_file: str, target_key: str,
 target_context: str, target_file: str) -> List[AffectedParameter]:
    affected: List[AffectedParameter] = []

    for filename, content in ns_files_map.items():

        is_target = filename == target_file
        matches = find_in_yaml(content, search_string, is_target, target_key, target_context)
        if matches:
            affected.extend(get_affected_param_map(
            cred_id, env, shared_cred_files, env_cred_file, filename, content, matches
            ))
    return affected
#############################################################	

def collects_shared_Credentials(instance_dir: str) -> List[str]:
    inventory_yaml = getEnvDefinition(instance_dir)
    
    shared_cred_files = inventory_yaml.get("envTemplate", {}).get("sharedMasterCredentialFiles", [])
    
    if shared_cred_files:
        logger.info(f"Inventory shared master creds list:\n{dump_as_yaml_format(shared_cred_files)}")
    
    return shared_cred_files


#############################################################
def check_if_many_envs_exist(env: str) -> str:
    envs = env.strip().splitlines()
    if len(envs) > 1:
        raise ValueError("Expected only one environment to be passed. Failing the job")
    return envs[0]

def scandir_recursive(
    path: str,
    yaml_files_map: Dict[str, Any],
    ns_files: List[str],
    env_name: str,
    shared_list: List[str],
    is_encrypted: bool,
    public_key: str
) -> None:
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            scandir_recursive(entry.path, yaml_files_map, ns_files, env_name, shared_list, is_encrypted, public_key)
            
        elif entry.is_file(follow_symlinks=False) and entry.name.endswith((".yml", ".yaml")):
            name_wo_ext = os.path.splitext(entry.name)[0]
            normalized_path = os.path.normpath(entry.path)

            if name_wo_ext in shared_list:
                content = (
                    crypt.decrypt_file(
                        entry.path,
                        in_place=True,
                        ignore_is_crypt=True,
                        public_key=public_key,
                        crypt_backend='SOPS'
                    ) if is_encrypted else openYaml(entry.path)
                )
                logger.info(f"am here {entry.path}")
                yaml_files_map[entry.path] = content

            else:
                ns_fragment = os.path.normpath(os.path.join(env_name, "Namespaces"))
                if ns_fragment in normalized_path:
                    ns_files.append(entry.path)

def scan_and_get_yaml_files(
    env_dir: str,
    env_name: str,
    shared_list: List[str],
    is_encrypted: bool,
    public_key: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    yaml_files_map = {}
    ns_files = []
    scandir_recursive(env_dir, yaml_files_map, ns_files, env_name, shared_list, is_encrypted, public_key)
    ns_files_map = asyncio.run(load_yaml_files_parallel(ns_files))
    return yaml_files_map, ns_files_map

def get_ns_content(
    yaml_content_map: Dict[str, Dict[str, Any]],
    namespace: str
) -> Optional[Tuple[str, Dict[str, Any]]]:
    for file_name, content in yaml_content_map.items():
    
        if file_name.endswith(("namespace.yml", "namespace.yaml")) and content:
            if namespace == content.get("name"):
                return file_name, content
    return None

def get_app_content(
    yaml_content_map: Dict[str, Dict[str, Any]],
    namespace: str,
    app: str
) -> Optional[Tuple[str, Dict[str, Any]]]:
    for file_name, content in yaml_content_map.items():
        if file_name.endswith(("namespace.yml", "namespace.yaml")) or content is None:
            continue

        if app != content.get("name"):
            continue

        parent_dir = Path(file_name).parent.parent
        ns_file_yaml = parent_dir / "namespace.yaml"
        ns_file_yml = parent_dir / "namespace.yml"

        try:
            ns_content = get_content_form_file(ns_file_yaml)
        except Exception:
            try:
                ns_content = get_content_form_file(ns_file_yml)
            except Exception as e:
                logger.warning(f"Failed to load namespace file for {file_name}: {e}")
                continue

        if ns_content and ns_content.get("name") == namespace:
            return file_name, content

    return None


def process_entry_in_payload(
    entry: PayloadEntry,
    env: str,
    shared_cred_content: Dict[str, Any],
    env_cred_content: Dict[str, Any],
    ns_files_map: Dict[str, Dict[str, Any]],
    processed_cred_and_files: Dict[str, List[CredMap]]
) -> Optional[RotationResult]:

    if entry.application and entry.context == "pipeline":
        raise ValueError(f"ERROR: context {entry.context} should not be used for application for parameter {entry.parameter_key}. Hence failing")

    logger.info(f"Processing namespace is {entry.namespace}, application is {entry.application}, param_key is {entry.parameter_key}, context is {entry.context}")

    if entry.application:
        target = get_app_content(ns_files_map, entry.namespace, entry.application)
    else:
        target = get_ns_content(ns_files_map, entry.namespace)

    if not target:
        raise ValueError(f"ERROR: Target File not found for parameter key {entry.parameter_key}")

    target_file, target_yaml = target
    param_type = resolve_param(entry.context)
    if param_type not in target_yaml:
        raise ValueError(f"Context '{entry.context}' not found in target yaml for parameter key {entry.parameter_key}")

    sub_content = target_yaml[param_type]
    try:
        value_to_search, cred_id = extract_credential(entry.parameter_key, sub_content, entry.credential_field)
    except Exception as e:
        raise Exception(f"ERROR: credential cannot be extracted for target key {entry.parameter_key}. Error {e}")

    if not value_to_search or not cred_id:
        raise Exception(f"ERROR: credential '{cred_id}' is not found in target file specified")

    # Find which credential files contain this credential
    shared_match_files = [k for k, v in shared_cred_content.items() if cred_id in v]
    env_cred_file = next((k for k, v in env_cred_content.items() if cred_id in v), "")


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
    logger.info(f"Finished processing of  param_key is {entry.parameter_key}")
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
    return None



def cred_rotation():
    start = time.time()
    logger.info(f"printing number of cpu {os.cpu_count()}")
    
    env_name, envgene_age_public_key = getenv_with_error('ENV_NAME'), getenv_with_error('ENVGENE_AGE_PUBLIC_KEY')
    creds_rotation_enabled, cred_payload = getenv_with_error('CRED_ROTATION_FORCE') == "true",yaml.safe_load(getenv_with_error('CRED_ROTATION_PAYLOAD'))
    cluster_name, work_dir, env = getenv_with_error('CLUSTER_NAME'),getenv_with_error('CI_PROJECT_DIR'),check_if_many_envs_exist(env_name)
    logger.info(f"Input is {creds_rotation_enabled} {env_name}  {work_dir} {cluster_name}")
    encrypt_type, is_encrypted = crypt.get_configured_encryption_type()
    encrypt_type = 'SOPS' ##########################REMOVE HARCODING#####################
    if encrypt_type == 'Fernet':
        raise Exception(f"Failed to update credential in file as supported type is only SOPS")
    
    base_env_path = f"{work_dir}/environments/{cluster_name}/{env}"
    env_cred_file = f"{base_env_path}/Credentials/credentials.yml"
    output_path = f"{work_dir}/affected-sensitive-parameters.yaml"
    creds_path = f"/tmp/payload.yml" ##########################CHANGE PATH#####################

    logger.info(f"base env path is {base_env_path}")
    write_yaml_to_file(creds_path, cred_payload)
	
	
    shared_creds =  collects_shared_Credentials(base_env_path)
    logger.info(f"Encryption is {is_encrypted} and type is {encrypt_type}")
    
    fileread = time.time()
    shared_content_map, ns_files_map = scan_and_get_yaml_files(base_env_path, env_name, shared_creds, is_encrypted, envgene_age_public_key)
    logger.info(f"✅ Fileread Completed in {round(time.time() - fileread, 2)} seconds.")
    env_cred_map ={}
    #Decrypt Environment credential file if encrypted
    env_cred_map[env_cred_file] = decrypt_file(envgene_age_public_key, env_cred_file, False, encrypt_type, '')  

    #Decrypt Payload file if encrypted
    payload_data = decrypt_file(envgene_age_public_key, creds_path, True, 'SOPS', 'Please check if encryption type is SOPS') 
        
    payload_raw =  payload_data.get("rotation_items", [])
   
    payload_objects: List[PayloadEntry] = [PayloadEntry.from_dict(entry) for entry in payload_raw]
    
    final_result: List[RotationResult] = []
    processed_cred_and_files = {}

    for entry in payload_objects:
        result = process_entry_in_payload(
            entry, env, shared_content_map, env_cred_map, ns_files_map, processed_cred_and_files
        )
        if result:
            final_result.append(result)
    logger.info(f"final result is {final_result}")
    if final_result:
        write_yaml_to_file(output_path, [r.to_dict() for r in final_result])
    else:
        raise Exception(f"No affected parameters found for the given target keys. Hence Failing")

    if not creds_rotation_enabled:
        raise Exception(f"Failed to update credential in file as creds rotation is not enabled")
    updated_content, original_content = update_cred_content(processed_cred_and_files)
    write_updated_cred_into_file(updated_content, original_content, is_encrypted, envgene_age_public_key)

    
    logger.info(f"✅ Completed in {round(time.time() - start, 2)} seconds.")

def decrypt_file(envgene_age_public_key, file_path, in_place, crypt_backend, error_message):
    try:
        return crypt.decrypt_file(file_path, in_place=in_place, ignore_is_crypt=True,
                           public_key=envgene_age_public_key, crypt_backend=crypt_backend
                           )
    except Exception as e:
        raise Exception(f"Decryption of payload failed. {error_message} {e}")
    
 
def update_cred_content(
    processed_cred_and_files: Dict[str, List[CredMap]]
):
    updated_files: Dict[str, List[Dict[str, Any]]] = {}
    original_files: Dict[str, List[Dict[str, Any]]] = {}

    try:
        logger.info(f"size is {len(processed_cred_and_files)}")
        for cred_file, updates in processed_cred_and_files.items():
            if not updates:
                logger.warning(f"No updates found for file {cred_file}, skipping")
                continue

            # Deep copy original content from the first update (assumed all updates share the same original content)
            original_content = copy.deepcopy(updates[0].shared_content)
            content = copy.deepcopy(original_content)

            for update in updates:
                cred_id = update.cred_id
                param_value = update.param_value
                cred_field = update.cred_field.lower()

                logger.debug(f"Updating credential '{cred_id}' field '{cred_field}' to '{param_value}' in file '{cred_file}'")

                if not content or cred_id not in content:
                    raise Exception(f"Credential ID '{cred_id}' not found in content for file '{cred_file}'")

                data_block = content[cred_id].get("data")
                if not data_block:
                    raise Exception(f"'data' block missing for credential ID '{cred_id}' in file '{cred_file}'")

                if cred_field not in {"username", "password", "secret"}:
                    raise Exception(f"Unsupported credential field '{cred_field}' for credential ID '{cred_id}'")

                # Apply the update
                data_block[cred_field] = param_value

            # Save results
            updated_files[cred_file] = content
            original_files[cred_file] = original_content
        return updated_files, original_files

    except Exception as e:
        raise Exception(f"Preparation of output data failed {e}")
        
        
       
                    
def write_updated_cred_into_file(updated_files, original_files, is_encrypted, envgene_age_public_key):
    try:
        # All files processed without errors, now write and encrypt if needed
        update_file(updated_files, is_encrypted, envgene_age_public_key)
    except Exception as e:
        logger.error(f"Updation of file failed {e} \n Hence reverting the change")
        update_file(original_files, is_encrypted, envgene_age_public_key)
        logger.info(f"Files restored to original state. Creds changes are not updated.")

def update_file(files_to_update, is_encrypted, envgene_age_public_key):
    futures = []
    with ProcessPoolExecutor(max_workers=min(os.cpu_count(), len(files_to_update))) as executor:
            for cred_file, creds in files_to_update.items():
                futures.append(
                    executor.submit(write_and_encrypt_task, cred_file, creds, is_encrypted, envgene_age_public_key)
                )
            # Wait for all to finish (optional)
    for future in futures:
        future.result()      

def write_and_encrypt_task(cred_file, creds, is_encrypted, public_key):
    
    # Write YAML
    writeYamlToFile(cred_file, creds)
    
    # Encrypt if needed
    
    if is_encrypted:
        crypt.encrypt_file(
            cred_file, in_place=True, ignore_is_crypt=True,
            public_key=public_key, crypt_backend='SOPS'
        )
    

if __name__ == "__main__":
    #print("scandir:", timeit.timeit(cred_rotation, number=2))
    cred_rotation()
    #times = timeit.repeat("cred_rotation()", globals=globals(), repeat=10, number=1)

     #times is a list like [0.36, 0.38, 0.35, 0.37, 0.39]
    #avg_time = sum(times) / len(times)
    #min_time = min(times)
    #max_time = max(times)

    #print(f"Runs:       {times}")
    #print(f"Average:    {avg_time:.3f}s")
    #print(f"Min:        {min_time:.3f}s")
    #print(f"Max:        {max_time:.3f}s")
