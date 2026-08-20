import os
import subprocess
import yaml
from pathlib import Path
from .data_builders import DataBuilder
from .base_workspace import BaseWorkspace

_TEST_DATA_DIR = Path(__file__).parent.parent / "test_data" / "einv" / "common"

PLACEHOLDER_FILE = _TEST_DATA_DIR / "placeholder.yml"
ENV_DEFINITION_FILE = _TEST_DATA_DIR / "env_definition.yml"

TEST_YAML_CONTENT = PLACEHOLDER_FILE.read_text(encoding="utf-8")
TEST_ENV_DEFINITION_CONTENT = ENV_DEFINITION_FILE.read_text(encoding="utf-8")


def delete_file_if_exists(path: Path) -> None:
    """Remove a file if it exists, then assert it is gone."""
    if path.exists():
        path.unlink()
    assert not path.exists()


def create_file(path: Path, content: str = TEST_YAML_CONTENT) -> None:
    """Create a file (including parent dirs) with the given text content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


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

        # Default cluster/env names — can be overridden per-test via a Given step.
        self.cluster_name = "test-cluster"
        self.env_name = "test-env"

        for d in [self.config_dir, self.creds_dir, self._sboms_dir, self.inventory_dir, self.regdefs_dir, self.blueprints_dir, self.environments_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        with open(self.creds_dir / "credentials.yml", "w") as f:
            yaml.dump({
                "test-registry": {
                    "data": {
                        "username": "dummy-user",
                        "password": "dummy-password",
                        "secret": "dummy-secret-value"
                    }
                }
            }, f)

        with open(self.config_dir / "registry.yml", "w") as f:
            yaml.dump({
                "test-registry": {
                    "maven-repo": "http://localhost:8000/release",
                    "username": "credentials('test-registry').username",
                    "password": "credentials('test-registry').password"
                }
            }, f)

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

        # Mock run_effective_set_cli for local tests (cross-platform)
        effective_set_cli_mock = self.base_dir / "run_effective_set_cli.bat"
        effective_set_cli_mock.write_text("#!/bin/sh\nexit 0\n")
        os.chmod(effective_set_cli_mock, 0o755)
        env["EFFECTIVE_SET_CLI_PATH"] = str(effective_set_cli_mock)

        if extra_env:
            env.update(extra_env)

        project_root = str(Path(__file__).parent.parent.parent.resolve())
        python_root = str(Path(project_root) / "python" / "envgene")
        artifact_searcher = str(Path(project_root) / "python" / "artifact-searcher")
        integration = str(Path(project_root) / "python" / "integration")
        jschon_sort = str(Path(project_root) / "python" / "jschon-sort")
        scripts_root = str(Path(project_root) / "scripts")
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{python_root}{os.pathsep}{artifact_searcher}{os.pathsep}{integration}{os.pathsep}{jschon_sort}{os.pathsep}{scripts_root}"
        
        # Add base_dir to PATH so that sops_mock (sops.bat) can be found
        env["PATH"] = f"{str(self.base_dir)}{os.pathsep}{env.get('PATH', '')}"

        import sys
        python_exe = sys.executable

        if os.environ.get("ENVGENE_DEBUG_IMPORT_PROBE"):
            probe = subprocess.run(
                [python_exe, "-c",
                 "import build_env.render_config_env as m, inspect, hashlib;"
                 "src=inspect.getsource(m.EnvGenerator.generate_namespace_files_and_map);"
                 "print('PROBE build_env.render_config_env.__file__ =', m.__file__);"
                 "print('PROBE generate_namespace_files_and_map sha256 =', hashlib.sha256(src.encode()).hexdigest());"
                 "print('PROBE generate_namespace_files_and_map source:\\n' + src)"],
                env=env, capture_output=True, text=True, cwd=project_root,
            )
            print("=== ENVGENE_DEBUG_IMPORT_PROBE stdout ===")
            print(probe.stdout)
            print("=== ENVGENE_DEBUG_IMPORT_PROBE stderr ===")
            print(probe.stderr)

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

    def entity_dir(self, subdir: str, scope: str, inventory: str = "Inventory") -> Path:
        """Return the directory for an entity file by scope.

        Args:
            subdir:    entity subdirectory name, e.g. "parameters", "credentials", "resource_profiles".
            scope:     "env", "cluster", or "site".
            inventory: Inventory folder name inserted for env-scope entities (default: "Inventory").

        Scope → path mapping:
            env     → environments/<cluster>/<env>/Inventory/<subdir>
            cluster → environments/<cluster>/<subdir>
            site    → environments/<subdir>
        """
        base = self._base_dir / "environments"
        if scope == "env":
            return base / self.cluster_name / self.env_name / inventory / subdir
        elif scope == "cluster":
            return base / self.cluster_name / subdir
        else:  # site
            return base / subdir

    def run_pipeline(self, extra_env: dict = None):
        project_root = str(Path(__file__).parent.parent.parent.resolve())
        env = {
            "ENV_NAMES": f"{self.cluster_name}/{self.env_name}",
            "CLUSTER_NAME": self.cluster_name,
            "ENVIRONMENT_NAME": self.env_name,
            "FULL_ENV_NAME": f"{self.cluster_name}/{self.env_name}",
            "INSTANCES_DIR": str(self.environments_dir),
            "JSON_SCHEMAS_DIR": str(Path(project_root) / "schemas"),
            "IS_LOCAL_DEV_TEST_ENVGENE": "true",
        }
        if extra_env:
            env.update(extra_env)

        return self.run_module("scripts.pipeline.orchestrator", extra_env=env)

    def assert_success(self, message: str = "Pipeline failed"):
        assert self.returncode == 0, f"{message}. Stderr: {self.stderr}"

    def assert_failure(self, message: str = "Pipeline should have failed"):
        if self.returncode == 0:
            print("STDOUT:\\n", self.stdout)
            print("STDERR:\\n", self.stderr)
        assert self.returncode != 0, message

    def assert_logs_contain(self, text: str):
        assert self.stderr or self.stdout, "No logs produced"
        logs = (self.stderr + self.stdout).lower()
        assert text.lower() in logs, f"Logs do not contain '{text}'"

    def assert_logs_not_contain(self, text: str):
        assert self.stderr or self.stdout, "No logs produced"
        logs = (self.stderr + self.stdout).lower()
        assert text.lower() not in logs, f"Logs erroneously contain '{text}'"

    def assert_file_exists(self, path):
        assert path.exists(), f"File {path} does not exist"

    def assert_file_not_exists(self, path):
        assert not path.exists(), f"File {path} should not exist"

    def assert_dir_deleted(self, path):
        assert not path.exists(), f"Directory {path} was not deleted. STDOUT: {self.stdout} STDERR: {self.stderr}"

    def get_yaml(self, path):
        self.assert_file_exists(path)
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def assert_yaml_content_matches(self, path, payload: dict):
        content = self.get_yaml(path)
        if "credentials" in str(path):
            assert len(content) > 0, "Credentials file is empty"
            for cred_key, cred_val in payload.items():
                assert cred_key in content, f"Credential {cred_key} missing from output"
                if "type" in cred_val:
                    assert content[cred_key]["type"] == cred_val["type"], "Credential type mismatch"
        else:
            assert content == payload, f"File content mismatch. Expected: {payload}, Actual: {content}"
