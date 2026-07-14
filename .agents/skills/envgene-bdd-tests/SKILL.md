---
name: envgene-bdd-tests
description: >
  Guidelines for creating, editing, and verifying BDD (Gherkin/Cucumber) tests
  for the EnvGene project. Covers feature file conventions, test data layout,
  step definition patterns, golden reference comparison, and the test runner
  wiring required by pytest-bdd.
when_to_use: >
  Use this skill when creating new BDD/Cucumber test scenarios, editing existing
  feature files, writing step definitions, setting up test data, debugging test
  failures, or reviewing test coverage against use-case documentation.
---

# EnvGene BDD Test Skill

This skill describes the conventions, structure, and patterns used in the
EnvGene BDD (Cucumber/Gherkin) test suite located under `cucumber_tests/`.

## Project Layout

```
cucumber_tests/
├── conftest.py                          # Session-scoped fixtures (mock_nexus, workspace)
├── pytest.ini                           # pytest configuration
├── features/                            # Gherkin .feature files
│   ├── environment-inventory-generation.feature
│   └── sbom-retention.feature
├── step_defs/                           # pytest-bdd step implementations + test runners
│   ├── __init__.py
│   ├── common_steps.py                  # Re-exports shared_steps/common_steps
│   ├── inventory_gen_steps.py           # EIG-specific step definitions
│   ├── sbom_retention_steps.py          # SBOM retention step definitions
│   ├── test_environment_inventory_generation.py  # Test runner for EIG
│   └── test_sbom_retention.py                    # Test runner for SBOM retention
├── shared_steps/                        # Steps reusable across projects
│   ├── __init__.py
│   ├── common_steps.py                  # Golden comparison, log assertions, pipeline params
│   └── unified_pipeline_steps.py        # Workspace init, pipeline run, orchestrator steps
├── framework/                           # Workspace and data builder infrastructure
│   ├── __init__.py
│   ├── base_workspace.py               # Abstract workspace contract
│   ├── workspace.py                    # EnvGeneWorkspace implementation
│   ├── base_data_builders.py           # Shared data builders (SBOM, BG state)
│   ├── data_builders.py                # EnvGene-specific data builders
│   └── golden_compare.py               # Deep directory comparison utility
└── test_data/                           # Static test fixtures
    ├── e2e/                             # End-to-end test data directories
    │   ├── uc-sbom-1/                   # One directory per scenario
    │   ├── uc-sbom-2/
    │   └── ...
    ├── einv/                            # Environment inventory test data
    └── golden/                          # Golden reference directories
        └── ref-uc-sbom/                 # Expected output for comparison
```

## Feature File Conventions

### Naming

- Feature files live in `cucumber_tests/features/`.
- File name matches the use-case document name: `sbom-retention.feature` ↔
  `docs/use-cases/sbom-retention.md`.

### Structure

```gherkin
Feature: <Title> - <use-case-doc-name>.md
  As an EnvGene developer
  I want to <goal>
  So that <benefit>

  Scenario: UC-<PREFIX>-<N>: <Scenario title from documentation>
    Given the workspace is initialized with test data from "e2e/uc-<prefix>-<n>"
    And the pipeline parameter "<PARAM>" is set to "<value>"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And <validation steps>
```

### Rules

1. **One scenario per use case.** Each `UC-*` from the documentation maps to
   exactly one `Scenario:` block.
2. **Scenario title must match the use-case title** in the documentation
   (prefix `UC-<PREFIX>-<N>:`).
3. **Use unified pipeline steps** (`Given the workspace is initialized...`,
   `When the unified pipeline orchestrator runs`, `Then the orchestrator
   completes successfully`) for all e2e scenarios.
4. **Add validation steps** beyond "pipeline succeeds". Check file counts,
   log messages, generated content.
5. **Use `the pipeline log contains`** step for log assertions.
6. **Use golden reference comparison** (`the environment instance ... matches
   the reference ...`) for structural output validation.

## Test Data Conventions

### Location

- Test data lives in `cucumber_tests/test_data/e2e/<test-data-id>/`.
- The `<test-data-id>` matches the scenario: `uc-sbom-1`, `uc-sbom-2`, etc.

### Structure

Each test data directory mirrors the workspace layout:

```
uc-sbom-2/
├── configuration/
│   └── config.yml              # Runtime config (sbom_retention, etc.)
├── environments/
│   └── test-cluster/
│       └── test-env/
│           ├── Inventory/
│           │   └── env_definition.yml
│           ├── AppDefs/
│           └── RegDefs/
└── sboms/
    ├── app-a/
    │   ├── app-a-v0.sbom.json
    │   └── ...
    └── app-b/
        └── ...
```

### Rules

1. **Each scenario gets its own test data directory** with unique content.
   Do NOT copy-paste identical directories.
2. **`configuration/config.yml`** is loaded into `workspace.config_data` at
   init time. If the file exists, its contents are merged into the in-memory
   config dict before the pipeline writes it.
3. **SBOM file naming**: `<app-name>-v<N>.sbom.json` where N is a numeric
   index. Files with higher N are treated as newer.
4. **SBOM file modification times** are set deterministically at workspace
   init time: `v0` = oldest, `vN` = newest.
5. **Large files** (e.g., for total size limit tests) should NOT be stored
   in the repo. Use a `Given` step with sparse files (`seek` + `write`) to
   inflate them at runtime.
6. **Golden references** go in `cucumber_tests/test_data/golden/<ref-name>/`.
   Run with `UPDATE_GOLDEN=1` to regenerate from actual output.

## Step Definition Conventions

### File Organization

- **Feature-specific steps**: `step_defs/<feature>_steps.py`
  (e.g., `sbom_retention_steps.py`).
- **Shared steps**: `shared_steps/common_steps.py` and
  `shared_steps/unified_pipeline_steps.py`.
- **Common re-export**: `step_defs/common_steps.py` re-exports from shared.

### Writing Steps

```python
from pytest_bdd import scenarios
from tests.shared_steps.unified_pipeline_steps import *   # maero
# from cucumber_tests.shared_steps.unified_pipeline_steps import *  # base

scenarios('../features/unified_pipeline_success/sbom-retention.feature')
```

### Rules

1. **First parameter is always `workspace`** — injected by the `workspace`
   fixture from `conftest.py`.
2. **Use `parsers.parse()`** for parameterized steps with typed arguments.
3. **Include descriptive assert messages** that show expected vs actual values.
4. **Do not use `pass`** in step implementations. Every step must either
   assert something or modify workspace state.
5. **Log assertions** use `workspace.stdout` and `workspace.stderr` (captured
   from subprocess).

## Test Runner Wiring

Each feature file needs a corresponding `test_<name>.py` in `step_defs/`:

```python
from pytest_bdd import scenarios
from cucumber_tests.step_defs.<feature>_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.common_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403

scenarios('../features/<feature-name>.feature')
```

Without this file, pytest-bdd will not discover or run the scenarios.

## Workspace API Reference

### Key Properties

| Property       | Type   | Description                                      |
|---------------|--------|--------------------------------------------------|
| `base_dir`    | `Path` | Root directory of the test workspace              |
| `sboms_dir`   | `Path` | `/sboms/` directory                              |
| `config_data` | `dict` | In-memory config (written to `config.yml` on run) |
| `stdout`      | `str`  | Captured stdout from last pipeline run            |
| `stderr`      | `str`  | Captured stderr from last pipeline run            |
| `returncode`  | `int`  | Return code from last pipeline run                |
| `builder`     | `DataBuilder` | Factory for creating test artifacts         |

### Key Methods

| Method              | Description                                   |
|--------------------|-----------------------------------------------|
| `run_pipeline()`   | Execute the unified pipeline orchestrator      |
| `assert_success()` | Assert returncode == 0                         |
| `assert_failure()` | Assert returncode != 0                         |
| `assert_logs_contain(text)` | Assert text appears in stdout+stderr  |

### DataBuilder Methods

| Method                                  | Description                              |
|----------------------------------------|------------------------------------------|
| `create_mock_sboms(app, count, size_mb)` | Create dummy SBOM files with distinct mtimes |
| `modify_first_sbom_size(app, size_mb)` | Inflate first SBOM file via sparse seek   |
| `get_env_dir(cluster, env)`            | Get environment directory path            |

## Checklist: Verifying Test Coverage

When reviewing a feature file against its use-case documentation, verify:

- [ ] **All UCs covered**: Each `UC-*` in the doc has a matching `Scenario:`
- [ ] **Test data is unique per scenario**: No copy-pasted identical directories
- [ ] **Configuration matches UC**: `config.yml` in test data reflects UC pre-requisites
- [ ] **Input data matches UC**: File counts, directory structure match UC pre-requisites
- [ ] **Validation steps present**: Not just "pipeline succeeds" — check actual behavior
- [ ] **Log assertions present**: Key log messages from UC Results section are verified
- [ ] **File state assertions present**: Post-pipeline file counts/existence are verified
- [ ] **Golden reference exists**: `test_data/golden/` has the expected reference data
- [ ] **Test runner exists**: `step_defs/test_<feature>.py` wires the feature
- [ ] **Workflow includes feature**: `.github/workflows/perform_e2e_tests.yml` runs it

## Running Tests Locally

```bash
# All BDD tests
pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini -v -s

# Specific feature
pytest cucumber_tests/step_defs/test_sbom_retention.py -v -s -c cucumber_tests/pytest.ini

# Specific scenario by name
pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini -k "UC-SBOM-1" -v -s

# Update golden references
UPDATE_GOLDEN=1 pytest cucumber_tests/step_defs/test_sbom_retention.py -v -s -c cucumber_tests/pytest.ini
```
