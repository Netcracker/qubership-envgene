# envgeneNullValue Validation Use Cases

- [envgeneNullValue Validation Use Cases](#envgenenullvalue-validation-use-cases)
  - [Overview](#overview)
    - [UC-NVV-1: Unresolved parameter at `generate_effective_set`](#uc-nvv-1-unresolved-parameter-at-generate_effective_set)
    - [UC-NVV-2: Unresolved credential at `generate_effective_set`](#uc-nvv-2-unresolved-credential-at-generate_effective_set)
    - [UC-NVV-3: Unresolved parameter at `cmdb_import`](#uc-nvv-3-unresolved-parameter-at-cmdb_import)
    - [UC-NVV-4: Unresolved credential at `cmdb_import`](#uc-nvv-4-unresolved-credential-at-cmdb_import)
    - [UC-NVV-5: All values resolved](#uc-nvv-5-all-values-resolved)

## Overview

This document covers use cases for `envgeneNullValue` validation — the safety check that prevents
unresolved placeholder values from reaching deployment.

Validation runs at two pipeline stages — `generate_effective_set` and `cmdb_import` — and at each stage
covers two scopes: parameters (`deployParameters`, `e2eParameters`, `technicalConfigurationParameters`) and
credentials (`Credentials/credentials.yml`). Both stages emit identical log messages on failure. See the
[envgeneNullValue tutorial](/docs/tutorials/envgene-null-value.md#where-validation-happens) for the full
description.

### UC-NVV-1: Unresolved parameter at `generate_effective_set`

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. At least one parameter in a generated Cloud or Namespace YAML equals `envgeneNullValue`, e.g.:

    ```yaml
    deployParameters:
      API_URL: envgeneNullValue
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
    1. Reads the existing Cloud and Namespace YAMLs from the Environment Instance.
    2. Iterates over `deployParameters`, `e2eParameters`, and `technicalConfigurationParameters`
       of each entity.
    3. Detects a value equal to `envgeneNullValue`.
    4. Aborts with a validation error.

**Results:**

1. The job fails with the message:

    ```text
    Error while validating parameters:
      <entity>.deployParameters.API_URL - is not set
    ```

2. No Effective Set is produced.
3. Deployment is blocked.

### UC-NVV-2: Unresolved credential at `generate_effective_set`

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. At least one credential entry in `/environments/<cluster-name>/<env-name>/Credentials/credentials.yml`
   has unresolved secret material, e.g.:

    ```yaml
    dbaas-cluster-dba-cred:
      type: usernamePassword
      data:
        username: "envgeneNullValue" # FillMe
        password: "envgeneNullValue" # FillMe
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
    1. Reads `Credentials/credentials.yml`.
    2. For each credential entry, checks the secret material against `envgeneNullValue`
       (`username`/`password` for `usernamePassword`, `secret` for `secret`, `secretId` for `vault`).
    3. Aborts with a validation error.

**Results:**

1. The job fails with the message:

    ```text
    Error while validating credentials:
      credId: dbaas-cluster-dba-cred - username or password is not set
    ```

2. No Effective Set is produced.
3. Deployment is blocked.

### UC-NVV-3: Unresolved parameter at `cmdb_import`

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. At least one parameter in a generated Cloud or Namespace YAML equals `envgeneNullValue`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CMDB_IMPORT: true`

**Steps:**

1. The `cmdb_import` job runs in the pipeline:
    1. Prepares the CMDB payload from the existing Cloud and Namespace YAMLs.
    2. Iterates over `deployParameters`, `e2eParameters`, and `technicalConfigurationParameters`.
    3. Detects a value equal to `envgeneNullValue`.
    4. Aborts with a validation error.

**Results:**

1. The job fails with the message:

    ```text
    Error while validating parameters:
      <entity>.deployParameters.API_URL - is not set
    ```

2. Nothing is pushed to the CMDB.
3. Deployment is blocked.

### UC-NVV-4: Unresolved credential at `cmdb_import`

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. At least one credential entry in `Credentials/credentials.yml` has unresolved secret material.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CMDB_IMPORT: true`

**Steps:**

1. The `cmdb_import` job runs in the pipeline:
    1. Reads `Credentials/credentials.yml`.
    2. For each credential entry, checks the secret material against `envgeneNullValue`.
    3. Aborts with a validation error.

**Results:**

1. The job fails with the message:

    ```text
    Error while validating credentials:
      credId: dbaas-cluster-dba-cred - username or password is not set
    ```

2. Nothing is pushed to the CMDB.
3. Deployment is blocked.

### UC-NVV-5: All values resolved

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. No parameter or credential value equals `envgeneNullValue` anywhere in the Environment Instance.

**Trigger:**

> [!Note]
> One of the following conditions must be met:

1. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `GENERATE_EFFECTIVE_SET: true`
2. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `CMDB_IMPORT: true`

**Steps:**

1. The `generate_effective_set` or `cmdb_import` job runs in the pipeline:
    1. Iterates over parameter maps and credentials.
    2. Finds no `envgeneNullValue` values.
    3. Proceeds with the rest of the job.

**Results:**

1. Validation passes for both scopes (parameters and credentials).
2. The Effective Set is produced (for `generate_effective_set`) or the CMDB payload is pushed
   successfully (for `cmdb_import`).
