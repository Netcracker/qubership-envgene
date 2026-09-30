# Environment Instance Repository Installation Guide

## Description

This guide describes the process of initializing and upgrading an Environment Instance repository using the Git-System-Follower (GSF) package manager.

## Prerequisites

GSF package manager must be installed on your local machine. [How to install GSF](https://github.com/Netcracker/qubership-git-system-follower/blob/main/docs/getting_started/installation.md).

Verify GSF is available:

```bash
git-system-follower --version
# Expected: git-system-follower x.x.x
```

## Required Environment Variables

Export these variables before running the GSF command. All subsequent commands reference them.

```bash
# Docker image path of the instance package (from the EnvGene release page)
# Example: docker.io/envgene/instance:1.2.3
export INSTANCE_PACKAGE_IMAGE=""

# Full HTTPS URL of your project instance repository
# Example: https://gitlab.example.com/myproject/myproject-envgene-instance.git
export INSTANCE_REPO_URL=""

# Branch to install into
export INSTANCE_REPO_BRANCH="master"

# GitLab access token with Maintainer role and API, read_repository, write_repository scopes
# (created in Initial Setup step 2)
# GSF uses this token to authenticate and also sets it as a CI/CD variable on
# the repository so the instance pipeline can use it without manual configuration.
export GITLAB_TOKEN=""

# Docker registry hostname used by the instance pipeline to pull images
# Example: ghcr.io
export DOCKER_REGISTRY=""
```

> [!NOTE]
> `GITLAB_TOKEN` is a secret. Do not store it in scripts or commit it to version control.

## Initial Setup (One-Time)

Perform these steps only once when setting up a new Environment Instance repository:

### 1. Create Instance Repository

> **Manual step — cannot be automated:** Repository creation requires access to the GitLab UI or GitLab API.
>
> Create a new Git repository for the Environment Instance within your project Git group.

### 2. Issue GitLab Token

> **Manual step — cannot be automated:** Token creation requires the GitLab web UI.
>
> Create a GitLab access token following [GitLab's documentation](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html#create-a-project-access-token). Use these parameters:
>
> - **Token name**: `access-token`
> - **Expiration date**: leave empty (never expires)
> - **Select a role**: Maintainer
> - **Select scopes**: API, read_api, read_repository, write_repository
>
> Copy the generated token value into `$GITLAB_TOKEN` in the [Required Environment Variables](#required-environment-variables) section.

## Installation or Upgrade

The process for both installation and upgrade is identical.

### Step 1: Locate Instance Package

1. Go to the [EnvGene release page](https://github.com/Netcracker/qubership-envgene/releases).
2. Select the required release (by default, use the latest version).
   > **Note**: It's recommended to use the same version as your template package.
3. Copy the instance package image path and set it as `$INSTANCE_PACKAGE_IMAGE`.

### Step 2: Run GSF Command

Ensure all [Required Environment Variables](#required-environment-variables) are exported, then run:

```bash
git-system-follower install "$INSTANCE_PACKAGE_IMAGE" \
   -r "$INSTANCE_REPO_URL" \
   -b "$INSTANCE_REPO_BRANCH" \
   -t "$GITLAB_TOKEN" \
   --extra GITLAB_TOKEN "$GITLAB_TOKEN" masked \
   --extra DOCKER_REGISTRY "$DOCKER_REGISTRY" no-masked
```

> [!NOTE]
> The token passed via `-t` must have the **Maintainer** role on the target repository.
> A Developer-role token can push files but cannot set CI/CD variables, and GSF will exit with
> a 403 error during variable provisioning.

### Step 3: Configure CI/CD Variables

`GITLAB_TOKEN` is mandatory. Additional variables such as `DOCKER_REGISTRY` can be passed if
required by the project.

| Variable name     | Masked |
|-------------------|--------|
| `GITLAB_TOKEN`    | Yes    |
| `DOCKER_REGISTRY` | No     |

**Option A — Automated (recommended):** Pass each variable as `--extra` in the GSF command as
shown in Step 2. GSF sets it automatically during installation. The token passed via `-t` must have
the Maintainer role for this to work.

**Option B — Manual:** If you ran GSF without `--extra`, or if automated provisioning failed,
set the variables manually:

1. Open the instance repository in GitLab.
2. Go to **Settings → CI/CD → Variables**.
3. Add each required variable from the table above.

**Example:**

```bash
# With variables already exported:
# INSTANCE_PACKAGE_IMAGE=docker.io/envgene/instance:1.2.3
# INSTANCE_REPO_URL=https://git.qubership.org/configuration-management/env-instance.git
# INSTANCE_REPO_BRANCH=master
# GITLAB_TOKEN=<your-token>
# DOCKER_REGISTRY=ghcr.io

git-system-follower install "$INSTANCE_PACKAGE_IMAGE" \
   -r "$INSTANCE_REPO_URL" \
   -b "$INSTANCE_REPO_BRANCH" \
   -t "$GITLAB_TOKEN" \
   --extra GITLAB_TOKEN "$GITLAB_TOKEN" masked \
   --extra DOCKER_REGISTRY "$DOCKER_REGISTRY" no-masked
```

Verify the installation succeeded by checking that GSF committed a new revision to the repository:

> [!WARNING]
> The command below embeds `$GITLAB_TOKEN` in the clone URL. This exposes the token in the shell
> process list and in git's credential logs. Run it in a private terminal and clear your shell
> history afterwards (`history -d` on bash, `history delete` on zsh).

```bash
git clone --branch "$INSTANCE_REPO_BRANCH" \
  "https://oauth2:${GITLAB_TOKEN}@${INSTANCE_REPO_URL#https://}" \
  instance-verify
git -C instance-verify log --oneline -3
# Expected: one or more commits from the GSF install run
```

