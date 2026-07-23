---
name: behavioral-guidelines
description: Coding principles — think before acting, keep it simple, make surgical changes, verify with clear success criteria. Biases toward caution over speed.
when_to_use: Use when planning an implementation, reviewing code, refactoring, or writing new features in this repository.
disable-model-invocation: false
---

# Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes.

**Trade-off:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface trade-offs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.


---

## 5. BDD Test Fixture Conventions

### Default configuration files (framework/defaults/)

Hardcoded data structures in test framework initializers are a maintenance hazard — they are invisible to diffing and cannot be audited by looking at test data.

**Rule**: all default fixture values written by `EnvGeneWorkspace.__init__()` must live as real files under `cucumber_tests/framework/defaults/`:

```
cucumber_tests/framework/defaults/
├── credentials.yml   # default test credentials (test-registry dummy values)
└── registry.yml      # default registry config (maven-repo localhost URL)
```

`workspace.py` copies these files with `shutil.copy()` during workspace setup. To override for a specific test case, place the replacement file under `configuration/` inside the test data directory:

```
test_data/e2e/uc_foo_1/
└── configuration/
    ├── credentials/
    │   └── credentials.yml   # overrides framework/defaults/credentials.yml
    └── registry.yml          # overrides framework/defaults/registry.yml
```

`shutil.copytree(source_dir, workspace.base_dir, dirs_exist_ok=True)` will overwrite the defaults with the test-specific values.

### Per-scenario pipeline parameters (params.yml)

Inline pipeline parameter values in feature files are acceptable only when they are:
- Short scalars (< 40 chars), e.g. `"true"`, `"env-templates:2.0.0"`
- Semantically meaningful without context, e.g. `"test-cluster/test-env"`

Long values (JSON payloads, structured objects) must be stored in `params.yml` inside the test data directory and loaded with the step:

```gherkin
Given the pipeline parameters are loaded from test data
```

This step reads `params.yml` from the workspace root and merges values into `workspace.extra_env`.

---

## 6. Running Tests After Changes

**After any code change to `cucumber_tests/`**, run the full test suite in Docker following `cucumber_tests/LOCAL_TESTING_GUIDE.md`. The short version:

### Step 1 — Ensure the Docker environment is running

```bash
# Build the production image (only needed if Dockerfile changed)
docker build -t local-envgene-main -f build_envgene/build/Dockerfile .

# Start / rebuild the cucumber container
docker compose -f devtools/docker-compose.yml up -d --build cucumber

# Install Python packages inside the container
docker compose -f devtools/docker-compose.yml exec -T cucumber \
  bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"
```

### Step 2 — Run all tests

```bash
docker compose -f devtools/docker-compose.yml exec -T cucumber bash -c \
  "export PYTHONPATH=/workspace && cd /workspace && \
   pytest cucumber_tests/step_defs/ -v -s \
     --junitxml=reports/full_run.xml"
```

- JUnit XML report is saved to `reports/full_run.xml`.
- All tests must be **green** (or `xpassed`) before committing.

### Step 3 — Run a single feature file (faster iteration)

```bash
docker compose -f devtools/docker-compose.yml exec -T cucumber bash -c \
  "export PYTHONPATH=/workspace && cd /workspace && \
   pytest cucumber_tests/step_defs/test_blue_green_deployment.py -v -s"
```

### Step 4 — Cleanup (optional)

```bash
docker compose -f devtools/docker-compose.yml down
```

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
