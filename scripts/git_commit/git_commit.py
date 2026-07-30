import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

from envgenehelper import logger
from envgenehelper.git_helper import GitRepoManager

from git_commit.minimize_cred_diffs import minimize_cred_diffs


@contextmanager
def _git_commit_lock(repo_manager: GitRepoManager):
    lock_path = Path(repo_manager.repo.common_dir) / "envgene-git-commit.lock"
    with lock_path.open("w", encoding="utf-8") as lock_file:
        logger.info(f"Acquiring git_commit lock: {lock_path}")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            logger.info(f"Released git_commit lock: {lock_path}")


def build_commit_message() -> str:
    ticket_id = os.getenv("DEPLOYMENT_TICKET_ID", "")
    commit_message = os.getenv("COMMIT_MESSAGE", "")
    cluster = os.getenv("CLUSTER_NAME", "")
    env_name = os.getenv("ENVIRONMENT_NAME", "")
    session_id = os.getenv("DEPLOYMENT_SESSION_ID", "")

    if commit_message:
        message = f"{ticket_id} {commit_message}".strip()
    else:
        message = f'{ticket_id} [ci_skip] Update "{cluster}/{env_name}" environment'.strip()

    if session_id:
        message = f"{message}\n\nDEPLOYMENT-SESSION-ID: {session_id}"
        logger.info(f"Appended deployment session id {session_id} to commit message")

    logger.info(f"Commit message: {message}")
    return message


def git_commit() -> None:
    repo_manager = GitRepoManager()
    with _git_commit_lock(repo_manager):
        repo_manager.configure()

        logger.info("Minimizing credential file diffs...")
        minimize_cred_diffs()
        if not repo_manager.stage_changes():
            logger.info("No changes. Skip.")
            return
        message = build_commit_message()
        sha = repo_manager.create_detached_commit(message)

        snapshot_paths = repo_manager.snapshot_excluded_paths()
        try:
            repo_manager.retry_cherry_pick_and_push(sha)
        finally:
            repo_manager.restore_excluded_paths(snapshot_paths)


if __name__ == '__main__':
    git_commit()
