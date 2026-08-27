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

## 0. Scope Restriction — MANDATORY

**This branch is strictly limited to BDD test infrastructure. Never create, modify, or delete
any file outside these two paths:**

- `cucumber_tests/` — all test code, test data, step definitions, features
- `.github/workflows/perform_e2e_tests.yml` — the CI workflow that runs the tests

If a change requires touching any file outside this scope, stop and tell the user explicitly
which file and why — do not proceed silently. Never "fix" production code, docs, linters,
or other CI workflows even if you notice a problem.

This rule overrides every other instruction.

---

## 1. Start: Map a Use-Case Document to Tests

Every use-case document under `docs/use-cases/` is the authoritative source for
what tests must exist. Before writing any code, read the target document
completely and list all `UC-<PREFIX>-<N>:` entries.

**Alternate source: technical-design sub-flow docs.** Not every feature has a `docs/use-cases/`
entry. `docs/technical-design/instance-pipeline/sub-flows/*.md` (`bgd.md`, `clean.md`, `deploy.md`,
`management-operations.md`) also drive test files (`bgd-sub-flows.feature`,
`clean-sub-flows.feature`) — one scenario per documented sub-flow/section, titled with a plain
descriptive sentence instead of `UC-<PREFIX>-<N>:` (e.g. `Scenario: CLEAN a whole environment
marks every namespace as cleaned and empties the deploy plan`). These docs state pipeline step
gating in prose ("the rendering functions are DEPLOY only") that can be stale relative to the
orchestrator — see the "Trust code over doc prose" pattern in §11 before asserting step statuses
from the doc text alone. `flow.md`'s step names are the single source of truth for orchestrator
step identifiers; a sub-flow doc's own step numbering (`1.13`, `1.14`, ...) does not always match
the `PipelineStep.name` strings used in `the pipeline step "{name}" has status "{status}"` — read
`scripts/pipeline/orchestrator.py`'s `PipelineStep` subclasses directly to get the real names and
`should_run()` gating per `OPERATION_TYPE`/`PIPELINE_TYPE`.

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
│   ├── data_builders.py                # EnvGene-specific data builders
│   └── golden_compare.py               # Deep directory comparison utility
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
6. **Use an `@xfail_<reason>` tag** for known gaps — scenarios that document expected
   behavior that is not yet implemented. The tag text alone does nothing: `conftest.py`'s
   `pytest_bdd_apply_tag()` only turns a tag into a real `pytest.mark.xfail(strict=True)` when
   that exact tag string is a key in `_XFAIL_REASONS`. A tag that looks meaningful
   (`@xfail_cli_npe`) but was never added to `_XFAIL_REASONS` is purely decorative — pytest
   emits `PytestUnknownMarkWarning: Unknown pytest.mark.xfail_...` and the scenario runs and
   fails normally instead of being reported as an expected failure. When adding a new
   `@xfail_<reason>` tag, always add a matching entry to `_XFAIL_REASONS` in the same change, and
   verify with a real run that the scenario shows `XFAIL` in the pytest output, not `FAILED`.

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
8. **Before writing a new step, grep sibling `step_defs/<other>_steps.py` files for the same step
   text.** If a step you're about to add (e.g. `the pipeline step "{name}" has status "{status}"`,
   or a BG state assertion) already exists in another feature's step-defs file and isn't actually
   feature-specific, **move it** to `shared_steps/unified_pipeline_steps.py` instead of copying it
   — two `@given`/`@then` functions bound to the same step text raise
   `AmbiguousStepDefinition` at collection time across the *whole* `step_defs/` package, not just
   your new file. After moving, re-run the original feature's tests to confirm nothing broke.

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

**Also add a CI step.** `.github/workflows/perform_e2e_tests.yml` runs each feature's
`test_<name>.py` as its own explicit step (build/compose-up/package-install are shared, once).
Copy the existing "Run BGD Sub-flows BDD tests" step, rename it, and point it at the new test
file:

```yaml
      - name: Run <Feature> BDD tests
        run: |
          docker compose -f devtools/docker-compose.yml exec -T cucumber bash -c \
            "set -o pipefail && \
             export PYTHONPATH=/workspace && \
             cd /workspace && \
             pytest cucumber_tests/step_defs/test_<feature>.py \
               -v -s \
               --junitxml=reports/<feature>.xml \
               | tee -a /workspace/e2e_tests.log"
```

Local `./run_bdd_tests.sh` is not a stand-in for this — it sets a wider `PYTHONPATH`
(`/workspace:/workspace/scripts:/envgene-src`) and passes `-c cucumber_tests/pytest.ini`
explicitly, neither of which the CI step does. A new test file that only ever ran through
`run_bdd_tests.sh` has not been proven to work in CI. Before calling the work done, exercise the
new `test_<feature>.py` through the exact CI invocation at least once: `docker build` +
`docker compose up -d --build cucumber` + the `up.sh` install step, then the `pytest
cucumber_tests/step_defs/test_<feature>.py ...` command above, run manually via `docker compose
exec`.

---

## 7. Workspace API Reference

### Key Properties

| Property | Type | Description |
|---|---|---|
| `base_dir` | `Path` | Root directory of the test workspace |
| `sboms_dir` | `Path` | `/sboms/` directory |
| `config_data` | `dict` | In-memory config (written to `config.yml` on run) |
| `stdout` | `str` | Captured stdout from last pipeline run |
| `stderr` | `str` | Captured stderr from last pipeline run |
| `returncode` | `int` | Return code from last pipeline run |
| `builder` | `DataBuilder` | Factory for creating test artifacts |
| `cluster_name` | `str` | Default: `"test-cluster"` — override via `Given environment is "<cluster>/<env>"` |
| `env_name` | `str` | Default: `"test-env"` — override via `Given environment is "<cluster>/<env>"` |
| `extra_env` | `dict` | Extra environment variables passed to pipeline subprocess |

### Key Methods

| Method | Description |
|---|---|
| `run_pipeline(extra_env)` | Execute the unified pipeline orchestrator |
| `assert_success(message)` | Assert `returncode == 0` |
| `assert_failure(message)` | Assert `returncode != 0` |
| `assert_logs_contain(text)` | Assert text in `stdout+stderr` (case-insensitive) |
| `assert_file_exists(path)` | Assert path exists |
| `assert_file_not_exists(path)` | Assert path does not exist |
| `assert_dir_deleted(path)` | Assert directory is gone |
| `get_yaml(path)` | Load and return YAML file as dict |
| `assert_yaml_content_matches(path, payload)` | Deep-compare YAML file to dict |
| `entity_dir(subdir, scope, inventory)` | Resolve entity directory by scope (`env`/`cluster`/`site`) |

### DataBuilder Methods

| Method | Description |
|---|---|
| `get_env_dir(cluster, env)` | Get (and create) environment directory path |
| `create_mock_sboms(app, count, size_mb)` | Create dummy SBOM files with distinct mtimes |
| `modify_first_sbom_size(app, size_mb)` | Inflate first SBOM file via sparse seek |
| `create_inventory_file(cluster, env, content)` | Create `env_definition.yml` |
| `create_paramset_file(place, name, content, cluster, env)` | Create paramset YAML |
| `create_credentials_file(place, name, content, cluster, env)` | Create credentials YAML |
| `create_resource_profile_file(place, name, content, cluster, env)` | Create resource profile YAML |
| `set_bg_state_files(origin_state, peer_state, cluster, env)` | Create BG state marker files |
| `create_bg_namespaces(origin_ns, peer_ns, different_content, cluster, env)` | Create BG namespace dirs |

### Entity Scope Paths

`workspace.entity_dir(subdir, scope)` resolves to:

| Scope | Path |
|---|---|
| `env` | `environments/<cluster>/<env>/Inventory/<subdir>` |
| `cluster` | `environments/<cluster>/<subdir>` |
| `site` | `environments/<subdir>` |

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
- [ ] **CI step added**: `.github/workflows/perform_e2e_tests.yml` has a "Run <Feature> BDD
  tests" step pointing at the new `test_<feature>.py` (§6) — a suite that only runs locally never
  catches a regression in CI
- [ ] **New test file exercised via the exact CI invocation** at least once (narrower
  `PYTHONPATH`, no `-c cucumber_tests/pytest.ini`), not only through `run_bdd_tests.sh`
- [ ] **Doc-vs-code prose checked**: any doc claim about what a step does or skips ("X is DEPLOY
  only", "Y is left untouched") re-verified against the actual `PipelineStep.should_run()`/
  `execute()` in `scripts/pipeline/orchestrator.py`, not asserted from the doc text alone

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

### Pattern: Snapshot for Rollback Tests

When a UC requires asserting that the repository state is unchanged after a
failure, take a snapshot before the pipeline runs:

```python
@given("the repository has an initial state for rollback testing")
def repo_has_initial_state(workspace: EnvGeneWorkspace):
    import shutil
    # ... setup initial files ...
    workspace.pre_run_snapshot_dir = workspace.base_dir.parent / "snapshot"
    if workspace.pre_run_snapshot_dir.exists():
        shutil.rmtree(workspace.pre_run_snapshot_dir)
    shutil.copytree(workspace.base_dir, workspace.pre_run_snapshot_dir)

@then("the repository state is identical to the initial state")
def repo_state_identical(workspace: EnvGeneWorkspace):
    from cucumber_tests.framework.golden_compare import compare_directories
    compare_directories(
        workspace.pre_run_snapshot_dir,
        workspace.base_dir,
        ignore_patterns=["build.env", "configuration/config.yml", "*.bat", "sops"],
    )
```

### Pattern: Large File Generation

Never store large files in Git. Use sparse files at runtime:

```python
@given(parsers.parse('the SBOM directory has a total size of {size_mb:d} MB'))
def sbom_dir_has_large_size(workspace: EnvGeneWorkspace, size_mb: int):
    workspace.builder.create_mock_sboms("app-a", count=3, size_mb=size_mb)
```

### Pattern: JSON Payload as Pipeline Parameter

Many features receive their instructions as a JSON string in an environment
variable. Store it via `workspace.extra_env`:

```python
@given(parsers.parse('the ENV_INVENTORY_CONTENT specifies "{action}" for "envDefinition"'))
def pipeline_inv_content_envdef(workspace: EnvGeneWorkspace, action: str):
    env_def = {"action": action}
    if action != "delete":
        env_def["content"] = {
            "inventory": {},
            "envTemplate": {"name": "test", "artifact": "env-templates:1.0.0"},
        }
    content = {"envDefinition": env_def}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.last_payload = env_def.get("content")
```

### Pitfall: Missing `test_<feature>.py`

Without the runner file, pytest-bdd silently skips all scenarios in the
feature file. Always verify with `--collect-only` that scenarios are discovered.

### Pitfall: Duplicate Step Definitions

Importing `*` from multiple step modules can cause `AmbiguousSteDefinition`
errors if the same step text is defined in more than one module. Always check
shared_steps before implementing a new step.

### Pitfall: Credential Files with Non-Deterministic Encryption

Files encrypted with Fernet (non-deterministic keys) cannot be compared via
golden references. Pass `ignore_patterns=['Credentials']` to
`compare_directories()`.

### Pitfall: `parsers.parse` cannot match an empty quoted value

`the pipeline parameter "{param}" is set to "{value}"` (and any step shaped like it) uses
`parsers.parse`, whose `{value}` placeholder requires at least one character. A step written as
`Given the pipeline parameter "NAMESPACE_NAMES" is set to ""` raises
`StepDefinitionNotFoundError`, not a value error — it looks like a missing step, not an empty
one. When a doc's launch-parameters table says "empty means default" (e.g. `NAMESPACE_NAMES: ""`,
commented as cleaning the whole environment), do not try to set the value to `""`. Omit the
`Given` step entirely — an env var that is never set reads back as falsy the same way an explicit empty
string does (`ctx.params.get("X") or ""`), so the two are equivalent from the pipeline's side.
Leave a one-line comment in the feature file explaining the omission is deliberate, not an
oversight.

### Pattern: Trust code over doc prose for step gating and side effects

Sub-flow docs (§1) describe behavior in prose that can lag the orchestrator. Before asserting a
pipeline step's status or claiming a step "leaves X untouched", read the step's
`should_run()`/`execute()` in `scripts/pipeline/orchestrator.py` (and whatever it calls) directly.
Two concrete traps hit while writing `clean-sub-flows.feature`:

- `clean.md` claims CLEAN's rendering functions are "DEPLOY only", but
  `EnvBuildStep.should_run()` returns true for both DEPLOY and CLEAN, and `build_env()` always
  re-renders every namespace from the template before the CLEAN-only `set_cleaned_mark()` runs at
  the end. The doc's *effective* claim (other content is unchanged) still holds, because the
  re-render is idempotent against the same template inputs — but a test asserting the render
  functions literally do not execute would be wrong. Assert the *effective* outcome (existing
  namespace content plus `cleaned: true`), not the doc's mechanism claim.
- A sub-flow doc's own step numbers (`1.13 generate_deployment_plan`) do not always match the
  orchestrator's step `name` strings (`process_deployment_plan`) — get the real name from the
  `PipelineStep` subclass, never from the doc's flow diagram text.

When code and doc genuinely disagree (not just differently worded), follow the existing
convention already used in `bgd-sub-flows.feature`: keep the code-derived assertion and add an
inline comment such as `# Not part of the documented flow for this sub-flow, but this is real,
current orchestrator behaviour.` so a future doc fix and a future behavior change are both caught
by a diff instead of silently drifting further apart.

### Pattern: Verify cross-referenced identifiers from source before writing fixtures

A single `NAMESPACE_NAMES`-style parameter can be matched against several *different* on-disk
identifiers by different code paths: `reduce_deployment_plan()` filters `deploy-plan.yml` entries
by their bare `namespace:` field, while `set_cleaned_mark()` matches namespace *objects* by
`NamespaceFile.name` — the internal `name:` field read from each `namespace.yml`
(`self.name = openYaml(self.definition_path)['name']`), which is not necessarily the same string
as the `Namespaces/<postfix>/` folder name (`self.postfix = self.path.name`) or an
environment-prefixed physical namespace name a doc example might show (`env-1-bss-origin`).
Nothing in the code cross-checks these against each other — a test fixture fully controls all of
them, so a naming mismatch between a `deploy-plan.yml` fixture and a template's
`template_override: {name: ...}` fails an assertion silently (namespace "not found") rather than
erroring loudly. Before writing deploy-plan/namespace fixtures for a new scenario, grep the
implementation for how each identifier is populated and read, and use one consistent identifier
across every fixture file the scenario touches.

### Pattern: Reuse an existing mock template artifact before registering a new one

`conftest.py`'s `mock_nexus` fixture already serves several pre-built template artifacts (see the
comments above each block in `mock_nexus()`, e.g. `test-artifact:v1` / `default-env-template`
rendering `core` / `bss-origin` / `bss-peer`). Before adding a new artifact block for a new
feature, check whether an existing one already renders the namespace shapes the new scenarios
need — `clean-sub-flows.feature` reuses `test-artifact:v1` as-is rather than registering a
`clean`-specific artifact. Each new artifact block is a new GAV to host, manifest to write, and
ZIP to build; only add one when the scenario genuinely needs content an existing artifact cannot
provide (e.g. `bgNsArtifacts` warmup scenarios need a *second*, distinguishable artifact
version — see the `test-artifact:v2` block and its history in this repository's own Git log for
why it is a version of the same artifactId, not an unrelated one).
