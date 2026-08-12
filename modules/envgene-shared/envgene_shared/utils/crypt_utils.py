import os
from pathlib import Path

from envgene_shared.utils.business_utils import get_envgene_config_yaml
from envgene_shared.utils.constants import *
from envgene_shared.utils.file_utils import check_file_exists


def get_crypt():
    config = get_envgene_config_yaml()
    return config.get('crypt', True)


def get_crypt_backend():
    config = get_envgene_config_yaml()
    return config.get('crypt_backend', FERNET_ID)


def validate_crypto_requirements(require_private_key: bool = False,) -> None:
    if not get_crypt():
        return
    backend = get_crypt_backend()
    if backend == FERNET_ID:
        if not os.getenv(SECRET_KEY_ID):
            raise ValueError(f"{SECRET_KEY_ID} is required for crypt_backend={FERNET_ID}")
        return

    if backend == SOPS_ID:
        missing = []
        if not os.getenv(PUBLIC_AGE_KEYS_ID):
            missing.append(PUBLIC_AGE_KEYS_ID)
        if require_private_key and not os.getenv(ENVGENE_AGE_PRIVATE_KEY_ID):
            missing.append(ENVGENE_AGE_PRIVATE_KEY_ID)
        if missing:
            raise ValueError("The following environment variables are required "
                f"for crypt_backend={SOPS_ID}: {', '.join(missing)}")
        return
    raise ValueError(
        f"Unsupported crypt_backend: {backend}"
    )


def handle_missing_file(file_path, default_yaml, allow_default):
    if check_file_exists(file_path):
        return 0  # sentinel value
    if not allow_default:
        raise FileNotFoundError(f"{file_path} not found or is not a file")
    return default_yaml()
    

def is_empty_cred_file(file_path: str) -> bool:
    try:
        if os.path.getsize(file_path) == 0:
            return True
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read().strip()
    except OSError:
        return True
    if not text:
        return True
    return text in ('{}', '---', 'null', '~')


def is_effective_set_cred_file(filepath: str) -> bool:
    return "effective-set" in Path(filepath).parts


def is_external_reference_file(value) -> bool:
    if isinstance(value, dict):
        if "secretStoreId" in value:
            return True
        for child in value.values():
            return is_external_reference_file(child)
        return False

    if isinstance(value, list):
        for child in value:
            return is_external_reference_file(child)
        return False

    if isinstance(value, str):
        return value.startswith("ref+")
    return False


def analyze_cred_file(data):
    literal_keys = set()
    has_reference = False
    has_literal = False

    def walk(value):
        nonlocal has_reference, has_literal
        if isinstance(value, dict):
            # ESO reference: don't inspect below this node
            if "secretStoreId" in value:
                has_reference = True
                return
            for key, child in value.items():
                if isinstance(child, (dict, list)):
                    walk(child)
                elif isinstance(child, str):
                    if child.startswith("ref+"):
                        has_reference = True
                    else:
                        has_literal = True
                        literal_keys.add(key)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(data)
    return literal_keys, has_literal, has_reference