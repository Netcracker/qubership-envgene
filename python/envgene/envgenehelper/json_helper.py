import json
import os
import pathlib
from os import path, makedirs

from .logger import logger

SCHEMAS_DIR  = "schemas"

def findFileInSchemas(file_name):
    schemas_dir = pathlib.Path(os.getcwd()).rglob("schemas")[0]
    logger.info(f"Schemas_dir path: {schemas_dir}")
    return list(schemas_dir.rglob("*.json"))

def openJson(filePath):
    logger.info(f"Open json file: {filePath}")
    with open(filePath, 'r') as f:
        resultJson = json.load(f)
    return resultJson


def findAllJsonsInDir(dir):
    result = []
    dirPointer = pathlib.Path(dir)
    fileList = list(dirPointer.rglob("*.json"))
    for f in fileList:
        result.append(str(f))
    return result


def writeJsonToFile(file_path: str, content: dict):
    logger.debug(f"Writing json to file: {file_path}")
    makedirs(path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w+') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    return
