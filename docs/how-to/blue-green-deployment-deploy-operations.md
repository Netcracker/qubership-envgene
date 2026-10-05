# Blue-Green Deployment deploy operations

- [Blue-Green Deployment deploy operations](#blue-green-deployment-deploy-operations)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Deploy to the origin or peer namespace](#deploy-to-the-origin-or-peer-namespace)
  - [Deploy to a non-BG namespace](#deploy-to-a-non-bg-namespace)
  - [Deploy to the controller namespace](#deploy-to-the-controller-namespace)
  - [Deploy operation summary](#deploy-operation-summary)
  - [Pipeline parameters by deploy operation](#pipeline-parameters-by-deploy-operation)
  - [BG lifecycle operations](#bg-lifecycle-operations)
  - [Related documentation](#related-documentation)

## Description

A deploy operation runs the Instance pipeline with
[`OPERATION_TYPE: DEPLOY`](/docs/instance-pipeline-parameters.md#operation_type) to deploy application
versions into a [Blue-Green Deployment (BGD)](/docs/features/blue-green-deployment.md) namespace. The
Solution Descriptor passed in
[`APPLICATION_VERSIONS`](/docs/instance-pipeline-parameters.md#application_versions) lists the
applications and versions to deploy. EnvGene renders only the namespaces those applications target,
resolved through the Namespace map.

A BG Domain exposes its origin and peer namespaces under one `deployPostfix`. When the Solution
Descriptor targets that postfix, set
[`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target) to `ORIGIN` or `PEER` so the
Namespace map binds the postfix to the right side. The controller namespace and non-BG namespaces have
their own `deployPostfix` and need no `BG_NS_TARGET`.

A deploy operation uses `OPERATION_TYPE: DEPLOY`. It is not a BG lifecycle operation. For the lifecycle
operations, see [BG lifecycle operations](#bg-lifecycle-operations).

The deploy orchestrator sets these parameters when it triggers the pipeline. Set the same parameters
for a manual run. Working examples are in
[`/docs/samples/blue-green-deployment/`](/docs/samples/blue-green-deployment/).

## Prerequisites

- An Environment configured for BGD. See
  [Configure Blue-Green Deployment](/docs/how-to/blue-green-deployment-configure.md).
- A Solution Descriptor that lists the applications to deploy.
- The [No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2) architecture. BGD runs only with
  `PIPELINE_TYPE: GITLAB_DEPLOY` and an Environment Inventory that sets `noCmdbVersion: v2`.

## Deploy to the origin or peer namespace

EnvGene renders the selected side from a template artifact version and recalculates its parameters. The
other side stays as it was. Origin and peer swap the `active` and `candidate`
[BG states](/docs/features/blue-green-deployment.md#what-state-files-tell-you) from release to release, so either
side can be the deploy target.

1. Choose the template artifact version for the side, one of:

   - Persist it in the Environment Inventory: `envTemplate.bgNsArtifacts.origin` or
     `envTemplate.bgNsArtifacts.peer`.
   - Set [`ENV_TEMPLATE_VERSION`](/docs/instance-pipeline-parameters.md#env_template_version) together
     with `BG_NS_TARGET` for this run. EnvGene writes the value into the matching `bgNsArtifacts` field.

   Without either, the side renders from the common `envTemplate.artifact`.

2. Run the Instance pipeline with the Solution Descriptor and the target side:

   ```yaml
   ENV_NAMES: "<cluster-name>/<environment-name>"
   OPERATION_TYPE: "DEPLOY"
   PIPELINE_TYPE: "GITLAB_DEPLOY"
   APPLICATION_VERSIONS: "<value>"
   BG_NS_TARGET: "PEER"
   ```

   For the origin side, set `BG_NS_TARGET: "ORIGIN"`.

3. Confirm that only the target side's namespace folder changed, for example `Namespaces/bss-peer/`. The
   other side's folder stays as it was.

The origin/peer descriptor layout is set up once when you configure the environment. See
[Configure Blue-Green Deployment](/docs/how-to/blue-green-deployment-configure.md#step-4-create-the-environment-template-descriptor).

> [!NOTE]
> The origin and peer entries share `bss.yml.j2`, so they inherit the same parametersets and resource
> profiles. When a BG cycle gives the two sides different parameters, bind an env-specific parameterset or
> resource profile to that side through `envTemplate.envSpecificParamsets` or
> `envTemplate.envSpecificResourceProfiles`, keyed by the side's deploy postfix (`bss-origin`, `bss-peer`).
> See
> [Configure Blue-Green Deployment](/docs/how-to/blue-green-deployment-configure.md#step-5-create-the-environment-inventory).

## Deploy to a non-BG namespace

A namespace outside any BG Domain has its own `deployPostfix` and renders from `envTemplate.artifact`. It
needs no `BG_NS_TARGET`. Include its applications in the Solution Descriptor and run the pipeline:

```yaml
ENV_NAMES: "<cluster-name>/<environment-name>"
OPERATION_TYPE: "DEPLOY"
PIPELINE_TYPE: "GITLAB_DEPLOY"
APPLICATION_VERSIONS: "<value>"
```

Confirm that only the namespaces referenced by the Solution Descriptor changed.

## Deploy to the controller namespace

The controller namespace is part of the BG Domain but has its own `deployPostfix`. It renders from
`envTemplate.artifact`, not from `bgNsArtifacts`, and needs no `BG_NS_TARGET`. Include the controller
applications in the Solution Descriptor and run as for a non-BG namespace.

Confirm that only the controller namespace folder changed, and that
`bg_domain.controllerNamespace.credentials` exists in the generated Credentials file. EnvGene creates it
during generation.

## Deploy operation summary

| Deploy target        | Rendered from          | `BG_NS_TARGET` |
|----------------------|------------------------|----------------|
| Origin side          | `bgNsArtifacts.origin` | `ORIGIN`       |
| Peer side            | `bgNsArtifacts.peer`   | `PEER`         |
| Controller namespace | `artifact`             | not set        |
| Non-BG namespace     | `artifact`             | not set        |

When `bgNsArtifacts` is not set, the origin and peer sides render from `artifact`.

## Pipeline parameters by deploy operation

| Parameter                                                                                | Used for                                                        |
|------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names)                           | Target environment, `<cluster-name>/<environment-name>`         |
| [`OPERATION_TYPE`](/docs/instance-pipeline-parameters.md#operation_type)                 | `DEPLOY` for a deploy operation                                 |
| [`PIPELINE_TYPE`](/docs/instance-pipeline-parameters.md#pipeline_type)                   | `GITLAB_DEPLOY` for the No-CMDB v2 architecture                     |
| [`APPLICATION_VERSIONS`](/docs/instance-pipeline-parameters.md#application_versions)     | Solution Descriptor of applications to deploy                   |
| [`BG_NS_TARGET`](/docs/instance-pipeline-parameters.md#bg_ns_target)                     | Select origin or peer when they share a `deployPostfix`         |
| [`ENV_TEMPLATE_VERSION`](/docs/instance-pipeline-parameters.md#env_template_version)     | Override the template version for this run                      |

## BG lifecycle operations

Initializing the domain, warmup, promote, rollback, and commit are BG lifecycle operations, not deploys.
They run with [`OPERATION_TYPE: BGD`](/docs/instance-pipeline-parameters.md#operation_type) and
[`BGD_OPERATION`](/docs/instance-pipeline-parameters.md#bgd_operation), and they change BG state rather
than deploy application versions. See [Blue-Green Deployment](/docs/features/blue-green-deployment.md).

## Related documentation

- [Configure Blue-Green Deployment](/docs/how-to/blue-green-deployment-configure.md)
- [Blue-Green Deployment (feature)](/docs/features/blue-green-deployment.md)
- [Environment Instance Generation](/docs/features/environment-instance-generation.md)
- [BG Domain object](/docs/envgene-objects.md#bg-domain)
- [BGD samples](/docs/samples/blue-green-deployment/)
