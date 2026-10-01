"""Rewrite local cred entries → type: external (+ properties from data keys)."""

from __future__ import annotations

from typing import Any

from .constants import ENVGENE_NULL, SUPPORTED_CRED_TYPES


class UnsupportedCredTypeError(Exception):
    def __init__(self, cred_id: str, cred_type: str):
        self.cred_id = cred_id
        self.cred_type = cred_type
        super().__init__(
            f"[{cred_id}] FAILED: unsupported cred type '{cred_type}'"
        )


def is_null_placeholder(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, dict):
        return any(is_null_placeholder(v) for v in value.values())
    if isinstance(value, str):
        return value.lower() == ENVGENE_NULL.lower()
    return False


def properties_from_data(data: Any, cred_type: str) -> list[dict[str, str]] | None:
    if cred_type == "secret":
        return None
    if cred_type == "usernamePassword":
        if isinstance(data, dict):
            props = []
            for key in data:
                if str(key).lower() == "type":
                    continue
                props.append({"name": str(key)})
            return props or [{"name": "username"}, {"name": "password"}]
        return [{"name": "username"}, {"name": "password"}]
    return None


def to_external_entry(
    cred_id: str,
    source_entry: dict[str, Any],
    *,
    remote_ref_path: str,
    create: bool | None,
    inferred_type: str | None = None,
) -> dict[str, Any]:
    cred_type = source_entry.get("type") or inferred_type or "secret"
    if cred_type == "external":
        raise ValueError(
            f"[{cred_id}] FAILED: source already type: external (partial migration)"
        )
    if cred_type not in SUPPORTED_CRED_TYPES:
        raise UnsupportedCredTypeError(cred_id, str(cred_type))

    data = source_entry.get("data")
    out: dict[str, Any] = {
        "type": "external",
        "secretStore": "default_store",
        "remoteRefPath": remote_ref_path,
    }
    if create is not None:
        out["create"] = create
    props = properties_from_data(data, cred_type)
    if props:
        out["properties"] = props
    # data intentionally omitted
    return out


def extract_plaintext_for_store(source_entry: dict[str, Any]) -> Any:
    return source_entry.get("data")
