from contextlib import contextmanager
from fnmatch import fnmatchcase
from pathlib import Path

from ruyaml import CommentedMap

from envgene_shared.utils.file_utils import is_cred_file, writeToFile
from envgene_shared.utils.logger import logger
from envgene_shared.utils.yaml_utils import remove_cred_yaml_comments, remove_empty_list_comments, \
    validate_yaml_by_scheme_or_fail

from .business_helper import NamespaceFile
from .config_helper import get_save_artifacts_strategy
from .models import SaveArtifactsStrategy
from .yaml_helper import dumpYamlToStr, make_quotes_for_strings, normalize_comments, sortYaml

GLOB_CHARS = set("*?[")
NEVER_WRITTEN_DIRS = ("Inventory",)
RAW_SKIPPED_DIRS = ("Credentials",)
YAML_EXTENSIONS = (".yml", ".yaml")


def _key(path) -> Path:
    return Path(path).resolve()


def _match(parts: tuple, pattern: tuple) -> bool:
    if not pattern:
        return not parts
    if pattern[0] == "**":
        return any(_match(parts[i:], pattern[1:]) for i in range(len(parts) + 1))
    return bool(parts) and fnmatchcase(parts[0], pattern[0]) and _match(parts[1:], pattern[1:])


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

    def bg_domain(self) -> CommentedMap:
        bg_domain_path = self.env_dir / "bg_domain.yml"
        return self.get(bg_domain_path) if self.exists(bg_domain_path) else CommentedMap()

    def namespaces(self) -> list[NamespaceFile]:
        bg_domain = self.bg_domain()
        return [NamespaceFile(path=p.parent, name=self.get(p)["name"], bgd=bg_domain)
                for p in self.list(self.env_dir / "Namespaces" / "*" / "namespace.yml")]

    def list(self, pattern) -> list[Path]:
        parts = Path(pattern).parts
        prefix_len = next((i for i, part in enumerate(parts) if GLOB_CHARS & set(part)), len(parts))
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
            yield key, rel

    def flush(self, raw=False, raw_dir=None):
        if raw:
            self._flush_raw(raw_dir)
            return
        invalid_object_paths = []
        for key, _ in self._write_targets():
            data = self._objects[key]
            schema_path, header_text = self._beautify.get(key, (None, ""))
            if schema_path:
                try:
                    validate_yaml_by_scheme_or_fail(input_yaml_content=data, schema_file_path=schema_path)
                except ValueError:
                    logger.error(f"{key} is invalid by schema {schema_path} and is not written")
                    invalid_object_paths.append(str(key))
                    continue
            if key in self._beautify:
                if schema_path:
                    data = sortYaml(data, schema_path, False)
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
        if invalid_object_paths:
            raise ValueError(f"Objects invalid by schema are not written: {invalid_object_paths}")

    def _flush_raw(self, raw_dir):
        if raw_dir is None or get_save_artifacts_strategy() == SaveArtifactsStrategy.NEVER:
            return
        for key, rel in self._write_targets():
            if rel.parts[0] in RAW_SKIPPED_DIRS or is_cred_file(str(key)):
                continue
            data = self._objects[key]
            normalize_comments(data)
            target = Path(raw_dir) / rel
            logger.info(f"Writing raw {target}")
            writeToFile(target, dumpYamlToStr(data))


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
