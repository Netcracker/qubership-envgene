import os
from typing import Callable
from pathlib import Path
import json
import pathlib

from envgene_shared.utils.logger import logger
from envgene_shared.utils.constants import *

def openJson(filePath):
    logger.debug(f"Open json file: {filePath}")
    with open(filePath, 'r') as f:
        resultJson = json.load(f)
    return resultJson


def writeToFile(filePath, contents):
    os.makedirs(os.path.dirname(filePath), exist_ok=True)
    with open(filePath, 'w+') as f:
        f.write(contents)
    return


def check_file_exists(file_path):
    file = Path(file_path)
    return file.exists() and file.is_file()

def getRelPath(path, start_path=None):
    if start_path:
        return os.path.relpath(path, start_path)
    return os.path.relpath(path, os.getenv('CI_PROJECT_DIR'))


def get_files_with_filter(path_to_filter: str, filter: Callable[[str], bool]) -> set[str]:
    matching_files = set()
    for root, _, files in os.walk(path_to_filter):
        for file in files:
            filepath = os.path.join(root, file)
            if filter(filepath):
                matching_files.add(filepath)
    return matching_files


def is_cred_file(fp: str) -> bool:
    file_path = Path(fp)
    name = file_path.name
    name_without_ext = file_path.stem
    parent_dirs = file_path.parent
    if not VALID_EXTENSIONS.search(name):
        return False
    if not any(part.lower() in TARGET_PARENT_DIRS for part in parent_dirs.parts):
        return False
    if TARGET_REGEX.search(name_without_ext) or any(
        part.lower() in TARGET_DIRS for part in parent_dirs.parts
    ):
        return True
    
    return False