from importlib.resources import read_binary
import os
from pathlib import Path
from time import perf_counter
from typing import Callable
from ruamel.yaml.comments import CommentedMap
from multiprocessing import Pool


from .yaml_helper import addHeaderToYaml, openYaml, writeToFile, readYaml, writeYamlToFile


def create_shadow_creds_dir(creds_path: str):
    _creds_path = Path(creds_path)
    creds_file_name = _creds_path.stem
    cur_creds_path = str(_creds_path.parent)
    cur_path = cur_creds_path + '/shades-' + creds_file_name
    if not os.path.exists(cur_path):
        os.makedirs(cur_path)
    return cur_path


def generate_file_header(source_credential_ID, cred_path):
    return f"""\
The contents of this Shade Credential File is generated from Credential: {source_credential_ID}
located at {cred_path}
Contents will be overwritten by next generation.
Please modify this contents only for development purposes or as workaround.\n"""


def create_shadow_file(content: dict, shadow_creds_path,  cred_id: str):
    shadow_file_name = 'shade-' + cred_id + '-cred.yml'
    shadow_cred_path = shadow_creds_path + '/' + shadow_file_name
    writeYamlToFile(shadow_cred_path, content)
    del content
    return shadow_cred_path


def split_creds_parallel():
    pass


def split_creds_file(creds_path: str, encryption_func: Callable, **kwargs):
    """split_cred_file is a function to create shade files from creds file"""
    creds = openYaml(creds_path)
    for cred_id, cred_data in creds.items():
        keys_set = set(cred_data['data'].values())
        if len(keys_set) == 1 and keys_set.pop() == 'valueIsSet':
            continue
        shadow_creds_path = create_shadow_creds_dir(creds_path)
        shadow_cred_path = create_shadow_file(
            {cred_id: cred_data}, shadow_creds_path, cred_id)
        addHeaderToYaml(shadow_cred_path,
                        generate_file_header(cred_id, creds_path))
        encryption_func(shadow_cred_path, **kwargs)
        #     cred_data['data'] = {
        #         _cred_id: 'valueIsSet' for _cred_id in cred_data['data']}

        # writeYamlToFile(creds_path, creds)
    del creds
    print('splited')

# FUNCTION FOR CREATE CREDS FILE FROM SHADOW FILES


def merge_creds_file(creds_path, encryption_func: Callable):
    """merge_creds_file is a function to create creds file from shadow files"""
    shadow_creds_path = Path(os.environ.get('shadow_creds_path', ''))
    shadow_creds_files = shadow_creds_path.iterdir()
    creds = {}
    for file in shadow_creds_files:
        cred = encryption_func(file)
        creds.update(cred)
    writeToFile(creds_path, creds)
    print('merged')
