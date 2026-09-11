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
    resolve_envgene_version,
    resolve_trace_id,
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
    monkeypatch.setenv("CI_PIPELINE_ID", "987654")
    monkeypatch.setenv("CI_PROJECT_ID", "12345")

    body, headers = build_structured_event_body(
        event_type="start",
        status="IN_PROGRESS",
        trace_id="trace-1",
        parent_id="parent-1",
        data={"envgeneVersion": "1.2.3", "inputParameters": {"PIPELINE_TYPE": "GITLAB_DEPLOY"}},
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
    assert event["technicalname"] == "instance_pipeline"
    assert event["jobid"] == "5550001"
    assert event["pipelineid"] == "987654"
    assert event["projectid"] == "12345"
    assert event["status"] == "IN_PROGRESS"
    assert event["data"]["envgeneVersion"] == "1.2.3"


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
    monkeypatch.setenv("ENVGENE_VERSION", "1.2.3")
    monkeypatch.setenv("envgen_image", "registry.example.com:17008/env-generator:2.3.4")
    monkeypatch.setenv("METRICS_COLLECTOR_PARENT_ID", "parent-1")
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append({"args": args, **kwargs}) or _Response(),
    )

    activity = MetricsCollectorActivity(_ctx(CUSTOM_PARAMS="x"), trace_id="trace-1")
    activity.send_start()
    activity.send_stop("SUCCESS", [SimpleNamespace(name="env_build", status="SUCCESS", duration_ms=120)])

    assert [json.loads(call["data"])["type"] for call in calls] == ["start", "stop"]
    assert all(call["verify"] is expected_verify for call in calls)
    assert calls[0]["args"][0] == "https://collector.example.com/base/api/v1/activity"
    assert calls[0]["headers"]["Content-Type"] == "application/cloudevents+json"
    assert calls[0]["headers"]["Accept"] == "application/json"
    assert "content-type" not in calls[0]["headers"]

    start = json.loads(calls[0]["data"])
    assert start["status"] == "IN_PROGRESS"
    assert start["traceid"] == "trace-1"
    assert start["parentid"] == "parent-1"
    assert start["data"]["envgeneVersion"] == "2.3.4"
    assert start["data"]["inputParameters"]["PIPELINE_TYPE"] == "GITLAB_DEPLOY"
    assert start["data"]["inputParameters"]["CUSTOM_PARAMS"] == "x"
    assert "CRED_ROTATION_PAYLOAD" not in start["data"]["inputParameters"]
    assert "steps" not in start["data"]

    stop = json.loads(calls[1]["data"])
    assert stop["status"] == "SUCCESS"
    assert stop["data"]["envgeneVersion"] == "2.3.4"
    assert stop["data"]["steps"] == [{"name": "env_build", "status": "SUCCESS", "durationMs": 120}]


@pytest.mark.parametrize(
    ("image", "expected"),
    [
        ("registry.example.com:17008/env-generator:feature_pdpldevops-25730_poc_latest_build_envgene",
         "feature_pdpldevops-25730_poc_latest_build_envgene"),
        (" env-generator:1.2.3 ", "1.2.3"),
        ("registry.example.com:17008/env-generator", "latest"),
        ("env-generator@sha256:abc123", "sha256:abc123"),
        ("env-generator:1.2.3@sha256:abc123", "1.2.3"),
        (None, "fallback-version"),
        (" ", "fallback-version"),
    ],
)
def test_resolve_envgene_version_from_image(monkeypatch, image, expected):
    monkeypatch.setenv("ENVGENE_VERSION", "fallback-version")
    if image is None:
        monkeypatch.delenv("envgen_image", raising=False)
    else:
        monkeypatch.setenv("envgen_image", image)

    assert resolve_envgene_version() == expected


def test_send_logs_request_body_before_post(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG, logger="pipeline.metrics_collector_activity")
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
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

    def raise_error(*args, **kwargs):
        raise requests.ConnectionError("collector unavailable")

    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", raise_error)

    MetricsCollectorActivity(_ctx(), trace_id="trace-1").send_start()


def test_send_logs_api_error_response(monkeypatch, caplog):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setattr("pipeline.metrics_collector_activity.requests.post", lambda *args, **kwargs: _ErrorResponse())

    MetricsCollectorActivity(_ctx(), trace_id="trace-1").send_start()

    assert "status_code=400" in caplog.text
    assert "type must be start, stop, or start_and_stop" in caplog.text


@pytest.mark.parametrize("base_path", ["", "/base", "/base/"])
def test_send_logs_actionable_message_for_missing_endpoint(monkeypatch, caplog, base_path):
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com" + base_path)
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


def test_build_structured_event_body_falls_back_without_sdk_event(monkeypatch):
    monkeypatch.setattr("pipeline.metrics_collector_activity.CloudEvent", None)
    monkeypatch.setattr("pipeline.metrics_collector_activity.to_structured_event", None)

    body, headers = build_structured_event_body(
        event_type="stop",
        status="SUCCESS",
        trace_id="trace-1",
        parent_id="",
        data={"envgeneVersion": "1.2.3", "inputParameters": {}, "steps": []},
    )

    event = json.loads(body)
    assert headers["Content-Type"] == "application/cloudevents+json"
    assert event["specversion"] == "1.0"
    assert event["type"] == "stop"
    assert event["status"] == "SUCCESS"
    assert event["data"]["steps"] == []


def test_send_skips_event_larger_than_one_mib(monkeypatch):
    calls = []
    monkeypatch.setenv("METRICS_COLLECTOR_URL", "https://collector.example.com")
    monkeypatch.setattr("pipeline.metrics_collector_activity.MAX_EVENT_BODY_BYTES", 1)
    monkeypatch.setattr(
        "pipeline.metrics_collector_activity.requests.post",
        lambda *args, **kwargs: calls.append(kwargs),
    )

    MetricsCollectorActivity(_ctx(), trace_id="trace-1").send_start()

    assert MAX_EVENT_BODY_BYTES == 1024 * 1024
    assert calls == []
