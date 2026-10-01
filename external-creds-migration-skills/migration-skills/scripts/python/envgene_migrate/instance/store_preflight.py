"""Instance Secret Store / SOPS pre-flight checks."""

from __future__ import annotations

import os
from pathlib import Path

from ..preflight import PreflightError
from .yaml_io import open_yaml

STORE_ENV_REQUIREMENTS = {
    "vault": ("VAULT_ADDR", "VAULT_TOKEN"),
    "openbao": ("VAULT_ADDR", "VAULT_TOKEN"),
    "gcp": ("GOOGLE_APPLICATION_CREDENTIALS",),
    "aws": ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"),
    "azure": ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"),
}


def require_sops_key_if_needed(encrypted_seen: bool) -> None:
    if not encrypted_seen:
        return
    if os.environ.get("SOPS_AGE_KEY") or os.environ.get("ENVGENE_AGE_PRIVATE_KEY"):
        return
    raise PreflightError(
        "SOPS-encrypted credential file(s) found but SOPS_AGE_KEY "
        "(or ENVGENE_AGE_PRIVATE_KEY) is not set"
    )


def load_default_store(repo_root: Path) -> dict:
    path = repo_root / "configuration" / "secret-stores.yml"
    data = open_yaml(path)
    if not data:
        raise PreflightError(f"missing Secret Store config: {path}")
    # Assumption 1: single default_store; no multi-store map support
    if "default_store" not in data:
        raise PreflightError(f"{path}: default_store is required")
    # Extra top-level store keys beyond default_store → multi-store violation
    extra = [k for k in data if k not in ("default_store",) and not str(k).startswith("#")]
    # Allow only default_store as the store entry for v1
    stores = data.get("stores") or data.get("secretStores")
    if stores and isinstance(stores, dict) and len(stores) > 1:
        raise PreflightError(
            "multiple stores in secret-stores.yml — not supported (Assumption: one store)"
        )
    return data["default_store"]


def require_store_env(store: dict) -> None:
    stype = (store.get("type") or "").lower()
    required = STORE_ENV_REQUIREMENTS.get(stype)
    if not required:
        raise PreflightError(f"unsupported or missing store type: {stype!r}")
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise PreflightError(
            f"missing Store auth env vars for type={stype}: {', '.join(missing)}"
        )
