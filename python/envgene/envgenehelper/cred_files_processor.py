
import os
from os import getenv, path
import subprocess

from .logger import logger

BASE_DIR = getenv('CI_PROJECT_DIR', os.getcwd())
try:
    profile
except NameError:
    def profile(func):
        return func
# run find command to search all credential files in cur BASE_DIR


@profile
def _get_files_subprocess(full_path='', env_name=''):
    cur_path = BASE_DIR if not full_path else full_path

    # find_command = f"find {cur_path} \\( -iname '*cred*.y*ml' -o -path */credentials* -o -path */Сredentials* \\) -a \\( ! -path */shade-* ! -iname shade-*-cred.y*ml \\) -type f"
    find_command = f'find {cur_path}environments/{env_name} -maxdepth 1 -mindepth 1 | xargs -I "{{}}" -P4 find "{{}}" -type f \\( -iname "*cred*.y*ml" -o -path "*/cred*" \\)  ! \\( -iname shade-*-cred.yml -o -path */shade-* \\); find {full_path}configuration/credentials/ -type f -iname "*.y*ml" ! \( -iname shade-*-cred.yml -o -path */shade-* \)'
    command_output = subprocess.run(find_command, shell=True,
                                    capture_output=True, text=True, timeout=20)
    result = set(command_output.stdout.splitlines())
    return result


@profile
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
