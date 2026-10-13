# Registry discovery use cases

- [Registry discovery use cases](#registry-discovery-use-cases)
  - [Overview](#overview)
  - [Use cases](#use-cases)
    - [UC-RD-1: Artifact Definition discovered from CMDB](#uc-rd-1-artifact-definition-discovered-from-cmdb)
    - [UC-RD-2: registry_discovery job is not added to pipeline](#uc-rd-2-registry_discovery-job-is-not-added-to-pipeline)
    - [UC-RD-3: Discovery forced when local definition exists](#uc-rd-3-discovery-forced-when-local-definition-exists)
    - [UC-RD-4: Pipeline generation fails when discovery disabled](#uc-rd-4-pipeline-generation-fails-when-discovery-disabled)
    - [UC-RD-5: Job runs but runtime discovery is skipped (invalid AppVer)](#uc-rd-5-job-runs-but-runtime-discovery-is-skipped-invalid-appver)
    - [UC-RD-6: CMDB export failure during discovery](#uc-rd-6-cmdb-export-failure-during-discovery)

## Overview

Discover Artifact Definitions from CMDB when they are missing locally in the instance repository.

These use cases cover the `registry_discovery` job in the EnvGene Instance pipeline.

## Use cases

### UC-RD-1: Artifact Definition discovered from CMDB

**Pre-requisites:**

1. `/configuration/config.yml` contains:

   ```yaml
   artifact_definitions_discovery_mode: auto
   ```

2. Artifact Definition for `env-template` is absent under `/configuration/artifact_definitions/`
3. Environment Instance exists at `/environments/<cluster>/<env>/`
4. Environment definition contains `envTemplate.artifact: env-template:1.0.0` (AppVer format)
5. Environment definition contains `inventory.deployer` referencing a deployer key
6. Deployer configuration exists at `/configuration/deployer.yml` or an environment-level deployer file
7. CMDB holds application definition metadata for `env-template` with a registry reference
8. CMDB holds registry metadata for the referenced registry

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
```

Optional variant - template name from pipeline parameter (AppVer, takes priority when value contains `:`):

```yaml
ENV_TEMPLATE_VERSION: custom-template:2.1.0
```

**Steps:**

1. The `registry_discovery` job runs.
2. The job writes an Artifact Definition for the resolved template under `/configuration/artifact_definitions/`.
3. The job updates registry credentials under `/configuration/credentials/` when a matching entry was absent before
   discovery.

**Results:**

1. Artifact Definition is created at `/configuration/artifact_definitions/<template_name>.yml` or `.yaml`
2. Registry credential entry exists in `/configuration/credentials/credentials.yml` when it was absent before
   discovery
3. Job status is `success`

---

### UC-RD-2: registry_discovery job is not added to pipeline

**Pre-requisites:**

1. Environment Instance exists at `/environments/<cluster>/<env>/` for variants that require it

**Trigger:**

Instance pipeline (GitLab or GitHub) generation is started. One of the following conditions must be met:

```yaml
# Variant A - ENV_BUILDER disabled
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: false
ENV_TEMPLATE_TEST: false

# Variant B - template test mode
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: true

# Variant C - auto mode, local definition exists (AppVer template)
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
# config: artifact_definitions_discovery_mode: auto
# file exists: /configuration/artifact_definitions/env-template.yaml

# Variant D - false mode, local definition exists (AppVer template)
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
# config: artifact_definitions_discovery_mode: false
# file exists: /configuration/artifact_definitions/env-template.yaml

# Variant E - no template source
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
# no env definition, ENV_TEMPLATE_VERSION not set or without ":"

# Variant F - GAV format only (envTemplate.templateArtifact, no envTemplate.artifact)
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
# ENV_TEMPLATE_VERSION not set or without ":"
```

**Steps:**

1. Pipeline generation completes for the active variant without adding a `registry_discovery` job.

**Results:**

1. Generated pipeline contains no `registry_discovery` job

---

### UC-RD-3: Discovery forced when local definition exists

**Pre-requisites:**

1. `/configuration/config.yml` contains:

   ```yaml
   artifact_definitions_discovery_mode: true
   ```

2. Artifact Definition exists at `/configuration/artifact_definitions/env-template.yaml`
3. Environment definition contains `envTemplate.artifact: env-template:1.0.0` (AppVer format)
4. CMDB holds current application definition and registry metadata for `env-template`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
```

**Steps:**

1. The `registry_discovery` job runs while a local Artifact Definition already exists.
2. The job overwrites the Artifact Definition under `/configuration/artifact_definitions/`.

**Results:**

1. `/configuration/artifact_definitions/env-template.yml` or `.yaml` is overwritten
2. Job status is `success`

---

### UC-RD-4: Pipeline generation fails when discovery disabled

**Pre-requisites:**

1. `/configuration/config.yml` contains:

   ```yaml
   artifact_definitions_discovery_mode: false
   ```

2. Artifact Definition for `env-template` is absent under `/configuration/artifact_definitions/`
3. Environment definition contains `envTemplate.artifact: env-template:1.0.0` (AppVer format)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
```

**Steps:**

1. Pipeline generation fails before any job runs.

**Results:**

1. No `registry_discovery` job is created
2. Error message references `env-template` and `artifact_definitions_discovery_mode: false`

---

### UC-RD-5: Job runs but runtime discovery is skipped (invalid AppVer)

**Pre-requisites:**

1. `/configuration/config.yml` contains:

   ```yaml
   artifact_definitions_discovery_mode: auto
   ```

2. Artifact Definition is absent under `/configuration/artifact_definitions/`
3. Environment definition contains an invalid AppVer - `envTemplate.artifact` is a string without `:` (application
   name only, no version)
4. `ENV_TEMPLATE_VERSION` is not set or does not contain `:`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
```

**Steps:**

1. The `registry_discovery` job runs.
2. The job completes without writing an Artifact Definition.

**Results:**

1. Job status is `success`
2. No Artifact Definition appears under `/configuration/artifact_definitions/`
3. No changes appear in `/configuration/credentials/credentials.yml`

---

### UC-RD-6: CMDB export failure during discovery

**Pre-requisites:**

1. Same as UC-RD-1, except CMDB does not hold application definition metadata for `env-template`, or deploytool
   export fails

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <cluster>/<env>
ENV_BUILDER: true
ENV_TEMPLATE_TEST: false
```

**Steps:**

1. The `registry_discovery` job runs.
2. The job fails.

**Results:**

1. Job status is `failed`
2. No Artifact Definition appears under `/configuration/artifact_definitions/`
