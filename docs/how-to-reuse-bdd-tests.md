# Reusing Qubership EnvGene BDD Tests

This document describes how external projects can reuse the BDD testing framework from `qubership-envgene`.

## Architecture

The testing framework is divided into a reusable (shared) part and a project-specific part:

- **Feature files**: Contain standard Gherkin scenarios (e.g., `sbom-retention.feature`, `blue-green-deployment.feature`).
- **Shared Steps**: Step definitions that are agnostic to the internal structure of any specific project. They interact with the environment exclusively through an abstract interface.
- **BaseWorkspace & BaseDataBuilder**: Abstract Base Classes (ABC) defining the contract (API) that each project must implement.

## Step 1: Accessing the Framework

An external project needs access to the `features/` and `shared_steps/` directories.
This can be achieved via copying, git submodules, or package installation.

## Step 2: Implementing the Workspace

Create a class in your project that inherits from `BaseWorkspace`. You must implement the abstract methods:

```python
from pathlib import Path
from qubership_envgene.tests.framework.base_workspace import BaseWorkspace
from qubership_envgene.tests.framework.base_data_builders import BaseDataBuilder

class ExternalDataBuilder(BaseDataBuilder):
    def get_env_dir(self, cluster_name: str, env_name: str) -> Path:
        return self.workspace.base_dir / "integration-workspaces" / cluster_name / env_name

    def create_inventory_file(self, cluster_name: str, env_name: str, content: dict):
        pass

class ExternalWorkspace(BaseWorkspace):
    def __init__(self, tmp_path):
        self._base_dir = tmp_path
        self._sboms_dir = tmp_path / "sboms"
        self._config_data = {}
        self._stdout = ""
        self._stderr = ""
        self._returncode = 0
        self._builder = ExternalDataBuilder(self)
        
        self._sboms_dir.mkdir(parents=True)

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
    @property
    def stderr(self): return self._stderr
    @property
    def returncode(self): return self._returncode
    @property
    def builder(self): return self._builder

    def run_pipeline(self, extra_env: dict = None):
        import subprocess
        result = subprocess.run(["python", "-m", "external_project.main"], capture_output=True, text=True)
        self._stdout = result.stdout
        self._stderr = result.stderr
        self._returncode = result.returncode
```

## Step 3: Pytest Configuration (conftest.py)

Create or update `conftest.py` in the root of your test directory to return your Workspace implementation:

```python
import pytest
from external_project.tests.workspace import ExternalWorkspace

@pytest.fixture
def workspace(tmp_path):
    return ExternalWorkspace(tmp_path)
```

## Step 4: Creating Entry Points (Step Defs)

Create wrapper files to execute the features. They must import `shared_steps` and bind them to the `features`:

```python
# tests/step_defs/test_sbom_retention.py
from pytest_bdd import scenarios
from qubership_envgene.tests.shared_steps.sbom_retention_steps import *
from qubership_envgene.tests.shared_steps.common_steps import *

scenarios('path/to/shared/features/sbom-retention.feature')
```

## CI/CD Endpoint Execution (Docker)

For the convenience of external projects, the `qubership-envgene` Docker image includes an endpoint script `bdd_runner.py`. This allows running tests against your data and configurations without needing to pull the EnvGene source code.

### Launch Parameters (Environment Variables)

The script is configured via the following optional environment variables:
- `BDD_DATA_DIR`: Local path to the folder containing your project (configurations and `tests/`).
- `BDD_GIT_URL`: Link to a git repository containing your project. If provided, the script will clone it before execution.
- `BDD_GIT_BRANCH`: Git repository branch (defaults to `main`).
- `BDD_TESTS_PATH`: Path to the `step_defs` folder within your project. If omitted, the framework attempts to find local `tests/step_defs` or executes the standard built-in EnvGene BDD scenarios.

All other environment variables are automatically passed into the test execution.

### GitLab CI Example (`.gitlab-ci.yml`)
```yaml
stages:
  - test

bdd_tests:
  stage: test
  image: ghcr.io/netcracker/qubership-envgene:latest
  variables:
    BDD_DATA_DIR: "$CI_PROJECT_DIR"
    BDD_TESTS_PATH: "tests/step_defs"
    TARGET_CLUSTER: "production-cluster"
  script:
    - python /module/scripts/bdd_runner.py
```

### GitHub Actions Example (`github-action.yml`)
```yaml
name: BDD Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/netcracker/qubership-envgene:latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Run BDD Framework
        env:
          BDD_DATA_DIR: ${{ github.workspace }}
          BDD_TESTS_PATH: "tests/step_defs"
        run: |
          python /module/scripts/bdd_runner.py
```
