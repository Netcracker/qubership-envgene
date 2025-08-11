
import os
from os import getenv, path
import subprocess

from .logger import logger

BASE_DIR = getenv('CI_PROJECT_DIR', os.getcwd())

# run find command to search all credential files in cur BASE_DIR
def _get_files_subprocess(full_path=''):
    cur_path = BASE_DIR if not full_path else full_path
    find_command = f"find {cur_path} \\( -iname '*cred*.y*ml' -o -path */credentials* -o -path */Сredentials* \\) -a \\( ! -path */shade-* ! -iname shade-*-cred.y*ml \\) -type f"
    command_output = subprocess.run(find_command, shell=True,
                                    capture_output=True, text=True, timeout=20)
    result = set(command_output.stdout.splitlines())
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
        cred_files.update(_get_files_subprocess(source))
    return cred_files