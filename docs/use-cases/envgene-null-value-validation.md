# envgeneNullValue validation use cases

- [envgeneNullValue validation use cases](#envgenenullvalue-validation-use-cases)
  - [Overview](#overview)
  - [Validation execution](#validation-execution)
    - [UC-NVV-1: Unresolved parameter blocks pipeline](#uc-nvv-1-unresolved-parameter-blocks-pipeline)
    - [UC-NVV-2: Unresolved credential blocks pipeline](#uc-nvv-2-unresolved-credential-blocks-pipeline)
    - [UC-NVV-3: All values resolved](#uc-nvv-3-all-values-resolved)
    - [UC-NVV-4: Multiple unresolved values reported together](#uc-nvv-4-multiple-unresolved-values-reported-together)

## Overview

This document covers use cases for `envgeneNullValue` validation - the safety check that prevents
unresolved placeholder values from reaching deployment.

Validation runs at two pipeline stages - `generate_effective_set` and `cmdb_import` - and at each stage
covers two scopes: parameters (`deployParameters`, `e2eParameters`, `technicalConfigurationParameters`) and
credentials (`Credentials/credentials.yml`). Both stages emit identical log messages on failure. See the
[envgeneNullValue tutorial](/docs/tutorials/envgene-null-value.md#where-validation-happens) for the full
description.

In error messages shown below, `<object>` is the name of the Environment Instance object
containing the unresolved value.

## Validation execution

### UC-NVV-1: Unresolved parameter blocks pipeline

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. At least one value in `deployParameters`, `e2eParameters`, or
   `technicalConfigurationParameters` of any generated Environment Instance object equals
   `envgeneNullValue`, e.g.:

    ```yaml
    deployParameters:
      API_URL: envgeneNullValue
    ```

**Trigger:**

> [!NOTE]
> One of the following conditions must be met:

1. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `GENERATE_EFFECTIVE_SET: true`
2. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `CMDB_IMPORT: true`

**Steps:**

1. The `generate_effective_set` or `cmdb_import` job runs.
2. Parameter validation detects an unresolved `envgeneNullValue`.
3. The job aborts with a validation error.

**Results:**

1. The job fails with the message:

    ```text
    Error while validating parameters:
      <object>.deployParameters.API_URL - is not set
    ```

### UC-NVV-2: Unresolved credential blocks pipeline

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. At least one credential entry in
   `/environments/<cluster-name>/<env-name>/Credentials/credentials.yml` has unresolved secret
   material, e.g.:

    ```yaml
    dbaas-cluster-dba-cred:
      type: usernamePassword
      data:
        username: "envgeneNullValue" # FillMe
        password: "envgeneNullValue" # FillMe
    ```

**Trigger:**

> [!NOTE]
> One of the following conditions must be met:

1. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `GENERATE_EFFECTIVE_SET: true`
2. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `CMDB_IMPORT: true`

**Steps:**

1. The `generate_effective_set` or `cmdb_import` job runs.
2. Credential validation detects an unresolved `envgeneNullValue`.
3. The job aborts with a validation error.

**Results:**

1. The job fails with the message:

    ```text
    Error while validating credentials:
      credId: dbaas-cluster-dba-cred - username or password is not set
    ```

### UC-NVV-3: All values resolved

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. No parameter or credential value equals `envgeneNullValue` anywhere in the Environment Instance.

**Trigger:**

> [!NOTE]
> One of the following conditions must be met:

1. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `GENERATE_EFFECTIVE_SET: true`
2. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `CMDB_IMPORT: true`

**Steps:**

1. The `generate_effective_set` or `cmdb_import` job runs.
2. Validation finds no `envgeneNullValue` values in parameters or credentials.
3. The job proceeds with its remaining work.

**Results:**

1. Validation passes for both scopes (parameters and credentials).
2. The Effective Set is produced (for `generate_effective_set`) or the CMDB payload is pushed
   successfully (for `cmdb_import`).

### UC-NVV-4: Multiple unresolved values reported together

**Pre-requisites:**

1. Environment Instance is generated under `/environments/<cluster-name>/<env-name>/`.
2. Solution Descriptor exists at `/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml`.
3. AppDef and RegDef exist for each `app:ver` listed in the SD.
4. `/environments/<cluster-name>/<env-name>/Credentials/credentials.yml` contains multiple
   entries with unresolved secret material, e.g.:

    ```yaml
    dbaas-cluster-dba-cred:
      type: usernamePassword
      data:
        username: "envgeneNullValue" # FillMe
        password: "envgeneNullValue" # FillMe
    consul-admin-cred:
      type: secret
      data:
        secret: "envgeneNullValue" # FillMe
    ```

**Trigger:**

> [!NOTE]
> One of the following conditions must be met:

1. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `GENERATE_EFFECTIVE_SET: true`
2. Instance pipeline (GitLab or GitHub) is started with parameters:
    1. `ENV_NAMES: <cluster-name>/<env-name>`
    2. `CMDB_IMPORT: true`

**Steps:**

1. The `generate_effective_set` or `cmdb_import` job runs.
2. Credential validation evaluates all entries rather than failing on the first violation.
3. Every unresolved `envgeneNullValue` value is included in a single aggregated error.
4. The job aborts with the aggregated validation error.

**Results:**

1. The job fails with a single error message listing every unresolved field:

    ```text
    Error while validating credentials:
      credId: dbaas-cluster-dba-cred - username or password is not set
      credId: consul-admin-cred - secret is not set
    ```
