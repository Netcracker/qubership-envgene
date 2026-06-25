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
        logger.info(f"Deployment session id is {session_id}")
        message = f"{message}\n\nDEPLOYMENT-SESSION-ID: {session_id}"
        logger.info("Appended commit message with session id")

    logger.info(f"Commit message: {message}")
    return message


def git_commit() -> None:
    logger.info("===== SCRIPT START =====")
    repo = GitRepoManager()
    repo.configure()

    logger.info("Minimizing credential file diffs...")
    minimize_cred_diffs()
    if not repo.stage_changes():
        logger.info("No changes. Skip.")
        return

    message = build_commit_message()
    sha = repo.create_detached_commit(message)
    repo.sync_and_push(sha)

    logger.info("===== SCRIPT END =====")


if __name__ == '__main__':
    git_commit()
