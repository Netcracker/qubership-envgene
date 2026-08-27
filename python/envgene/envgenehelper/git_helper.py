import os
from pathlib import Path

from envgenehelper import logger
from envgenehelper.http_helper import ApiClient
from envgenehelper.retry import GIT_RETRY_POLICY, retry_call, RetryPolicy
from git import GitCommandError, Repo
from pydantic import BaseModel


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
                "project_path": os.getenv("GITHUB_REPOSITORY"),
                "ref_name": os.getenv("GITHUB_REF_NAME"),
                "user_email": os.getenv("GITHUB_USER_EMAIL"),
                "user_name": os.getenv("GITHUB_USER_NAME"),
                "token": os.getenv("GITHUB_TOKEN"),
                "commit_sha": os.getenv("GITHUB_SHA")
            }
        elif os.getenv("GITLAB_CI"):
            data = {
                "platform": "gitlab",
                "server_protocol": os.getenv("CI_SERVER_PROTOCOL"),
                "server_host": os.getenv("CI_SERVER_HOST"),
                "project_path": os.getenv("CI_PROJECT_PATH"),
                "ref_name": os.getenv("CI_COMMIT_REF_NAME"),
                "user_email": os.getenv("GITLAB_USER_EMAIL"),
                "user_name": os.getenv("GITLAB_USER_LOGIN"),
                "token": os.getenv("GITLAB_TOKEN"),
                "commit_sha": os.getenv("CI_COMMIT_SHA")
            }
        else:
            raise RuntimeError("Neither GITHUB_ACTIONS nor GITLAB_CI detected")

        return cls(**data)


class GitRepoManager:
    def __init__(self):
        self.repo = Repo.init(Path(os.getenv("CI_PROJECT_DIR", os.getcwd())))
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

    def _fetch(self, ref: str, checkout: str, checkout_option: list[str], create_remote: bool = False) -> None:
        if create_remote:
            self.repo.create_remote("origin", self._resolve_remote_url())
        else:
            self.repo.remote("origin").set_url(self._resolve_remote_url(), push=True)

        try:
            logger.info(f"git fetch --depth=1 origin {ref}")
            self.repo.git.fetch("--depth", "1", "origin", ref)
            logger.info(f"git checkout {' '.join(checkout_option)} {checkout}")
            self.repo.git.checkout(*checkout_option, checkout)
        except GitCommandError as exc:
            raise RuntimeError(f"Failed to prepare repository for '{ref}': {exc}") from exc

    def stage_changes(self) -> bool:
        logger.info("Staging changes...")

        self.repo.git.add("--all", "--")

        staged_files = self.repo.git.diff("--cached", "--name-only")
        for file in staged_files.splitlines():
            logger.info(file)

        status, _, _ = self.repo.git.diff("--cached", "--quiet", with_exceptions=False, with_extended_output=True)
        if status == 0:
            return False

        if status == 1:
            return True

        raise RuntimeError(f"git diff failed with exit code {status}")

    def create_detached_commit(self, message: str) -> str:
        # git commit-tree "$(git write-tree)" -p HEAD -m "${message}"
        tree_sha = self.repo.git.write_tree()
        parent_sha = self.repo.head.commit.hexsha
        commit_sha = self.repo.git.commit_tree(tree_sha, p=parent_sha, m=message).strip()
        logger.info(f"Created hidden commit {commit_sha} (not attached to any branch)")
        return commit_sha

    def _cherry_pick_and_push(self, snapshot_sha: str) -> None:
        self._fetch(ref=self.ctx.ref_name, checkout="FETCH_HEAD", checkout_option=["--force", "--detach"])
        try:
            logger.info(f"git cherry-pick --strategy=recursive -X no-renames {snapshot_sha}")
            self.repo.git.cherry_pick("--strategy=recursive", "-X", "no-renames", snapshot_sha)
            logger.info(f"git push origin HEAD:{self.ctx.ref_name}")
            self.repo.git.push("origin", f"HEAD:{self.ctx.ref_name}")
        except Exception as e:
            self.repo.git.cherry_pick("--abort", with_exceptions=False)
            raise RuntimeError(f"Cherry-pick or push failed on {snapshot_sha}: {e}") from e

    def retry_cherry_pick_and_push(self, snapshot_sha: str, retry_policy: RetryPolicy = GIT_RETRY_POLICY) -> None:
        attempt = {"count": 0}

        def run():
            attempt["count"] += 1

            if attempt["count"] > 1:
                logger.info(f"Retry {attempt['count'] - 1}/{retry_policy.limit - 1}")

            self._cherry_pick_and_push(snapshot_sha)

        retry_call(retry_policy, run, retry_on=(RuntimeError,))


class GitLabClient:
    def __init__(self, token: str):
        self.token = token
        self.api_url = os.getenv("CI_API_V4_URL").rstrip("/")
        self.http = ApiClient()

    @property
    def headers(self):
        return {"PRIVATE-TOKEN": self.token}

    def get_pipeline_bridges(self, project_id, pipeline_id):
        url = f"{self.api_url}/projects/{project_id}/pipelines/{pipeline_id}/bridges"
        return self.http.get_json(url, headers=self.headers)

    def get_pipeline_jobs(self, project_id, pipeline_id):
        url = f"{self.api_url}/projects/{project_id}/pipelines/{pipeline_id}/jobs"
        return self.http.get_json(url, headers=self.headers)

    def download_job_artifacts(self, project_id, job_id, dest_artifacts_path):
        url = f"{self.api_url}/projects/{project_id}/jobs/{job_id}/artifacts"
        self.http.download_file(url, dest_artifacts_path, headers=self.headers)

    def get_project_variables(self, project_id):
        url = f"{self.api_url}/projects/{project_id}/variables"
        return self.http.get_json(url, headers=self.headers)
