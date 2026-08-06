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
regenerates the configuration of the selected namespaces so a new application version can be deployed
there. Three inputs control the run:

- which namespaces are regenerated (`NS_BUILD_FILTER`)
- which template artifact version renders them
- what the run produces: the Effective Set (`GENERATE_EFFECTIVE_SET`) or a CMDB import (`CMDB_IMPORT`)

The right combination depends on the target - the origin/peer pair, the controller namespace, or a
non-BG namespace. The deploy orchestrator passes these parameters when it triggers the pipeline. Set
the same parameters for a manual run.

Working examples are in [`/docs/samples/blue-green-deployment/`](/docs/samples/blue-green-deployment/).

## Prerequisites

- An Environment configured for BGD (see
  [Migrate to Blue-Green Deployment](/docs/how-to/blue-green-deployment-migration.md))

## Deploy operations

[`NS_BUILD_FILTER`](/docs/features/namespace-render-filtering.md) selects the namespaces to
regenerate, by name or by BG Domain role alias:

- `@origin` - origin namespace
- `@peer` - peer namespace
- `@controller` - controller namespace

The examples below show the Effective Set flow. For the CMDB import flow, replace
`GENERATE_EFFECTIVE_SET` with `CMDB_IMPORT: "true"`.

> [!NOTE]
> On the GitHub pipeline, `NS_BUILD_FILTER`, `ENV_TEMPLATE_VERSION_ORIGIN`, and
> `ENV_TEMPLATE_VERSION_PEER` have no dedicated workflow inputs. Pass them through
> [`GH_ADDITIONAL_PARAMS`](/docs/instance-pipeline-parameters.md#gh_additional_params).

### Deploy in origin or peer namespace

EnvGene regenerates the selected BG-role namespace from a template artifact version and recalculates
its parameters. The other role's namespace is untouched. Either namespace can be the deploy target:
origin and peer swap the `active` and `candidate`
[BG states](/docs/features/blue-green-deployment.md#bg-state-files) from release to release.

1. Choose the template artifact version that renders the namespace, one of:

   - Persist it in the Environment Inventory: `envTemplate.bgNsArtifacts.origin` or
     `envTemplate.bgNsArtifacts.peer`.
   - Set the pipeline parameter
     [`ENV_TEMPLATE_VERSION_ORIGIN`](/docs/instance-pipeline-parameters.md#env_template_version_origin)
     or [`ENV_TEMPLATE_VERSION_PEER`](/docs/instance-pipeline-parameters.md#env_template_version_peer)
     for this run. EnvGene writes the value into the matching `bgNsArtifacts` field.

   When neither is set, the namespace renders from the common `envTemplate.artifact`.

2. Run the Instance pipeline with the role alias:

   ```yaml
   ENV_NAMES: "<cluster-name>/<environment-name>"
   ENV_BUILDER: "true"
   NS_BUILD_FILTER: "@peer"
   GENERATE_EFFECTIVE_SET: "true"
   ```

   For the origin namespace, set `NS_BUILD_FILTER: "@origin"`.

3. Confirm that only the target namespace folder changed (for example `Namespaces/bss-peer/`). The
   other role's folder stays as it was.

The descriptor layout behind the origin/peer pair is set up once during migration - see
[Migrate to Blue-Green Deployment, Step 3](/docs/how-to/blue-green-deployment-migration.md#step-3-extend-the-environment-template-descriptor).

### Deploy non-BG namespace

Namespaces outside the BG Domain (no origin/peer pair, no BG state files) always render from
`envTemplate.artifact`.

1. Run the Instance pipeline selecting the namespace by name:

   ```yaml
   ENV_NAMES: "<cluster-name>/<environment-name>"
   ENV_BUILDER: "true"
   NS_BUILD_FILTER: "<namespace-name>"
   GENERATE_EFFECTIVE_SET: "true"
   ```

   Or regenerate everything except the BG roles with
   `NS_BUILD_FILTER: "! @peer,@origin,@controller"`.

2. Confirm that only the selected namespace folders changed.

> [!NOTE]
> Mixed alias and direct name selectors in one `NS_BUILD_FILTER` expression are not allowed. See
> [Namespace Render Filter](/docs/features/namespace-render-filtering.md#multiple-selection).

### Deploy in controller namespace

The controller namespace always renders from `envTemplate.artifact`, not from `bgNsArtifacts`. Its
mapping in `bg_domain.yml` is set up once during migration - see
[Migrate to Blue-Green Deployment, Step 2](/docs/how-to/blue-green-deployment-migration.md#step-2-add-the-bg-domain-template).

1. Run the Instance pipeline with the role alias:

   ```yaml
   ENV_NAMES: "<cluster-name>/<environment-name>"
   ENV_BUILDER: "true"
   NS_BUILD_FILTER: "@controller"
   GENERATE_EFFECTIVE_SET: "true"
   ```

2. Confirm that only the `Namespaces/bg-controller/` folder changed, and that
   `bg_domain.controllerNamespace.credentials` exists in the generated Credentials file (EnvGene
   creates it during generation).

> [!NOTE]
> `bg-plugin` is not part of the BG Domain, so `@controller` does not select it. Regenerate it by
> namespace name, as for any non-BG namespace.

## Deploy operation summary

| Deploy operation     | Namespace role        | Rendered from          | Typical `NS_BUILD_FILTER` |
|----------------------|-----------------------|------------------------|---------------------------|
| Deploy in peer       | `peerNamespace`       | `bgNsArtifacts.peer`   | `@peer`                   |
| Deploy in origin     | `originNamespace`     | `bgNsArtifacts.origin` | `@origin`                 |
| Deploy non-BG        | Not in BG Domain      | `artifact`             | `<namespace-name>`        |
| Deploy in controller | `controllerNamespace` | `artifact`             | `@controller`             |

When `bgNsArtifacts` is not set, origin and peer render from `artifact`. Non-BG namespaces can also
be selected by exclusion: `! @peer,@origin,@controller`.

## Pipeline parameters by deploy operation

| Parameter                                                                                          | Used for                                                        |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names)                                     | Target environment, `<cluster-name>/<environment-name>`         |
| [`ENV_BUILDER`](/docs/instance-pipeline-parameters.md#env_builder)                                 | Enable Environment Instance generation                          |
| [`NS_BUILD_FILTER`](/docs/instance-pipeline-parameters.md#ns_build_filter)                         | Limit which namespaces are regenerated                          |
| [`ENV_TEMPLATE_VERSION`](/docs/instance-pipeline-parameters.md#env_template_version)               | Override `envTemplate.artifact` for this run                    |
| [`ENV_TEMPLATE_VERSION_ORIGIN`](/docs/instance-pipeline-parameters.md#env_template_version_origin) | Override `envTemplate.bgNsArtifacts.origin`                     |
| [`ENV_TEMPLATE_VERSION_PEER`](/docs/instance-pipeline-parameters.md#env_template_version_peer)     | Override `envTemplate.bgNsArtifacts.peer`                       |
| [`GENERATE_EFFECTIVE_SET`](/docs/instance-pipeline-parameters.md#generate_effective_set)           | Produce the Effective Set                                       |
| [`CMDB_IMPORT`](/docs/instance-pipeline-parameters.md#cmdb_import)                                 | Export the Environment Instance to a CMDB                       |
| [`BG_MANAGE`](/docs/instance-pipeline-parameters.md#bg_manage)                                     | Run BG lifecycle job (not used for ordinary deploy-only runs)   |
| [`BG_STATE`](/docs/instance-pipeline-parameters.md#bg_state)                                       | Target BG states for `bg_manage`                                |
| [`GH_ADDITIONAL_PARAMS`](/docs/instance-pipeline-parameters.md#gh_additional_params)               | Carrier for parameters without dedicated GitHub workflow inputs |

For BG lifecycle operations (warmup, promote, commit), see
[Blue-Green Deployment Use Cases](/docs/use-cases/blue-green-deployment.md).

## Related documentation

- [Migrate to Blue-Green Deployment](/docs/how-to/blue-green-deployment-migration.md)
- [Blue-Green Deployment (feature)](/docs/features/blue-green-deployment.md)
- [Blue-Green Deployment Use Cases](/docs/use-cases/blue-green-deployment.md)
- [Environment Instance Generation](/docs/features/environment-instance-generation.md)
- [Namespace Render Filter](/docs/features/namespace-render-filtering.md)
- [BG Domain object](/docs/envgene-objects.md#bg-domain)
- [BGD samples](/docs/samples/blue-green-deployment/)
