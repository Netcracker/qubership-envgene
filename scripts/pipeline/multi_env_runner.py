import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from envgenehelper import logger
from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.repo_paths import REPO_ROOT_PATHS, get_env_artifact_paths

ORCHESTRATOR_MODULE = "pipeline.orchestrator"


def _worktree_path(base_dir: Path, full_env_name: str) -> Path:
    cluster_name, env_name = full_env_name.split("/", 1)
    return base_dir / "tmp" / "worktrees" / cluster_name / env_name


def _resolve_commit_sha() -> str:
    return os.getenv("CI_COMMIT_SHA", "HEAD")


def _create_worktree(base_repo: Path, worktree_path: Path, commit_sha: str) -> None:
    if worktree_path.exists():
        _remove_worktree(base_repo, worktree_path)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Creating worktree for {worktree_path.name} at {worktree_path}")
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree_path), commit_sha],
        cwd=base_repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _remove_worktree(base_repo: Path, worktree_path: Path) -> None:
    if not worktree_path.exists():
        return
    logger.info(f"Removing worktree at {worktree_path}")
    try:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=base_repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError:
        shutil.rmtree(worktree_path, ignore_errors=True)
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=base_repo,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )


def _copy_worktree_outputs(worktree_path: Path, main_path: Path, full_env_name: str) -> None:
    cluster_name, env_name = full_env_name.split("/", 1)
    sparse_paths = list(REPO_ROOT_PATHS)
    sparse_paths.extend(get_env_artifact_paths(cluster_name, env_name))
    for rel_path in sparse_paths:
        src = worktree_path / rel_path
        if not src.exists():
            continue
        dst = main_path / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)


def resolve_env_selection() -> None:
    env_names = os.getenv("ENV_NAMES")
    if env_names:
        for var in ("CLUSTER_NAME", "ENVIRONMENT_NAME", "FULL_ENV_NAME"):
            os.environ.pop(var, None)
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


def _child_env_for(full_env_name: str, worktree_path: Path) -> dict[str, str]:
    cluster_name, env_name = full_env_name.split("/", 1)
    child = dict(os.environ)
    child["ENV_NAMES"] = full_env_name
    child["FULL_ENV_NAME"] = full_env_name
    child["CLUSTER_NAME"] = cluster_name
    child["ENVIRONMENT_NAME"] = env_name
    child["CI_PROJECT_DIR"] = str(worktree_path)
    child["ENVGENE_WORKTREE"] = "1"
    return child


def _run_single_env_pipeline() -> None:
    # Local import keeps the multi-env dispatcher lightweight; the orchestrator is only
    # loaded when running in single-env mode.
    from pipeline.orchestrator import run_unified_pipeline

    run_unified_pipeline()


def _run_child_subprocess(
    full_env_name: str, worktree_path: Path, logs_dir: Path
) -> int:
    log_file_name = full_env_name.replace("/", "_") + ".log"
    log_path = logs_dir / log_file_name
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        f"========== START: multi-env child {full_env_name} (log: {log_path}) =========="
    )
    proc = subprocess.Popen(
        [sys.executable, "-m", ORCHESTRATOR_MODULE],
        env=_child_env_for(full_env_name, worktree_path),
        cwd=worktree_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    prefix = f"[{full_env_name}] "
    with log_path.open("w", encoding="utf-8") as log_file:
        for line in proc.stdout:
            log_file.write(line)
            log_file.flush()
            sys.stderr.write(f"{prefix}{line}")
            sys.stderr.flush()
    returncode = proc.wait()

    if returncode != 0:
        logger.error(
            f"Pipeline failed for {full_env_name} with exit code {returncode}"
        )
    else:
        logger.info(
            f"========== END: multi-env child {full_env_name} - SUCCESS =========="
        )
    return returncode


def _fan_out(env_names: Sequence[str], max_workers: int) -> int:
    base_repo = Path(os.getenv("CI_PROJECT_DIR", os.getcwd()))
    main_path = base_repo
    commit_sha = _resolve_commit_sha()
    failed: list[str] = []
    worktrees: list[Path] = []
    env_to_worktree: dict[str, Path] = {}

    logs_dir = main_path / "tmp" / "logs"
    shutil.rmtree(logs_dir, ignore_errors=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    for full_env_name in env_names:
        worktree_path = _worktree_path(base_repo, full_env_name)
        worktrees.append(worktree_path)
        env_to_worktree[full_env_name] = worktree_path
        _create_worktree(base_repo, worktree_path, commit_sha)

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    _run_child_subprocess,
                    full_env_name,
                    worktree_path,
                    logs_dir,
                ): full_env_name
                for full_env_name, worktree_path in env_to_worktree.items()
            }
            for future in as_completed(futures):
                full_env_name = futures[future]
                worktree_path = env_to_worktree[full_env_name]
                try:
                    returncode = future.result()
                except Exception:
                    logger.exception(f"Failed to run pipeline for {full_env_name}")
                    returncode = 1
                if returncode == 0:
                    _copy_worktree_outputs(worktree_path, main_path, full_env_name)
                else:
                    failed.append(full_env_name)
    finally:
        for worktree_path in worktrees:
            _remove_worktree(base_repo, worktree_path)

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
