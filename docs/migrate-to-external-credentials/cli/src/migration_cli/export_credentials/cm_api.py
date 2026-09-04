"""CM API client — list credential ids and types for a tenant."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from migration_cli.export_credentials.http_client import JenkinsHttpClient

log = logging.getLogger(__name__)

SUPPORTED_TYPES = frozenset({"usernamePassword", "secret"})


@dataclass(frozen=True)
class CredentialRef:
    cred_id: str
    cred_type: str


def _parse_credential_entry(entry: Any) -> CredentialRef | None:
    if not isinstance(entry, dict):
        return None
    cred_id = entry.get("id")
    cred_type = entry.get("type")
    if not isinstance(cred_id, str) or not cred_id:
        return None
    if not isinstance(cred_type, str) or not cred_type:
        return None
    return CredentialRef(cred_id=cred_id, cred_type=cred_type)


def list_credentials(*, client: JenkinsHttpClient, tenant: str) -> list[CredentialRef]:
    path = f"/cm/v1/domains/{tenant}/credentials"
    headers = {
        "type": "usernamePassword,secret",
        "Content-Type": "application/json",
    }
    payload = client.get_json_with_body(path=path, headers=headers, json_body={"tenant": tenant})

    if payload is None:
        return []

    if isinstance(payload, dict):
        items = payload.get("credentials") or payload.get("items") or []
    elif isinstance(payload, list):
        items = payload
    else:
        items = []

    refs: list[CredentialRef] = []
    for entry in items:
        ref = _parse_credential_entry(entry)
        if ref is None:
            continue
        if ref.cred_type not in SUPPORTED_TYPES:
            log.warning("Unsupported type %r for %r — skipped.", ref.cred_type, ref.cred_id)
            continue
        refs.append(ref)

    return refs
