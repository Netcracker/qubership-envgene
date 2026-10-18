import os
import shutil
from contextlib import contextmanager
from fnmatch import fnmatchcase
from functools import lru_cache
from pathlib import Path
from time import time as _diag_now

from ruyaml import CommentedMap

from envgene_shared.utils.file_utils import is_cred_file, writeToFile
from envgene_shared.utils.logger import logger
from envgene_shared.utils.yaml_utils import (
    openYaml,
    remove_cred_yaml_comments,
    remove_empty_list_comments,
    skip_validated,
)

from .business_helper import NamespaceFile
from .constants import cleanup_targets
from .object_hash_manifest import (
    ROOT_OBJECT_DIRS, canonical_hash, load_manifest, manifest_bytes, save_manifest, schema_file_hash,
)
from .yaml_helper import dumpYamlToStr, make_quotes_for_strings, normalize_comments, sortYaml

# An env-specific Resource Profile from Inventory is put into the store only to be read later.
# It is an input file of the user, so flush() must not write it back.
NEVER_WRITTEN_DIRS = ("Inventory",)
YAML_EXTENSIONS = (".yml", ".yaml")


def _key(path) -> Path:
    return _resolve(str(path))


@lru_cache(maxsize=None)
def _resolve(path: str) -> Path:
    return Path(path).resolve()


def _match(parts: tuple, pattern: tuple) -> bool:
    return len(parts) == len(pattern) and all(fnmatchcase(part, name) for part, name in zip(parts, pattern))


class CurrentEnvInstanceStore:
    def __init__(self, env_dir, base_dir=None, validated=None):
        self.env_dir = _key(env_dir)
        # When set, objects that live under base_dir but outside env_dir (e.g. the
        # root AppDefs/RegDefs copies) are also tracked and written, keyed by their
        # base_dir-relative path. None keeps the store env-scoped (legacy behavior).
        self.base_dir = _key(base_dir) if base_dir is not None else None
        self._objects = {}
        self._keys_by_dir = {}
        self._to_write = set()
        self._beautify = {}
        self._replaced_dirs = set()
        self.validated = validated

    def _env_relative(self, key: Path) -> Path | None:
        """Key relative to env_dir, or None if not under it. Used for the never-written
        guard and the stale sweep, which are both env-scoped."""
        if not key.is_relative_to(self.env_dir):
            return None
        return key.relative_to(self.env_dir)

    def _relative(self, key: Path) -> Path | None:
        """Key relative to the narrowest known root (env_dir first, then base_dir),
        or None if the object belongs to neither. Used as the manifest key."""
        env_rel = self._env_relative(key)
        if env_rel is not None:
            return env_rel
        if self.base_dir is not None and key.is_relative_to(self.base_dir):
            base_rel = key.relative_to(self.base_dir)
            if base_rel.parts and base_rel.parts[0] in ROOT_OBJECT_DIRS:
                return base_rel
        return None

    def put(self, path, obj):
        key = _key(path)
        logger.debug(f"Object store put: {key}")
        self._objects[key] = obj
        self._keys_by_dir.setdefault(key.parent, set()).add(key)
        self._to_write.add(key)
        return obj

    def replace_dir(self, path):
        self._replaced_dirs.add(_key(path))

    def get(self, path):
        key = _key(path)
        if key not in self._objects:
            raise FileNotFoundError(f"{key} is not in the object store")
        return self._objects[key]

    def exists(self, path) -> bool:
        return _key(path) in self._objects

    def _dirs_under(self, dir_path):
        dir_parts = _key(dir_path).parts
        return [d for d in self._keys_by_dir if d.parts[:len(dir_parts)] == dir_parts]

    def find_yaml(self, dir_path, name) -> Path | None:
        return min((key for d in self._dirs_under(dir_path) for key in self._keys_by_dir[d]
                    if key.stem == name and key.suffix in YAML_EXTENSIONS), default=None)

    def get_yaml(self, dir_path, name):
        key = self.find_yaml(dir_path, name)
        if key is None and (key := self._disk_root_obj(dir_path, name)) is None:
            raise FileNotFoundError(f"{name} is not in the object store under {_key(dir_path)}")
        return self._objects[key]

    def _disk_root_obj(self, dir_path, name):
        if self.base_dir is None or Path(dir_path).name not in ROOT_OBJECT_DIRS:
            return None
        for suffix in YAML_EXTENSIONS:
            path = Path(dir_path) / f"{name}{suffix}"
            if path.is_file():
                self._put_readonly(path, openYaml(path))
                return path
        return None

    def _put_readonly(self, path, obj):
        key = _key(path)
        self._objects[key] = obj
        self._keys_by_dir.setdefault(key.parent, set()).add(key)

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
        root = _key(Path(*parts[:prefix_len]))
        rest = parts[prefix_len:]
        if not rest:
            return [root] if root in self._objects else []
        root_len = len(root.parts)
        return sorted(key for d in self._dirs_under(root) if _match(d.parts[root_len:], rest[:-1])
                      for key in self._keys_by_dir[d] if fnmatchcase(key.name, rest[-1]))

    def beautify(self, path, schema_path, header_text=""):
        key = _key(path)
        self.get(key)
        previous_header = self._beautify.get(key, (None, ""))[1]
        self._beautify[key] = (schema_path, header_text or previous_header)
        self._to_write.add(key)
        logger.debug(f"Object store beautify: {key} with schema {schema_path}")

    def _write_targets(self) -> dict:
        targets = {}
        for key in sorted(self._to_write):
            rel = self._relative(key)
            if rel is None or not rel.parts or rel.parts[0] in NEVER_WRITTEN_DIRS:
                continue
            targets[key] = rel
        return targets

    def _object_meta(self, key):
        if key not in self._beautify:
            return None, "", ""
        schema_path, header_text = self._beautify[key]
        schema_hash = schema_file_hash(str(schema_path)) if schema_path and Path(schema_path).exists() else ""
        return schema_path, schema_hash, header_text

    def flush(self):
        _t0 = _diag_now()
        manifest = load_manifest(self.env_dir)
        _t_manifest = _diag_now()
        stored = manifest["objects"]
        new_manifest = {"objects": {}}
        written, skipped = 0, 0
        targets = self._write_targets()
        _t_hash = 0.0
        _t_beautify = 0.0
        _t_write = 0.0
        _flush_stats = []  # [diag] (beautify_ms, emitted_bytes, name) per flushed object
        for key, rel in targets.items():
            data = self._objects[key]
            schema_path, schema_hash, header_text = self._object_meta(key)
            _h0 = _diag_now()
            content_hash = canonical_hash(data, salt=schema_hash)
            _t_hash += _diag_now() - _h0
            entry = {"hash": content_hash, "schema": schema_hash}
            new_manifest["objects"][rel.as_posix()] = entry
            in_env_dir = key.is_relative_to(self.env_dir)
            if in_env_dir and stored.get(rel.as_posix()) == entry and key.is_file():
                skipped += 1
                logger.info(f"Skipping {key} (unchanged)")
                continue
            _b0 = _diag_now()
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
            if not in_env_dir and key.is_file() and key.read_text() == text:
                skipped += 1
                _flush_stats.append((_diag_now() - _b0, len(text), key.name))
                logger.info(f"Skipping {key} (unchanged on disk)")
                continue
            written += 1
            logger.info(f"Writing {key} (schema: {schema_path})")
            _w0 = _diag_now()
            writeToFile(key, text)
            _flush_stats.append((_w0 - _b0, len(text), key.name))
            _t_beautify += _w0 - _b0
            _t_write += _diag_now() - _w0
        _t_loop = _diag_now()
        # [diag] flush weight: total bytes flushed and the heaviest objects by beautify
        # time and by size, to show what hash-skip actually saves per environment.
        _flush_bytes = sum(b for _, b, _ in _flush_stats)
        _top_ms = sorted(_flush_stats, key=lambda x: x[0], reverse=True)[:5]
        _top_bytes = sorted(_flush_stats, key=lambda x: x[1], reverse=True)[:5]
        logger.info(f"[diag] flush weight: {len(_flush_stats)} objects, {_flush_bytes} bytes; "
                    f"top by ms: {[(round(ms, 1), name) for ms, _, name in _top_ms]}; "
                    f"top by bytes: {[(b, name) for _, b, name in _top_bytes]}")
        if not self._delete_stale_objects(targets):
            cleanup_toplevel = {Path(target).name for target in cleanup_targets}
            for rel, entry in stored.items():
                if Path(rel).parts[0] in cleanup_toplevel:
                    new_manifest["objects"].setdefault(rel, entry)
            new_manifest["validated"] = sorted(set(manifest.get("validated", [])) | self._validated_this_run())
        else:
            new_manifest["validated"] = sorted(self._validated_this_run())
        for dir_key in sorted(self._replaced_dirs):
            self._prune_dir(dir_key, self._names_written_to(targets, dir_key))
        _s0 = _diag_now()
        save_manifest(self.env_dir, new_manifest)
        _t_save = _diag_now() - _s0
        logger.info(f"[diag] flush: load_manifest={(_t_manifest-_t0)*1000:.1f}ms, "
                    f"hash(480x)={_t_hash*1000:.1f}ms, beautify={_t_beautify*1000:.1f}ms, "
                    f"write={_t_write*1000:.1f}ms, post-loop={(_t_loop-_t_manifest-_t_hash-_t_beautify-_t_write)*1000:.1f}ms, "
                    f"save_manifest={_t_save*1000:.1f}ms")
        logger.info(f"Object store flush: {written} written, {skipped} skipped")

    def _validated_this_run(self) -> set:
        return self.validated.seen if self.validated else set()

    def _delete_stale_objects(self, targets: dict) -> bool:
        # The sweep prunes env-generated cleanup targets (what env_build renders). It is
        # only safe when the store actually holds objects in those scopes. If the store
        # was populated with only non-cleanup objects (e.g. BGD-warmup renders app/reg
        # defs but env_build does not run), sweeping would wipe the environment's existing
        # generated objects. AppDefs/RegDefs are not cleanup targets, so env copies of
        # them do not activate the sweep.
        cleanup_toplevel = {Path(target).name for target in cleanup_targets}
        env_keys = [key for key in targets if key.is_relative_to(self.env_dir)]
        if not any(targets[key].parts[0] in cleanup_toplevel for key in env_keys):
            logger.debug("Object store flush: no env-generated objects, skipping stale sweep")
            return False
        covered = {os.path.normcase(key) for key in env_keys}
        for target in cleanup_targets:
            path = self.env_dir / target
            if path.is_file():
                if os.path.normcase(path) not in covered:
                    path.unlink()
            elif path.is_dir():
                for root, _, files in os.walk(path, topdown=False):
                    for name in files:
                        file = os.path.join(root, name)
                        if os.path.normcase(file) not in covered:
                            os.remove(file)
                    if not os.listdir(root):
                        os.rmdir(root)
        return True

    @staticmethod
    def _names_written_to(written, dir_path) -> set:
        dir_key = _key(dir_path)
        return {key.name for key in written if key.parent == dir_key}

    @staticmethod
    def _prune_dir(dir_path, kept):
        if not dir_path.is_dir():
            return
        for entry in sorted(dir_path.iterdir()):
            if entry.is_dir():
                shutil.rmtree(entry)
                logger.info(f"Pruning stale app/reg def: {entry}")
            elif entry.name not in kept:
                entry.unlink()
                logger.info(f"Pruning stale app/reg def: {entry}")
        if not any(dir_path.iterdir()):
            dir_path.rmdir()


_open_store = None


@contextmanager
def open_current_env_instance_store(env_dir, base_dir=None):
    global _open_store
    if _open_store is not None:
        raise RuntimeError(f"Current env instance store is already open for {_open_store.env_dir}")
    with skip_validated(load_manifest(env_dir).get("validated", [])) as validated:
        _open_store = CurrentEnvInstanceStore(env_dir, base_dir=base_dir, validated=validated)
        try:
            yield _open_store
        finally:
            _open_store = None


def current_env_instance_store() -> CurrentEnvInstanceStore:
    if _open_store is None:
        raise RuntimeError("Current env instance store is not open: it exists only inside the env build step")
    return _open_store
