import requests
import tempfile
import logging
import os
import json
import threading
from pathlib import Path
from typing import Optional

import dpg.v1.utils as utils
from dpg.v1.utils.data_provider import DataProviderInterface
from dpg.v1.utils.singleton import Singleton
from dpg.v1.utils.registry import ArtifactoryUtils, RegistryInfo

DDCACHE_FOLDER = Path(os.getcwd(), ".ddcache")
DDCACHE_TRANSFORMER_FILENAME = lambda appver: appver.replace(":", "-") + ".json"

DDCACHE_FOLDER.mkdir(parents=True, exist_ok=True)

class DDCache(metaclass=Singleton):
    """In-memory cache for app:ver -> chart specs."""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._lock = threading.Lock()

    def get(self, app_ver: str) -> dict | None:
        with self._lock:
            cached = self._cache.get(app_ver)
            if cached is not None:
                logging.debug(f"DDCache: hit dd content cache for key=`{app_ver}`")
                return cached

        path = DDCACHE_FOLDER / DDCACHE_TRANSFORMER_FILENAME(app_ver)
        if utils.is_file_path(path):
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            self.__write_key(app_ver, content, withfile=False)
            logging.debug(f"DDCache: hit dd content cache for key=`{app_ver}` from `{path}`")

        with self._lock:
            return self._cache.get(app_ver)

    def set(self, app_ver: str, value: dict) -> None:
        self.__write_key(app_ver, value, withfile=True, force=True)

    def __write_key(self, key: str, value: dict, force: bool = False, withfile: bool = False) -> dict:
        with self._lock:
            if not force and key in self._cache:
                return self._cache[key]

            logging.debug(f"DDCache: setting dd content cache to key=`{key}`")
            self._cache[key] = value

            path = DDCACHE_FOLDER / DDCACHE_TRANSFORMER_FILENAME(key)
            if withfile and not utils.is_file_path(path):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(value))

        return self._cache[key]

class DDFinder(metaclass=Singleton):
    def __init__(self, data_provider: DataProviderInterface = None):
        self.__cache = DDCache()
        self.__data_provider = data_provider

    def get(self, app_ver: str, **kwargs) -> Optional[dict]:
        if self.__data_provider is None:
            self.__data_provider = get_data_provider(**kwargs)

        cached = self.__cache.get(app_ver)
        if cached is not None:
            return cached

        if utils.is_file_path(app_ver):
            with open(app_ver, encoding="utf-8") as f:
                content = json.load(f)
                self.__cache.set(app_ver, content)
                return content

        name, version = app_ver.split(":")
        appdef = self.__data_provider.get_app_def(application=name)
        reginfo = self.__data_provider.get_registry_info(registry=appdef.registry)

        json_url, *_ = ArtifactoryUtils.search_artifacts_on_registry(app_name=name, app_version=version, app_info=appdef, artifact_extension='json', registry_info=reginfo)

        with tempfile.TemporaryDirectory() as temp_dir:
            json_file_path = ArtifactoryUtils.download_file_from_artifactory(temp_dir, json_url, reginfo)
            with open(json_file_path, 'r') as f:
                content = json.load(f)

        self.__cache.set(app_ver, content)
        return content

