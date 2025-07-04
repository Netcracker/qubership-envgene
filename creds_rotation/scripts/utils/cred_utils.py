
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
        raise KeyError(f"Key '{target_key}' not found in content specified")

    if not isinstance(value, str):
        raise ValueError(f"Expected string but got {type(value)} for target_key: {target_key}")

    match = pattern.search(value)
    if match:
        return match.group(0), match.group(1)
    return None, None

def get_shared_cred_files(shared_creds: List[str], source_dir, stop_dir, final_creds_map):
    for cred_name in shared_creds:
        found_map = {}
        find_cred_file_upwards(Path(source_dir), Path(stop_dir), cred_name, found_map)

        matches = found_map.get(cred_name, [])
        if len(matches) == 1:
            final_creds_map[cred_name] = matches[0]
        elif len(matches) > 1:
            logger.error(f" Duplicate credential file '{cred_name}' found:\n\t" + "\n\t".join(matches))
            raise ReferenceError(f"Duplicate credential file found for: {cred_name}")
        else:
            logger.warning(f"Credential '{cred_name}' not found between {source_dir} and {stop_dir}")

def find_cred_file_upwards(
    current_dir: Path,
    stop_dir: Path,
    cred_name: str,
    found_map: Dict[str, List[str]]
) -> None:

    current_dir = current_dir.absolute()
    stop_dir = stop_dir.absolute()

    if stop_dir not in current_dir.parents and current_dir != stop_dir:
        raise ReferenceError(f"{stop_dir} is not a parent of {current_dir}")

    scan_dir_for_cred(current_dir, cred_name, found_map)

    # Stop recursion early if file found
    if cred_name in found_map and found_map[cred_name]:
        logger.debug(f"Credential {cred_name} found in {current_dir}. Stopping upward search.")
        return

    if current_dir == stop_dir:
        return

    find_cred_file_upwards(current_dir.parent, stop_dir, cred_name, found_map)

def scan_dir_for_cred(path, shared_cred: str, found_map):
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            scan_dir_for_cred(entry.path, shared_cred, found_map)

        elif entry.is_file(follow_symlinks=False) and entry.name.endswith((".yml", ".yaml", ".json")):
            name_wo_ext = os.path.splitext(entry.name)[0]

            if name_wo_ext == shared_cred:
                found_map.setdefault(shared_cred, []).append(entry.path)

def read_cred_files(final_creds_map, is_encrypted, public_key):
    shared_creds_map = {}
    for cred_name, filepath in final_creds_map.items():
        if is_encrypted:
            content = crypt.decrypt_file(
                            filepath,
                            in_place=True,
                            ignore_is_crypt=True,
                            public_key=public_key,
                            crypt_backend='SOPS'
                        )
        else:
            if filepath.endswith(".json"):
                content = openJson(filepath)
            else:
                content = openYaml(filepath)

        shared_creds_map[filepath] = content
    return shared_creds_map


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

    logger.info(f"Preparing updates for {len(processed_cred_and_files)} credential files")
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

            if not content or cred_id not in content:
                raise Exception(f"Credential ID '{cred_id}' not found in  file '{cred_file}'")

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
        crypt.encrypt_file(
            cred_file, in_place=True, ignore_is_crypt=True,
            public_key=public_key, crypt_backend='SOPS'
        )

