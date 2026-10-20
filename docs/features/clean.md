# Cleanup

- [Cleanup](#cleanup)
  - [Description](#description)
  - [Cleanup output by deployment architecture](#cleanup-output-by-deployment-architecture)
  - [Emitted output](#emitted-output)
    - [Cleanup context (No-CMDB v1)](#cleanup-context-no-cmdb-v1)
    - [`.cleaned` marker (No-CMDB v2)](#cleaned-marker-no-cmdb-v2)
  - [Who triggers what](#who-triggers-what)
  - [Where to read next](#where-to-read-next)

## Description

EnvGene writes cleanup output into the [Effective Set](/docs/features/calculator-cli.md#effective-set-v20) in Git
so that a deployed namespace, or a whole environment, can be removed from a cluster. EnvGene does not remove
anything itself. Teardown tooling outside EnvGene consumes the output.

Cleanup is one subject with two forms of output.

1. [No-CMDB v1](/docs/deployment-architecture.md#no-cmdb-v1) has no `CLEAN` operation. It produces a per-namespace
   cleanup context on every deploy that has a Solution Descriptor, ahead of need, so the data is ready whenever
   that namespace is later cleaned.
2. [No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2) has a `CLEAN` operation that marks namespaces for
   removal and produces no cleanup context.

Cleanup output exists only in Effective Set v2.0. Effective Set v1.0 has none. The Effective Set version is a
separate axis from the No-CMDB architecture version.

## Cleanup output by deployment architecture

EnvGene emits one of two forms, selected by the deployment architecture and the operation.

| Architecture | Operation | What EnvGene emits                                            |
|--------------|-----------|---------------------------------------------------------------|
| No-CMDB v1   | `DEPLOY`  | A cleanup context for every namespace of the environment      |
| No-CMDB v2   | `DEPLOY`  | No cleanup output                                             |
| No-CMDB v2   | `CLEAN`   | A `.cleaned` marker per cleaned namespace, no cleanup context |

In No-CMDB v1, when the environment has a Solution Descriptor, the cleanup context is written for every
namespace, including one with no deployed application versions. A run with no Solution Descriptor produces no
cleanup context.

No-CMDB v2 produces no cleanup context, on deploy or on clean. Its `CLEAN` operation marks the target namespaces
instead. The absence of a cleanup context in No-CMDB v2 is unconditional: a missing `cleanup/` folder does not
mean the environment has nothing to clean.

## Emitted output

### Cleanup context (No-CMDB v1)

Per namespace, EnvGene writes:

- `cleanup/<namespace>/parameters.yaml`
- `cleanup/<namespace>/credentials.yaml`

and an entry in `cleanup/mapping.yaml`.

The context merges the `deployParameters` of the `Tenant`, `Cloud`, and `Namespace` Environment Instance objects.
Non-sensitive values go to `parameters.yaml`, sensitive values go to `credentials.yaml`.
Application-level parameters are not included. Custom parameters from the `deployment` section override these values.

The exact file layout and sensitive-value handling are in
[Calculator CLI](/docs/features/calculator-cli.md#version-20-cleanup-context).

The calculator input
[`--generate-cleanup-context`](/docs/features/calculator-cli.md#calculator-command-line-tool-execution-attributes)
decides whether the context is produced. The pipeline derives it from `PIPELINE_TYPE` and the presence of a
Solution Descriptor. No dedicated pipeline parameter controls it.

### `.cleaned` marker (No-CMDB v2)

For each namespace cleaned by a `CLEAN` operation, EnvGene writes an empty `.cleaned` file into
`deployment/<namespace>/` and `runtime/<namespace>/`, with no application content.

The cleaned namespace stays listed in `deployment/mapping.yaml` and `runtime/mapping.yaml`. The marker, not a change
to the mapping, is the cleaned-state signal.

A later `DEPLOY` restores the namespace and deletes its `.cleaned` marker.

## Who triggers what

EnvGene's cleanup runs as a step of the Instance pipeline. External orchestrating pipelines call the Instance
pipeline and pass the operation and its parameters. Running the Instance pipeline directly, outside an
orchestrator, happens only for debugging.

In No-CMDB v2, a cleanup is a `CLEAN` operation launched with:

- [`OPERATION_TYPE: CLEAN`](/docs/instance-pipeline-parameters.md#operation_type)
- [`PIPELINE_TYPE: GITLAB_DEPLOY`](/docs/instance-pipeline-parameters.md#pipeline_type)
- [`NAMESPACE_NAMES`](/docs/instance-pipeline-parameters.md#namespace_names) sets the scope: a list cleans the named
  namespaces, and an empty value cleans the whole environment.

The step-by-step behavior is in [CLEAN sub-flows](/docs/technical-design/instance-pipeline/sub-flows/clean.md).

In No-CMDB v1, there is no cleanup operation to trigger. EnvGene produces the cleanup context during each deploy
that has a Solution Descriptor, ahead of need.

## Where to read next

| If you want to…                                                   | Read                                                                                                                  |
|-------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| Look up the cleanup context file layout                           | [Calculator CLI - Cleanup Context](/docs/features/calculator-cli.md#version-20-cleanup-context)                       |
| See how the `CLEAN` operation runs step by step                   | [CLEAN sub-flows](/docs/technical-design/instance-pipeline/sub-flows/clean.md)                                        |
| See cleanup inside the full Effective Set generation flow         | [Effective Set generation](/docs/features/effective-set-generation.md#cleanup-context)                                |
| Walk through cleanup-context use cases                            | [Calculator CLI use cases - cleanup context generation](/docs/use-cases/calculator-cli.md#cleanup-context-generation) |
| Look up pipeline parameters (`OPERATION_TYPE`, `NAMESPACE_NAMES`) | [Instance pipeline parameters](/docs/instance-pipeline-parameters.md)                                                 |
| Understand the deployment architectures                           | [Deployment architecture](/docs/deployment-architecture.md)                                                           |
| See the decision and why                                          | [ADR-0011](/docs/adr/0011-generate-cleanup-context-only-in-no-cmdb-v1.md)                                             |
