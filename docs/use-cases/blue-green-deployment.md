# Blue-Green Deployment Use Cases

- [Blue-Green Deployment Use Cases](#blue-green-deployment-use-cases)
  - [Overview](#overview)
    - [UC-BG-1: Init Domain](#uc-bg-1-init-domain)
    - [UC-BG-2: Warmup](#uc-bg-2-warmup)
    - [UC-BG-3: Promote](#uc-bg-3-promote)
    - [UC-BG-4: Commit](#uc-bg-4-commit)
    - [UC-BG-5: Rollback](#uc-bg-5-rollback)
    - [UC-BG-6: Reverse Warmup](#uc-bg-6-reverse-warmup)
    - [UC-BG-7: Reverse Promote](#uc-bg-7-reverse-promote)
    - [UC-BG-8: Reverse Commit](#uc-bg-8-reverse-commit)
    - [UC-BG-9: Reverse Rollback](#uc-bg-9-reverse-rollback)

## Overview

This document covers use cases for [Blue-Green Deployment](/docs/features/blue-green-deployment.md) operations performed by the `bg_manage` job in EnvGene pipeline. These operations manage state transitions between origin and peer namespaces in Blue-Green Domains.

### UC-BG-1: Init Domain

**Pre-requisites:**

1. State files are not created

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `BG_STATE: {\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"idle\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"idle\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-active` and `.peer-idle`

**Results:**

1. State files `.origin-active` and `.peer-idle` are created

### UC-BG-2: Warmup

**Pre-requisites:**

1. State files `.origin-active` and `.peer-idle` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"candidate","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"candidate\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Replaces the contents of the candidate namespace folder (peer) with the contents (including nested Applications) of the active namespace folder (origin), keeping only the candidate namespace `name` attribute
   3. Updates the Environment Inventory: Copies `envTemplate.bgArtifacts.origin` → `envTemplate.bgArtifacts.peer`
   4. Updates state files: Creates `.origin-active` and `.peer-candidate` in the Environment folder

**Results:**

1. Origin namespace folder (active) and peer namespace folder (candidate) have the same content
2. State files `.origin-active` and `.peer-candidate` are set in the Environment folder

### UC-BG-3: Promote

**Pre-requisites:**

1. State files `.origin-active` and `.peer-candidate` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"legacy","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"legacy\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-legacy` and `.peer-active` in the Environment folder

**Results:**

1. State files `.origin-legacy` and `.peer-active` are set in the Environment folder

### UC-BG-4: Commit

**Pre-requisites:**

1. State files `.origin-legacy` and `.peer-active` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"idle","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"idle\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-idle` and `.peer-active` in the Environment folder

**Results:**

1. State files `.origin-idle` and `.peer-active` are set in the Environment folder

### UC-BG-5: Rollback

> [!Note]
> `rollback` operation has the same state transition as `commit` operation. The difference is semantic: `rollback` is used when reverting from a failed promotion, while `commit` is used after a successful promotion. Both operations result in the same final state: origin becomes idle and peer remains active.

**Pre-requisites:**

1. State files `.origin-legacy` and `.peer-active` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"idle","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"idle\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-idle` and `.peer-active` in the Environment folder

**Results:**

1. State files `.origin-idle` and `.peer-active` are set in the Environment folder

### UC-BG-6: Reverse Warmup

**Pre-requisites:**

1. State files `.origin-active` and `.peer-idle` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"candidate","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"candidate\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Replaces the contents of the candidate namespace folder (origin) with the contents (including nested Applications) of the active namespace folder (peer), keeping only the candidate namespace `name` attribute
   3. Updates the Environment Inventory: Copies `envTemplate.bgArtifacts.peer` → `envTemplate.bgArtifacts.origin`
   4. Updates state files: Creates `.origin-candidate` and `.peer-active` in the Environment folder

**Results:**

1. Origin namespace folder (candidate) and peer namespace folder (active) have the same content
2. State files `.origin-candidate` and `.peer-active` are set in the Environment folder

### UC-BG-7: Reverse Promote

**Pre-requisites:**

1. State files `.origin-candidate` and `.peer-active` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"legacy","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"legacy\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-active` and `.peer-legacy` in the Environment folder

**Results:**

1. State files `.origin-active` and `.peer-legacy` are set in the Environment folder

### UC-BG-8: Reverse Commit

**Pre-requisites:**

1. State files `.origin-active` and `.peer-legacy` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"idle","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"idle\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-active` and `.peer-idle` in the Environment folder

**Results:**

1. State files `.origin-active` and `.peer-idle` are set in the Environment folder

### UC-BG-9: Reverse Rollback

> [!Note]
> `reverse rollback` operation has the same state transition as `reverse commit` operation. The difference is semantic: `reverse rollback` is used when reverting from a failed reverse promotion, while `reverse commit` is used after a successful reverse promotion. Both operations result in the same final state: origin remains active and peer becomes idle.

**Pre-requisites:**

1. State files `.origin-active` and `.peer-legacy` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. GitLab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"idle","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: "BG_MANAGE=true,BG_STATE={\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"idle\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}"`

**Steps:**

1. The `bg_manage` job runs in the pipeline:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-active` and `.peer-idle` in the Environment folder

**Results:**

1. State files `.origin-active` and `.peer-idle` are set in the Environment folder
