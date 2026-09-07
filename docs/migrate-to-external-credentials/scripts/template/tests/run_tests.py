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


def _find_schemas() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "schemas"
        if candidate.is_dir():
            return candidate
    raise SystemExit("schemas/ directory not found walking up from tests")


SCHEMAS = _find_schemas()

sys.path.insert(0, str(SCRIPTS))
from common import (  # noqa: E402
    _strip_jinja2_for_yaml,
    collect_paramset_names,
    collect_paramset_names_from_text,
    load_yaml,
)


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


def test_j2_yaml_preprocessing() -> None:
    sample = """\
---
name: "{{ current_env.cloud }}"
{% if current_env.additionalTemplateVariables.site == "offsite" %}
deployParameterSets:
  - bound-set
{% elif current_env.additionalTemplateVariables.site == "onsite" %}
deployParameterSets:
  - other-set
{%- endif -%}
{{ current_env.additionalTemplateVariables.cloudParameters | to_nice_yaml | indent(2) }}
template_path: "{{ templates_dir }}/env_templates/demo/cloud.yml.j2"
"""
    stripped = _strip_jinja2_for_yaml(sample)
    assert "{%" not in stripped
    assert "to_nice_yaml" not in stripped
    assert 'name: "{{ current_env.cloud }}"' in stripped
    assert 'template_path: "{{ templates_dir }}/env_templates/demo/cloud.yml.j2"' in stripped
    assert "bound-set" in stripped
    assert "other-set" in stripped

    import yaml

    doc = yaml.safe_load(stripped)
    assert doc["name"] == "{{ current_env.cloud }}"
    assert set(collect_paramset_names(doc)) == {"other-set"}
    assert set(collect_paramset_names_from_text(sample, strip_jinja=True)) == {
        "bound-set",
        "other-set",
    }

    j2_fixture = (
        FIXTURES
        / "templates"
        / "env_templates"
        / "demo"
        / "ns-jinja-blocks.yml.j2"
    )
    raw = j2_fixture.read_text(encoding="utf-8")
    assert set(collect_paramset_names_from_text(raw, strip_jinja=True)) == {
        "paramset-with-creds",
        "other-set",
    }
    loaded = load_yaml(j2_fixture)
    assert loaded["name"] == "{{ current_env.name }}-ns"
    assert set(collect_paramset_names(loaded)) == {"other-set"}
    assert loaded["template_path"] == (
        "{{ templates_dir }}/env_templates/demo/cloud.yml.j2"
    )


def main() -> None:
    test_j2_yaml_preprocessing()
    proc = run(["preflight.py", "--repo", str(FIXTURES)])
    data = parse(proc)
    assert proc.returncode == 0, (proc.returncode, proc.stdout)
    assert data["status"] == "ok"
    assert data["summary"]["credentials"] == 4
    assert any(
        w["kind"] == "missing_external_credential_template_field"
        for w in data["warnings"]
    ), data["warnings"]
    by_id = {c["credId"]: c for c in data["templates"][0]["credentials"]}
    assert by_id["app-db-cred"]["structure"] == "multi_field"
    assert by_id["app-token"]["structure"] == "single_value"

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
        assert written["app-db-cred"]["secretStore"] == "default_store"
        assert "create" not in written["ns-deploy-cred"]
        assert written["ns-deploy-cred"]["secretStore"] == "default_store"
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
