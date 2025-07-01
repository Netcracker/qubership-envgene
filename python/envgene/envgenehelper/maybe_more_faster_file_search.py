import os
import re
from os import getenv, path
from time import perf_counter
from typing import Callable

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
        self.IGNORE_DIR = ['/shades-']
        self.ALLOWED_DIR_PARTS = self.TARGET_PARENT_DIRS + self.TARGET_DIR_REGEX

    def _get_files_with_filter(self, path_to_filter: str, filter: Callable[[str], bool]) -> set[str]:
        matching_files = set()
        for root, dirs, files in os.walk(path_to_filter):
            dirs[:] = [d for d in dirs if any(
                part in os.path.join(root, d) for part in self.ALLOWED_DIR_PARTS)]
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
