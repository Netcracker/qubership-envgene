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
  - [Parameter priority](#parameter-priority)
  - [Repository variables](#repository-variables)
    - [Variables used by the workflow](#variables-used-by-the-workflow)
    - [CMDB import requirements](#cmdb-import-requirements)
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
`scripts/pipeline/orchestrator.py`, and uploads the generated package. A second job (`sync`) runs only when
the dispatch inputs specify `PIPELINE_TYPE=GITLAB_DEPLOY` and an `OPERATION_TYPE` other than `CLEAN`, after
`env-prepare` succeeds.

Orchestrator capabilities include environment inventory generation, application and registry definition rendering,
Solution Descriptor (SD) processing, environment build, Effective Set generation, Blue-Green operations, credential
rotation, and Git commit of generated artifacts.

The files in this directory are copied into the instance repository. The EnvGene release workflow updates the
`ENVGENE_VERSION` fallback in `Envgene.yml`. `SYNCER_VERSION` is managed separately. Copy updated workflow files into
your instance repository when upgrading. An explicit repository variable overrides the corresponding fallback.

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

The copied tree includes the workflow, `process_variables.sh`, the `load-env-files` action, and an empty
`pipeline_vars.env` file.

### Step 2: Configure required secrets

Go to **Settings** → **Secrets and variables** → **Actions** → **Secrets**, and add:

| Secret                    | Required                              | Description                                                          |
|---------------------------|---------------------------------------|----------------------------------------------------------------------|
| `SECRET_KEY`              | When using Fernet                     | Fernet key for credential encryption                                 |
| `ENVGENE_AGE_PUBLIC_KEY`  | When using SOPS or deploy/warmup sync | Public key from the EnvGene AGE key pair (SOPS encryption)           |
| `ENVGENE_AGE_PRIVATE_KEY` | When using SOPS or deploy/warmup sync | Private key from the EnvGene AGE key pair (SOPS decryption)          |
| `GH_ACCESS_TOKEN`         | Yes                                   | Token with `contents: write` so EnvGene can commit to the repository |
| `GCP_SA_KEY`              | When using GAR                        | Full JSON key of a GCP service account for Artifact Registry access  |

> [!NOTE]
> Configure at least one encryption method (Fernet or SOPS) if the repository uses encrypted credentials. See
> [Credential encryption](/docs/how-to/credential-encryption.md).
>
> For `GITLAB_DEPLOY` with `DEPLOY` or BGD `warmup`, configure both AGE secrets. The workflow attempts to encrypt
> `ARGO_DPG_CONTEXT.env` even if the public-key secret is empty.

CMDB import needs an integration-specific image and credential mapping. See
[CMDB import requirements](#cmdb-import-requirements).

### Step 3: Optional - Repository variables

Configure variables in **Settings** → **Secrets and variables** → **Actions** → **Variables** to override defaults:

| Variable                   | Default                      | Purpose                             |
|----------------------------|------------------------------|-------------------------------------|
| `DOCKER_REGISTRY`          | `ghcr.io`                    | Registry host for the EnvGene image |
| `DOCKER_NAMESPACE`         | `netcracker`                 | Image namespace (owner)             |
| `ENVGENE_IMAGE`            | `qubership-envgene`          | Image name                          |
| `ENVGENE_VERSION`          | Release tag in `Envgene.yml` | Image tag                           |
| `GH_RUNNER_TAG_NAME`       | `ubuntu-22.04`               | Runner label for workflow jobs      |
| `GH_RUNNER_SCRIPT_TIMEOUT` | `10`                         | Job timeout in minutes              |

See [Repository variables](#repository-variables) for the full list used by `Envgene.yml`.

### Step 4: Optional - Customize configuration

The shipped `.github/pipeline_vars.env` is empty. Add nonsecret runtime parameters there when you need recurring
values, such as `ENVGENE_LOG_LEVEL=DEBUG`. The workflow loads the file if it exists and warns if it is missing.
Dedicated inputs, including empty strings and default booleans, take precedence over this file. See
[Parameter priority](#parameter-priority).

### Verifying the setup

1. Ensure the workflow file is at `.github/workflows/Envgene.yml`.
1. Ensure required secrets are set.
1. Trigger the workflow manually (see [Quick start](#quick-start)) with valid `ENV_NAMES` and `OPERATION_TYPE` values.

For initializing a new instance repository from scratch, see the
[Environment Instance Repository installation guide](/docs/how-to/envgene-maitanance.md).

## Quick start

> [!TIP]
> New to EnvGene? Start with [Installation](#installation), then come back here.

1. Ensure the pipeline is installed (see [Installation](#installation)).
1. Go to **Actions** → **EnvGene Execution** → **Run workflow**.
1. Fill in **ENV_NAMES** (for example `cluster-01/env-01`) and set **OPERATION_TYPE** to `DEPLOY` for a normal build.
1. Keep **ENV_BUILDER** enabled. Enable **GENERATE_EFFECTIVE_SET** if you also need the Effective Set.
1. Click **Run workflow**.

## Workflow structure

| Job           | When it runs                                                   | Purpose                                                                   |
|---------------|----------------------------------------------------------------|---------------------------------------------------------------------------|
| `env-prepare` | Always                                                         | Load inputs, run the EnvGene orchestrator, upload the environment package |
| `sync`        | `PIPELINE_TYPE == GITLAB_DEPLOY` and `OPERATION_TYPE != CLEAN` | Apply the generated Argo CD / DPG context with the syncer image           |

`env-prepare` is a single container job. Multiple environments in `ENV_NAMES` are processed inside that job (the
orchestrator fans out child processes). GitHub Actions does not start one matrix job per environment.

`PIPELINE_TYPE=GITLAB_DEPLOY` supports only one resolved environment.

Concurrency groups use the branch ref and the original `ENV_NAMES` input. A new run does not cancel an active run in
the same group (`cancel-in-progress: false`). Different input strings can select overlapping environments without
sharing a group.

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

The **EnvGene Execution** step always runs `python3 /module/scripts/pipeline/orchestrator.py`. Before any pipeline
step, the orchestrator resolves the environment names, runs the sparse checkout, and installs the CA certificates
in one process. When it installs certificates, it writes `REQUESTS_CA_BUNDLE` to `envgene-vars.env` for the
commands that follow.

When `PIPELINE_TYPE` is `GITLAB_DEPLOY` and `OPERATION_TYPE` is `DEPLOY`, or `OPERATION_TYPE` is `BGD` with
`BGD_OPERATION=warmup`, the same step then generates Argo DPG structure and encrypts `ARGO_DPG_CONTEXT.env` with SOPS.
Both AGE secrets must be configured for this path. For every `GITLAB_DEPLOY` run it then pushes the Effective Set with
`es-pusher`, using overwrite mode only for `CLEAN`.

The selected image must provide the EnvGene scripts under `/module/scripts`, Argo DPG under `/python/argocd-dpg`, and
`es-pusher` under `/python/es-pusher` for the operations that use them.

When `PIPELINE_TYPE` is not `GITLAB_DEPLOY` and `CMDB_IMPORT` is `true`, it runs
`/module/scripts/cmdb_import/cmdb_import.sh`. See [CMDB import requirements](#cmdb-import-requirements).

### Job: `sync`

Needs a successful `env-prepare`. Its image is assembled from repository variables and their fallbacks:

```text
${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${SYNCER_IMAGE}:${SYNCER_VERSION}
```

`SYNCER_IMAGE` is an image name, such as `qubership-envgene`, rather than a full registry reference. It defaults to
`qubership-envgene`, and `SYNCER_VERSION` defaults to `2.6.6`. The image must provide `update-certificate`, SOPS,
`/usr/local/bin/uv`, and `argo-app-life`.

| Step                         | Description                                                                                    |
|------------------------------|------------------------------------------------------------------------------------------------|
| Download environment package | Downloads the `PACKAGE_NAME` artifact from `env-prepare`                                       |
| Sync                         | Decrypts `ARGO_DPG_CONTEXT.env` when the AGE public key is nonempty, then runs `argo-app-life` |
| Upload sync artifacts        | Syncer logs and deploy report (1-day retention, missing files ignored)                         |

The job condition reads the original `PIPELINE_TYPE` and `OPERATION_TYPE` dispatch inputs. Set these directly in the
form or API request. Runtime overrides do not change whether this job starts.

The workflow creates `ARGO_DPG_CONTEXT.env` only for `DEPLOY` and BGD `warmup`. Other non-`CLEAN` operations still match
the `sync` condition, so they need a compatible context from another source to complete synchronization.

### Orchestrator steps

These steps run inside the EnvGene image, in this order. A step is skipped when its condition is false. If earlier
steps succeed, `git_commit` runs and does nothing when there are no changes to stage.

| Step                           | Runs when                                                                              |
|--------------------------------|----------------------------------------------------------------------------------------|
| `get_passport`                 | `GET_PASSPORT` is true                                                                 |
| `credential_rotation`          | `CRED_ROTATION_PAYLOAD` is set (cannot be combined with `GET_PASSPORT`)                |
| `change_bg_state`              | `PIPELINE_TYPE=GITLAB_DEPLOY` and `OPERATION_TYPE=BGD`                                 |
| `warmup`                       | `GITLAB_DEPLOY`, `OPERATION_TYPE=BGD`, and `BGD_OPERATION=warmup`                      |
| `env_inventory_generation`     | `ENV_INVENTORY_CONTENT` is set, or a deprecated inventory init parameter is set        |
| `set_template_version`         | `ENV_TEMPLATE_VERSION` is set                                                          |
| `appregdef_render`             | `GITLAB_DEPLOY`, or `ENV_BUILDER`, or `SD_VERSION` / `SD_DATA`                         |
| `regdefv2_adapter`             | `GITLAB_DEPLOY` deploy, clean, or BGD warmup. Legacy: see below                        |
| `deploy_postfix_namespace_map` | `GITLAB_DEPLOY` and `OPERATION_TYPE=DEPLOY`                                            |
| `process_sd`                   | Legacy deploy with `SD_VERSION` or `SD_DATA` (not `GITLAB_DEPLOY`)                     |
| `migrate_sd_to_deploy_plan`    | Legacy: incoming SD, or committed SD requiring migration (see below)                   |
| `process_deployment_plan`      | `GITLAB_DEPLOY` and `OPERATION_TYPE` is `DEPLOY` or `CLEAN`                            |
| `env_build`                    | `ENV_BUILDER`, or `GITLAB_DEPLOY` with `DEPLOY` / `CLEAN`                              |
| `generate_effective_set`       | `GENERATE_EFFECTIVE_SET`, or `GITLAB_DEPLOY` with `DEPLOY` / `CLEAN` / BGD warmup      |
| `git_commit`                   | Always                                                                                 |
| `CMDB_import`                  | Legacy: a parameter plugin enables `CMDB_IMPORT`. Requires the `nc_cmdb_import` plugin |

On the legacy path, `regdefv2_adapter` requires `ENV_BUILDER` and either incoming SD or `GENERATE_EFFECTIVE_SET`.
Migration of committed SD requires `use_committed_sd` to be enabled, an existing `sd.yaml`, and no `deploy-plan.yml`.

The standard parameter loader does not load `CMDB_IMPORT` into the orchestrator context. The shell invocation after
the orchestrator is separate. See [CMDB import requirements](#cmdb-import-requirements).

For full parameter semantics, see [Instance pipeline parameters](/docs/instance-pipeline-parameters.md). For the
shared pipeline story, see [EnvGene pipelines](/docs/envgene-pipelines.md).

## Workflow dispatch inputs

These are the inputs declared in `Envgene.yml`. Their descriptions in the workflow file are empty. Meanings live in
[Instance pipeline parameters](/docs/instance-pipeline-parameters.md).

| Input                    | Required | Default | Type    | Description                                                         |
|--------------------------|----------|---------|---------|---------------------------------------------------------------------|
| `ENV_NAMES`              | Yes      | -       | string  | Environment(s) as `cluster/env`. Comma-separated list OK            |
| `CLUSTER_NAME`           | No       | `""`    | string  | Cluster part of a single environment (with `ENVIRONMENT_NAME`)      |
| `ENVIRONMENT_NAME`       | No       | `""`    | string  | Environment part of a single environment                            |
| `PIPELINE_TYPE`          | No       | `""`    | string  | Leave empty for the legacy path. Set `GITLAB_DEPLOY` for deployment |
| `OPERATION_TYPE`         | No       | `""`    | string  | `DEPLOY`, `CLEAN`, or `BGD`                                         |
| `BGD_OPERATION`          | No       | `""`    | string  | Blue-Green operation when `OPERATION_TYPE=BGD`                      |
| `BG_NS_TARGET`           | No       | `""`    | string  | Blue-Green namespace target                                         |
| `NAMESPACE_NAMES`        | No       | `""`    | string  | Namespaces for CLEAN / filters                                      |
| `DEPLOYMENT_TICKET_ID`   | No       | `""`    | string  | Ticket ID used as a commit message prefix                           |
| `ENV_TEMPLATE_VERSION`   | No       | `""`    | string  | Template version to apply                                           |
| `ENV_INVENTORY_CONTENT`  | No       | `""`    | string  | Inventory generation payload                                        |
| `CUSTOM_PARAMS`          | No       | `""`    | string  | Extra parameters for Effective Set generation                       |
| `DEPLOYMENT_SESSION_ID`  | No       | `""`    | string  | Session ID appended to the commit message                           |
| `APPLICATION_VERSIONS`   | No       | `""`    | string  | Application versions for the deploy plan                            |
| `ENV_BUILDER`            | No       | `true`  | boolean | Enable environment build                                            |
| `GENERATE_EFFECTIVE_SET` | No       | `false` | boolean | Enable Effective Set generation on the legacy path                  |
| `GET_PASSPORT`           | No       | `false` | boolean | Enable Cloud Passport discovery                                     |
| `CMDB_IMPORT`            | No       | `false` | boolean | Enable CMDB export (non-`GITLAB_DEPLOY` only)                       |
| `GH_ADDITIONAL_PARAMS`   | No       | `""`    | string  | Comma-separated `KEY=VALUE` pairs for other parameters              |

If both `CLUSTER_NAME` and `ENVIRONMENT_NAME` are set, they take precedence over `ENV_NAMES` and select a single
environment. Provide both or neither. `ENV_NAMES` must still be nonempty because `process_variables.sh` validates it
before resolving the pair.

Leave `PIPELINE_TYPE` empty for the legacy path. Do not enter `LEGACY`, which the environment-name resolver rejects.

The orchestrator interprets an empty `OPERATION_TYPE` as `DEPLOY`. For `GITLAB_DEPLOY`, set `OPERATION_TYPE` explicitly:
the workflow shell checks the raw value and only generates deployment context for the literal `DEPLOY` or BGD
`warmup` combination. Use the uppercase operation values shown in the table.

Use single-line input values. For multiple environments, use a comma-separated list without spaces, such as
`cluster-01/env-01,cluster-01/env-02`. JSON inputs such as `ENV_INVENTORY_CONTENT`, `CUSTOM_PARAMS`, and
`APPLICATION_VERSIONS` must also be on one line. The exporter does not encode multiline values for `GITHUB_ENV`.

## GH_ADDITIONAL_PARAMS

`GH_ADDITIONAL_PARAMS` carries instance-pipeline parameters that are not dedicated workflow inputs. `process_variables.sh`
parses it and writes each pair to `GITHUB_ENV`.

Use it for simple values such as `SD_VERSION`, `SD_REPO_MERGE_MODE`, `CRED_ROTATION_FORCE`, or `ENVGENE_LOG_LEVEL`.
Supported runtime parameters are listed in [Instance pipeline parameters](/docs/instance-pipeline-parameters.md).
See [Parameter priority](#parameter-priority) before overriding a dedicated input. Set `PIPELINE_TYPE` and
`OPERATION_TYPE` directly because the `sync` condition uses the original inputs.

### Format

`KEY1=VALUE1,KEY2=VALUE2,KEY3=VALUE3`

- Every comma separates pairs, including commas inside quoted values or JSON.
- Each pair is `KEY=VALUE`. Use no spaces around `=`.
- The parser uses `xargs` to trim each pair. This also consumes quotes and backslashes and collapses whitespace.
- Empty pairs, empty keys, and empty values are not exported as overrides.
- The script logs the additional-parameter string and parsed values. Keep secrets out of this field.

### Examples

**Simple values:**

```text
SD_VERSION=my-app:v1.0,SD_REPO_MERGE_MODE=replace
```

**Debug logging:**

```text
ENVGENE_LOG_LEVEL=DEBUG
```

### JSON values

Use a dedicated workflow input for JSON when one exists. For other nonsecret JSON parameters, use
`.github/pipeline_vars.env`. For secret payloads, add an explicit secret-backed environment mapping to your copy of
`Envgene.yml` and store the value as single-line JSON in an Actions secret.

`GH_ADDITIONAL_PARAMS` does not provide a general JSON escaping format. Escaping quotes in an API request does not
protect commas from this parser.

### When to use pipeline_vars.env instead

Use `.github/pipeline_vars.env` when:

- A nonsecret JSON value contains commas or quotes.
- You want the same values on many runs (for example debugging).
- The parameter has no dedicated input that would overwrite it.

Use one `KEY=VALUE` assignment per line. The action copies the file verbatim into `GITHUB_ENV`. It does not interpret
shell syntax, remove surrounding quotes, or process `export` statements. Keep JSON on one line with its internal
quotes intact, and do not add shell quotes around the entire value. Do not commit secrets to this file.

## Adding new parameters

`process_variables.sh` exports every `workflow_dispatch` input automatically. You do not add `echo` lines for new
inputs.

**Dedicated input.** Add the field under `on.workflow_dispatch.inputs` in `Envgene.yml`. The next run exports it.

**`GH_ADDITIONAL_PARAMS`.** Pass `MY_NEW_PARAM=value` when the parameter already exists in
[Instance pipeline parameters](/docs/instance-pipeline-parameters.md) but has no dedicated input.

**`pipeline_vars.env`.** Add `MY_NEW_PARAM=my_value` in `.github/pipeline_vars.env`.

Exporting a name does not implement new behavior. The EnvGene scripts or plugins in the selected image must support
the parameter. Check [Instance pipeline parameters](/docs/instance-pipeline-parameters.md) before adding one.

## Parameter priority

For a name written to `GITHUB_ENV` (orchestrator parameters), later writes win:

1. `GH_ADDITIONAL_PARAMS`
1. Dedicated workflow inputs
1. `.github/pipeline_vars.env`

For values interpolated in `Envgene.yml` itself (image, runner label, timeout), GitHub `vars` apply, then the
fallback in the workflow file. `pipeline_vars.env` and `GH_ADDITIONAL_PARAMS` cannot configure these expressions.

Dedicated inputs overwrite file values even when the input is an empty string or a default boolean. For example,
`ENV_TEMPLATE_VERSION` in the file is overwritten by the empty workflow input. A nonempty value in
`GH_ADDITIONAL_PARAMS` overrides the runtime value afterward, but `sync` still uses the original dispatch inputs.

## Repository variables

Repository variables are configured in **Settings → Secrets and variables → Actions → Variables**. The workflow reads
them as `vars.VARIABLE_NAME`.

### Variables used by the workflow

| Variable                         | Purpose                                            | Fallback when empty                |
|----------------------------------|----------------------------------------------------|------------------------------------|
| `DOCKER_REGISTRY`                | Registry host for both job images                  | `ghcr.io`                          |
| `DOCKER_NAMESPACE`               | Image namespace                                    | `netcracker`                       |
| `ENVGENE_IMAGE`                  | Image name                                         | `qubership-envgene`                |
| `ENVGENE_VERSION`                | EnvGene image tag                                  | Release tag in `Envgene.yml`       |
| `DOCKER_CLOUD_REGISTRY_PROVIDER` | `GCP` selects GAR credentials on the container job | (empty, GHCR auth)                 |
| `GH_RUNNER_TAG_NAME`             | Runner label                                       | `ubuntu-22.04`                     |
| `GH_RUNNER_SCRIPT_TIMEOUT`       | Job timeout in minutes                             | `10`                               |
| `GH_USER_EMAIL`                  | Git commit author email                            | `<actor>@users.noreply.github.com` |
| `GH_USER_NAME`                   | Git commit author name                             | `github.actor`                     |
| `SECRET_POSTFIX`                 | Exported for integration-specific scripts          | `secret_postfix`                   |
| `SYNCER_IMAGE`                   | Image name for the `sync` job                      | `qubership-envgene`                |
| `SYNCER_VERSION`                 | Image tag for the `sync` job                       | `2.6.6`                            |

For secrets and variables used by EnvGene at runtime (encryption keys, log level, and so on), see
[EnvGene repository variables](/docs/envgene-repository-variables.md).

### CMDB import requirements

`CMDB_IMPORT=true` on a non-`GITLAB_DEPLOY` run calls `/module/scripts/cmdb_import/cmdb_import.sh` after the
orchestrator. The current source tree does not provide that script. To use this integration, select an image that
supplies it and explicitly map the credentials required by that implementation into the job.

The orchestrator also has a separate `CMDB_import` plugin step. It requires a parameter plugin to populate
`CMDB_IMPORT` and an implementation under `/module/scripts/plugins/nc_cmdb_import`.

`SECRET_POSTFIX` is exported from repository variables, but `Envgene.yml` does not look up or pass a per-cluster CMDB
secret. Creating a secret named `{CLUSTER_NAME}_{SECRET_POSTFIX}` alone does not make it available to the container.

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
timeout-minutes: ${{ fromJSON(vars.GH_RUNNER_SCRIPT_TIMEOUT || '10') }}
```

You do not need to define variables that have fallbacks. Check `Envgene.yml` for the release-specific EnvGene tag.
`ENVGENE_VERSION` and `SYNCER_VERSION` are independent.

## Using different Docker registries

Both jobs use `DOCKER_REGISTRY` and `DOCKER_NAMESPACE`. The `env-prepare` image path is:

```text
${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${ENVGENE_IMAGE}:${ENVGENE_VERSION}
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
  "https://api.github.com/repos/<OWNER>/<REPO>/actions/workflows/Envgene.yml/dispatches" \
  -d '{
    "ref": "main",
    "inputs": {
      "ENV_NAMES": "cluster-01/env-01",
      "OPERATION_TYPE": "DEPLOY",
      "ENV_BUILDER": "true",
      "GENERATE_EFFECTIVE_SET": "true",
      "DEPLOYMENT_TICKET_ID": "QBSHP-0001",
      "GH_ADDITIONAL_PARAMS": "ENVGENE_LOG_LEVEL=DEBUG"
    }
  }'
```

Replace `<YOUR_GITHUB_TOKEN>`, `<OWNER>`, `<REPO>`, and `main` as needed.

</details>

## Directory structure

```text
github_workflows/instance-repo-pipeline/
└── .github/
    ├── README.md                # This guide
    ├── actions/
    │   └── load-env-files/
    │       └── action.yml       # Copies environment files into GITHUB_ENV
    ├── docs/
    │   └── assets/
    │       └── envgene-workflow-header.png
    ├── pipeline_vars.env        # Empty runtime configuration file
    ├── scripts/
    │   └── process_variables.sh # Exports workflow inputs and GH_ADDITIONAL_PARAMS
    └── workflows/
        └── Envgene.yml          # Instance pipeline workflow
```

## Use case scenarios

The legacy scenarios below leave `PIPELINE_TYPE` empty and set `OPERATION_TYPE=DEPLOY` explicitly.

Additional configured inputs, plugins, and existing repository files can enable more steps than those listed.
On the legacy path, `migrate_sd_to_deploy_plan` runs without new SD input if `use_committed_sd` is enabled,
`sd.yaml` exists, and `deploy-plan.yml` does not. `use_committed_sd` defaults to `true`.

### Scenario 1: Environment build and Effective Set

**Goal:** Build the environment and generate the Effective Set.

| Parameter                | Value                  |
|--------------------------|------------------------|
| `ENV_NAMES`              | `prod-cluster/prod-01` |
| `OPERATION_TYPE`         | `DEPLOY`               |
| `ENV_BUILDER`            | `true`                 |
| `GENERATE_EFFECTIVE_SET` | `true`                 |
| `DEPLOYMENT_TICKET_ID`   | `QBSHP-1234`           |

**Orchestrator steps that run:** `appregdef_render` → `regdefv2_adapter` → `env_build` → `generate_effective_set` →
`git_commit`.

**Result:** Environment Instance is generated, Effective Set is written under the environment tree, changes are
committed.

### Scenario 2: Environment build only

**Goal:** Regenerate the Environment Instance without Effective Set on the legacy path.

| Parameter        | Value                |
|------------------|----------------------|
| `ENV_NAMES`      | `dev-cluster/dev-01` |
| `OPERATION_TYPE` | `DEPLOY`             |
| `ENV_BUILDER`    | `true`               |

**Result:** `generate_effective_set` is skipped unless `PIPELINE_TYPE=GITLAB_DEPLOY` forces it.

### Scenario 3: Update template version and rebuild

| Parameter              | Value                  |
|------------------------|------------------------|
| `ENV_NAMES`            | `prod-cluster/prod-01` |
| `OPERATION_TYPE`       | `DEPLOY`               |
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

Configure both AGE secrets and an image with the sync tools via `SYNCER_IMAGE` and `SYNCER_VERSION`, or verify that
their fallbacks meet your requirements. After `env-prepare` succeeds, `sync` runs.

Set `BG_STATE` in `.github/pipeline_vars.env` as single-line JSON using the
[`BG_STATE` structure](/docs/instance-pipeline-parameters.md#bg_state). The `change_bg_state` step reads it before
`warmup`, so it is required for this scenario too. Keep the JSON quotes intact and do not wrap the value in shell
quotes.

See [Blue-Green deployment](/docs/features/blue-green-deployment.md) and
[Instance pipeline parameters](/docs/instance-pipeline-parameters.md) for `BGD_OPERATION` and `BG_STATE`.

### Scenario 5: Credential rotation

| Parameter        | Value                  |
|------------------|------------------------|
| `ENV_NAMES`      | `prod-cluster/prod-01` |
| `OPERATION_TYPE` | `DEPLOY`               |
| `ENV_BUILDER`    | `false`                |

Add a secret-backed `CRED_ROTATION_PAYLOAD` environment mapping under `jobs.env-prepare.env` in your instance copy
of `Envgene.yml`. Store the payload as single-line JSON in that Actions secret. Use the `rotation_items` structure
described in [Credential rotation](/docs/features/cred-rotation.md). Do not pass the payload through
`GH_ADDITIONAL_PARAMS`, which logs its values and consumes JSON syntax.

**Orchestrator steps that run:** `credential_rotation` → `git_commit`.

Do not set `GET_PASSPORT` in the same run. See [Credential rotation](/docs/features/cred-rotation.md).

### Scenario 6: Process Solution Descriptor from artifact (legacy)

| Parameter              | Value                                                      |
|------------------------|------------------------------------------------------------|
| `ENV_NAMES`            | `prod-cluster/prod-01`                                     |
| `OPERATION_TYPE`       | `DEPLOY`                                                   |
| `GH_ADDITIONAL_PARAMS` | `SD_VERSION=my-solution:v1.2.3,SD_REPO_MERGE_MODE=replace` |

`process_sd` runs only when `PIPELINE_TYPE` is not `GITLAB_DEPLOY`. See
[SD processing](/docs/use-cases/sd-processing.md).

### Scenario 7: Generate new environment inventory

| Parameter               | Value                          |
|-------------------------|--------------------------------|
| `ENV_NAMES`             | `new-cluster/new-env`          |
| `OPERATION_TYPE`        | `DEPLOY`                       |
| `ENV_BUILDER`           | `false`                        |
| `ENV_INVENTORY_CONTENT` | Valid single-line JSON payload |

**Orchestrator steps that run:** `env_inventory_generation` → `git_commit`.

Use the payload structure and examples in
[Environment inventory generation](/docs/features/env-inventory-generation.md#full-env_inventory_content-example).
Do not include real credentials in dispatch inputs.

### Scenario 8: Multiple environments in one run

| Parameter        | Value                                 |
|------------------|---------------------------------------|
| `ENV_NAMES`      | `cluster-01/env-01,cluster-01/env-02` |
| `OPERATION_TYPE` | `DEPLOY`                              |
| `ENV_BUILDER`    | `true`                                |

**Result:** One `env-prepare` job. The orchestrator fans out one child process per environment. This is not a GitHub
matrix. `PIPELINE_TYPE=GITLAB_DEPLOY` rejects multiple resolved environments.

## Further reading

| Document                                                                               | Description                    |
|----------------------------------------------------------------------------------------|--------------------------------|
| [Instance pipeline parameters](/docs/instance-pipeline-parameters.md)                  | Full parameter reference       |
| [EnvGene pipelines](/docs/envgene-pipelines.md)                                        | Pipeline flow and descriptions |
| [Using different Docker registries](/docs/how-to/docker-registry-configuration.md)     | GHCR and GAR configuration     |
| [Blue-Green deployment](/docs/features/blue-green-deployment.md)                       | BG-related parameters          |
| [SD processing](/docs/use-cases/sd-processing.md)                                      | Solution Descriptor use cases  |
