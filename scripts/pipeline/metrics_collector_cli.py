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

    ctx = _pipeline_context()
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


def _pipeline_context():
    # In env-prepare, use EnvGene's canonical parameter parser so the report
    # contains the same complete, secret-filtered config as the orchestrator.
    if os.getenv("ENV_NAMES", "").strip():
        try:
            from envgene_shared.utils.collections_utils import split_multi_value_param
            from pipeline.pipeline_parameters import PipelineParametersHandler

            original_names = os.environ["ENV_NAMES"]
            names = split_multi_value_param(original_names)
            os.environ["ENV_NAMES"] = names[0]
            handler = PipelineParametersHandler.from_env()
            handler.params["ENV_NAMES"] = ",".join(names)
            return SimpleNamespace(params=handler.params, sensitive_params=handler.sensitive_params)
        except ModuleNotFoundError:
            pass
        except Exception:
            logging.getLogger(__name__).exception("Could not load EnvGene pipeline parameters for metrics.")
        finally:
            if "original_names" in locals():
                os.environ["ENV_NAMES"] = original_names

    # Portable sync hooks do not include the EnvGene package. They consume
    # the config saved by env-prepare; retain a minimal fallback for early errors.
    names = ["PIPELINE_TYPE", "ENV_NAMES"]
    params = {key: os.getenv(key, "") for key in names}
    return SimpleNamespace(params=params, sensitive_params=[])


if __name__ == "__main__":
    raise SystemExit(main())
