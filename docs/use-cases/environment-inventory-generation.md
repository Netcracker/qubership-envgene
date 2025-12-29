- [Environment Inventory Generation Use Cases](#environment-inventory-generation-use-cases)
  - [Overview](#overview-1)
  - [Environment Inventory: env_definition.yml](#environment-inventory-env_definitionyml)
    - [UC-EINV-ED-1: Create env_definition.yml (CREATE)](#uc-einv-ed-1-create-env_definitionyml-create)
    - [UC-EINV-ED-2: Update env_definition.yml (OVERRIDE)](#uc-einv-ed-2-update-env_definitionyml-override)
    - [UC-EINV-ED-3: Upsert env_definition.yml (UPSERT)](#uc-einv-ed-3-upsert-env_definitionyml-upsert)

  - [Environment Inventory: Paramsets](#environment-inventory-paramsets)
    - [UC-EINV-PS-1: Create Paramset File (CREATE)](#uc-einv-ps-1-create-paramset-file-create)
    - [UC-EINV-PS-2: Update Paramset File (OVERRIDE)](#uc-einv-ps-2-update-paramset-file-override)
    - [UC-EINV-PS-3: Upsert Paramset File (UPSERT)](#uc-einv-ps-3-upsert-paramset-file-upsert)

  - [Environment Inventory: Resource Profile Overrides](#environment-inventory-resource-profile-overrides)
    - [UC-EINV-RP-1: Create Resource Profile Override File (CREATE)](#uc-einv-rp-1-create-resource-profile-override-file-create)
    - [UC-EINV-RP-2: Update Resource Profile Override File (OVERRIDE)](#uc-einv-rp-2-update-resource-profile-override-file-override)
    - [UC-EINV-RP-3: Upsert Resource Profile Override File (UPSERT)](#uc-einv-rp-3-upsert-resource-profile-override-file-upsert)

 - [Environment Inventory: Credentials](#environment-inventory-credentials)
    - [UC-EINV-CR-1: Create Credentials File (CREATE)](#uc-einv-cr-1-create-credentials-file)
    - [UC-EINV-CR-2: Update Credentials File (OVERRIDE)](#uc-einv-cr-2-update-credentials-file)
    - [UC-EINV-CR-3: Upsert Credentials File (UPSERT)](#uc-einv-cr-3-upsert-credentials-file)

- [Environment Inventory: Template Version Mode](#environment-inventory-template-version-mode)
  - [Overview](#overview-2)
  - [UC-EINV-TV-1: Apply Template Version for Current Run Only (APPLY_ONLY)](#uc-einv-tv-1-apply-template-version-for-current-run-only-apply_only)

    
## Overview

    This document covers use cases for Environment Inventory Generation — the process of creating, overriding, or upserting env_definition.yml, as well as generating paramsets, resource_profiles, and credentials via ENV_INVENTORY_CONTENT.

### UC-EINV-ED-1: Create env_definition.yml (CREATE)

**Pre-requisites:**
1. The Environment Inventory file does not exist:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

**Trigger:**
Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <env-name>`
2. `ENV_TEMPLATE_VERSION: <value>`
3. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**
1. The `env_inventory_generation` job runs in the pipeline:
   1. Parses `ENV_INVENTORY_CONTENT`.
   2. Validates the payload structure:
        - `env_definition` section exists
        - `env_definition.$action` and `env_definition.$content` exist
        - `$action` value is a valid enum
        - `env_definition.$content` matches the `env_definition` schema
   3. Validates the action:
        - If `$action == create` → step 4.
        - If `$action == override` → see [UC-EINV-ED-2](#uc-einv-ed-2-update-env_definitionyml-override).
     - If `$action == upsert` → see [UC-EINV-ED-3](#uc-einv-ed-3-upsert-env_definitionyml-upsert).
        - If `$action` is not one of `{ create, override, upsert }` → the job fails with a validation error.
   4. Checks that the target file does not exist:
      - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
      - if the file exists → the job fails (CREATE is not allowed when inventory already exists).
   5. Builds the content of `env_definition.yml`:
      - extracts data from `env_definition.$content`
   6. Creates directories if missing:
      - `/environments/<cluster-name>/<env-name>/Inventory/`
   7. Creates the file:
      - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
      - with the content from step 1.5
2. The `git_commit` job runs:
   1. Commits the created `env_definition.yml` to the Instance repository.

**Results:**
1. Environment Inventory file is created:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
2. The changes are committed to the Instance repository by the `git_commit` job.

### UC-EINV-ED-2: OVERRIDE env_definition.yml (OVERRIDE)

**Pre-requisites:**
1. Environment Inventory file exists:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

**Trigger:**
Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**
1. The `env_inventory_generation` job runs in the pipeline:
   1. The job parses `ENV_INVENTORY_CONTENT`.
   2. The job validates the payload structure:
      - presence of the `env_definition` section
      - presence of `env_definition.$action` and `env_definition.$content`
      - `$action` has a valid enum value
      - `env_definition.$content` matches the `env_definition` schema
   3. The job checks `env_definition.$action`:
      - if `$action == override` → step 4..
      - If `$action == create` → see [UC-EINV-ED-1](#uc-einv-ed-1-create-env_definitionyml-create).
      - If `$action == upsert` → see [UC-EINV-ED-3](#uc-einv-ed-3-upsert-env_definitionyml-upsert).
        - If `$action` is not one of `{ create, override, upsert }` → the job fails with a validation error.
   4. The job checks that the file exists:
      - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
      - if the file does not exist → the job fails (cannot OVERRIDE a non-existing inventory).
   5. The job applies OVERRIDE logic to the existing inventory using `env_definition.$content`:
      - all fields provided in `$content` overwrite existing values
      - nested sections provided in `$content` replace the corresponding sections entirely
      - fields not specified in `$content` are removed
   6. The job saves the updated file:
      - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
2. The `git_commit` job runs:
   1. The job commits the updated `env_definition.yml` into the Instance repository.

**Results:**
1. The file is updated:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
2. Changes are applied in OVERRIDE mode:
   - sections provided in `$content` are replaced entirely
3. Changes are committed by the `git_commit` job


### UC-EINV-ED-3: Upsert env_definition.yml (UPSERT)

**Pre-requisites:**
1. The Environment Inventory file does not exist, or exists

**Trigger:**
Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`
3. `ENV_TEMPLATE_VERSION: <value>`

**Steps:**
1. The `env_inventory_generation` job runs in the pipeline:
   1. The job parses `ENV_INVENTORY_CONTENT`.
   2. The job validates the payload structure:
      - presence of `env_definition`
      - presence of `env_definition.$action` and `env_definition.$content`
      - `$action` has a valid enum value
      - `env_definition.$content` matches the `env_definition` schema
   3. The job checks `env_definition.$action`:
      - if `$action == upsert` → the step 4.
      - if `$action == override` see [UC-EINV-ED-2](#uc-einv-ed-2-update-env_definitionyml-override).
      - If `$action == create` → see [UC-EINV-ED-1](#uc-einv-ed-1-create-env_definitionyml-create).
      - If `$action` is not one of `{ create, override, upsert }` → the job fails with a validation error.
   4. The job checks if the Environment Inventory file exists:
      - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
   5. Decision logic:
      - If the file `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` **exists** → follow **[UC-EINV-ED-2: Update existing env_definition.yml (OVERRIDE)](#uc-einv-ed-2-update-existing-env_definitionyml-override)**
      - If the file `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` **does not exist** → follow **[UC-EINV-ED-1: Create env_definition.yml (CREATE)](#uc-einv-ed-1-create-env_definitionyml-create)**

**Results:**
1. If the file did not exist: `env_definition.yml` file is created
2. If the file existed: `env_definition.yml` file is fully replaced


### UC-EINV-PS-1: Create Paramset File (CREATE)

**Pre-requisites:**

1. The Paramset file does not exist in the target directory (based on `$place`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `paramsets[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == create`
      - `$place` is one of `{ env, cluster, site }`
      - `$content` matches Paramset schema
   3. Extracts `<paramset-name>` from `$content.name`.
   4. Resolves the target file path based on `$place`:
      - `$place=env` → `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml`
      - `$place=cluster` → `/environments/<cluster-name>/Inventory/parameters/<paramset-name>.yml`
      - `$place=site` → `/environments/Inventory/parameters/<paramset-name>.yml`
   5. Validates that the target file does not exist:
      - If file exists → the job fails with validation error.
   6. Creates the target directory `parameters/` if it does not exist.
   7. Creates the file `<paramset-name>.yml` with content from `paramsets[].$content`.
2. The `git_commit` job runs:
   1. Commits the created Paramset file into the Instance repository.

**Results:**

1. A Paramset file is created at the resolved path (based on `$place`), for example:
   - `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml`
2. Changes are committed by the `git_commit` job.


### UC-EINV-PS-2: Update Paramset File (OVERRIDE)

**Pre-requisites:**

1. The Paramset file  exist in the target directory (based on `$place`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `paramsets[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == override`
      - `$place` is one of `{ env, cluster, site }`
      - `$content` matches Paramset schema
   3. Extracts `<paramset-name>` from `$content.name`.
   4. Resolves the target file path based on `$place`:
      - `$place=env` → `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml`
      - `$place=cluster` → `/environments/<cluster-name>/Inventory/parameters/<paramset-name>.yml`
      - `$place=site` → `/environments/Inventory/parameters/<paramset-name>.yml`
   5. Validates that the target file exists:
      - If file does not exist → the job fails with validation error (override is not possible for a missing file).
   6. Applies OVERRIDE logic:
      - The target file content is fully replaced with `paramsets[].$content`.
   7. Saves the updated Paramset file.
2. The `git_commit` job runs:
   1. Commits the updated Paramset file into the Instance repository.

**Results:**

1. The Paramset file is updated at the resolved path, for example:
   - `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml`
2. Changes are committed by the `git_commit` job.


### UC-EINV-PS-3: Upsert Paramset File (UPSERT)

**Pre-requisites:**

1. The Paramset file with the same `<paramset-name>`  exist or doest exist, in the target directory (based on `$place`)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `paramsets[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == upsert`
      - `$place` is one of `{ env, cluster, site }`
      - `$content` matches Paramset schema
   3. Extracts `<paramset-name>` from `$content.name`.
   4. Resolves the target file path based on `$place`:
      - `$place=env` → `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml`
      - `$place=cluster` → `/environments/<cluster-name>/Inventory/parameters/<paramset-name>.yml`
      - `$place=site` → `/environments/Inventory/parameters/<paramset-name>.yml`
   5. Scenario selection logic:
      - If the target file **exists** → follow **[UC-EINV-PS-2: Update Paramset File (OVERRIDE)](#uc-einv-ps-2-update-paramset-file-override)**
      - If the target file **does not exist** → follow **[UC-EINV-PS-1: Create Paramset File (CREATE)](#uc-einv-ps-1-create-paramset-file-create)**


**Results:**

1. If the file did not exist: Paramset file is created at the resolved path.
2. If the file existed: Paramset file is replaced with the content from `$content`.


### UC-EINV-RP-1: Create Resource Profile Override File (CREATE)

**Pre-requisites:**

1. The target override file does not exist in the directory resolved from `$place`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `resource_profiles[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == create`
      - `$place` is one of `{ env, cluster, site }`
      - `$content` matches Resource Profile Override schema
   3. Extracts `<override-name>` from `$content.name`.
   4. Resolves the target file path based on `$place`:
      - `$place=env` → `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<override-name>.yml`
      - `$place=cluster` → `/environments/<cluster-name>/resource_profiles/<override-name>.yml`
      - `$place=site` → `/environments/resource_profiles/<override-name>.yml`
   5. Validates that the target file does not exist:
      - If file exists → the job fails with validation error (duplicate create is not allowed).
   6. Creates the target directory `resource_profiles` if it does not exist.
   7. Creates the file `<override-name>.yml` with content from `resource_profiles[].$content`.
2. The `git_commit` job runs:
   1. Commits the created override file into the Instance repository.

**Results:**

1. A Resource Profile Override file is created at the resolved path, for example:
   - `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<override-name>.yml`
3. Changes are committed by the `git_commit` job.


### UC-EINV-RP-2: Update Resource Profile Override File (OVERRIDE)

**Pre-requisites:**

1. The target file `<override-name>.yml` exists in the directory resolved from `$place`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `resource_profiles[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == override`
      - `$place` is one of `{ env, cluster, site }`
      - `$content` matches Resource Profile Override schema
   3. Extracts `<override-name>` from `$content.name`.
   4. Resolves the target file path based on `$place`:
      - `$place=env` → `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<override-name>.yml`
      - `$place=cluster` → `/environments/<cluster-name>/resource_profiles/<override-name>.yml`
      - `$place=site` → `/environments/resource_profiles/<override-name>.yml`
   5. Validates that the target file exists:
      - If file does not exist → the job fails with validation error (override is not possible for a missing file).
   6. Applies OVERRIDE logic:
      - The target file content is fully replaced with `resource_profiles[].$content`.
   7. Saves the updated override file.
2. The `git_commit` job runs:
   1. Commits the updated override file  into the Instance repository.

**Results:**

1. The Resource Profile Override file is fully replaced at the resolved path, for example:
   - `/.../resource_profiles/<override-name>.yml`
3. Changes are committed by the `git_commit` job.


### UC-EINV-RP-3: Upsert Resource Profile Override File (UPSERT)

**Pre-requisites:**

1. 1. The Profile Override File does not exist or exist in the target directory (based on `$place`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates `resource_profiles[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == upsert`
      - `$place` is one of `{ env, cluster, site }`
      - `$content` matches Resource Profile Override schema
   3. Extracts `<override-name>` from `$content.name`.
   4. Resolves the target file path based on `$place`:
      - `$place=env` → `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<override-name>.yml`
      - `$place=cluster` → `/environments/<cluster-name>/resource_profiles/<override-name>.yml`
      - `$place=site` → `/environments/resource_profiles/<override-name>.yml`
   5. Scenario selection logic:
      - If the target file **exists** → follow **[UC-EINV-RP-2: Update Resource Profile Override File (OVERRIDE)](#uc-einv-rp-2-update-resource-profile-override-file-override)**
      - If the target file **does not exist** → follow **[UC-EINV-RP-1: Create Resource Profile Override File (CREATE)](#uc-einv-rp-1-create-resource-profile-override-file-create)**

**Results:**

1. If the file did not exist: Resource Profile Override file is created at the resolved path.
2. If the file existed: Resource Profile Override file is fully replaced with the content from `$content`

### UC-EINV-CR-1: Create Credentials File (CREATE) 

**Pre-requisites:**

1. Target credentials file does not exist

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `credentials[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == create`
      - `$place == env`
      - `$content` matches credentials schema (Credential objects map)
   3. Resolves target credentials file path based on `$place`:
      - `$place=env` → `/environments/<cluster-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml`
   4. Validates the target file does not exist:
      - If the file exists → the job fails with validation error (duplicate create is not allowed).
   5. Creates directory if it does not exist:
      - `/environments/<cluster-name>/<env-name>/Inventory/credentials/`
   6. Creates credentials file:
      - `inventory_generation_creds.yml`
      - Writes content from `credentials[].$content`
2. The `git_commit` job runs:
   1. Commits created credentials file and updated `env_definition.yml` into the Instance repository.

**Results:**

1. Credentials file is created:
   - `/environments/<cluster-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml`
3. Changes are committed by the `git_commit` job.


---

### UC-EINV-CR-2: Update Credentials File (OVERRIDE) 

**Pre-requisites:**

1. Target credentials file exists

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `credentials[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == override`
      - `$place == env`
      - `$content` matches credentials schema (Credential objects map)
   3. Resolves credentials file path:
      - `/environments/<cluster-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml`
   4. Validates the target file exists:
      - If the file does not exist → the job fails with validation error (override is not possible for missing file).
   5. Applies OVERRIDE logic:
      - Fully replaces credentials file content with `credentials[].$content`
2. The `git_commit` job runs:
   1. Commits updated credentials file  into the Instance repository.

**Results:**

1. Credentials file is fully replaced
3. Changes are committed by the `git_commit` job.


---

### UC-EINV-CR-3: Upsert Credentials File (UPSERT) 

**Pre-requisites:**
1. Target credentials file does not exist or exist

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `ENV_INVENTORY_CONTENT: <payload>`

**Steps:**

1. The `env_inventory_generation` job runs in the pipeline:
   1. Reads and parses `ENV_INVENTORY_CONTENT`.
   2. Validates the `credentials[]` item:
      - `$action`, `$place`, `$content` are present
      - `$action == upsert`
      - `$place == env`
      - `$content` matches credentials schema (Credential objects map)
   3. Resolves credentials file path:
      - `/environments/<cluster-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml`
   4. Scenario selection logic:
      - If the credentials file exists → follow [UC-EINV-CR-2: Update Credentials File (OVERRIDE) ](#uc-einv-cr-2-update-credentials-file-override)
      - If the credentials file does not exist → follow [UC-EINV-CR-1: Create Credentials File (CREATE)](#uc-einv-cr-1-create-credentials-file-create)


**Results:**

1. If the file did not exist: credentials file is created
2. If the file existed: credentials file is fully replaced

---

### UC-EINV-TV-1: Apply Template Version for Current Run Only (APPLY_ONLY)

**Pre-requisites:**

1. Instance repository is writable (pipeline can commit changes).
2. Target environment is identified by `ENV_NAMES: <cluster-name>/<env-name>`.
3. Environment Inventory exists:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
4. `env_definition.yml` already contains a baseline template artifact (for example a SNAPSHOT):
   ```yaml
   envTemplate:
     artifact: "telus-env-template:master-SNAPSHOT"

**Trigger**

Instance pipeline (GitLab or GitHub) is started with parameters:
1. ENV_NAMES: <cluster-name>/<env-name>
2. ENV_TEMPLATE_VERSION: <application:version>
3. ENV_TEMPLATE_VERSION_MODE: APPLY_ONLY

**Steps:**
1. The job parses ENV_TEMPLATE_VERSION_MODE:
    1. If the value is APPLY_ONLY → proceed to the next steps.
    2. If the value is not APPLY_ONLY → execute the current logic (system update Environment Template version in the Environment Inventory. System overrides `envTemplate.templateArtifact.artifact.version` OR `envTemplate.artifact at /environments/<ENV_NAME>/Inventory/env_definition.yml`).
3. If ENV_TEMPLATE_VERSION_MODE=APPLY_ONLY, the job applies the template version only for the current run:
4. The job does not update envTemplate.templateArtifact.artifact.version or envTemplate.artifact in `/environments/<ENV_NAME>/Inventory/env_definition.yml`
5. After successful execution, the job records the applied version into:
`generatedVersions.generateEnvironmentLatestVersion: "<ENV_TEMPLATE_VERSION>"`
The git_commit job runs:

**Results:**

1.The Environment Inventory file is not modified: `/environments/<ENV_NAME>/Inventory/env_definition.yml`, `envTemplate.templateArtifact.artifact.version` / `envTemplate.artifact` remain unchanged.

2.The applied template version is recorded in the Environment Inventory under:
`generatedVersions.generateEnvironmentLatestVersion`: "<ENV_TEMPLATE_VERSION>" (committed if the pipeline commits inventory changes).