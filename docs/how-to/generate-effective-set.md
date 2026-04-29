# How to Generate an Effective Set

- [How to Generate an Effective Set](#how-to-generate-an-effective-set)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Steps](#steps)
    - [1. Verify the Inventory Is Configured](#1-verify-the-inventory-is-configured)
    - [2. Prepare the Solution Descriptor](#2-prepare-the-solution-descriptor)
    - [3. Trigger the Pipeline](#3-trigger-the-pipeline)
  - [Results](#results)
  - [Other Common Scenarios](#other-common-scenarios)
    - [Generate Without a Solution Descriptor](#generate-without-a-solution-descriptor)
    - [Inject High-Priority Parameters at Runtime](#inject-high-priority-parameters-at-runtime)

## Description

This guide explains how to trigger a full Effective Set generation for a specific environment in the Instance Repository.

The **Effective Set** is the final resolved parameter set for an environment - the output consumed by ArgoCD and other deployment tools. EnvGene calculates it by merging parameters from multiple sources in strict priority order.

The Effective Set is written to `environments/<cluster>/<env>/effective-set/`.

> [!IMPORTANT]
> The pipeline run is **not atomic**. If any earlier job fails, the Effective Set is not updated. You do not need to prepare the Environment Instance manually - the pipeline builds it as part of the same run.

## Prerequisites

1. An Instance Repository exists with the target environment's Inventory configured under `environments/<cluster>/<env>/Inventory/`
2. A template artifact is published and accessible (e.g. `env-template:2.5.0`)
3. A Solution Descriptor artifact is published and accessible (e.g. `sd:1.2.3`) - or you intend to generate only the `topology` and `pipeline` contexts (see [Generate Without a Solution Descriptor](#generate-without-a-solution-descriptor))

---

## Steps

### 1. Verify the Inventory Is Configured

Confirm that the environment's Inventory is present in the repository:

```text
environments/prod-cluster/prod-01/
└── Inventory/
    └── env_definition.yml
```

If `env_definition.yml` is missing, create it before proceeding. See [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

---

### 2. Prepare the Solution Descriptor

Provide the SD via one of the following pipeline variables. The pipeline writes it to `environments/prod-cluster/prod-01/Inventory/solution-descriptor/sd.yaml` automatically.

**Option A - Artifact reference (SD_SOURCE_TYPE + SD_VERSION):**

The SD is fetched from an artifact registry at pipeline start and written to the repository path above:

```text
SD_SOURCE_TYPE: artifact
SD_VERSION:     sd:1.2.3
```

**Option B - Inline content (SD_SOURCE_TYPE + SD_DATA):**

Pass the SD content as a JSON string directly as a pipeline variable. Useful for testing or one-off runs:

```text
SD_SOURCE_TYPE: json
SD_DATA:        '{"applications":[{"version":"Cloud-BSS:1.2.3","deployPostfix":"bss"},{"version":"cloud-oss:2.0.1","deployPostfix":"oss"}]}'
```

If neither is provided, the existing `sd.yaml` file already committed in the repository is used.

---

### 3. Trigger the Pipeline

Trigger the Instance pipeline with the following variables:

| Variable                 | Value                  | Description                                        |
|--------------------------|------------------------|----------------------------------------------------|
| `ENV_NAMES`              | `prod-cluster/prod-01` | Target environment; comma-separated for multiple   |
| `ENV_BUILDER`            | `true`                 | Rebuild the Environment Instance from the template |
| `ENV_TEMPLATE_VERSION`   | `env-template:2.5.0`   | Template version to use for the Instance build     |
| `GENERATE_EFFECTIVE_SET` | `true`                 | Enable the effective set generation job            |
| `SD_SOURCE_TYPE`         | `artifact`             | How the SD is provided (`artifact` or `json`)      |
| `SD_VERSION`             | `sd:1.2.3`             | SD artifact name and version                       |

The pipeline executes the following job sequence:

```text
appregdef_render → process_sd → env_build → generate_effective_set → git_commit
```

If only the Effective Set needs to be regenerated without rebuilding the Environment Instance, set `ENV_BUILDER: false`. The `generate_effective_set` job will use the existing Instance files from the previous run.

> [!IMPORTANT]
> The `generate_effective_set` job always depends on `env_build`. If `ENV_BUILDER: false` is set but the Environment Instance files are already present from a previous run, generation proceeds normally.

---

## Results

A successful run produces the following structure under `environments/prod-cluster/prod-01/effective-set/`:

```text
effective-set/
├── topology/
│   ├── parameters.yaml
│   └── credentials.yaml
├── pipeline/
│   ├── parameters.yaml
│   └── credentials.yaml
├── deployment/
│   ├── mapping.yml
│   ├── bss/
│   │   └── Cloud-BSS/
│   │       └── values/
│   │           ├── deployment-parameters.yaml
│   │           ├── collision-deployment-parameters.yaml
│   │           ├── credentials.yaml
│   │           ├── collision-credentials.yaml
│   │           ├── deploy-descriptor.yaml
│   │           ├── custom-params.yaml
│   │           └── per-service-parameters/
│   │               └── cloud-bss-7b/
│   │                   └── deployment-parameters.yaml
│   └── oss/
│       └── cloud-oss/
│           └── values/
│               ├── deployment-parameters.yaml
│               ├── collision-deployment-parameters.yaml
│               ├── credentials.yaml
│               ├── collision-credentials.yaml
│               ├── deploy-descriptor.yaml
│               ├── custom-params.yaml
│               └── per-service-parameters/
│                   └── cloud-oss/
│                       └── deployment-parameters.yaml
├── runtime/
│   ├── mapping.yml
│   ├── bss/
│   │   └── Cloud-BSS/
│   │       ├── parameters.yaml
│   │       └── credentials.yaml
│   └── oss/
│       └── cloud-oss/
│           ├── parameters.yaml
│           └── credentials.yaml
└── cleanup/
    ├── mapping.yml
    ├── bss/
    │   ├── parameters.yaml
    │   └── credentials.yaml
    └── oss/
        ├── parameters.yaml
        └── credentials.yaml
```

The `git_commit` job commits these files to the Instance Repository automatically. The pipeline run is complete when `git_commit` succeeds and the files appear under `environments/prod-cluster/prod-01/effective-set/`.

---

## Other Common Scenarios

### Generate Without a Solution Descriptor

When no Solution Descriptor is provided - for example when setting up infrastructure-only namespaces or preparing an environment before any applications are defined - the Effective Set is generated in a partial mode.

Without an SD, EnvGene does not know which applications belong to which namespaces, so the application-specific contexts cannot be produced. The following contexts are generated normally:

- `topology` - cluster structure, namespace mapping, composite structure, BG domain
- `pipeline` - orchestration pipeline parameters

The following contexts are **not generated**:

- `deployment` - requires application definitions from the SD
- `runtime` - requires application definitions from the SD
- `cleanup` - requires application definitions from the SD

To use this mode, simply omit `SD_VERSION` and `SD_SOURCE_TYPE` from the pipeline variables. If no SD artifact is passed and no `sd.yaml` exists in the repository, EnvGene skips all application-level processing automatically.

---

### Inject High-Priority Parameters at Runtime

Use `CUSTOM_PARAMS` to inject parameters at the highest priority level, overriding everything else. This is useful for temporary overrides, incident response, or injecting session-specific values.

`CUSTOM_PARAMS` accepts a JSON-in-string value:

```json
{
  "deployment": {
    "FEATURE_FLAG_NEW_BILLING": "true",
    "MAX_RETRIES": "5"
  },
  "runtime": {
    "LOG_LEVEL": "DEBUG"
  }
}
```

Set this as a pipeline variable:

```text
CUSTOM_PARAMS: '{"deployment":{"FEATURE_FLAG_NEW_BILLING":"true","MAX_RETRIES":"5"}}'
```

The injected parameters are written to `custom-params.yaml` inside each application's `values/` folder, applied at the highest priority level after all other values files.

> [!WARNING]
> Custom Params override all other parameter sources. Use them only for temporary, session-specific values. Do not use Custom Params to replace permanent configuration - use Environment Specific ParameterSets instead.
