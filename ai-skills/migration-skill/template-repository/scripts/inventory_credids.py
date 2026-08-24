#!/usr/bin/env python3
"""Inventory credIds and evidence from Environment Template files (read-only)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import (
    DEFAULT_TEMPLATE_PATH,
    EXIT_ERROR,
    EXIT_NEEDS_INPUT,
    EXIT_OK,
    collect_cred_evidence,
    emit,
    find_descriptors,
    heuristic_provider_markers,
    load_yaml,
)


def resolve_template_files(repo: Path, descriptor: Path) -> list[Path]:
    doc = load_yaml(descriptor) or {}
    files = []
    templates_dir = repo / "templates"
    for key in ("tenant", "cloud", "external_credential_template"):
        val = doc.get(key)
        if isinstance(val, str) and "{{ templates_dir }}" in val:
            rel = val.replace("{{ templates_dir }}", "templates").replace("\\", "/")
            # strip quotes artifacts
            p = repo / rel
            if p.is_file():
                files.append(p)
    for ns in doc.get("namespaces") or []:
        if isinstance(ns, dict):
            val = ns.get("template_path")
            if isinstance(val, str) and "{{ templates_dir }}" in val:
                rel = val.replace("{{ templates_dir }}", "templates")
                p = repo / rel
                if p.is_file():
                    files.append(p)
    # ParameterSets under templates/parameters
    params = repo / "templates" / "parameters"
    if params.is_dir():
        files.extend(sorted(params.glob("*.yml")))
        files.extend(sorted(params.glob("*.yaml")))
        files.extend(sorted(params.glob("*.j2")))
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument(
        "--descriptors",
        nargs="*",
        help="Relative descriptor paths; default = discover all",
    )
    args = parser.parse_args()
    repo = args.repo.resolve()

    if args.descriptors:
        descriptors = [(repo / d).resolve() for d in args.descriptors]
    else:
        descriptors = find_descriptors(repo)

    if not descriptors:
        emit(
            {
                "status": "error",
                "error": "No Template Descriptors found",
            },
            EXIT_ERROR,
        )

    templates_out = []
    decisions = []
    ambiguous = []

    for desc in descriptors:
        rel_desc = str(desc.relative_to(repo).as_posix())
        files = resolve_template_files(repo, desc)
        merged: dict = {}
        for fpath in files:
            try:
                doc = load_yaml(fpath)
            except Exception as exc:  # noqa: BLE001
                emit(
                    {"status": "error", "error": f"Parse failed {fpath}: {exc}"},
                    EXIT_ERROR,
                )
            evidence = collect_cred_evidence(doc)
            for cid, meta in evidence.items():
                dest = merged.setdefault(
                    cid,
                    {
                        "shapes": set(),
                        "locations": [],
                        "seen_technical": False,
                        "seen_non_technical": False,
                    },
                )
                dest["shapes"] |= meta["shapes"]
                dest["locations"].extend(
                    [f"{fpath.relative_to(repo).as_posix()}:{loc}" for loc in meta["locations"]]
                )
                dest["seen_technical"] = dest["seen_technical"] or meta["seen_technical"]
                dest["seen_non_technical"] = (
                    dest["seen_non_technical"] or meta["seen_non_technical"]
                )

        creds = []
        for cid, meta in sorted(merged.items()):
            shapes = meta["shapes"]
            evidence = [f"locations: {len(meta['locations'])}"]
            markers = heuristic_provider_markers(cid)
            evidence.extend(markers)

            if len(shapes) > 1:
                structure = "conflict"
                ambiguous.append(
                    {
                        "id": f"structure:{rel_desc}:{cid}",
                        "status": "NEEDS_INPUT",
                        "message": (
                            f"{cid} used as both multi_field and single_value. "
                            "Ask the user which structure to use."
                        ),
                        "credId": cid,
                        "descriptor": rel_desc,
                    }
                )
            elif shapes == {"multi_field"}:
                structure = "multi_field"
            elif shapes == {"single_value"}:
                structure = "single_value"
            else:
                structure = "unknown"
                decisions.append(
                    {
                        "id": f"structure:{rel_desc}:{cid}",
                        "status": "NEEDS_INPUT",
                        "message": f"{cid}: structure not determined from references. Ask user.",
                        "credId": cid,
                        "descriptor": rel_desc,
                    }
                )

            if markers:
                owner = "unknown"
                prop_create = None
                prop_path = None
                confidence = "ambiguous"
                needs_review = True
                evidence.append("heuristic only - not proof of provider ownership")
            else:
                owner = "envgene"
                prop_create = True
                prop_path = DEFAULT_TEMPLATE_PATH
                confidence = "proposed"
                needs_review = True

            record = {
                "credId": cid,
                "sourcePath": rel_desc,
                "tier": "env-tier",
                "scope": "environment",
                "structure": structure,
                "creationOwner": owner,
                "evidence": evidence,
                "confidence": confidence,
                "proposedCreate": prop_create,
                "proposedRemoteRefPath": prop_path,
                "needsReview": needs_review,
                "locations": meta["locations"],
                "technical_only": meta["seen_technical"] and not meta["seen_non_technical"],
            }
            creds.append(record)
            if needs_review or structure in ("unknown", "conflict"):
                decisions.append(
                    {
                        "id": f"decision:{rel_desc}:{cid}",
                        "status": "NEEDS_INPUT",
                        "credId": cid,
                        "message": (
                            "Confirm creationOwner, create, remoteRefPath before draft. "
                            "Show evidence and proposals."
                        ),
                        "evidence": evidence,
                        "proposedCreate": prop_create,
                        "proposedRemoteRefPath": prop_path,
                        "creationOwner": owner,
                        "structure": structure,
                        "confidence": confidence,
                    }
                )

        templates_out.append(
            {
                "descriptor": rel_desc,
                "files_scanned": [str(f.relative_to(repo).as_posix()) for f in files],
                "credentials": creds,
            }
        )

    decisions.extend(
        [
            {
                "id": "secret_store",
                "status": "NEEDS_INPUT",
                "message": "Confirm Secret Store id (default_store if applicable).",
            },
        ]
    )

    # dedupe decisions by id
    seen = set()
    uniq = []
    for d in decisions + [{"id": a["id"], **a} for a in ambiguous]:
        if d["id"] in seen:
            continue
        seen.add(d["id"])
        uniq.append(d)

    emit(
        {
            "status": "NEEDS_INPUT",
            "mode": "analyze",
            "templates": templates_out,
            "ambiguous": ambiguous,
            "decisions_needed": uniq,
            "note": (
                "Do not migrate Template System Credentials (stay local). "
                "No secret values included. "
                "Default path proposal uses cloud/name only - not namespace."
            ),
        },
        EXIT_NEEDS_INPUT,
    )


if __name__ == "__main__":
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    main()
