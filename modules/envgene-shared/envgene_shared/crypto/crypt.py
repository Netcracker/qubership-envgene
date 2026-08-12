import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from os import getenv, path
from typing import Callable

from envgene_shared.utils.yaml_utils import openYaml, get_empty_yaml, validate_yaml_by_scheme_or_fail
from envgene_shared.utils.business_utils import get_schema_dir, get_project_root
from envgene_shared.utils.file_utils import check_file_exists, get_files_with_filter, is_cred_file
from envgene_shared.utils.logger import logger
from envgene_shared.utils.collections_utils import split_multi_value_param
from envgene_shared.utils.crypt_utils import *
from envgene_shared.utils.constants import FERNET_ID, SOPS_ID

from envgene_shared.crypto.fernet_handler import crypt_Fernet, extract_value_Fernet, is_encrypted_Fernet
from envgene_shared.crypto.sops_handler import crypt_SOPS, extract_value_SOPS, is_encrypted_SOPS

CRYPT_FUNCTIONS = {
    'SOPS': crypt_SOPS,
    'Fernet': crypt_Fernet
}

IS_ENCRYPTED_FUNCTIONS = {
    'SOPS': is_encrypted_SOPS,
    'Fernet': is_encrypted_Fernet,
}

EXTRACT_FUNCTIONS = {
    'SOPS': extract_value_SOPS,
    'Fernet': extract_value_Fernet
}

def get_configured_encryption_type():
    return get_crypt_backend(), get_crypt()


def decrypt_file(file_path, *, secret_key=None, in_place=True, public_key=None, crypt_backend=None,
                 ignore_is_crypt=False,
                 default_yaml: Callable = get_empty_yaml, allow_default=False, is_crypt=None,
                 load_result=True, _file_info=None, **kwargs):
    res = handle_missing_file(file_path, default_yaml, allow_default)
    if res != 0:
        return res
    if is_empty_cred_file(file_path):
        logger.debug(f'File is empty, skipping decryption. Path: {file_path}')
        return get_empty_yaml() if load_result else None 
    crypt_backend = detect_crypt_backend_from_file(file_path)
    encrypted = crypt_backend is not None
    is_crypt = is_crypt if is_crypt is not None else get_crypt()
    if not ignore_is_crypt and not is_crypt:
        if encrypted:
            raise ValueError(f'Parameter crypt is set to false in config, but this cred file is encrypted: {file_path}')
        logger.info("'crypt' is set to 'false', skipping decryption")
        if load_result:
            return openYaml(file_path)
        return None
      
    if not encrypted:
        logger.warning(f'File is not encrypted. Path: {file_path}')
        return openYaml(file_path) if load_result else None
    
    return CRYPT_FUNCTIONS[crypt_backend](
        file_path=file_path, secret_key=secret_key, in_place=in_place,
        public_key=public_key, mode='decrypt', load_result=load_result, **kwargs
    )


def encrypt_file(file_path, *, secret_key=None, in_place=True, public_key=None, crypt_backend=None,
                 ignore_is_crypt=False, is_crypt=None,
                 minimize_diff=False, old_file_path=None, default_yaml: Callable = get_empty_yaml, allow_default=False,
                 load_result=True, **kwargs):
    crypt_backend = crypt_backend if crypt_backend is not None else get_crypt_backend()
    if minimize_diff:
        if not old_file_path:
            raise ValueError('minimize_diff was set to true but old_file_path was not specified')
        if not check_file_exists(old_file_path):
            minimize_diff = False
            logger.warning(f"Cred file at {old_file_path} doesn't exist, minimize_diff parameter is ignored")
        elif not is_encrypted(old_file_path, crypt_backend):
            minimize_diff = False
            logger.warning(f"Cred file at {old_file_path} is not encrypted, minimize_diff parameter is ignored")
    res = handle_missing_file(file_path, default_yaml, allow_default)
    if res != 0:
        return res
    if is_empty_cred_file(file_path):
        logger.debug(f'File is empty, skipping encryption. Path: {file_path}')
        return get_empty_yaml() if load_result else None
    is_crypt = is_crypt if is_crypt is not None else get_crypt()    
    encrypted = is_encrypted(file_path, crypt_backend)
    if not ignore_is_crypt and not is_crypt:
        if encrypted:
            raise ValueError(f'Parameter crypt is set to false in config, but this cred file is encrypted: {file_path}')
        logger.info("'crypt' is set to 'false', skipping encryption")
        if load_result:
            return openYaml(file_path)
        return None    
    if encrypted:
        logger.warning(f'File is already encrypted. Path: {file_path}')
        return openYaml(file_path) if load_result else None

    encrypted_regex = None
    file_content = openYaml(file_path)
    if is_effective_set_cred_file(file_path):  
        literal_keys, has_literal, has_reference = analyze_cred_file(file_content)      
        if not has_literal:
            logger.debug(f"No literal keys found, skipping encryption. Path: {file_path}")
            return file_content if load_result else None
        elif not has_reference:
            logger.debug(f"full file to be encrypted. Path: {file_path}")
            encrypted_regex = None
        else:
            encrypted_regex = "|".join(
                f"^{re.escape(key)}$"
                for key in sorted(literal_keys)
            )
        logger.debug(f"encrypted_regex = {encrypted_regex} for file = {file_path}")
    else:
        validate_yaml_by_scheme_or_fail(input_yaml_content=file_content, schema_file_path=get_schema_dir() / "credential.schema.json")
        encrypted_regex = r"^data$"

    return CRYPT_FUNCTIONS[crypt_backend](
        file_path=file_path, secret_key=secret_key, in_place=in_place,
        public_key=public_key, mode='encrypt', minimize_diff=minimize_diff,
        old_file_path=old_file_path, load_result=load_result, encrypted_regex=encrypted_regex, **kwargs
    )


def extract_encrypted_data(file_path, attribute_str):
    """
    @param file_path: path to a file
    @param attribute_str: dot separated path to an attribute 'path.to.an.attribute'
    @return: decrypted value
    """
    crypt_backend = get_crypt_backend()
    return EXTRACT_FUNCTIONS[crypt_backend](file_path, attribute_str)


def get_all_necessary_cred_files() -> set[str]:
    BASE_DIR = get_project_root()
    env_names = getenv("ENV_NAMES", None)
    if not env_names:
        logger.info("ENV_NAMES not set, extracting credential files for full repository")
        return get_files_with_filter(BASE_DIR, is_cred_file)
    env_names_list = split_multi_value_param(env_names)

    sources = set()
    sources.add("configuration")
    
    global_source_locations = ["credentials", "Credentials", "shared-credentials",]
    for location in global_source_locations:
        sources.add(path.join("environments", location))

    for env_name in env_names_list:
        cluster, env = env_name.strip().split("/")
        env_specific_source_locations = ["credentials", "cloud-passport", "cloud-passports",
                                         env, "Credentials", "shared-credentials",]  # relative to BASE_DIR/<cluster_name>/
        for location in env_specific_source_locations:
            sources.add(path.join("environments", cluster, location))

    cred_files = set()
    for source in sources:
        source = path.join(BASE_DIR, source)
        if not path.exists(source):
            continue
        cred_files.update(get_files_with_filter(source, is_cred_file))

    return cred_files


def is_encrypted(file_path, crypt_backend=None):
    CRYPT_BACKEND = get_crypt_backend()
    crypt_backend = crypt_backend if crypt_backend else CRYPT_BACKEND
    return IS_ENCRYPTED_FUNCTIONS[crypt_backend](file_path)


def detect_crypt_backend_from_file(file_path: str) -> str:
    if is_encrypted_Fernet(file_path):
        return FERNET_ID
    if is_encrypted_SOPS(file_path):
        return SOPS_ID
    return None


def _batch_cred_op(files, op_func, **kwargs):
    backend = kwargs.get('crypt_backend') or get_crypt_backend()
    if backend == 'Fernet':
        for file_path in sorted(files):
            op_func(file_path, **{**kwargs, 'load_result': False})
        return
    _parallel_cred_op(files, op_func, **kwargs)


def _parallel_cred_op(files, op_func, **kwargs):
    file_list = sorted(files)
    if not file_list:
        return
    if kwargs.get('minimize_diff'):
        max_workers = 1
    else:
        max_workers = min(len(file_list), os.cpu_count() or 2)
    errors = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(op_func, f, **{**kwargs, 'load_result': False}): f
            for f in file_list
        }
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                future.result()
            except Exception as e:
                errors.append((file_path, e))

    if errors:
        summary = '; '.join(
            f'{file_path} ({type(exc).__name__}: {exc})' for file_path, exc in errors
        )
        raise RuntimeError(f'{op_func.__name__} failed: {summary}') from errors[0][1]


def decrypt_all_cred_files_for_env(**kwargs):
    logger.info("Starting decryption of credential files")
    files = get_all_necessary_cred_files()
    backend = get_crypt_backend()
    validate_crypto_requirements(False)
    t0 = time.perf_counter()
    _parallel_cred_op(files, decrypt_file, **kwargs)
    elapsed = time.perf_counter() - t0
    logger.info(f'Decrypted {len(files)} cred files in {elapsed:.3f}s (backend={backend})')
    logger.debug("Decrypted next cred files:")
    logger.debug(files)


def encrypt_all_cred_files_for_env(**kwargs):
    logger.info("Starting encryption of credential files")
    files = get_all_necessary_cred_files()
    logger.debug("Attempting to encrypt(if crypt is true) next files:")
    logger.debug(files)
    backend = get_crypt_backend()
    validate_crypto_requirements(True)
    t0 = time.perf_counter()
    _parallel_cred_op(files, encrypt_file, **kwargs)
    elapsed = time.perf_counter() - t0
    logger.info(f'Encrypted {len(files)} cred files in {elapsed:.3f}s (backend={backend})')

