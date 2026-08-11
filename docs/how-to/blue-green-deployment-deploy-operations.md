# Blue-Green Deployment deploy operations

- [Blue-Green Deployment deploy operations](#blue-green-deployment-deploy-operations)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Deploy operations](#deploy-operations)
    - [Deploy in origin or peer namespace](#deploy-in-origin-or-peer-namespace)
    - [Deploy non-BG namespace](#deploy-non-bg-namespace)
    - [Deploy in controller namespace](#deploy-in-controller-namespace)
  - [Deploy operation summary](#deploy-operation-summary)
  - [Pipeline parameters by deploy operation](#pipeline-parameters-by-deploy-operation)
  - [Related documentation](#related-documentation)

## Description

An Instance pipeline run is part of a
[Blue-Green Deployment (BGD)](/docs/features/blue-green-deployment.md) deploy operation: it
regenerates the configuration of the Namespaces that belong to the applications in the current
[Solution Descriptor](/docs/envgene-objects.md#solution-descriptor) (SD) so a new application version
can be deployed there. Three inputs control the run:

- which Namespaces are regenerated (automatic selection from the SD via
  [Namespace map](/docs/tech/namespace-map.md) and
  [Namespace render filtering](/docs/features/namespace-render-filtering.md))
- which template artifact version renders them
- what the run produces: the Effective Set (`GENERATE_EFFECTIVE_SET`) or a CMDB import (`CMDB_IMPORT`)

For a BG Domain side, also set
[`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) so the Namespace map binds each
shared `deployPostfix` to origin or peer. `BG_NS_TARGET` is not a render filter.

The right combination depends on the target - the origin/peer pair, the controller namespace, or a
non-BG namespace. The deploy orchestrator passes these parameters when it triggers the pipeline. Set
the same parameters for a manual run.

Working examples are in [`/docs/samples/blue-green-deployment/`](/docs/samples/blue-green-deployment/).

## Prerequisites

- An Environment configured for BGD (see
  [Migrate to Blue-Green Deployment](/docs/how-to/blue-green-deployment-migration.md))

## Deploy operations

When the run supplies an SD, EnvGene resolves application
[`deployPostfix`](/docs/glossary.md#deploy-postfix) values through the Namespace map and
`env_build` re-renders only the resulting Namespace `name` values. See
[Namespace render filtering](/docs/features/namespace-render-filtering.md).

The examples below show the Effective Set flow. For the CMDB import flow, replace
`GENERATE_EFFECTIVE_SET` with `CMDB_IMPORT: "true"`.

> [!NOTE]
> On the GitHub pipeline, `BG_NS_TARGET` and related template-version overrides have no dedicated
> workflow inputs. Pass them through
> [`GH_ADDITIONAL_PARAMS`](/docs/instance-pipeline-parameters.md#gh_additional_params).

### Deploy in origin or peer namespace

EnvGene regenerates the BG-role Namespace selected by the Namespace map from a template artifact
version and recalculates its parameters. The other role's Namespace is untouched. Either Namespace
can be the deploy target: origin and peer swap the `active` and `candidate`
[BG states](/docs/features/blue-green-deployment.md#state-storage) from release to release.

1. Choose the template artifact version that renders the namespace, one of:

   - Persist it in the Environment Inventory: `envTemplate.bgNsArtifacts.origin` or
     `envTemplate.bgNsArtifacts.peer`.
   - Set [`ENV_TEMPLATE_VERSION`](/docs/instance-pipeline-parameters.md#env_template_version) together
     with [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) `origin` or `peer` for
     this run. EnvGene writes the value into the matching `bgNsArtifacts` field.

   When neither is set, the namespace renders from the common `envTemplate.artifact`.

2. Run the Instance pipeline with the SD for the applications to deploy and the BG side:

   ```yaml
   ENV_NAMES: "<cluster-name>/<environment-name>"
   ENV_BUILDER: "true"
   SD_SOURCE_TYPE: artifact
   SD_VERSION: "<application>:<version>"
   BG_NS_TARGET: peer
   GENERATE_EFFECTIVE_SET: "true"
   ```

   For the origin namespace, set `BG_NS_TARGET: origin`.

3. Confirm that only the target namespace folder changed (for example `Namespaces/bss-peer/`). The
   other role's folder stays as it was.

The descriptor layout behind the origin/peer pair is set up once during migration - see
[Migrate to Blue-Green Deployment, Step 3](/docs/how-to/blue-green-deployment-migration.md#step-3-extend-the-environment-template-descriptor).

### Deploy non-BG namespace

Namespaces outside the BG Domain (no origin/peer pair, no BG state files) always render from
`envTemplate.artifact`.

1. Run the Instance pipeline with an SD whose applications map to that Namespace:

   ```yaml
   ENV_NAMES: "<cluster-name>/<environment-name>"
   ENV_BUILDER: "true"
   SD_SOURCE_TYPE: artifact
   SD_VERSION: "<application>:<version>"
   GENERATE_EFFECTIVE_SET: "true"
   ```

2. Confirm that only the Namespace folders selected through the Namespace map changed.

### Deploy in controller namespace

The controller namespace always renders from `envTemplate.artifact`, not from `bgNsArtifacts`. Its
mapping in `bg_domain.yml` is set up once during migration - see
[Migrate to Blue-Green Deployment, Step 2](/docs/how-to/blue-green-deployment-migration.md#step-2-add-the-bg-domain-template).

1. Run the Instance pipeline with an SD whose applications map to the controller Namespace through
   the Namespace map:

   ```yaml
   ENV_NAMES: "<cluster-name>/<environment-name>"
   ENV_BUILDER: "true"
   SD_SOURCE_TYPE: artifact
   SD_VERSION: "<application>:<version>"
   GENERATE_EFFECTIVE_SET: "true"
   ```

2. Confirm that only the controller Namespace folder changed, and that
   `bg_domain.controllerNamespace.credentials` exists in the generated Credentials file (EnvGene
   creates it during generation).

> [!NOTE]
> `bg-plugin` is not part of the BG Domain. Regenerate it the same way as any non-BG Namespace:
> supply an SD whose applications map to that Namespace.

## Deploy operation summary

| Deploy operation     | Namespace role        | Rendered from          | Side / selection input                          |
|----------------------|-----------------------|------------------------|-------------------------------------------------|
| Deploy in peer       | `peerNamespace`       | `bgNsArtifacts.peer`   | SD apps + `BG_NS_TARGET: peer`                  |
| Deploy in origin     | `originNamespace`     | `bgNsArtifacts.origin` | SD apps + `BG_NS_TARGET: origin`                |
| Deploy non-BG        | Not in BG Domain      | `artifact`             | SD apps via Namespace map                       |
| Deploy in controller | `controllerNamespace` | `artifact`             | SD apps via Namespace map                       |

When `bgNsArtifacts` is not set, origin and peer render from `artifact`.

## Pipeline parameters by deploy operation

| Parameter                                                                                | Used for                                                        |
|------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names)                           | Target environment, `<cluster-name>/<environment-name>`         |
| [`ENV_BUILDER`](/docs/instance-pipeline-parameters.md#env_builder)                       | Enable Environment Instance generation                          |
| [`SD_SOURCE_TYPE`](/docs/instance-pipeline-parameters.md#sd_source_type)                 | How the Solution Descriptor is supplied                         |
| [`SD_VERSION`](/docs/instance-pipeline-parameters.md#sd_version)                         | SD artifact for this run                                        |
| [`SD_DATA`](/docs/instance-pipeline-parameters.md#sd_data)                               | Inline SD content for this run                                  |
| [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target)                     | Bind shared `deployPostfix` to origin or peer in Namespace map |
| [`ENV_TEMPLATE_VERSION`](/docs/instance-pipeline-parameters.md#env_template_version)     | Override template artifact / `bgNsArtifacts` with `BG_NS_TARGET` |
| [`GENERATE_EFFECTIVE_SET`](/docs/instance-pipeline-parameters.md#generate_effective_set) | Produce the Effective Set                                       |
| [`CMDB_IMPORT`](/docs/instance-pipeline-parameters.md#cmdb_import)                       | Export the Environment Instance to a CMDB                       |
| [`BG_MANAGE`](/docs/instance-pipeline-parameters.md#bg_manage)                           | Run BG lifecycle job (not used for ordinary deploy-only runs)   |
| [`BG_STATE`](/docs/instance-pipeline-parameters.md#bg_state)                             | Target BG states for `bg_manage`                                |
| [`GH_ADDITIONAL_PARAMS`](/docs/instance-pipeline-parameters.md#gh_additional_params)     | Carrier for parameters without dedicated GitHub workflow inputs |

For BG lifecycle operations (warmup, promote, commit), see
[Blue-Green Deployment Use Cases](/docs/use-cases/blue-green-deployment.md).

## Related documentation

- [Migrate to Blue-Green Deployment](/docs/how-to/blue-green-deployment-migration.md)
- [Blue-Green Deployment (feature)](/docs/features/blue-green-deployment.md)
- [Blue-Green Deployment Use Cases](/docs/use-cases/blue-green-deployment.md)
- [Environment Instance Generation](/docs/features/environment-instance-generation.md)
- [Namespace render filtering](/docs/features/namespace-render-filtering.md)
- [Namespace map](/docs/tech/namespace-map.md)
- [BG Domain object](/docs/envgene-objects.md#bg-domain)
- [BGD samples](/docs/samples/blue-green-deployment/)
