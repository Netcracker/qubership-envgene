#!/usr/bin/env python3
"""Run instance-repository migration script smoke tests."""

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
    if not proc.stdout.strip():
        raise AssertionError(f"empty stdout: stderr={proc.stderr}")
    return json.loads(proc.stdout)


def confirmed(cred_id: str, source: str, **kwargs) -> dict:
    base = {
        "credId": cred_id,
        "sourcePath": source,
        "tier": "passport-tier",
        "scope": "cluster",
        "creationOwner": "pre-existing",
        "evidence": ["test confirmation"],
        "confidence": "confirmed",
        "proposedCreate": False,
        "proposedRemoteRefPath": "cluster",
        "needsReview": False,
        "writeToStore": True,
    }
    base.update(kwargs)
    return base


def main() -> None:
    proc = run(["inventory.py", "--repo", str(FIXTURES)])
    data = parse(proc)
    assert proc.returncode == 0, proc.stderr
    assert data["status"] == "ok"

    proc = run(["classify_credentials.py", "--repo", str(FIXTURES)])
    data = parse(proc)
    assert proc.returncode == 2, (proc.returncode, proc.stdout)
    assert data["status"] == "NEEDS_INPUT"
    dbaas = next(c for c in data["credentials"] if c["credId"] == "dbaas")
    assert dbaas["creationOwner"] == "unknown"
    assert dbaas["needsReview"] is True
    assert dbaas["proposedCreate"] is None
    consul = next(c for c in data["credentials"] if c["credId"] == "consul")
    assert consul["creationOwner"] == "unknown"

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(FIXTURES, work)
        passport = "environments/cluster/cloud-passport/cluster-creds.yml"

        # refuse without decisions
        decisions_path = Path(tmp) / "empty.json"
        decisions_path.write_text("[]", encoding="utf-8")
        proc = run(
            [
                "convert_credential_files.py",
                "--repo",
                str(work),
                "--files",
                passport,
                "--decisions-json",
                str(decisions_path),
                "--plan",
            ]
        )
        data = parse(proc)
        assert proc.returncode == 2
        assert data["status"] == "NEEDS_INPUT"

        # confirmed pre-existing (omit create); rename away from provider markers for happy path
        # Use shared-cred which has no provider marker in classify - convert shared file
        shared = "environments/cluster/shared-credentials/shared-credentials.yml"
        decisions = [
            confirmed(
                "shared-cred",
                shared,
                tier="external-tier",
                scope="shared",
                proposedRemoteRefPath="external",
            )
        ]
        decisions_path.write_text(json.dumps(decisions), encoding="utf-8")
        proc = run(
            [
                "convert_credential_files.py",
                "--repo",
                str(work),
                "--files",
                shared,
                "--decisions-json",
                str(decisions_path),
                "--apply",
            ]
        )
        data = parse(proc)
        assert proc.returncode == 0, proc.stdout
        written = json.loads(
            json.dumps(
                __import__("yaml").safe_load(
                    (work / shared).read_text(encoding="utf-8")
                )
            )
        )
        assert "create" not in written["shared-cred"]
        assert written["shared-cred"]["remoteRefPath"] == "external"
        assert "writeToStore" not in written["shared-cred"]

        # refuse ambiguous decision
        bad = [
            confirmed(
                "dbaas",
                passport,
                creationOwner="unknown",
                confidence="ambiguous",
                needsReview=True,
                proposedCreate=None,
                proposedRemoteRefPath=None,
            )
        ]
        decisions_path.write_text(json.dumps(bad), encoding="utf-8")
        proc = run(
            [
                "convert_credential_files.py",
                "--repo",
                str(work),
                "--files",
                passport,
                "--decisions-json",
                str(decisions_path),
                "--plan",
            ]
        )
        assert parse(proc)["status"] == "NEEDS_INPUT"

        # confirmed passport without provider markers - use renamed entries in a copy
        # convert consul with confirmed provider (false create)
        provider_dec = [
            confirmed(
                "consul",
                passport,
                creationOwner="provider",
                proposedCreate=False,
                proposedRemoteRefPath="cluster",
                confidence="confirmed",
                needsReview=False,
            ),
            confirmed(
                "dbaas",
                passport,
                creationOwner="pre-existing",
                proposedCreate=False,
                proposedRemoteRefPath="cluster",
                confidence="confirmed",
                needsReview=False,
            ),
        ]
        decisions_path.write_text(json.dumps(provider_dec), encoding="utf-8")
        proc = run(
            [
                "convert_credential_files.py",
                "--repo",
                str(work),
                "--files",
                passport,
                "--decisions-json",
                str(decisions_path),
                "--apply",
            ]
        )
        data = parse(proc)
        assert proc.returncode == 0, proc.stdout

        proc = run(
            [
                "replace_macros.py",
                "--repo",
                str(work),
                "--files",
                "environments/cluster/cloud-passport/cluster.yml",
                "--apply",
            ]
        )
        assert parse(proc)["status"] == "ok", proc.stdout

        proc = run(["fix_shared_master_refs.py", "--repo", str(work), "--apply"])
        assert parse(proc)["status"] == "ok"

        sys_file = "configuration/credentials/credentials.yml"
        decisions_path.write_text(
            json.dumps(
                [
                    confirmed(
                        "self-token",
                        sys_file,
                        tier="external-tier",
                        scope="system",
                        creationOwner="pre-existing",
                        proposedCreate=False,
                        proposedRemoteRefPath="external",
                    )
                ]
            ),
            encoding="utf-8",
        )
        proc = run(
            [
                "convert_credential_files.py",
                "--repo",
                str(work),
                "--files",
                sys_file,
                "--decisions-json",
                str(decisions_path),
                "--apply",
            ]
        )
        assert parse(proc)["status"] == "ok", proc.stdout

        proc = run(
            [
                "cleanup_generated.py",
                "--repo",
                str(work),
                "--environments",
                "cluster/env",
                "--apply",
            ]
        )
        assert parse(proc)["status"] == "ok"

        proc = run(
            [
                "validate_instance.py",
                "--repo",
                str(work),
                "--schemas-dir",
                str(SCHEMAS),
                "--macro-files",
                "environments/cluster/cloud-passport/cluster.yml",
            ]
        )
        data = parse(proc)
        assert proc.returncode == 0, proc.stdout
        assert data["status"] == "ok"

    print("ALL INSTANCE SCRIPT TESTS PASSED")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print("FAILED:", exc)
        sys.exit(1)
