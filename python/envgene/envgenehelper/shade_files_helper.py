import glob
import yaml

from .yaml_helper import openYaml
from .file_helper import delete_dir
from .logger import logger
import os
from pathlib import Path
CPU_COUNT = os.cpu_count()


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
# The contents of this Shade Credential File is generated from Credential: {source_credential_ID}
# located at {cred_path}
# Contents will be overwritten by next generation.
# Please modify this contents only for development purposes or as workaround.\n"""

def _create_shadow_file(content: dict, shadow_creds_path,  cred_id: str):
    shadow_file_name = 'shade-' + cred_id + '-cred.yml'
    shadow_cred_path = Path(shadow_creds_path, shadow_file_name)
    with open(shadow_cred_path, 'w+', buffering=16*1024) as f:
        yaml.dump(content, f, Dumper=yaml.CDumper)
    del content
    return shadow_cred_path
# Create shade file for each <<credential>> object in credentials files

def _add_comment(file, comment):
    with open(file, 'r+') as f:
        content = f.read()
        f.seek(0)
        f.write(comment + content)

def split_creds_file(creds_path: str):
    """split_cred_file is a function to create shade files from creds file"""
    with open(creds_path) as cred_file:
        creds = yaml.load(cred_file, Loader=yaml.CLoader)
    if creds:
        shadow_creds_path = _init_shadow_creds_dir(creds_path, True)
        results = []
        for cred_id, cred_data in creds.items():
            keys_set = set(cred_data['data'].values())
            if len(keys_set) == 1 and keys_set.issubset({'envgeneNullValue', 'valueIsSet'}):
                continue
            results.append(_create_shadow_file(
                {cred_id: cred_data}, shadow_creds_path, cred_id))
            cred_data['data'] = {_id: 'valueIsSet' for _id in cred_data['data']}
        with open(creds_path, 'w') as f:
            yaml.safe_dump(creds, f)
        return results

    return []

def get_shades_files(creds_path):
    shadow_creds_path = _init_shadow_creds_dir(creds_path, False)
    return(glob.glob(f"{shadow_creds_path}/*.yml")) 

def merge_creds_file(creds_path, shade_files):
    """merge_creds_file is a function to create creds file from shadow files"""
    shadow_creds_path = _init_shadow_creds_dir(creds_path, False)
    if not shadow_creds_path.exists():
        logger.debug(
            f'Failed to find shadow creds dir {shadow_creds_path}. Skip')
        return openYaml(creds_path)
    creds = {}
    for file in shade_files:
        with open(file) as f:
            creds.update(yaml.load(f, Loader=yaml.CLoader))
    try:
        delete_dir(shadow_creds_path)
        with open(creds_path, 'w+') as f:
            yaml.dump(creds, f)
    except Exception as e:
        logger.error(e)
    logger.debug(f'File {creds_path} merged and decrypted')
    return creds
