"""Mirror Java SecretNameBuilder / ExternalCredUtils VALS helpers (subset)."""

from __future__ import annotations

from typing import Any, Literal

StoreType = Literal["vault", "azure", "aws", "gcp", "openbao"]


def build_normalized_secret_name(
    remote_ref_path: str,
    cred_id: str,
    store_type: str,
) -> str:
    """Append normalised cred-id to remoteRefPath per store type (Java parity)."""
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


# Back-compat alias used by older call sites / docs
build_vals_uri_without_fragment = build_vals_uri


def provision_data_payload(data: Any) -> Any:
    """Shape plaintext for external-cred-provision `data` field."""
    if isinstance(data, dict):
        return {str(k): ("" if v is None else str(v)) for k, v in data.items()}
    if data is None:
        return {}
    return {"value": str(data)}
