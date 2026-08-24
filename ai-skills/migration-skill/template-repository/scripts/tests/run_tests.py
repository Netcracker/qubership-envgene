#!/usr/bin/env python3
"""Smoke tests for template-repository migration scripts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "repo"
SCHEMAS = Path(__file__).resolve().parents[5] / "schemas"


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=SCRIPTS,
        capture_output=True,
        text=True,
        check=False,
    )


def parse(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


def main() -> None:
    proc = run(["inventory_credids.py", "--repo", str(FIXTURES)])
    data = parse(proc)
    assert proc.returncode == 2, (proc.returncode, proc.stdout)
    assert data["status"] == "NEEDS_INPUT"
    creds = data["templates"][0]["credentials"]
    by_id = {c["credId"]: c for c in creds}
    assert by_id["app-db-cred"]["structure"] == "multi_field", by_id
    assert by_id["app-db-cred"]["proposedRemoteRefPath"] == (
        "{{ current_env.cloud }}/{{ current_env.name }}"
    )
    assert by_id["app-db-cred"]["needsReview"] is True
    assert by_id["app-token"]["structure"] == "single_value", by_id

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(FIXTURES, work)

        # refuse ambiguous
        proc = run(
            [
                "draft_credential_template.py",
                "--repo",
                str(work),
                "--output",
                "templates/env_templates/demo/external-credentials.yml.j2",
                "--credentials-json",
                json.dumps(
                    [
                        {
                            "credId": "x",
                            "structure": "multi_field",
                            "creationOwner": "unknown",
                            "proposedCreate": None,
                            "needsReview": True,
                            "confidence": "ambiguous",
                        }
                    ]
                ),
                "--plan",
            ]
        )
        assert proc.returncode == 2

        cred_json = json.dumps(
            [
                {
                    "credId": "app-db-cred",
                    "structure": "multi_field",
                    "creationOwner": "envgene",
                    "proposedCreate": True,
                    "proposedRemoteRefPath": "{{ current_env.cloud }}/{{ current_env.name }}",
                    "confidence": "confirmed",
                    "needsReview": False,
                },
                {
                    "credId": "app-token",
                    "structure": "single_value",
                    "creationOwner": "envgene",
                    "proposedCreate": True,
                    "proposedRemoteRefPath": "{{ current_env.cloud }}/{{ current_env.name }}",
                    "confidence": "confirmed",
                    "needsReview": False,
                },
                {
                    "credId": "ns-deploy-cred",
                    "structure": "single_value",
                    "creationOwner": "pre-existing",
                    "proposedCreate": False,
                    "proposedRemoteRefPath": "{{ current_env.cloud }}/{{ current_env.name }}",
                    "confidence": "confirmed",
                    "needsReview": False,
                },
                {
                    "credId": "tenant-cred",
                    "structure": "single_value",
                    "creationOwner": "pre-existing",
                    "proposedCreate": False,
                    "proposedRemoteRefPath": "{{ current_env.cloud }}/{{ current_env.name }}",
                    "confidence": "confirmed",
                    "needsReview": False,
                },
            ]
        )
        out = "templates/env_templates/demo/external-credentials.yml.j2"
        proc = run(
            [
                "draft_credential_template.py",
                "--repo",
                str(work),
                "--output",
                out,
                "--credentials-json",
                cred_json,
                "--apply",
            ]
        )
        assert parse(proc)["status"] == "ok", proc.stdout

        import yaml

        written = yaml.safe_load((work / out).read_text(encoding="utf-8"))
        assert written["app-db-cred"].get("create") is True
        assert "create" not in written["ns-deploy-cred"]
        assert "writeToStore" not in written["ns-deploy-cred"]

        tpl = "{{ templates_dir }}/env_templates/demo/external-credentials.yml.j2"
        proc = run(
            [
                "register_descriptor.py",
                "--repo",
                str(work),
                "--descriptor",
                "templates/env_templates/demo-sample.yml",
                "--template-path",
                tpl,
                "--apply",
            ]
        )
        assert parse(proc)["status"] == "ok", proc.stdout

        proc = run(
            [
                "replace_macros.py",
                "--repo",
                str(work),
                "--files",
                "templates/env_templates/demo/cloud.yml.j2",
                "--apply",
            ]
        )
        assert parse(proc)["status"] == "ok", proc.stdout

        proc = run(
            [
                "validate_template.py",
                "--repo",
                str(work),
                "--descriptor",
                "templates/env_templates/demo-sample.yml",
                "--credential-template",
                out,
                "--macro-files",
                "templates/env_templates/demo/cloud.yml.j2",
                "--schemas-dir",
                str(SCHEMAS),
            ]
        )
        data = parse(proc)
        assert proc.returncode == 0, proc.stdout
        assert data["status"] == "ok"

    print("ALL TEMPLATE SCRIPT TESTS PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print("FAILED:", exc)
        sys.exit(1)
