import os
import re
from typing import Any
from cryptography.fernet import Fernet

from envgene_shared.utils.business_utils import getenv_with_error
from envgene_shared.utils.yaml_utils import openYaml, writeYamlToFile, get_or_create_nested_yaml_attribute
from envgene_shared.utils.logger import logger
from envgene_shared.utils.constants import *

def _apply_Fernet(value, fernet: Fernet, fernet_func, encrypted_regex=None, encrypt=False):
    if isinstance(value, dict):
        for key, child in value.items():
            should_encrypt = (encrypt or encrypted_regex is None or encrypted_regex.match(key))
            value[key] = _apply_Fernet(child, fernet, fernet_func, encrypted_regex, should_encrypt)
        return value

    if isinstance(value, list):
        for index, child in enumerate(value):
            value[index] = _apply_Fernet(child, fernet, fernet_func, encrypted_regex, encrypt)
        return value

    if (isinstance(value, str) and value != '' and encrypt):
        return fernet_func(value, fernet)
    return value

def _apply_Fernet_to_dict(data: dict, fernet:Fernet, fernet_func, encrypted_regex=None,) -> dict:
    for key, value in data.items():
        if isinstance(value, dict):
            _apply_Fernet_to_dict(value, fernet, fernet_func)
        elif value != '' and (encrypted_regex is None or encrypted_regex.match(key)):
            data[key] = fernet_func(value, fernet)
    return data

def _encrypt_Fernet(text, fernet: Fernet) -> str:
    text = str(text)
    return f"{FERNET_STR}{fernet.encrypt(text.encode('utf-8')).decode('utf-8')}"

def _decrypt_Fernet(text, fernet: Fernet):
    text = str(text)
    if not text:
        return text
    if not FERNET_STR in text:
        return text
    return fernet.decrypt(text.replace(FERNET_STR, '').encode('utf-8')).decode('utf-8')

def _remove_unnecessary_changes(data: dict, old_data_path: str, fernet: Fernet) -> None:
    if not os.path.exists(old_data_path):
        return
    old_data = openYaml(old_data_path)
    _reuse_old_fernet_tokens(data, dict(old_data), fernet)

def _reuse_old_fernet_tokens(data: dict, old_data: dict, fernet: Fernet) -> None:
    for k, v in data.items():
        if not k in old_data.keys():
            continue
        if isinstance(v, dict) and isinstance(old_data[k], dict):
            _reuse_old_fernet_tokens(v, old_data[k], fernet)
            continue
        decoded_old_v = _decrypt_Fernet(old_data[k], fernet)
        if old_data[k] == decoded_old_v:
            continue
        elif decoded_old_v == _decrypt_Fernet(v, fernet):
            data[k] = old_data[k]

def extract_value_Fernet(file_path: str, attribute_str: str) -> Any:
    data = crypt_Fernet(file_path, secret_key=None, in_place=False, mode='decrypt')
    value = get_or_create_nested_yaml_attribute(data, attribute_str, None)
    return value

def crypt_Fernet(file_path, secret_key, in_place, mode, minimize_diff=None, old_file_path=None,
                 load_result=True, encrypted_regex=None, *args, **kwargs):
    if not secret_key:
        secret_key = getenv_with_error("SECRET_KEY")
    data = openYaml(file_path)
    fernet = Fernet(secret_key)
    fernet_func = _decrypt_Fernet if mode == "decrypt" else _encrypt_Fernet
    compiled_regex = (re.compile(encrypted_regex) if encrypted_regex else None)
    if isinstance(data, dict):
        new_data = _apply_Fernet(data, fernet, fernet_func, compiled_regex)
    else:
        new_data = {}
    if minimize_diff and old_file_path and mode != "decrypt":
        _remove_unnecessary_changes(new_data, old_file_path, fernet)
    if in_place:
        writeYamlToFile(file_path, new_data)
        return new_data if load_result else None
    return new_data

def is_encrypted_Fernet(file_path):
    content = openYaml(file_path)
    return _is_encrypted_Fernet(content)

def _is_encrypted_Fernet(data):
    for _, value in data.items():
        if isinstance(value, dict) and _is_encrypted_Fernet(value):
            return True
        if isinstance(value, str) and value.startswith(FERNET_STR):
            return True
    return False

