"""Write configuration/secret-stores.yml (invoked from skill, not a CLI command)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .store_preflight import STORE_ENV_REQUIREMENTS
from .yaml_io import open_yaml, write_yaml

_STORE_TYPES = frozenset({"vault", "azure", "aws", "gcp"})
# Fields that matter for EnvGene VALS / identity (not connection host).
_REQUIRED_BY_TYPE = {
    "vault": ("mountPath",),
    "azure": ("vaultName",),
    "aws": ("region",),
    "gcp": ("projectId",),
}


class SecretStoreError(Exception):
    pass


def _validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise SecretStoreError("spec must be a mapping")
    stype = str(spec.get("type") or "").lower()
    if stype == "openbao":
        stype = "vault"
    if stype not in _STORE_TYPES:
        raise SecretStoreError(
            f"type must be one of {sorted(_STORE_TYPES)!r} (got {spec.get('type')!r})"
        )
    store: dict[str, Any] = {"type": stype}
    # url is optional (schema legacy). Not used for Vault/GCP connection or VALS.
    url = spec.get("url")
    if url is not None and str(url).strip():
        store["url"] = str(url).strip()
    for key in _REQUIRED_BY_TYPE.get(stype, ()):
        val = spec.get(key)
        if not val or not str(val).strip():
            raise SecretStoreError(f"{key} is required when type={stype}")
        store[key] = str(val).strip()
    return store


def write_secret_stores(
    repo_root: Path,
    spec: dict[str, Any],
    *,
    overwrite: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create or replace ``configuration/secret-stores.yml`` with ``default_store``.

    Returns a JSON-serializable result for the skill (no secrets in spec).
    """
    repo_root = Path(repo_root)
    store = _validate_spec(spec)
    path = repo_root / "configuration" / "secret-stores.yml"
    exists = path.is_file()
    if exists and not overwrite:
        raise SecretStoreError(
            f"{path} already exists — pass overwrite=true to replace"
        )
    doc = {"default_store": store}
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_yaml(path, doc)
    stype = store["type"]
    env_vars = list(STORE_ENV_REQUIREMENTS.get(stype, ()))
    return {
        "ok": True,
        "path": str(path),
        "created": not exists,
        "overwritten": exists and overwrite,
        "dry_run": dry_run,
        "store_type": stype,
        "env_vars_needed": env_vars,
    }


def read_secret_stores(repo_root: Path) -> dict[str, Any] | None:
    """Return parsed secret-stores.yml or None if missing."""
    path = Path(repo_root) / "configuration" / "secret-stores.yml"
    if not path.is_file():
        return None
    return open_yaml(path)
