import copy
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from envgene_shared.crypto.crypt import decrypt_bytes, encrypt_bytes, get_all_necessary_cred_files
from envgene_shared.crypto.sops_handler import is_encrypted_SOPS_text
from envgene_shared.utils.business_utils import get_schema_dir
from envgene_shared.utils.constants import SOPS_ID
from envgene_shared.utils.crypt_utils import analyze_cred_file, get_crypt_backend, is_effective_set_cred_file
from envgene_shared.utils.yaml_utils import dumpYamlToStr, get_empty_yaml, make_quotes_for_strings, readYaml, \
    remove_cred_yaml_comments, sortYaml


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
        self._decrypted = {}
        self._put = set()
        self._headers = {}
        for file in files:
            if os.path.isfile(file):
                self._original[self._key(file)] = Path(file).read_bytes()

    @staticmethod
    def _key(path):
        return str(Path(path).resolve())

    def _decrypt_original(self, key):
        obj = decrypt_bytes(self._original[key], key)
        with self._lock:
            self._decrypted_original.setdefault(key, copy.deepcopy(obj))
            return self._decrypted.setdefault(key, obj)

    def get(self, path, allow_default=False) -> dict:
        key = self._key(path)
        with self._lock:
            if key in self._decrypted:
                return self._decrypted[key]
            if key not in self._original and os.path.isfile(key):
                self._original[key] = Path(key).read_bytes()
        if allow_default and key not in self._original:
            return get_empty_yaml()
        return self._decrypt_original(key)

    def put(self, path, obj: dict, header_text: str = "") -> None:
        with self._lock:
            self._decrypted[self._key(path)] = obj
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

    def _sops_edit_base(self, key, obj, is_es):
        old_data = self._original.get(key)
        if get_crypt_backend() != SOPS_ID or old_data is None:
            return None
        old_text = old_data.decode("utf-8")
        if not is_encrypted_SOPS_text(old_text):
            return None
        if is_es and _encrypted_literal_keys(readYaml(old_text)) != analyze_cred_file(obj)[0]:
            return None
        return old_data

    def _write(self, key, obj):
        path = Path(key)
        is_es = is_effective_set_cred_file(key)
        if not is_es:
            obj = sortYaml(obj, get_schema_dir() / "credential.schema.json", False, validate=False)
            make_quotes_for_strings(obj)
            remove_cred_yaml_comments(obj)
        data = encrypt_bytes(dumpYamlToStr(obj).encode("utf-8"), key, old_data=self._sops_edit_base(key, obj, is_es),
                             validate=False)
        header_text = self._headers.get(key)
        if header_text and not data.startswith(b"#"):
            data = ("# " + header_text.replace("\n", "\n# ") + "\n").encode("utf-8") + data
        os.makedirs(path.parent, exist_ok=True)
        path.write_bytes(data)

    def write_changed(self) -> None:
        with self._lock:
            decrypted = dict(self._decrypted)
        changed = {key: obj for key, obj in decrypted.items() if self._is_changed(key, obj)}
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


def current_cred_store() -> CredStore:
    if _open_store is None:
        raise RuntimeError("Cred store is not open: it exists only inside the pipeline steps before git commit")
    return _open_store
