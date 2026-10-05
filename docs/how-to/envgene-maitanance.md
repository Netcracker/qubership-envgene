# Environment Instance Repository Installation Guide

## Description

This guide describes the process of initializing and upgrading an Environment Instance repository using the Git-System-Follower (GSF) package manager.

## Prerequisites

1. GSF Package Manager Installation

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

Expand the variables section from **Settings → CI/CD** in your GitLab repository and set the following variable:

- `GITLAB_TOKEN`: The token created in Step 2

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
   -t <gitlab_token>
```

**Parameter Details:**

- `<path_to_instance_package_image>`: Docker image path from Step 1
- `<project_instance_repository_path>`: Project instance repository URL (format: `https://git.com/project.git`)
- `<project_instance_repository_branch>`: Branch of project instance repository
- `<gitlab_token>`: Project instance repository token from Initial Setup Step 2

**Example:**

```bash
git-system-follower install \
   docker.io/envgene/instance:1.2.3 \
   -r https://git.qubership.org/configuration-management/env-instance.git \
   -b master \
   -t token-placeholder-123
```
