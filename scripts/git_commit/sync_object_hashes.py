from pathlib import Path

from envgene_shared.utils.logger import logger
from envgenehelper import getenv_with_error
from envgenehelper.git_helper import GitRepoManager
from envgenehelper.object_hash_manifest import MANIFEST_DIR, MANIFEST_NAME, sync_manifest_with_disk

COMMIT_MESSAGE = "[ci_skip] Sync object hash manifests with the repository"


def sync_all_manifests(work_dir: Path) -> list[str]:
    changed = []
    for manifest in sorted((work_dir / "environments").glob(f"*/*/{MANIFEST_DIR}/{MANIFEST_NAME}")):
        if sync_manifest_with_disk(manifest.parent.parent, base_dir=work_dir):
            changed.append(manifest.relative_to(work_dir).as_posix())
    return changed


def sync_object_hashes() -> None:
    changed = sync_all_manifests(Path(getenv_with_error("CI_PROJECT_DIR")))
    if not changed:
        logger.info("Object hash manifests already match the repository, nothing to commit")
        return

    logger.info(f"Object hash manifests updated: {changed}")
    repo_manager = GitRepoManager()
    repo_manager.configure()
    if not repo_manager.stage_changes(changed):
        return
    repo_manager.retry_cherry_pick_and_push(repo_manager.create_detached_commit(COMMIT_MESSAGE))


if __name__ == '__main__':
    sync_object_hashes()
