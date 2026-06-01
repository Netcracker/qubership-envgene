# Effective Set external export use cases

- [Effective Set external export use cases](#effective-set-external-export-use-cases)
  - [Scope](#scope)
  - [Placement](#placement)
    - [UC-ESE-PL-1: Instance publish when placement is absent](#uc-ese-pl-1-instance-publish-when-placement-is-absent)
    - [UC-ESE-PL-2: Remote publish only](#uc-ese-pl-2-remote-publish-only)
    - [UC-ESE-PL-3: Dual publish to Instance and external repository](#uc-ese-pl-3-dual-publish-to-instance-and-external-repository)
  - [DCL fallback (e2eParameters)](#dcl-fallback-e2eparameters)
    - [UC-ESE-DCL-1: Connection parameters from `e2eParameters` when Cloud Passport has no ARGOCD values](#uc-ese-dcl-1-connection-parameters-from-e2eparameters-when-cloud-passport-has-no-argocd-values)
    - [UC-ESE-DCL-2: Publish branch from `e2eParameters` when Cloud Passport has no branch](#uc-ese-dcl-2-publish-branch-from-e2eparameters-when-cloud-passport-has-no-branch)
  - [Repository access validation](#repository-access-validation)
    - [UC-ESE-VAL-1: Repository access check fails before publish](#uc-ese-val-1-repository-access-check-fails-before-publish)

## Scope

This document defines use cases for external Effective Set publish in
[/docs/features/effective-set-generation.md#external-export](/docs/features/effective-set-generation.md#external-export).
It covers `effective_set.placement` (including external publish targets), DCL fallback from `e2eParameters` in
`cloud.yaml`, and access validation. Successful external publish is covered by
[UC-ESE-PL-2](#uc-ese-pl-2-remote-publish-only) and [UC-ESE-PL-3](#uc-ese-pl-3-dual-publish-to-instance-and-external-repository).

## Placement

### UC-ESE-PL-1: Instance publish when placement is absent

**Pre-requisites:**

1. `env_definition.yml` exists at:
   - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
2. `effective_set.placement` is absent.
3. Effective Set generation inputs exist for the environment.

**Trigger:**

Instance pipeline is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
GENERATE_EFFECTIVE_SET: true
```

**Steps:**

1. The `generate_effective_set` job runs.
2. Effective Set files are generated in the workspace.
3. Placement is not set.
4. The `git_commit` stage commits the Effective Set to the Instance repository.

**Results:**

1. Effective Set is committed at:
   - `/environments/<cloud-name>/<env-name>/effective-set/`
2. No external repository publish runs.

### UC-ESE-PL-2: Remote publish only

**Pre-requisites:**

1. `env_definition.yml` contains `effective_set.placement: remote`:

   ```yaml
   effective_set:
     placement: remote
   ```

2. Connection parameters resolve from Cloud Passport and/or `e2eParameters` in `cloud.yaml`.

3. External repository access validation succeeds.

**Trigger:**

Instance pipeline is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
GENERATE_EFFECTIVE_SET: true
```

**Steps:**

1. The `generate_effective_set` job runs.
2. Effective Set files are generated in the workspace.
3. Placement is `remote`.
4. Effective Set is published to the external repository.
5. The `git_commit` stage runs for other Instance repository changes.

**Results:**

1. Effective Set is present in the external repository at:
   - `/environments/<environment_id>/effective-set/`
2. `git_commit` does not add, update, or delete files under:
   - `/environments/<cloud-name>/<env-name>/effective-set/`

### UC-ESE-PL-3: Dual publish to Instance and external repository

**Pre-requisites:**

1. `env_definition.yml` contains `effective_set.placement: dual`:

   ```yaml
   effective_set:
     placement: dual
   ```

2. Connection parameters resolve from Cloud Passport and/or `e2eParameters` in `cloud.yaml`.

3. External repository access validation succeeds.

**Trigger:**

Instance pipeline is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
GENERATE_EFFECTIVE_SET: true
```

**Steps:**

1. The `generate_effective_set` job runs.
2. Effective Set files are generated in the workspace.
3. Placement is `dual`.
4. Effective Set is published to the external repository.
5. The `git_commit` stage commits the Effective Set to the Instance repository.

**Results:**

1. Effective Set is present in the external repository at:
   - `/environments/<environment_id>/effective-set/`
2. Effective Set is committed in the Instance repository at:
   - `/environments/<cloud-name>/<env-name>/effective-set/`

## DCL fallback (e2eParameters)

When Cloud Passport has no `ARGOCD_*` connection values, EnvGene reads the mapped `DCL_*` keys from `e2eParameters` in
`cloud.yaml`. See [Parameter resolution](/docs/features/effective-set-generation.md#parameter-resolution) and
[Branch resolution](/docs/features/effective-set-generation.md#branch-resolution).

### UC-ESE-DCL-1: Connection parameters from `e2eParameters` when Cloud Passport has no ARGOCD values

**Pre-requisites:**

1. `env_definition.yml` contains `effective_set.placement: remote` or `effective_set.placement: dual`.
2. Cloud Passport has no `ARGOCD_*` connection parameters for external publish.
3. `cloud.yaml` for the environment defines mapped `DCL_*` keys in `e2eParameters`:

```yaml
e2eParameters:
  DCL_GIT_URL: "https://gitlab.example.com/group/external-effective-set.git"
  DCL_CONFIG_GITLAB_USER: "ci-bot"
  DCL_CONFIG_GITLAB_TOKEN: "glpat-xxxx"
  DCL_CONFIG_ARGOCD_URL: "https://argocd.example.com"
  DCL_CONFIG_ARGOCD_USER: "argocd-user"
  DCL_CONFIG_ARGOCD_PASSWORD: "argocd-password"
```

**Trigger:**

Instance pipeline is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
GENERATE_EFFECTIVE_SET: true
```

**Steps:**

1. The `generate_effective_set` job runs.
2. Placement is `remote` or `dual`.
3. Connection parameters are resolved.
4. No `ARGOCD_*` values are found in Cloud Passport.
5. All mapped connection parameters are read from `e2eParameters` in `cloud.yaml`.

**Results:**

1. External publish uses `DCL_*` values from `e2eParameters`.
2. Repository access validation runs against the resolved GitLab URL and credentials.

### UC-ESE-DCL-2: Publish branch from `e2eParameters` when Cloud Passport has no branch

**Pre-requisites:**

1. `env_definition.yml` contains `effective_set.placement: remote` or `effective_set.placement: dual`.
2. Cloud Passport does not define `ARGOCD_GITLAB_BRANCH`.
3. Connection parameters resolve (from Cloud Passport and/or `e2eParameters`).
4. `cloud.yaml` defines `DCL_GIT_BRANCH` in `e2eParameters`:

```yaml
e2eParameters:
  DCL_GIT_BRANCH: "main"
```

**Trigger:**

Instance pipeline is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
GENERATE_EFFECTIVE_SET: true
```

**Steps:**

1. The `generate_effective_set` job runs.
2. Publish branch is resolved.
3. `ARGOCD_GITLAB_BRANCH` is not found in Cloud Passport.
4. Publish branch is read from `DCL_GIT_BRANCH` in `e2eParameters` in `cloud.yaml`.

**Results:**

1. External publish uses the branch value from `DCL_GIT_BRANCH`.

## Repository access validation

For `placement: remote` or `placement: dual`, EnvGene checks the external GitLab repository before publish. See
[Validation](/docs/features/effective-set-generation.md#validation) in the feature document.

### UC-ESE-VAL-1: Repository access check fails before publish

**Pre-requisites:**

1. `env_definition.yml` contains `effective_set.placement: remote` or `effective_set.placement: dual`.
2. Connection parameters and publish branch resolve.

**Trigger:**

1. The resolved external GitLab URL does not respond (reachability failure).
2. The resolved credentials do not authenticate to that URL (authentication failure).

Instance pipeline is started with parameters:

```yaml
ENV_NAMES: <cluster-name>/<env-name>
GENERATE_EFFECTIVE_SET: true
```

**Steps:**

1. The `generate_effective_set` job runs.
2. Pre-publish repository access check runs against the resolved external GitLab URL.
3. Reachability or authentication fails.
4. The job terminates before external publish.

**Results:**

1. The `generate_effective_set` job fails with one of:
   - `endpoint_unreachable` when the URL does not respond. Error includes the checked URL.
   - `authentication_failed` when credentials fail. Error includes the checked URL and remediation guidance.
2. External publish does not run.
