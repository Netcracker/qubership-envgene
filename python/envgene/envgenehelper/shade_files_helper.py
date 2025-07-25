from .logger import logger
import os
from pathlib import Path
from typing import Callable

from envgenehelper.file_helper import delete_dir


from .yaml_helper import addHeaderToYaml, openYaml, writeYamlToFile

# Creates shade files directory if not exists
def _init_shadow_creds_dir(creds_path: str, encryption_mode: bool):
    _creds_path = Path(creds_path)
    creds_file_name = _creds_path.stem
    cur_creds_path = str(_creds_path.parent)
    dir_path = cur_creds_path + '/shades-' + creds_file_name
    if not os.path.exists(dir_path) and encryption_mode:
        os.makedirs(dir_path)
    return Path(dir_path)


def _generate_file_header(source_credential_ID, cred_path):
    return f"""\
The contents of this Shade Credential File is generated from Credential: {source_credential_ID}
located at {cred_path}
Contents will be overwritten by next generation.
Please modify this contents only for development purposes or as workaround.\n"""


def _create_shadow_file(content: dict, shadow_creds_path,  cred_id: str):
    shadow_file_name = 'shade-' + cred_id + '-cred.yml'
    shadow_cred_path = Path(shadow_creds_path, shadow_file_name)
    writeYamlToFile(shadow_cred_path, content)
    del content
    return shadow_cred_path

# Create shade file for each <<credential>> object in credentials files
def split_creds_file(creds_path: str, encryption_func: Callable, **kwargs):
    """split_cred_file is a function to create shade files from creds file"""
    creds = openYaml(creds_path)

    shadow_creds_path = _init_shadow_creds_dir(creds_path, True)
    for cred_id, cred_data in creds.items():
        keys_set = set(cred_data['data'].values())
        if len(keys_set) == 1 and keys_set.issubset({'envgeneNullValue', 'valueIsSet'}):
            continue
        shadow_cred_path = _create_shadow_file(
            {cred_id: cred_data}, shadow_creds_path, cred_id)

        cred_data['data'] = {
            _cred_id: 'valueIsSet' for _cred_id in cred_data['data']}
        encryption_func(shadow_cred_path, **kwargs)
        addHeaderToYaml(str(shadow_cred_path),
                        _generate_file_header(cred_id, creds_path))
    writeYamlToFile(creds_path, creds)
    del creds
    logger.debug(f'File {creds_path} was splitted and encrypted')
    return 0

# 
def merge_creds_file(creds_path, encryption_func: Callable, **kwargs):
    """merge_creds_file is a function to create creds file from shadow files"""
    shadow_creds_path = _init_shadow_creds_dir(creds_path, False)
    if not shadow_creds_path.exists():
        logger.warning(
            f'Failed to find shadow creds dir {shadow_creds_path}. Skip')
        return
    shadow_creds_files = shadow_creds_path.iterdir()
    creds = {}
    for file in shadow_creds_files:
        cred = encryption_func(file, **kwargs)
        creds.update(cred)
    delete_dir(shadow_creds_path)
    writeYamlToFile(creds_path, creds)
    logger.debug(f'File {creds_path} merged and decrypted')
    return creds
