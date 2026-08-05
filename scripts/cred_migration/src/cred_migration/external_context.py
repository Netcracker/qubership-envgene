"""CLI-context builder for external-cred-provision.

Produces the YAML shape the CLI consumes:
    credentials:
      <cred-id>:
        vals: "<vals-url>"
        strategy: overwrite      # migration always overwrites - Git is source of truth
        data: {...} | "..."      # plaintext from Git; Vault/OpenBao wrap scalars in {secret: X}

Migration composes one context per apply run, batched across all creds/stores.
"""

from .external_creds import build_vals_uri, normalize_secret_name

# Vault-family stores reject scalar `data`; migration promotes bare strings to {secret: X}.
_DICT_ONLY_STORES = frozenset({"vault", "openbao"})

# envgeneNullValue placeholders cannot be written to a Store.
_NULL_MARKER = "envgeneNullValue"


def build_data_from_source(source_data, store_type):
    """Shape source cred `data` field for the CLI context.

    - Dict passes through as-is.
    - Scalar promoted to {secret: X} for Vault-family (dict-only) stores; passes through elsewhere.
    """
    if isinstance(source_data, dict):
        return dict(source_data)
    if store_type in _DICT_ONLY_STORES:
        return {"secret": source_data}
    return source_data


def _contains_null_marker(source_data):
    if isinstance(source_data, dict):
        return any(v == _NULL_MARKER for v in source_data.values())
    return source_data == _NULL_MARKER


def build_context_entry(
    cred_id, remote_ref_path, source_data, store_type, store_config, store_id, default_store_id
):
    """Build one CLI-context entry (vals + strategy + data)."""
    if _contains_null_marker(source_data):
        raise ValueError(
            f"cred {cred_id!r} carries envgeneNullValue placeholder; skip Store write and warn"
        )
    normalized = normalize_secret_name(remote_ref_path, cred_id, store_type)
    vals = build_vals_uri(store_type, store_config, normalized, store_id, default_store_id)
    return {
        "vals": vals,
        "strategy": "overwrite",
        "data": build_data_from_source(source_data, store_type),
    }


def build_context(creds, default_store_id):
    """Build the full CLI-context YAML dict from a list of cred descriptors.

    Each descriptor is a dict with keys:
        cred_id, remote_ref_path, source_data, store_type, store_config, store_id
    """
    entries = {}
    for cred in creds:
        entries[cred["cred_id"]] = build_context_entry(
            cred_id=cred["cred_id"],
            remote_ref_path=cred["remote_ref_path"],
            source_data=cred["source_data"],
            store_type=cred["store_type"],
            store_config=cred["store_config"],
            store_id=cred["store_id"],
            default_store_id=default_store_id,
        )
    return {"credentials": entries}
