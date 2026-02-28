# EnvGene GitHub Workflow — User Guide

![EnvGene Workflow](assets/envgene-workflow-diagram.png)

- [EnvGene GitHub Workflow — User Guide](#envgene-github-workflow--user-guide)
  - [Overview](#overview)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Workflow Structure](#workflow-structure)
    - [Pipeline Steps](#pipeline-steps)
  - [Workflow Dispatch Inputs](#workflow-dispatch-inputs)
    - [Understanding the 10-Input Limit](#understanding-the-10-input-limit)
    - [Input Reference](#input-reference)
  - [GH_ADDITIONAL_PARAMS — Passing Extra Parameters](#gh_additional_params--passing-extra-parameters)
    - [What Is GH_ADDITIONAL_PARAMS?](#what-is-gh_additional_params)
    - [Format and Syntax](#format-and-syntax)
    - [Examples](#examples)
    - [JSON Values and Escaping](#json-values-and-escaping)
    - [When to Use pipeline_vars.env Instead](#when-to-use-pipeline_varsenv-instead)
  - [Adding New Parameters](#adding-new-parameters)
    - [Option A: Add as Workflow Input (If Under the Limit)](#option-a-add-as-workflow-input-if-under-the-limit)
    - [Option B: Use GH_ADDITIONAL_PARAMS](#option-b-use-gh_additional_params)
    - [Option C: Use pipeline_vars.env](#option-c-use-pipeline_varsenv)
  - [Adding New Jobs and Conditional Execution](#adding-new-jobs-and-conditional-execution)
    - [Step 1: Ensure the Variable Is Available](#step-1-ensure-the-variable-is-available)
    - [Step 2: Expose the Variable as a Job Output](#step-2-expose-the-variable-as-a-job-output)
    - [Step 3: Add the Job Step with an if Condition](#step-3-add-the-job-step-with-an-if-condition)
    - [Complete Example: Adding a Custom Job](#complete-example-adding-a-custom-job)
  - [Parameter Priority](#parameter-priority)
  - [Repository Variables (vars)](#repository-variables-vars)
  - [How to Trigger the Workflow](#how-to-trigger-the-workflow)
    - [Via GitHub Actions UI](#via-github-actions-ui)
    - [Via GitHub API](#via-github-api)
  - [Directory Structure](#directory-structure)
  - [Further Reading](#further-reading)

## Overview

The **EnvGene** workflow (`Envgene.yml`) is a GitHub Actions pipeline that automates environment generation, configuration, and deployment for the EnvGene platform. It provides the same functionality as the GitLab-based instance pipeline, adapted for GitHub Actions.

The workflow is **manually triggered only** (`workflow_dispatch`) and supports:

- Environment inventory generation
- Application and registry definition processing
- Solution Descriptor (SD) processing
- Environment build
- Effective Set generation
- Blue-Green management
- Credential rotation
- Git commit of generated artifacts

## Installation

This section describes what you need to set up the EnvGene workflow in your instance repository.

### Prerequisites

- A GitHub repository (instance repository) with the [EnvGene instance structure](/docs/samples/instance-repository/)
- GitHub Actions enabled for the repository
- GitHub-hosted runners (or self-hosted runners with Docker available)

### Step 1: Copy the Pipeline

Copy the `.github` directory from this folder to the root of your instance repository:

```bash
cp -r github_workflows/instance-repo-pipeline/.github /path/to/your/instance-repo/
```

The copied structure includes the workflow, scripts, configuration files, and the `load-env-files` action.

### Step 2: Configure Required Secrets

Go to **Settings** → **Secrets and variables** → **Actions** → **Secrets**, and add:

| Secret                    | Required          | Description                                                           |
|---------------------------|-------------------|-----------------------------------------------------------------------|
| `SECRET_KEY`              | When using Fernet | Fernet key for credential encryption                                 |
| `ENVGENE_AGE_PUBLIC_KEY`  | When using SOPS   | Public key from EnvGene AGE key pair (SOPS encryption)               |
| `ENVGENE_AGE_PRIVATE_KEY` | When using SOPS   | Private key from EnvGene AGE key pair (SOPS decryption)                |
| `GH_ACCESS_TOKEN`         | Yes               | GitHub token with `contents: write` to commit changes to repository  |

At least one encryption method (Fernet or SOPS) must be configured if your repository uses encrypted credentials. See [Credential Encryption](/docs/how-to/credential-encryption.md) for details.

### Step 3: Optional — Repository Variables

Configure variables in **Settings** → **Secrets and variables** → **Actions** → **Variables** to override defaults:

| Variable                   | Default              | Purpose                                           |
|----------------------------|----------------------|---------------------------------------------------|
| `DOCKER_REGISTRY`          | `ghcr.io/netcracker` | Docker registry for EnvGene images                 |
| `GH_RUNNER_TAG_NAME`       | `ubuntu-22.04`       | Runner label for workflow jobs                     |
| `GH_RUNNER_SCRIPT_TIMEOUT` | `10`                 | Job timeout in minutes                             |

See [Repository Variables (vars)](#repository-variables-vars) for details.

### Step 4: Optional — Customize Configuration

- **`.github/configuration/config.env`** — Base pipeline configuration (e.g. `CI_PROJECT_DIR`, `GITHUB_USER_*`). Edit if you need different defaults.
- **`.github/pipeline_vars.env`** — Override pipeline parameters for debugging or recurring runs. Leave empty or add variables as needed.

### Verifying the Setup

1. Ensure the workflow file is at `.github/workflows/Envgene.yml`.
1. Ensure required secrets are set.
1. Trigger the workflow manually (see [Quick Start](#quick-start)) with a valid `ENV_NAMES` value.

For initializing a new instance repository from scratch, see [Environment Instance Repository Installation Guide](/docs/how-to/envgene-maitanance.md).

## Quick Start

1. Ensure the pipeline is installed (see [Installation](#installation)).
1. Go to **Actions** → **EnvGene Execution** → **Run workflow**.
1. Fill in **ENV_NAMES** (e.g. `cluster-01/env-01`) and any other parameters.
1. Click **Run workflow**.

## Workflow Structure

The workflow consists of two main jobs:

| Job                              | Purpose                                                                 |
|----------------------------------|-------------------------------------------------------------------------|
| `process_environment_variables`  | Parses inputs, loads config, builds matrix, exports variables           |
| `envgene_execution`              | Runs EnvGene steps per environment (matrix job)                         |

The first job prepares all parameters and passes them to the second job via a shared `.env` artifact and job outputs. The second job runs once per environment in the matrix.

### Pipeline Steps

The following sections describe each step in the pipeline as defined in `Envgene.yml`. Steps marked as *conditional* run only when their condition is met.

#### Job: `process_environment_variables`

| Step                         | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| Repository Checkout          | Checks out the repository (without persisting credentials)                  |
| Load environment variables   | Loads `config.env` and `pipeline_vars.env` into `GITHUB_ENV`               |
| Process Input Parameters     | Exports workflow inputs (ENV_NAMES, ENV_BUILDER, etc.) to environment       |
| Process additional variables | Parses `GH_ADDITIONAL_PARAMS` and adds each `KEY=VALUE` to environment     |
| Create env_generation_params  | Builds `ENV_GENERATION_PARAMS` JSON from SD/ENV_SPECIFIC_PARAMS variables   |
| Multiple Environment Processing | Generates environment matrix from `ENV_NAMES` (comma/semicolon/space)     |
| Create .env file             | Dumps all environment variables to `.env`                                   |
| Upload .env as artifact      | Uploads `.env` for use by `envgene_execution` job                           |

#### Job: `envgene_execution` (runs per environment in matrix)

| Step                    | Condition                                      | Description                                                                 |
|-------------------------|------------------------------------------------|-----------------------------------------------------------------------------|
| Repository Checkout     | Always                                         | Checks out repository with full history                                    |
| Download environment-file| Always                                         | Downloads `.env` artifact from previous job                                |
| Prepare environment     | Always                                         | Restores env vars, sets `PACKAGE_NAME`, extracts `CLUSTER_NAME`/`ENV_NAME`  |
| Create name for dynamic secret | Always                                   | Sets `SECRET_NAME` for cluster-specific secrets                            |
| Create env file for container | Always                                    | Exports env to `.env.container` for Docker steps                           |
| **BG_MANAGE**           | `BG_MANAGE == 'true'`                          | Blue-Green operations: state management, Origin/Peer config, validation     |
| **ENV_INVENTORY_GENERATION** | `ENV_INVENTORY_CONTENT` / `ENV_SPECIFIC_PARAMS` / `ENV_TEMPLATE_NAME` set | Generates Environment Inventory at `env_definition.yml` |
| **CREDENTIAL_ROTATION**  | `CRED_ROTATION_PAYLOAD` not empty              | Rotates credentials per payload                                            |
| **APP_REG_DEF_PROCESS**  | `ENV_BUILDER == 'true'`                        | Sets template version, renders App/Reg definitions, handles certs            |
| **PROCESS_SD**           | `SD_SOURCE_TYPE=json` + `SD_DATA` or `artifact` + `SD_VERSION`              | Processes Solution Descriptor (JSON or artifact)   |
| **ENV_BUILD**            | `ENV_BUILDER == 'true'`                        | Main environment build: generates Environment Instance from templates      |
| **GENERATE_EFFECTIVE_SET** | `GENERATE_EFFECTIVE_SET == 'true'`           | Generates Effective Set (SBOMs, validation, deployment artifacts)           |
| **GIT_COMMIT**           | Always                                         | Commits changes to repository, prepares artifacts for downstream use        |

Each conditional step (in **bold**) also uploads its output as an artifact. The `GIT_COMMIT` step always runs at the end of the pipeline.

## Workflow Dispatch Inputs

### Understanding the 10-Input Limit

GitHub Actions limits `workflow_dispatch` to **10 input parameters**. The EnvGene pipeline uses 9 of them for the most common parameters. The 10th slot is reserved for `GH_ADDITIONAL_PARAMS`, which acts as a container for all other parameters.

This design lets you pass any number of additional parameters without hitting the limit.

### Input Reference

| Input                   | Required | Default   | Type   | Description                                                             |
|-------------------------|----------|-----------|--------|-------------------------------------------------------------------------|
| `ENV_NAMES`             | Yes      | —         | string | Environment(s) to process. Format: `cluster/env` or comma-separated     |
| `DEPLOYMENT_TICKET_ID`  | No       | `""`      | string | Ticket ID used as commit message prefix                                 |
| `ENV_TEMPLATE_VERSION`  | No       | `""`      | string | Template version to apply (e.g. `env-template:v1.2.3`)                   |
| `ENV_BUILDER`           | No       | `"true"`  | choice | Enable environment build. Options: `true`, `false`                       |
| `GENERATE_EFFECTIVE_SET`| No       | `"false"` | choice | Enable Effective Set generation. Options: `true`, `false`                |
| `GET_PASSPORT`          | No       | `"false"` | choice | Enable Cloud Passport discovery. Options: `true`, `false`                |
| `CMDB_IMPORT`           | No       | `"false"` | choice | Enable CMDB export. Options: `true`, `false`                             |
| `GH_ADDITIONAL_PARAMS`  | No       | `""`      | string | Comma-separated key-value pairs for all other parameters                 |

For full parameter semantics, see [Instance Pipeline Parameters](/docs/instance-pipeline-parameters.md).

## GH_ADDITIONAL_PARAMS — Passing Extra Parameters

### What Is GH_ADDITIONAL_PARAMS?

`GH_ADDITIONAL_PARAMS` is a single string input that carries all pipeline parameters that are not exposed as separate workflow inputs. It is parsed by `.github/scripts/process_additional_variables.sh`, which adds each `KEY=VALUE` pair to the workflow environment.

Use it for parameters such as:

- `BG_MANAGE`, `BG_STATE` — Blue-Green operations
- `SD_SOURCE_TYPE`, `SD_VERSION`, `SD_DATA` — Solution Descriptor
- `ENV_SPECIFIC_PARAMS`, `ENV_TEMPLATE_NAME` — Environment configuration
- `EFFECTIVE_SET_CONFIG` — Effective Set options
- `CRED_ROTATION_PAYLOAD` — Credential rotation
- Any other parameter from [Instance Pipeline Parameters](/docs/instance-pipeline-parameters.md)

### Format and Syntax

**Format:** `KEY1=VALUE1,KEY2=VALUE2,KEY3=VALUE3`

**Rules:**

- Pairs are separated by commas.
- Each pair is `KEY=VALUE` (no spaces around `=`).
- Keys and values are trimmed of leading/trailing whitespace.
- Empty pairs are ignored.

### Examples

**Simple values:**

```text
BG_MANAGE=true,SD_SOURCE_TYPE=artifact,SD_VERSION=my-app:v1.0
```

**With JSON (escape double quotes):**

```text
EFFECTIVE_SET_CONFIG={\"version\": \"v2.0\", \"app_chart_validation\": \"false\"}
```

**Multiple parameters:**

```text
SD_SOURCE_TYPE=json,SD_DATA=[{\"version\":2.1,\"type\":\"solutionDeploy\"}],ENV_SPECIFIC_PARAMS={\"tenantName\":\"my-tenant\"}
```

**Blue-Green state:**

```text
BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"bss-controller\",\"originNamespace\":{\"name\":\"bss-origin\",\"state\":\"active\"}}
```

### JSON Values and Escaping

For JSON values:

1. Escape internal double quotes: `\"` instead of `"`.
1. Be aware that commas inside JSON are used as pair separators. If your JSON contains commas, the parser may split it incorrectly.

**Workaround for complex JSON:** Use `pipeline_vars.env` (see below) or pass the parameter via the GitHub API with proper escaping.

### When to Use pipeline_vars.env Instead

Use `.github/pipeline_vars.env` when:

- You have complex JSON with many commas.
- You want to keep sensitive or long values out of the UI.
- You need the same values across many runs (e.g. for debugging).

Variables in `pipeline_vars.env` must be in standard `KEY=VALUE` format. Do **not** wrap them in `GH_ADDITIONAL_PARAMS`.

## Adding New Parameters

### Option A: Add as Workflow Input (If Under the Limit)

If you have fewer than 10 inputs and want a dedicated UI field:

1. Add the input under `on.workflow_dispatch.inputs` in `Envgene.yml`:

```yaml
on:
  workflow_dispatch:
    inputs:
      # ... existing inputs ...
      MY_NEW_PARAM:
        required: false
        default: ""
        type: string
        description: "Description of the parameter"
```

1. Add a line in the "Process Input Parameters" step to export it:

```yaml
echo "MY_NEW_PARAM=${{ github.event.inputs.MY_NEW_PARAM }}" >> $GITHUB_ENV
```

1. If the parameter controls job execution, add it to `process_environment_variables.outputs` (see [Adding New Jobs](#adding-new-jobs-and-conditional-execution)).

### Option B: Use GH_ADDITIONAL_PARAMS

1. Pass the parameter in `GH_ADDITIONAL_PARAMS`, e.g. `MY_NEW_PARAM=value`.
1. It will be parsed and added to `GITHUB_ENV` automatically.
1. If you need it for conditional steps, add it to the job outputs (see below).

### Option C: Use pipeline_vars.env

1. Add the variable to `.github/pipeline_vars.env`:

```text
MY_NEW_PARAM=my_value
```

1. It will be loaded by the `load-env-files` action.
1. If you need it for conditional steps, add it to the job outputs.

## Adding New Jobs and Conditional Execution

To add a new step that runs only when a parameter is set, follow these steps.

### Step 1: Ensure the Variable Is Available

The variable must be present in `GITHUB_ENV` after the `process_environment_variables` job. It can come from:

- A workflow input (and the "Process Input Parameters" step)
- `GH_ADDITIONAL_PARAMS` (parsed by `process_additional_variables.sh`)
- `pipeline_vars.env` or `config.env` (loaded by `load-env-files`)

### Step 2: Expose the Variable as a Job Output

Add the variable to the `outputs` of `process_environment_variables` in `Envgene.yml`:

```yaml
jobs:
  process_environment_variables:
    outputs:
      env_matrix: ${{ steps.matrix-generator.outputs.env_matrix }}
      # ... existing outputs ...
      MY_NEW_FEATURE: ${{ env.MY_NEW_FEATURE }}
```

Without this, the next job cannot use it in `if` conditions.

### Step 3: Add the Job Step with an if Condition

Add your step inside the `envgene_execution` job with an `if`:

```yaml
- name: MY_NEW_JOB
  if: needs.process_environment_variables.outputs.MY_NEW_FEATURE == 'true'
  run: |
    # Your commands here
```

**Common condition patterns:**

| Condition type      | Example                                                                 |
|---------------------|-------------------------------------------------------------------------|
| Equals string       | `needs.process_environment_variables.outputs.MY_VAR == 'true'`          |
| Not empty           | `needs.process_environment_variables.outputs.MY_VAR != ''`               |
| Logical OR          | `(condition1) \|\| (condition2)`                                         |
| Logical AND         | `(condition1) && (condition2)`                                           |
| Multiple conditions | `outputs.ENV_BUILDER == 'true' && outputs.SD_VERSION != ''`              |

### Complete Example: Adding a Custom Job

Assume you want a step that runs only when `RUN_CUSTOM_VALIDATION=true`.

**1. Pass the parameter** via `GH_ADDITIONAL_PARAMS`:

```text
RUN_CUSTOM_VALIDATION=true
```

**2. Add the output** in `Envgene.yml`:

```yaml
process_environment_variables:
  outputs:
    # ... existing ...
    RUN_CUSTOM_VALIDATION: ${{ env.RUN_CUSTOM_VALIDATION }}
```

**3. Add the step** in `envgene_execution`:

```yaml
- name: CUSTOM_VALIDATION
  if: needs.process_environment_variables.outputs.RUN_CUSTOM_VALIDATION == 'true'
  run: |
    echo "Running custom validation..."
    # Your validation logic
```

## Parameter Priority

When the same parameter is set in multiple places, the effective value is chosen by this order (highest first):

1. Workflow input parameters (UI or API)
1. `pipeline_vars.env`
1. Repository variables (`vars`)
1. Organization variables

## Repository Variables (vars)

Repository variables are configured in **Settings → Secrets and variables → Actions → Variables** (repository-level) or at the organization level. They are referenced in the workflow as `vars.VARIABLE_NAME` and are available to all workflow runs.

### Variables Used by the Workflow

| Variable                   | Purpose                                  | Default when empty   |
|----------------------------|------------------------------------------|----------------------|
| `DOCKER_REGISTRY`          | Docker registry base for EnvGene images  | `ghcr.io/netcracker` |
| `GH_RUNNER_TAG_NAME`       | Runner label for jobs (e.g. ubuntu-22.04)| `ubuntu-22.04`       |
| `GH_RUNNER_SCRIPT_TIMEOUT` | Job timeout in minutes                   | `10`                 |

### How to Add Repository Variables

1. Go to your repository on GitHub.
1. Open **Settings** → **Secrets and variables** → **Actions**.
1. Open the **Variables** tab.
1. Click **New repository variable**.
1. Enter the name (e.g. `DOCKER_REGISTRY`) and value.
1. Click **Add variable**.

### When Variables Are Empty or Missing

The workflow uses fallback values when a variable is not set or is empty. For example:

```yaml
runs-on: ${{ vars.GH_RUNNER_TAG_NAME || 'ubuntu-22.04' }}
DOCKER_IMAGE_NAME_ENVGENE: "${{ vars.DOCKER_REGISTRY || 'ghcr.io/netcracker' }}/qubership-envgene"
timeout-minutes: ${{ fromJSON(vars.GH_RUNNER_SCRIPT_TIMEOUT || '10') }}
```

- If `vars.GH_RUNNER_TAG_NAME` is empty or missing → `ubuntu-22.04` is used.
- If `vars.DOCKER_REGISTRY` is empty or missing → `ghcr.io/netcracker` is used.
- If `vars.GH_RUNNER_SCRIPT_TIMEOUT` is empty or missing → `10` is used.

You do not need to define these variables for the workflow to run; defaults are applied automatically.

### Adding Custom Variables

To use your own variables in the workflow:

1. Add the variable in **Settings → Secrets and variables → Actions → Variables**.
1. Reference it in `Envgene.yml` as `${{ vars.MY_CUSTOM_VAR }}`.
1. For optional variables with a default, use: `${{ vars.MY_CUSTOM_VAR || 'default_value' }}`.

For a full list of supported repository variables, see [EnvGene Repository Variables](/docs/envgene-repository-variables.md).

## How to Trigger the Workflow

### Via GitHub Actions UI

1. Open your repository on GitHub.
1. Go to **Actions**.
1. Select **EnvGene Execution**.
1. Click **Run workflow**.
1. Choose the branch, fill in parameters, and run.

### Via GitHub API

```bash
curl -X POST \
  -H "Authorization: token <YOUR_GITHUB_TOKEN>" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/<OWNER>/<REPO>/actions/workflows/Envgene.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "ENV_NAMES": "cluster-01/env-01",
      "ENV_BUILDER": "true",
      "GENERATE_EFFECTIVE_SET": "true",
      "DEPLOYMENT_TICKET_ID": "QBSHP-0001",
      "GH_ADDITIONAL_PARAMS": "EFFECTIVE_SET_CONFIG={\"version\": \"v2.0\", \"app_chart_validation\": \"false\"}"
    }
  }'
```

Replace `<YOUR_GITHUB_TOKEN>`, `<OWNER>`, `<REPO>`, and `main` as needed.

## Directory Structure

```text
instance-repo-pipeline/
├── README.md                    # This file
└── .github/
    ├── actions/
    │   └── load-env-files/      # Loads .env files into GITHUB_ENV
    ├── configuration/
    │   └── config.env           # Base pipeline configuration
    ├── docs/
    │   └── README.md            # Additional usage notes
    ├── scripts/
    │   ├── generate_env_matrix.sh           # Builds environment matrix from ENV_NAMES
    │   ├── process_additional_variables.sh  # Parses GH_ADDITIONAL_PARAMS
    │   ├── process_matrix_iteration.sh      # Extracts cluster/env from matrix
    │   └── create_env_generation_params.sh # Builds ENV_GENERATION_PARAMS JSON
    ├── workflows/
    │   └── Envgene.yml          # Main workflow definition
    └── pipeline_vars.env       # Optional overrides (template, often empty)
```

## Further Reading

- [Instance Pipeline Parameters](/docs/instance-pipeline-parameters.md) — Full parameter reference
- [EnvGene Pipelines](/docs/envgene-pipelines.md) — Pipeline flow and job descriptions
- [Blue-Green Deployment](/docs/features/blue-green-deployment.md) — BG-related parameters
- [SD Processing](/docs/use-cases/sd-processing.md) — Solution Descriptor use cases
