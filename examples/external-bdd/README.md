# Guide: Integrating E2E Tests into Implementation Projects

This directory contains templates and examples to help you quickly integrate E2E (BDD) testing using `qubership-envgene` into your implementation projects.

By using this framework, you can automatically validate that your environment instances and templates build correctly before pushing them to production.

---

## 1. Quick Start: GitLab CI Integration

If your configurations (templates and environment instances) are stored in Git repositories, we provide a ready CI template that automatically fetches the required data and runs the testing pipeline.

1. Copy `implementation-project-template.gitlab-ci.yml` to the root of your project as `.gitlab-ci.yml` (or include it).
   *Note: This template contains multiple examples (jobs) showing how to run all tests, a single specific test, custom tests with HTML reports, and how to use a matrix to test an array of environments.*
2. Set your repository URLs in the variables:
   ```yaml
   ENV_TEMPLATES_REPO: "https://gitlab.example.com/my-group/env-templates.git"
   ENV_INSTANCES_REPO: "https://gitlab.example.com/my-group/env-instances.git"
   ```
3. For private repositories, use authentication (e.g., Deploy Tokens or CI Job Tokens) in the `git clone` steps inside the `before_script` block.

---

## 2. Writing BDD Test Scenarios

The framework uses **Gherkin syntax** (`Given`, `When`, `Then`) to describe test scenarios. You should place your `.feature` files in your project's test directory (e.g., `tests/features/`).

### Reusing Unified Pipeline Steps
You **do not** need to write Python code for standard pipeline operations. `qubership-envgene` provides a set of pre-built, unified steps that you can import directly.

Here are the most important unified steps available to you:

| Step Pattern | Description | Example |
|--------------|-------------|---------|
| `Given the workspace is initialized with test data from "{path}"` | Copies your test data (e.g., `test_data/e2e/base`) into the isolated test workspace. | `Given the workspace is initialized with test data from "e2e/base"` |
| `And the pipeline parameter "{param}" is set to "{value}"` | Sets an environment variable for the pipeline execution. | `And the pipeline parameter "ENV_NAMES" is set to "cluster1/env1"` |
| `When the unified pipeline orchestrator runs` | Executes the main EnvGene pipeline using the parameters you set. | `When the unified pipeline orchestrator runs` |
| `Then the orchestrator completes successfully` | Asserts that the pipeline finished with an exit code of `0`. | `Then the orchestrator completes successfully` |
| `Then the orchestrator fails` | Asserts that the pipeline failed (exit code != `0`). | `Then the orchestrator fails` |
| `And the environment instance "{env_path}" matches the reference "{ref_path}"` | Recursively compares the generated output against a "Golden" reference directory. | `And the environment instance "cluster1/env1" matches the reference "golden/ref-env1"` |

### Example Scenario
See `customer-e2e-template.feature` for a complete example of how to combine these steps into successful and failure test cases.

---

## 3. Structuring Test Data (Base vs Golden)

When writing tests, you typically need two types of test data:

1. **Base Data (`test_data/e2e/base`)**: The starting state of your repositories *before* the pipeline runs. It usually contains mock versions of `env-templates` and `env-instances`.
2. **Golden Reference Data (`test_data/golden/ref-1`)**: The exact expected state of the repository *after* the pipeline completes successfully.

Your test project structure should look like this:
```
my-project/
├── tests/
│   ├── features/
│   │   └── my-tests.feature         # Gherkin scenarios
│   ├── step_defs/
│   │   └── test_my_feature.py       # Python glue code
│   └── conftest.py                  # Pytest fixtures
└── test_data/
    ├── e2e/
    │   └── base/                    # Starting state (templates/instances)
    └── golden/
        └── ref-1/                   # Expected result for comparison
```

---

## 4. Customizing Test Logic in Python

To run these tests, you need a bit of Python glue code. 

1. **Workspace Fixture**: Copy `workspace_template.py` and `conftest_template.py` into your `tests/` directory to provide the isolated workspace environment for tests.
2. **Step Definitions**: Copy `steps_template.py` and modify it. It shows you how to import the unified steps mentioned above, and how to define your own custom steps (e.g., checking for specific files in your output).

By reusing the unified steps, your custom Python code remains minimal and focused only on project-specific assertions!
