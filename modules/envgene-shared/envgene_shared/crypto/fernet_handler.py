from cryptography.fernet import Fernet

from envgene_shared.utils.constants import FERNET_STR


def _decrypt_values(value, fernet: Fernet):
    if isinstance(value, dict):
        for key, child in value.items():
            value[key] = _decrypt_values(child, fernet)
        return value
    if isinstance(value, list):
        for index, child in enumerate(value):
            value[index] = _decrypt_values(child, fernet)
        return value
    if isinstance(value, str) and value.startswith(FERNET_STR):
        return fernet.decrypt(value[len(FERNET_STR):].encode('utf-8')).decode('utf-8')
    return value


def decrypt_Fernet_data(data, secret_key):
    return _decrypt_values(data, Fernet(secret_key))


def is_encrypted_Fernet(data):
    for _, value in data.items():
        if isinstance(value, dict) and is_encrypted_Fernet(value):
            return True
        if isinstance(value, str) and value.startswith(FERNET_STR):
            return True
    return False
