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

Cleanup is one subject, approached differently by the two deployment architectures.
[No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2) cleans a namespace on demand, through its `CLEAN`
operation. [No-CMDB v1](/docs/deployment-architecture.md#no-cmdb-v1) has no `CLEAN` operation, so EnvGene prepares
each namespace's cleanup context on every deploy, ahead of need. A dedicated cleanup application reads that
context and performs the cleanup.

## Cleanup output by deployment architecture

EnvGene emits one of two forms, selected by the deployment architecture and the operation.

| Architecture | Operation | What EnvGene emits                                       |
|--------------|-----------|----------------------------------------------------------|
| No-CMDB v1   | `DEPLOY`  | A cleanup context for every namespace of the environment |
| No-CMDB v2   | `DEPLOY`  | No cleanup output                                        |
| No-CMDB v2   | `CLEAN`   | Namespace content replaced by a `.cleaned` marker        |

In No-CMDB v1, when the environment has a Solution Descriptor, the cleanup context is written for every
namespace, including one with no deployed application versions. A run with no Solution Descriptor produces no
cleanup context.

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

For each namespace cleaned by a `CLEAN` operation, EnvGene removes the namespace's application content from
`deployment/<namespace>/` and `runtime/<namespace>/` and replaces it with an empty `.cleaned` marker file.

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

In No-CMDB v1, there is no cleanup operation to trigger. The cleanup context is a by-product of deploy.

## Where to read next

| If you want to…                                                   | Read                                                                                                                  |
|-------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| Look up the cleanup context file layout                           | [Calculator CLI - Cleanup Context](/docs/features/calculator-cli.md#version-20-cleanup-context)                       |
| See how the `CLEAN` operation runs step by step                   | [CLEAN sub-flows](/docs/technical-design/instance-pipeline/sub-flows/clean.md)                                        |
| See cleanup inside the full Effective Set generation flow         | [Effective Set generation](/docs/features/effective-set-generation.md#cleanup-context)                                |
| Look up pipeline parameters (`OPERATION_TYPE`, `NAMESPACE_NAMES`) | [Instance pipeline parameters](/docs/instance-pipeline-parameters.md)                                                 |
