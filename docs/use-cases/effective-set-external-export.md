# Effective Set external export use cases

- [Effective Set external export use cases](#effective-set-external-export-use-cases)
  - [Scope](#scope)
  - [PIPELINE_TYPE](#pipeline_type)
    - [UC-ESE-01: Commit to Instance repository](#uc-ese-01-commit-to-instance-repository)
    - [UC-ESE-02: Export to external repository](#uc-ese-02-export-to-external-repository)
    - [UC-ESE-03: Invalid PIPELINE_TYPE fails before generation](#uc-ese-03-invalid-pipeline_type-fails-before-generation)
    - [UC-ESE-04: Missing DCL parameter fails external export](#uc-ese-04-missing-dcl-parameter-fails-external-export)

## Scope

This document defines use cases for Effective Set external export in
[/docs/features/effective-set-generation.md#external-export](/docs/features/effective-set-generation.md#external-export).
It covers `PIPELINE_TYPE` publish paths and connection parameters from the pipeline context.

## PIPELINE_TYPE

### UC-ESE-01: Commit to Instance repository

**Pre-requisites:**

1. Effective Set generation inputs exist for the environment.

**Trigger:**

> [!NOTE]
> One of the following conditions must be met:

1. Instance pipeline (GitLab or GitHub) is started with parameters:
   1. `ENV_NAMES: <cluster-name>/<env-name>`
   2. `GENERATE_EFFECTIVE_SET: true`
   3. `PIPELINE_TYPE` is not passed
2. Instance pipeline (GitLab or GitHub) is started with parameters:
   1. `ENV_NAMES: <cluster-name>/<env-name>`
   2. `GENERATE_EFFECTIVE_SET: true`
   3. `PIPELINE_TYPE: null`
3. Instance pipeline (GitLab or GitHub) is started with parameters:
   1. `ENV_NAMES: <cluster-name>/<env-name>`
   2. `GENERATE_EFFECTIVE_SET: true`
   3. `PIPELINE_TYPE` is an empty string

**Steps:**

1. The `generate_effective_set` job runs.
2. The Effective Set is generated.
3. The Effective Set is committed to the Instance repository.

**Results:**

1. The Effective Set is committed at:
   - `/environments/<cluster-name>/<env-name>/effective-set/`
2. External publish does not run.

### UC-ESE-02: Export to external repository

**Pre-requisites:**

1. Effective Set generation inputs exist for the environment.
2. The environment template supplies `DCL_GIT_URL`, `DCL_GIT_BRANCH`, `DCL_CONFIG_GITLAB_USER`, and
   `DCL_CONFIG_GITLAB_TOKEN` in `e2eParameters` of the rendered `cloud.yml`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `PIPELINE_TYPE: GITLAB_DEPLOY`

**Steps:**

1. The `generate_effective_set` job runs.
2. The Effective Set is generated.
3. The Effective Set is published to the external repository.
4. The Effective Set is removed from the Instance repository.

**Results:**

1. The Effective Set is present in the external repository at:
   - `/environments/<cluster-name>/<env-name>/effective-set/`
2. The Effective Set is not present in the Instance repository at:
   - `/environments/<cluster-name>/<env-name>/effective-set/`

### UC-ESE-03: Invalid PIPELINE_TYPE fails before generation

**Pre-requisites:**

1. Effective Set generation inputs exist for the environment.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `PIPELINE_TYPE` is set to a non-empty value other than `GITLAB_DEPLOY`

**Steps:**

1. The `generate_effective_set` job validates `PIPELINE_TYPE`.
2. The job fails because `PIPELINE_TYPE` is not `GITLAB_DEPLOY`.
3. Effective Set generation does not start.

**Results:**

1. The `generate_effective_set` job fails.
2. No Effective Set is generated for this run.
3. External publish does not run.

### UC-ESE-04: Missing DCL parameter fails external export

**Pre-requisites:**

1. Effective Set generation inputs exist for the environment.
2. The rendered `cloud.yml` omits at least one of `DCL_GIT_URL`, `DCL_GIT_BRANCH`, `DCL_CONFIG_GITLAB_USER`, or
   `DCL_CONFIG_GITLAB_TOKEN` in `e2eParameters`, or a template macro for one of these keys does not render during
   Effective Set generation.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `PIPELINE_TYPE: GITLAB_DEPLOY`

**Steps:**

1. The `generate_effective_set` job runs.
2. The Effective Set is generated.
3. At least one required `DCL_*` parameter is absent from the pipeline context.
4. The job fails before external publish.

**Results:**

1. The `generate_effective_set` job fails.
2. External publish does not run.
3. The Effective Set remains in the Instance repository at
   `/environments/<cluster-name>/<env-name>/effective-set/`.
