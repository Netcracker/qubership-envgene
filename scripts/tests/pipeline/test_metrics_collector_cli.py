import json
from types import SimpleNamespace

import pytest

from pipeline.metrics_collector_cli import main
from pipeline.metrics_collector_activity import MetricsCollectorActivity


@pytest.mark.parametrize(
    ("args", "job_status", "event_type", "status"),
    [
        (["start"], "running", "start", "IN_PROGRESS"),
        (["running"], "running", "running", "IN_PROGRESS"),
        (["running", "--status", "FAILED"], "failed", "running", "FAILED"),
        (["stop"], "success", "stop", "SUCCESS"),
        (["stop"], "failed", "stop", "FAILED"),
        (["stop"], "canceled", "stop", "CANCELLED"),
        (["stop"], "skipped", "stop", "SKIPPED"),
        (["stop"], "", "stop", "UNKNOWN"),
        (["stop", "--status", "FAILED"], "success", "stop", "FAILED"),
    ],
)
def test_hook_events(monkeypatch, args, job_status, event_type, status):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("METRICS_COLLECTOR_TRACE_ID", "shared-trace")
    monkeypatch.setenv("METRICS_COLLECTOR_PARENT_ID", "parent")
    monkeypatch.setenv("CI_JOB_NAME", "sync")
    monkeypatch.setenv("CI_JOB_STATUS", job_status)
    monkeypatch.setenv("PIPELINE_TYPE", "GITLAB_DEPLOY")
    monkeypatch.delenv("ENV_NAMES", raising=False)
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )
    assert main(args) == 0
    event = calls[0]
    assert event["type"] == event_type
    assert event["status"] == status
    assert event["traceid"] == "shared-trace"
    assert event["parentid"] == "parent"
    assert event["technicalname"] == "sync"
    assert event["data"]["inputParameters"] == {"PIPELINE_TYPE": "GITLAB_DEPLOY"}
    assert "steps" not in event["data"]


def test_disabled_hooks_do_not_post(monkeypatch, capsys):
    monkeypatch.delenv("METRICS_COLLECTOR_URL", raising=False)
    def unexpected_post(*args, **kwargs):
        pytest.fail("Disabled integration must not POST")
    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", unexpected_post)
    for event in ("trace-id", "start", "running", "stop"):
        assert main([event]) == 0
    assert capsys.readouterr().out == ""


def test_trace_id_can_be_exported_and_reused(monkeypatch, capsys):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.delenv("METRICS_COLLECTOR_TRACE_ID", raising=False)
    assert main(["trace-id"]) == 0
    trace_id = capsys.readouterr().out.strip()
    assert len(trace_id) == 32
    monkeypatch.setenv("METRICS_COLLECTOR_TRACE_ID", trace_id)
    assert main(["trace-id"]) == 0
    assert capsys.readouterr().out.strip() == trace_id


@pytest.mark.parametrize(
    ("pipeline_status", "job_status", "expected"),
    [("FAILED", "success", "FAILED"), ("SKIPPED", "success", "SKIPPED"),
     ("SUCCESS", "failed", "FAILED"), ("SUCCESS", "canceled", "CANCELLED"),
     ("SUCCESS", "success", "SUCCESS"), ("CANCELLED", "failed", "FAILED"),
     ("UNKNOWN", "success", "UNKNOWN")],
)
def test_stop_uses_recorded_pipeline_results(monkeypatch, pipeline_status, job_status, expected):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("METRICS_COLLECTOR_TRACE_ID", "shared-trace")
    monkeypatch.setenv("CI_JOB_STATUS", job_status)
    ctx = SimpleNamespace(params={"ENV_NAMES": "cluster/env", "SECRET": "redacted"},
                          sensitive_params=["SECRET"])
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )
    MetricsCollectorActivity(ctx).record_completion(
        pipeline_status, [SimpleNamespace(name="env_build", status=pipeline_status, duration_ms=123)],
    )
    assert calls == []
    assert main(["stop"]) == 0
    assert len(calls) == 1
    assert calls[0]["type"] == "stop"
    assert calls[0]["status"] == expected
    assert calls[0]["data"]["steps"] == [
        {"name": "env_build", "status": pipeline_status, "durationMs": 123},
    ]
    assert "SECRET" not in calls[0]["data"]["inputParameters"]


def test_stop_aggregates_child_results_from_shared_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("METRICS_COLLECTOR_TRACE_ID", "shared-trace")
    monkeypatch.setenv("CI_JOB_STATUS", "success")
    monkeypatch.setenv("METRICS_COLLECTOR_RESULTS_ROOT", str(tmp_path))
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )
    for environment, status in [("cluster/one", "SUCCESS"), ("cluster/two", "FAILED")]:
        monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path / environment))
        ctx = SimpleNamespace(params={"ENV_NAMES": environment}, sensitive_params=[])
        MetricsCollectorActivity(ctx).record_completion(
            status, [SimpleNamespace(name="env_build", status=status, duration_ms=10)],
        )
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    assert main(["stop"]) == 0
    assert len(calls) == 1
    assert calls[0]["status"] == "FAILED"
    assert {step["environment"] for step in calls[0]["data"]["steps"]} == {"cluster/one", "cluster/two"}


def test_stop_ignores_results_from_another_job(monkeypatch):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("METRICS_COLLECTOR_TRACE_ID", "shared-trace")
    monkeypatch.setenv("CI_JOB_ID", "previous-job")
    ctx = SimpleNamespace(params={}, sensitive_params=[])
    MetricsCollectorActivity(ctx).record_completion("FAILED", [])
    monkeypatch.setenv("CI_JOB_ID", "current-job")
    monkeypatch.setenv("CI_JOB_STATUS", "success")
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )
    assert main(["stop"]) == 0
    assert calls[0]["status"] == "SUCCESS"
    assert "steps" not in calls[0]["data"]


@pytest.mark.parametrize("failure", [None, "execute", "copy"])
def test_orchestrator_completion_is_sent_only_by_stop_hook(monkeypatch, failure):
    from unittest.mock import Mock
    from pipeline import orchestrator

    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("METRICS_COLLECTOR_TRACE_ID", "shared-trace")
    monkeypatch.setenv("CI_JOB_STATUS", "success")
    ctx = Mock(params={"ENV_NAMES": "cluster/env"}, sensitive_params=[])
    monkeypatch.setattr(orchestrator.PipelineParametersHandler, "from_env", lambda: ctx)
    for cls in orchestrator.PipelineStep.__subclasses__():
        monkeypatch.setattr(cls, "should_run", lambda self, ctx: False)
    monkeypatch.setattr(orchestrator.GitCommitStep, "should_run", lambda self, ctx: True)

    def execute(self, ctx):
        if failure == "execute":
            raise RuntimeError("step failed")

    def copy(ctx):
        if failure == "copy":
            raise RuntimeError("copy failed")

    monkeypatch.setattr(orchestrator.GitCommitStep, "execute", execute)
    monkeypatch.setattr(orchestrator, "copy_env_artifact", copy)
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )
    if failure == "execute":
        with pytest.raises(RuntimeError, match="step failed"):
            orchestrator.run_single_env_pipeline()
    else:
        orchestrator.run_single_env_pipeline()
    assert [(event["type"], event["status"]) for event in calls] == [
        ("running", "IN_PROGRESS"), ("running", "FAILED" if failure else "SUCCESS"),
    ]
    assert "steps" in calls[1]["data"]
    assert main(["stop"]) == 0
    assert len(calls) == 3
    assert calls[2]["type"] == "stop"
    assert calls[2]["status"] == ("FAILED" if failure else "SUCCESS")
    steps = {step["name"]: step for step in calls[2]["data"]["steps"]}
    assert steps["git_commit"]["status"] == ("FAILED" if failure == "execute" else "SUCCESS")
    assert steps["copy_env_artifact"]["status"] == ("FAILED" if failure == "copy" else "SUCCESS")
    assert steps["env_build"]["status"] == "SKIPPED"


def test_explicit_stop_status_keeps_steps_and_cleans_reports(monkeypatch, tmp_path):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    ctx = SimpleNamespace(params={"ENV_NAMES": "cluster/env"}, sensitive_params=[])
    activity = MetricsCollectorActivity(ctx)
    activity.record_completion("SUCCESS", [SimpleNamespace(name="env_build", status="SUCCESS", duration_ms=10)])
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )

    assert main(["stop", "--status", "FAILED"]) == 0

    assert calls[0]["status"] == "FAILED"
    assert calls[0]["data"]["steps"][0]["name"] == "env_build"
    assert activity._completion_directory().exists()


@pytest.mark.parametrize("job2_status", ["success", "failed", "canceled"])
@pytest.mark.parametrize("job1_stop", [False, True])
def test_two_job_pipeline_flow_with_artifact_handoff(monkeypatch, tmp_path, job2_status, job1_stop):
    import shutil

    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_PIPELINE_ID", "pipeline-1")
    monkeypatch.setenv("CI_PROJECT_ID", "project-1")
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.setenv("PIPELINE_TYPE", "GITLAB_DEPLOY")
    monkeypatch.setenv("OPERATION_TYPE", "DEPLOY")
    monkeypatch.delenv("METRICS_COLLECTOR_TRACE_ID", raising=False)
    monkeypatch.delenv("METRICS_COLLECTOR_RESULTS_ROOT", raising=False)
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )
    assert main(["start"]) == 0
    trace_id = calls[0]["traceid"]
    ctx = SimpleNamespace(
        params={"ENV_NAMES": "cluster/env", "SD_VERSION": "release-1", "ENV_BUILDER": False,
                "CRED_ROTATION_PAYLOAD": "secret"},
        sensitive_params=["CRED_ROTATION_PAYLOAD"],
    )
    activity = MetricsCollectorActivity(ctx)
    activity.send_running()
    results = [SimpleNamespace(name="env_build", status="SUCCESS", duration_ms=10)]
    activity.record_completion("SUCCESS", results)
    activity.send_running(results=results)
    monkeypatch.setenv("CI_JOB_STATUS", "success")
    assert main(["running"]) == 0
    assert activity._completion_directory().exists()
    assert not activity._delivery_receipt().exists()

    if job1_stop:
        assert main(["stop"]) == 0
        assert main(["stop"]) == 0
        assert main(["running"]) == 0
        assert activity._delivery_receipt().exists()
        assert list(activity._completion_directory().glob("*.json"))

    # Simulate downloading J1's artifacts into J2's separate checkout.
    job2_root = tmp_path / "job2"
    shutil.copytree(tmp_path / ".metrics-collector-client", job2_root / ".metrics-collector-client")
    monkeypatch.setenv("CI_PROJECT_DIR", str(job2_root))
    monkeypatch.setenv("CI_JOB_ID", "job-2")
    monkeypatch.setenv("CI_JOB_STATUS", "running")
    monkeypatch.delenv("METRICS_COLLECTOR_TRACE_ID")
    assert main(["running"]) == 0
    monkeypatch.setenv("CI_JOB_STATUS", job2_status)
    assert main(["stop"]) == 0
    assert main(["stop"]) == 0
    assert main(["running"]) == 0

    expected_types = ["start", "running", "running", "running"]
    if job1_stop:
        expected_types.append("stop")
    assert [event["type"] for event in calls] == expected_types + ["running", "stop"]
    assert {event["traceid"] for event in calls} == {trace_id}
    assert all(event["status"] == "IN_PROGRESS" for event in calls if event["type"] != "stop")
    assert calls[-1]["status"] == {"success": "SUCCESS", "failed": "FAILED", "canceled": "CANCELLED"}[job2_status]
    assert calls[3]["data"]["steps"] == [{"name": "env_build", "status": "SUCCESS", "durationMs": 10}]
    for event in calls[-2:]:
        assert "steps" not in event["data"]
        assert event["data"]["inputParameters"] == {
            "ENV_NAMES": "cluster/env", "SD_VERSION": "release-1", "ENV_BUILDER": False,
        }
    assert MetricsCollectorActivity(ctx)._completion_directory().exists()


@pytest.mark.parametrize("outcome", ["FAILED", "CANCELLED", "UNKNOWN"])
def test_running_preserves_outcome_until_hook_requests_stop(monkeypatch, outcome):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_PIPELINE_ID", "pipeline-1")
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.setenv("CI_JOB_STATUS", "success")
    monkeypatch.setenv("PIPELINE_TYPE", "GITLAB_DEPLOY")
    monkeypatch.setenv("OPERATION_TYPE", "DEPLOY")
    ctx = SimpleNamespace(params={}, sensitive_params=[])
    activity = MetricsCollectorActivity(ctx)
    activity.record_completion(outcome, [])
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )

    assert main(["running"]) == 0

    assert len(calls) == 1
    assert calls[0]["type"] == "running"
    assert calls[0]["status"] == "IN_PROGRESS"
    assert activity._completion_directory().exists()
    assert not activity._delivery_receipt().exists()

    assert main(["stop"]) == 0

    assert calls[1]["type"] == "stop"
    assert calls[1]["status"] == outcome
    assert activity._completion_directory().exists()


def test_reports_from_different_jobs_are_not_overwritten(monkeypatch):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_PIPELINE_ID", "pipeline-1")
    ctx = SimpleNamespace(params={"ENV_NAMES": "cluster/env"}, sensitive_params=[])
    for job_id in ("job-1", "job-2"):
        monkeypatch.setenv("CI_JOB_ID", job_id)
        MetricsCollectorActivity(ctx).record_completion(
            "SUCCESS", [SimpleNamespace(name="env_build", status="SUCCESS", duration_ms=10)],
        )
    monkeypatch.setenv("CI_JOB_STATUS", "success")
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )

    assert main(["stop"]) == 0

    assert calls[0]["data"]["steps"] == [{"name": "env_build", "status": "SUCCESS", "durationMs": 10}]


def test_pipeline_results_are_isolated_from_other_pipelines(monkeypatch):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_PIPELINE_ID", "previous-pipeline")
    ctx = SimpleNamespace(params={}, sensitive_params=[])
    previous = MetricsCollectorActivity(ctx)
    previous.record_completion("FAILED", [])
    previous_directory = previous._completion_directory()
    monkeypatch.setenv("CI_PIPELINE_ID", "current-pipeline")
    monkeypatch.setenv("CI_JOB_STATUS", "success")
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )

    assert main(["stop"]) == 0

    assert calls[0]["status"] == "SUCCESS"
    assert "steps" not in calls[0]["data"]
    assert previous_directory.exists()


def test_stop_from_fresh_shell_and_different_directory_is_not_repeated(monkeypatch, tmp_path):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_JOB_ID", "123")
    monkeypatch.setenv("METRICS_COLLECTOR_TRACE_ID", "original-trace")
    monkeypatch.setenv("METRICS_COLLECTOR_PARENT_ID", "original-parent")
    ctx = SimpleNamespace(params={"ENV_NAMES": "cluster/env"}, sensitive_params=[])
    activity = MetricsCollectorActivity(ctx)
    activity.record_completion("FAILED", [])
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.delenv("METRICS_COLLECTOR_TRACE_ID")
    monkeypatch.delenv("METRICS_COLLECTOR_PARENT_ID")
    monkeypatch.setenv("CI_JOB_STATUS", "success")
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(json.loads(kwargs["data"])) or SimpleNamespace(ok=True),
    )

    assert main(["stop"]) == 0
    monkeypatch.delenv("METRICS_COLLECTOR_TRACE_ID")
    assert main(["stop"]) == 0

    assert len(calls) == 1
    assert calls[0]["status"] == "FAILED"
    assert calls[0]["traceid"] == "original-trace"
    assert calls[0]["parentid"] == "original-parent"
    assert activity._completion_directory().exists()
