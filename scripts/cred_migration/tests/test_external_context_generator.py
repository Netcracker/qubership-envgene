"""Tests for envgene-external-context-generator CLI (plan + repo → context YAML)."""

import subprocess
import sys

import yaml


def _run(args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "cred_migration.external_context_generator"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _make(tmp_path, relpath, content=""):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def _setup_minimal_repo(tmp_path, cred_data=None):
    """Minimal instance repo + valid plan for a single cred."""
    _make(tmp_path, "configuration/secret-stores.yml",
          yaml.safe_dump({"default_store": {"type": "vault", "mountPath": "kv"}}))
    _make(tmp_path, "environments/credentials/global.yml",
          yaml.safe_dump({"c": {"type": "secret",
                                 "data": cred_data if cred_data is not None else {"secret": "s"}}}))
    plan_path = tmp_path / "migration-plan.yaml"
    plan_path.write_text(yaml.safe_dump({
        "repo_type": "instance",
        "generated_at": "2026-08-06T00:00:00Z",
        "credentials": [{
            "sourceFile": "environments/credentials/global.yml",
            "to_review": {},
            "to_confirm": {"c": {"remoteRefPath": "/external", "create": False,
                                  "writeToStore": True}},
        }],
        "to_delete": {},
    }))
    return plan_path


def test_cli_emits_context_yaml_to_stdout(tmp_path):
    plan_path = _setup_minimal_repo(tmp_path)
    result = _run(["--plan", str(plan_path), "--repo", str(tmp_path)])
    assert result.returncode == 0, result.stderr
    ctx = yaml.safe_load(result.stdout)
    assert ctx == {
        "credentials": {
            "c": {
                "vals": "ref+vault://kv/data/external/c",
                "strategy": "overwrite",
                "data": {"secret": "s"},
            }
        }
    }


def test_cli_defaults_to_cwd_when_no_flags_given(tmp_path):
    """Zero-flag invocation from repo root: --plan defaults to CWD/migration-plan.yaml, --repo to CWD."""
    _setup_minimal_repo(tmp_path)
    result = _run([], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    ctx = yaml.safe_load(result.stdout)
    assert "c" in ctx["credentials"]


def test_cli_writes_to_out_file(tmp_path):
    plan_path = _setup_minimal_repo(tmp_path)
    out = tmp_path / "context.yaml"
    result = _run(["--plan", str(plan_path), "--repo", str(tmp_path), "--out", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()
    ctx = yaml.safe_load(out.read_text())
    assert "c" in ctx["credentials"]


def test_cli_exits_nonzero_on_missing_plan(tmp_path):
    result = _run(["--plan", str(tmp_path / "nope.yaml"), "--repo", str(tmp_path)])
    assert result.returncode == 2
    assert "not found" in result.stderr.lower()


def test_cli_exits_nonzero_on_missing_repo(tmp_path):
    plan_path = _setup_minimal_repo(tmp_path)
    result = _run(["--plan", str(plan_path), "--repo", str(tmp_path / "nowhere")])
    assert result.returncode == 2


def test_cli_warns_on_envgene_null_value_but_still_succeeds(tmp_path):
    plan_path = _setup_minimal_repo(tmp_path, cred_data={"secret": "envgeneNullValue"})
    result = _run(["--plan", str(plan_path), "--repo", str(tmp_path)])
    # Skipped is a warning, not an error → exit 0 with empty credentials block.
    assert result.returncode == 0
    assert "envgeneNullValue" in result.stderr
    ctx = yaml.safe_load(result.stdout)
    assert ctx["credentials"] == {}


def test_cli_exits_nonzero_on_multi_store(tmp_path):
    _make(tmp_path, "configuration/secret-stores.yml",
          yaml.safe_dump({"a": {"type": "vault"}, "b": {"type": "aws"}}))
    plan_path = tmp_path / "migration-plan.yaml"
    plan_path.write_text(yaml.safe_dump({
        "repo_type": "instance", "credentials": [], "to_delete": {},
    }))
    result = _run(["--plan", str(plan_path), "--repo", str(tmp_path)])
    assert result.returncode == 2
    assert "multiple" in result.stderr.lower()
