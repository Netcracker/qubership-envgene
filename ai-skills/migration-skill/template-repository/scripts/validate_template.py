#!/usr/bin/env python3
"""Validate Template Repository External Credentials migration (read-only)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema

from common import (
    EXIT_ERROR,
    EXIT_OK,
    emit,
    find_remaining_macros,
    load_yaml,
    path_contains_cred_id,
)


def find_schema(repo: Path, name: str) -> Path | None:
    for parent in [repo, *repo.parents]:
        candidate = parent / "schemas" / name
        if candidate.is_file():
            return candidate
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--descriptor", required=True)
    parser.add_argument("--credential-template", required=True)
    parser.add_argument("--macro-files", nargs="*", default=[])
    parser.add_argument("--schemas-dir", type=Path, default=None)
    args = parser.parse_args()

    repo = args.repo.resolve()
    issues = []
    checked = []

    desc_path = repo / args.descriptor
    cred_path = repo / args.credential_template
    if not desc_path.is_file():
        emit({"status": "error", "error": f"Missing descriptor {args.descriptor}"}, EXIT_ERROR)
    if not cred_path.is_file():
        emit(
            {
                "status": "error",
                "error": f"Missing credential template {args.credential_template}",
            },
            EXIT_ERROR,
        )

    desc = load_yaml(desc_path) or {}
    checked.append(args.descriptor)
    field = desc.get("external_credential_template")
    expected_fs = args.credential_template
    # Compare normalized templates_dir form
    if not field:
        issues.append(
            {
                "severity": "error",
                "message": "descriptor missing external_credential_template",
            }
        )
    else:
        normalized = field.replace("{{ templates_dir }}", "templates")
        if normalized != expected_fs.replace("\\", "/"):
            issues.append(
                {
                    "severity": "warning",
                    "message": (
                        f"descriptor path {field!r} does not match "
                        f"credential-template arg {args.credential_template!r}"
                    ),
                }
            )

    cred_doc = load_yaml(cred_path) or {}
    checked.append(args.credential_template)
    schema_path = None
    if args.schemas_dir:
        schema_path = args.schemas_dir / "credential.schema.json"
    else:
        schema_path = find_schema(repo, "credential.schema.json")
    if schema_path and schema_path.is_file():
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(cred_doc, schema)
        except jsonschema.ValidationError as exc:
            issues.append(
                {
                    "severity": "error",
                    "message": f"credential template schema: {exc.message}",
                }
            )

    if not isinstance(cred_doc, dict):
        issues.append({"severity": "error", "message": "credential template root must be mapping"})
    else:
        for cred_id, entry in cred_doc.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "external":
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{cred_id}: type must be external",
                    }
                )
            if "data" in entry:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{cred_id}: must not have data",
                    }
                )
            props = entry.get("properties")
            if props is not None:
                for p in props:
                    if not isinstance(p, dict) or "name" not in p:
                        issues.append(
                            {
                                "severity": "error",
                                "message": f"{cred_id}: properties must use - name:",
                            }
                        )
            if entry.get("create") is False:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{cred_id}: omit create:false in final YAML",
                    }
                )
            if "writeToStore" in entry:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{cred_id}: writeToStore must not appear in Credential YAML",
                    }
                )
            rrp = entry.get("remoteRefPath")
            if isinstance(rrp, str) and path_contains_cred_id(rrp, cred_id):
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{cred_id}: remoteRefPath must not append credId",
                    }
                )
            if isinstance(rrp, str) and "{{ current_env.namespace }}" in rrp:
                issues.append(
                    {
                        "severity": "error",
                        "message": (
                            f"{cred_id}: {{ current_env.namespace }} is not an approved "
                            "Template Jinja variable"
                        ),
                    }
                )

    for rel in args.macro_files:
        path = repo / rel
        if not path.is_file():
            issues.append({"severity": "error", "message": f"Missing macro file {rel}"})
            continue
        checked.append(rel)
        doc = load_yaml(path)
        for hit in find_remaining_macros(doc):
            if hit.get("technical"):
                issues.append(
                    {
                        "severity": "warning",
                        "message": f"{rel}: macro in technical scope at {hit.get('path')}",
                    }
                )
            else:
                issues.append(
                    {
                        "severity": "error",
                        "message": f"{rel}: leftover macro at {hit.get('path')}",
                    }
                )

    errors = [i for i in issues if i["severity"] == "error"]
    status = "ok" if not errors else "error"
    emit(
        {
            "status": status,
            "mode": "analyze",
            "checked_files": checked,
            "issues": issues,
            "error_count": len(errors),
            "warning_count": len(issues) - len(errors),
        },
        EXIT_OK if status == "ok" else EXIT_ERROR,
    )


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
