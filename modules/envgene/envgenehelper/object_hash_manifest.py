import json
from pathlib import Path

from envgene_shared.utils.content_hash import canonical_hash, schema_file_hash
from envgene_shared.utils.file_utils import is_cred_file, writeToFile
from envgene_shared.utils.logger import logger
from envgene_shared.utils.yaml_utils import openYaml

MANIFEST_DIR = ".envgene"
MANIFEST_NAME = "object-hashes.json"
ROOT_OBJECT_DIRS = ("appdefs", "regdefs")


def manifest_path(env_dir) -> Path:
    return Path(env_dir) / MANIFEST_DIR / MANIFEST_NAME


def _empty_manifest() -> dict:
    return {"objects": {}}


def load_manifest(env_dir) -> dict:
    path = manifest_path(env_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as ex:
        logger.warning(f"Object hash manifest {path} is absent or invalid, full build will run: {ex}")
        return _empty_manifest()
    if not isinstance(data, dict) or not isinstance(data.get("objects"), dict):
        logger.warning(f"Object hash manifest {path} is malformed, full build will run")
        return _empty_manifest()
    return data


def manifest_bytes(manifest: dict) -> bytes:
    return (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def save_manifest(env_dir, manifest: dict) -> None:
    writeToFile(manifest_path(env_dir), manifest_bytes(manifest).decode("utf-8"))


def sync_manifest_with_disk(env_dir, base_dir=None) -> bool:
    path = manifest_path(env_dir)
    if not path.is_file():
        return False
    manifest = load_manifest(env_dir)
    synced = {}
    for rel, entry in manifest["objects"].items():
        in_root = base_dir is not None and Path(rel).parts[0] in ROOT_OBJECT_DIRS
        file = Path(base_dir if in_root else env_dir) / rel
        if not file.is_file():
            logger.info(f"Object hash manifest {path}: {rel} is gone, entry removed")
            continue
        if is_cred_file(str(file)):
            synced[rel] = entry
            continue
        disk_hash = canonical_hash(openYaml(file), salt=entry.get("schema", ""))
        if disk_hash != entry.get("hash"):
            logger.info(f"Object hash manifest {path}: {rel} differs from the manifest, entry updated")
        synced[rel] = {**entry, "hash": disk_hash}
    if synced == manifest["objects"]:
        return False
    save_manifest(env_dir, {**manifest, "objects": synced})
    return True
