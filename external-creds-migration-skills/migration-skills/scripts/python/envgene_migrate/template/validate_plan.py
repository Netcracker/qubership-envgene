"""Plan consistency validation (warn vs error)."""

from __future__ import annotations

from typing import Any

from .plan_schema import iter_plan_entries


def validate_plan_entries(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (warnings, errors). Errors abort apply before writes."""
    warnings: list[str] = []
    errors: list[str] = []
    repo = plan.get("repo_type")

    for err in plan.get("plan_errors") or []:
        errors.append(str(err))

    for src, _bucket, cred_id, fields in iter_plan_entries(plan):
        path = str(fields.get("remoteRefPath") or "")
        create = fields.get("create")
        write_to_store = fields.get("writeToStore", True)

        segments = [s for s in path.strip("/").split("/") if s]
        # Jinja paths: skip strict segment checks
        if "{{" in path or "}}" in path:
            pass
        elif path == "global" or path == "/global" or segments[:1] == ["global"]:
            if create is True:
                warnings.append(
                    f"{cred_id}: create:true with remoteRefPath=global is unusual"
                )
        elif len(segments) == 1:
            # passport-ish <cluster>
            pass
        elif len(segments) in (2, 3):
            pass
        elif path:
            warnings.append(
                f"{cred_id}: path shape unusual; confirm intentional override ({path})"
            )

        if create is None and repo == "instance":
            pass

        if write_to_store is True and fields.get("_hasNullPlaceholder"):
            warnings.append(
                f"{cred_id}: writeToStore:true with envgeneNullValue — Store write will be skipped"
            )

        if not path:
            errors.append(f"[{cred_id}] FAILED: remoteRefPath missing in plan ({src})")

    return warnings, errors
