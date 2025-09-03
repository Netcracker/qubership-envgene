from os import path, makedirs
import json
import pathlib
from .file_helper import findFiles
from .logger import logger

def openJson(filePath):
    logger.debug(f"Open json file: {filePath}")
    with open(filePath, 'r') as f:
        resultJson = json.load(f)
    return resultJson

def findAllJsonsInDir(dir) :
    result = []
    dirPointer = pathlib.Path(dir)
    fileList = list(dirPointer.rglob("*.json"))
    for f in fileList :
        result.append(str(f))
    return result

def findJsons(dir, pattern, notPattern="", additionalRegexpPattern="", additionalRegexpNotPattern="") :
    fileList = findAllJsonsInDir(dir)
    return findFiles(fileList, pattern, notPattern, additionalRegexpPattern, additionalRegexpNotPattern)

def writeJsonToFile(file_path: str, content: dict):
    logger.debug(f"Writing json to file: {file_path}")
    makedirs(path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w+') as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
    return
