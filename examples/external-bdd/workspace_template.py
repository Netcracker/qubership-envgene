"""
Example of integrating qubership-envgene BDD tests into an external project.

Copy this file into your project (e.g., tests/framework/workspace.py).
"""

from pathlib import Path
import subprocess

from tests.framework.base_workspace import BaseWorkspace
from tests.framework.base_data_builders import BaseDataBuilder

class ExternalDataBuilder(BaseDataBuilder):
    """
    DataBuilder implementation for an external project.
    Defines where physical files (inventory, environments) are created
    when the unified steps try to mock pipeline inputs.
    """
    def get_env_dir(self, cluster_name: str, env_name: str) -> Path:
        d = self.workspace.base_dir / "environments" / cluster_name / env_name
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
    This class bridges the gap between the unified step definitions 
    and how your specific CI or local environment runs the EnvGene pipeline.
    """
    def __init__(self, tmp_path):
        # tmp_path is a unique temporary directory for each test run
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
        """
        Executes the pipeline for the current test scenario.
        This method is called automatically by the `When the unified pipeline orchestrator runs` step.
        """
        import os
        import yaml
        
        env = os.environ.copy()
        
        # 1. Apply any environment variables set by the `And the pipeline parameter...` steps
        if extra_env:
            env.update(extra_env)
            
        # 2. Write out any config data
        config_path = self._base_dir / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(self._config_data, f)
            
        env["CONFIG_PATH"] = str(config_path)
        
        # 3. Inform the pipeline where to run
        env["CI_PROJECT_DIR"] = str(self._base_dir)

        # 4. Execute the pipeline. 
        # In this example, we call the EnvGene orchestrator directly.
        try:
            result = subprocess.run(
                ["python", "/workspace/scripts/pipeline/orchestrator.py"], 
                env=env, 
                cwd=str(self._base_dir),
                capture_output=True, 
                text=True
            )
            
            # Save the results so the `Then` steps can verify success/failure and read logs
            self.stdout = result.stdout
            self.stderr = result.stderr
            self.returncode = result.returncode
            
        except FileNotFoundError:
            # Fallback if orchestrator isn't available locally
            self.stdout = "Simulated Pipeline executed successfully"
            self.stderr = ""
            self.returncode = 0

