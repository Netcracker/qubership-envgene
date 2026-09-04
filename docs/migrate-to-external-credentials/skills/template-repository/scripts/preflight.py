#!/usr/bin/env python3
"""Preflight checks for Template Repository External Credentials migration.

Read-only. Scans template and ParameterSet files for credential macros and
migration blockers. Exit 0 when safe to continue; exit 2 when blockers need
user action; exit 1 on errors.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_TEMPLATE_PATH,
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    NAMESPACE_JINJA,
    collect_cred_evidence,
    emit,
    find_descriptors,
    find_macro_issues,
    heuristic_provider_markers,
    list_credential_scan_files,
    load_yaml,
    resolve_descriptor_paths,
)


def _rel(repo: Path, path: Path) -> str:
    return str(path.relative_to(repo).as_posix())


def _issue(
    *,
    kind: str,
    severity: str,
    message: str,
    path: str | None = None,
    cred_id: str | None = None,
    suggested_action: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "kind": kind,
        "severity": severity,
        "message": message,
    }
    if path is not None:
        item["path"] = path
    if cred_id is not None:
        item["credId"] = cred_id
    if suggested_action is not None:
        item["suggested_action"] = suggested_action
    item.update(extra)
    return item


def _check_existing_credential_template(
    repo: Path, path: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    rel = _rel(repo, path)
    try:
        doc = load_yaml(path) or {}
    except Exception as exc:  # noqa: BLE001
        blockers.append(
            _issue(
                kind="credential_template_parse_error",
                severity="blocker",
                path=rel,
                message=f"Failed to parse Credential Template: {exc}",
            )
        )
        return blockers, warnings

    if not isinstance(doc, dict):
        return blockers, warnings

    for cred_id, entry in doc.items():
        if not isinstance(entry, dict) or "type" not in entry:
            continue
        if entry.get("type") != "external":
            warnings.append(
                _issue(
                    kind="non_external_in_credential_template",
                    severity="warning",
                    path=rel,
                    cred_id=str(cred_id),
                    message=(
                        f"Credential Template entry type is '{entry.get('type')}', "
                        "expected external"
                    ),
                )
            )
        if "data" in entry:
            blockers.append(
                _issue(
                    kind="data_in_credential_template",
                    severity="blocker",
                    path=rel,
                    cred_id=str(cred_id),
                    message="Credential Template must not contain data",
                    suggested_action="Remove data from the Credential Template",
                )
            )
        if "writeToStore" in entry:
            blockers.append(
                _issue(
                    kind="write_to_store_in_yaml",
                    severity="blocker",
                    path=rel,
                    cred_id=str(cred_id),
                    message="writeToStore must not appear in Credential Template YAML",
                    suggested_action="Remove writeToStore",
                )
            )
        if not entry.get("secretStore"):
            blockers.append(
                _issue(
                    kind="missing_secret_store",
                    severity="blocker",
                    path=rel,
                    cred_id=str(cred_id),
                    message=(
                        "secretStore is required; EnvGene does not fill schema defaults"
                    ),
                    suggested_action="Set secretStore: default_store (or a store id from secret-stores.yml)",
                )
            )
        rrp = entry.get("remoteRefPath")
        if isinstance(rrp, str) and NAMESPACE_JINJA in rrp:
            blockers.append(
                _issue(
                    kind="namespace_in_remote_ref_path",
                    severity="blocker",
                    path=rel,
                    cred_id=str(cred_id),
                    message=(
                        "EnvGene does not support {{ current_env.namespace }} in "
                        "Credential Template Jinja context"
                    ),
                    suggested_action=(
                        f"Use default '{DEFAULT_TEMPLATE_PATH}' or a confirmed static suffix"
                    ),
                )
            )
        if entry.get("create") is False:
            warnings.append(
                _issue(
                    kind="create_false_literal",
                    severity="warning",
                    path=rel,
                    cred_id=str(cred_id),
                    message="Prefer omitting create instead of writing create: false",
                )
            )
    return blockers, warnings


def analyze_descriptor(repo: Path, descriptor: Path) -> dict[str, Any]:
    rel_desc = _rel(repo, descriptor)
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    try:
        resolved = resolve_descriptor_paths(repo, descriptor)
    except Exception as exc:  # noqa: BLE001
        return {
            "descriptor": rel_desc,
            "blockers": [
                _issue(
                    kind="descriptor_parse_error",
                    severity="blocker",
                    path=rel_desc,
                    message=str(exc),
                )
            ],
            "warnings": [],
            "credentials": [],
            "files_scanned": [],
        }

    for missing in resolved["missing"]:
        blockers.append(
            _issue(
                kind="missing_referenced_file",
                severity="blocker",
                path=rel_desc,
                message=f"Descriptor references missing file: {missing}",
                suggested_action="Fix the descriptor path or restore the file",
            )
        )

    if not resolved["has_external_credential_template_field"]:
        warnings.append(
            _issue(
                kind="missing_external_credential_template_field",
                severity="warning",
                path=rel_desc,
                message=(
                    "external_credential_template is not set yet "
                    "(expected before migration completes)"
                ),
                suggested_action=(
                    "Create templates/external-credentials/<descriptor-stem>.yml.j2 "
                    "and register it on the descriptor"
                ),
            )
        )

    if resolved["credential_template"] is not None:
        b, w = _check_existing_credential_template(repo, resolved["credential_template"])
        blockers.extend(b)
        warnings.extend(w)

    scan_files = list_credential_scan_files(repo, descriptor)
    merged: dict[str, dict[str, Any]] = {}

    for fpath in scan_files:
        rel = _rel(repo, fpath)
        try:
            doc = load_yaml(fpath)
        except Exception as exc:  # noqa: BLE001
            blockers.append(
                _issue(
                    kind="parse_error",
                    severity="blocker",
                    path=rel,
                    message=f"Failed to parse: {exc}",
                )
            )
            continue

        for issue in find_macro_issues(doc):
            issue = {**issue, "file": rel}
            if issue.get("severity") == "blocker":
                blockers.append(issue)
            else:
                warnings.append(issue)

        evidence = collect_cred_evidence(doc)
        for cred_id, meta in evidence.items():
            dest = merged.setdefault(
                cred_id,
                {
                    "shapes": set(),
                    "locations": [],
                    "seen_technical": False,
                    "seen_non_technical": False,
                },
            )
            dest["shapes"] |= meta["shapes"]
            dest["locations"].extend([f"{rel}:{loc}" for loc in meta["locations"]])
            dest["seen_technical"] = dest["seen_technical"] or meta["seen_technical"]
            dest["seen_non_technical"] = (
                dest["seen_non_technical"] or meta["seen_non_technical"]
            )

    credentials: list[dict[str, Any]] = []
    for cred_id, meta in sorted(merged.items()):
        shapes = meta["shapes"]
        if len(shapes) > 1:
            structure = "conflict"
            blockers.append(
                _issue(
                    kind="structure_conflict",
                    severity="blocker",
                    path=rel_desc,
                    cred_id=cred_id,
                    message=(
                        f"{cred_id} is used as both multi_field and single_value; "
                        "confirm the intended structure"
                    ),
                    suggested_action="Pick one structure before drafting the Credential Template",
                    locations=meta["locations"],
                )
            )
        elif shapes == {"multi_field"}:
            structure = "multi_field"
        elif shapes == {"single_value"}:
            structure = "single_value"
        else:
            structure = "unknown"
            warnings.append(
                _issue(
                    kind="structure_unknown",
                    severity="warning",
                    path=rel_desc,
                    cred_id=cred_id,
                    message=f"{cred_id}: structure not determined from references",
                    suggested_action="Confirm multi_field vs single_value with the owner",
                    locations=meta["locations"],
                )
            )

        markers = heuristic_provider_markers(cred_id)
        for marker in markers:
            warnings.append(
                _issue(
                    kind="heuristic_review",
                    severity="warning",
                    path=rel_desc,
                    cred_id=cred_id,
                    message=marker,
                    suggested_action=(
                        "Confirm ownership - do not put Passport/Shared-owned "
                        "credIds into the Credential Template without confirmation"
                    ),
                )
            )

        if meta["seen_technical"] and not meta["seen_non_technical"]:
            warnings.append(
                _issue(
                    kind="technical_only_cred",
                    severity="warning",
                    path=rel_desc,
                    cred_id=cred_id,
                    message=(
                        f"{cred_id} appears only in technicalConfigurationParameters "
                        "(out of migration scope)"
                    ),
                )
            )

        credentials.append(
            {
                "credId": cred_id,
                "structure": structure,
                "locations": meta["locations"],
                "technical_only": meta["seen_technical"] and not meta["seen_non_technical"],
                "proposedRemoteRefPath": DEFAULT_TEMPLATE_PATH,
                "needsReview": bool(markers) or structure in ("unknown", "conflict"),
            }
        )

    return {
        "descriptor": rel_desc,
        "descriptor_stem": Path(rel_desc).stem,
        "files_scanned": [_rel(repo, p) for p in scan_files],
        "credential_template": (
            _rel(repo, resolved["credential_template"])
            if resolved["credential_template"] is not None
            else None
        ),
        "credentials": credentials,
        "blockers": blockers,
        "warnings": warnings,
    }


def run_preflight(repo: Path, descriptors: list[Path] | None = None) -> dict[str, Any]:
    found = descriptors if descriptors is not None else find_descriptors(repo)
    if not found:
        return {
            "status": "error",
            "error": "No Template Descriptors found under templates/env_templates/",
        }

    templates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for desc in found:
        result = analyze_descriptor(repo, desc)
        blockers.extend(result.pop("blockers"))
        warnings.extend(result.pop("warnings"))
        templates.append(result)

    status = "ok" if not blockers else "NEEDS_INPUT"
    return {
        "status": status,
        "mode": "preflight",
        "repo": str(repo),
        "templates": templates,
        "blockers": blockers,
        "warnings": warnings,
        "summary": {
            "descriptors": len(templates),
            "blockers": len(blockers),
            "warnings": len(warnings),
            "credentials": sum(len(t["credentials"]) for t in templates),
        },
        "note": (
            "Read-only preflight. Fix blockers, then re-run. "
            f"Default path proposal is '{DEFAULT_TEMPLATE_PATH}' "
            "(no namespace). Secret values are never printed."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="Template Repository root")
    parser.add_argument(
        "--descriptors",
        nargs="*",
        help="Optional relative descriptor paths; default = discover all",
    )
    args = parser.parse_args()
    repo = args.repo.resolve()
    if not repo.is_dir():
        emit({"status": "error", "error": f"Not a directory: {repo}"}, EXIT_ERROR)

    descriptors = None
    if args.descriptors:
        descriptors = [(repo / d).resolve() for d in args.descriptors]

    result = run_preflight(repo, descriptors)
    if result.get("status") == "error":
        emit(result, EXIT_ERROR)
    if result.get("status") == "NEEDS_INPUT":
        emit(result, EXIT_NEEDS_INPUT)
    emit(result, EXIT_OK)


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
