
import os
import copy
import re
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List, Tuple, Optional, Set
from models import CredMap
from .yaml_utils import get_nested_target_key
from .file_utils import openJson
from pathlib import Path
from envgenehelper import crypt, writeYamlToFile, openYaml, dump_as_yaml_format
import envgenehelper.logger as logger
from utils.error_constants import  *
from envgenehelper.errors import ValidationError, ValueError
from multiprocessing import Pool, cpu_count

pattern  = re.compile(r"\$\{creds\.get\([\"']([^\"']+)[\"']\)\.(username|password|secret)\}")

def collect_shared_credentials(env_files_map: Dict[str, Any]) -> Set[str]:
    shared_cred_names: Set[str] = set()
    for file_content in env_files_map.values():
        creds = file_content.get("envTemplate", {}).get("sharedMasterCredentialFiles", [])
        if creds:
            shared_cred_names.update(creds)
    
    if shared_cred_names:
        logger.info(f"✅ Inventory shared master creds list collected from all envs:\n{dump_as_yaml_format(sorted(shared_cred_names))}")
    
    return shared_cred_names


def extract_credential(target_key: str, yaml_content: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    if  target_key in yaml_content:
         value = yaml_content.get(target_key)
    elif "." in target_key:
        value = get_nested_target_key(yaml_content, target_key)
    else:
        raise ValidationError(ErrorMessages.PARAM_NOT_FOUND.format(target_key=target_key), ErrorCodes.INVALID_INPUT_CODE)

    if not isinstance(value, str):
        raise ValueError(ErrorMessages.INVALID_DATA_TYPE.format(expected="string", value=target_key, type=type(value)), ErrorCodes.INVALID_DATA_TYPE_CODE)

    match = pattern.search(value)
    if match:
        return match.group(0), match.group(1), match.group(2)
    return None

def read_shared_cred_files(shared_creds: Set[str], cluster_dir: str, work_dir: str,  is_encrypted: str, public_key: str):
    shared_creds_files_set = set()
    dirs_to_scan = [f'{work_dir}/environments', f'{work_dir}/environments/credentials', f'{work_dir}/environments/Credentials']
    allowed_exts = ('.yml', '.yaml', '.json')
    source_path = Path(cluster_dir).resolve()
    scan_dir_for_creds(source_path, shared_creds, shared_creds_files_set)
    files = [entry.path for d in dirs_to_scan if os.path.exists(d) for entry in os.scandir(d) if entry.is_file() and entry.name.endswith(allowed_exts) and os.path.splitext(entry.name)[0] in shared_creds]
    shared_creds_files_set.update(files)
    shared_content_map = read_env_cred_files(shared_creds_files_set, is_encrypted, public_key)
    return shared_content_map


def scan_dir_for_creds(path: Path, shared_creds: set, shared_creds_files_set: List[str]):
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            scan_dir_for_creds(Path(entry.path), shared_creds, shared_creds_files_set)
        elif entry.is_file(follow_symlinks=False) and entry.name.endswith((".yml", ".yaml", ".json")):
            name_wo_ext = os.path.splitext(entry.name)[0]
            if name_wo_ext in shared_creds and entry.path not in shared_creds_files_set:
                logger.debug(f"✅ Found shared credential file: {entry.path}")
                shared_creds_files_set.add(entry.path)


def decrypt_task(args):
    is_encrypted, public_key, filepath = args
    content = decrypt_and_get_content(is_encrypted, public_key, filepath)
    return filepath, content

def read_env_cred_files(creds_files, is_encrypted, public_key):
    # Use multiprocessing only if heavy workload
    parallel_threshold = 8
    use_parallel = len(creds_files) >= parallel_threshold

    if use_parallel:
        args_list = [(is_encrypted, public_key, filepath) for filepath in creds_files]
        with Pool(min(len(creds_files), cpu_count())) as pool:
            results = pool.map(decrypt_task, args_list)
        return dict(results)

    # Fall back to sequential for small workloads
    result = {}
    for filepath in creds_files:
        result[filepath] = decrypt_and_get_content(is_encrypted, public_key, filepath)
    return result

def decrypt_and_get_content(is_encrypted, public_key, filepath):
    if is_encrypted:
        return decrypt_file(public_key, filepath, True, 'SOPS', ErrorMessages.FILE_DECRYPT_ERROR, ErrorCodes.INVALID_CONFIG_CODE)
    try:
        if filepath.endswith(".json"):
            content = openJson(filepath)
        else:
            content = openYaml(filepath)
        return content
    except Exception as e:
        raise ValidationError(ErrorMessages.FILE_READ_ERROR.format(file=filepath, e=str(e)), error_code=ErrorCodes.INVALID_CONFIG_CODE)


def decrypt_file(envgene_age_public_key, file_path, in_place, crypt_backend, error_msg, error_code):
    try:
        return crypt.decrypt_file(file_path, in_place=in_place, ignore_is_crypt=True,
                           public_key=envgene_age_public_key, crypt_backend=crypt_backend
                           )
    except Exception as e:
        raise ValidationError(error_msg.format(file=file_path, e=str(e)), error_code=error_code)


def update_cred_content(
    processed_cred_and_files: Dict[str, List[CredMap]]
):
    updated_files: Dict[str, List[Dict[str, Any]]] = {}
    original_files: Dict[str, List[Dict[str, Any]]] = {}

    logger.info(f"Preparing updates for {len(processed_cred_and_files)} credential files")
    logger.info(f"Credential files are {list(processed_cred_and_files.keys())}")
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

            logger.debug(f"Updating credential '{cred_id}' field '{cred_field}' in file '{cred_file}'")

            data_block = content[cred_id].get("data")
            if not data_block:
                raise ValidationError(ErrorMessages.MISSING_BLOCK.format(block="data", cred_id=cred_id, cred_file=cred_file), ErrorCodes.INVALID_INPUT_CODE)

            # Apply the update
            data_block[cred_field] = param_value

        # Save results
        updated_files[cred_file] = content
        original_files[cred_file] = original_content
    return updated_files, original_files


def write_updated_cred_into_file(updated_files, original_files, is_encrypted, envgene_age_public_key):
    try:
        # All files processed without errors, now write and encrypt if needed
        update_file(updated_files, is_encrypted, envgene_age_public_key)
    except Exception as e:
        logger.error(f"Updation of credential file failed {e} \n Hence reverting the change")
        update_file(original_files, is_encrypted, envgene_age_public_key)
        logger.info("No creds changes are updated. Files are restored to original state")


def update_file(files_to_update, is_encrypted, envgene_age_public_key):
    futures = []
    with ProcessPoolExecutor(max_workers=min(os.cpu_count(), len(files_to_update))) as executor:
            for cred_file, creds in files_to_update.items():
                futures.append(
                    executor.submit(write_and_encrypt_task, cred_file, creds, is_encrypted, envgene_age_public_key)
                )
    for future in futures:
        future.result()


def write_and_encrypt_task(cred_file, creds, is_encrypted, public_key):

    # Write YAML
    writeYamlToFile(cred_file, creds)
    # Encrypt if needed
    if is_encrypted:
        try:
            crypt.encrypt_file(
                cred_file, in_place=True, ignore_is_crypt=True,
                public_key=public_key, crypt_backend='SOPS'
            )
        except Exception as e:
           raise ValidationError(ErrorMessages.FILE_ENCRYPT_ERROR.format(file=cred_file, e=str(e)), error_code=ErrorCodes.INVALID_CONFIG_CODE)
