import json
import os
import pathlib
from os import path, makedirs

from .logger import logger

SCHEMAS_DIR = "/schemas"

def openJson(filePath):
    logger.info(f"Open json file: {filePath}")
    for path in pathlib.Path("/").rglob("schemas"):
        logger.info(f"{SCHEMAS_DIR} path: {path}")
        for root, dirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                logger.info(full_path)
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
