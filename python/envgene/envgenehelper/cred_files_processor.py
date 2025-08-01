import os
from os import getenv
import subprocess

from .logger import logger

BASE_DIR = getenv('CI_PROJECT_DIR', os.getcwd())

# run find command to search all credential files in cur BASE_DIR


def normalize_path(path: str) -> str:
    if os.name == 'nt':
        if path.startswith('/c/'):
            path = path.replace('/c/', 'C:/').replace('/', '\\')
    return path


def _get_files_subprocess(full_path='', env_name=''):
    cur_path = BASE_DIR if not full_path else full_path
    bash_path = cur_path.replace('\\', '/').replace(':', '').replace('C', '/c')
    if not bash_path.endswith('/'):
        bash_path += '/'
    find_env_creds = f'find {bash_path}environments/{env_name} -maxdepth 1 -mindepth 1 | xargs -I "{{}}" -P6 find "{{}}" -type f \\( -iname "*cred*.y*ml" -o -path "*/cred*" -o -path "*/Cred*" \\)  ! \\( -iname shade-*-cred.yml -o -path */shade-* \\)'
    find_config_creds = f'find {bash_path}configuration/credentials/ -type f -iname "*.y*ml" ! \\( -iname shade-*-cred.yml -o -path */shade-* \\)'
    find_env_creds_output = subprocess.run(find_env_creds, shell=True,
                                           capture_output=True, text=True, encoding='utf-8', timeout=20)
    find_config_creds_output = subprocess.run(find_config_creds, shell=True,
                                              capture_output=True, text=True, encoding='utf-8', timeout=20)
    paths = find_env_creds_output.stdout.strip().splitlines() + \
        find_config_creds_output.stdout.strip().splitlines()
    result = set([normalize_path(p) for p in paths])
    return result


def get_all_necessary_cred_files() -> set[str]:
    env_names = getenv("ENV_NAMES", None)
    if not env_names:
        logger.info(f"ENV_NAMES not set, searching for whole dir {BASE_DIR}")
        return _get_files_subprocess(BASE_DIR)
    if env_names == "env_template_test":
        logger.info("Running in env_template_test mode")
        return _get_files_subprocess(BASE_DIR)
    env_names_list = env_names.split("\n")
    cred_files = set()
    for env_name in env_names_list:
        cred_files.update(_get_files_subprocess(BASE_DIR, env_name))
    return cred_files
