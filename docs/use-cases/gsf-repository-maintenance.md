# GSF Repository Maintenance Use Cases

- [GSF Repository Maintenance Use Cases](#gsf-repository-maintenance-use-cases)
  - [Overview](#overview)
  - [Template Repository Maintenance via GSF](#template-repository-maintenance-via-gsf)
    - [UC-GSF-TMP-1: Initialize Template Repository via GSF (compare with reference)](#uc-gsf-tmp-1-initialize-template-repository-via-gsf-compare-with-reference)
    - [UC-GSF-TMP-2: Upgrade Template Repository via GSF (compare with reference)](#uc-gsf-tmp-2-upgrade-template-repository-via-gsf-compare-with-reference)
  - [Instance Repository Maintenance via GSF](#instance-repository-maintenance-via-gsf)
    - [UC-GSF-INST-1: Initialize Instance Repository via GSF (compare with reference)](#uc-gsf-inst-1-initialize-instance-repository-via-gsf-compare-with-reference)
    - [UC-GSF-INST-2: Upgrade Instance Repository via GSF (compare with reference)](#uc-gsf-inst-2-upgrade-instance-repository-via-gsf-compare-with-reference)

## Overview

This document describes use cases for maintaining EnvGene Template and Instance repositories using the Git-System-Follower (GSF) package manager.  
It focuses on two main scenarios for each repository type:

- Initial installation (init)
- Upgrade to a new EnvGene package version

In both cases, the repository contents after GSF execution must be compared against a reference structure (the "golden" or etalon state) to ensure a correct installation or upgrade.

For detailed installation and maintenance steps, see:

- Template Repository: [Maintain Template Repository via GSF](/docs/how-to/template-repository-maintenance.md)
- Instance Repository: [Environment Instance Repository Installation Guide](/docs/how-to/envgene-maitanance.md)

## Template Repository Maintenance via GSF

### UC-GSF-TMP-1: Initialize Template Repository via GSF (compare with reference)

**Pre-requisites:**

1. A new Git repository for the Environment Template exists in the project Git group and does not yet contain EnvGene-specific files.
2. GitLab technical user and access token with required permissions are available.
3. GSF package manager is installed and working on the operator's machine.
4. Template package image path for the desired EnvGene version is known.
5. A reference (target) Template Repository structure for this version is defined.

**Trigger:**

Operator runs GSF on the local machine to initialize the Template Repository:

```bash
git-system-follower install <path_to_template_package_image> \
  -r <project_template_repository_path> \
  -b <project_template_repository_branch> \
  -t <gitlab_token> \
  --extra env_template_artifact_name <template-artifact-name> no-masked
```

**Steps:**

1. GSF connects to the Template Repository using the provided URL, branch, and token.
2. GSF pulls the template package image and applies its contents to the repository (CI/CD configuration, templates, and supporting files).

уКАЗАТЬ ПРО УДАЛЕНИЕ И ВСТАВКУ
ДАУНГРЕЙД НА ПРЕДЫДУЩ ВЕРСИЮ

**Results:**

1. Template Repository is initialized with the EnvGene template package for the selected version and is ready to be used as the Environment Template source.
 - ДОПИСАТЬ ПРО СВЕРКУ С ЭТАЛОНОМ
 рЕПОЗИТОРИЙ СОДЕРЖИТ ВСЕ ФАЙЛЫ ИЗ ГСФ ПАКЕТА НОВОЙ ВЕРСИИ 
 пРЕДЫДЩУИЕ ВЕРСИИ УДАЛЕНЫ 


### UC-GSF-TMP-2: Upgrade Template Repository via GSF (compare with reference)

**Pre-requisites:**

1. Template Repository already exists and contains a previous EnvGene template package version.
2. GitLab technical user, token, and required CI/CD variables are available.
3. GSF package manager is installed and working on the operator's machine.
4. Target EnvGene template package image path is known.
5. A reference Template Repository structure for the target EnvGene version is defined.

**Trigger:**

Operator runs GSF on the local machine to upgrade the Template Repository to a new EnvGene version:

```bash
git-system-follower install <path_to_template_package_image> \
  -r <project_template_repository_path> \
  -b <project_template_repository_branch> \
  -t <gitlab_token> \
  --extra env_template_artifact_name <template-artifact-name> no-masked
```

**Steps:**

1. GSF connects to the existing Template Repository and pulls the target template package image.
2. GSF applies package changes on top of the existing repository contents (updates CI/CD configuration, adds new files, updates or removes outdated files).

**Results:**

1. Template Repository is upgraded to the target EnvGene template package version and matches the expected reference state.

## Instance Repository Maintenance via GSF

### UC-GSF-INST-1: Initialize Instance Repository via GSF (compare with reference)

**Pre-requisites:**

1. A new Git repository for the Environment Instance exists in the project Git group.
2. GitLab project access token with required scopes is available.
3. GSF package manager is installed and working on the operator's machine.
4. Instance package image path for the chosen EnvGene version is known.
5. A reference Instance Repository structure for this version is defined.

**Trigger:**

Operator runs GSF on the local machine to initialize the Instance Repository:

```bash
git-system-follower install <path_to_instance_package_image> \
   -r <project_instance_repository_path> \
   -b <project_instance_repository_branch> \
   -t <gitlab_token>
```

**Steps:**

1. GSF connects to the target Instance Repository using the provided URL, branch, and token.
2. GSF pulls the instance package image and applies its contents to the repository (CI/CD configuration, initial folders, and configuration files).

**Results:**

1. Instance Repository is initialized with the EnvGene instance package for the selected version and is ready to be used for running EnvGene pipelines.

### UC-GSF-INST-2: Upgrade Instance Repository via GSF (compare with reference)

**Pre-requisites:**

1. Instance Repository already exists and contains a previous EnvGene instance package version.
2. GitLab token and required CI/CD variables are available.
3. GSF package manager is installed and working on the operator's machine.
4. Target EnvGene instance package image path is known.
5. A reference Instance Repository structure for the target EnvGene version is defined.

**Trigger:**

Operator runs GSF on the local machine to upgrade the Instance Repository:

```bash
git-system-follower install <path_to_instance_package_image> \
   -r <project_instance_repository_path> \
   -b <project_instance_repository_branch> \
   -t <gitlab_token>
```

**Steps:**

1. GSF connects to the existing Instance Repository and pulls the target instance package image.
2. GSF applies package changes on top of the existing repository contents (updates CI/CD configuration, adds new files, updates or removes outdated files).

**Results:**

1. Instance Repository is upgraded to the target EnvGene instance package version and matches the expected reference state.

