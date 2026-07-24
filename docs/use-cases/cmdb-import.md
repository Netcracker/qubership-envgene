# CMDB import use cases

- [CMDB import use cases](#cmdb-import-use-cases)
  - [Overview](#overview)
  - [Credential management modes](#credential-management-modes)
    - [UC-CMDB-1: CMDB import with create](#uc-cmdb-1-cmdb-import-with-create)
    - [UC-CMDB-2: CMDB import with do_not_create](#uc-cmdb-2-cmdb-import-with-do_not_create)
    - [UC-CMDB-3: CMDB import with validate_only](#uc-cmdb-3-cmdb-import-with-validate_only)
    - [UC-CMDB-4: Placeholder credentials pass validation](#uc-cmdb-4-placeholder-credentials-pass-validation)

## Overview

These use cases cover `cmdb_import` for each `credential_management_mode` value.

## Credential management modes

### UC-CMDB-1: CMDB import with create

**Pre-requisites:**

1. Environment exists under `/environments/<cluster-name>/<env-name>/`.
2. `/configuration/config.yml` sets `credential_management_mode` to `create`, or omits the attribute (default is
   `create`).
3. `/environments/<cluster-name>/<env-name>/Credentials/credentials.yml` holds real secret values, not placeholders.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
CMDB_IMPORT: true
```

**Steps:**

1. The `cmdb_import` job runs.
2. Environment Instance data is exported to CMDB.
3. Credential objects are created in CMDB from `credentials.yml`.

**Results:**

1. The `cmdb_import` job completes with status SUCCESS.
2. Credential objects are created in CMDB.
3. Environment data is available in CMDB.

### UC-CMDB-2: CMDB import with do_not_create

**Pre-requisites:**

1. Environment exists under `/environments/<cluster-name>/<env-name>/`.
2. `/configuration/config.yml` contains:

   ```yaml
   credential_management_mode: do_not_create
   ```

3. `/environments/<cluster-name>/<env-name>/Credentials/credentials.yml` exists.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
CMDB_IMPORT: true
```

**Steps:**

1. The `cmdb_import` job runs.
2. Environment Instance data is exported to CMDB.

**Results:**

1. The `cmdb_import` job completes with status SUCCESS.
2. No credential objects are created in CMDB.
3. Environment data is available in CMDB.

### UC-CMDB-3: CMDB import with validate_only

**Pre-requisites:**

1. Environment exists under `/environments/<cluster-name>/<env-name>/`.
2. `/configuration/config.yml` contains:

   ```yaml
   credential_management_mode: validate_only
   ```

3. `/environments/<cluster-name>/<env-name>/Credentials/credentials.yml` contains placeholders (`envgeneNullValue`).
4. Every credential ID in `credentials.yml` already exists in CMDB.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
CMDB_IMPORT: true
```

**Steps:**

1. The `cmdb_import` job runs.
2. Credential IDs are validated against CMDB.
3. Environment Instance data is exported to CMDB.

**Results:**

1. The `cmdb_import` job completes with status SUCCESS.
2. No credential objects are created in CMDB.
3. Environment data is available in CMDB.

### UC-CMDB-4: Placeholder credentials pass validation

**Pre-requisites:**

1. Environment exists under `/environments/<cluster-name>/<env-name>/`.
2. `/configuration/config.yml` contains:

   ```yaml
   credential_management_mode: validate_only
   ```

3. `/environments/<cluster-name>/<env-name>/Credentials/credentials.yml` contains a placeholder credential, for
   example:

   ```yaml
   sample-cred:
     type: usernamePassword
     data:
       username: "envgeneNullValue"
       password: "envgeneNullValue"
   ```

4. The credential ID `sample-cred` already exists in CMDB.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
CMDB_IMPORT: true
```

**Steps:**

1. The `cmdb_import` job runs.
2. Credential validation accepts `envgeneNullValue` placeholders in `credentials.yml`.
3. Credential ID existence in CMDB is validated.
4. Environment Instance data is exported to CMDB.

**Results:**

1. The `cmdb_import` job completes with status SUCCESS.
2. Credential validation does not report `username or password is not set` or `secret is not set`.
3. No credential objects are created in CMDB.
4. Environment data is available in CMDB.
