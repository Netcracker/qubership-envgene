import os
from typing import Any
from cryptography.fernet import Fernet

from ..business_helper import getenv_with_error
from ..yaml_helper import openYaml, writeYamlToFile, get_or_create_nested_yaml_attribute

from .constants import *

def _apply_Fernet_to_dict(data: dict, fernet:Fernet, fernet_func) -> dict:
    for key, value in data.items():
        if isinstance(value, dict):
            _apply_Fernet_to_dict(value, fernet, fernet_func)
        elif value != '' and not UNENCRYPTED_REGEX.match(key):
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

def crypt_Fernet(file_path, secret_key, in_place, mode, minimize_diff=None, old_file_path=None, *args, **kwargs):
    if not secret_key:
        secret_key = getenv_with_error("SECRET_KEY")
    data = openYaml(file_path)
    fernet = Fernet(secret_key)
    fernet_func = _decrypt_Fernet if mode == "decrypt" else _encrypt_Fernet
    if isinstance(data, dict):
        new_data = _apply_Fernet_to_dict(data, fernet, fernet_func)
    else:
        new_data = {}
    if minimize_diff and old_file_path and mode != "decrypt":
        _remove_unnecessary_changes(new_data, old_file_path, fernet)
    if in_place:
        writeYamlToFile(file_path, new_data)
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

