import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def run_ci(tmp_path):
    root = Path(__file__).resolve().parents[3]
    workflow = yaml.safe_load((root / "github_workflows/instance-repo-pipeline/.github/workflows/Envgene.yml").read_text())
    script = next(step["run"] for job in workflow["jobs"].values() for step in job.get("steps", [])
                  if step.get("name") == "EnvGene Execution")
    (tmp_path / "envgene-vars.env").touch()
    command = (
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "program = Path(sys.argv[0]).name\n"
        "with open(os.environ['CALL_LOG'], 'a') as stream:\n"
        "    stream.write(json.dumps({'program': program, 'args': sys.argv[1:]}) + '\\n')\n"
        "if sys.argv[1].endswith('/pipeline/orchestrator.py'):\n"
        "    sys.exit(int(os.environ.get('ORCHESTRATOR_EXIT', '0')))\n"
        "if program == 'argo-dpg':\n"
        "    sys.exit(int(os.environ.get('CLEANUP_EXIT', '0')))\n"
    )
    for name in ("python3", "argo-dpg"):
        executable = tmp_path / name
        executable.write_text(command)
        executable.chmod(0o755)

    def run(**overrides):
        log = tmp_path / "calls.jsonl"
        log.write_text("")
        env = os.environ | {
            "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
            "CALL_LOG": str(log), "PIPELINE_TYPE": "GITLAB_DEPLOY", "OPERATION_TYPE": "CLEAN",
            "BGD_OPERATION": "", "FULL_ENV_NAME": "cluster/env", "CLUSTER_NAME": "cluster",
            "ENVIRONMENT_NAME": "env", "CI_PROJECT_DIR": str(tmp_path), "NAMESPACE_NAMES": "",
            "ENVGENE_LOG_LEVEL": "INFO", "CMDB_IMPORT": "false",
        } | overrides
        env.pop("ENVGENE_AGE_PUBLIC_KEY", None)
        result = subprocess.run(["bash", "-c", script], cwd=tmp_path, env=env, text=True, capture_output=True)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        return result, calls

    return run


@pytest.mark.parametrize("namespaces", ["", "env-core;env-bss"])
def test_clean_runs_separately_after_orchestrator(run_ci, namespaces):
    result, calls = run_ci(NAMESPACE_NAMES=namespaces)

    assert result.returncode == 0, result.stderr
    assert len(calls) == 2
    assert calls[0]["args"] == ["/module/scripts/pipeline/orchestrator.py"]
    assert calls[1]["program"] == "argo-dpg"
    assert calls[1]["args"][:2] == ["cleanup", "structure"]
    assert f"params.namespace_names={namespaces}" in calls[1]["args"]
    assert "params.environment_id=cluster/env" in calls[1]["args"]


@pytest.mark.parametrize("pipeline, operation, bgd, generates", [
    ("GITLAB_DEPLOY", "DEPLOY", "", True),
    ("GITLAB_DEPLOY", "BGD", "warmup", True),
    ("GITLAB_DEPLOY", "BGD", "promote", False),
    ("LEGACY", "DEPLOY", "", False),
])
def test_other_operations_do_not_run_cleanup(run_ci, pipeline, operation, bgd, generates):
    result, calls = run_ci(PIPELINE_TYPE=pipeline, OPERATION_TYPE=operation, BGD_OPERATION=bgd)

    assert result.returncode == 0, result.stderr
    assert len(calls) == (2 if generates else 1)
    if generates:
        assert calls[1]["args"][1:3] == ["generate", "structure"]


def test_orchestrator_failure_prevents_es_cleanup(run_ci):
    result, calls = run_ci(ORCHESTRATOR_EXIT="17")

    assert result.returncode == 17
    assert len(calls) == 1
    assert calls[0]["args"] == ["/module/scripts/pipeline/orchestrator.py"]


def test_separate_cleanup_failure_fails_job(run_ci):
    result, calls = run_ci(CLEANUP_EXIT="23")

    assert result.returncode == 23
    assert len(calls) == 2
    assert calls[1]["program"] == "argo-dpg"
