
import os
import copy
import re
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List, Tuple, Optional
from models import CredMap
from .yaml_utils import get_nested_target_key
from .file_utils import openJson
from pathlib import Path
from envgenehelper import crypt, writeYamlToFile, openYaml, getEnvDefinition, dump_as_yaml_format
import envgenehelper.logger as logger
from utils.error_constants import  *
from envgenehelper.errors import ValidationError, ValueError, ReferenceError


def collects_shared_credentials(instance_dir: str) -> List[str]:
    inventory_yaml = getEnvDefinition(instance_dir)
    shared_cred_names = inventory_yaml.get("envTemplate", {}).get("sharedMasterCredentialFiles", [])
    if shared_cred_names:
        logger.info(f"Inventory shared master creds list:\n{dump_as_yaml_format(shared_cred_names)}")
    return shared_cred_names


def extract_credential(target_key: str, yaml_content: Dict[str, Any], cred_field: str) -> Tuple[Optional[str], Optional[str]]:
    pattern  = re.compile(r"\$\{creds\.get\([\"']([^\"']+)[\"']\)\.(" + re.escape(cred_field) + r")\}")
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
        return match.group(0), match.group(1)
    return None, None

def get_shared_cred_files(shared_creds: List[str], source_dir: str, stop_dir: str, final_creds_map: Dict[str, str]):
    source_path = Path(source_dir).resolve()
    stop_path = Path(stop_dir).resolve()

    remaining_creds = set(shared_creds)

    while True:
        if stop_path not in source_path.parents and source_path != stop_path:
            raise ReferenceError(ErrorMessages.INVALID_PATH.format(stop_dir=stop_dir, source_path=source_path), ErrorCodes.INVALID_PATH_CODE)
        logger.info(f"Searching for shared credentials in {source_path}")
        found_map = {}
        scan_dir_for_creds(source_path, remaining_creds, found_map)

        remaining_creds = decide_to_scan(found_map, final_creds_map, remaining_creds)

        if not remaining_creds or source_path == stop_path:
            break

        source_path = source_path.parent

def decide_to_scan(found_map: Dict[str, List[str]], final_creds_map: Dict[str, str], remaining_creds: set) -> set:
    next_round = set()
    for cred_name in remaining_creds:
        matches = found_map.get(cred_name, [])
        if len(matches) == 1:
            final_creds_map[cred_name] = matches[0]
        elif len(matches) > 1:
            logger.error(f"Duplicate credential file '{cred_name}' found:\n\t" + "\n\t".join(matches))
            raise ReferenceError(ErrorMessages.DUPLICATE_FILE_ERROR.format(matches=len(matches), cred_name=cred_name), ErrorCodes.DUPLICATE_FILES_CODE)
        else:
            next_round.add(cred_name)
            logger.info(f"Credential '{cred_name}' not found in current dir. Will scan upwards.")
    return next_round

def scan_dir_for_creds(path: Path, shared_creds: set, found_map: Dict[str, List[str]]):
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            scan_dir_for_creds(Path(entry.path), shared_creds, found_map)
        elif entry.is_file(follow_symlinks=False) and entry.name.endswith((".yml", ".yaml", ".json")):
            name_wo_ext = os.path.splitext(entry.name)[0]
            if name_wo_ext in shared_creds:
                found_map.setdefault(name_wo_ext, []).append(entry.path)


def read_cred_files(final_creds_map, is_encrypted, public_key):
    shared_creds_map = {}
    for cred_name, filepath in final_creds_map.items():
        if is_encrypted:
            content = decrypt_file(public_key, filepath, True, 'SOPS', ErrorMessages.FILE_DECRYPT_ERROR, ErrorCodes.INVALID_CONFIG_CODE) 
        else:
            if filepath.endswith(".json"):
                content = openJson(filepath)
            else:
                content = openYaml(filepath)

        shared_creds_map[filepath] = content
    return shared_creds_map


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
