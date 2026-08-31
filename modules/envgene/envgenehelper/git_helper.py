import os
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

from envgenehelper import logger
from envgenehelper.errors import IntegrationError
from envgenehelper.business_helper import getenv_with_error
from envgenehelper.file_helper import delete_dir_if_exists
from envgenehelper.http_helper import ApiClient
from envgenehelper.retry import GIT_RETRY_POLICY, retry_call, RetryPolicy
from git import GitCommandError, InvalidGitRepositoryError, Repo
from pydantic import BaseModel
from envgenehelper.models import PipelineType
from envgenehelper.repo_paths import get_sparse_checkout_paths


class ConflictError(RuntimeError):
    pass


class GitContext(BaseModel):
    platform: str
    server_protocol: str
    server_host: str
    project_path: str
    ref_name: str
    user_email: str
    user_name: str
    token: str
    commit_sha: str

    def model_post_init(self, __context) -> None:
        logger.info(f"GitContext created: {self.model_dump(exclude={'token'})}")

    @classmethod
    def from_env(cls) -> "GitContext":
        if os.getenv("GITHUB_ACTIONS"):
            data = {
                "platform": "github",
                "server_protocol": "https",
                "server_host": "github.com",
                "project_path": getenv_with_error("GITHUB_REPOSITORY"),
                "ref_name": getenv_with_error("GITHUB_REF_NAME"),
                "user_email": getenv_with_error("GITHUB_USER_EMAIL"),
                "user_name": getenv_with_error("GITHUB_USER_NAME"),
                "token": getenv_with_error("GITHUB_TOKEN", no_log=True),
                "commit_sha": getenv_with_error("GITHUB_SHA")
            }
        elif os.getenv("GITLAB_CI"):
            data = {
                "platform": "gitlab",
                "server_protocol": getenv_with_error("CI_SERVER_PROTOCOL"),
                "server_host": getenv_with_error("CI_SERVER_HOST"),
                "project_path": getenv_with_error("CI_PROJECT_PATH"),
                "ref_name": getenv_with_error("CI_COMMIT_REF_NAME"),
                "user_email": getenv_with_error("GITLAB_USER_EMAIL"),
                "user_name": getenv_with_error("GITLAB_USER_LOGIN"),
                "token": getenv_with_error("GITLAB_TOKEN", no_log=True),
                "commit_sha": getenv_with_error("CI_COMMIT_SHA")
            }
        elif os.getenv("IS_LOCAL_DEV_TEST_ENVGENE") == "true":
            data = {
                "platform": "local",
                "server_protocol": "http",
                "server_host": "localhost",
                "project_path": "local/project",
                "ref_name": "local",
                "user_email": "local@localhost",
                "user_name": "local",
                "token": "local",
                "commit_sha": "local"
            }
        else:
            raise RuntimeError("Neither GITHUB_ACTIONS nor GITLAB_CI detected")

        return cls(**data)


class GitRepoManager:
    def __init__(self, project_dir: Path | str | None = None):
        project_dir = Path(project_dir or os.getenv("CI_PROJECT_DIR", os.getcwd()))
        try:
            self.repo = Repo(project_dir)
        except InvalidGitRepositoryError:
            self.repo = Repo.init(project_dir)
        self.ctx = GitContext.from_env()

    def configure(self) -> None:
        with self.repo.config_writer() as cfg:
            cfg.set_value("user", "email", self.ctx.user_email)
            cfg.set_value("user", "name", self.ctx.user_name)
            cfg.set_value("gc", "auto", "0")

    def _resolve_remote_url(self) -> str:
        if self.ctx.platform == "github":
            return (f"{self.ctx.server_protocol}://{self.ctx.token}@"
                    f"{self.ctx.server_host}/{self.ctx.project_path}.git"
                    )
        else:
            return (
                f"{self.ctx.server_protocol}://{self.ctx.user_name}:{self.ctx.token}@"
                f"{self.ctx.server_host}/{self.ctx.project_path}.git"
            )

    def _fetch(self, ref: str, checkout: str, checkout_option: list[str]) -> None:
        origin = self.repo.remote("origin")
        origin.set_url(self._resolve_remote_url())
        origin.set_url(self._resolve_remote_url(), push=True)

        try:
            logger.info(f"git fetch --depth=1 origin {ref}")
            self.repo.git.fetch("--depth", "1", "origin", ref)
            logger.info(f"git checkout {' '.join(checkout_option)} {checkout}")
            self.repo.git.checkout(*checkout_option, checkout)
        except GitCommandError as exc:
            raise RuntimeError(f"Failed to prepare repository for '{ref}': {exc}") from exc

    def _get_excluded_paths(self) -> list[str]:
        full_env_name = os.getenv("FULL_ENV_NAME")
        if not full_env_name:
            return []

        return [f"environments/{full_env_name}/Inventory/delta-deploy-plan.yml",
                f"environments/{full_env_name}/Inventory/namespace-map.yml"]

    def _get_dcl_paths(self) -> list[str]:
        full_env_name = os.getenv("FULL_ENV_NAME")
        if os.getenv("PIPELINE_TYPE") != PipelineType.GITLAB_DEPLOY or not full_env_name:
            return []

        return [f"environments/{full_env_name}/effective-set/deployment",
                f"environments/{full_env_name}/effective-set/cleanup",
                f"environments/{full_env_name}/effective-set/runtime"]

    @property
    def _repo_root(self) -> Path:
        return Path(self.repo.working_dir)

    def _snapshot_root(self) -> Path:
        return self._repo_root / "tmp" / "git_commit_snapshot"

    def snapshot_excluded_paths(self) -> list[str]:
        # protects excluded paths from being reset by the checkout further down
        snapshot_root = self._snapshot_root()

        snapshot_paths = []
        for rel_path in self._get_excluded_paths() + self._get_dcl_paths():
            src = self._repo_root / rel_path
            if not src.exists():
                continue

            dst = snapshot_root / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            # os.rename within repo_root, not a copy - no extra disk space used
            shutil.move(str(src), str(dst))
            snapshot_paths.append(rel_path)

        return snapshot_paths

    def remove_dcl_paths_from_index(self) -> None:
        dcl_paths = self._get_dcl_paths()
        if not dcl_paths:
            return

        logger.info("Removing DCL contexts from the repository index...")
        self.repo.git.rm("--cached", "-r", "--ignore-unmatch", "--", *dcl_paths)

    def restore_excluded_paths(self, rel_paths: list[str]) -> None:
        snapshot_root = self._snapshot_root()

        logger.info(f"Restoring {len(rel_paths)} excluded path(s) from snapshot...")
        for rel_path in rel_paths:
            src = snapshot_root / rel_path
            dst = self._repo_root / rel_path

            delete_dir_if_exists(dst)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            logger.info(f"Restored {rel_path}")

        delete_dir_if_exists(snapshot_root)

    def stage_changes(self, sparse_paths: Optional[list[str]] = None) -> bool:
        logger.info("Staging changes...")
        if sparse_paths is None:
            sparse_paths = get_sparse_checkout_paths(os.environ["FULL_ENV_NAME"])

        existing_paths = [path for path in sparse_paths if Path(path).exists()]
        exclude_args = [f":(exclude){path}" for path in self._get_excluded_paths()]
        self.repo.git.add("--all", "--", *existing_paths, *exclude_args)

        staged_files = self.repo.git.diff("--cached", "--name-only")
        for file in staged_files.splitlines():
            logger.info(file)

        return self._has_staged_changes()

    def create_detached_commit(self, message: str) -> str:
        # git commit-tree "$(git write-tree)" -p HEAD -m "${message}"
        tree_sha = self.repo.git.write_tree()
        try:
            parent_sha = self.repo.head.commit.hexsha
            commit_args = ["-p", parent_sha, "-m", message]
        except ValueError:
            commit_args = ["-m", message]

        commit_sha = self.repo.git.commit_tree(tree_sha, *commit_args).strip()
        logger.info(f"Created hidden commit {commit_sha} (not attached to any branch)")
        return commit_sha

    def _has_staged_changes(self) -> bool:
        status, _, _ = self.repo.git.diff(
            "--cached", "--quiet", with_exceptions=False, with_extended_output=True
        )
        if status not in (0, 1):
            raise RuntimeError(f"git diff failed with exit code {status}")
        return status == 1

    def _cherry_pick_and_push(self, snapshot_sha: str) -> None:
        if os.getenv("IS_LOCAL_DEV_TEST_ENVGENE") == "true":
            logger.info("Local test mode: skipping cherry-pick and push")
            return

        self._fetch(ref=self.ctx.ref_name, checkout="FETCH_HEAD", checkout_option=["--force", "--detach"])

        try:
            logger.info(f"git cherry-pick --strategy=recursive -X no-renames {snapshot_sha}")
            self.repo.git.cherry_pick("--strategy=recursive", "-X", "no-renames", snapshot_sha)
        except GitCommandError as e:
            status = self.repo.git.status("--porcelain=v1")
            unmerged_codes = {"UU", "AA", "DD", "AU", "UA", "UD", "DU"}
            has_unresolved_conflicts = any(line[:2] in unmerged_codes for line in status.splitlines())

            if not has_unresolved_conflicts and not self._has_staged_changes():
                logger.info(
                    f"Cherry-pick of {snapshot_sha} is empty after conflict resolution "
                    f"(changes already present on {self.ctx.ref_name}); skipping commit, nothing to push."
                )
                self.repo.git.cherry_pick("--skip", with_exceptions=False)
                return

            self.repo.git.cherry_pick("--abort", with_exceptions=False)
            raise RuntimeError(f"Cherry-pick failed on {snapshot_sha}: {e}") from e
        except Exception as e:
            self.repo.git.cherry_pick("--abort", with_exceptions=False)
            raise RuntimeError(f"Cherry-pick failed on {snapshot_sha}: {e}") from e

        try:
            logger.info(f"git push origin HEAD:{self.ctx.ref_name}")
            self.repo.git.push("origin", f"HEAD:{self.ctx.ref_name}")
        except Exception as e:
            raise RuntimeError(f"Push failed after cherry-pick of {snapshot_sha}: {e}") from e

    def retry_cherry_pick_and_push(self, snapshot_sha: str, retry_policy: RetryPolicy = GIT_RETRY_POLICY) -> None:
        attempt = {"count": 0}

        def run():
            attempt["count"] += 1

            if attempt["count"] > 1:
                logger.info(f"Retry {attempt['count'] - 1}/{retry_policy.limit - 1}")

            self._cherry_pick_and_push(snapshot_sha)

        retry_call(retry_policy, run, retry_on=(RuntimeError,))

    def sparse_checkout(self, sparse_paths: list[str]) -> None:
        logger.info("git update-ref HEAD FETCH_HEAD")
        self.repo.git.update_ref("HEAD", "FETCH_HEAD")
        
        logger.info("git sparse-checkout init --cone")
        self.repo.git.sparse_checkout("init", "--cone")
        logger.info(f"git sparse-checkout set ({len(sparse_paths)} paths)")
        self.repo.git.sparse_checkout("set", *sparse_paths)
        logger.info("git read-tree -mu HEAD")
        self.repo.git.read_tree("-mu", "HEAD")
        logger.info("sparse checkout complete")


class GitLabClient:
    def __init__(self, token: str):
        self.token = token
        self.api_url = os.getenv("CI_API_V4_URL").rstrip("/")
        self.http = ApiClient()

    @property
    def headers(self):
        return {"PRIVATE-TOKEN": self.token}

    @staticmethod
    def _project_url_segment(project: str | int) -> str:
        return quote(str(project), safe="")

    def get_pipeline_jobs(self, project, pipeline_id):
        project_segment = self._project_url_segment(project)
        url = f"{self.api_url}/projects/{project_segment}/pipelines/{pipeline_id}/jobs"
        return self.http.get_json(url, headers=self.headers)

    def download_job_artifacts(self, project, job_id, dest_artifacts_path):
        project_segment = self._project_url_segment(project)
        url = f"{self.api_url}/projects/{project_segment}/jobs/{job_id}/artifacts"
        self.http.download_file(url, dest_artifacts_path, headers=self.headers)

    def get_project_variables(self, project):
        project_segment = self._project_url_segment(project)
        url = f"{self.api_url}/projects/{project_segment}/variables"
        return self.http.get_json(url, headers=self.headers)

    def trigger_pipeline(self, project_path: str, ref: str, variables: dict) -> dict:
        project_segment = self._project_url_segment(project_path)
        url = f"{self.api_url}/projects/{project_segment}/pipeline"
        payload = {
            "ref": ref,
            "variables": [{"key": key, "value": value} for key, value in variables.items()],
        }
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                verify=self.http.verify_ssl,
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise IntegrationError(
                f"Pipeline trigger failed for {project_path}@{ref}: {e}"
            )
