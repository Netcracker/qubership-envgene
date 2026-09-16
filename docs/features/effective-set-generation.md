# Effective Set Generation

- [Effective Set Generation](#effective-set-generation)
  - [Overview](#overview)
  - [Location](#location)
  - [Inputs](#inputs)
  - [Solution Descriptor Role](#solution-descriptor-role)
  - [Pipeline Stage](#pipeline-stage)
  - [Generation Modes](#generation-modes)
    - [Full Generation](#full-generation)
    - [Partial Generation](#partial-generation)
      - [Forward merge](#forward-merge)
      - [Reverse merge](#reverse-merge)
      - [Limitation](#limitation)
    - [No-SD Mode](#no-sd-mode)
  - [Cleanup context](#cleanup-context)
  - [Configuration](#configuration)
  - [See also](#see-also)

## Overview

The Effective Set (ES) is the resolved parameter set for an environment — the output consumed by deployment tooling such as ArgoCD. It is produced by merging inputs from the Solution Descriptor, the environment instance objects, Application SBOMs, and registry configuration according to strict priority rules.

ES generation runs as a dedicated stage in the Instance Repository pipeline and commits its output back to the repository.

## Location

The generated ES is stored alongside its environment:

```text
/environments/<cloud-name>/<env-name>/effective-set/
├── topology/
├── pipeline/
├── deployment/
├── runtime/
└── cleanup/
```

`topology/` and `pipeline/` hold solution-level data. `deployment/`, `runtime/`, and `cleanup/` contain per-namespace (and per-application for `deployment` and `runtime`) data.

The detailed file-level layout and contents are documented in [Calculator CLI](/docs/features/calculator-cli.md#version-20-effective-set-structure).

## Inputs

- **Full Solution Descriptor** — the definitive list of applications and their target namespaces. Required for `deployment` and `runtime` contexts, and absent in [No-SD Mode](#no-sd-mode). See [SD processing](/docs/features/sd-processing.md).
- **Environment instance data** — `namespace.yml`, `cloud.yml`, credentials, and other environment objects under the environment's directory.
- **Application SBOMs** — produced externally, cached in the Instance Repository. See [SBOM](/docs/features/sbom.md).
- **Registry configuration** — `/configuration/registry.yml`.
- **Pipeline-time overrides** — optional custom parameters and effective-set configuration passed via pipeline variables.

## Solution Descriptor Role

The Solution Descriptor (SD) is the source of structure for Effective Set generation: it determines which applications and in which namespaces (via `deployPostfix`) are included.

Parameters at the namespace, application, and service levels are computed only for applications listed in the SD. Objects present in the Environment Instance that are not referenced by the SD are ignored and do not appear in the Effective Set.

Behavior in mismatched cases:

- **Namespace in Environment Instance but not referenced by any SD application** — the namespace is not included in the `deployment` or `runtime` contexts. Generation continues for the remaining applications. In No-CMDB v1 the namespace can still receive a `cleanup` context. See [Cleanup context](#cleanup-context).
- **Application in Environment Instance but absent from the SD** — the application is not included. Generation continues for the remaining applications.
- **SD application's `deployPostfix` refers to a namespace that does not exist in the Environment Instance** — generation terminates with an error.
- **SD application is not present in the Environment Instance** — generation succeeds, but no user-defined parameters are produced for that application.

## Pipeline Stage

ES generation is the `generate_effective_set` stage of the Instance Repository pipeline. It runs after [SD processing](/docs/features/sd-processing.md) and after the required Application SBOMs are available in the cache.

See [How to generate an Effective Set](/docs/how-to/generate-effective-set.md) for operational guidance.

## Generation Modes

The generation path is chosen automatically based on the outcome of SD processing in the current pipeline run. The user does not select the mode directly.

### Full Generation

The entire ES is rebuilt from the current Full SD and environment instance data. The `topology`, `pipeline`, `deployment`, and `runtime` contexts are produced. The `cleanup` context follows [Cleanup context](#cleanup-context). Applied when:

- `SD_REPO_MERGE_MODE=replace`, or
- The pipeline runs without an incoming SD, a Full SD already exists in the repository, and
  `use_committed_sd` is `true` (the default), or
- An incoming SD is supplied with a merge mode but no Full SD exists yet — the incoming SD becomes the Full SD, there is nothing to merge against.

Application and Registry Definitions for every application in the Full SD must be available.

### Partial Generation

The `topology`, `pipeline`, `deployment`, and `runtime` contexts remain present in the persistent ES, exactly as in full generation. The `cleanup` context follows [Cleanup context](#cleanup-context). The difference is in *how* they are produced: the calculator is invoked with the Delta SD instead of the Full SD, and its output is recursively merged into the persistent ES — only slices affected by the SD change are recomputed. Applications unchanged in the current run keep their existing slices and their SBOMs are not requested.

Applied when SD processing produces a Delta SD — that is, `SD_REPO_MERGE_MODE` is `basic-merge`, `extended-merge`, or `basic-exclusion-merge`, and a Full SD already exists.

Application and Registry Definitions for every application in the Delta SD must be available.

This mode is available only when `effective_set_generation_strategy=partial` or not set in [`config.yml`](/docs/envgene-configs.md#configyml).

#### Forward merge

Applies to `SD_REPO_MERGE_MODE` values `basic-merge` and `extended-merge`. The Delta SD lists the applications being added or updated.

- The calculator is invoked with the Delta SD as input. It produces output across all five contexts, scoped to the Delta SD.
- The output is merged into the persistent ES recursively: per-application slices under `deployment/` and `runtime/` are replaced for the applications in the Delta SD; `topology/` and `pipeline/` are replaced in full, and `cleanup/` is replaced in full for all namespaces regardless of the Delta SD scope; `mapping.yml` entries are upserted (added or updated, without removing entries for namespaces outside the Delta SD).
- Applications not in the Delta SD keep their existing slices; their SBOMs are not requested.

#### Reverse merge

Applies to `SD_REPO_MERGE_MODE` value `basic-exclusion-merge`. The Delta SD lists the applications being removed.

- The calculator is not invoked. SBOMs for the removed applications are not requested.
- Per-application slices of the removed applications are deleted from `deployment/` and `runtime/`.
- If removing an application leaves a namespace with no applications in the Full SD, that namespace is removed from `deployment/` and `runtime/`, and its entry is dropped from those two `mapping.yml` files. The namespace keeps its `cleanup/` context and `cleanup/mapping.yml` entry, because the namespace object still exists.

#### Limitation

Under partial forward merge, the `generate_effective_set` stage follows the Delta SD scope: `topology/`, `pipeline/`, and `cleanup/` are refreshed from the merged calculator output, but **`deployment/` and `runtime/` are recomputed only for applications in the Delta SD**. For every other application, the stage **does not rewrite** that application's slices under `effective-set/deployment/` and `effective-set/runtime/`. Environment-instance changes for those applications are **not** folded into the Effective Set on this run. To recalculate **all** applications, trigger [full generation](#full-generation).

### No-SD Mode

Applied when the pipeline runs without an incoming SD and one of the following holds:

- No Full SD exists in the repository, or
- A Full SD exists but `use_committed_sd` is `false` in
  [`config.yml`](/docs/envgene-configs.md#configyml).

Only `topology`, `pipeline`, and `cleanup` contexts are produced. `deployment` and `runtime` require application
data from a Solution Descriptor, so they are not produced. The `cleanup` context does not depend on the Solution
Descriptor and is produced for every namespace of the environment. SBOMs are not required so are not generated.

By default (`use_committed_sd: true`) a run with no incoming SD uses the committed Full SD and Full
Generation runs.

See [Generate Without a Solution Descriptor](/docs/how-to/generate-effective-set.md#generate-without-a-solution-descriptor)
in the how-to guide.

## Cleanup context

The `cleanup/` context holds, per namespace, the parameters and credentials that downstream tooling reads to undeploy a namespace. EnvGene produces the context. The cluster-side removal is performed by the consuming tooling. The per-namespace file layout is documented in [Calculator CLI](/docs/features/calculator-cli.md#version-20-cleanup-context).

Two kinds of tooling consume the cleanup output, and they need different parts of it. Pipeline-driven cleanup reads the per-namespace cleanup context to undeploy each namespace. A cluster-resident cleaner reads only the environment topology and resolves the rest itself. The cleanup context is produced only for the flows whose consumer reads it.

Which namespaces receive it depends on the [deployment architecture](/docs/deployment-architecture.md) and the operation:

| Architecture | Operation | Cleanup context produced for       |
| ------------ | --------- | ---------------------------------- |
| No-CMDB v1   | `DEPLOY`  | every namespace of the environment |
| No-CMDB v2   | `DEPLOY`  | no namespace                       |
| No-CMDB v2   | `CLEAN`   | no namespace                       |

In No-CMDB v1 deploy, a namespace with no application versions deployed to it still receives a cleanup context and a `cleanup/mapping.yaml` entry, so a later teardown of the whole environment covers every namespace. No `.cleaned` marker is written for these namespaces. The cleanup context is produced the same way in [No-SD Mode](#no-sd-mode), where the environment has namespaces but no current solution.

In No-CMDB v2 clean, no cleanup context is produced. The `CLEAN` operation marks the target namespaces' deployment and runtime for removal, writing a `.cleaned` marker into `deployment/<ns>/` and `runtime/<ns>/` and dropping them from `deployment/mapping.yaml` and `runtime/mapping.yaml`. See [CLEAN sub-flows](/docs/technical-design/instance-pipeline/sub-flows/clean.md).

The cleanup context of a namespace merges the `deployParameters` of the `Tenant`, `Cloud`, and `Namespace` Environment Instance objects. Non-sensitive values go to `parameters.yaml` and sensitive values go to `credentials.yaml`. Application-level parameters are not included. Custom parameters from the `deployment` section override these values.

Whether the cleanup context is generated for every namespace is controlled by the calculator input [`--generate-cleanup-context`](/docs/features/calculator-cli.md#calculator-command-line-tool-execution-attributes), which the pipeline derives from `PIPELINE_TYPE`. No dedicated pipeline parameter controls it.

## Configuration

Key pipeline parameters that affect ES generation:

- `SD_DATA` / `SD_VERSION` — the incoming SD.
- `SD_REPO_MERGE_MODE` — how the incoming SD is merged with the existing one; determines whether partial or full generation applies.
- `EFFECTIVE_SET_CONFIG` — effective-set version selection and related options.
- `CUSTOM_PARAMS` — optional overrides injected into `deployment`, `runtime`, and `cleanup` contexts.

See [Instance pipeline parameters](/docs/instance-pipeline-parameters.md) for the full list.

## See also

- [Calculator CLI](/docs/features/calculator-cli.md) — the underlying tool and the detailed ES file-structure reference.
- [How to generate an Effective Set](/docs/how-to/generate-effective-set.md) — operational guide.
- [Tutorial: Understanding the Effective Set](/docs/tutorials/effective-set.md) — walkthrough of ES contents and parameter flow.
- [SD processing](/docs/features/sd-processing.md) — how the Solution Descriptor is merged and stored.
- [SBOM](/docs/features/sbom.md) — how Application SBOMs are produced and cached.
