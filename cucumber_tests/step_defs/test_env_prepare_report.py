import json
import re
import subprocess

from pytest_bdd import given, parsers, scenarios, then

from cucumber_tests.shared_steps.common_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403


scenarios("../features/env-prepare-report.feature")


def _report_path(workspace):
    return workspace.base_dir / "artifacts" / "env-prepare-report.json"


@then("the env_prepare report is published")
def env_prepare_report_is_published(workspace):
    report_path = _report_path(workspace)
    assert report_path.is_file(), f"Expected EnvPrepareReport at {report_path}"


@then("the env_prepare report is not published")
def env_prepare_report_is_not_published(workspace):
    assert not _report_path(workspace).exists()


@then(parsers.parse('the env_prepare report has kind "{kind}" and apiVersion "{api_version}"'))
def env_prepare_report_has_metadata(workspace, kind, api_version):
    report = json.loads(_report_path(workspace).read_text(encoding="utf-8"))
    assert report["kind"] == kind
    assert report["apiVersion"] == api_version


@then(parsers.parse('the env_prepare report contains a skipped step named "{step_name}" without a time'))
def env_prepare_report_contains_skipped_step(workspace, step_name):
    report = json.loads(_report_path(workspace).read_text(encoding="utf-8"))
    step = next(step for step in report["steps"] if step["name"] == step_name)
    assert step["status"] == "SKIPPED"
    assert "time" not in step


@then(parsers.parse('the env_prepare report contains a failed step named "{step_name}"'))
def env_prepare_report_contains_failed_step(workspace, step_name):
    report = json.loads(_report_path(workspace).read_text(encoding="utf-8"))
    step = next(step for step in report["steps"] if step["name"] == step_name)
    assert step["status"] == "FAILED"


@then(parsers.parse('the env_prepare report contains a step named "{step_name}" with a time in "H:MM:SS" format'))
def env_prepare_report_contains_timed_step(workspace, step_name):
    report = json.loads(_report_path(workspace).read_text(encoding="utf-8"))
    step = next(step for step in report["steps"] if step["name"] == step_name)
    assert re.fullmatch(r"[0-9]+:[0-5][0-9]:[0-5][0-9]", step["time"])


@given("Metrics Collector is configured")
def metrics_collector_is_configured(workspace):
    workspace.extra_env = getattr(workspace, "extra_env", {})
    workspace.extra_env["METRICS_COLLECTOR_URL"] = "https://collector.example.com"
    workspace.extra_env["ENVGENE_FAN_OUT_CHILD"] = "1"


@then("the env_prepare report steps match the Metrics Collector activity record")
def report_steps_match_metrics_record(workspace):
    report = json.loads(_report_path(workspace).read_text(encoding="utf-8"))
    records = list((workspace.base_dir / ".metrics-collector-client" / "state").rglob("*.json"))
    assert records, "No Metrics Collector activity record was produced"
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["data"]["steps"] == report["steps"]


@given("the env_prepare report path is occupied by a directory")
def occupy_env_prepare_report_path(workspace):
    (_report_path(workspace)).mkdir(parents=True, exist_ok=True)


@given("the pipeline uses multiple environment names")
def use_multiple_environment_names(workspace):
    workspace.extra_env = getattr(workspace, "extra_env", {})
    workspace.extra_env.update({
        "ENV_NAMES": "test-cluster/test-env,test-cluster/test-env-2",
        "CLUSTER_NAME": "",
        "ENVIRONMENT_NAME": "",
    })


@given("the test workspace is initialized as a Git repository")
def initialize_workspace_as_git_repository(workspace):
    subprocess.run(["git", "init"], cwd=workspace.base_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "bdd-tests@example.com"],
        cwd=workspace.base_dir,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "BDD Tests"],
        cwd=workspace.base_dir,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=workspace.base_dir, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initialize BDD workspace"],
        cwd=workspace.base_dir,
        check=True,
        capture_output=True,
    )


@then("the published artifacts were trimmed")
def published_artifacts_were_trimmed(workspace):
    marker = workspace.base_dir / "artifacts" / "NOT-PUBLISHED.txt"
    assert marker.is_file(), f"Expected artifact trim marker at {marker}"
