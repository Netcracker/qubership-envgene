from pathlib import Path
from git import Repo, GitCommandError
from python.envgene.envgenehelper.http_helper import ApiClient, download_file


class GitRepoManager:
    def __init__(self, repo_path, git_user_email, git_user_name, git_token, server_host, project_path, branch):
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
            import shutil
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
    def __init__(self, token: str, api_url: str):
        self.token = token
        self.api_url = api_url.rstrip("/")
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
