"""Recognize stored protection and references without evaluating secret values."""

from __future__ import annotations

import re
from typing import Any

_TOKEN = re.compile(r'ENC\[AES256_GCM,data:[A-Za-z0-9+/=]+,iv:[A-Za-z0-9+/=]+,tag:[A-Za-z0-9+/=]+,type:(?:str|int|float|bool|bytes)\]')
_CALL = r'''creds\s*\.\s*get\s*\(\s*(["'])([^"'{}\\\r\n]+)\1\s*\)(?:\s*\.\s*([A-Za-z_]\w*))?'''
_LOCAL = re.compile(r'\$\{\s*' + _CALL + r'\s*\}')
_SYSTEM = re.compile(r'envgen\s*\.\s*' + _CALL)
_RECIPIENTS = {
    'age': ('recipient',), 'pgp': ('fp',), 'kms': ('arn',),
    'gcp_kms': ('resource_id',), 'azure_kv': ('vault_url', 'name', 'version'),
    'hc_vault': ('vault_address', 'engine_path', 'key_name'),
}


def literal_name(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not any(
        mark in value for mark in ('${', '{{', '{%', '\n', '\r')
    )


def parse_reference(value: Any) -> tuple[str, str | None, str] | None:
    if isinstance(value, dict):
        if (set(value) - {'$type', 'credId', 'property'}
                or value.get('$type') != 'credRef' or not literal_name(value.get('credId'))):
            return None
        field = value.get('property')
        if 'property' in value and field not in ('username', 'password'):
            return None
        return value['credId'], field, 'external'
    if not isinstance(value, str):
        return None
    match = _LOCAL.fullmatch(value.strip())
    kind = 'local'
    if match is None:
        match = _SYSTEM.fullmatch(value.strip())
        kind = 'system'
    if not match or not literal_name(match[2]) or match[3] not in ('username', 'password', 'secret'):
        return None
    return match[2], match[3], kind


def valid_external(entry: Any) -> bool:
    if not isinstance(entry, dict) or entry.get('type') != 'external':
        return False
    if set(entry) - {'type', 'secretStore', 'remoteRefPath', 'create', 'properties'}:
        return False
    if 'secretStore' in entry and not literal_name(entry['secretStore']):
        return False
    if 'create' in entry and not isinstance(entry['create'], bool):
        return False
    if 'remoteRefPath' in entry and not literal_name(entry['remoteRefPath']):
        return False
    if 'properties' in entry:
        props = entry['properties']
        if not isinstance(props, list) or not all(
            isinstance(prop, dict) and set(prop) == {'name'}
            and prop['name'] in ('username', 'password') for prop in props
        ):
            return False
    return True


def sops_metadata(document: Any) -> bool:
    meta = document.get('sops') if isinstance(document, dict) else None
    if (not isinstance(meta, dict) or not isinstance(meta.get('version'), str)
            or not meta['version'].strip()):
        return False
    mac = meta.get('mac')
    if not isinstance(mac, str) or not _TOKEN.fullmatch(mac):
        return False
    return any(
        isinstance(meta.get(kind), list) and any(
            isinstance(item, dict) and isinstance(item.get('enc'), str) and bool(item['enc'].strip())
            and all(isinstance(item.get(key), str) and bool(item[key].strip()) for key in required)
            for item in meta[kind]
        ) for kind, required in _RECIPIENTS.items()
    )


def classify(value: Any, document: Any) -> str:
    if value is None or value == '':
        return 'empty'
    if not isinstance(value, (str, int, float, bool)):
        return 'unknown'
    if not isinstance(value, str):
        return 'literal'
    if _TOKEN.fullmatch(value):
        return 'protected' if sops_metadata(document) else 'unknown'
    if value.startswith('[encrypted:AES256_Fernet]'):
        return 'unsupported'
    if re.fullmatch(r'\$[A-Za-z_]\w*', value) or any(
        mark in value for mark in ('${', '{{', '{%', 'ENC[', 'envgen.creds.', '[encrypted:')
    ):
        return 'unknown'
    return 'literal'
