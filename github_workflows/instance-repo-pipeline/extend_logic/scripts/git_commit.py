#!/usr/bin/env python3
"""
git_commit.py - Commit and push changes from pipeline (GitLab CI).

Requires: GITLAB_TOKEN, CI_PROJECT_DIR
Optional: GITLAB_CI_USER (default: oauth2), CI_SERVER_HOST, CI_PROJECT_PATH, CI_COMMIT_REF_NAME
         PIPELINE_OUTPUT_DIR (default: extended_github_instance_pipeline) - output folder name for commit message
"""

import os
import subprocess
import sys


def run(cmd, check=True, env=None):
    """Run command (list of args), return completed process."""
    env = env or os.environ.copy()
    result = subprocess.run(cmd, env=env)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def main():
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        print("Error: GITLAB_TOKEN is not set", file=sys.stderr)
        sys.exit(1)

    project_dir = os.environ.get("CI_PROJECT_DIR")
    if not project_dir:
        print("Error: CI_PROJECT_DIR is not set", file=sys.stderr)
        sys.exit(1)

    os.chdir(project_dir)

    ci_user = os.environ.get("GITLAB_CI_USER", "oauth2")
    server_host = os.environ.get("CI_SERVER_HOST", "gitlab.com")
    project_path = os.environ.get("CI_PROJECT_PATH")
    ref_name = os.environ.get("CI_COMMIT_REF_NAME", "main")

    # CI_PROJECT_PATH not set (e.g. running locally) — derive from git remote
    if not project_path:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            # Parse https://host/ns/proj.git or git@host:ns/proj.git
            if "://" in url:
                path = url.split("://", 1)[1].split("/", 1)[-1]
            elif ":" in url:
                path = url.split(":", 1)[1]
            else:
                path = ""
            path = path.rstrip("/").removesuffix(".git").strip("/")
            if path and path != ".git":
                project_path = path
        if not project_path:
            print(
                "Error: CI_PROJECT_PATH not set and could not derive from git remote.\n"
                "  Set CI_PROJECT_PATH (e.g. 'group/project') or fix origin:\n"
                "  git remote set-url origin https://gitlab.com/OWNER/REPO.git",
                file=sys.stderr,
            )
            sys.exit(1)

    print(f"Push: token OK, user={ci_user}, pwd={os.getcwd()}", flush=True)

    env = os.environ.copy()
    env["HOME"] = "/tmp"

    run(["git", "config", "--global", "--add", "safe.directory", project_dir], env=env)
    run(["git", "config", "user.email", "ci@gitlab"], env=env)
    run(["git", "config", "user.name", "GitLab CI"], env=env)

    origin_url = f"https://{ci_user}:{token}@{server_host}/{project_path}.git"
    run(["git", "remote", "set-url", "origin", origin_url], env=env)

    run(["git", "add", "."], env=env)

    result = subprocess.run(
        ["git", "diff", "--staged", "--quiet"],
        env=env,
        capture_output=True,
    )

    if result.returncode != 0:
        output_dir = os.environ.get("PIPELINE_OUTPUT_DIR", "extended_github_instance_pipeline")
        run(["git", "commit", "-m", f"chore: update {output_dir} from pipeline [ci skip]"], env=env)
        result = subprocess.run(
            ["git", "push", "origin", f"HEAD:{ref_name}"],
            env=env,
        )
        if result.returncode != 0:
            print(
                "Error: git push failed - check token scope (write_repository)",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        print("No changes to commit")


if __name__ == "__main__":
    main()
