# Extension Pipeline & apply_envgene_patch Documentation

This document describes the GitLab CI extension pipeline and the `apply_envgene_patch` script used to customize the EnvGene GitHub Actions workflow for your instance.

In the [qubership-envgene](https://github.com/Netcracker/qubership-envgene) repository, the Python scripts (`apply_envgene_patch.py`, `git_commit.py`) live under **`github_workflows/instance-repo-pipeline/extend_logic/scripts/`**. The `qubership-instance-repo-pipeline` Docker image copies that folder into the container at **`/opt/github/extend_logic/scripts/`**.

---

## Table of Contents

1. [Overview](#overview)
2. [Pipeline Flow](#pipeline-flow)
3. [GitLab CI configuration](#gitlab-ci-configuration)
4. [apply_envgene_patch Script](#apply_envgene_patch-script)
5. [Patch File Format](#patch-file-format)
6. [Operations Reference](#operations-reference)
7. [Examples](#examples)

---

## Overview

The pipeline uses the Docker image `qubership-instance-repo-pipeline` from [Netcracker/qubership-envgene](https://github.com/Netcracker/qubership-envgene) and extends the base EnvGene workflow by adding new variables and components to `Envgene.yml` - as **steps** or **jobs** depending on the project.

**Flow:**

1. **Init & apply** — `apply_envgene_patch.py` copies the base workflow from `/opt/github` into a **staging directory** `extended_github_instance_pipeline/<tag>/`, applies YAML patch files (components), then by default **packs the result into** **`extended_github_instance_pipeline/<tag>.zip`** and deletes the staging folder. `<tag>` comes from `DOCKER_IMAGE_TAG` or `INSTANCE_REPO_PIPELINE_IMAGE_TAG` (default `latest`). If you pass **no patch files**, only the base snapshot is written as a ZIP (nothing merged or inserted). Use **`--output-format dir`** to keep the versioned folder instead of a ZIP.
2. **Commit & push** — `git_commit.py` commits and pushes changes under `extended_github_instance_pipeline/` (ZIP files and, if used, leftover directories)

This allows instance repositories to extend the base EnvGene workflow with custom variables, steps, and configuration without forking the entire workflow.

---

## Pipeline Flow

The pipeline is defined in `.gitlab-ci.yml` in your instance repository and runs in the `qubership-instance-repo-pipeline` Docker image (from [qubership-envgene](https://github.com/Netcracker/qubership-envgene)). Scripts are executed from paths inside the image: `/opt/github/extend_logic/scripts/` (same files as in the repository under `github_workflows/instance-repo-pipeline/extend_logic/scripts/`).

A complete copypaste example for `.gitlab-ci.yml` is in [GitLab CI configuration](#gitlab-ci-configuration).

**Steps:**

| Step | Description |
|------|-------------|
| Init & apply | Runs `apply_envgene_patch.py`: removes `extended_github_instance_pipeline/<tag>/` (staging) and `.github/`, copies `/opt/github`, applies patches, then writes **`extended_github_instance_pipeline/<tag>.zip`** by default and removes the staging dir |
| Commit & push | Commits changes and pushes to the current branch |

**Requirements:**

- `GITLAB_TOKEN` with `write_repository` scope (for `git_commit.py`)
- `DOCKER_IMAGE_TAG` or `INSTANCE_REPO_PIPELINE_IMAGE_TAG` set so the snapshot path matches the pipeline image tag (see [GitLab CI configuration](#gitlab-ci-configuration))
- Pipeline runs on schedule or manual trigger (not on push/MR by default)

---

## GitLab CI configuration

Copy the following into the root of your instance repository as `.gitlab-ci.yml`, or merge the `extend-the-gh-pipeline` job into an existing file. The image must be a build of [instance-repo-pipeline](https://github.com/Netcracker/qubership-envgene/tree/main/github_workflows/instance-repo-pipeline) whose Dockerfile copies **`extend_logic/scripts/`** from that directory into **`/opt/github/extend_logic/scripts/`** in the image.

**Placeholders:**

| Placeholder | Description |
|-------------|-------------|
| `DOCKER_IMAGE_NAME` | Container image name without tag (for example `registry.example.com/org/qubership-instance-repo-pipeline`) |
| `DOCKER_IMAGE_TAG` | Image tag (for example `1.2.3` or `latest`). Must match the pipeline image tag; the artifact file is **`extended_github_instance_pipeline/<tag>.zip`**. |
| `PATH_TO_COMPONENT` | Zero or more patch YAML files in your repository (for example `components/component-a.yaml`). Omit all arguments to only materialize the base workflow as a ZIP (no merges). |

GitLab artifacts should still publish **`extended_github_instance_pipeline/`** as a whole. By default each run produces **`extended_github_instance_pipeline/<DOCKER_IMAGE_TAG>.zip`** (for example `extended_github_instance_pipeline/1.2.3.zip`). Extract the ZIP to get `workflows/`, `configuration/`, and so on at the archive root.

```yaml
---
#Variables
variables:
  INSTANCE_REPO_PIPELINE_IMAGE: DOCKER_IMAGE_NAME
  INSTANCE_REPO_PIPELINE_IMAGE_TAG: DOCKER_IMAGE_TAG
  DOCKER_IMAGE_TAG: "${INSTANCE_REPO_PIPELINE_IMAGE_TAG}"

#Rules
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "push" || $CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - when: always

#Stages
stages:
  - extend-pipeline

extend-the-gh-pipeline:
  stage: extend-pipeline
  image:
    name: ${INSTANCE_REPO_PIPELINE_IMAGE}:${INSTANCE_REPO_PIPELINE_IMAGE_TAG}
  script:
    - python3 /opt/github/extend_logic/scripts/apply_envgene_patch.py PATH_TO_COMPONENT
    - python3 /opt/github/extend_logic/scripts/git_commit.py
  artifacts:
    paths:
      - extended_github_instance_pipeline/
```

To run **without component patches** (only pack the base workflow into **`extended_github_instance_pipeline/<tag>.zip`**), use a script line with no patch arguments:

```yaml
    - python3 /opt/github/extend_logic/scripts/apply_envgene_patch.py
```

To **keep a directory** instead of a ZIP (for example for debugging), add **`--output-format dir`**:

```yaml
    - python3 /opt/github/extend_logic/scripts/apply_envgene_patch.py --output-format dir PATH_TO_COMPONENT
```

---

## apply_envgene_patch Script

**Location:** `git_commit.py` is in the same directory as `apply_envgene_patch.py`.

- **qubership-envgene tree:** `github_workflows/instance-repo-pipeline/extend_logic/scripts/`
- **`qubership-instance-repo-pipeline` image:** `/opt/github/extend_logic/scripts/`

**Usage:**

```bash
# From the root of a qubership-envgene clone - CI / full run (init from /opt/github + apply patches)
python3 github_workflows/instance-repo-pipeline/extend_logic/scripts/apply_envgene_patch.py components/component-a.yaml components/variables.yaml

# Local run (skip init, apply patches to existing output dir)
python3 github_workflows/instance-repo-pipeline/extend_logic/scripts/apply_envgene_patch.py --no-init components/component-a.yaml components/variables.yaml

# Custom output dir
python3 github_workflows/instance-repo-pipeline/extend_logic/scripts/apply_envgene_patch.py --output-dir my_pipeline components/component-a.yaml

# Keep a versioned directory instead of a ZIP (no packaging step)
python3 github_workflows/instance-repo-pipeline/extend_logic/scripts/apply_envgene_patch.py --output-format dir components/component-a.yaml
```

Adjust the path to the script if your working directory is not the repository root.

**Environment variables (versioned name):**

| Variable | Description |
|----------|-------------|
| `DOCKER_IMAGE_TAG` | Preferred. Used in **`extended_github_instance_pipeline/<tag>.zip`** (or folder `<tag>/` with `--output-format dir`). |
| `INSTANCE_REPO_PIPELINE_IMAGE_TAG` | Used if `DOCKER_IMAGE_TAG` is unset (same value as the pipeline image tag in CI). |
| (none) | Defaults to `latest`. |

Patches are applied against the **staging tree** **`<output-dir>/<tag>/`**. Unless **`--output-format dir`** is used, that directory is removed after **`extended_github_instance_pipeline/<tag>.zip`** is written.

**Options:**

| Option | Description |
|--------|-------------|
| `--output-dir DIR` | Parent directory for artifacts and staging. Maps `target_file` paths starting with `.github/` into the staging directory. Default: `extended_github_instance_pipeline`. |
| `--output-format` | **ZIP** (default): after patching, create **`<output-dir>/<tag>.zip`** and delete staging. **Directory** (`dir`): keep **`<output-dir>/<tag>/`** and do not create a ZIP file. |
| `--init-from DIR` | Before applying patches: remove `<output-dir>/<tag>/` and `.github`, copy DIR into the staging directory. Default: `/opt/github`. |
| `--no-init` | Skip init step. Use when the staging directory already exists (e.g. local runs without `/opt/github`). |

**Default behavior:** The script initializes **`<output-dir>/<tag>/`**, applies patches (if any), then **writes a ZIP archive** unless **`--output-format dir`**. If you pass **no patch file paths**, it only initializes and writes the base snapshot as a ZIP. Use `--no-init` for local runs when the staging tree already exists.

**Dependencies:** `ruamel.yaml` (install via `pip install ruamel.yaml`)

The script reads patch files and applies a sequence of operations to target files. Each operation has an `action` and optional `target_file` (defaults to the first operation's target). Paths like `.github/workflows/Envgene.yml` are resolved to **`<output-dir>/<tag>/workflows/Envgene.yml`** during processing (that path exists only until the ZIP packaging step when using the default format).

---

## Patch File Format

Patch files are YAML documents containing a list of operations. Use `target_file` paths starting with `.github/` — they are resolved under the **staging** snapshot root (e.g. `.github/workflows/Envgene.yml` → `extended_github_instance_pipeline/<tag>/workflows/Envgene.yml` before the result is packaged as a ZIP):

```yaml
---
- target_file: .github/workflows/Envgene.yml
  action: merge
  section: DOCKER_IMAGE_NAMES
  content:
    DOCKER_IMAGE_NAME_DEPLOYTOOL: "my-registry/my-image"

- target_file: .github/configuration/config.env
  action: merge
  content:
    MY_VAR: "value"
```

---

## Operations Reference

### 1. Merge (action: `merge`)

Adds or updates key-value pairs in the target file.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `target_file` | Yes* | Path to target file |
| `action` | Yes | `merge` |
| `content` | Yes | Dict of key-value pairs |
| `section` | For YAML | Section comment (e.g. `#DOCKER_IMAGE_NAMES`) |
| `path` | For YAML | Dotted path (e.g. `jobs.process_environment_variables.outputs`) |

**Merge variants:**

- **.env files** — Merges `KEY=value`; no section/path needed
- **YAML with section** — Merges into block after `#SECTION` comment
- **YAML with path** — Merges into block at dotted path (e.g. `jobs.job_name.outputs`)

---

### 2. Insert (action: `insert`)

Inserts a block of content at a specific position. Requires exactly one anchor.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `target_file` | Yes* | Path to target file |
| `action` | Yes | `insert` |
| `content` | Yes | String or YAML block to insert |
| `after_section` | One of | Insert after `### SECTION - END ###` |
| `before_section` | One of | Insert before `### SECTION - START ###` |
| `after_step` | One of | Insert after step with given name |
| `before_step` | One of | Insert before step with given name |
| `skip_if_present` | No | Skip if this string is already in the file |

**Formatting:** Inserted content gets 2 empty lines before and after; indentation is preserved.

---

## Examples

### Example 1: Merge Docker image names (section-based)

Add or override Docker image names in the `#DOCKER_IMAGE_NAMES` section:

```yaml
---
- path: env
  target_file: .github/workflows/Envgene.yml
  action: merge
  section: DOCKER_IMAGE_NAMES
  content:
    DOCKER_IMAGE_NAME_DEPLOYTOOL: "ghcr.io/myorg/deploytool"
    DOCKER_IMAGE_NAME_ENVGENE: "ghcr.io/myorg/envgene"
```

---

### Example 2: Merge job outputs (path-based)

Add outputs to a specific job:

```yaml
---
- path: jobs.process_environment_variables.outputs
  target_file: .github/workflows/Envgene.yml
  action: merge
  content:
    MY_CUSTOM_OUTPUT: "custom_value"
    ANOTHER_OUTPUT: ${{ env.SOME_VAR }}
```

---

### Example 3: Merge .env variables

Add or update variables in configuration files:

```yaml
---
- target_file: .github/configuration/config.env
  action: merge
  content:
    CONFIG_VAR_1: "value1"
    CONFIG_VAR_2: "value2"

- target_file: .github/pipeline_vars.env
  action: merge
  content:
    PIPELINE_VAR: "my_value"
```

---

### Example 4: Insert block after section (with markers)

Insert a new step block after `### GIT COMMIT - END ###`:

```yaml
---
- target_file: .github/workflows/Envgene.yml
  action: insert
  after_section: "GIT COMMIT"
  content: |
            ### MY CUSTOM STEP - START ###
            - name: My Custom Step
              run: echo "Hello from custom step"
            ### MY CUSTOM STEP - END ###
```

---

### Example 5: Insert block before section

Insert content before a section starts:

```yaml
---
- target_file: .github/workflows/Envgene.yml
  action: insert
  before_section: "BG MANAGE"
  content: |
            - name: Pre-BG step
              run: echo "Running before BG MANAGE"
```

---

### Example 6: Insert by step name (no section markers)

Insert a step after "Prepare environment" or before "Create env file for container":

```yaml
---
- target_file: .github/workflows/Envgene.yml
  action: insert
  after_step: "Prepare environment"
  content: |
            - name: Create name for dynamic secret
              run: |
                SECRET_NAME=$(echo "${{ matrix.environment }}" | awk -F "/" '{print $1}')_${{ env.SECRET_POSTFIX }}
                echo "SECRET_NAME=$SECRET_NAME" >> $GITHUB_ENV
```

Or insert before a step:

```yaml
---
- target_file: .github/workflows/Envgene.yml
  action: insert
  before_step: "Create env file for container"
  content: |
            - name: My step before Create env file
              run: echo "pre-step"
```

**Step name matching:** Case-insensitive, supports partial match (e.g. `"Prepare environment"` matches `"Prepare environment"`).

---

### Example 7: Skip if already present

Avoid duplicate insertion:

```yaml
---
- target_file: .github/workflows/Envgene.yml
  action: insert
  after_section: "GIT COMMIT"
  skip_if_present: "### MY CUSTOM STEP - START ###"
  content: |
            ### MY CUSTOM STEP - START ###
            - name: My Custom Step
              ...
```

---

### Example 8: Full component file (component-a.yaml)

```yaml
---
- path: env
  target_file: .github/workflows/Envgene.yml
  action: merge
  section: DOCKER_IMAGE_NAMES
  content:
    DOCKER_IMAGE_NAME_DEPLOYTOOL: "MY_VALUE"

- path: env
  target_file: .github/workflows/Envgene.yml
  action: merge
  section: DOCKER_IMAGE_TAGS
  content:
    DOCKER_IMAGE_TAG_DEPLOYTOOL: "MY_VALUE"

- path: jobs.process_environment_variables.outputs
  target_file: .github/workflows/Envgene.yml
  action: merge
  content:
    MY_NEW_VARIABLE: "MY_VALUE"

- path: jobs.envgene_execution.steps
  target_file: .github/workflows/Envgene.yml
  action: insert
  after_section: "GIT COMMIT"
  content: |
            ### MY CUSTOM STEP - START ###
            - name: My Custom Step
              if: needs.process_environment_variables.outputs.MY_FEATURE_ENABLED == 'true'
              env:
                DYNAMIC_SECRET: ${{ secrets[env.SECRET_NAME] }}
              run: |
                echo "Custom step logic..."
            ### MY CUSTOM STEP - END ###
```

---

## Envgene.yml Structure (Reference)

The base workflow uses these extension points:

| Extension point | Type | Example |
|-----------------|------|---------|
| `#DOCKER_IMAGE_NAMES` | Section comment | Merge env vars |
| `#DOCKER_IMAGE_TAGS` | Section comment | Merge env vars |
| `jobs.process_environment_variables.outputs` | Dotted path | Merge job outputs |
| `### SECTION - START ###` / `### SECTION - END ###` | Section markers | Insert steps |
| Step names | `- name: "..."` | Insert by step anchor |

---

## Adding New Patch Files

1. Create a YAML file in `components/` (e.g. `components/my-feature.yaml`)
1. Add operations following the format above
1. Register the file in `.gitlab-ci.yml` (paths below match scripts inside the pipeline image):

```yaml
- python3 /opt/github/extend_logic/scripts/apply_envgene_patch.py components/component-a.yaml components/variables.yaml components/my-feature.yaml
```

1. Patches are applied in order; later patches can override or extend earlier ones.

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Source directory not found: /opt/github` | Running locally without Docker image | Use `--no-init` and ensure output-dir exists, or `--init-from` a local path |
| `Section #X not found` | Section comment missing in target | Add `#SECTION` comment or use `path` |
| `Marker '### X - END ###' not found` | Section markers missing | Add `### SECTION - START ###` and `### SECTION - END ###` |
| `Step 'X' not found` | Step name doesn't match | Use exact or partial step name (case-insensitive) |
| `Block 'path' not found` | Dotted path invalid | Verify YAML structure (jobs → job_name → outputs) |
| `File not found` | Wrong target path or output-dir missing | Use path relative to repository root; run with init or `--no-init` on existing dir |
| `Invalid DOCKER_IMAGE_TAG` | Tag contains path separators | Use a plain tag only (for example `1.2.3`), not a path |
