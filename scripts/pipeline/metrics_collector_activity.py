from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import requests
from cloudevents.core.bindings.http import to_structured_event
from cloudevents.core.v1.event import CloudEvent

if TYPE_CHECKING:
    from pipeline.orchestrator import StepResult


ACTIVITY_PATH = "/api/v1/activity"
MAX_EVENT_BODY_BYTES = 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 5
PIPELINE_DISPLAY_NAME = "EnvGene Instance Pipeline"
DEFAULT_EVENT_SOURCE = "urn:envgene:instance-pipeline"
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

    def send_running(self, status: str = "IN_PROGRESS", results: list[StepResult] | None = None,
                     *, use_recorded_completion: bool = False) -> None:
        data = None
        if self.enabled and use_recorded_completion:
            try:
                if self._delivery_receipt().exists():
                    return
                reports = [json.loads(path.read_text(encoding="utf-8"))
                           for path in sorted(self._completion_directory().glob("*.json"))]
                if reports:
                    data = self._completion_data(reports)
            except Exception:
                logger.exception("Failed to read Metrics Collector pipeline progress.")
        self._send("running", status, results, data=data)

    def record_completion(self, status: str, results: list[StepResult]) -> None:
        if not self.enabled:
            return
        temporary = None
        try:
            directory = self._completion_directory()
            directory.mkdir(parents=True, exist_ok=True)
            environment = str(self.ctx.params.get("ENV_NAMES", os.getenv("ENV_NAMES", "")))
            identity = json.dumps([os.getenv("CI_JOB_ID", ""), environment])
            name = hashlib.sha256(identity.encode()).hexdigest()[:32]
            path = directory / f"{name}.json"
            temporary = directory / f"{uuid.uuid4().hex}.tmp"
            temporary.write_text(json.dumps({
                "status": status,
                "environment": environment,
                "jobid": os.getenv("CI_JOB_ID", ""),
                "traceid": self.trace_id,
                "parentid": self.parent_id,
                "data": self._event_data(results),
            }), encoding="utf-8")
            temporary.replace(path)
        except Exception:
            logger.exception("Failed to record Metrics Collector pipeline completion.")
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    logger.exception("Failed to remove temporary Metrics Collector completion file.")

    def _completion_directory(self) -> Path:
        # Children write outside their worktrees so after_script can read the results.
        root = completion_root()
        # after_script runs in a fresh shell and may not inherit the generated trace ID.
        job_id = os.getenv("CI_JOB_ID", "").strip()
        identity = json.dumps(["job", job_id] if job_id else ["trace", self.trace_id])
        if os.getenv("CI_PIPELINE_ID", "").strip():
            identity = json.dumps(["pipeline", os.getenv("CI_PROJECT_ID", ""), os.environ["CI_PIPELINE_ID"]])
        key = hashlib.sha256(identity.encode()).hexdigest()[:32]
        return Path(root) / ".metrics-collector-client" / "state" / key

    def _delivery_receipt(self) -> Path:
        directory = self._completion_directory()
        job_key = hashlib.sha256(os.getenv("CI_JOB_ID", "").encode()).hexdigest()[:32]
        return directory.parent.parent / f".metrics-collector-{directory.name}-{job_key}.sent"

    def _completion_data(self, reports: list[dict[str, Any]]) -> dict[str, Any]:
        self.trace_id = reports[0]["traceid"]
        self.parent_id = reports[0]["parentid"]
        data = dict(reports[0]["data"])
        if len(reports) > 1:
            environments = dict.fromkeys(report["environment"] for report in reports)
            data["inputParameters"] = {**data["inputParameters"], "ENV_NAMES": ",".join(environments)}
        data.pop("steps", None)
        job_reports = [report for report in reports if report["jobid"] == os.getenv("CI_JOB_ID", "")]
        if job_reports:
            data["steps"] = [
                dict(step, **({"environment": report["environment"]} if len(job_reports) > 1 else {}))
                for report in job_reports for step in report["data"]["steps"]
            ]
        return data

    def send_stop(self, status: str, *, use_recorded_completion: bool = False,
                  override_status: bool = False) -> None:
        data = None
        report_paths = []
        receipt = None
        if self.enabled and use_recorded_completion:
            try:
                directory = self._completion_directory()
                receipt = self._delivery_receipt()
                report_paths = sorted(directory.glob("*.json"))
                if receipt.exists():
                    return
                reports = [json.loads(path.read_text(encoding="utf-8"))
                           for path in report_paths]
                if reports:
                    statuses = {report["status"] for report in reports}
                    outcomes = statuses | {status}
                    if not override_status:
                        if "FAILED" in outcomes:
                            status = "FAILED"
                        elif "CANCELLED" in outcomes:
                            status = "CANCELLED"
                        elif "UNKNOWN" in statuses:
                            status = "UNKNOWN"
                        else:
                            status = "SKIPPED" if statuses == {"SKIPPED"} else "SUCCESS"
                    data = self._completion_data(reports)
            except Exception:
                data = None
                receipt = None
                report_paths = []
                logger.exception("Failed to read Metrics Collector pipeline completion.")
                if status not in ("FAILED", "CANCELLED"):
                    status = "UNKNOWN"
        if self._send("stop", status, data=data):
            if receipt is not None:
                try:
                    receipt.parent.mkdir(parents=True, exist_ok=True)
                    receipt.touch()
                except OSError:
                    logger.exception("Failed to record Metrics Collector stop delivery.")
                    return

    def _event_data(self, results: list[StepResult] | None = None) -> dict[str, Any]:
        # Sync normally reuses the saved payload; it does not need the EnvGene package.
        try:
            from envgenehelper.version_helper import resolve_envgene_version
        except ModuleNotFoundError:
            version = os.getenv("ENVGENE_VERSION", "UNKNOWN")
        else:
            version = resolve_envgene_version()
        data = {
            "envgeneVersion": version,
            "inputParameters": {key: value for key, value in self.ctx.params.items()
                                if key not in self.ctx.sensitive_params and value not in (None, "")},
        }
        if results is not None:
            data["steps"] = serialize_step_results(results)
        return data

    def _send(self, event_type: str, status: str, results: list[StepResult] | None = None,
              *, data: dict[str, Any] | None = None) -> bool:
        if not self.enabled:
            return False

        try:
            if data is None:
                data = self._event_data(results)
            body, headers = build_structured_event_body(
                event_type=event_type,
                status=status,
                trace_id=self.trace_id,
                parent_id=self.parent_id,
                data=data,
            )
            if len(body.encode("utf-8")) > MAX_EVENT_BODY_BYTES:
                logger.error("Metrics Collector activity event exceeds 1 MiB and will not be sent.")
                return False

            logger.debug("Sending Metrics Collector activity event: %s", body)
            activity_url = urljoin(self.base_url.rstrip("/") + "/", ACTIVITY_PATH.lstrip("/"))
            response = requests.post(
                activity_url,
                data=body,
                headers={**{key: value for key, value in headers.items()
                            if key.lower() not in ("content-type", "accept")},
                         "Content-Type": "application/cloudevents+json", "Accept": "application/json"},
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
                    return False
                logger.error(
                    "Metrics Collector activity event was rejected: "
                    f"status_code={response.status_code}, response={response.text}"
                )
                return False
            return True
        except requests.RequestException as exc:
            logger.error(f"Failed to send Metrics Collector activity event: {exc}")
        except Exception:
            logger.exception("Failed to prepare Metrics Collector activity event.")
        return False


def completion_root() -> Path:
    project = Path(os.getenv("CI_PROJECT_DIR") or os.getcwd()).resolve()
    configured = Path(os.getenv("METRICS_COLLECTOR_RESULTS_ROOT") or project)
    return (project / configured).resolve()


def resolve_trace_id() -> str:
    trace_id = os.getenv("METRICS_COLLECTOR_TRACE_ID", "").strip()
    if trace_id:
        return trace_id
    trace_id = uuid.uuid4().hex
    os.environ["METRICS_COLLECTOR_TRACE_ID"] = trace_id
    return trace_id


def serialize_step_results(results: list[StepResult]) -> list[dict[str, str | int]]:
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

    message = to_structured_event(CloudEvent(attributes=attributes, data=data))
    body = message.body
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    return body, message.headers
