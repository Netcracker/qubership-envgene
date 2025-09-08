import os, time
import asyncio
from pathlib import Path
import aiofiles
import yaml, json
from typing import Any, Dict, List, Tuple, Set
from utils.error_constants import  *
from utils.search_utils import trim_path_from_environments
import envgenehelper.logger as logger
from envgenehelper.errors import  ValidationError
try:
    logger.info("Loading CLoader")
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


async def read_yaml_file(path: str) -> tuple[str, dict]:
    try:
        async with aiofiles.open(path, mode='r') as f:
            content = await f.read()
        data = yaml.load(content, Loader=Loader)
        #data = yaml.safe_load(content)
        return path, data
    except Exception as e:
         raise ValidationError(ErrorMessages.INVALID_YAML_FILE.format(file=path, e=str(e)), ErrorCodes.INVALID_CONFIG_CODE)


async def load_yaml_files_parallel(paths: List[str]) -> Dict[str, dict]:
    tasks = [read_yaml_file(path) for path in paths]
    results = await asyncio.gather(*tasks)
    return {path: content for path, content in results if content is not None}


def scandir_recursive_optimized(
    path: str,
    ns_files: List[str],
    definition_files: List[str],
    env_creds_files: List[str]
) -> None:
    # Pre-compile path parts for faster lookups
    yaml_extensions = ('.yml', '.yaml')
    target_filenames = {'env-definition.yml', 'credentials.yml'}

    try:
        with os.scandir(path) as entries:
            dirs_to_process = []

            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    dirs_to_process.append(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    name = entry.name

                    # Quick filename check before path processing
                    if name.endswith(yaml_extensions):
                        entry_path = entry.path

                        # Use pathlib for more efficient path operations
                        path_obj = Path(entry_path)
                        path_parts = path_obj.parts

                        # More efficient categorization
                        if "Namespaces" in path_parts:
                            ns_files.append(entry_path)
                        elif name == "env-definition.yml" and "Inventory" in path_parts:
                            definition_files.append(entry_path)
                        elif name == "credentials.yml" and "Credentials" in path_parts:
                            env_creds_files.append(entry_path)

            # Recursively process directories
            for dir_path in dirs_to_process:
                scandir_recursive_optimized(dir_path, ns_files, definition_files, env_creds_files)

    except (OSError, PermissionError):
        # Skip directories we can't access instead of crashing
        pass

def scandir_recursive(
    path: str,
    ns_files: Set[str],
    definition_files: Set[str],
    env_creds_files: Set[str]
) -> None:
    yaml_extensions = ('.yml', '.yaml')

    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            scandir_recursive(entry.path,  ns_files, definition_files, env_creds_files)
        elif entry.is_file(follow_symlinks=False) and entry.name.endswith(yaml_extensions):
            path_obj = Path(entry.path)
            path_parts = path_obj.parts

            if "Namespaces" in path_parts:
                ns_files.add(entry.path)
            elif entry.name == "env_definition.yml" and "Inventory" in path_parts:
                definition_files.add(entry.path)

            elif entry.name == "credentials.yml" and "Credentials" in path_parts:
                env_creds_files.add(entry.path)

def scan_and_get_yaml_files(
    env_dir: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    entity_files = set()
    env_def_files = set()
    env_creds_files = set()
    scandir_recursive(env_dir,  entity_files, env_def_files, env_creds_files)
    entity_files_map = asyncio.run(load_yaml_files_parallel(entity_files))
    env_files_map = asyncio.run(load_yaml_files_parallel(env_def_files))
    return  entity_files_map, env_files_map, env_creds_files


def openJson(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return json.loads(content)

def write_cred_file_path(cred_paths:  List[str], env_dir: str):
    with open(f"{env_dir}/credfilestoupdate.yml", "w") as f:
        for cred_path in cred_paths:
            f.write(f"{trim_path_from_environments(cred_path)}\n")
