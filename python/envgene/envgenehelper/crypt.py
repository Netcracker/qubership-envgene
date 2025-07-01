import os
import re
from os import getenv, path
from time import perf_counter
from typing import Callable

from envgenehelper.business_helper import getenv_with_error
from envgenehelper.maybe_more_faster_file_search import FileProcessor

from .config_helper import get_envgene_config_yaml
from .yaml_helper import openYaml, get_empty_yaml
from .file_helper import check_file_exists, get_files_with_filter
from .logger import logger
from .shade_files_helper import split_creds_file, merge_creds_file

from .crypt_backends.fernet_handler import crypt_Fernet, extract_value_Fernet, is_encrypted_Fernet
from .crypt_backends.sops_handler import crypt_SOPS, extract_value_SOPS, is_encrypted_SOPS


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
    if check_file_exists(file_path):
        return 0  # sentinel value
    if not allow_default:
        raise FileNotFoundError(f"{file_path} not found or is not a file")
    return default_yaml()


def decrypt_file(file_path, *, secret_key=None, in_place=True, public_key=None, crypt_backend=None, ignore_is_crypt=False,
                 default_yaml: Callable = get_empty_yaml, allow_default=False, is_crypt=None, **kwargs):
    res = _handle_missing_file(file_path, default_yaml, allow_default)
    if res != 0:
        return res
    crypt_backend = crypt_backend if crypt_backend else CRYPT_BACKEND
    is_crypt = is_crypt if is_crypt != None else IS_CRYPT
    if ignore_is_crypt == False and is_crypt == False:
        logger.info("'crypt' is set to 'false', skipping decryption")
        return openYaml(file_path)
    return CRYPT_FUNCTIONS[crypt_backend](file_path=file_path, secret_key=secret_key, in_place=in_place, public_key=public_key, mode='decrypt')


def encrypt_file(file_path, *, secret_key=None, in_place=True, public_key=None, crypt_backend=None, ignore_is_crypt=False, is_crypt=None,
                 minimize_diff=False, old_file_path=None, default_yaml: Callable = get_empty_yaml, allow_default=False, **kwargs):
    if minimize_diff != False:
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
    res = _handle_missing_file(file_path, default_yaml, allow_default)
    if res != 0:
        return res
    crypt_backend = crypt_backend if crypt_backend else CRYPT_BACKEND
    is_crypt = is_crypt if is_crypt != None else IS_CRYPT
    if ignore_is_crypt == False and is_crypt == False:
        logger.info("'crypt' is set to 'false', skipping encryption")
        return openYaml(file_path)
    return CRYPT_FUNCTIONS[crypt_backend](file_path=file_path, secret_key=secret_key, in_place=in_place, public_key=public_key, mode='encrypt', minimize_diff=minimize_diff, old_file_path=old_file_path)


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


def get_all_necessary_cred_files() -> set[str]:
    env_names = getenv("ENV_NAMES", None)
    if not env_names:
        logger.info("ENV_NAMES not set, running in test mode")
        return get_files_with_filter(BASE_DIR, is_cred_file)
    if env_names == "env_template_test":
        logger.info("Running in env_template_test mode")
        return get_files_with_filter(BASE_DIR, is_cred_file)
    env_names_list = env_names.split("\n")

    sources = set()
    sources.add("configuration")
    sources.add(path.join("environments", "credentials"))

    for env_name in env_names_list:
        cluster, env = env_name.strip().split("/")
        # relative to BASE_DIR/<cluster_name>/
        env_specific_source_locations = [
            "credentials", "cloud-passport", "cloud-passports", env]
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
    crypt_backend = crypt_backend if crypt_backend else CRYPT_BACKEND
    return IS_ENCRYPTED_FUNCTIONS[crypt_backend](file_path)


def check_for_encrypted_files(files):
    err_msg = "Parameter crypt is set to false in config, but this cred file is encrypted: {}"
    for f in files:
        if is_encrypted(f):
            raise ValueError(err_msg.format(f))


def decrypt_all_cred_files_for_env(**kwargs):
   # crypt.decrypt_all_cred_files_for_env()
    start = perf_counter()
    get_files = FileProcessor(config)
    files = get_files.get_all_necessary_cred_files()
    end = perf_counter()
    print(f"Get all cred files: {end - start:.4f} seconds")

    if not IS_CRYPT:
        check_for_encrypted_files(files)
    else:
        if CREATE_SHADES:
            for f in files:
                merge_creds_file(f, decrypt_file)
        else:
            for f in files:
                decrypt_file(f, **kwargs)
        logger.debug("Decrypted next cred files:")
        logger.debug(files)


def encrypt_all_cred_files_for_env(**kwargs):
    start = perf_counter()
    get_files = FileProcessor(config)
    files_1 = get_files.get_all_necessary_cred_files()
    end = perf_counter()
    print(f"Get all cred files: {end - start:.4f} seconds")
    start = perf_counter()
    get_files = FileProcessor(config)
    files = get_all_necessary_cred_files()
    end = perf_counter()
    print(f"Get all cred files: {end - start:.4f} seconds")

    logger.debug("Attempting to encrypt(if crypt is true) next files:")
    logger.debug(files)
    if CREATE_SHADES:
        for f in files:
            split_creds_file(f, encrypt_file)
    else:
        for f in files:
            encrypt_file(f, **kwargs)
