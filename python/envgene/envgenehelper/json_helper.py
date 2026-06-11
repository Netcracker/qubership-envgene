import json
import os
import pathlib

from .logger import logger

SCHEMAS_DIR  = "schemas"

def findFileInSchemas(file_name):
    schemas_dir = pathlib.Path("/").rglob("schemas")
    logger.info(f"Schemas_dir path: {schemas_dir}")
    for dir in schemas_dir:
        for file_path in list(dir.rglob("*.json")):
            if file_name in file_path:
                return file_path
    return None


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
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w+') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    return
