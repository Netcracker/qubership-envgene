from concurrent.futures import ThreadPoolExecutor, as_completed
import imp
from logging import config
import os
from pathlib import Path
import threading
from time import perf_counter
from typing import Callable
from envgenehelper.shade_file_processor import FileProcessor


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


def _split_cred_file(creds_files_content: dict[str, dict]):
    shadow_creds_paths = []
    print(f"[{threading.get_ident()}] started at {perf_counter()}")
    for creds_path, creds_content in creds_files_content.items():
        for cred_id, cred_data in creds_content.items():
            keys_set = set(cred_data['data'].values())
            if len(keys_set) == 1 and keys_set.pop() == 'valueIsSet':
                continue
            shadow_cred_path = create_shadow_file(
                {cred_id: cred_data}, shadow_creds_path, cred_id)
            addHeaderToYaml(shadow_cred_path,
                            generate_file_header(cred_id, creds_path))
            shadow_creds_paths.append(shadow_cred_path)
    print(f"[{threading.get_ident()}] finished at {perf_counter()}")
    return shadow_creds_paths


def _read_creds_files(creds_path_list):
    _shadow_creds = {}
    print(f"[{threading.get_ident()}] started at {perf_counter()}")
    for creds_path in creds_path_list:
        creds = openYaml(creds_path)
        _shadow_creds[creds_path] = creds
    print(f"[{threading.get_ident()}] finished at {perf_counter()}")
    return _shadow_creds


def split_creds_file(creds_paths_list: list[str], encryption_func: Callable, **kwargs):
    """split_cred_file is a function to create shade files from creds file"""
    all_shadow_creds_files = []
    cpu_count = 4
    chunks = FileProcessor._chunks(creds_paths_list, cpu_count)
    future_to_paths = {}
    # created {path: cred_content} dict
    _creds_files = _read_creds_files(creds_paths_list)
    for cred_path in _creds_files.keys():
        create_shadow_creds_dir(cred_path)

    # with ThreadPoolExecutor(max_workers=cpu_count) as executor:
    #     for chunk in chunks:
    #         future = executor.submit(_read_creds_files, chunk)
    #         future_to_paths[future] = chunk
    #     for future in as_completed(future_to_paths):
    #         try:
    #             result = future.result()
    #             all_shadow_creds_files.extend(result)
    #         except Exception as e:
    #             print(f"Ошибка при обработке: {e}")
    # print(all_shadow_creds_files)
    # for shadow_cred in all_shadow_creds_files:
    #     split_creds_file()
        #     cred_data['data'] = {
        #         _cred_id: 'valueIsSet' for _cred_id in cred_data['data']}

        # writeYamlToFile(creds_path, creds)

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
