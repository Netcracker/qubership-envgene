"""Metrics commands for Instance pipeline before_script, script, and after_script hooks."""

import argparse
import logging
import os
from types import SimpleNamespace

from pipeline.metrics_collector_activity import MetricsCollectorActivity, resolve_trace_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event", choices=("trace-id", "start", "running", "stop"))
    parser.add_argument("--status", choices=("IN_PROGRESS", "SUCCESS", "FAILED", "CANCELLED", "SKIPPED", "UNKNOWN"))
    args = parser.parse_args(argv)
    logging.basicConfig(level=os.getenv("ENVGENE_LOG_LEVEL", "INFO").upper())
    if not os.getenv("METRICS_COLLECTOR_URL", "").strip():
        return 0
    if args.event == "trace-id":
        # Export this value in the first job and pass it to later hooks/jobs via dotenv.
        print(resolve_trace_id())
        return 0

    # Hooks must work before environment preparation, including jobs without ENV_NAMES.
    ctx = SimpleNamespace(
        params={key: os.getenv(key, "") for key in ("PIPELINE_TYPE", "ENV_NAMES")},
        sensitive_params=[],
    )
    activity = MetricsCollectorActivity(ctx)
    if args.event == "start":
        activity.send_start()
    elif args.event == "running":
        activity.send_running(args.status or "IN_PROGRESS", use_recorded_completion=True)
    else:
        status = args.status or {
            "success": "SUCCESS",
            "failed": "FAILED",
            "canceled": "CANCELLED",
            "skipped": "SKIPPED",
        }.get(os.getenv("CI_JOB_STATUS", ""), "UNKNOWN")
        if status == "IN_PROGRESS":
            parser.error("stop requires a terminal status")
        activity.send_stop(status, use_recorded_completion=True, override_status=args.status is not None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
