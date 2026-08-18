---
name: envgene-bdd-tests
description: >
  Guidelines for creating, editing, and verifying BDD (Gherkin/Cucumber) tests
  for the EnvGene project. Covers the full workflow: mapping use-case documents
  to feature files, structuring test data, writing step definitions, wiring test
  runners, golden reference comparison, and the checklist to verify coverage.
when_to_use: >
  Use this skill when creating new BDD/Cucumber test scenarios, editing existing
  feature files, writing step definitions, setting up test data, debugging test
  failures, or reviewing test coverage against use-case documentation.
---

# EnvGene BDD Test Skill

This skill describes the conventions, structure, and end-to-end workflow for
adding new BDD (Cucumber/Gherkin) tests to the EnvGene suite under
`cucumber_tests/`.

---

## 1. Start: Map a Use-Case Document to Tests

Every use-case document under `docs/use-cases/` is the authoritative source for
what tests must exist. Before writing any code, read the target document
completely and list all `UC-<PREFIX>-<N>:` entries.

### Use-Case Document Structure

Each use case follows this template:

```text
### UC-<PREFIX>-<N>: <Title>

**Pre-requisites:**
  <initial state of the workspace / filesystem>

**Trigger:**
  <pipeline parameters set to start the pipeline>

**Steps:**
  <observable processing steps>

**Results:**
  <verifiable outcomes: files created/deleted, log messages>
```

**Key fields you will use in tests:**

| Field | Maps to Gherkin keyword |
|---|---|
| Pre-requisites | `Given` |
| Trigger (pipeline params) | `And the pipeline parameter "X" is set to "Y"` or feature-specific `Given` |
| Pipeline execution | `When the unified pipeline orchestrator runs` |
| Results (success/failure) | `Then the orchestrator completes successfully` / `Then the pipeline fails` |
| Results (log messages) | `And the pipeline log contains "..."` |
| Results (file state) | `And the "<file>" file is created/updated/deleted` |
| Results (structural output) | `And the environment instance "..." matches the reference "..."` |

---

## 2. Project Layout

```text
cucumber_tests/
├── conftest.py                          # Session-scoped fixtures (mock_nexus, workspace)
├── pytest.ini                           # pytest configuration
├── features/                            # Gherkin .feature files
│   └── <feature-name>.feature
├── step_defs/                           # pytest-bdd step implementations + test runners
│   ├── __init__.py
│   ├── common_steps.py                  # Re-exports shared_steps/common_steps
│   ├── <feature>_steps.py              # Feature-specific step definitions
│   └── test_<feature>.py               # Test runner (wires scenarios to pytest)
├── shared_steps/                        # Steps reusable across all features
│   ├── __init__.py
│   ├── common_steps.py                  # Golden comparison, log assertions, pipeline params
│   └── unified_pipeline_steps.py        # Workspace init, pipeline run, orchestrator steps
├── framework/                           # Workspace and data builder infrastructure
│   ├── __init__.py
│   ├── base_workspace.py               # Abstract workspace contract
│   ├── workspace.py                    # EnvGeneWorkspace implementation
│   ├── base_data_builders.py           # Shared data builders (SBOM, BG state)
│   ├── data_builders.py               # EnvGene-specific data builders
│   └── golden_compare.py              # Deep directory comparison utility
└── test_data/                           # Static test fixtures
    ├── e2e/                             # One directory per scenario
    │   └── uc_<prefix>_<n>/            # Mirrors workspace layout
    ├── einv/                            # Shared inventory fixtures (common/, env_definition.yml)
    └── golden/                          # Golden reference directories
        └── ref-<prefix>/               # Expected output for comparison
```

---

## 3. Feature File Conventions

### Naming and Location

- Feature files live in `cucumber_tests/features/`.
- Filename must match the use-case document name (without path):
  `environment-inventory-generation.feature` ↔
  `docs/use-cases/environment-inventory-generation.md`.

### Structure Template

```gherkin
Feature: <Title> - <use-case-doc-name>.md
  As an EnvGene <actor>
  I want to <goal>
  So that <benefit>

  Background:
    Given <common precondition for all scenarios, if any>

  # ── <Group heading from the UC doc> ──────────────────────────────────────

  Scenario: UC-<PREFIX>-<N>: <Scenario title from documentation>
    Given <pre-requisites setup>
    And the pipeline parameter "<PARAM>" is set to "<value>"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And <validation steps>
```

### Negative (failure) Scenario Template

```gherkin
  Scenario: UC-<PREFIX>-<N>: <Scenario title — negative case>
    Given <pre-requisites setup>
    And <input that triggers failure>
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log contains "<error message from Results section>"
    And <additional state assertions>
```

### Rules

1. **One scenario per UC.** Each `UC-*` in the doc maps to exactly one
   `Scenario:` block. Do not merge or split UC entries.
2. **Scenario title must match the UC title** from the documentation
   (prefix `UC-<PREFIX>-<N>:`).
3. **Group scenarios** with comment headers (`# ── <Group> ───`) matching
   the section headings in the UC document.
4. **Use `Background:` sparingly** — only for preconditions shared by
   every scenario in the file (e.g., `Given the pipeline has ENV_BUILD set to "false"`).
5. **Always add validation steps** beyond "pipeline succeeds". Check file
   state, log messages, or generated content from the UC Results section.
6. **Use `@xfail` tag** for known gaps — scenarios that document expected
   behavior that is not yet implemented.

---

## 4. Test Data Conventions

### Location

Test data lives in `cucumber_tests/test_data/e2e/<test-data-id>/`.
The `<test-data-id>` matches the scenario slug: `uc_einv_ed_2`,
`uc_sbom_3`, etc. (lowercase, underscores).

### Workspace Layout

Each test data directory mirrors the workspace root:

```text
uc_<prefix>_<n>/
├── configuration/
│   └── config.yml              # Runtime config (sbom_retention, etc.)
├── environments/
│   └── <cluster-name>/
│       └── <env-name>/
│           ├── Inventory/
│           │   └── env_definition.yml
│           ├── AppDefs/
│           └── RegDefs/
└── sboms/
    └── <app-name>/
        └── <app-name>-v0.sbom.json
```

### Scenario Rules

1. **Each scenario gets its own test data directory** with unique content.
   Do NOT copypaste identical directories.
2. **Only create a test data directory** when the scenario has a meaningful
   pre-existing state. If the scenario starts from scratch ("file does not
   exist"), omit the directory and use a `Given` step that does nothing or
   clears the path.
3. **`configuration/config.yml`** is loaded at workspace init time and
   merged into the in-memory config dict before the pipeline writes it.
4. **SBOM file naming**: `<app-name>-v<N>.sbom.json` where N is a numeric
   index. Files with higher N are treated as newer (modification time is
   set deterministically: `v0` = oldest, `vN` = newest).
5. **Large files** (e.g., for total size limit tests) must NOT be stored
   in the repository. Use a `Given` step with sparse files (`seek` + `write`) to
   inflate them at runtime via `workspace.builder.create_mock_sboms(..., size_mb=...)`.
6. **Golden references** go in `cucumber_tests/test_data/golden/<ref-name>/`.
   Run with `UPDATE_GOLDEN=1` to regenerate from actual output.

---

## 5. Step Definition Conventions

### File Organization

| File | Purpose |
|---|---|
| `step_defs/<feature>_steps.py` | Feature-specific steps |
| `shared_steps/common_steps.py` | Generic assertions (golden compare, log check, pipeline params) |
| `shared_steps/unified_pipeline_steps.py` | Workspace init, pipeline execution, common orchestrator steps |
| `step_defs/common_steps.py` | Reexports from `shared_steps/common_steps` |

### Available Shared Steps (no need to re-implement)

**From `shared_steps/unified_pipeline_steps.py`:**

```gherkin
Given the workspace is initialized with test data from "<e2e/uc_xyz>"
Given the pipeline parameter "<PARAM>" is set to "<value>"
Given the config parameter "<param>" is set to <value>
Given a deploy parameter "<param>" is set to "<value>" in the environment instance
Given a credential "<cred_id>" has "<value>" for username in the environment instance
When the unified pipeline orchestrator runs
Then the orchestrator completes successfully
Then the orchestrator fails
Then the orchestrator fails with return code <N>
Then the pipeline log contains "<message>"
```

**From `shared_steps/common_steps.py`:**

```gherkin
Given the pipeline has <PARAM> set to "<value>"
Then the pipeline fails
Then the effective set is generated successfully
Then the pipeline log shows "<message>"
Then the environment instance "<cluster>/<env>" matches the reference "<ref-path>"
Then the workspace matches the reference "<ref-path>"
Then the generated definitions match the reference "<ref-path>"
```

### Writing Feature-Specific Steps

```python
# step_defs/<feature>_steps.py
from pytest_bdd import given, when, then, parsers
from cucumber_tests.framework.workspace import EnvGeneWorkspace
import yaml
from pathlib import Path


@given(parsers.parse('the <entity> file "{name}" does not exist at "{scope}" scope'))
def target_entity_not_exist(workspace: EnvGeneWorkspace, entity: str, name: str, scope: str):
    """Ensure entity file is absent before test."""
    path = _entity_dir(workspace, entity, scope) / f"{name}.yml"
    if path.exists():
        path.unlink()
    assert not path.exists()


@then(parsers.parse('the "{filename}" file is created'))
def file_is_created(workspace: EnvGeneWorkspace, filename: str):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    file_path = env_dir / "Inventory" / filename
    assert file_path.exists(), (
        f"File {filename} was not created.\nSTDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    workspace.last_checked_file_path = file_path
```

### Step Writing Rules

1. **First parameter is always `workspace`** — injected by the `workspace`
   fixture from `conftest.py`.
2. **Use `parsers.parse()`** for parameterized steps with typed arguments.
3. **Include descriptive assert messages** showing expected vs actual values,
   and append `workspace.stdout` / `workspace.stderr` to failure messages.
4. **Never use `pass`** in step implementations. Every step must either
   assert something or modify workspace state.
5. **Store intermediate values on workspace** using dynamic attributes
   (`workspace.last_checked_file_path`, `workspace.last_payload`,
   `workspace.pre_run_snapshot_dir`, etc.) to pass context between steps
   within the same scenario.
6. **Log assertions** use `workspace.assert_logs_contain(text)` which
   searches both `workspace.stdout` and `workspace.stderr` (case-insensitive).
7. **Set extra environment variables** via `workspace.extra_env[KEY] = value`.
   Always check `if not hasattr(workspace, 'extra_env'): workspace.extra_env = {}`.

---

## 6. Test Runner Wiring

Each feature file needs a corresponding `test_<name>.py` in `step_defs/`:

```python
# cucumber_tests/step_defs/test_<feature-name>.py
from pytest_bdd import scenarios
from cucumber_tests.step_defs.<feature>_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.common_steps import *   # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403

scenarios('../features/<feature-name>.feature')
```

Without this file, pytest-bdd will not discover or run the scenarios.

---

## 7. Workspace API

Full property, method and DataBuilder reference: `references/workspace-api.md`.

---

## 8. Step-by-Step Workflow for a New Feature

Follow this order when implementing BDD tests for a new use-case document:

### Step 1 — Read the UC document

Open `docs/use-cases/<feature-name>.md`. List every `UC-*` entry with its:

- Pre-requisites (what files/config must exist)
- Trigger (what pipeline parameters to set)
- Results (what to assert)


### Step 2 — Create the feature file

```text
cucumber_tests/features/<feature-name>.feature
```

Write one `Scenario:` per UC entry. Use grouping comments that match the
document sections. Mark unimplemented behavior with `@xfail`.

### Step 3 — Create test data directories

For each scenario where pre-requisites require existing files, create:

```text
cucumber_tests/test_data/e2e/uc_<prefix>_<n>/
```

Contents must mirror the workspace layout. Only include files that differ
from the "empty workspace" baseline.

### Step 4 — Identify missing steps

Run the feature file with pytest-bdd to get `StepDefinitionNotFoundError`
for each unimplemented step:

```bash
pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini \
  --collect-only 2>&1 | grep "StepDefinitionNotFoundError"
```

### Step 5 — Implement feature-specific steps

Create `cucumber_tests/step_defs/<feature>_steps.py`. Reuse all shared
steps from `shared_steps/`. Only implement what is genuinely feature-specific.

### Step 6 — Wire the test runner

Create `cucumber_tests/step_defs/test_<feature-name>.py` (see §6).

### Step 7 — Run and iterate

```bash
pytest cucumber_tests/step_defs/test_<feature>.py -v -s -c cucumber_tests/pytest.ini
```

Fix failures. Once green, generate golden references if needed:

```bash
UPDATE_GOLDEN=1 pytest cucumber_tests/step_defs/test_<feature>.py -v -s \
  -c cucumber_tests/pytest.ini
```

---

## 9. Checklist: Verifying Test Coverage

When reviewing a feature file against its use-case documentation, verify:

- [ ] **All UCs covered**: Each `UC-*` in the doc has a matching `Scenario:`
- [ ] **Scenario titles match**: `Scenario: UC-<PREFIX>-<N>: <exact title>`
- [ ] **Test data is unique per scenario**: No copypasted identical directories
- [ ] **Pre-requisites reflected**: Config and file state match UC prerequisites
- [ ] **Trigger parameters set**: Pipeline env vars match UC Trigger section
- [ ] **Success/failure asserted**: `orchestrator completes successfully` or `pipeline fails`
- [ ] **Log assertions present**: Key log messages from UC Results are verified
- [ ] **File state assertions present**: Post-pipeline file counts/existence checked
- [ ] **Payload/content assertions present**: YAML content verified where applicable
- [ ] **Golden reference exists**: `test_data/golden/` has expected data (if used)
- [ ] **Test runner exists**: `step_defs/test_<feature>.py` wires the feature
- [ ] **No shared step re-implementation**: Feature steps do not duplicate shared steps

---

## 10. Running Tests Locally

```bash
# All BDD tests
pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini -v -s

# Specific feature
pytest cucumber_tests/step_defs/test_<feature>.py -v -s -c cucumber_tests/pytest.ini

# Specific scenario by name
pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini -k "UC-EINV-1" -v -s

# Update golden references
UPDATE_GOLDEN=1 pytest cucumber_tests/step_defs/test_<feature>.py -v -s \
  -c cucumber_tests/pytest.ini
```

---

## 11. Common Patterns and Pitfalls

See `references/patterns.md` for full examples of:

- Snapshot pattern for rollback tests
- Large file generation via sparse files
- JSON payload as pipeline parameter
- Pitfalls: missing runner file, duplicate step definitions, non-deterministic encryption
