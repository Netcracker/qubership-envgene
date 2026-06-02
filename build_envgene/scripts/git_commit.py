#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path

from envgenehelper import logger
from retry import GIT_RETRY_POLICY, retry_call


SHARED_DIRS = ("parameters", "credentials", "resource_profiles", "shared_template_variables")


def run(cmd, cwd=None, check=True, capture_output=False, text=True):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=capture_output,
        text=text,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}")
    return result


def bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() == "true"


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def detect_platform() -> dict:
    if os.getenv("GITHUB_ACTIONS"):
        return {
            "platform": "github",
            "server_protocol": "https",
            "server_host": "github.com",
            "project_path": os.getenv("GITHUB_REPOSITORY", ""),
            "ref_name": os.getenv("GITHUB_REF_NAME", ""),
            "user_email": os.getenv("GITHUB_USER_EMAIL", ""),
            "user_name": os.getenv("GITHUB_USER_NAME", ""),
            "token": os.getenv("GITHUB_TOKEN", ""),
        }
    if os.getenv("GITLAB_CI"):
        return {
            "platform": "gitlab",
            "server_protocol": os.getenv("CI_SERVER_PROTOCOL", ""),
            "server_host": os.getenv("CI_SERVER_HOST", ""),
            "project_path": os.getenv("CI_PROJECT_PATH", ""),
            "ref_name": os.getenv("CI_COMMIT_REF_NAME", ""),
            "user_email": os.getenv("GITLAB_USER_EMAIL", ""),
            "user_name": os.getenv("GITLAB_USER_LOGIN", ""),
            "token": os.getenv("GITLAB_TOKEN", ""),
        }
    raise RuntimeError("Neither GITHUB_ACTIONS nor GITLAB_CI detected")


def build_remote_url(platform_data: dict) -> str:
    if platform_data["platform"] == "github":
        return (
            f'{platform_data["server_protocol"]}://{platform_data["token"]}@'
            f'{platform_data["server_host"]}/{platform_data["project_path"]}.git'
        )
    return (
        f'{platform_data["server_protocol"]}://{platform_data["user_name"]}:{platform_data["token"]}@'
        f'{platform_data["server_host"]}/{platform_data["project_path"]}.git'
    )


def mask_remote_url(remote_url: str) -> str:
    if "://" not in remote_url or "@" not in remote_url:
        return remote_url
    scheme, rest = remote_url.split("://", 1)
    credentials, host_path = rest.split("@", 1)
    user = credentials.split(":", 1)[0]
    return f"{scheme}://{user}:***@{host_path}"


def log_execution_context(platform_data: dict) -> None:
    fields = {
        "Platform": platform_data.get("platform"),
        "Server Protocol": platform_data.get("server_protocol"),
        "Server Host": platform_data.get("server_host"),
        "Project Path": platform_data.get("project_path"),
        "Branch/Ref Name": platform_data.get("ref_name"),
        "User Email": platform_data.get("user_email"),
        "User Name": platform_data.get("user_name"),
        "ENV_NAME": os.getenv("ENV_NAME", ""),
        "CLUSTER_NAME": os.getenv("CLUSTER_NAME", ""),
        "ENVIRONMENT_NAME": os.getenv("ENVIRONMENT_NAME", ""),
        "DEPLOYMENT_TICKET_ID": os.getenv("DEPLOYMENT_TICKET_ID", ""),
        "COMMIT_ENV": os.getenv("COMMIT_ENV", ""),
        "COMMIT_MESSAGE": os.getenv("COMMIT_MESSAGE", ""),
        "DEPLOYMENT_SESSION_ID": os.getenv("DEPLOYMENT_SESSION_ID", ""),
    }

    logger.info("===== CONTEXT =====")

    for key, value in fields.items():
        logger.info(f"{key}: {value}")


def resolve_branch_head(repo_dir: Path, ref_name: str) -> str:
    result = run(
        ["git", "ls-remote", "origin", f"refs/heads/{ref_name}"],
        cwd=repo_dir,
        capture_output=True,
    )
    output = (result.stdout or "").strip()
    if not output:
        raise RuntimeError(f"Could not resolve remote branch head for {ref_name}")
    return output.split()[0]


def fetch_and_checkout_detached(repo_dir: Path, ref_name: str, commit_hash: str) -> None:
    run(["git", "fetch", "--depth", "1", "origin", commit_hash], cwd=repo_dir)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=repo_dir)
    run(["git", "update-ref", f"refs/remotes/origin/{ref_name}", "FETCH_HEAD"], cwd=repo_dir)


def init_detached_repo(repo_dir: Path, platform_data: dict) -> None:
    logger.info("Initing new repository")
    run(["git", "init"], cwd=repo_dir)
    run(["git", "config", "--global", "--add", "safe.directory", str(repo_dir)], cwd=repo_dir)
    run(["git", "config", "--global", "user.email", platform_data["user_email"]], cwd=repo_dir)
    run(["git", "config", "--global", "user.name", platform_data["user_name"]], cwd=repo_dir)
    run(["git", "config", "pull.rebase", "true"], cwd=repo_dir)

    remote_url = build_remote_url(platform_data)
    logger.info(f"Adding remote: {mask_remote_url(remote_url)}")
    run(["git", "remote", "add", "origin", remote_url], cwd=repo_dir)

    ref_name = platform_data["ref_name"]
    commit_hash = resolve_branch_head(repo_dir, ref_name)
    logger.info(f"Fetching contents from GIT (branch: {ref_name}, commit: {commit_hash})")
    fetch_and_checkout_detached(repo_dir, ref_name, commit_hash)


def clean_repo_dir(repo_dir: Path) -> None:
    logger.info("Clearing contents of repository")
    if not repo_dir.exists():
        raise RuntimeError(f"Repo dir does not exist: {repo_dir}")
    if repo_dir == Path("/"):
        raise RuntimeError("Refusing to clean root directory")
    for item in repo_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def backup_artifacts(repo_dir: Path, cluster: str, env_name: str, commit_env: bool) -> dict:
    logger.info(f"Moving env environments/{cluster}/{env_name} artifacts to temporary location")
    backup_root = Path("/tmp/envgene_git_commit")
    safe_rmtree(backup_root)
    backup_root.mkdir(parents=True, exist_ok=True)

    artifact_env_cluster = backup_root / "artifact_environments" / cluster
    artifact_shared = backup_root / "artifact_shared"
    updated_creds_root = backup_root / "updated_creds"

    env_path = repo_dir / "environments" / cluster / env_name
    if commit_env and env_path.exists():
        copy_tree(env_path, artifact_env_cluster / env_name)

    cloud_passport = repo_dir / "environments" / cluster / "cloud-passport"
    if cloud_passport.exists():
        copy_tree(cloud_passport, artifact_env_cluster / "cloud-passport")

    configuration = repo_dir / "configuration"
    if configuration.exists():
        logger.info("Copy config folder")
        copy_tree(configuration, backup_root / "configuration")

    sboms = repo_dir / "sboms"
    if sboms.exists():
        logger.info("Copy sboms folder")
        copy_tree(sboms, backup_root / "sboms")

    gitlab_ci_prefix = repo_dir / "gitlab-ci" / "prefix_build"
    if gitlab_ci_prefix.exists():
        logger.info("Copy gitlab-ci")
        copy_tree(repo_dir / "gitlab-ci", backup_root / "gitlab-ci")
        logger.info("Copy templates")
        if (repo_dir / "templates").exists():
            copy_tree(repo_dir / "templates", backup_root / "templates")

    logger.info("Saving cluster and site shared folders")
    cluster_root = repo_dir / "environments" / cluster
    if cluster_root.exists():
        for shared_dir in SHARED_DIRS:
            src = cluster_root / shared_dir
            if src.exists():
                logger.info(f"Saving {src}")
                copy_tree(src, artifact_shared / "environments" / cluster / shared_dir)

    global_env_root = repo_dir / "environments"
    if global_env_root.exists():
        for shared_dir in SHARED_DIRS:
            src = global_env_root / shared_dir
            if src.exists():
                logger.info(f"Saving {src}")
                copy_tree(src, artifact_shared / "environments" / shared_dir)

    creds_file = repo_dir / "environments" / "credfilestoupdate.yml"
    if creds_file.exists():
        logger.info(f"Processing {creds_file} for copying filtered creds...")
        for line in creds_file.read_text(encoding="utf-8").splitlines():
            file_path = line.strip()
            if not file_path or file_path.startswith("#"):
                continue
            logger.info(f"Credential update for {file_path}")
            if f"{cluster}/{env_name}/" in file_path:
                continue
            src = repo_dir / file_path
            if src.exists() and src.is_file():
                logger.info(f"Copying {file_path} to {updated_creds_root}/")
                copy_file(src, updated_creds_root / file_path)
            else:
                logger.warning(f"Source file does not exist: {file_path}")

    return {"root": backup_root}


def restore_shared_dirs(repo_dir: Path, backup_root: Path, cluster: str) -> None:
    logger.info("Restoring cluster and site shared folders")
    artifact_shared = backup_root / "artifact_shared"
    for shared_dir in SHARED_DIRS:
        src = artifact_shared / "environments" / shared_dir
        dst = repo_dir / "environments" / shared_dir
        if src.exists():
            safe_rmtree(dst)
            copy_tree(src, dst)

    for shared_dir in SHARED_DIRS:
        src = artifact_shared / "environments" / cluster / shared_dir
        dst = repo_dir / "environments" / cluster / shared_dir
        if src.exists():
            safe_rmtree(dst)
            copy_tree(src, dst)


def restore_artifacts(repo_dir: Path, backup_root: Path, cluster: str, env_name: str, commit_env: bool) -> bool:
    restore_gitlab_ci_message = False
    artifact_env_cluster = backup_root / "artifact_environments" / cluster

    restore_shared_dirs(repo_dir, backup_root, cluster)

    logger.info(f"Restoring environments/{cluster}/{env_name}")
    env_backup = artifact_env_cluster / env_name
    env_target = repo_dir / "environments" / cluster / env_name
    if commit_env:
        if env_backup.exists():
            safe_rmtree(env_target)
            copy_tree(env_backup, env_target)
        elif env_target.exists():
            logger.info(f"Folder environments/{cluster}/{env_name} no longer exists, deleting from repo")
            safe_rmtree(env_target)

    cloud_passport_backup = artifact_env_cluster / "cloud-passport"
    cloud_passport_target = repo_dir / "environments" / cluster / "cloud-passport"
    if cloud_passport_backup.exists():
        safe_rmtree(cloud_passport_target)
        copy_tree(cloud_passport_backup, cloud_passport_target)

    configuration_backup = backup_root / "configuration"
    if configuration_backup.exists():
        logger.info("Restoring config folder")
        safe_rmtree(repo_dir / "configuration")
        copy_tree(configuration_backup, repo_dir / "configuration")

    sboms_backup = backup_root / "sboms"
    if sboms_backup.exists():
        logger.info("Restoring sboms folder")
        safe_rmtree(repo_dir / "sboms")
        copy_tree(sboms_backup, repo_dir / "sboms")

    gitlab_ci_backup = backup_root / "gitlab-ci"
    if gitlab_ci_backup.exists():
        logger.info("Restoring gitlab-ci folder")
        safe_rmtree(repo_dir / "gitlab-ci")
        copy_tree(gitlab_ci_backup, repo_dir / "gitlab-ci")
        restore_gitlab_ci_message = True

        templates_backup = backup_root / "templates"
        if templates_backup.exists():
            logger.info("Restoring templates folder")
            safe_rmtree(repo_dir / "templates")
            copy_tree(templates_backup, repo_dir / "templates")

    updated_creds = backup_root / "updated_creds"
    if updated_creds.exists():
        for src in updated_creds.rglob("*"):
            if src.is_file():
                rel = src.relative_to(updated_creds)
                dst = repo_dir / rel
                if dst.exists():
                    logger.info(f"Copying file from {src} to {dst}")
                    copy_file(src, dst)
                else:
                    logger.warning(f"Skipping: {rel} does not exist in repo after pull")

    return restore_gitlab_ci_message


def build_commit_message(used_gitlab_ci_update: bool) -> str:
    ticket_id = os.getenv("DEPLOYMENT_TICKET_ID", "")
    commit_message = os.getenv("COMMIT_MESSAGE", "")
    cluster = os.getenv("CLUSTER_NAME", "")
    env_name = os.getenv("ENVIRONMENT_NAME", "")
    session_id = os.getenv("DEPLOYMENT_SESSION_ID", "")

    if used_gitlab_ci_update:
        message = f"{ticket_id} [ci_build_parameters] Update gitlab-ci configurations".strip()
    elif commit_message:
        message = f"{ticket_id} {commit_message}".strip()
    else:
        message = f'{ticket_id} [ci_skip] Update "{cluster}/{env_name}" environment'.strip()

    if session_id:
        logger.info(f"Deployment session id is {session_id}")
        message = f"{message}\n\nDEPLOYMENT-SESSION-ID: {session_id}"
        logger.info("Appended commit message with session id")

    logger.info(f"Commit message: {message}")
    return message


def stage_changes(repo_dir: Path) -> bool:
    """Mirror bash: git add ./* then git commit -a staging via git add -u."""
    logger.info("Checking changes...")
    run(["bash", "-c", "git add ./* 2>/dev/null || true"], cwd=repo_dir, check=False)
    run(["git", "add", "-u"], cwd=repo_dir)
    staged = run(["git", "diff", "--cached", "--name-only"], cwd=repo_dir, capture_output=True, check=False)
    for line in (staged.stdout or "").splitlines():
        if line.strip():
            logger.info(line.strip())
    diff = run(["git", "diff", "--cached", "--quiet"], cwd=repo_dir, check=False)
    return diff.returncode != 0


def create_patch(repo_dir: Path, patch_path: Path) -> None:
    result = run(["git", "diff", "--binary", "--cached"], cwd=repo_dir, capture_output=True)
    patch_path.write_text(result.stdout or "", encoding="utf-8")


def prepare_attempt_state(repo_dir: Path, ref_name: str) -> None:
    commit_hash = resolve_branch_head(repo_dir, ref_name)
    logger.info(f"Fetching latest changes from origin/{ref_name} ({commit_hash})...")
    fetch_and_checkout_detached(repo_dir, ref_name, commit_hash)


def log_push_context(repo_dir: Path, ref_name: str) -> None:
    head = run(["git", "rev-parse", "HEAD"], cwd=repo_dir, capture_output=True, check=False)
    remote = run(["git", "rev-parse", f"origin/{ref_name}"], cwd=repo_dir, capture_output=True, check=False)
    logger.info(f"Current commit: {(head.stdout or '').strip() or 'unknown'}")
    if remote.returncode == 0:
        logger.info(f"Remote commit: {(remote.stdout or '').strip()}")
    else:
        logger.info("Remote commit: unknown")


def push_attempt(repo_dir: Path, ref_name: str, message: str, patch_path: Path) -> None:
    prepare_attempt_state(repo_dir, ref_name)
    try:
        run(["git", "apply", "--3way", "--index", str(patch_path)], cwd=repo_dir)
        run(["git", "commit", "-m", message], cwd=repo_dir)
        logger.info(f"Pushing to origin HEAD:{ref_name}")
        log_push_context(repo_dir, ref_name)
        pushed = run(["git", "push", "origin", f"HEAD:{ref_name}"], cwd=repo_dir, check=False)
        if pushed.returncode != 0:
            raise RuntimeError(f"git push failed with exit code {pushed.returncode}")
        logger.info("Push succeeded")
    finally:
        run(["git", "reset", "--hard"], cwd=repo_dir, check=False)


def try_push_with_retry(repo_dir: Path, ref_name: str, message: str, patch_path: Path) -> int:
    attempt = {"count": 0}

    def push_with_logging() -> None:
        attempt["count"] += 1
        if attempt["count"] > 1:
            logger.info(f"Attempting push (retry {attempt['count'] - 1})...")
        try:
            push_attempt(repo_dir, ref_name, message, patch_path)
        except RuntimeError as exc:
            if attempt["count"] < GIT_RETRY_POLICY.limit:
                logger.warning(f"Push failed, retry attempt: {attempt['count']} of {GIT_RETRY_POLICY.limit}")
                logger.warning(str(exc))
            raise

    try:
        retry_call(
            GIT_RETRY_POLICY,
            push_with_logging,
            retry_on=(RuntimeError,),
        )
        if attempt["count"] > 1:
            logger.info(f"Push succeeded on retry attempt {attempt['count'] - 1}")
        return 0
    except RuntimeError as exc:
        logger.error(f"Failed to push after {GIT_RETRY_POLICY.limit} attempts")
        logger.error(str(exc))
        return 1


def main() -> int:
    logger.info("===== SCRIPT START =====")
    exit_code = 0

    try:
        platform_data = detect_platform()
        if not platform_data["token"]:
            logger.error("No auth token was found. Please check!")
            exit_code = 1
        elif not platform_data["ref_name"]:
            logger.error("Branch/ref name is not set")
            exit_code = 1
        else:
            log_execution_context(platform_data)

            repo_dir = Path(os.getenv("CI_PROJECT_DIR", os.getcwd())).resolve()
            cluster = os.getenv("CLUSTER_NAME", "")
            env_name = os.getenv("ENVIRONMENT_NAME", "")
            commit_env = bool_env("COMMIT_ENV", default=False)

            backup = backup_artifacts(repo_dir, cluster, env_name, commit_env)
            clean_repo_dir(repo_dir)
            init_detached_repo(repo_dir, platform_data)

            used_gitlab_ci_update = restore_artifacts(repo_dir, backup["root"], cluster, env_name, commit_env)
            message = build_commit_message(used_gitlab_ci_update)

            if not stage_changes(repo_dir):
                logger.info("No changes to commit. Skipping...")
            else:
                logger.info("Changes detected. Committing...")
                patch_path = backup["root"] / "changes.patch"
                create_patch(repo_dir, patch_path)
                exit_code = try_push_with_retry(repo_dir, platform_data["ref_name"], message, patch_path)
                if exit_code != 0:
                    logger.error(f"Failed to push changes after {GIT_RETRY_POLICY.limit} attempts")
    except RuntimeError as exc:
        logger.error(str(exc))
        exit_code = 1
    finally:
        logger.info("===== SCRIPT END =====")
        if exit_code != 0:
            logger.error(f"Final exit code: {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
