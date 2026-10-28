import copy
import os
import shutil
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from envgene_shared.crypto.crypt import (
    CRYPT_FUNCTIONS, decrypt_file, encrypt_file, get_all_necessary_cred_files, is_encrypted_SOPS
)
from envgene_shared.utils.business_utils import get_schema_dir
from envgene_shared.utils.constants import SOPS_ID
from envgene_shared.utils.crypt_utils import analyze_cred_file, get_crypt_backend, is_effective_set_cred_file
from envgene_shared.utils.file_utils import writeToFile
from envgene_shared.utils.yaml_utils import make_quotes_for_strings, openYaml, remove_cred_yaml_comments, \
    sortYaml, writeYamlToFile


def _encrypted_literal_keys(value, keys=None):
    keys = set() if keys is None else keys
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "sops":
                continue
            if isinstance(child, str) and child.startswith("ENC["):
                keys.add(key)
            else:
                _encrypted_literal_keys(child, keys)
    elif isinstance(value, list):
        for child in value:
            _encrypted_literal_keys(child, keys)
    return keys


class CredStore:
    def __init__(self, files: Iterable[str]):
        self._lock = threading.Lock()
        self._original = {}
        self._decrypted_original = {}
        self._objects = {}
        self._put = set()
        self._headers = {}
        for file in files:
            if os.path.isfile(file):
                self._original[self._key(file)] = Path(file).read_bytes()

    @staticmethod
    def _key(path):
        return str(Path(path).resolve())

    def knows(self, path) -> bool:
        key = self._key(path)
        return key in self._original or key in self._objects

    def _decrypt_original(self, key):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_file = Path(tmp) / Path(key).name
            tmp_file.write_bytes(self._original[key])
            obj = decrypt_file(tmp_file, in_place=False)
        with self._lock:
            self._decrypted_original.setdefault(key, copy.deepcopy(obj))
            return self._objects.setdefault(key, obj)

    def get(self, path) -> dict:
        key = self._key(path)
        with self._lock:
            if key in self._objects:
                return self._objects[key]
        return self._decrypt_original(key)

    def put(self, path, obj: dict, header_text: str = "") -> None:
        with self._lock:
            self._objects[self._key(path)] = obj
            self._put.add(self._key(path))
            if header_text:
                self._headers[self._key(path)] = header_text

    def _is_changed(self, key, obj):
        if key not in self._original or (key in self._put and not os.path.isfile(key)):
            return True
        if key not in self._decrypted_original:
            if is_effective_set_cred_file(key):
                return True
            self._decrypt_original(key)
        return obj != self._decrypted_original[key]

    def _write(self, key, obj):
        path = Path(key)
        os.makedirs(path.parent, exist_ok=True)
        is_es = is_effective_set_cred_file(key)
        if not is_es:
            obj = sortYaml(obj, get_schema_dir() / "credential.schema.json", False, validate=False)
            make_quotes_for_strings(obj)
            remove_cred_yaml_comments(obj)
        with tempfile.TemporaryDirectory() as tmp:
            work_file = Path(tmp) / ("effective-set" if is_es else "Credentials") / path.name
            writeYamlToFile(work_file, obj)
            encrypt_kwargs = {}
            old_bytes = self._original.get(key)
            if get_crypt_backend() == SOPS_ID and old_bytes is not None:
                old_file = Path(tmp) / "old" / path.name
                os.makedirs(old_file.parent)
                old_file.write_bytes(old_bytes)
                if is_encrypted_SOPS(old_file) and (
                        not is_es or _encrypted_literal_keys(openYaml(old_file)) == analyze_cred_file(obj)[0]):
                    encrypt_kwargs = {"minimize_diff": True, "old_file_path": str(old_file)}
            encrypt_file(work_file, in_place=True, load_result=False, validate=False, **encrypt_kwargs)
            shutil.copyfile(work_file, path)
        header_text = self._headers.get(key)
        if header_text:
            content = path.read_text(encoding="utf-8")
            if not content.startswith("#"):
                writeToFile(path, "# " + header_text.replace("\n", "\n# ") + "\n" + content)

    def write_changed(self) -> None:
        with self._lock:
            objects = dict(self._objects)
        changed = {key: obj for key, obj in objects.items() if self._is_changed(key, obj)}
        if not changed:
            return
        with ThreadPoolExecutor(max_workers=min(len(changed), os.cpu_count() or 2)) as executor:
            for future in [executor.submit(self._write, key, obj) for key, obj in changed.items()]:
                future.result()


_open_store = None


@contextmanager
def open_cred_store():
    global _open_store
    if _open_store is not None:
        raise RuntimeError("Cred store is already open")
    _open_store = CredStore(get_all_necessary_cred_files())
    try:
        yield _open_store
        _open_store.write_changed()
    finally:
        _open_store = None


def current_cred_store() -> CredStore | None:
    return _open_store
