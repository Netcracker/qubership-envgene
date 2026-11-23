"""Metrics commands for Instance pipeline before_script, script, and after_script hooks."""

import argparse
import logging
import os
import shutil
import stat
from pathlib import Path
from types import SimpleNamespace

logger = logging.getLogger(__name__)
METRICS_COLLECTOR_DEPS_DIR = Path("/module/metrics-collector-deps")
_JOB_STATUS = {
    "success": "SUCCESS",
    "failed": "FAILED",
    "canceled": "CANCELLED",
    "skipped": "SKIPPED",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "event",
        choices=("trace-id", "start", "running", "stop", "stop-prepare", "start-sync", "stop-sync"),
    )
    parser.add_argument("--status", choices=("IN_PROGRESS", "SUCCESS", "FAILED", "CANCELLED", "SKIPPED", "UNKNOWN"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=os.getenv("ENVGENE_LOG_LEVEL", "INFO").upper())
    if args.event == "stop-prepare":
        stop_prepare()
        return 0
    if args.event == "start-sync":
        start_sync()
        return 0
    if args.event == "stop-sync":
        stop_sync()
        return 0
    if not os.getenv("METRICS_COLLECTOR_URL", "").strip():
        return 0
    if args.event == "trace-id":
        # Export this value in the first job and pass it to later hooks/jobs via dotenv.
        print(_resolve_trace_id())
        return 0

    ctx = _pipeline_context()
    activity = _activity(ctx)
    if args.event == "start":
        activity.send_start()
    elif args.event == "running":
        activity.send_running(args.status or "IN_PROGRESS", use_recorded_completion=True)
    else:
        status = args.status or _JOB_STATUS.get(os.getenv("CI_JOB_STATUS", ""), "UNKNOWN")
        if status == "IN_PROGRESS":
            parser.error("stop requires a terminal status")
        activity.send_stop(status, use_recorded_completion=True, override_status=args.status is not None)
    return 0


def start_metrics_collector() -> None:
    if not os.getenv("METRICS_COLLECTOR_URL", "").strip():
        return
    project_dir = os.getenv("CI_PROJECT_DIR", "").strip()
    client_root = None
    if project_dir:
        root = Path(project_dir)
        os.environ["METRICS_COLLECTOR_RESULTS_ROOT"] = str(root / "tmp")
        client_root = root / "tmp" / ".metrics-collector-client"
        try:
            pipeline_dir = client_root / "pipeline"
            pipeline_dir.mkdir(parents=True, exist_ok=True)
            source_dir = Path(__file__).resolve().parent
            for name in ("__init__.py", "metrics_collector_activity.py", "metrics_collector_cli.py"):
                source = source_dir / name
                if source.is_file():
                    shutil.copy2(source, pipeline_dir / name)
            if METRICS_COLLECTOR_DEPS_DIR.is_dir():
                shutil.copytree(
                    METRICS_COLLECTOR_DEPS_DIR,
                    client_root / METRICS_COLLECTOR_DEPS_DIR.name,
                    dirs_exist_ok=True,
                )
        except OSError:
            logger.exception("Failed to stage Metrics Collector client.")
    try:
        trace_id = _resolve_trace_id()
    except Exception:
        logger.exception("Failed to resolve Metrics Collector trace ID.")
        return
    if client_root is not None:
        try:
            (client_root.parent / ".metrics-collector-trace-id").write_text(trace_id, encoding="utf-8")
        except OSError:
            logger.exception("Failed to save Metrics Collector trace ID.")
    try:
        _activity(_pipeline_context()).send_start()
    except Exception:
        logger.exception("Failed to start Metrics Collector activity.")


def stop_prepare() -> None:
    _set_results_root()
    try:
        if os.getenv("METRICS_COLLECTOR_URL", "").strip():
            if _load_trace_id():
                status = _terminal_status()
                activity = _activity(_pipeline_context())
                activity.send_running(status, use_recorded_completion=True)
                if not _sync_expected() or status != "SUCCESS":
                    activity.send_stop(status, use_recorded_completion=True, override_status=False)
            else:
                print("Metrics Collector events skipped: trace ID artifact is missing.")
    except Exception:
        logger.exception("Failed to report Metrics Collector prepare result.")
    _chmod_client()


def start_sync() -> None:
    _set_results_root()
    if not os.getenv("METRICS_COLLECTOR_URL", "").strip():
        return
    try:
        if not _load_trace_id():
            print("Metrics Collector event skipped: trace ID artifact is missing.")
            return
        _activity(_pipeline_context()).send_running("IN_PROGRESS", use_recorded_completion=True)
    except Exception:
        logger.exception("Failed to report Metrics Collector sync start.")


def stop_sync() -> None:
    _set_results_root()
    try:
        if os.getenv("METRICS_COLLECTOR_URL", "").strip():
            if _load_trace_id():
                _activity(_pipeline_context()).send_stop(
                    _terminal_status(), use_recorded_completion=True, override_status=False,
                )
            else:
                print("Metrics Collector event skipped: trace ID artifact is missing.")
    except Exception:
        logger.exception("Failed to report Metrics Collector sync stop.")
    if os.getenv("CI_JOB_STATUS") == "success":
        _cleanup()
    else:
        print(f"Keeping metrics collector files for diagnostics: J2 status is {os.getenv('CI_JOB_STATUS') or 'unknown'}.")


def _activity(ctx):
    from pipeline.metrics_collector_activity import MetricsCollectorActivity

    return MetricsCollectorActivity(ctx)


def _resolve_trace_id() -> str:
    from pipeline.metrics_collector_activity import resolve_trace_id

    return resolve_trace_id()


def _set_results_root() -> None:
    project_dir = os.getenv("CI_PROJECT_DIR", "").strip()
    if project_dir:
        os.environ["METRICS_COLLECTOR_RESULTS_ROOT"] = str(Path(project_dir) / "tmp")


def _trace_file() -> Path | None:
    project_dir = os.getenv("CI_PROJECT_DIR", "").strip()
    if not project_dir:
        return None
    return Path(project_dir) / "tmp" / ".metrics-collector-trace-id"


def _load_trace_id() -> bool:
    path = _trace_file()
    if path is None or not path.is_file() or path.stat().st_size == 0:
        return False
    os.environ["METRICS_COLLECTOR_TRACE_ID"] = path.read_text(encoding="utf-8").rstrip("\n")
    return True


def _terminal_status() -> str:
    return _JOB_STATUS.get(os.getenv("CI_JOB_STATUS", ""), "UNKNOWN")


def _sync_expected() -> bool:
    if os.getenv("PIPELINE_TYPE") != "GITLAB_DEPLOY":
        return False
    operation = os.getenv("OPERATION_TYPE")
    if operation == "DEPLOY":
        return True
    return operation == "BGD" and os.getenv("BGD_OPERATION") == "warmup"


def _chmod_client() -> None:
    project_dir = os.getenv("CI_PROJECT_DIR", "").strip()
    if not project_dir:
        return
    client = Path(project_dir) / "tmp" / ".metrics-collector-client"
    if not client.is_dir():
        return
    try:
        tmp = client.parent
        os.chmod(tmp, tmp.stat().st_mode | stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        for path in (client, *client.rglob("*")):
            mode = path.stat().st_mode
            extra = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH
            if path.is_dir() or mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                extra |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            os.chmod(path, mode | extra)
    except OSError:
        logger.exception("Failed to widen Metrics Collector client permissions.")


def _cleanup() -> None:
    project_dir = os.getenv("CI_PROJECT_DIR", "").strip()
    if not project_dir or project_dir == "/":
        return
    root = Path(project_dir) / "tmp"
    shutil.rmtree(root / ".metrics-collector-client", ignore_errors=True)
    try:
        (root / ".metrics-collector-trace-id").unlink(missing_ok=True)
    except OSError:
        logger.exception("Failed to remove Metrics Collector trace ID.")


def _pipeline_context():
    # Collect params only so the report contains the same complete, secret-filtered config as the orchestrator.
    if os.getenv("ENV_NAMES", "").strip():
        try:
            from pipeline.pipeline_parameters import PipelineParametersHandler
        except ModuleNotFoundError:
            pass
        else:
            # Secrets are filtered by MetricsCollectorActivity (SENSITIVE_CONFIG_KEYS).
            return SimpleNamespace(params=PipelineParametersHandler.build_params(), sensitive_params=[])

    # Portable sync hooks do not include the EnvGene package. They consume
    # the config saved by env-prepare; retain a minimal fallback for early errors.
    names = ["PIPELINE_TYPE", "ENV_NAMES"]
    params = {key: os.getenv(key, "") for key in names}
    return SimpleNamespace(params=params, sensitive_params=[])


if __name__ == "__main__":
    raise SystemExit(main())
