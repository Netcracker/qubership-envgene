import hashlib
import os
import pickle
from contextlib import contextmanager
from fnmatch import fnmatchcase
from pathlib import Path

from ruyaml import CommentedMap

from envgene_shared.crypto.cred_store import current_cred_store
from envgene_shared.utils.business_utils import get_envgene_config_yaml, to_bool
from envgene_shared.utils.file_utils import is_cred_file, writeToFile
from envgene_shared.utils.logger import logger
from envgene_shared.utils.yaml_utils import (
    remove_empty_list_comments, validate_yaml_by_scheme_or_fail, openYaml, dumpYamlToStr, make_quotes_for_strings
)

from .business_helper import NamespaceFile
from .models import SCHEMA_TO_MODEL, YamlBacked, bind_yaml, CredentialMode
from .yaml_helper import normalize_comments, sortYaml

# An env-specific Resource Profile from Inventory is put into the store only to be read later.
# It is an input file of the user, so flush() must not write it back.
NEVER_WRITTEN_DIRS = ("Inventory",)
YAML_EXTENSIONS = (".yml", ".yaml")

def profile_cache_dir() -> Path | None:
    root = os.environ.get("CI_PROJECT_DIR")
    if not root or not to_bool(get_envgene_config_yaml().get("cache", {}).get("enabled"), default=True):
        return None
    return Path(root) / ".shared" / "profile-cache"


def _key(path) -> Path:
    return Path(path).resolve()


def _match(parts: tuple, pattern: tuple) -> bool:
    return len(parts) == len(pattern) and all(fnmatchcase(part, name) for part, name in zip(parts, pattern))


def _to_model(obj, schema_path, path):
    name = Path(str(schema_path)).name
    model_cls = SCHEMA_TO_MODEL.get(name)
    if model_cls is None:
        logger.info(f"Validating {path} (schema: {schema_path})")
        if isinstance(schema_path, Path) or name != str(schema_path):
            validate_yaml_by_scheme_or_fail(input_yaml_content=obj, schema_file_path=str(schema_path))
        else:
            validate_yaml_by_scheme_or_fail(input_yaml_content=obj, schema_name=name)
        return obj
    if isinstance(obj, model_cls):
        return obj
    logger.info(f"Validating {path} (schema: {schema_path})")
    try:
        model = model_cls.model_validate(obj)
    except ValueError as error:
        raise ValueError(f"Validation failed for {path} (schema: {schema_path}): {error}") from error
    bind_yaml(model, obj)
    return model


class CurrentEnvInstanceStore:
    def __init__(self, env_dir, credential_mode=CredentialMode.LOCAL):
        self.env_dir = _key(env_dir)
        self.credential_mode = credential_mode
        self._objects = {}
        self._to_write = set()
        self._schemas = {}
        self._beautify = {}

    def _relative(self, key: Path) -> Path | None:
        if not key.is_relative_to(self.env_dir):
            return None
        return key.relative_to(self.env_dir)

    def put(self, path, obj):
        key = _key(path)
        logger.debug(f"Object store put: {key}")
        schema_path = self._schemas.get(key)
        if schema_path:
            obj = _to_model(obj, schema_path, key)
        if is_cred_file(str(key)):
            current_cred_store().put(key, obj.to_yaml() if isinstance(obj, YamlBacked) else obj)
            if schema_path:
                self._objects[key] = obj
            return obj
        self._objects[key] = obj
        self._to_write.add(key)
        return obj

    def get(self, path):
        key = _key(path)
        if is_cred_file(str(key)) and key not in self._schemas:
            return current_cred_store().load_decrypted(key)
        if key not in self._objects:
            raise FileNotFoundError(f"{key} is not in the object store")
        return self._objects[key]

    def exists(self, path) -> bool:
        key = _key(path)
        if is_cred_file(str(key)):
            return current_cred_store().exists(key)
        return key in self._objects

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

    def bg_domain(self) -> CommentedMap | YamlBacked:
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

    def bind(self, path, schema_path):
        key = _key(path)
        self._objects[key] = _to_model(self.get(key), schema_path, key)
        self._schemas[key] = schema_path
        return self._objects[key]

    def beautify(self, path, schema_path, header_text=""):
        key = _key(path)
        self.bind(key, schema_path)
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
        # Credential models keep schema checks while the cred store owns encryption and disk writes.
        for key in self._schemas:
            if is_cred_file(str(key)):
                data = self._objects[key]
                header_text = self._beautify.get(key, (None, ""))[1]
                current_cred_store().put(key, data.to_yaml() if isinstance(data, YamlBacked) else data, header_text)
        for key in self._write_targets():
            if is_cred_file(str(key)):
                continue
            data = self._objects[key]
            if isinstance(data, YamlBacked):
                data = data.to_yaml()
            schema_path, header_text = self._beautify.get(key, (None, ""))
            if key in self._beautify:
                if schema_path:
                    data = sortYaml(data, schema_path, False, validate=False)
                make_quotes_for_strings(data)
            normalize_comments(data)
            remove_empty_list_comments(data)
            text = dumpYamlToStr(data)
            if header_text and not text.startswith("#"):
                text = "# " + header_text.replace("\n", "\n# ") + "\n" + text
            logger.info(f"Writing {key} (schema: {schema_path})")
            writeToFile(key, text)


_open_store = None


@contextmanager
def open_current_env_instance_store(env_dir, credential_mode=CredentialMode.LOCAL):
    global _open_store
    if _open_store is not None:
        raise RuntimeError(f"Current env instance store is already open for {_open_store.env_dir}")
    _open_store = CurrentEnvInstanceStore(env_dir, credential_mode)
    try:
        yield _open_store
    finally:
        _open_store = None


def current_env_instance_store() -> CurrentEnvInstanceStore:
    if _open_store is None:
        raise RuntimeError("Current env instance store is not open: it exists only inside the env build step")
    return _open_store
