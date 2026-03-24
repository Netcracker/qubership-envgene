# Using Docker Registries in EnvGene GitHub Workflow

- [Using Docker Registries in EnvGene GitHub Workflow](#using-docker-registries-in-envgene-github-workflow)
  - [Description](#description)
  - [Supported Registries](#supported-registries)
  - [Prerequisites](#prerequisites)
  - [How the Workflow Uses the Registry](#how-the-workflow-uses-the-registry)
  - [Option 1: GitHub Container Registry (GHCR)](#option-1-github-container-registry-ghcr)
    - [GHCR Configuration](#ghcr-configuration)
    - [GHCR Authentication](#ghcr-authentication)
  - [Option 2: Google Artifact Registry (GAR)](#option-2-google-artifact-registry-gar)
    - [GAR Prerequisites](#gar-prerequisites)
    - [Step 1: Configure GitHub Repository Variables](#step-1-configure-github-repository-variables)
    - [Step 2: Add GCP\_SA\_KEY Secret](#step-2-add-gcp_sa_key-secret)
    - [GAR Authentication Flow](#gar-authentication-flow)
  - [Parameter Reference](#parameter-reference)
  - [Switching Between Registries](#switching-between-registries)
  - [Troubleshooting](#troubleshooting)

## Description

This guide explains how to configure the EnvGene GitHub workflow to pull Docker images from different registries. The workflow uses three EnvGene images: `qubership-envgene`, `qubership-pipegene`, and `qubership-effective-set-generator`. By default, these images are pulled from GitHub Container Registry (GHCR). You can switch to Google Artifact Registry (GAR) by configuring the appropriate variables and secrets.

## Supported Registries

The EnvGene GitHub workflow currently supports two Docker registries:

- **GitHub Container Registry (GHCR)** - Default option, no additional configuration required
- **Google Artifact Registry (GAR)** - Requires GCP service account configuration

> [!NOTE]
> For other registry types (AWS ECR, Azure ACR, custom registries), custom authentication steps need to be added to the workflow.

## Prerequisites

- Instance repository with the EnvGene GitHub workflow installed
- Access to **Settings → Secrets and variables → Actions** in your GitHub repository

## How the Workflow Uses the Registry

The workflow defines image names in the `env` section of `Envgene.yml`:

```yaml
env:
  DOCKER_IMAGE_NAME_ENVGENE: "${{ vars.DOCKER_REGISTRY || 'ghcr.io/netcracker' }}/qubership-envgene"
  DOCKER_IMAGE_NAME_PIPEGENE: "${{ vars.DOCKER_REGISTRY || 'ghcr.io/netcracker' }}/qubership-pipegene"
  DOCKER_IMAGE_NAME_EFFECTIVE_SET_GENERATOR: "${{ vars.DOCKER_REGISTRY || 'ghcr.io/netcracker' }}/qubership-effective-set-generator"
```

The `DOCKER_REGISTRY` variable (from repository variables) determines the registry base. When `DOCKER_CLOUD_REGISTRY_PROVIDER` is set to `GCP`, the workflow runs an authentication step before pulling images from GAR.

## Option 1: GitHub Container Registry (GHCR)

GHCR is the default registry. No additional configuration is required if your images are hosted at `ghcr.io/netcracker`.

### GHCR Configuration

| Where to configure       | Parameter         | Value                |
|--------------------------|-------------------|----------------------|
| **Settings → Variables** | `DOCKER_REGISTRY` | `ghcr.io/netcracker` |

If you omit `DOCKER_REGISTRY`, the workflow uses `ghcr.io/netcracker` by default.

### GHCR Authentication

GitHub Actions automatically authenticates to `ghcr.io` using `GITHUB_TOKEN` when pulling images. No extra secrets are needed. Ensure your repository has access to the container images (e.g. via package permissions if the images are in a different organization).

## Option 2: Google Artifact Registry (GAR)

To use Google Artifact Registry, you must configure the registry URL, set the cloud provider, and provide a GCP service account key for authentication.

### GAR Prerequisites

- Registry URL (path to your GAR repository)
- GCP service account JSON key with access to the registry

### Step 1: Configure GitHub Repository Variables

1. Go to your repository on GitHub.
2. Open **Settings → Secrets and variables → Actions**.
3. Open the **Variables** tab.
4. Add or edit the following variables:

| Variable                         | Value                                        |
|----------------------------------|----------------------------------------------|
| `DOCKER_REGISTRY`                | `REGION-docker.pkg.dev/PROJECT_ID/REPO_NAME` |
| `DOCKER_CLOUD_REGISTRY_PROVIDER` | `GCP`                                        |

**Example for `DOCKER_REGISTRY`:**

```text
europe-west1-docker.pkg.dev/my-gcp-project/envgene-images
```

Replace:

- `REGION` with your GAR region (e.g. `europe-west1`, `us-central1`)
- `PROJECT_ID` with your GCP project ID
- `REPO_NAME` with your Artifact Registry repository name

### Step 2: Add GCP_SA_KEY Secret

1. In **Settings → Secrets and variables → Actions**, open the **Secrets** tab.
2. Click **New repository secret**.
3. Name: `GCP_SA_KEY`.
4. Value: Paste the full JSON content of the GCP service account key (including `{` and `}`).
5. Click **Add secret**.

> [!IMPORTANT]
> The secret must contain the full JSON. Do not truncate or modify it. The workflow uses it with `docker login -u _json_key --password-stdin`.

### GAR Authentication Flow

When `DOCKER_CLOUD_REGISTRY_PROVIDER` is set to `GCP`, the workflow runs this step in the `envgene_execution` job:

```yaml
- name: Authenticate to GAR (Google Artifact Registry)
  if: needs.process_environment_variables.outputs.DOCKER_CLOUD_REGISTRY_PROVIDER == 'GCP'
  run: |
    REGISTRY_HOST=$(echo "${{ vars.DOCKER_REGISTRY }}" | cut -d'/' -f1)
    echo '${{ secrets.GCP_SA_KEY }}' | docker login -u _json_key --password-stdin "$REGISTRY_HOST"
```

The step extracts the registry host (e.g. `europe-west1-docker.pkg.dev`) from `DOCKER_REGISTRY` and authenticates before any Docker image pulls.

## Parameter Reference

| Parameter                        | Location  | Required for GHCR     | Required for GAR       |
|----------------------------------|-----------|-----------------------|------------------------|
| `DOCKER_REGISTRY`                | Variables | No (uses default)     | Yes                    |
| `DOCKER_CLOUD_REGISTRY_PROVIDER` | Variables | No                    | Yes - set to `GCP`     |
| `GCP_SA_KEY`                     | Secrets   | No                    | Yes                    |

> [!NOTE]
> For GHCR: If you omit `DOCKER_REGISTRY`, the workflow uses the default value `ghcr.io/netcracker`. Set `DOCKER_REGISTRY` only if your images are in a different GHCR organization or path.

## Switching Between Registries

To switch from GHCR to GAR:

1. Add `DOCKER_REGISTRY` and `DOCKER_CLOUD_REGISTRY_PROVIDER` variables.
2. Add `GCP_SA_KEY` secret.
3. Trigger the workflow. The GAR authentication step will run automatically.

To switch back to GHCR:

1. Remove or clear `DOCKER_CLOUD_REGISTRY_PROVIDER` (or set it to empty).
2. Set `DOCKER_REGISTRY` to `ghcr.io/netcracker` (or remove it to use the default).
3. Optionally remove `GCP_SA_KEY` if no longer needed.

## Troubleshooting

**Authentication fails with "unauthorized" or "denied":**

- Verify `GCP_SA_KEY` contains the full JSON key.
- Ensure the service account has `Artifact Registry Reader` role on the repository.
- Check that the key has not expired.

**Image pull fails with "not found":**

- Verify `DOCKER_REGISTRY` format: `REGION-docker.pkg.dev/PROJECT_ID/REPO_NAME`.
- Ensure the images exist in the repository with the expected names: `qubership-envgene`, `qubership-pipegene`, `qubership-effective-set-generator`.
- Check the image tags match those in the workflow (e.g. `1.31.9`).

**GAR authentication step does not run:**

- Confirm `DOCKER_CLOUD_REGISTRY_PROVIDER` is set to `GCP` (case-sensitive).
- Variables are passed via `process_environment_variables` job outputs. Ensure the variable is not overridden in `config.env` or `pipeline_vars.env` with an empty value.
