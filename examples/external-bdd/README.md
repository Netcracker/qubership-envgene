# Guide: Integrating E2E Tests into Implementation Projects

This directory contains templates and examples to help you quickly integrate E2E (BDD) testing using `qubership-envgene` into your implementation projects.

By using this framework, you can automatically validate that your environment instances and templates build correctly before pushing them to production.

---

## 1. Quick Start: CI/CD Integration

If your configurations (templates and environment instances) are stored in Git repositories, we provide ready-to-use CI templates that automatically clone your repositories and run the testing pipeline.

### GitHub Actions
1. Copy `github-action-template.yml` into your `.github/workflows/` directory.
2. Set your repository URLs in the `env` section:
   ```yaml
   ENV_TEMPLATES_REPO: "https://github.com/your-org/env-templates.git"
   ENV_INSTANCES_REPO: "https://github.com/your-org/env-instances.git"
   ```
3. For private repositories, utilize Personal Access Tokens (PAT) mapped to GitHub Secrets and configure the `git clone` steps accordingly.

### GitLab CI
1. Copy `implementation-project-template.gitlab-ci.yml` to the root of your project as `.gitlab-ci.yml`.
2. Configure your repository variables.
3. For private repositories, use authentication (e.g., Deploy Tokens or `CI_JOB_TOKEN`) in the `git clone` steps inside the `before_script` block.

**Both CI templates contain multiple comprehensive examples:**
* **Run All Tests:** Clones repositories and executes all scenarios in your test suite.
* **Run Specific Tests:** Shows how to run a single test, filter by name, or use logical OR conditions (`-k "TestA or TestB"`).
* **Run Custom Tests:** Demonstrates how to run a subset of custom tests and output a self-contained HTML report.
* **Run Array/Matrix of Tests:** Parallelizes tests across multiple clusters or environments by creating isolated data directories for each matrix job.

---

## 2. Structuring Test Data (Base vs Golden)

When writing tests, you typically need two types of test data to perform reliable verifications:

1. **Base Data (`test_data/e2e/base`)**: The starting state of your repositories *before* the pipeline runs. It usually contains mock versions of your `env-templates` and `env-instances` tailored for the test case.
2. **Golden Reference Data (`test_data/golden/ref-1`)**: The exact expected output state *after* the pipeline completes successfully.

### Recommended Directory Structure

```text
my-project/
├── tests/
│   ├── features/
│   │   └── customer-e2e-template.feature # Gherkin scenarios (BDD)
│   ├── step_defs/
│   │   └── steps_template.py             # Python glue code connecting scenarios to functions
│   ├── conftest.py                       # Pytest fixtures (copy from conftest_template.py)
│   └── workspace_template.py             # Logic for isolating workspaces during testing
└── test_data/
    ├── e2e/
    │   └── base_proj/                    # The mocked templates/instances repositories
    └── golden/
        └── ref-proj-001/                 # The Expected Output reference data for assertions
```

---

## 3. Writing BDD Test Scenarios

The framework uses **Gherkin syntax** (`Given`, `When`, `Then`) to describe test scenarios in `.feature` files.

### Reusing Unified Pipeline Steps

You **do not** need to write complex Python code for standard pipeline operations. `qubership-envgene` provides a set of pre-built, unified steps that you can import directly into your step definitions.

| Step Pattern | Description | Example |
|--------------|-------------|---------|
| `Given the workspace is initialized with test data from "{path}"` | Copies your base test data into an isolated test workspace. | `Given the workspace is initialized with test data from "e2e/base"` |
| `And the pipeline parameter "{param}" is set to "{value}"` | Sets an environment variable for the pipeline execution. | `And the pipeline parameter "ENV_NAMES" is set to "cluster1/env1"` |
| `When the unified pipeline orchestrator runs` | Executes the main EnvGene pipeline using the parameters you provided. | `When the unified pipeline orchestrator runs` |
| `Then the orchestrator completes successfully` | Asserts that the pipeline finished with an exit code of `0`. | `Then the orchestrator completes successfully` |
| `Then the orchestrator fails` | Asserts that the pipeline failed (exit code != `0`). | `Then the orchestrator fails` |
| `And the environment instance "{env_path}" matches the reference "{ref_path}"` | Recursively compares the generated output against a "Golden" reference directory. | `And the environment instance "cluster1/env1" matches the reference "golden/ref-env1"` |

### Concrete Test Case Examples

Review `customer-e2e-template.feature` for comprehensive examples. 

**Example: A Happy Path Execution**
```gherkin
Scenario: UC-PROJ-001: Successful Environment Generation
  Given the workspace is initialized with test data from "e2e/base_proj"
  And the pipeline parameter "ENV_NAMES" is set to "prod-cluster/backend-env"
  And the pipeline parameter "ENV_BUILDER" is set to "true"
  When the unified pipeline orchestrator runs
  Then the orchestrator completes successfully
  And the environment instance "prod-cluster/backend-env" matches the reference "golden/ref-proj-001"
```

---

## 4. Customizing Test Logic in Python

To execute the `.feature` files, you need "glue code" in Python.

1. **Workspace Fixtures**: Copy `workspace_template.py` and `conftest_template.py` into your `tests/` directory to manage isolated filesystem environments for every test case.
2. **Step Definitions**: Copy `steps_template.py` into your `tests/step_defs/` folder. This file shows how to automatically map the Gherkin statements to Python functions.

### Writing Custom Assertions
If the unified steps are not enough, you can write custom steps in your `steps_template.py` file. 

**In your feature file:**
```gherkin
And a project-specific audit file is created at "dev-cluster/frontend-env"
```

**In your Python steps file:**
```python
from pytest_bdd import then, parsers
import os

@then(parsers.parse('a project-specific audit file is created at "{env_path}"'))
def check_audit_file(workspace, env_path):
    audit_file = workspace.workspace_dir / "environments" / env_path / "audit.log"
    assert audit_file.exists(), f"Audit file missing at {audit_file}"
```

By reusing the unified steps, your custom Python code remains minimal and focused only on project-specific business logic!
