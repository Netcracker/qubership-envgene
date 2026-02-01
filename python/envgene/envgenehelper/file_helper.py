import os
import glob
import re
import shutil
import tarfile
import zipfile
from typing import Callable
from pathlib import Path

from .logger import logger


def extractNameFromFile(filePath):
    return Path(filePath).stem


def extractNameWithExtensionFromFile(filePath):
    return Path(filePath).name


def extractNameFromDir(dirName):
    return Path(dirName).stem


def check_dir_exists(dir_path):
    dir = Path(dir_path)
    return dir.exists() and dir.is_dir()


def identify_yaml_extension(file_path: str) -> str:
    """
    Takes file_path and check if it exists either with .yml or .yaml extension and returns existing file
    """
    file_root, _ = os.path.splitext(file_path)
    possible_files = [file_root + ext for ext in ['.yml', '.yaml']]
    for file in possible_files:
        if os.path.isfile(file):
            return file
    raise FileNotFoundError(f"Neither of these files: {possible_files} exist.")


def find_all_sub_dir(dir_path):
    return os.walk(dir_path)


def check_file_exists(file_path):
    file = Path(file_path)
    return file.exists() and file.is_file()


def check_dir_exist_and_create(dir_path):
    logger.debug(f'Checking that dir exists or create dir in path: {dir_path}')
    os.makedirs(dir_path, exist_ok=True)


def delete_dir(path):
    try:
        shutil.rmtree(path)
    except:
        logger.warning(f'{path} directory does not exist')


def is_glob(path: str) -> bool:
    return any(ch in str(path) for ch in ["*", "?", "["])


def is_source_path_valid(source_path: Path, target_path: Path) -> bool:
    if not source_path.exists():
        logger.info(f"Path {source_path} doesn't exist. Skipping...")
        return False
    if source_path == target_path:
        logger.info(f"Trying to copy {source_path} to itself ({target_path}). Skipping...")
        return False
    return True


def _is_glob(path: str) -> bool:
    return any(ch in str(path) for ch in ["*", "?", "["])


def copy_path(source_path: str, target_dir: str):
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    if _is_glob(source_path):
        matches = sorted(glob.glob(source_path))
        if not matches:
            return
        for match in matches:
            _copy_single(Path(match), target_dir, is_from_glob=True)
    else:
        _copy_single(Path(source_path), target_dir, is_from_glob=False)


def _copy_single(src: Path, target_dir: Path, is_from_glob: bool):
    is_source_path_valid(src, target_dir)

    if src.is_dir():
        for item in src.rglob("*"):
            rel = item.relative_to(src.parent if is_from_glob else src)
            dst = target_dir / rel
            if item.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst)
    elif src.is_file():
        dst = target_dir / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def move_path(source_path, target_path):
    if glob.glob(source_path):
        logger.info(f'Moving from {source_path} to {target_path}')
        logger.debug(f'Checking target path {target_path} exists: {os.path.exists(target_path)}')
        if not os.path.exists(target_path):
            if os.path.isdir(target_path):
                dirPath = target_path
            else:
                dirPath = os.path.dirname(target_path)
            logger.debug(f'Creating dir {dirPath}')
            os.makedirs(dirPath, exist_ok=True)
        exit_code = os.system(f"mv -f {source_path} {target_path}")
        if (exit_code):
            logger.error(f"Error during Moving from {source_path} to {target_path}")
            exit(1)
    else:
        logger.info(f"Path {source_path} doesn't exist. Skipping...")


def openFileAsString(filePath):
    with open(filePath, 'r') as f:
        result = f.read()
    return result


def deleteFile(filePath):
    os.remove(filePath)


def deleteFileIfExists(filePath):
    if check_file_exists(filePath):
        os.remove(filePath)


def writeToFile(filePath, contents):
    os.makedirs(os.path.dirname(filePath), exist_ok=True)
    with open(filePath, 'w+') as f:
        f.write(contents)
    return


def getAbsPath(path):
    return os.path.abspath(path)


def getRelPath(path, start_path=None):
    if start_path:
        return os.path.relpath(path, start_path)
    return os.path.relpath(path, os.getenv('CI_PROJECT_DIR'))


def get_parent_dir_for_dir(dirPath):
    path = Path(dirPath)
    return str(path.parent.absolute())


def getDirName(filePath):
    return os.path.dirname(filePath)


def getParentDirName(filePath):
    return os.path.dirname(getDirName(filePath))


def get_files_with_filter(path_to_filter: str, filter: Callable[[str], bool]) -> set[str]:
    matching_files = set()
    for root, _, files in os.walk(path_to_filter):
        for file in files:
            filepath = os.path.join(root, file)
            if filter(filepath):
                matching_files.add(filepath)
    return matching_files


def findAllFilesInDir(dir, pattern, notPattern="", additionalRegexpPattern="", additionalRegexpNotPattern=""):
    result = []
    dirPointer = Path(dir)
    fileList = list(dirPointer.rglob("*.*"))
    for f in fileList:
        result.append(str(f))
    return findFiles(result, pattern, notPattern, additionalRegexpPattern, additionalRegexpNotPattern)


def findFiles(fileList: list[Path], pattern, notPattern="", additionalRegexpPattern="", additionalRegexpNotPattern=""):
    result = []
    for filePath in fileList:
        # this ensures that pattern matching works correctly on both Windows (\) and Unix (/)
        file_path_posix = Path(filePath).as_posix()
        if (
                pattern in file_path_posix
                and (notPattern == "" or notPattern not in file_path_posix)
                and (additionalRegexpPattern == "" or re.match(additionalRegexpPattern, file_path_posix))
                and (additionalRegexpNotPattern == "" or not re.match(additionalRegexpNotPattern, file_path_posix))
        ):
            result.append(filePath)
            logger.debug(
                f"Path {filePath} match pattern: {pattern} or notPattern: {notPattern} or additionalPattern: {additionalRegexpPattern}")
        else:
            logger.debug(
                f"Path {filePath} doesn't match pattern: {pattern} or notPattern: {notPattern} or additionalPattern: {additionalRegexpPattern}")
    return result


def get_all_files_in_dir(dir):
    dir_path = Path(dir)
    result = []
    for item in dir_path.rglob("*"):
        if item.is_file():
            result.append(str(item.relative_to(dir_path)))
    return result


def ensure_directory(path: Path, mode: int):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
    else:
        logger.info(f"Directory already exists: {path}")
    path.chmod(mode)


def unpack_archive(src: str, dest: str):
    os.makedirs(dest, exist_ok=True)
    if src.endswith(".zip"):
        with zipfile.ZipFile(src, "r") as z:
            z.extractall(dest)
        logger.info(f"Unpacked zip archive {src} to {dest}")
    elif src.endswith((".tar.gz", ".tgz", ".tar")):
        with tarfile.open(src, "r:*") as t:
            t.extractall(dest)
        logger.info(f"Unpacked tar archive {src} to {dest}")
    else:
        raise ValueError(f"Unsupported archive format: {src}")


def cleanup_dir(path: str):
    dir_path = Path(path)

    if dir_path.exists() and dir_path.is_dir():
        shutil.rmtree(dir_path)

    dir_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directory has been recreated: {path}")
