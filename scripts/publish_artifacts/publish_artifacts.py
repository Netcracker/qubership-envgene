import os
import shutil
from pathlib import Path

from envgenehelper import get_save_artifacts_strategy, logger
from envgenehelper.models import SaveArtifactsStrategy
from envgenehelper.file_helper import writeToFile

from publish_artifacts.scope import copy_scope

NOT_PUBLISHED_FILE_NAME = "NOT-PUBLISHED.txt"
LIMIT_MULTIPLIER = 3


def artifacts_output_root(work_dir: Path) -> Path:
    return Path(os.getenv("ARTIFACTS_OUTPUT_DIR", str(work_dir / "artifacts")))


def copy_env_artifact(ctx) -> None:
    if get_save_artifacts_strategy() == SaveArtifactsStrategy.NEVER:
        return
    output_root = artifacts_output_root(ctx.work_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    copy_scope(ctx.work_dir, output_root / ctx.cluster_name / ctx.env_name)


def finalize_artifacts(output_root: Path, limit_mb: int) -> None:
    if get_save_artifacts_strategy() == SaveArtifactsStrategy.NEVER:
        logger.info(f"save_artifacts_strategy is NEVER")
        writeToFile(output_root / NOT_PUBLISHED_FILE_NAME, "save_artifacts_strategy is NEVER\n")
        return
    logger.info(f"save_artifacts_strategy is ALWAYS (default), checking size limit for {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    effective_limit_mb = limit_mb * LIMIT_MULTIPLIER
    limit_bytes = effective_limit_mb * 1024 * 1024
    size = sum(f.stat().st_size for f in output_root.rglob("*") if f.is_file())

    if size > limit_bytes:
        logger.warning(f"Artifact is over the {effective_limit_mb}MB limit - republishing with logs only")
        for child in output_root.iterdir():
            if child.name != "logs":
                shutil.rmtree(child) if child.is_dir() else child.unlink()
        writeToFile(output_root / NOT_PUBLISHED_FILE_NAME, f"combined artifact exceeded {effective_limit_mb}MB\n")
