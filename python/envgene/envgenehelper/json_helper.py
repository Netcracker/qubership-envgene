import json
import os
from pathlib import *

from .logger import logger

SCHEMAS_DIR = "schemas"


def find_file_in_schemas(file_name):
    files_schemas = list(Path.home().rglob("schemas/*.json"))
    for file_path in files_schemas:
        if file_name in file_path.name:
            logger.info(f"Json file path: {file_name}")
            return file_path
    return None


def openJson(filePath):
    logger.info(f"Open json file: {filePath}")
    with open(filePath, 'r') as f:
        resultJson = json.load(f)
    return resultJson


def findAllJsonsInDir(dir):
    result = []
    dirPointer = Path(dir)
    fileList = list(dirPointer.rglob("*.json"))
    for f in fileList:
        result.append(str(f))
    return list(Path(dir).rglob("schemas/*.json"))


def writeJsonToFile(file_path: str, content: dict):
    logger.debug(f"Writing json to file: {file_path}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w+') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    return
