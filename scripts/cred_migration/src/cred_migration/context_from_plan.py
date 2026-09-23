"""Compose an external-cred-provision context YAML from a plan + repo.

Called by the standalone `envgene-external-context-generator` CLI (thin wrapper) and by
`apply_cmd` at apply time. Reads:
- `configuration/secret-stores.yml` from the repo (single-store per Assumption 1).
- Each source cred file listed in the plan (extracts the `data` field).

Emits a dict shaped for external-cred-provision:
    {"credentials": {<cred-id>: {vals, strategy, data}, ...}}

Also returns a list of cred-ids skipped because their source `data` carries `envgeneNullValue`
placeholders that cannot be written to a Store.
"""

from pathlib import Path

import yaml

from .external_context import build_context
from .pre_flight import check_single_store

_NULL_MARKER = "envgeneNullValue"


def _iter_plan_entries(plan):
    for group in plan.get("credentials", []):
        source_file = group["sourceFile"]
        for section in ("to_review", "to_confirm"):
            for cred_id, entry in (group.get(section) or {}).items():
                yield source_file, cred_id, entry


def _contains_null_marker(data):
    if isinstance(data, dict):
        return any(v == _NULL_MARKER for v in data.values())
    return data == _NULL_MARKER


def build_context_from_repo(plan, repo_root):
    """Read secret-stores.yml + source cred files, return (context_dict, skipped_cred_ids)."""
    repo_root = Path(repo_root)
    stores_path = repo_root / "configuration" / "secret-stores.yml"
    if not stores_path.exists():
        raise ValueError(
            f"secret-stores.yml not found at {stores_path}; create it before running apply"
        )
    secret_stores = yaml.safe_load(stores_path.read_text()) or {}
    check_single_store(secret_stores)  # raises on multi-store (Assumption 1 violation)
    if not secret_stores:
        raise ValueError("secret-stores.yml is empty")

    store_id, store_config = next(iter(secret_stores.items()))
    store_type = store_config["type"]

    descriptors = []
    skipped = []
    for source_file, cred_id, entry in _iter_plan_entries(plan):
        if not entry.get("writeToStore", True):
            continue
        source_path = repo_root / source_file
        source_yaml = yaml.safe_load(source_path.read_text()) or {}
        source_data = source_yaml.get(cred_id, {}).get("data")
        if _contains_null_marker(source_data):
            skipped.append(cred_id)
            continue
        descriptors.append({
            "cred_id": cred_id,
            "remote_ref_path": entry["remoteRefPath"].lstrip("/"),
            "source_data": source_data,
            "store_type": store_type,
            "store_config": store_config,
            "store_id": store_id,
        })
    context = build_context(descriptors, default_store_id=store_id)
    return context, skipped
