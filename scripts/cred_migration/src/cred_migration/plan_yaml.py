"""migration-plan.yaml structure builders, validation, and I/O.

Plan structure (see design doc "migration-plan.yaml schema"):
{
    "repo_type": "instance" | "template",
    "generated_at": "<ISO timestamp>",
    "credentials": [
        {
            "sourceFile": "<repo-relative path>",
            "to_review": {"<cred-id>": {editable-fields...}, ...},
            "to_confirm": {"<cred-id>": {editable-fields...}, ...},
        }, ...
    ],
    "to_delete": {"<group-name>": ["<path>", ...], ...},
}

Editable fields per cred entry: remoteRefPath, create, writeToStore (instance only), suggestions.
"""

import yaml


class PlanValidationError(ValueError):
    """Raised when a loaded plan violates the schema."""


_VALID_REPO_TYPES = {"instance", "template"}


def build_cred_entry(remote_ref_path, create, write_to_store, suggestions):
    """Build a single cred entry dict, omitting empty/None optional fields."""
    entry = {"remoteRefPath": remote_ref_path, "create": create}
    if write_to_store is not None:
        entry["writeToStore"] = write_to_store
    if suggestions:
        entry["suggestions"] = list(suggestions)
    return entry


def build_source_group(source_file, to_review, to_confirm):
    """Build a per-source-file group dict."""
    return {
        "sourceFile": source_file,
        "to_review": dict(to_review or {}),
        "to_confirm": dict(to_confirm or {}),
    }


def build_plan(repo_type, generated_at, credentials, to_delete):
    """Compose the top-level plan structure."""
    return {
        "repo_type": repo_type,
        "generated_at": generated_at,
        "credentials": list(credentials),
        "to_delete": dict(to_delete or {}),
    }


def validate_plan(plan):
    """Raise PlanValidationError if the plan violates the schema."""
    if not isinstance(plan, dict):
        raise PlanValidationError("plan must be a mapping")

    repo_type = plan.get("repo_type")
    if repo_type not in _VALID_REPO_TYPES:
        raise PlanValidationError(
            f"repo_type must be one of {sorted(_VALID_REPO_TYPES)}, got {repo_type!r}"
        )

    creds = plan.get("credentials", [])
    if not isinstance(creds, list):
        raise PlanValidationError("credentials must be a list")

    for group in creds:
        if not isinstance(group, dict):
            raise PlanValidationError("each credentials entry must be a mapping")
        if "sourceFile" not in group:
            raise PlanValidationError("each credentials group must include sourceFile")

        for section in ("to_review", "to_confirm"):
            entries = group.get(section, {})
            if not isinstance(entries, dict):
                raise PlanValidationError(
                    f"{section} in group {group['sourceFile']!r} must be a mapping"
                )
            for cred_id, entry in entries.items():
                if not isinstance(entry, dict):
                    raise PlanValidationError(
                        f"cred entry for {cred_id!r} must be a mapping"
                    )
                if "remoteRefPath" not in entry:
                    raise PlanValidationError(
                        f"cred entry {cred_id!r} in {group['sourceFile']!r} missing remoteRefPath"
                    )


def dump_plan(plan, path):
    """Serialize plan to YAML with block style. Overwrites destination file."""
    validate_plan(plan)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(plan, fh, sort_keys=False, default_flow_style=False, allow_unicode=True)


def load_plan(path):
    """Load and validate a plan YAML from disk."""
    with open(path, encoding="utf-8") as fh:
        plan = yaml.safe_load(fh)
    validate_plan(plan)
    return plan
