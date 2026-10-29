import copy
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable

from envgene_shared.crypto.crypt import decrypt_bytes, encrypt_bytes, encryption_rule, get_all_necessary_cred_files
from envgene_shared.crypto.sops_handler import is_encrypted_SOPS_text
from envgene_shared.utils.business_utils import get_schema_dir
from envgene_shared.utils.crypt_utils import is_effective_set_cred_file
from envgene_shared.utils.yaml_utils import dumpYamlToStr, get_empty_yaml, make_quotes_for_strings, readYaml, \
    remove_cred_yaml_comments, sortYaml


class CredStore:
    def __init__(self, files: Iterable[str]):
        self._lock = threading.Lock()
        self._snapshot = {}
        self._decrypted_snapshot = {}
        self._decrypted = {}
        self._headers = {}
        for file in files:
            if os.path.isfile(file):
                self._snapshot[self._key(file)] = Path(file).read_bytes()

    @staticmethod
    def _key(path):
        return Path(path).resolve()

    def _lazy_decrypt(self, key):
        obj = decrypt_bytes(self._snapshot[key], key)
        with self._lock:
            self._decrypted_snapshot.setdefault(key, copy.deepcopy(obj))
            return self._decrypted.setdefault(key, obj)

    def get(self, path, allow_default=False) -> dict:
        key = self._key(path)
        with self._lock:
            if key in self._decrypted:
                return self._decrypted[key]
            if key not in self._snapshot and key.is_file():
                self._snapshot[key] = key.read_bytes()
        if key not in self._snapshot:
            if allow_default:
                return get_empty_yaml()
            raise FileNotFoundError(f"{key} is not in the cred store and not on disk")
        return self._lazy_decrypt(key)

    def exists(self, path) -> bool:
        key = self._key(path)
        with self._lock:
            return key in self._decrypted or key.is_file()

    def list(self, dir_path) -> list[Path]:
        root = self._key(dir_path)
        with self._lock:
            keys = set(self._decrypted) | set(self._snapshot)
            return sorted(key for key in keys if key.is_relative_to(root) and key.suffix in (".yml", ".yaml")
                          and (key in self._decrypted or key.is_file()))

    def put(self, path, obj: dict, header_text: str = "") -> None:
        with self._lock:
            self._decrypted[self._key(path)] = obj
            if header_text:
                self._headers[self._key(path)] = header_text

    def _is_changed(self, key, obj):
        if key not in self._snapshot:
            return True
        if key not in self._decrypted_snapshot:
            if is_effective_set_cred_file(key):
                return True
            self._lazy_decrypt(key)
        return obj != self._decrypted_snapshot[key]

    def _sops_edit_base(self, key, obj, is_es):
        old_data = self._snapshot.get(key)
        if old_data is None:
            return None
        old_text = old_data.decode("utf-8")
        if not is_encrypted_SOPS_text(old_text):
            return None
        if is_es and readYaml(old_text)["sops"].get("encrypted_regex") != encryption_rule(obj, key, False)[1]:
            return None
        return old_data

    def _write(self, key, obj):
        is_es = is_effective_set_cred_file(key)
        if not is_es:
            obj = sortYaml(obj, get_schema_dir() / "credential.schema.json", False, validate=False)
            make_quotes_for_strings(obj)
            remove_cred_yaml_comments(obj)
        text = "" if is_es and not obj else dumpYamlToStr(obj)
        data = encrypt_bytes(text.encode("utf-8"), key, old_data=self._sops_edit_base(key, obj, is_es),
                             validate=False)
        header_text = self._headers.get(key)
        if header_text and not data.startswith(b"#"):
            data = ("# " + header_text.replace("\n", "\n# ") + "\n").encode("utf-8") + data
        os.makedirs(key.parent, exist_ok=True)
        key.write_bytes(data)

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
