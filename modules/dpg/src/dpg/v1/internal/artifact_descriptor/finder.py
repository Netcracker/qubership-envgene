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

def _ddcache_folder() -> Path:
    return Path(os.getenv("APP_ARTIFACTS_DIR", ".ddcache"))


def _cache_path(appver: str, is_sd: bool) -> Path:
    app, ver = appver.split(":")
    filename = "sd.yaml" if is_sd else "dd.json"
    return _ddcache_folder() / app / ver / filename


class DDCache(metaclass=Singleton):
    """In-memory + file-backed cache for app:ver -> chart specs."""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._lock = threading.Lock()

    def get(self, key: str, file_path: Path | None = None) -> dict | None:
        with self._lock:
            if (cached := self._cache.get(key)) is not None:
                logging.debug(f"DDCache: memory hit for key=`{key}`")
                return cached

        if file_path is not None and utils.is_file_path(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            with self._lock:
                self._cache[key] = content
            logging.debug(f"DDCache: file hit for key=`{key}` from `{file_path}`")
            return content

        return None

    def set(self, key: str, value: dict, file_path: Path | None = None) -> None:
        with self._lock:
            self._cache[key] = value
            logging.debug(f"DDCache: set key=`{key}`")

            if file_path is not None and not utils.is_file_path(file_path):
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(json.dumps(value), encoding="utf-8")


class DDFinder(metaclass=Singleton):
    def __init__(self, data_provider: DataProviderInterface = None):
        self.__cache = DDCache()
        self.__data_provider = data_provider

    def get(self, app_ver: str, **kwargs) -> Optional[dict]:
        if self.__data_provider is None:
            self.__data_provider = get_data_provider(**kwargs)

        if utils.is_file_path(app_ver):
            cached = self.__cache.get(app_ver)
            if cached is not None:
                return cached
            with open(app_ver, encoding="utf-8") as f:
                content = json.load(f)
            self.__cache.set(app_ver, content)
            return content

        name, version = app_ver.split(":")
        appdef = self.__data_provider.get_app_def(application=name)
        file_path = _cache_path(app_ver, is_sd=appdef.solution_descriptor)

        cached = self.__cache.get(app_ver, file_path=file_path)
        if cached is not None:
            return cached

        reginfo = self.__data_provider.get_registry_info(registry=appdef.registry)
        json_url, *_ = ArtifactoryUtils.search_artifacts_on_registry(
            app_name=name, app_version=version, app_info=appdef,
            artifact_extension='json', registry_info=reginfo,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            json_file_path = ArtifactoryUtils.download_file_from_artifactory(temp_dir, json_url, reginfo)
            with open(json_file_path, 'r') as f:
                content = json.load(f)

        self.__cache.set(app_ver, content, file_path=file_path)
        return content
