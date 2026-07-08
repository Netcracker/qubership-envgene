import os

from envgenehelper import logger
from envgenehelper.git_helper import GitRepoManager

from minimize_cred_diffs import minimize_cred_diffs


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
    repo_manager.configure()

    logger.info("Minimizing credential file diffs...")
    minimize_cred_diffs()
    if not repo_manager.stage_changes():
        logger.info("No changes. Skip.")
        return
    message = build_commit_message()
    sha = repo_manager.create_detached_commit(message)
    repo_manager.retry_cherry_pick_and_push(sha)


if __name__ == '__main__':
    git_commit()
