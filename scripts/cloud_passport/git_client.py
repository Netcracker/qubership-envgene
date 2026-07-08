import os
import shutil
from pathlib import Path

from git import GitCommandError, Repo

from envgenehelper.http_helper import ApiClient


class GitRepoManager:
    def __init__(
            self,
            repo_path,
            git_token,
            git_user_email=None,
            git_user_name=None,
            server_host=None,
            project_path=None,
            branch=None,
    ):
        git_user_email = git_user_email or os.getenv("GITLAB_USER_EMAIL")
        git_user_name = git_user_name or os.getenv("GITLAB_USER_LOGIN")
        server_host = server_host or os.getenv("CI_SERVER_HOST")
        project_path = project_path or os.getenv("CI_PROJECT_PATH")
        branch = branch or os.getenv("CI_COMMIT_REF_NAME")

        self.repo_path = Path(repo_path)
        self.git_user_email = git_user_email
        self.git_user_name = git_user_name
        self.git_token = git_token
        self.server_host = server_host
        self.project_path = project_path
        self.branch = branch

        self.repo = Repo(self.repo_path)

    def prepare_repo(self):
        with self.repo.config_writer() as cw:
            cw.set_value("user", "email", self.git_user_email)
            cw.set_value("user", "name", self.git_user_name)
            cw.set_value("pull", "rebase", "true")
            cw.release()

        rebase_dir = self.repo_path / ".git/rebase-merge"
        if rebase_dir.exists():
            shutil.rmtree(rebase_dir)

        push_url = f"https://project_32647_bot:{self.git_token}@{self.server_host}/{self.project_path}.git"
        origin = self.repo.remote(name='origin')
        origin.set_url(push_url, push=True)

        self.repo.git.reset('--hard')

        try:
            origin.pull(self.branch)
        except GitCommandError as e:
            raise RuntimeError(f"Failed to pull branch '{self.branch}' from remote 'origin': {e}")


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
