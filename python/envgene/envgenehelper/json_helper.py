import json
import os
from pathlib import *

from .logger import logger


def find_file_in_schemas(file_name):
    for file_path in list(Path('/').rglob(file_name)):
        logger.info(f"Json file path: {str(file_path)}")
        return str(file_path)
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
