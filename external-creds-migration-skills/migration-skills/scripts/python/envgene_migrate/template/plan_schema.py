"""migration-plan.yaml read/write."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..exit_codes import PLAN_FILENAME
from .yaml_io import open_yaml, write_yaml


def empty_plan(repo_type: str) -> dict[str, Any]:
    return {
        "repo_type": repo_type,
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "credentials": [],
        "to_delete": {},
    }


def add_source_group(
    plan: dict[str, Any],
    source_file: str,
    *,
    to_review: dict[str, Any] | None = None,
    to_confirm: dict[str, Any] | None = None,
) -> None:
    plan.setdefault("credentials", []).append(
        {
            "sourceFile": source_file,
            "to_review": to_review or {},
            "to_confirm": to_confirm or {},
        }
    )


def write_plan(plan: dict[str, Any], cwd: Path | None = None) -> Path:
    root = cwd or Path.cwd()
    path = root / PLAN_FILENAME
    write_yaml(path, plan)
    return path


def read_plan(cwd: Path | None = None) -> dict[str, Any]:
    root = cwd or Path.cwd()
    path = root / PLAN_FILENAME
    data = open_yaml(path)
    if not data:
        raise FileNotFoundError(f"missing {path}")
    return data


def unbound_parameter_sets(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Rows for ParameterSets not in any descriptor closure (legacy key: orphans)."""
    direct = plan.get("unbound_parameter_sets")
    if isinstance(direct, list):
        return list(direct)
    nested = (plan.get("orphans") or {}).get("unbound_parameter_sets")
    if isinstance(nested, list):
        return list(nested)
    return []


def iter_plan_entries(plan: dict[str, Any]):
    """Yield (source_file, bucket, cred_id, fields)."""
    for group in plan.get("credentials") or []:
        src = group.get("sourceFile") or ""
        for bucket in ("to_review", "to_confirm"):
            mapping = group.get(bucket) or {}
            for cred_id, fields in mapping.items():
                yield src, bucket, cred_id, fields or {}


CARRY_OVERRIDE_FIELDS = (
    "remoteRefPath",
    "create",
    "includeInCredentialTemplate",
)


def try_load_prior_plan(cwd: Path | None = None) -> dict[str, Any] | None:
    root = cwd or Path.cwd()
    if not (root / PLAN_FILENAME).is_file():
        return None
    try:
        return read_plan(cwd)
    except FileNotFoundError:
        return None


def merge_prior_plan_overrides(
    new_plan: dict[str, Any],
    prior: dict[str, Any] | None,
    *,
    carry_fields: tuple[str, ...] = CARRY_OVERRIDE_FIELDS,
) -> None:
    """Carry operator_decisions and per-cred overrides from a prior plan file."""
    if not prior:
        return
    od = prior.get("operator_decisions")
    if isinstance(od, dict) and od:
        new_plan["operator_decisions"] = dict(od)
    prior_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for src, _bucket, cid, fields in iter_plan_entries(prior):
        if isinstance(fields, dict):
            prior_by_key[(src, str(cid))] = fields
    for src, _bucket, cid, fields in iter_plan_entries(new_plan):
        old = prior_by_key.get((src, str(cid)))
        if not old or not isinstance(fields, dict):
            continue
        for key in carry_fields:
            if key in old:
                fields[key] = old[key]
