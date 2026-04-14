# GSF Repository Maintenance Use Cases

- [GSF Repository Maintenance Use Cases](#gsf-repository-maintenance-use-cases)
  - [Overview](#overview)
  - [Template Repository Maintenance via GSF](#template-repository-maintenance-via-gsf)
    - [UC-GSF-TMP-1: Initialize Template Repository via GSF](#uc-gsf-tmp-1-initialize-template-repository-via-gsf)
    - [UC-GSF-TMP-2: Upgrade Template Repository via GSF](#uc-gsf-tmp-2-upgrade-template-repository-via-gsf)
    - [UC-GSF-TMP-3: Downgrade Template Repository via GSF](#uc-gsf-tmp-3-downgrade-template-repository-via-gsf)
  - [Instance Repository Maintenance via GSF](#instance-repository-maintenance-via-gsf)
    - [UC-GSF-INST-1: Initialize Instance Repository via GSF](#uc-gsf-inst-1-initialize-instance-repository-via-gsf)
    - [UC-GSF-INST-2: Upgrade Instance Repository via GSF](#uc-gsf-inst-2-upgrade-instance-repository-via-gsf)
    - [UC-GSF-INST-3: Downgrade Instance Repository via GSF](#uc-gsf-inst-3-downgrade-instance-repository-via-gsf)

## Overview

This document defines use cases for maintaining EnvGene Template and Instance repositories with the Git-System-Follower (GSF) package manager.

For each repository type, it covers three maintenance scenarios:

- Initial installation (init)
- Upgrade to a new EnvGene package version
- Downgrade to an older EnvGene package version

For every scenario, repository contents after GSF execution are validated against a reference structure (golden state) to confirm that managed files are correctly added, updated, or removed.

For detailed installation and maintenance steps, see:

- Template Repository: [Maintain Template Repository via GSF](/docs/how-to/template-repository-maintenance.md)
- Instance Repository: [Environment Instance Repository Installation Guide](/docs/how-to/envgene-maitanance.md)

## Template Repository Maintenance via GSF

### UC-GSF-TMP-1: Initialize Template Repository via GSF

**Pre-requisites:**

1. A new Git repository for the Environment Template exists in the project Git group and does not yet contain EnvGene-specific files.
2. GitLab technical user and access token with required permissions are available.
3. GSF package manager is installed and working on the local machine.
4. Template package image path for the desired EnvGene version is known.
5. A reference (target) Template Repository structure for this version is defined.

**Trigger:**

User runs GSF on the local machine to initialize the Template Repository:

```bash
git-system-follower install <path_to_template_package_image> \
  -r <project_template_repository_path> \
  -b <project_template_repository_branch> \
  -t <gitlab_token> \
  --extra env_template_artifact_name <template-artifact-name> no-masked
```

**Steps:**

1. Run GSF with repository URL, branch, token, and package image.
2. GSF applies the selected package to the Template Repository.
3. GSF adds required files from the selected version and removes obsolete managed files (if any).

**Results:**

1. Template Repository is initialized.
2. Required files from the selected version are present.
3. Old managed files are removed or replaced.
4. Repository matches the reference structure.

### UC-GSF-TMP-2: Upgrade Template Repository via GSF

**Pre-requisites:**

1. Template Repository already exists and contains a previous EnvGene template package version.
2. GitLab technical user, token, and required CI/CD variables are available.
3. GSF package manager is installed and working on the local machine.
4. Target EnvGene template package image path is known.
5. A reference Template Repository structure for the target EnvGene version is defined.

**Trigger:**

User runs GSF on the local machine to upgrade the Template Repository to a new EnvGene version:

```bash
git-system-follower install <path_to_template_package_image> \
  -r <project_template_repository_path> \
  -b <project_template_repository_branch> \
  -t <gitlab_token> \
  --extra env_template_artifact_name <template-artifact-name> no-masked
```

**Steps:**

1. Run GSF with repository URL, branch, token, and target package image.
2. GSF updates the Template Repository to the target version.
3. GSF updates changed files, adds new files, and removes outdated managed files.
4. Verify restricted files for Template Repository:
   - `pipeline_vars.yml` or `pipeline_vars.yaml`
   - `build_vars.sh`
   - `description_template.yml` or `description_template.yaml`
5. Verify restricted file behavior:
   - `build_vars.sh` and `description_template.*` preserve user-defined values after upgrade
   - `pipeline_vars.*` preserves user-defined values, except allowed structural alignment with current package structure

**Results:**

1. Template Repository is upgraded to the target version.
2. Repository matches the reference structure.
3. Restricted files are preserved according to policy:
   - `build_vars.sh` and `description_template.*` are not replaced with package defaults
   - `pipeline_vars.*` is preserved, with structural alignment allowed when required
4. No regressions related to repository upgrade are observed.

### UC-GSF-TMP-3: Downgrade Template Repository via GSF

**Pre-requisites:**

1. Template Repository already exists and has a later version.
2. GitLab token and required variables are available.
3. GSF is installed on the local machine.
4. Path to an older template package image is known.
5. Reference structure for the older version is available.

**Trigger:**

User runs GSF on the local machine to install an older template package version:

```bash
git-system-follower install <path_to_template_package_image> \
  -r <project_template_repository_path> \
  -b <project_template_repository_branch> \
  -t <gitlab_token> \
  --extra env_template_artifact_name <template-artifact-name> no-masked
```

**Steps:**

1. Run GSF with repository URL, branch, token, and older package image.
2. GSF applies the older package to the Template Repository.
3. GSF replaces current managed files with older-version files and removes extra files.

**Results:**

1. Template Repository is switched to the older version.
2. Required files for the older version are present.
3. Files from the later version are removed.
4. Repository matches the reference structure.

## Instance Repository Maintenance via GSF

### UC-GSF-INST-1: Initialize Instance Repository via GSF

**Pre-requisites:**

1. A new Git repository for the Environment Instance exists in the project Git group.
2. GitLab project access token with required scopes is available.
3. GSF package manager is installed and working on the local machine.
4. Instance package image path for the chosen EnvGene version is known.
5. A reference Instance Repository structure for this version is defined.

**Trigger:**

User runs GSF on the local machine to initialize the Instance Repository:

```bash
git-system-follower install <path_to_instance_package_image> \
   -r <project_instance_repository_path> \
   -b <project_instance_repository_branch> \
   -t <gitlab_token>
```

**Steps:**

1. Run GSF with repository URL, branch, token, and package image.
2. GSF applies the selected package to the Instance Repository.
3. GSF creates the required CI/CD and configuration files for the selected version.

**Results:**

1. Instance Repository is initialized.
2. Required files from the selected version are present.
3. Repository matches the reference structure.

### UC-GSF-INST-2: Upgrade Instance Repository via GSF

**Pre-requisites:**

1. Instance Repository already exists and contains a previous EnvGene instance package version.
2. GitLab token and required CI/CD variables are available.
3. GSF package manager is installed and working on the operator's machine.
4. Target EnvGene instance package image path is known.
5. A reference Instance Repository structure for the target EnvGene version is defined.

**Trigger:**

User runs GSF on the local machine to upgrade the Instance Repository:

```bash
git-system-follower install <path_to_instance_package_image> \
   -r <project_instance_repository_path> \
   -b <project_instance_repository_branch> \
   -t <gitlab_token>
```

**Steps:**

1. Run GSF with repository URL, branch, token, and target package image.
2. GSF updates the Instance Repository to the target version.
3. GSF updates changed files, adds new files, and removes outdated managed files.
4. Verify `configuration/credentials/credentials.yml` contains `self-token-cred`:
   - `type: secret`
   - `data.secret` is present.
5. Verify `configuration/integration.yml` contains:
   - `self_token: "${creds.get('self-token-cred').secret}"`.
6. Verify legacy `self_token` definition is absent in `configuration/config.yml` or ignored by the target version.
7. Verify placeholder file `configuration/.gitkeep` is present.

**Results:**

1. Instance Repository is upgraded to the target version.
2. Repository matches the reference structure.
3. Token configuration is migrated and valid:
   - `configuration/credentials/credentials.yml` contains `self-token-cred` with non-empty secret data,
   - `configuration/integration.yml` references `${creds.get('self-token-cred').secret}` in `self_token`,
   - runtime execution does not fail with missing `self_token` or missing `self-token-cred`.
4. Legacy token definition in `configuration/config.yml` is absent or ignored by the target version, and does not affect runtime behavior.

### UC-GSF-INST-3: Downgrade Instance Repository via GSF

**Pre-requisites:**

1. Instance Repository already exists and has a later version.
2. GitLab token and required variables are available.
3. GSF is installed on the local machine.
4. Path to an older instance package image is known.
5. Reference structure for the older version is available.

**Trigger:**

User runs GSF on the local machine to install an older instance package version:

```bash
git-system-follower install <path_to_instance_package_image> \
   -r <project_instance_repository_path> \
   -b <project_instance_repository_branch> \
   -t <gitlab_token>
```

**Steps:**

1. Run GSF with repository URL, branch, token, and older package image.
2. GSF applies the older package to the Instance Repository.
3. GSF replaces current managed files with older-version files and removes extra files.

**Results:**

1. Instance Repository is switched to the older version.
2. Required files for the older version are present.
3. Files from the later version are removed.
4. Repository matches the reference structure.
