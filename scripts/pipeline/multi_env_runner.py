import os
import subprocess
import sys
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed

from envgenehelper import logger
from envgenehelper.collections_helper import split_multi_value_param

ORCHESTRATOR_MODULE = "pipeline.orchestrator"


def resolve_env_selection() -> None:
    env_names = os.getenv("ENV_NAMES")
    if env_names:
        for var in ("CLUSTER_NAME", "ENVIRONMENT_NAME", "FULL_ENV_NAME"):
            if os.getenv(var):
                raise ValueError(f"Do not set {var} when ENV_NAMES is set.")
        for full_env_name in split_multi_value_param(env_names):
            if "/" not in full_env_name:
                raise ValueError(
                    f"Invalid environment name '{full_env_name}'. "
                    f"Expected format: <cluster>/<env>"
                )
        return

    cluster_name = os.getenv("CLUSTER_NAME")
    env_name = os.getenv("ENVIRONMENT_NAME")
    if not cluster_name or not env_name:
        raise ValueError("Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME")

    os.environ["ENV_NAMES"] = f"{cluster_name}/{env_name}"


def _child_env_for(full_env_name: str) -> dict[str, str]:
    cluster_name, env_name = full_env_name.split("/", 1)
    child = dict(os.environ)
    child["ENV_NAMES"] = full_env_name
    child["FULL_ENV_NAME"] = full_env_name
    child["CLUSTER_NAME"] = cluster_name
    child["ENVIRONMENT_NAME"] = env_name
    return child


def _run_single_env_pipeline() -> None:
    # Local import keeps the multi-env dispatcher lightweight; the orchestrator is only
    # loaded when running in single-env mode.
    from pipeline.orchestrator import run_unified_pipeline

    run_unified_pipeline()


def _run_child_subprocess(full_env_name: str) -> int:
    logger.info(f"========== START: multi-env child {full_env_name} ==========")
    proc = subprocess.Popen(
        [sys.executable, "-m", ORCHESTRATOR_MODULE],
        env=_child_env_for(full_env_name),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    prefix = f"[{full_env_name}] "
    try:
        for line in proc.stdout:
            sys.stderr.write(f"{prefix}{line}")
            sys.stderr.flush()
    finally:
        returncode = proc.wait()

    if returncode != 0:
        logger.error(
            f"Pipeline failed for {full_env_name} with exit code {returncode}"
        )
    else:
        logger.info(f"========== END: multi-env child {full_env_name} - SUCCESS ==========")
    return returncode


def _fan_out(env_names: Sequence[str], max_workers: int) -> int:
    failed: list[str] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_run_child_subprocess, full_env_name): full_env_name
            for full_env_name in env_names
        }
        for future in as_completed(futures):
            full_env_name = futures[future]
            try:
                returncode = future.result()
            except Exception:
                logger.exception(f"Failed to run pipeline for {full_env_name}")
                returncode = 1
            if returncode != 0:
                failed.append(full_env_name)

    if failed:
        logger.error(f"Multi-env pipeline finished with failures: {', '.join(failed)}")
        return 1

    logger.info("Multi-env pipeline finished successfully for all environments")
    return 0


def dispatch() -> int:
    resolve_env_selection()
    env_names = split_multi_value_param(os.getenv("ENV_NAMES", ""))
    if len(env_names) <= 1:
        _run_single_env_pipeline()
        return 0

    max_workers = min(len(env_names), os.cpu_count() or 1)
    logger.info(
        f"ENV_NAMES contains {len(env_names)} environments; "
        f"running parallel subprocess fan-out (max_workers={max_workers})"
    )
    return _fan_out(env_names, max_workers)


if __name__ == "__main__":
    raise SystemExit(dispatch())
