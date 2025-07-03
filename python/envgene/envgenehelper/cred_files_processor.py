import chunk
import os
import re
from os import cpu_count, getenv, path
import threading
from time import perf_counter
from traceback import TracebackException
from typing import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from envgenehelper.business_helper import getenv_with_error

from .config_helper import get_envgene_config_yaml

from .file_helper import get_files_with_filter
from .logger import logger


class FileProcessor:
    def __init__(self, config) -> None:
        self.BASE_DIR = getenv('CI_PROJECT_DIR', os.getcwd())
        self.VALID_EXTENSIONS = ('.yml', '.yaml')
        self.TARGET_WORDS = ['credentials', 'creds']
        self.TARGET_DIR_REGEX = ['credentials', 'Credentials']
        self.TARGET_PARENT_DIRS = ['/configuration', '/environments']
        self.IGNORE_DIR = ['/shades-', '/Namespaces',
                           '/Profiles', '/parameters']
        self.ALLOWED_DIR_PARTS = self.TARGET_PARENT_DIRS + self.TARGET_DIR_REGEX
        self.cpu_count = 4

    @staticmethod
    def _chunks(lst, cpu_count):
        chunk_size = round(len(lst)/cpu_count)
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

    @staticmethod
    def _path_walk(paths_to_filter: list[str], filter: Callable[[str], bool]) -> set[str]:
        matching_files = set()
        for path_to_filter in paths_to_filter:
            for root, _, files in os.walk(path_to_filter):
                for file in files:
                    filepath = os.path.join(root, file)
                    if filter(filepath):
                        matching_files.add(filepath)
        return matching_files

    def _get_files_with_filter(self, path_to_filter: str, filter: Callable[[str], bool]) -> set[str]:
        matching_files = set()
        for root, dirs, files in os.walk(path_to_filter):
            if round(len(dirs)/self.cpu_count) >= 2:
                future_to_paths = {}
                paths = [os.path.join(root, d) for d in dirs]
                chunks = FileProcessor._chunks(paths, self.cpu_count)
                with ThreadPoolExecutor(max_workers=self.cpu_count) as executor:
                    for chunk in chunks:
                        future = executor.submit(
                            FileProcessor._path_walk, chunk, filter)
                        future_to_paths[future] = chunk
                    for future in as_completed(future_to_paths):
                        try:
                            result = future.result()
                            matching_files.update(result)
                        except Exception as e:
                            print(f"Ошибка при обработке: {e}")
                return matching_files
            for file in files:
                filepath = os.path.join(root, file)
                if filter(filepath):
                    matching_files.add(filepath)
        return matching_files

    def is_cred_file(self, fp: str) -> bool:
        name = os.path.basename(fp)
        name_without_ext = os.path.splitext(name)[0]
        parent_dirs = os.path.dirname(fp)
        # if file extention match VALID_EXTENTIONS regex
        if not name.endswith(self.VALID_EXTENSIONS):
            return False
        if not any(sub in fp for sub in self.TARGET_PARENT_DIRS):
            return False
        if any(sub in fp for sub in self.IGNORE_DIR):
            return False
        # if file name is matches name_without_ext or file dir matches TARGET_DIR_REGEX
        if any(k in name_without_ext for k in self.TARGET_WORDS) or any(k in parent_dirs for k in self.TARGET_DIR_REGEX):
            return True
        return False

    def get_all_necessary_cred_files(self) -> set[str]:
        env_names = getenv("ENV_NAMES", None)
        if not env_names:
            logger.info("ENV_NAMES not set, running in test mode")
            return self._get_files_with_filter(self.BASE_DIR, self.is_cred_file)
        if env_names == "env_template_test":
            logger.info("Running in env_template_test mode")
            return self._get_files_with_filter(self.BASE_DIR, self.is_cred_file)
        env_names_list = env_names.split("\n")

        sources = set()
        sources.add("configuration")
        sources.add(path.join("environments", "credentials"))

        for env_name in env_names_list:
            cluster, env = env_name.strip().split("/")
            # relative to BASE_DIR/<cluster_name>/
            env_specific_source_locations = [
                "credentials", "cloud-passport", "cloud-passports", env]
            for location in env_specific_source_locations:
                sources.add(path.join("environments", cluster, location))

        cred_files = set()
        for source in sources:
            source = path.join(self.BASE_DIR, source)
            if not path.exists(source):
                continue
            cred_files.update(get_files_with_filter(source, self.is_cred_file))
        return cred_files
