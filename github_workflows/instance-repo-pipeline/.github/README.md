# EnvGene GitHub workflow

<div align="center">

User Guide

[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-workflow_dispatch-2088FF?style=flat-square&logo=github-actions&logoColor=white)](https://docs.github.com/en/actions)
[![Manual Trigger](https://img.shields.io/badge/trigger-manual-orange?style=flat-square)](#how-to-trigger-the-workflow)

</div>

- [EnvGene GitHub workflow](#envgene-github-workflow)
  - [Overview](#overview)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Step 1: Copy the pipeline](#step-1-copy-the-pipeline)
    - [Step 2: Configure required secrets](#step-2-configure-required-secrets)
    - [Step 3: Optional - Repository variables](#step-3-optional---repository-variables)
    - [Step 4: Optional - Customize configuration](#step-4-optional---customize-configuration)
    - [Verifying the setup](#verifying-the-setup)
  - [Quick start](#quick-start)
  - [Workflow structure](#workflow-structure)
    - [Job: `env-prepare`](#job-env-prepare)
    - [Job: `sync`](#job-sync)
    - [Orchestrator steps](#orchestrator-steps)
  - [Workflow dispatch inputs](#workflow-dispatch-inputs)
  - [GH_ADDITIONAL_PARAMS](#gh_additional_params)
    - [Format](#format)
    - [Examples](#examples)
    - [JSON values](#json-values)
    - [When to use pipeline_vars.env instead](#when-to-use-pipeline_varsenv-instead)
  - [Adding new parameters](#adding-new-parameters)
  - [Extending the workflow](#extending-the-workflow)
  - [Parameter priority](#parameter-priority)
  - [Repository variables](#repository-variables)
    - [Variables used by the workflow](#variables-used-by-the-workflow)
    - [CMDB import secret](#cmdb-import-secret)
    - [How to add repository variables](#how-to-add-repository-variables)
    - [When variables are empty or missing](#when-variables-are-empty-or-missing)
  - [Using different Docker registries](#using-different-docker-registries)
    - [GitHub Container Registry (GHCR)](#github-container-registry-ghcr)
    - [Google Artifact Registry (GAR)](#google-artifact-registry-gar)
  - [How to trigger the workflow](#how-to-trigger-the-workflow)
    - [Via GitHub Actions UI](#via-github-actions-ui)
    - [Via GitHub API](#via-github-api)
  - [Directory structure](#directory-structure)
  - [Use case scenarios](#use-case-scenarios)
  - [Further reading](#further-reading)

## Overview

The EnvGene workflow (`Envgene.yml`) is the GitHub Actions instance pipeline. It is triggered only by
`workflow_dispatch` (UI or API). There is no automatic trigger on push or pull request.

The workflow runs EnvGene inside the `qubership-envgene` image. One job (`env-prepare`) loads inputs, runs
`scripts/pipeline/orchestrator.py`, and uploads the generated package. A second job (`sync`) runs only for
`PIPELINE_TYPE=GITLAB_DEPLOY` when `OPERATION_TYPE` is not `CLEAN`.

Orchestrator capabilities include environment inventory generation, application and registry definition rendering,
Solution Descriptor (SD) processing, environment build, Effective Set generation, Blue-Green operations, credential
rotation, and git commit of generated artifacts.

## Installation

This section describes what you need to set up the EnvGene workflow in your instance repository.

### Prerequisites

- A GitHub repository (instance repository) with the [EnvGene instance structure](/docs/samples/instance-repository/)
- GitHub Actions enabled for the repository
- GitHub-hosted runners, or self-hosted runners that can run container jobs

### Step 1: Copy the pipeline

Copy the `.github` directory from this folder to the root of your instance repository:

```bash
cp -r github_workflows/instance-repo-pipeline/.github /path/to/your/instance-repo/
```

The copied tree includes the workflow, `process_variables.sh`, and the `load-env-files` action.

### Step 2: Configure required secrets

Go to **Settings** → **Secrets and variables** → **Actions** → **Secrets**, and add:

| Secret                    | Required          | Description                                                          |
|---------------------------|-------------------|----------------------------------------------------------------------|
| `SECRET_KEY`              | When using Fernet | Fernet key for credential encryption                                 |
| `ENVGENE_AGE_PUBLIC_KEY`  | When using SOPS   | Public key from the EnvGene AGE key pair (SOPS encryption)           |
| `ENVGENE_AGE_PRIVATE_KEY` | When using SOPS   | Private key from the EnvGene AGE key pair (SOPS decryption)          |
| `GH_ACCESS_TOKEN`         | Yes               | Token with `contents: write` so EnvGene can commit to the repository |
| `GCP_SA_KEY`              | When using GAR    | Full JSON key of a GCP service account for Artifact Registry access  |

> [!NOTE]
> Configure at least one encryption method (Fernet or SOPS) if the repository uses encrypted credentials. See
> [Credential encryption](/docs/how-to/credential-encryption.md).
>
> For CMDB import, add a per-cluster secret named `{CLUSTER_NAME}_{SECRET_POSTFIX}`. See
> [CMDB import secret](#cmdb-import-secret).

### Step 3: Optional - Repository variables

Configure variables in **Settings** → **Secrets and variables** → **Actions** → **Variables** to override defaults:

| Variable                   | Default             | Purpose                             |
|----------------------------|---------------------|-------------------------------------|
| `DOCKER_REGISTRY`          | `ghcr.io`           | Registry host for the EnvGene image |
| `DOCKER_NAMESPACE`         | `netcracker`        | Image namespace (owner)             |
| `ENVGENE_IMAGE`            | `qubership-envgene` | Image name                          |
| `ENVGENE_VERSION`          | `100.100.100`       | Image tag                           |
| `GH_RUNNER_TAG_NAME`       | `ubuntu-22.04`      | Runner label for workflow jobs      |
| `GH_RUNNER_SCRIPT_TIMEOUT` | `10`                | Job timeout in minutes              |

See [Repository variables](#repository-variables) for the full list used by `Envgene.yml`.

### Step 4: Optional - Customize configuration

`.github/pipeline_vars.env` is optional. Create it in the instance repository when you want standing overrides (for
example debugging or recurring values). The workflow loads it if the file exists. Missing file is not an error.

### Verifying the setup

1. Ensure the workflow file is at `.github/workflows/Envgene.yml`.
1. Ensure required secrets are set.
1. Trigger the workflow manually (see [Quick start](#quick-start)) with a valid `ENV_NAMES` value.

For initializing a new instance repository from scratch, see the
[Environment Instance Repository installation guide](/docs/how-to/envgene-maitanance.md).

## Quick start

> [!TIP]
> New to EnvGene? Start with [Installation](#installation), then come back here.

1. Ensure the pipeline is installed (see [Installation](#installation)).
1. Go to **Actions** → **EnvGene Execution** → **Run workflow**.
1. Fill in **ENV_NAMES** (for example `cluster-01/env-01`) and any other parameters.
1. Click **Run workflow**.

## Workflow structure

| Job           | When it runs                                                   | Purpose                                                                   |
|---------------|----------------------------------------------------------------|---------------------------------------------------------------------------|
| `env-prepare` | Always                                                         | Load inputs, run the EnvGene orchestrator, upload the environment package |
| `sync`        | `PIPELINE_TYPE == GITLAB_DEPLOY` and `OPERATION_TYPE != CLEAN` | Apply the generated Argo CD / DPG context with the syncer image           |

`env-prepare` is a single container job. Multiple environments in `ENV_NAMES` are processed inside that job (the
orchestrator fans out child processes). GitHub Actions does not start one matrix job per environment.

`PIPELINE_TYPE=GITLAB_DEPLOY` does not accept more than one value in `ENV_NAMES`.

### Job: `env-prepare`

Runs on `${{ vars.GH_RUNNER_TAG_NAME || 'ubuntu-22.04' }}` in the EnvGene image:

```text
${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${ENVGENE_IMAGE}:${ENVGENE_VERSION}
```

| Step                                                | Description                                                                                             |
|-----------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| Repository Checkout                                 | Checks out the instance repository (`fetch-depth: 1`, credentials not persisted)                        |
| Load environment variables from configuration files | Loads `.github/pipeline_vars.env` into `GITHUB_ENV` when the file exists                                |
| Process Input Parameters                            | `.github/scripts/process_variables.sh` exports dispatch inputs and `GH_ADDITIONAL_PARAMS`               |
| Set job outputs                                     | Publishes `PACKAGE_NAME` for the artifact and for `sync`                                                |
| EnvGene Execution                                   | Certs, env-name resolution, sparse checkout, orchestrator, then optional GITLAB_DEPLOY / CMDB steps     |
| Upload generated environment package                | Artifact with `environments/`, `configuration/`, `sboms/`, `templates/`, `tmp/`, `ARGO_DPG_CONTEXT.env` |

The **EnvGene Execution** step always runs:

1. `/module/scripts/utils/handle_certs.sh`
1. `python3 /module/scripts/pipeline/resolve_env_names.py` (writes `envgene-resolved.env`)
1. `python3 /module/scripts/utils/sparse_checkout.py`
1. `python3 /module/scripts/pipeline/orchestrator.py`

When `PIPELINE_TYPE` is `GITLAB_DEPLOY` and `OPERATION_TYPE` is `DEPLOY`, or `OPERATION_TYPE` is `BGD` with
`BGD_OPERATION=warmup`, the same step then generates Argo DPG structure and encrypts `ARGO_DPG_CONTEXT.env` when
`ENVGENE_AGE_PUBLIC_KEY` is set. For any `GITLAB_DEPLOY` run it then pushes the Effective Set with `es-pusher`.

When `PIPELINE_TYPE` is not `GITLAB_DEPLOY` and `CMDB_IMPORT` is `true`, it runs
`/module/scripts/cmdb_import/cmdb_import.sh`. That step reads CMDB credentials from a GitHub Actions
secret whose name is `{CLUSTER_NAME}_{SECRET_POSTFIX}`. See [CMDB import secret](#cmdb-import-secret).

### Job: `sync`

Needs `env-prepare`. Uses `${{ vars.SYNCER_IMAGE }}` (no fallback). Set `SYNCER_IMAGE` before you run
`PIPELINE_TYPE=GITLAB_DEPLOY` with an operation other than `CLEAN`.

| Step                         | Description                                                                      |
|------------------------------|----------------------------------------------------------------------------------|
| Download environment package | Downloads the `PACKAGE_NAME` artifact from `env-prepare`                         |
| Sync                         | Decrypts `ARGO_DPG_CONTEXT.env` when AGE keys are set, then runs `argo-app-life` |
| Upload sync artifacts        | Syncer logs and deploy report (1-day retention, missing files ignored)           |

### Orchestrator steps

These steps run inside the EnvGene image, in this order. A step is skipped when its condition is false. `git_commit`
always runs (it no-ops when there is nothing to stage).

| Step                           | Runs when                                                                         |
|--------------------------------|-----------------------------------------------------------------------------------|
| `get_passport`                 | `GET_PASSPORT` is true                                                            |
| `credential_rotation`          | `CRED_ROTATION_PAYLOAD` is set (cannot be combined with `GET_PASSPORT`)           |
| `change_bg_state`              | `PIPELINE_TYPE=GITLAB_DEPLOY` and `OPERATION_TYPE=BGD`                            |
| `warmup`                       | `PIPELINE_TYPE=GITLAB_DEPLOY` and `BGD_OPERATION=warmup`                          |
| `env_inventory_generation`     | `ENV_INVENTORY_CONTENT` is set, or a deprecated inventory init parameter is set   |
| `set_template_version`         | `ENV_TEMPLATE_VERSION` is set                                                     |
| `appregdef_render`             | `GITLAB_DEPLOY`, or `ENV_BUILDER`, or `SD_VERSION` / `SD_DATA`                    |
| `deploy_postfix_namespace_map` | `GITLAB_DEPLOY` and `OPERATION_TYPE=DEPLOY`                                       |
| `process_sd`                   | Legacy deploy with `SD_VERSION` or `SD_DATA` (not `GITLAB_DEPLOY`)                |
| `migrate_sd_to_deploy_plan`    | Legacy flow: incoming SD, or a committed `sd.yaml` without `deploy-plan.yml` yet  |
| `process_deployment_plan`      | `GITLAB_DEPLOY` and `OPERATION_TYPE` is `DEPLOY` or `CLEAN`                       |
| `env_build`                    | `ENV_BUILDER`, or `GITLAB_DEPLOY` with `DEPLOY` / `CLEAN`                         |
| `generate_effective_set`       | `GENERATE_EFFECTIVE_SET`, or `GITLAB_DEPLOY` with `DEPLOY` / `CLEAN` / BGD warmup |
| `git_commit`                   | Always                                                                            |

For full parameter semantics, see [Instance pipeline parameters](/docs/instance-pipeline-parameters.md). For the
shared pipeline story, see [EnvGene pipelines](/docs/envgene-pipelines.md).

## Workflow dispatch inputs

These are the inputs declared on `Envgene.yml`. Empty descriptions in the workflow file are intentional. Meanings live
in [Instance pipeline parameters](/docs/instance-pipeline-parameters.md).

| Input                    | Required | Default | Type    | Description                                                    |
|--------------------------|----------|---------|---------|----------------------------------------------------------------|
| `ENV_NAMES`              | Yes      | -       | string  | Environment(s) as `cluster/env`. Comma-separated list OK       |
| `CLUSTER_NAME`           | No       | `""`    | string  | Cluster part of a single environment (with `ENVIRONMENT_NAME`) |
| `ENVIRONMENT_NAME`       | No       | `""`    | string  | Environment part of a single environment                       |
| `PIPELINE_TYPE`          | No       | `""`    | string  | `LEGACY` (default in EnvGene) or `GITLAB_DEPLOY`               |
| `OPERATION_TYPE`         | No       | `""`    | string  | `DEPLOY`, `CLEAN`, or `BGD`                                    |
| `BGD_OPERATION`          | No       | `""`    | string  | Blue-Green operation when `OPERATION_TYPE=BGD`                 |
| `BG_NS_TARGET`           | No       | `""`    | string  | Blue-Green namespace target                                    |
| `NAMESPACE_NAMES`        | No       | `""`    | string  | Namespaces for CLEAN / filters                                 |
| `DEPLOYMENT_TICKET_ID`   | No       | `""`    | string  | Ticket ID used as a commit message prefix                      |
| `ENV_TEMPLATE_VERSION`   | No       | `""`    | string  | Template version to apply                                      |
| `ENV_INVENTORY_CONTENT`  | No       | `""`    | string  | Inventory generation payload                                   |
| `CUSTOM_PARAMS`          | No       | `""`    | string  | Extra parameters for Effective Set generation                  |
| `DEPLOYMENT_SESSION_ID`  | No       | `""`    | string  | Session id appended to the commit message                      |
| `APPLICATION_VERSIONS`   | No       | `""`    | string  | Application versions for the deploy plan                       |
| `ENV_BUILDER`            | No       | `true`  | boolean | Enable environment build                                       |
| `GENERATE_EFFECTIVE_SET` | No       | `false` | boolean | Enable Effective Set generation on the legacy path             |
| `GET_PASSPORT`           | No       | `false` | boolean | Enable Cloud Passport discovery                                |
| `CMDB_IMPORT`            | No       | `false` | boolean | Enable CMDB export (non-`GITLAB_DEPLOY` only)                  |
| `GH_ADDITIONAL_PARAMS`   | No       | `""`    | string  | Comma-separated `KEY=VALUE` pairs for other parameters         |

If both `CLUSTER_NAME` and `ENVIRONMENT_NAME` are set, they take precedence over `ENV_NAMES` and select a single
environment.

## GH_ADDITIONAL_PARAMS

`GH_ADDITIONAL_PARAMS` carries instance-pipeline parameters that are not dedicated workflow inputs. `process_variables.sh`
parses it and writes each pair to `GITHUB_ENV`.

Use it for parameters such as:

- `SD_VERSION`, `SD_DATA`, `SD_REPO_MERGE_MODE` - Solution Descriptor (legacy path)
- `CRED_ROTATION_PAYLOAD`, `CRED_ROTATION_FORCE` - credential rotation
- `BG_STATE` - Blue-Green state JSON for `OPERATION_TYPE=BGD`
- `EFFECTIVE_SET_CONFIG` - Effective Set options
- any other parameter listed in [Instance pipeline parameters](/docs/instance-pipeline-parameters.md)

Do not put a dedicated workflow input into `GH_ADDITIONAL_PARAMS` unless you intend to override that input (see
[Parameter priority](#parameter-priority)).

### Format

`KEY1=VALUE1,KEY2=VALUE2,KEY3=VALUE3`

- Pairs are separated by commas.
- Each pair is `KEY=VALUE` (no spaces around `=`).
- Keys and values are trimmed of leading and trailing whitespace.
- Empty pairs are ignored.

### Examples

**Simple values:**

```text
SD_VERSION=my-app:v1.0,SD_REPO_MERGE_MODE=replace
```

**With JSON (escape double quotes):**

```text
EFFECTIVE_SET_CONFIG={\"version\": \"v2.0\", \"app_chart_validation\": \"false\"}
```

**Credential rotation:**

```text
CRED_ROTATION_PAYLOAD={\"credentials\":[{\"name\":\"db-password\",\"newValue\":\"<new-secret>\"}]}
```

### JSON values

1. Escape internal double quotes: `\"` instead of `"`.
1. Commas inside JSON are also pair separators. Complex JSON can split incorrectly.

> [!CAUTION]
> For JSON with many commas, put the parameter in `.github/pipeline_vars.env` or pass it through the GitHub API with
> proper escaping.

### When to use pipeline_vars.env instead

Use `.github/pipeline_vars.env` when:

- The value is long JSON with many commas.
- You want the same values on many runs (for example debugging).
- You want the value out of the workflow UI.

Variables in `pipeline_vars.env` must be `KEY=VALUE` lines. Do not wrap them in `GH_ADDITIONAL_PARAMS`.

## Adding new parameters

`process_variables.sh` exports every `workflow_dispatch` input automatically. You do not add `echo` lines for new
inputs.

**Dedicated input.** Add the field under `on.workflow_dispatch.inputs` in `Envgene.yml`. The next run exports it.

**`GH_ADDITIONAL_PARAMS`.** Pass `MY_NEW_PARAM=value` when the parameter already exists in
[Instance pipeline parameters](/docs/instance-pipeline-parameters.md) but has no dedicated input.

**`pipeline_vars.env`.** Add `MY_NEW_PARAM=my_value` in `.github/pipeline_vars.env`.

EnvGene processes only the parameters listed in [Instance pipeline parameters](/docs/instance-pipeline-parameters.md).
Unknown names are written to `GITHUB_ENV` and then ignored by the orchestrator.

## Extending the workflow

YAML jobs in the base workflow are `env-prepare` and `sync`. Extra GitHub Actions jobs or steps are not added by
setting a parameter. They are added by patching `Envgene.yml` with the instance-repo-pipeline image.

See [Extend the GitHub instance pipeline](/docs/how-to/extend-github-instance-pipeline.md).

## Parameter priority

For a name written to `GITHUB_ENV` (orchestrator parameters), later writes win:

1. `GH_ADDITIONAL_PARAMS`
1. Dedicated workflow inputs
1. `.github/pipeline_vars.env`

For values interpolated in `Envgene.yml` itself (image, runner label, timeout), GitHub `vars` apply, then the
fallback in the workflow file. Organization variables apply when the repository variable is unset.

## Repository variables

Repository variables are configured in **Settings → Secrets and variables → Actions → Variables**. The workflow reads
them as `vars.VARIABLE_NAME`.

### Variables used by the workflow

| Variable                         | Purpose                                            | Fallback when empty                |
|----------------------------------|----------------------------------------------------|------------------------------------|
| `DOCKER_REGISTRY`                | Registry host for the EnvGene image                | `ghcr.io`                          |
| `DOCKER_NAMESPACE`               | Image namespace                                    | `netcracker`                       |
| `ENVGENE_IMAGE`                  | Image name                                         | `qubership-envgene`                |
| `ENVGENE_VERSION`                | Image tag                                          | `100.100.100`                      |
| `DOCKER_CLOUD_REGISTRY_PROVIDER` | `GCP` selects GAR credentials on the container job | (empty, GHCR auth)                 |
| `GH_RUNNER_TAG_NAME`             | Runner label                                       | `ubuntu-22.04`                     |
| `GH_RUNNER_SCRIPT_TIMEOUT`       | Job timeout in minutes                             | `10`                               |
| `GH_USER_EMAIL`                  | Git commit author email                            | `<actor>@users.noreply.github.com` |
| `GH_USER_NAME`                   | Git commit author name                             | `github.actor`                     |
| `SECRET_POSTFIX`                 | Suffix for the per-cluster CMDB import secret      | `secret_postfix`                   |
| `SYNCER_IMAGE`                   | Full image reference for the `sync` job            | none (required for sync)           |

For secrets and variables used by EnvGene at runtime (encryption keys, log level, and so on), see
[EnvGene repository variables](/docs/envgene-repository-variables.md).

### CMDB import secret

CMDB import authenticates with a GitHub Actions **secret**, not with `SECRET_POSTFIX` itself.
`SECRET_POSTFIX` is only the shared suffix. The secret name is the cluster name, an underscore, then that suffix:

```text
SECRET_NAME = {CLUSTER_NAME}_{SECRET_POSTFIX}
```

`CLUSTER_NAME` is the cluster part of `ENV_NAMES` (the text before `/`). `SECRET_POSTFIX` comes from
`vars.SECRET_POSTFIX` and defaults to `secret_postfix`.

With `ENV_NAMES=prod-cluster/prod-01` and the default postfix, the secret name is
`prod-cluster_secret_postfix`.

To use CMDB import:

1. Set `SECRET_POSTFIX` once in repository variables, or keep the default.
1. Create one Actions secret per cluster, named `{CLUSTER_NAME}_{SECRET_POSTFIX}`.
1. Run the workflow with `CMDB_IMPORT=true`.

Different clusters can share one postfix and still have separate secrets, because the cluster name is the
first part of `SECRET_NAME`.

### How to add repository variables

1. Open the repository on GitHub.
1. Open **Settings** → **Secrets and variables** → **Actions**.
1. Open the **Variables** tab.
1. Click **New repository variable**.
1. Enter the name (for example `ENVGENE_VERSION`) and value.
1. Click **Add variable**.

### When variables are empty or missing

```yaml
runs-on: ${{ vars.GH_RUNNER_TAG_NAME || 'ubuntu-22.04' }}
image: ${{ vars.DOCKER_REGISTRY || 'ghcr.io' }}/${{ vars.DOCKER_NAMESPACE || 'netcracker' }}/${{ vars.ENVGENE_IMAGE || 'qubership-envgene' }}:${{ vars.ENVGENE_VERSION || '100.100.100' }}
```

You do not need to define the variables that have fallbacks. `SYNCER_IMAGE` has no fallback.

## Using different Docker registries

`env-prepare` pulls one EnvGene image. Image path:

```text
${{ vars.DOCKER_REGISTRY || 'ghcr.io' }}/${{ vars.DOCKER_NAMESPACE || 'netcracker' }}/${{ vars.ENVGENE_IMAGE || 'qubership-envgene' }}:${{ vars.ENVGENE_VERSION || '100.100.100' }}
```

Container registry credentials:

- Default (GHCR): `github.actor` / `github.token`
- `DOCKER_CLOUD_REGISTRY_PROVIDER=GCP`: `_json_key` / `secrets.GCP_SA_KEY`

There is no separate `docker login` step. Authentication is the `container.credentials` block on the job.

### GitHub Container Registry (GHCR)

GHCR is the default. No extra variables are required for `ghcr.io/netcracker/qubership-envgene`.

| Where to configure       | Parameter         | Value     |
|--------------------------|-------------------|-----------|
| **Settings → Variables** | `DOCKER_REGISTRY` | `ghcr.io` |

Set `DOCKER_NAMESPACE` if the image is not under `netcracker`. Set `ENVGENE_VERSION` to the tag you want to run.

### Google Artifact Registry (GAR)

| Where to configure       | Parameter                        | Value                                        |
|--------------------------|----------------------------------|----------------------------------------------|
| **Settings → Variables** | `DOCKER_REGISTRY`                | `REGION-docker.pkg.dev/PROJECT_ID/REPO_NAME` |
| **Settings → Variables** | `DOCKER_NAMESPACE`               | Image namespace in that repository           |
| **Settings → Variables** | `DOCKER_CLOUD_REGISTRY_PROVIDER` | `GCP`                                        |
| **Settings → Secrets**   | `GCP_SA_KEY`                     | Full JSON key of the GCP service account     |

**Example `DOCKER_REGISTRY` for GAR:**

```text
europe-west1-docker.pkg.dev/my-gcp-project/envgene-images
```

The service account needs at least `Artifact Registry Reader` on the repository.

For a longer GAR key walkthrough, see
[Using different Docker registries](/docs/how-to/docker-registry-configuration.md). That how-to still describes an older
image-name layout (`DOCKER_IMAGE_NAME_*`). Trust the formula in `Envgene.yml` for the current path.

## How to trigger the workflow

### Via GitHub Actions UI

1. Open your repository on GitHub.
1. Go to **Actions**.
1. Select **EnvGene Execution**.
1. Click **Run workflow**.
1. Choose the branch, fill in parameters, and run.

### Via GitHub API

<details>
<summary>Click to expand API example</summary>

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

</details>

## Directory structure

```text
github_workflows/instance-repo-pipeline/
├── Dockerfile                   # qubership-instance-repo-pipeline image (patch/extend tooling)
├── extend_logic/scripts/        # apply_envgene_patch.py, git_commit.py (used inside that image)
└── .github/
    ├── README.md                # This guide
    ├── actions/
    │   └── load-env-files/      # Loads .env files into GITHUB_ENV
    ├── scripts/
    │   └── process_variables.sh # Exports workflow inputs and GH_ADDITIONAL_PARAMS
    └── workflows/
        └── Envgene.yml          # Instance pipeline workflow
```

`.github/pipeline_vars.env` is not shipped. Create it in the instance repository when you need it.

## Use case scenarios

### Scenario 1: Environment build and Effective Set

**Goal:** Build the environment and generate the Effective Set.

| Parameter                | Value                  |
|--------------------------|------------------------|
| `ENV_NAMES`              | `prod-cluster/prod-01` |
| `ENV_BUILDER`            | `true`                 |
| `GENERATE_EFFECTIVE_SET` | `true`                 |
| `DEPLOYMENT_TICKET_ID`   | `QBSHP-1234`           |

**Orchestrator steps that run:** `appregdef_render` → `env_build` → `generate_effective_set` → `git_commit` (plus any
other step whose condition is also true).

**Result:** Environment Instance is generated, Effective Set is written under the environment tree, changes are
committed.

### Scenario 2: Environment build only

**Goal:** Regenerate the Environment Instance without Effective Set on the legacy path.

| Parameter     | Value                |
|---------------|----------------------|
| `ENV_NAMES`   | `dev-cluster/dev-01` |
| `ENV_BUILDER` | `true`               |

**Result:** `generate_effective_set` is skipped unless `PIPELINE_TYPE=GITLAB_DEPLOY` forces it.

### Scenario 3: Update template version and rebuild

| Parameter              | Value                  |
|------------------------|------------------------|
| `ENV_NAMES`            | `prod-cluster/prod-01` |
| `ENV_BUILDER`          | `true`                 |
| `ENV_TEMPLATE_VERSION` | `env-template:v2.1.0`  |

**Orchestrator steps that run:** `set_template_version` → `appregdef_render` → `env_build` → `git_commit`.

### Scenario 4: Blue-Green operation (`GITLAB_DEPLOY`)

| Parameter              | Value                  |
|------------------------|------------------------|
| `ENV_NAMES`            | `prod-cluster/prod-01` |
| `PIPELINE_TYPE`        | `GITLAB_DEPLOY`        |
| `OPERATION_TYPE`       | `BGD`                  |
| `BGD_OPERATION`        | `warmup`               |
| `GH_ADDITIONAL_PARAMS` | `BG_STATE={...}`       |

Set `SYNCER_IMAGE`. After `env-prepare`, `sync` runs (`OPERATION_TYPE` is not `CLEAN`).

See [Blue-Green deployment](/docs/features/blue-green-deployment.md) and
[Instance pipeline parameters](/docs/instance-pipeline-parameters.md) for `BGD_OPERATION` and `BG_STATE`.

### Scenario 5: Credential rotation

| Parameter              | Value                         |
|------------------------|-------------------------------|
| `ENV_NAMES`            | `prod-cluster/prod-01`        |
| `GH_ADDITIONAL_PARAMS` | `CRED_ROTATION_PAYLOAD={...}` |

**Orchestrator steps that run:** `credential_rotation` → `git_commit`.

Do not set `GET_PASSPORT` in the same run. See [Credential rotation](/docs/features/cred-rotation.md).

### Scenario 6: Process Solution Descriptor from artifact (legacy)

| Parameter              | Value                                                      |
|------------------------|------------------------------------------------------------|
| `ENV_NAMES`            | `prod-cluster/prod-01`                                     |
| `GH_ADDITIONAL_PARAMS` | `SD_VERSION=my-solution:v1.2.3,SD_REPO_MERGE_MODE=replace` |

`process_sd` runs only when `PIPELINE_TYPE` is not `GITLAB_DEPLOY`. See
[SD processing](/docs/use-cases/sd-processing.md).

### Scenario 7: Generate new environment inventory

| Parameter               | Value                 |
|-------------------------|-----------------------|
| `ENV_NAMES`             | `new-cluster/new-env` |
| `ENV_INVENTORY_CONTENT` | `{...}`               |

**Orchestrator steps that run:** `env_inventory_generation` → `git_commit`.

See [Environment inventory generation](/docs/features/env-inventory-generation.md).

### Scenario 8: Multiple environments in one run

| Parameter     | Value                                     |
|---------------|-------------------------------------------|
| `ENV_NAMES`   | `cluster-01/env-01,cluster-01/env-02,...` |
| `ENV_BUILDER` | `true`                                    |

**Result:** One `env-prepare` job. The orchestrator fans out one child process per environment. This is not a GitHub
matrix. `PIPELINE_TYPE=GITLAB_DEPLOY` rejects multiple `ENV_NAMES` values.

## Further reading

| Document                                                                               | Description                    |
|----------------------------------------------------------------------------------------|--------------------------------|
| [Instance pipeline parameters](/docs/instance-pipeline-parameters.md)                  | Full parameter reference       |
| [EnvGene pipelines](/docs/envgene-pipelines.md)                                        | Pipeline flow and descriptions |
| [Using different Docker registries](/docs/how-to/docker-registry-configuration.md)     | GHCR and GAR configuration     |
| [Extend the GitHub instance pipeline](/docs/how-to/extend-github-instance-pipeline.md) | Patch `Envgene.yml`            |
| [Blue-Green deployment](/docs/features/blue-green-deployment.md)                       | BG-related parameters          |
| [SD processing](/docs/use-cases/sd-processing.md)                                      | Solution Descriptor use cases  |
