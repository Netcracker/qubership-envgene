import os
import subprocess
import yaml
from pathlib import Path
from .data_builders import DataBuilder
from .base_workspace import BaseWorkspace

class EnvGeneWorkspace(BaseWorkspace):
    def __init__(self, tmp_path):
        self._base_dir = tmp_path
        self.config_dir = self._base_dir / "configuration"
        self.config_file = self.config_dir / "config.yml"
        self._config_data = {}

        self._sboms_dir = self._base_dir / "sboms"
        self.inventory_dir = self._base_dir / "inventory"
        self.regdefs_dir = self._base_dir / "regdefs"
        self.blueprints_dir = self._base_dir / "blueprints"
        self.environments_dir = self._base_dir / "environments"
        self.creds_dir = self.config_dir / "credentials"

        for d in [self.config_dir, self.creds_dir, self._sboms_dir, self.inventory_dir, self.regdefs_dir, self.blueprints_dir, self.environments_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        with open(self.creds_dir / "credentials.yml", "w") as f:
            yaml.dump({}, f)

        with open(self.config_dir / "registry.yml", "w") as f:
            yaml.dump({}, f)

        self._stdout = ""
        self._stderr = ""
        self._returncode = 0

        self._builder = DataBuilder(self)

    @property
    def base_dir(self): return self._base_dir

    @property
    def sboms_dir(self): return self._sboms_dir

    @property
    def config_data(self): return self._config_data

    @config_data.setter
    def config_data(self, value): self._config_data = value

    @property
    def stdout(self): return self._stdout

    @stdout.setter
    def stdout(self, value): self._stdout = value

    @property
    def stderr(self): return self._stderr

    @stderr.setter
    def stderr(self, value): self._stderr = value

    @property
    def returncode(self): return self._returncode

    @returncode.setter
    def returncode(self, value): self._returncode = value

    @property
    def builder(self): return self._builder

    def write_config(self):
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config_data, f)

    def run_module(self, module_name: str, extra_env: dict = None):
        self.write_config()

        env = os.environ.copy()
        env["CI_PROJECT_DIR"] = str(self.base_dir)
        env["SECRET_KEY"] = "c2VjcmV0LWtleS1tdXN0LWJlLTMyLWJ5dGVzLWxvbmc="
        env["EFFECTIVE_SET_CLI_PATH"] = "echo"

        if extra_env:
            env.update(extra_env)

        project_root = str(Path(__file__).parent.parent.parent.resolve())
        python_root = str(Path(project_root) / "python" / "envgene")
        artifact_searcher = str(Path(project_root) / "python" / "artifact-searcher")
        integration = str(Path(project_root) / "python" / "integration")
        jschon_sort = str(Path(project_root) / "python" / "jschon-sort")
        scripts_root = str(Path(project_root) / "scripts")
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{python_root}{os.pathsep}{artifact_searcher}{os.pathsep}{integration}{os.pathsep}{jschon_sort}{os.pathsep}{scripts_root}"

        import sys
        python_exe = sys.executable

        result = subprocess.run(
            [python_exe, "-m", module_name],
            env=env,
            capture_output=True,
            text=True,
            cwd=project_root
        )

        self.stdout = result.stdout
        self.stderr = result.stderr
        self.returncode = result.returncode
        return result

    def run_pipeline(self, extra_env: dict = None):
        env = {
            "ENV_NAMES": "test-cluster/test-env",
            "CLUSTER_NAME": "test-cluster",
            "ENVIRONMENT_NAME": "test-env",
            "FULL_ENV_NAME": "test-cluster/test-env",
            "INSTANCES_DIR": str(self.environments_dir)
        }
        if extra_env:
            env.update(extra_env)

        return self.run_module("scripts.pipeline.orchestrator", extra_env=env)
