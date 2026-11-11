# Environment Instance Repository Installation Guide

## Description

This guide describes the process of initializing and upgrading an Environment Instance repository using the Git-System-Follower (GSF) package manager.

## Prerequisites

### 1. GSF Package Manager Installation

GSF package manager must be installed on your local machine. [How to install GSF](https://github.com/Netcracker/qubership-git-system-follower/blob/main/docs/getting_started/installation.md).

## Initial Setup (One-Time)

Perform these steps only once when setting up a new Environment Instance repository:

### 1. Create Instance Repository

Create a new Git repository for the Environment Instance within your project Git group.

### 2. Issue GitLab Token

Create a GitLab access token following [GitLab's documentation](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html#create-a-project-access-token). Use these parameters:

- **Token name**: `access-token`
- **Expiration date**: leave empty (never expires)
- **Select a role**: Maintainer
- **Select scopes**: API, read_api, read_repository, write_repository

### 3. Configure CI/CD Variables

`GITLAB_TOKEN` is mandatory. Additional CI/CD variables, such as `DOCKER_REGISTRY`, may be required depending on the project.

CI/CD variables can be configured automatically by GSF or manually in GitLab.

| Variable name | Masked |
| --- | --- |
| `GITLAB_TOKEN` | Yes |
| `DOCKER_REGISTRY` | No |

#### Option A — Automated (Recommended)

Pass the required variables to GSF using the `--extra` option in the GSF command.

The `--extra` option is used to provide additional variables to GSF.
These variables may be used by the template package and/or configured as CI/CD variables in the Environment Instance repository, depending on the variable.

GSF automatically configures the applicable CI/CD variables during installation.

The token passed via `-t` must have the **Maintainer** role for GSF to configure CI/CD variables automatically.

#### Option B — Manual

If GSF is run without the required `--extra` values, or if automated CI/CD variable provisioning fails, configure the required CI/CD variables manually:

1. Open the Environment Instance repository in GitLab.
2. Go to **Settings → CI/CD → Variables**.
3. Add each required variable from the table above.

## Installation or Upgrade

The process for both installation and upgrade is identical.

### Step 1: Locate Instance Package

1. Go to the [EnvGene release page](https://github.com/Netcracker/qubership-envgene/releases).
2. Select the required release (by default, use the latest version).
   > **Note**: It's recommended to use the same version as your template package.
3. Copy the instance package image path.

### Step 2: Run GSF Command

Run the GSF package manager on your local machine with the following command:

```bash
git-system-follower install <path_to_instance_package_image> \
   -r <project_instance_repository_path> \
   -b <project_instance_repository_branch> \
   -t <gitlab_token> \
   --extra <variable_name> <variable_value> <masked/no-masked>
```

The `--extra` option can be specified multiple times to provide additional variables required during installation.

**Parameter Details:**

- `<path_to_instance_package_image>`: Docker image path from Step 1
- `<project_instance_repository_path>`: Project instance repository URL (format: `https://git.com/project.git`)
- `<project_instance_repository_branch>`: Branch of project instance repository
- `<gitlab_token>`: Project instance repository token from Initial Setup Step 2
- `--extra <variable_name> <variable_value> <masked/no-masked>`: Additional parameters used by the GSF template package or to configure CI/CD variables.

**Example:**

```bash
git-system-follower install \
   docker.io/envgene/instance:1.2.3 \
   -r https://git.qubership.org/configuration-management/env-instance.git \
   -b master \
   -t token-placeholder-123 \
   --extra GITLAB_TOKEN token-placeholder-123 masked \
   --extra DOCKER_REGISTRY registry.example.com no-masked
```
