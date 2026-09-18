import json
from types import SimpleNamespace

import pytest

from pipeline.metrics_collector_cli import main


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
