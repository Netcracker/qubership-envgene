import os
import asyncio
import aiofiles
import yaml, json
from typing import Any, Dict, List, Tuple
import envgenehelper.logger as logger

async def read_yaml_file(path: str) -> tuple[str, dict]:
    try:
        async with aiofiles.open(path, mode='r') as f:
            content = await f.read()
        data = yaml.safe_load(content)
        return path, data
    except Exception as e:
        print(f"Failed to read {path}: {e}")
        return path, None


async def load_yaml_files_parallel(paths: List[str]) -> Dict[str, dict]:
    tasks = [read_yaml_file(path) for path in paths]
    results = await asyncio.gather(*tasks)
    return {path: content for path, content in results if content is not None}


def scandir_recursive(
    path: str,
    ns_files: List[str],
    env_name: str,
) -> None:
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            scandir_recursive(entry.path,  ns_files, env_name)
            
        elif entry.is_file(follow_symlinks=False) and entry.name.endswith((".yml", ".yaml")):
            normalized_path = os.path.normpath(entry.path)
            ns_fragment = os.path.normpath(os.path.join(env_name, "Namespaces"))
            if ns_fragment in normalized_path:
                ns_files.append(entry.path)

def scan_and_get_yaml_files(
    env_dir: str,
    env_name: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:

    ns_files = []
    scandir_recursive(env_dir,  ns_files, env_name)
    ns_files_map = asyncio.run(load_yaml_files_parallel(ns_files))
    return  ns_files_map


def openJson(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return json.loads(content)