# BG Operations

- [BG Operations](#bg-operations)
  - [BG Operation in `bg_manage` EnvGene Job. Forward Flow](#bg-operation-in-bg_manage-envgene-job-forward-flow)
    - [init-domain](#init-domain)
    - [warmup](#warmup)
    - [promote](#promote)
    - [commit](#commit)
    - [rollback](#rollback)
  - [BG Operation in `bg_manage` EnvGene Job. Reverse Flow](#bg-operation-in-bg_manage-envgene-job-reverse-flow)
    - [reverse warmup](#reverse-warmup)
    - [reverse promote](#reverse-promote)
    - [reverse commit](#reverse-commit)
    - [reverse rollback](#reverse-rollback)

## BG Operation in `bg_manage` EnvGene Job. Forward Flow

The operations below describe the forward flow, where the peer namespace becomes candidate and then active.

### init-domain

**Pre-requisites:**

1. State files are not created

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `BG_STATE: {\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"idle\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: {\"BG_MANAGE\":true,\"BG_STATE\":{\"controllerNamespace\":\"<controller-ns>\",\"originNamespace\":{\"name\":\"<origin-ns>\",\"state\":\"active\",\"version\":\"<version>\"},\"peerNamespace\":{\"name\":\"<peer-ns>\",\"state\":\"idle\",\"version\":\"<version>\"},\"updateTime\":\"<timestamp>\"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-active` and `.peer-idle`

**Results:**

1. State files `.origin-active` and `.peer-idle` are created

### warmup

**Pre-requisites:**

1. State files `.origin-active` and `.peer-idle` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"candidate","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: {"BG_MANAGE":true,"BG_STATE":{"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"candidate","version":"<version>"},"updateTime":"<timestamp>"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Replaces the contents of the candidate namespace folder (peer) with the contents (including nested Applications) of the active namespace folder (origin), keeping only the candidate namespace `name` attribute
   3. Updates state files: Creates `.origin-active` and `.peer-candidate` in the Environment folder

**Results:**

1. Origin namespace folder (active) and peer namespace folder (candidate) have the same content
2. State files `.origin-active` and `.peer-candidate` are set in the Environment folder

### promote

**Pre-requisites:**

1. State files `.origin-active` and `.peer-candidate` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"legacy","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: {"BG_MANAGE":true,"BG_STATE":{"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"legacy","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-legacy` and `.peer-active` in the Environment folder

**Results:**

1. State files `.origin-legacy` and `.peer-active` are set in the Environment folder

### commit

**Pre-requisites:**

1. State files `.origin-legacy` and `.peer-active` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"idle","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: {"BG_MANAGE":true,"BG_STATE":{"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"idle","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-idle` and `.peer-active` in the Environment folder

**Results:**

1. State files `.origin-idle` and `.peer-active` are set in the Environment folder

### rollback

> [!Note]
> `rollback` operation has the same state transition as `commit` operation. The difference is semantic: `rollback` is used when reverting from a failed promotion, while `commit` is used after a successful promotion. Both operations result in the same final state: origin becomes idle and peer remains active.

**Pre-requisites:**

1. State files `.origin-legacy` and `.peer-active` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"idle","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: {"BG_MANAGE":true,"BG_STATE":{"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"idle","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-idle` and `.peer-active` in the Environment folder

**Results:**

1. State files `.origin-idle` and `.peer-active` are set in the Environment folder

## BG Operation in `bg_manage` EnvGene Job. Reverse Flow

Reverse flow operations are the inverse of forward flow operations. In reverse flow, the origin namespace becomes the candidate and then active.

### reverse warmup

**Pre-requisites:**

1. State files `.origin-active` and `.peer-idle` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"candidate","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_name>`
   2. `GH_ADDITIONAL_PARAMS: {"BG_MANAGE":true,"BG_STATE":{"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"candidate","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"active","version":"<version>"},"updateTime":"<timestamp>"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Replaces the contents of the candidate namespace folder (origin) with the contents (including nested Applications) of the active namespace folder (peer), keeping only the candidate namespace `name` attribute
   3. Updates state files: Creates `.origin-candidate` and `.peer-active` in the Environment folder

**Results:**

1. Origin namespace folder (candidate) and peer namespace folder (active) have the same content
2. State files `.origin-candidate` and `.peer-active` are set in the Environment folder

### reverse promote

**Pre-requisites:**

1. State files `.origin-candidate` and `.peer-active` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"legacy","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: {"BG_MANAGE":true,"BG_STATE":{"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"legacy","version":"<version>"},"updateTime":"<timestamp>"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-active` and `.peer-legacy` in the Environment folder

**Results:**

1. State files `.origin-active` and `.peer-legacy` are set in the Environment folder

### reverse commit

**Pre-requisites:**

1. State files `.origin-active` and `.peer-legacy` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"idle","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: {"BG_MANAGE":true,"BG_STATE":{"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"idle","version":"<version>"},"updateTime":"<timestamp>"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-active` and `.peer-idle` in the Environment folder

**Results:**

1. State files `.origin-active` and `.peer-idle` are set in the Environment folder

### reverse rollback

> [!Note]
> `reverse rollback` operation has the same state transition as `reverse commit` operation. The difference is semantic: `reverse rollback` is used when reverting from a failed reverse promotion, while `reverse commit` is used after a successful reverse promotion. Both operations result in the same final state: origin remains active and peer becomes idle.

**Pre-requisites:**

1. State files `.origin-active` and `.peer-legacy` exist

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Gitlab Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `BG_STATE: {"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"idle","version":"<version>"},"updateTime":"<timestamp>"}`
   3. `BG_MANAGE: true`
2. GitHub Instance pipeline is started with parameters:
   1. `ENV_NAMES: <env_names_separated_by_commas>`
   2. `GH_ADDITIONAL_PARAMS: {"BG_MANAGE":true,"BG_STATE":{"controllerNamespace":"<controller-ns>","originNamespace":{"name":"<origin-ns>","state":"active","version":"<version>"},"peerNamespace":{"name":"<peer-ns>","state":"idle","version":"<version>"},"updateTime":"<timestamp>"}}`

**Steps:**

1. EnvGene runs the pipeline with the `bg_manage` job:
   1. Validates states in `BG_STATE` against state files in the repository
   2. Updates state files: Creates `.origin-active` and `.peer-idle` in the Environment folder

**Results:**

1. State files `.origin-active` and `.peer-idle` are set in the Environment folder
