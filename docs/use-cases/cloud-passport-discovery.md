# Cloud Passport discovery use cases

- [Cloud Passport discovery use cases](#cloud-passport-discovery-use-cases)
  - [Overview](#overview)
  - [Use cases](#use-cases)
    - [UC-CPD-1: Cloud Passport discovered from Discovery pipeline](#uc-cpd-1-cloud-passport-discovered-from-discovery-pipeline)
    - [UC-CPD-2: Passport jobs skipped and env_builder fails](#uc-cpd-2-passport-jobs-skipped-and-env_builder-fails)
    - [UC-CPD-3: Pipeline generation fails when integration is missing](#uc-cpd-3-pipeline-generation-fails-when-integration-is-missing)
    - [UC-CPD-4: Pipeline generation fails when GET_PASSPORT and CRED_ROTATION_PAYLOAD are both set](#uc-cpd-4-pipeline-generation-fails-when-get_passport-and-cred_rotation_payload-are-both-set)

## Overview

Generate Cloud Passport files in the instance repository by triggering the external Discovery
repository and importing its artifacts.

These use cases cover the `trigger_passport` and `get_passport` jobs in the GitLab Instance
pipeline, and the case where passport jobs are skipped and `env_builder` fails. For passport
association during `env_builder`, see
[Cloud Passport association use cases](/docs/use-cases/cloud-passport.md).

## Use cases

### UC-CPD-1: Cloud Passport discovered from Discovery pipeline

**Pre-requisites:**

1. Instance repository and Discovery repository are initialised and follow the required layout
2. `/configuration/integration.yml` contains:

   ```yaml
   cp_discovery:
     gitlab:
       project: <discovery-repository>
       branch: <discovery-branch>
       token: envgen.creds.get(<discovery-cred-id>).secret
   ```

3. Credential for the Discovery repository token exists in `/configuration/credentials/credentials.yml`
4. Cluster folder exists at `/environments/<cluster>/`
5. Environment folder exists at `/environments/<cluster>/<env>/`
6. Kubeconfig is present at `/environments/<cluster>/kubeconfig`
7. Cloud Passport template is present at `/environments/<cluster>/<env>/cloud_template.yml`
8. `GITLAB_TOKEN` is set in the GitLab CI environment

**Trigger:**

GitLab Instance pipeline is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
GET_PASSPORT: true
```

**Steps:**

1. The `trigger_passport` job runs.
2. The `trigger_passport` job triggers the Discovery repository pipeline with `ENV_NAME=<cluster>/<env>`.
3. The `get_passport` job runs after the Discovery pipeline completes.
4. The `get_passport` job writes Cloud Passport files under `/environments/<cluster>/cloud-passport/`.
5. The `get_passport` job commits changes to the instance repository.

**Results:**

1. Cloud Passport file is created at `/environments/<cluster>/cloud-passport/<cluster>.yml`
2. Credential file is created at `/environments/<cluster>/cloud-passport/<cluster>-creds.yml`
3. `trigger_passport` job status is `success`
4. `get_passport` job status is `success`

---

### UC-CPD-2: Passport jobs skipped and env_builder fails

**Pre-requisites:**

1. Environment definition at `/environments/<cluster>/<env>/Inventory/env_definition.yml` contains:

   ```yaml
   inventory:
     cloudPassport: <cluster>
   ```

2. No Cloud Passport files exist under `/environments/<cluster>/cloud-passport/`
3. `/configuration/integration.yml` exists

**Trigger:**

GitLab Instance pipeline is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
GET_PASSPORT: false
ENV_BUILDER: true
```

> [!NOTE]
> `GET_PASSPORT` defaults to `false` when omitted.

**Steps:**

1. Pipeline generation completes without adding `trigger_passport` or `get_passport` jobs.
2. The `env_builder` job runs.
3. The `env_builder` job aborts because the Cloud Passport file referenced in `env_definition.yml`
   is missing.

**Results:**

1. Generated pipeline contains no `trigger_passport` job
2. Generated pipeline contains no `get_passport` job
3. `env_builder` job fails with an error that the Cloud Passport file was not found

---

### UC-CPD-3: Pipeline generation fails when integration is missing

**Pre-requisites:**

1. `/configuration/integration.yml` is missing
2. Cluster and environment folders exist under `/environments/<cluster>/<env>/`

**Trigger:**

GitLab Instance pipeline generation is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
GET_PASSPORT: true
```

**Steps:**

1. Pipeline generation runs validation before creating jobs.
2. Validation aborts because `/configuration/integration.yml` is missing when `GET_PASSPORT` is
   `true`.

**Results:**

1. Pipeline generation fails before any passport job is created
2. No `trigger_passport` or `get_passport` job appears in the generated pipeline

---

### UC-CPD-4: Pipeline generation fails when GET_PASSPORT and CRED_ROTATION_PAYLOAD are both set

**Pre-requisites:**

1. `/configuration/integration.yml` contains a `cp_discovery` block that passes schema validation
2. `CRED_ROTATION_PAYLOAD` is set to a non-empty JSON rotation payload

**Trigger:**

GitLab Instance pipeline generation is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
GET_PASSPORT: true
CRED_ROTATION_PAYLOAD: <rotation-json>
```

**Steps:**

1. Pipeline generation runs validation before creating jobs.
2. Validation aborts because `GET_PASSPORT` and `CRED_ROTATION_PAYLOAD` cannot be used in the
   same pipeline run.

**Results:**

1. Pipeline generation fails before any passport or credential rotation job is created
2. No `trigger_passport`, `get_passport`, or `credential_rotation` job appears in the generated
   pipeline
