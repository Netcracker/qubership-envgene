# Troubleshooting artifacts

- [Troubleshooting artifacts](#troubleshooting-artifacts)
  - [Overview](#overview)
  - [Security](#security)
  - [Scope](#scope)
  - [Save criteria](#save-criteria)
    - [Strategy](#strategy)
    - [Size limit](#size-limit)
  - [Multi-environment runs](#multi-environment-runs)

## Overview

By default, EnvGene saves the work directory of an instance repository pipeline run and publishes it as a job
artifact for troubleshooting. The artifact holds the intermediate and output files the run produced, so an
operator can inspect them without rerunning the pipeline. When `ENV_NAMES` lists several environments, each one
runs in its own isolated work directory, and the artifact includes all of them, one per environment.

## Security

EnvGene decrypts credential files at the start of the job and encrypts them at the end. On a successful run,
all credential values in the artifact are encrypted. A failure before the encrypt pass leaves plaintext
credential values in a failed run's artifact. Treat failure artifacts as potentially sensitive. See
[Credential encryption](/docs/features/credential-encryption.md).

## Scope

The artifact is the work directory as the run left it. Each run works in its own isolated git worktree that commits
its result independently, laid out under a `<cluster-name>-<environment-name>/` wrapper. The tree below shows the full
layout. When the work directory is not saved, the artifact holds only `NOT-PUBLISHED.txt` (see
[Save criteria](#save-criteria)).

```text
artifacts
├── NOT-PUBLISHED.txt                            # only when the run is not saved (NEVER, or over the 1500 MB limit)
└── <cluster-name>-<environment-name>/           # isolated worktree of one run (multi-env: one sibling per environment)
    ├── appdefs/                                 # Effective Application Definitions
    ├── regdefs/                                 # Effective Registry Definitions
    ├── configuration/                           # Repository wide configuration
    ├── sboms/                                   # SBOMs
    ├── environments/
    │   ├── <shared-site-dirs>/                  # Shared repository wide paramsets, resource profiles, credentials
    │   └── <cluster-name>/
    │       ├── <shared-cluster-dirs>/           # Shared cluster wide paramsets, resource profiles, credentials. Cloud Passport
    │       └── <environment-name>/              # env instance, Inventory, sd.yml, effective-set, deploy-plan.yml, ArgoCD repo
    ├── cmdb-import/                             # CMDB import structure
    ├── templates/                               # downloaded env template
    │   ├── common/                              # non Blue-Green or Blue-Green common template
    │   ├── origin/                              # Blue-Green origin template
    │   └── peer/                                # Blue-Green peer template
    └── app-artifacts/
        └── <app-name>/
            └── <app-version>/
                └── dd.json
```

`environments/` holds the processed environments plus the repository-wide and cluster-wide shared directories:
parameter sets, resource profiles, credentials, and the cluster's Cloud Passport. Under each environment you
find the Environment Instance, the Environment Inventory (`env_definition.yml`), the Solution Descriptor,
environment-specific parameter sets, resource profiles, credentials, the Effective Set, `deploy-plan.yml`, and
the ArgoCD repository output.

> [!NOTE]
> The `.git` metadata is not saved. Under `tmp/` in the work directory, only the downloaded environment
> templates and the `dd.json` deployment descriptors of the application artifact cache are saved. They appear
> in the artifact under the wrapper, as `templates/` and `app-artifacts/`. Everything else under `tmp/` is left
> out.

## Save criteria

Two checks decide whether the work directory is saved: the strategy and the size limit. When either check
stops the save, the job publishes a single `NOT-PUBLISHED.txt` file instead. Its text states the reason: the
strategy is `NEVER`, or the content to save exceeded the 1500 MB limit.

### Strategy

The strategy has two controls:

1. [`save_artifacts_strategy`](/docs/envgene-configs.md#configyml) in `/configuration/config.yml` is the
   repository-wide policy. The default is `ALWAYS`.
2. The [`SAVE_ARTIFACTS_STRATEGY`](/docs/instance-pipeline-parameters.md#save_artifacts_strategy) CI/CD
   variable overrides the policy for a single pipeline run. To force a save on a single run, set the variable
   to `ALWAYS`.

The precedence is CI/CD variable over `config.yml` over the `ALWAYS` default.

Repository policy in `/configuration/config.yml`:

```yaml
# Optional. Default value - `ALWAYS`
save_artifacts_strategy: enum [`ALWAYS`, `NEVER`]
```

Per-run override as a CI/CD variable:

```yaml
# Optional. No default value
SAVE_ARTIFACTS_STRATEGY: enum [`ALWAYS`, `NEVER`]
```

### Size limit

A size guard runs before archiving. It measures the uncompressed size of the content to save, that is the
work directory minus the exclusions listed in [Scope](#scope). Above the 1500 MB limit, the work directory is
not saved. The job does not fail on size, so `ALWAYS` is safe even when runs produce large output.

The 1500 MB limit is fixed and not configurable. Measuring the uncompressed size against it is conservative,
because the CI platform's job artifact limit applies to the smaller archived artifact.

## Multi-environment runs

When [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names) lists more than one environment, each
environment runs in its own isolated git worktree and commits its result independently. Each environment
produces its own `<cluster-name>-<environment-name>/` artifact wrapper, one per environment. The save criteria
apply to each environment independently. An environment that fails partway through still publishes the partial
output produced up to the failure point.

To avoid a large artifact on every run, set `save_artifacts_strategy: NEVER` in `config.yml`. To
troubleshoot, rerun the affected environment with `SAVE_ARTIFACTS_STRATEGY: ALWAYS`.
