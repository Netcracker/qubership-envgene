import os
import re
from os import getenv
from typing import Callable

from .cred_files_processor import get_all_necessary_cred_files

from .config_helper import get_envgene_config_yaml
from .yaml_helper import openYaml, get_empty_yaml
from .file_helper import check_dir_exists, check_file_exists
from .logger import logger

from .crypt_backends.fernet_handler import crypt_Fernet, extract_value_Fernet, is_encrypted_Fernet
from .crypt_backends.sops_handler import crypt_SOPS, extract_value_SOPS, is_encrypted_SOPS
from envgenehelper import shade_files_helper
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

config = get_envgene_config_yaml()
IS_CRYPT = config.get('crypt', True)
CRYPT_BACKEND = config.get('crypt_backend', 'Fernet')
CREATE_SHADES = config.get('crypt_create_shades', True)

BASE_DIR = getenv('CI_PROJECT_DIR', os.getcwd())
VALID_EXTENSIONS = re.compile(r'\.ya?ml$')
TARGET_REGEX = re.compile(r'(^credentials$|creds$)')
TARGET_DIR_REGEX = re.compile(r'/[Cc]redentials(/|$)')
TARGET_PARENT_DIRS = re.compile(r'/(configuration|environments)(/|$)')
IGNORE_DIR = re.compile(r'(/shades-.*)')
CPU_COUNT = os.cpu_count()

try:
    profile
except NameError:
    def profile(func):
        return func
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


def _handle_missing_file(file_path, default_yaml, allow_default):
    if CREATE_SHADES and check_dir_exists(file_path):
        return 0
    if check_file_exists(file_path):
        return 0  # sentinel value
    if not allow_default:
        raise FileNotFoundError(f"{file_path} not found or is not a file")
    return default_yaml()


def encrypt_file(file_path, **kwargs):
    if CREATE_SHADES and CRYPT_BACKEND != 'Fernet':
        if 'effective-set' in file_path:
            return _encrypt_file(file_path, **kwargs)
        return shade_files_helper.split_creds_file(file_path, _encrypt_file, **kwargs)
    return _encrypt_file(file_path, **kwargs)


def decrypt_file(file_path, **kwargs):
    if CREATE_SHADES and CRYPT_BACKEND != 'Fernet':
        if 'effective-set' in file_path:
            return _decrypt_file(file_path, **kwargs)
        return shade_files_helper.merge_creds_file(
            file_path, _decrypt_file, **kwargs)
    return _decrypt_file(file_path, **kwargs)


@profile
def _encrypt_file(file_path, *, secret_key=None, in_place=True, public_key=None, crypt_backend=None, ignore_is_crypt=False, is_crypt=None,
                  minimize_diff=False, old_file_path=None, default_yaml: Callable = get_empty_yaml, allow_default=False, **kwargs):
    if minimize_diff:
        if not old_file_path:
            raise ValueError(
                'minimize_diff was set to true but old_file_path was not specified')
        if not check_file_exists(old_file_path):
            minimize_diff = False
            logger.warning(
                f"Cred file at {old_file_path} doesn't exist, minimize_diff parameter is ignored")
        if not is_encrypted(old_file_path, crypt_backend):
            minimize_diff = False
            logger.warning(
                f"Cred file at {old_file_path} is not encrypted, minimize_diff parameter is ignored")
    if not CREATE_SHADES:
        res = _handle_missing_file(file_path, default_yaml, allow_default)
        if res != 0:
            return res
    crypt_backend = crypt_backend if crypt_backend else CRYPT_BACKEND
    is_crypt = is_crypt if is_crypt is not None else IS_CRYPT
    if not ignore_is_crypt and not is_crypt:
        logger.info("'crypt' is set to 'false', skipping encryption")
        return openYaml(file_path)
    return CRYPT_FUNCTIONS[crypt_backend](file_path=file_path, secret_key=secret_key, in_place=in_place, public_key=public_key, mode='encrypt', minimize_diff=minimize_diff, old_file_path=old_file_path)


def _decrypt_file(file_path, *, secret_key=None, in_place=True, public_key=None, crypt_backend=None, ignore_is_crypt=False,
                  default_yaml: Callable = get_empty_yaml, allow_default=False, is_crypt=None, **kwargs):
    if not CREATE_SHADES:
        res = _handle_missing_file(file_path, default_yaml, allow_default)
        if res != 0:
            return res
    crypt_backend = crypt_backend if crypt_backend else CRYPT_BACKEND
    is_crypt = is_crypt if is_crypt is not None else IS_CRYPT
    if not ignore_is_crypt and not is_crypt:
        logger.info("'crypt' is set to 'false', skipping decryption")
        return openYaml(file_path)
    return CRYPT_FUNCTIONS[crypt_backend](file_path=file_path, secret_key=secret_key, in_place=in_place, public_key=public_key, mode='decrypt')


def extract_encrypted_data(file_path, attribute_str):
    """
    @param file_path: path to a file
    @param attribute_str: dot separated path to an attribute 'path.to.an.attribute'
    @return: decrypted value
    """
    crypt_backend = CRYPT_BACKEND
    return EXTRACT_FUNCTIONS[crypt_backend](file_path, attribute_str)


def is_cred_file(fp: str) -> bool:
    name = os.path.basename(fp)
    name_without_ext = os.path.splitext(name)[0]
    parent_dirs = os.path.dirname(fp)
    # if file extention match VALID_EXTENTIONS regex
    if not VALID_EXTENSIONS.search(name):
        return False
    if not TARGET_PARENT_DIRS.search(parent_dirs):
        return False
    if IGNORE_DIR.search(parent_dirs):
        return False
    # if file name is matches name_without_ext or file dir matches TARGET_DIR_REGEX
    if TARGET_REGEX.search(name_without_ext) or re.search(TARGET_DIR_REGEX, parent_dirs):
        return True
    return False


def is_encrypted(file_path, crypt_backend=None):
    crypt_backend = crypt_backend if crypt_backend else CRYPT_BACKEND
    return IS_ENCRYPTED_FUNCTIONS[crypt_backend](file_path)


def check_for_encrypted_files(files):
    err_msg = "Parameter crypt is set to false in config, but this cred file is encrypted: {}"
    for f in files:
        if is_encrypted(f):
            raise ValueError(err_msg.format(f))


def decrypt_all_cred_files_for_env(**kwargs):
    files = get_all_necessary_cred_files()

    if not IS_CRYPT:
        check_for_encrypted_files(files)
    else:
        # for f in files:
        #     decrypt_file(f, **kwargs)
        with ThreadPoolExecutor(max_workers=4 if not CPU_COUNT else CPU_COUNT) as pool:
            pool.map(decrypt_file, files)
        logger.debug("Decrypted next cred files:")
        logger.debug(files)


@profile
def encrypt_all_cred_files_for_env(**kwargs):
    files = get_all_necessary_cred_files()
    print(files)

    logger.debug("Attempting to encrypt(if crypt is true) next files:")
    logger.debug(files)
    with ThreadPoolExecutor(max_workers=4 if not CPU_COUNT else CPU_COUNT * 2) as pool:
        pool.map(encrypt_file, files)
    # for f in files:
    #     encrypt_file(f, **kwargs)
    logger.info('repo successfully encrypted')
