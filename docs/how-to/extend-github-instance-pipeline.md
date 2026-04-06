# Extension Pipeline & apply_envgene_patch Documentation

This document describes the GitLab CI extension pipeline and the `apply_envgene_patch` script used to customize the EnvGene GitHub Actions workflow for your instance.

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

1. **Init & apply** — `apply_envgene_patch.py` removes old output, copies base workflow from `/opt/github` to `extended_github_instance_pipeline/`, then applies YAML patch files (components) that add variables and workflow steps/jobs
2. **Commit & push** — `git_commit.py` commits and pushes the modified `extended_github_instance_pipeline/` directory

This allows instance repositories to extend the base EnvGene workflow with custom variables, steps, and configuration without forking the entire workflow.

---

## Pipeline Flow

The pipeline is defined in `.gitlab-ci.yml` in your instance repository and runs in the `qubership-instance-repo-pipeline` Docker image (from [qubership-envgene](https://github.com/Netcracker/qubership-envgene)). Scripts are executed from paths inside the image: `/opt/github/extend_logic/scripts/`.

A complete copy-paste example for `.gitlab-ci.yml` is in [GitLab CI configuration](#gitlab-ci-configuration).

**Steps:**

| Step | Description |
|------|-------------|
| Init & apply | Runs `apply_envgene_patch.py`: removes `extended_github_instance_pipeline/` and `.github/`, copies `/opt/github` to output dir, applies patches (adds variables and steps/jobs to `Envgene.yml`) |
| Commit & push | Commits changes and pushes to the current branch |

**Requirements:**

- `GITLAB_TOKEN` with `write_repository` scope (for `git_commit.py`)
- Pipeline runs on schedule or manual trigger (not on push/MR by default)

---

## GitLab CI configuration

Copy the following into the root of your instance repository as `.gitlab-ci.yml`, or merge the `extend-the-gh-pipeline` job into an existing file. The image must be a build of [instance-repo-pipeline](https://github.com/Netcracker/qubership-envgene/tree/main/github_workflows/instance-repo-pipeline) that includes `extend_logic` scripts under `/opt/github/extend_logic/scripts/`.

**Placeholders:**

| Placeholder | Description |
|-------------|-------------|
| `DOCKER_IMAGE_NAME` | Container image name without tag (for example `registry.example.com/org/qubership-instance-repo-pipeline`) |
| `DOCKER_IMAGE_TAG` | Image tag (for example `1.2.3` or `latest`) |
| `PATH_TO_COMPONENT` | One or more patch YAML files in your repo (for example `components/component-a.yaml` or several paths separated as extra arguments to the script) |

```yaml
---
#Variables
variables:
  INSTANCE_REPO_PIPELINE_IMAGE: DOCKER_IMAGE_NAME
  INSTANCE_REPO_PIPELINE_IMAGE_TAG: DOCKER_IMAGE_TAG

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

---

## apply_envgene_patch Script

**Location:** in your repository clone, use `scripts/apply_envgene_patch.py` if you keep scripts next to the pipeline; in the `qubership-instance-repo-pipeline` image, use `/opt/github/extend_logic/scripts/apply_envgene_patch.py`.

**Usage:**

```bash
# CI / full run (init from /opt/github + apply patches)
python3 scripts/apply_envgene_patch.py components/component-a.yaml components/variables.yaml

# Local run (skip init, apply patches to existing output dir)
python3 scripts/apply_envgene_patch.py --no-init components/component-a.yaml components/variables.yaml

# Custom output dir
python3 scripts/apply_envgene_patch.py --output-dir my_pipeline components/component-a.yaml
```

**Options:**

| Option | Description |
|--------|-------------|
| `--output-dir DIR` | Output directory. Maps `target_file` paths starting with `.github/` to this directory. Default: `extended_github_instance_pipeline`. |
| `--init-from DIR` | Before applying patches: remove output-dir and `.github`, copy DIR to output-dir. Default: `/opt/github`. |
| `--no-init` | Skip init step. Use when output-dir already exists (e.g. local runs without `/opt/github`). |

**Default behavior:** The script first initializes the output directory (removes `extended_github_instance_pipeline/` and `.github/`, copies `/opt/github` to output-dir), then applies patches. Use `--no-init` for local runs.

**Dependencies:** `ruamel.yaml` (install via `pip install ruamel.yaml`)

The script reads patch files and applies a sequence of operations to target files. Each operation has an `action` and optional `target_file` (defaults to the first operation's target). Paths like `.github/workflows/Envgene.yml` are resolved to `output_dir/workflows/Envgene.yml`.

---

## Patch File Format

Patch files are YAML documents containing a list of operations. Use `target_file` paths starting with `.github/` — they are resolved to the output directory (e.g. `.github/workflows/Envgene.yml` → `extended_github_instance_pipeline/workflows/Envgene.yml`):

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
