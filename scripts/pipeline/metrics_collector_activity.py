import json
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import requests

try:
    from cloudevents.core.bindings.http import to_structured_event
    from cloudevents.core.v1.event import CloudEvent
except ImportError:
    CloudEvent = None
    to_structured_event = None


ACTIVITY_PATH = "/api/v1/activity"
MAX_EVENT_BODY_BYTES = 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 5
PIPELINE_DISPLAY_NAME = "EnvGene Instance Pipeline"
DEFAULT_EVENT_SOURCE = "urn:envgene:instance-pipeline"
UNKNOWN_VERSION = "UNKNOWN"
logger = logging.getLogger(__name__)


class MetricsCollectorActivity:
    def __init__(self, ctx, trace_id: str | None = None, parent_id: str | None = None):
        self.ctx = ctx
        self.base_url = os.getenv("METRICS_COLLECTOR_URL", "").strip()
        self.verify_ssl = os.getenv("METRICS_COLLECTOR_SSL_VERIFY", "true").strip().lower() != "false"
        self.trace_id = trace_id or (resolve_trace_id() if self.base_url else "")
        self.parent_id = parent_id if parent_id is not None else os.getenv("METRICS_COLLECTOR_PARENT_ID", "")

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def send_start(self) -> None:
        self._send("start", "IN_PROGRESS")

    def send_stop(self, status: str, results: list[Any]) -> None:
        self._send("stop", status, results)

    def _send(self, event_type: str, status: str, results: list[Any] | None = None) -> None:
        if not self.enabled:
            return

        data = {
            "envgeneVersion": resolve_envgene_version(),
            "inputParameters": selected_input_parameters(self.ctx),
        }
        if results is not None:
            data["steps"] = serialize_step_results(results)

        try:
            body, headers = build_structured_event_body(
                event_type=event_type,
                status=status,
                trace_id=self.trace_id,
                parent_id=self.parent_id,
                data=data,
            )
            if len(body.encode("utf-8")) > MAX_EVENT_BODY_BYTES:
                logger.error("Metrics Collector activity event exceeds 1 MiB and will not be sent.")
                return

            logger.debug("Sending Metrics Collector activity event: %s", body)
            activity_url = urljoin(self.base_url.rstrip("/") + "/", ACTIVITY_PATH.lstrip("/"))
            response = requests.post(
                activity_url,
                data=body,
                headers=with_activity_headers(headers),
                timeout=REQUEST_TIMEOUT_SECONDS,
                verify=self.verify_ssl,
            )
            if not response.ok:
                if response.status_code == 404:
                    logger.error(
                        "Metrics Collector activity endpoint not found (HTTP 404): %s. "
                        "Check METRICS_COLLECTOR_URL: it must point to the collector base URL; "
                        "EnvGene appends /api/v1/activity. Also check the collector route configuration. "
                        "The activity event was not sent; pipeline execution will continue.",
                        activity_url,
                    )
                    return
                logger.error(
                    "Metrics Collector activity event was rejected: "
                    f"status_code={response.status_code}, response={response.text}"
                )
                return
        except requests.RequestException as exc:
            logger.error(f"Failed to send Metrics Collector activity event: {exc}")
        except Exception:
            logger.exception("Failed to prepare Metrics Collector activity event.")


def resolve_trace_id() -> str:
    trace_id = os.getenv("METRICS_COLLECTOR_TRACE_ID", "").strip()
    if trace_id:
        return trace_id
    trace_id = uuid.uuid4().hex
    os.environ["METRICS_COLLECTOR_TRACE_ID"] = trace_id
    return trace_id


def selected_input_parameters(ctx) -> dict[str, Any]:
    params = {}
    sensitive = set(getattr(ctx, "sensitive_params", []))
    for key, value in ctx.params.items():
        if key in sensitive or value in (None, ""):
            continue
        params[key] = value
    return params


def serialize_step_results(results: list[Any]) -> list[dict[str, Any]]:
    serialized = []
    for result in results:
        item = {
            "name": result.name,
            "status": str(result.status),
        }
        if result.duration_ms is not None:
            item["durationMs"] = result.duration_ms
        serialized.append(item)
    return serialized


def build_structured_event_body(
        event_type: str,
        status: str,
        trace_id: str,
        parent_id: str,
        data: dict[str, Any],
) -> tuple[str, dict[str, str]]:
    attributes = {
        "id": str(uuid.uuid4()),
        "source": os.getenv("CI_PROJECT_URL", "").strip() or DEFAULT_EVENT_SOURCE,
        "type": event_type,
        "time": datetime.now(UTC).replace(microsecond=0),
        "kind": "pipeline",
        "kindversion": "1.0",
        "traceid": trace_id,
        "parentid": parent_id,
        "technicalname": os.getenv("CI_JOB_NAME", "instance_pipeline"),
        "displayname": PIPELINE_DISPLAY_NAME,
        "jobid": os.getenv("CI_JOB_ID", ""),
        "pipelineid": os.getenv("CI_PIPELINE_ID", ""),
        "projectid": os.getenv("CI_PROJECT_ID", ""),
        "status": status,
    }

    if CloudEvent is not None and to_structured_event is not None:
        message = to_structured_event(CloudEvent(attributes=attributes, data=data))
        body = message.body
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        return body, message.headers

    return json.dumps({**base_event_attributes(attributes), "data": data}), {
        "Content-Type": "application/cloudevents+json"
    }


def with_activity_headers(headers: dict[str, str]) -> dict[str, str]:
    normalized = dict(headers)
    normalized.pop("content-type", None)
    normalized["Content-Type"] = "application/cloudevents+json"
    normalized["Accept"] = "application/json"
    return normalized


def base_event_attributes(attributes: dict[str, Any]) -> dict[str, Any]:
    event_attributes = {
        "specversion": "1.0",
        "id": attributes.pop("id"),
        "source": attributes.pop("source"),
        "type": attributes.pop("type"),
        "time": format_event_time(attributes.pop("time")),
    }
    event_attributes.update(attributes)
    return event_attributes


def format_event_time(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    return str(value)


def resolve_envgene_version() -> str:
    image = os.getenv("envgen_image", "").strip()
    if image:
        image_name, digest_separator, digest = image.partition("@")
        _, tag_separator, tag = image_name.rsplit("/", 1)[-1].partition(":")
        if tag_separator and tag:
            return tag
        if digest_separator and digest:
            return digest
        return "latest"

    for key in ("ENVGENE_VERSION", "CI_COMMIT_TAG", "CI_COMMIT_SHORT_SHA", "CI_COMMIT_SHA"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return UNKNOWN_VERSION
