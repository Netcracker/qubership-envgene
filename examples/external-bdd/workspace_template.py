"""
Example of integrating qubership-envgene BDD tests into an external project.

Copy these files into your project (e.g., tests/e2e/framework/).
"""

from pathlib import Path
import subprocess

from tests.framework.base_workspace import BaseWorkspace
from tests.framework.base_data_builders import BaseDataBuilder


class ExternalDataBuilder(BaseDataBuilder):
    """
    DataBuilder implementation for an external project.
    Defines where physical files (inventory, environments) are created.
    """
    def get_env_dir(self, cluster_name: str, env_name: str) -> Path:
        d = self.workspace.base_dir / "integration-workspaces" / cluster_name / env_name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def create_inventory_file(self, cluster_name: str, env_name: str, content: dict):
        import yaml
        inv_dir = self.get_env_dir(cluster_name, env_name) / "Inventory"
        inv_dir.mkdir(parents=True, exist_ok=True)
        with open(inv_dir / "env_definition.yml", "w") as f:
            yaml.dump(content, f)


class ExternalWorkspace(BaseWorkspace):
    """
    Workspace implementation for an external project.
    Provides paths and executes your pipeline logic.
    """
    def __init__(self, tmp_path):
        self._base_dir = tmp_path
        self._sboms_dir = self._base_dir / "sboms"
        self._sboms_dir.mkdir(parents=True, exist_ok=True)

        self._config_data = {}
        self._stdout = ""
        self._stderr = ""
        self._returncode = 0
        
        self._builder = ExternalDataBuilder(self)

    @property
    def base_dir(self) -> Path: return self._base_dir
    
    @property
    def sboms_dir(self) -> Path: return self._sboms_dir

    @property
    def config_data(self) -> dict: return self._config_data

    @config_data.setter
    def config_data(self, value: dict): self._config_data = value

    @property
    def stdout(self) -> str: return self._stdout

    @stdout.setter
    def stdout(self, value: str): self._stdout = value

    @property
    def stderr(self) -> str: return self._stderr

    @stderr.setter
    def stderr(self, value: str): self._stderr = value

    @property
    def returncode(self) -> int: return self._returncode

    @returncode.setter
    def returncode(self, value: int): self._returncode = value

    @property
    def builder(self) -> BaseDataBuilder: return self._builder

    def run_pipeline(self, extra_env: dict = None):
        """Executes the pipeline for the current test scenario."""
        import os
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
            
        config_path = self._base_dir / "config.yml"
        import yaml
        with open(config_path, "w") as f:
            yaml.dump(self._config_data, f)
            
        env["CONFIG_PATH"] = str(config_path)

        # Example of how to call your actual pipeline entrypoint:
        # result = subprocess.run(["python", "-m", "external_project.pipeline_entrypoint"], env=env, capture_output=True, text=True)
        
        self.stdout = "Pipeline executed successfully"
        self.stderr = ""
        self.returncode = 0
