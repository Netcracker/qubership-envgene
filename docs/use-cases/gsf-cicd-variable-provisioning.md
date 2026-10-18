# GSF CI/CD variable provisioning use cases

- [GSF CI/CD variable provisioning use cases](#gsf-cicd-variable-provisioning-use-cases)
  - [Overview](#overview)
  - [Provisioned variables](#provisioned-variables)
  - [UC-VAR-1: Initialize - variables created](#uc-var-1-initialize---variables-created)
  - [UC-VAR-2: Upgrade - variables updated alongside package files](#uc-var-2-upgrade---variables-updated-alongside-package-files)
  - [UC-VAR-3: Failure - insufficient token permissions](#uc-var-3-failure---insufficient-token-permissions)
  - [UC-VAR-4: Failure - required variable not supplied](#uc-var-4-failure---required-variable-not-supplied)

## Overview

During GSF installation of the EnvGene instance package, GSF sets a defined set of GitLab project
CI/CD variables on the target repository. This eliminates the manual step of opening GitLab
**Settings → CI/CD → Variables** after installation.

GSF provisions variables on first install and on version upgrade. It does not re-run provisioning
when the same package version is already installed.

For installation steps, see the
[Environment Instance Repository Installation Guide](/docs/how-to/envgene-maitanance.md).

## Provisioned variables

`GITLAB_TOKEN` is mandatory. Additional variables such as `DOCKER_REGISTRY` can be passed if
required by the project.

| Variable name     | Masked | Purpose                                           |
|-------------------|--------|---------------------------------------------------|
| `GITLAB_TOKEN`    | yes    | GitLab token for instance pipeline authentication |
| `DOCKER_REGISTRY` | no     | Docker registry hostname for pipeline image pulls |

A variable is set only when the corresponding `--extra` is provided. Omitting an `--extra` leaves
the existing variable on the repository unchanged.

---

### UC-VAR-1: Initialize - variables created

**Pre-requisites:**

1. A new Git repository for the Environment Instance exists and contains no CI/CD variables.
2. A GitLab access token with the Maintainer role and API, read_repository, write_repository
   scopes is available.
3. GSF package manager is installed on the local machine.
4. Instance package image path is known.

**Trigger:**

User runs GSF on the local machine:

```bash
git-system-follower install <instance_package_image> \
  -r <instance_repo_url> \
  -b <branch> \
  -t <gitlab_token> \
  --extra GITLAB_TOKEN <gitlab_token> masked \
  --extra DOCKER_REGISTRY <registry_host> no-masked
```

**Steps:**

1. GSF applies the instance package to the repository (files, pipeline config).
2. GSF checks the repository for an existing `GITLAB_TOKEN` CI/CD variable - none found.
3. GSF creates `GITLAB_TOKEN` as a masked project CI/CD variable.
4. GSF checks the repository for an existing `DOCKER_REGISTRY` CI/CD variable - none found.
5. GSF creates `DOCKER_REGISTRY` as a non-masked project CI/CD variable.

**Results:**

1. Repository contains the package-managed files for the installed version.
2. `GITLAB_TOKEN` exists as a masked CI/CD variable on the repository with the supplied value.
3. `DOCKER_REGISTRY` exists as a non-masked CI/CD variable on the repository with the supplied value.
4. The instance pipeline can run without manual variable configuration in GitLab Settings.

---

### UC-VAR-2: Upgrade - variables updated alongside package files

**Pre-requisites:**

1. Instance Repository already exists with a previous EnvGene package version.
2. CI/CD variables were set during the previous install.
3. A GitLab access token with the Maintainer role is available.
4. Target EnvGene instance package image path is known.

**Trigger:**

User runs GSF with the new package version:

```bash
git-system-follower install <new_instance_package_image> \
  -r <instance_repo_url> \
  -b <branch> \
  -t <gitlab_token> \
  --extra GITLAB_TOKEN <gitlab_token> masked \
  --extra DOCKER_REGISTRY <registry_host> no-masked
```

**Steps:**

1. GSF updates the repository files to the new package version.
2. GSF overwrites each supplied CI/CD variable with the value from the upgrade command.

**Results:**

1. Repository files are upgraded to the new package version.
2. CI/CD variables reflect the values supplied in the upgrade command.
3. No duplicate variables are created.
4. `pipeline_vars.*` preserves user-defined values per existing upgrade policy.

---

### UC-VAR-3: Failure - insufficient token permissions

**Pre-requisites:**

1. Instance Repository exists.
2. The token used has the Developer role (not Maintainer or Owner) on the project.

**Trigger:**

User runs GSF install with a Developer-role token:

```bash
git-system-follower install <instance_package_image> \
  -r <instance_repo_url> \
  -b <branch> \
  -t <developer_token> \
  --extra GITLAB_TOKEN <developer_token> masked
```

**Steps:**

1. GSF applies the instance package files to the repository.
2. GSF attempts to set `GITLAB_TOKEN` as a CI/CD variable via the GitLab API.
3. The GitLab API rejects the request (403 Forbidden) because CI/CD variable management
   requires Maintainer access.
4. GSF exits with an error.

**Results:**

1. GSF exits with a 403 error.
2. Repository files may have been updated before the failure (file changes run before variable
   provisioning).
3. No CI/CD variables are set or updated.

> [!NOTE]
> To recover: re-run GSF with a token that has the Maintainer role on the target repository.
> Re-running also re-applies any file changes, which is safe.

---

### UC-VAR-4: Failure - required variable not supplied

**Pre-requisites:**

1. Instance Repository exists (new or existing).
2. A GitLab access token with the Maintainer role is available.

**Trigger:**

User runs GSF install without supplying the `GITLAB_TOKEN` extra:

```bash
git-system-follower install <instance_package_image> \
  -r <instance_repo_url> \
  -b <branch> \
  -t <gitlab_token>
```

**Steps:**

1. GSF applies the instance package files to the repository.
2. No extras matching `GITLAB_TOKEN` are supplied, so GSF skips variable provisioning.

**Results:**

1. Repository files are installed or upgraded successfully.
2. No CI/CD variables are created or updated.
3. The instance pipeline cannot authenticate until `GITLAB_TOKEN` is set manually in
   GitLab **Settings → CI/CD → Variables**, or GSF is re-run with `--extra GITLAB_TOKEN`.
