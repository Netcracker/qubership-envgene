import hashlib
import os
import pickle
from contextlib import contextmanager
from fnmatch import fnmatchcase
from pathlib import Path

from ruyaml import CommentedMap

from envgene_shared.utils.business_utils import get_envgene_config_yaml
from envgene_shared.utils.file_utils import is_cred_file, writeToFile
from envgene_shared.utils.logger import logger
from envgene_shared.utils.yaml_utils import openYaml, remove_cred_yaml_comments, remove_empty_list_comments

from .business_helper import NamespaceFile
from .yaml_helper import dumpYamlToStr, make_quotes_for_strings, normalize_comments, sortYaml

# An env-specific Resource Profile from Inventory is put into the store only to be read later.
# It is an input file of the user, so flush() must not write it back.
NEVER_WRITTEN_DIRS = ("Inventory",)
YAML_EXTENSIONS = (".yml", ".yaml")

def profile_cache_dir() -> Path | None:
    root = os.environ.get("CI_PROJECT_DIR")
    if not root or str(get_envgene_config_yaml().get("cache", {}).get("enabled", True)).lower() != "true":
        return None
    return Path(root) / ".shared" / "profile-cache"


def _key(path) -> Path:
    return Path(path).resolve()


def _match(parts: tuple, pattern: tuple) -> bool:
    return len(parts) == len(pattern) and all(fnmatchcase(part, name) for part, name in zip(parts, pattern))


class CurrentEnvInstanceStore:
    def __init__(self, env_dir):
        self.env_dir = _key(env_dir)
        self._objects = {}
        self._to_write = set()
        self._beautify = {}

    def _relative(self, key: Path) -> Path | None:
        if not key.is_relative_to(self.env_dir):
            return None
        return key.relative_to(self.env_dir)

    def put(self, path, obj):
        key = _key(path)
        logger.debug(f"Object store put: {key}")
        self._objects[key] = obj
        self._to_write.add(key)
        return obj

    def get(self, path):
        key = _key(path)
        if key not in self._objects:
            raise FileNotFoundError(f"{key} is not in the object store")
        return self._objects[key]

    def exists(self, path) -> bool:
        return _key(path) in self._objects

    def find_yaml(self, dir_path, name) -> Path | None:
        dir_parts = _key(dir_path).parts
        for key in sorted(self._objects):
            if key.parts[:len(dir_parts)] == dir_parts and key.stem == name and key.suffix in YAML_EXTENSIONS:
                return key
        return None

    def load_profile_from_cache(self, profile_path):
        raw = Path(profile_path).read_bytes()
        key = hashlib.sha256(raw).hexdigest()
        cache_dir = profile_cache_dir()
        cache_file = cache_dir / f"{key}.pkl" if cache_dir else None
        if cache_file is not None:
            try:
                if cache_file.is_file():
                    with cache_file.open("rb") as f:
                        return pickle.load(f)
            except Exception as ex:
                logger.warning(f"Profile parse cache is unreadable for {Path(profile_path).name}, re-parsing: {ex}")
        profile = openYaml(profile_path)
        if cache_file is not None:
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with cache_file.open("wb") as f:
                    pickle.dump(profile, f)
            except Exception as ex:
                logger.warning(f"Profile parse cache is unwritable for {Path(profile_path).name}: {ex}")
        return profile

    def bg_domain(self) -> CommentedMap:
        bg_domain_path = self.env_dir / "bg_domain.yml"
        return self.get(bg_domain_path) if self.exists(bg_domain_path) else CommentedMap()

    def namespaces(self) -> list[NamespaceFile]:
        bg_domain = self.bg_domain()
        return [NamespaceFile(path=p.parent, name=self.get(p)["name"], bgd=bg_domain)
                for p in self.list(self.env_dir / "Namespaces" / "*" / "namespace.yml")]

    def list(self, pattern) -> list[Path]:
        parts = Path(pattern).parts
        prefix_len = next((i for i, part in enumerate(parts) if "*" in part), len(parts))
        root_parts = _key(Path(*parts[:prefix_len])).parts
        rest = parts[prefix_len:]
        return sorted(k for k in self._objects
                      if k.parts[:len(root_parts)] == root_parts and _match(k.parts[len(root_parts):], rest))

    def beautify(self, path, schema_path, header_text=""):
        key = _key(path)
        self.get(key)
        previous_header = self._beautify.get(key, (None, ""))[1]
        self._beautify[key] = (schema_path, header_text or previous_header)
        self._to_write.add(key)
        logger.debug(f"Object store beautify: {key} with schema {schema_path}")

    def _write_targets(self):
        for key in sorted(self._to_write):
            rel = self._relative(key)
            if rel is None or not rel.parts or rel.parts[0] in NEVER_WRITTEN_DIRS:
                continue
            yield key

    def flush(self):
        for key in self._write_targets():
            data = self._objects[key]
            schema_path, header_text = self._beautify.get(key, (None, ""))
            if key in self._beautify:
                if schema_path:
                    data = sortYaml(data, schema_path, False, validate=False)
                make_quotes_for_strings(data)
            normalize_comments(data)
            if is_cred_file(str(key)):
                remove_cred_yaml_comments(data)
            else:
                remove_empty_list_comments(data)
            text = dumpYamlToStr(data)
            if header_text and not text.startswith("#"):
                text = "# " + header_text.replace("\n", "\n# ") + "\n" + text
            logger.info(f"Writing {key} (schema: {schema_path})")
            writeToFile(key, text)


_open_store = None


@contextmanager
def open_current_env_instance_store(env_dir):
    global _open_store
    if _open_store is not None:
        raise RuntimeError(f"Current env instance store is already open for {_open_store.env_dir}")
    _open_store = CurrentEnvInstanceStore(env_dir)
    try:
        yield _open_store
    finally:
        _open_store = None


def current_env_instance_store() -> CurrentEnvInstanceStore:
    if _open_store is None:
        raise RuntimeError("Current env instance store is not open: it exists only inside the env build step")
    return _open_store
