"""Build VALS URIs and normalised secret names for provision context."""

from __future__ import annotations

from typing import Any, Literal

StoreType = Literal["vault", "azure", "aws", "gcp", "openbao"]

GLOBAL_PATH = "global"


def build_normalized_secret_name(
    remote_ref_path: str,
    cred_id: str,
    store_type: str,
) -> str:
    if not remote_ref_path or not cred_id or not store_type:
        raise ValueError(
            f"normalization input error: path={remote_ref_path!r} "
            f"credId={cred_id!r} type={store_type!r}"
        )
    path = remote_ref_path.strip().rstrip("/")
    cid = cred_id.strip()
    st = store_type.lower()

    if st in ("vault", "openbao", "aws"):
        return f"{path}/{cid}"
    if st == "azure":
        azure_path = path.replace("/", "--").strip("-")
        return f"{azure_path}--{cid}"
    if st == "gcp":
        gcp_path = path.replace("/", "--").strip("-")
        return f"{gcp_path}--{cid}"
    raise ValueError(f"unsupported store type: {store_type}")


def build_vals_uri(store: dict[str, Any], normalized_name: str) -> str:
    """Product provision context `vals` string (no #fragment)."""
    stype = (store.get("type") or "vault").lower()
    if stype in ("vault", "openbao"):
        mount = store.get("mountPath") or store.get("mount") or "secret"
        path = normalized_name.lstrip("/")
        return f"ref+vault://{mount}/{path}"
    if stype == "aws":
        return f"ref+awssecrets://{normalized_name.lstrip('/')}"
    if stype == "gcp":
        project = store.get("projectId") or store.get("project") or ""
        name = normalized_name.lstrip("/").replace("/", "--")
        return f"ref+gcpsecrets://{project}/{name}"
    if stype == "azure":
        vault = store.get("vaultName") or store.get("vault_name") or ""
        return f"ref+azurekeyvault://{vault}/{normalized_name.lstrip('/')}"
    raise ValueError(f"unsupported store type for vals: {stype}")


def load_default_store(instance_root) -> dict[str, Any]:
    from pathlib import Path

    import yaml

    from migration_cli.errors import ValidationError

    path = Path(instance_root) / "configuration" / "secret-stores.yml"
    if not path.is_file():
        path = Path(instance_root) / "configuration" / "secret-stores.yaml"
    if not path.is_file():
        raise ValidationError(
            f"Missing configuration/secret-stores.yml under {instance_root}"
        )
    with path.open(encoding="utf-8") as handle:
        doc = yaml.safe_load(handle)
    if not isinstance(doc, dict) or not isinstance(doc.get("default_store"), dict):
        raise ValidationError(f"{path}: expected top-level default_store mapping")
    return doc["default_store"]
