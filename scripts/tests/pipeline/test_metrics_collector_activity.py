import json
import logging
import os
from types import SimpleNamespace

import requests
import pytest

from pipeline.metrics_collector_activity import (
    MAX_EVENT_BODY_BYTES,
    MetricsCollectorActivity,
    build_structured_event_body,
    resolve_trace_id,
    serialize_step_results,
)


def _ctx(**params):
    return SimpleNamespace(
        params={
            "PIPELINE_TYPE": "GITLAB_DEPLOY",
            "ENV_BUILDER": False,
            "EMPTY": "",
            "CRED_ROTATION_PAYLOAD": "secret",
            **params,
        },
        sensitive_params=["CRED_ROTATION_PAYLOAD"],
    )


class _Response:
    ok = True
    status_code = 202
    text = '{"result":"accepted"}'


class _ErrorResponse:
    ok = False
    status_code = 400
    text = '{"error":"type must be start, stop, or start_and_stop"}'


def test_resolve_trace_id_uses_parent_value(monkeypatch):
    monkeypatch.setenv("METRICS_COLLECTOR_TRACE_ID", "parent-trace")

    assert resolve_trace_id() == "parent-trace"


def test_resolve_trace_id_generates_and_exports_value(monkeypatch):
    monkeypatch.delenv("METRICS_COLLECTOR_TRACE_ID", raising=False)

    trace_id = resolve_trace_id()

    assert trace_id
    assert trace_id == trace_id.lower()
    assert len(trace_id) == 32
    assert trace_id == os.environ["METRICS_COLLECTOR_TRACE_ID"]


def test_build_structured_event_body_contains_cloudevent_fields(monkeypatch):
    monkeypatch.setenv("CI_PROJECT_URL", "https://gitlab.example.com/platform/env-instance-repo")
    monkeypatch.setenv("CI_JOB_NAME", "instance_pipeline")
    monkeypatch.setenv("CI_JOB_ID", "5550001")
    monkeypatch.setenv("ENVGENE_DD_VERSION", "1.2.3")
    monkeypatch.setenv("CI_PIPELINE_ID", "987654")
    monkeypatch.setenv("CI_PROJECT_ID", "12345")

    body, headers = build_structured_event_body(
        event_type="start",
        status="IN_PROGRESS",
        trace_id="trace-1",
        parent_id="parent-1",
        data={"kind": "EnvGenePipelineReport", "apiVersion": "v1"},
    )

    event = json.loads(body)
    content_type = headers.get("Content-Type") or headers.get("content-type")
    assert content_type.startswith("application/cloudevents+json")
    assert event["specversion"] == "1.0"
    assert event["source"] == "https://gitlab.example.com/platform/env-instance-repo"
    assert event["type"] == "start"
    assert event["kind"] == "pipeline"
    assert event["kindversion"] == "1.0"
    assert event["traceid"] == "trace-1"
    assert event["parentid"] == "parent-1"
    assert event["technicalname"] == "envgene-instance-pipeline:instance_pipeline"
    assert event["technicalversion"] == "1.2.3"
    assert event["datacontenttype"] == "application/json"
    assert event["subject"] == "5550001"
    assert event["jobid"] == "5550001"
    assert event["pipelineid"] == "987654"
    assert event["projectid"] == "12345"
    assert event["status"] == "IN_PROGRESS"
    assert event["data"] == {"kind": "EnvGenePipelineReport", "apiVersion": "v1"}


def test_build_structured_event_body_omits_empty_parent_id(monkeypatch):
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.delenv("CI_JOB_NAME", raising=False)
    monkeypatch.delenv("ENVGENE_DD_VERSION", raising=False)

    body, _ = build_structured_event_body(
        event_type="start", status="IN_PROGRESS", trace_id="trace-1", parent_id=" ", data={},
    )

    event = json.loads(body)
    assert "parentid" not in event
    assert event["technicalname"] == "envgene-instance-pipeline:"
    assert event["subject"] == "job-1"
    assert event["technicalversion"] == ""


def test_serialize_step_results_formats_rounded_durations():
    results = [
        SimpleNamespace(name="round_down", status="SUCCESS", duration_ms=499),
        SimpleNamespace(name="round_up", status="SUCCESS", duration_ms=500),
        SimpleNamespace(name="hour", status="SUCCESS", duration_ms=3_661_500),
        SimpleNamespace(name="skipped", status="SKIPPED", duration_ms=1000),
    ]

    assert serialize_step_results(results) == [
        {"name": "round_down", "status": "SUCCESS", "time": "0:00:00"},
        {"name": "round_up", "status": "SUCCESS", "time": "0:00:01"},
        {"name": "hour", "status": "SUCCESS", "time": "1:01:02"},
        {"name": "skipped", "status": "SKIPPED"},
    ]


def test_send_skips_when_url_is_absent(monkeypatch):
    calls = []
    monkeypatch.delenv("METRICS_COLLECTOR_URL", raising=False)
    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", lambda **kwargs: calls.append(kwargs))

    MetricsCollectorActivity(_ctx()).send_start()

    assert calls == []


@pytest.mark.parametrize(
    ("ssl_verify", "expected_verify"),
    [(None, True), ("true", True), ("false", False), (" FALSE ", False), ("invalid", True)],
)
def test_send_start_and_stop_events(monkeypatch, ssl_verify, expected_verify):
    calls = []
    if ssl_verify is None:
        monkeypatch.delenv("METRICS_COLLECTOR_SSL_VERIFY", raising=False)
    else:
        monkeypatch.setenv("METRICS_COLLECTOR_SSL_VERIFY", ssl_verify)
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com/base")
    monkeypatch.setenv("ENVGENE_DD_VERSION", "2.3.4")
    monkeypatch.setenv("CI_JOB_NAME", "instance_pipeline")
    monkeypatch.setenv("CI_JOB_ID", "5550001")
    monkeypatch.setenv("GITLAB_USER_LOGIN", "test-user")
    monkeypatch.setenv("GITLAB_USER_EMAIL", "test@example.com")
    monkeypatch.setenv("METRICS_COLLECTOR_PARENT_ID", "parent-1")
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append({"args": args, **kwargs}) or _Response(),
    )

    activity = MetricsCollectorActivity(_ctx(CUSTOM_PARAMS="x"), trace_id="trace-1")
    activity.send_start()
    activity.send_running()
    activity.send_running("SUCCESS", [SimpleNamespace(name="env_build", status="SUCCESS", duration_ms=120)])
    activity.send_stop("SUCCESS")

    assert [json.loads(call["data"])["type"] for call in calls] == ["start", "running", "running", "stop"]
    assert all(call["verify"] is expected_verify for call in calls)
    assert calls[0]["args"][0] == "https://collector.example.com/base/api/v1/activity"
    assert calls[0]["headers"]["Content-Type"] == "application/cloudevents+json"
    assert calls[0]["headers"]["Accept"] == "application/json"
    assert "content-type" not in calls[0]["headers"]

    start = json.loads(calls[0]["data"])
    assert start["status"] == "IN_PROGRESS"
    assert start["traceid"] == "trace-1"
    assert start["parentid"] == "parent-1"
    assert start["technicalname"] == "envgene-instance-pipeline:instance_pipeline"
    assert start["technicalversion"] == "2.3.4"
    assert start["datacontenttype"] == "application/json"
    assert start["subject"] == "5550001"
    assert start["data"]["kind"] == "EnvGenePipelineReport"
    assert start["data"]["apiVersion"] == "v1"
    assert start["data"]["user"] == "test-user"
    assert start["data"]["email"] == "test@example.com"
    config = {item["name"]: item["value"] for item in start["data"]["config"]}
    assert config["PIPELINE_TYPE"] == "GITLAB_DEPLOY"
    assert config["CUSTOM_PARAMS"] == "x"
    assert config["ENV_BUILDER"] == "False"
    assert "EMPTY" not in config
    assert "CRED_ROTATION_PAYLOAD" not in config
    assert "ENV_INVENTORY_CONTENT" not in config
    assert "envgeneVersion" not in start["data"]
    assert "inputParameters" not in start["data"]
    assert "steps" not in start["data"]

    running = json.loads(calls[1]["data"])
    assert running["status"] == "IN_PROGRESS"
    assert "steps" not in running["data"]
    finished = json.loads(calls[2]["data"])
    assert finished["status"] == "SUCCESS"
    assert finished["data"]["steps"] == [{"name": "env_build", "status": "SUCCESS", "time": "0:00:00"}]
    assert "durationMs" not in json.dumps(finished["data"])
    events = [json.loads(call["data"]) for call in calls]
    assert len({event["id"] for event in events}) == 4
    assert {event["traceid"] for event in events} == {"trace-1"}
    assert {event["parentid"] for event in events} == {"parent-1"}
    stop = json.loads(calls[3]["data"])
    assert stop["status"] == "SUCCESS"
    assert stop["technicalversion"] == "2.3.4"
    assert "envgeneVersion" not in stop["data"]
    assert "steps" not in stop["data"]


def test_send_logs_request_body_before_post(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG, logger="pipeline.metrics_collector_activity")
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: _Response(),
    )

    MetricsCollectorActivity(_ctx(), trace_id="trace-1").send_start()

    assert "Sending Metrics Collector activity event:" in caplog.text
    assert '"type": "start"' in caplog.text
    assert all(record.levelno == logging.DEBUG for record in caplog.records
               if record.name == "pipeline.metrics_collector_activity")


def test_send_logs_and_continues_on_transport_error(monkeypatch):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_JOB_ID", "job-1")

    def raise_error(*args, **kwargs):
        raise requests.ConnectionError("collector unavailable")

    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", raise_error)

    MetricsCollectorActivity(_ctx(), trace_id="trace-1").send_start()


def test_send_logs_api_error_response(monkeypatch, caplog):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", lambda *args, **kwargs: _ErrorResponse())

    MetricsCollectorActivity(_ctx(), trace_id="trace-1").send_start()

    assert "status_code=400" in caplog.text
    assert "type must be start, stop, or start_and_stop" in caplog.text


@pytest.mark.parametrize("base_path", ["", "/base", "/base/"])
def test_send_logs_actionable_message_for_missing_endpoint(monkeypatch, caplog, base_path):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com" + base_path)
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    response = SimpleNamespace(
        ok=False,
        status_code=404,
        text="<html><head><title>404 Not Found</title></head><body>nginx</body></html>",
    )
    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", lambda *args, **kwargs: response)

    MetricsCollectorActivity(_ctx(), trace_id="trace-1").send_start()

    assert "endpoint not found (HTTP 404)" in caplog.text
    assert "https://collector.example.com" + base_path.rstrip("/") + "/api/v1/activity" in caplog.text
    assert "Check METRICS_COLLECTOR_URL" in caplog.text
    assert "collector base URL" in caplog.text
    assert "pipeline execution will continue" in caplog.text
    assert "<html>" not in caplog.text


def test_send_skips_event_larger_than_one_mib(monkeypatch):
    calls = []
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.setattr("pipeline.metrics_collector_activity.MAX_EVENT_BODY_BYTES", 1)
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(kwargs),
    )

    MetricsCollectorActivity(_ctx(), trace_id="trace-1").send_start()

    assert MAX_EVENT_BODY_BYTES == 1024 * 1024
    assert calls == []


@pytest.mark.parametrize("other_job", [False, True])
def test_stop_retains_delivered_reports_for_downstream_jobs(monkeypatch, tmp_path, other_job):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.setenv("METRICS_COLLECTOR_RESULTS_ROOT", str(tmp_path))
    activity = MetricsCollectorActivity(_ctx(), trace_id="current")
    activity.record_completion("SUCCESS", [])
    directory = activity._completion_directory()
    sibling = MetricsCollectorActivity(_ctx(), trace_id="other")
    if other_job:
        sibling.record_completion("FAILED", [])
    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", lambda *args, **kwargs: _Response())

    activity.send_stop("SUCCESS", use_recorded_completion=True)

    assert len(list(directory.glob("*.json"))) == 1
    assert activity._delivery_receipt().exists()
    if other_job:
        assert len(list(sibling._completion_directory().glob("*.json"))) == 1


@pytest.mark.parametrize("failure", ["transport", "rejected", "oversized", "malformed"])
def test_stop_keeps_reports_when_not_delivered(monkeypatch, tmp_path, failure):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.setenv("METRICS_COLLECTOR_RESULTS_ROOT", str(tmp_path))
    activity = MetricsCollectorActivity(_ctx(), trace_id="current")
    activity.record_completion("FAILED", [])
    report = next(activity._completion_directory().glob("*.json"))
    if failure == "oversized":
        monkeypatch.setattr("pipeline.metrics_collector_activity.MAX_EVENT_BODY_BYTES", 1)
    if failure == "malformed":
        report.write_text("invalid json", encoding="utf-8")

    def post(*args, **kwargs):
        if failure == "transport":
            raise requests.ConnectionError("unavailable")
        return _ErrorResponse() if failure == "rejected" else _Response()

    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", post)
    activity.send_stop("SUCCESS", use_recorded_completion=True)

    assert report.exists()


def test_repeated_stop_retains_reports_without_deleting_files(monkeypatch, tmp_path, caplog):
    from pathlib import Path

    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setenv("CI_JOB_ID", "job-1")
    monkeypatch.setenv("METRICS_COLLECTOR_RESULTS_ROOT", str(tmp_path))
    activity = MetricsCollectorActivity(_ctx(), trace_id="current")
    activity.record_completion("SUCCESS", [])
    calls = []
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(kwargs) or _Response(),
    )

    def unlink(*args, **kwargs):
        raise PermissionError("file locked")

    with monkeypatch.context() as locked:
        locked.setattr(Path, "unlink", unlink)
        activity.send_stop("SUCCESS", use_recorded_completion=True)

    assert "Failed to clean up" not in caplog.text
    activity.send_stop("SUCCESS", use_recorded_completion=True)
    assert len(calls) == 1
    assert activity._completion_directory().exists()
