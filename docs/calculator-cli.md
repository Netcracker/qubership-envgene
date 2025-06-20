
# Calculator CLI

- [Calculator CLI](#calculator-cli)
  - [Requirements](#requirements)
  - [Proposed Approach](#proposed-approach)
    - [Calculator CLI execution attributes](#calculator-cli-execution-attributes)
    - [Registry Configuration](#registry-configuration)
    - [Effective Set v1.0](#effective-set-v10)
      - [\[Version 1.0\] Effective Set Structure](#version-10-effective-set-structure)
      - [\[Version 1.0\] deployment-parameters.yaml](#version-10-deployment-parametersyaml)
      - [\[Version 1.0\] credentials.yaml](#version-10-credentialsyaml)
      - [\[Version 1.0\] technical-configuration-parameters.yaml](#version-10-technical-configuration-parametersyaml)
      - [\[Version 1.0\] mapping.yml](#version-10-mappingyml)
    - [Effective Set v2.0](#effective-set-v20)
      - [\[Version 2.0\] Effective Set Structure](#version-20-effective-set-structure)
      - [\[Version 2.0\] Service Inclusion Criteria and Naming Convention](#version-20-service-inclusion-criteria-and-naming-convention)
      - [\[Version 2.0\] Handling Missing Attributes in SBOM](#version-20-handling-missing-attributes-in-sbom)
      - [\[Version 2.0\] Deployment Parameter Context](#version-20-deployment-parameter-context)
        - [\[Version 2.0\]\[Deployment Parameter Context\] `deployment-parameters.yaml`](#version-20deployment-parameter-context-deployment-parametersyaml)
        - [\[Version 2.0\]\[Deployment Parameter Context\] `credentials.yaml`](#version-20deployment-parameter-context-credentialsyaml)
        - [\[Version 2.0\]\[Deployment Parameter Context\] Collision Parameters](#version-20deployment-parameter-context-collision-parameters)
        - [\[Version 2.0\]\[Deployment Parameter Context\] `deploy-descriptor.yaml`](#version-20deployment-parameter-context-deploy-descriptoryaml)
          - [Predefined `deploy-descriptor.yaml` parameters](#predefined-deploy-descriptoryaml-parameters)
          - [\[Version 2.0\] Service Artifacts](#version-20-service-artifacts)
          - [\[Version 2.0\] Primary Service Artifact](#version-20-primary-service-artifact)
        - [\[Version 2.0\]\[Deployment Parameter Context\] Per Service parameters](#version-20deployment-parameter-context-per-service-parameters)
          - [\[Version 2.0\]\[Deployment Parameter Context\] Resource Profile Processing](#version-20deployment-parameter-context-resource-profile-processing)
        - [\[Version 2.0\]\[Deployment Parameter Context\] `mapping.yml`](#version-20deployment-parameter-context-mappingyml)
      - [\[Version 2.0\] Pipeline Parameter Context](#version-20-pipeline-parameter-context)
        - [\[Version 2.0\]\[Pipeline Parameter Context\] `parameters.yaml`](#version-20pipeline-parameter-context-parametersyaml)
        - [\[Version 2.0\]\[Pipeline Parameter Context\] `credentials.yaml`](#version-20pipeline-parameter-context-credentialsyaml)
        - [\[Version 2.0\]\[Pipeline Parameter Context\] `<consumer>-parameters.yaml`](#version-20pipeline-parameter-context-consumer-parametersyaml)
        - [\[Version 2.0\]\[Pipeline Parameter Context\] `<consumer>-credentials.yaml`](#version-20pipeline-parameter-context-consumer-credentialsyaml)
      - [\[Version 2.0\] Topology Context](#version-20-topology-context)
        - [\[Version 2.0\]\[Topology Context\] `composite_structure` Example](#version-20topology-context-composite_structure-example)
        - [\[Version 2.0\]\[Topology Context\] `k8s_tokens` Example](#version-20topology-context-k8s_tokens-example)
        - [\[Version 2.0\]\[Topology Context\] `environments` Example](#version-20topology-context-environments-example)
      - [\[Version 2.0\] Runtime Parameter Context](#version-20-runtime-parameter-context)
        - [\[Version 2.0\]\[Runtime Parameter Context\] `parameters.yaml`](#version-20runtime-parameter-context-parametersyaml)
        - [\[Version 2.0\]\[Runtime Parameter Context\] `credentials.yaml`](#version-20runtime-parameter-context-credentialsyaml)
        - [\[Version 2.0\]\[Runtime Parameter Context\] `mapping.yml`](#version-20runtime-parameter-context-mappingyml)
    - [Macros](#macros)
  - [Use Cases](#use-cases)
    - [Effective Set Calculation](#effective-set-calculation)

## Requirements

1. Calculator CLI must support [Effective Set version 1.0](#effective-set-v10) generation
2. Calculator CLI must support [Effective Set version 2.0](#effective-set-v20) generation
3. Calculator CLI must process [execution attributes](#calculator-cli-execution-attributes)
4. Calculator CLI must not encrypt or decrypt sensitive parameters (credentials.yaml)
5. Calculator CLI must resolve [macros](#macros)
6. Calculator CLI should not process Parameter Sets
7. Calculator CLI must not cast parameters type
8. Calculator CLI must display reason of error
9. Calculator CLI must must not lookup, download and process any artifacts from a registry
10. The Calculator CLI must support loading and parsing SBOM files, extracting parameters for calculating the Effective Set
    1. [Solution SBOM](../schemas/solution.sbom.schema.json)
    2. [Application SBOM](../schemas/application.sbom.schema.json)
    3. [Env Template SBOM](../schemas/env-template.sbom.schema.json)
11. Calculator CLI should generate Effective Set for one environment no more than 1 minute
12. The Calculator CLI must adhere to the [Service Inclusion Criteria and Naming Convention](#version-20-service-inclusion-criteria-and-naming-convention) when compiling the application's service list.
13. Parameters in all files of Effective Set must be sorted alphabetically

## Proposed Approach

![sbom-generation.png](./images/effective-set-calculation.png)

### Calculator CLI execution attributes

Below is a **complete** list of attributes

| Attribute | Type | Mandatory | Description | Default | Example |
|---|---|---|---|---|--|
| `--env-id`/`-e` | string | yes | Environment id in `<cluster-name>/<environment-name>` notation | N/A | `cluster/platform-00` |
| `--envs-path`/`-ep` | string | yes | Path to `/environments` folder | N/A |  `/environments` |
| `--sboms-path`/`-sp`| string | yes | Path to the folder with Application and Environment Template SBOMs. In Solution SBOM, the path to Application SBOM and Environment Template SBOM is specified relative to this folder. | N/A |`/sboms` |
| `--solution-sbom-path`/`-ssp`| string | yes | Path to the Solution SBOM. | N/A | `/environments/cluster/platform-00/Inventory/solution-descriptor/solution.sbom.json` |
| `--registries`/`-r`| string | yes | Path to the [registry configuration](#registry-configuration) | N/A | `/configuration/registry.yml` |
| `--output`/`-o` | string | yes | Folder where the result will be put by Calculator CLI | N/A | `/environments/cluster/platform-00/effective-set` |
| `--effective-set-version`/`-esv` | string | no | The version of the effective set to be generated. Available options are `v1.0` and `v2.0` | `v2.0` | `v1.0` |
| `--pipeline-consumer-specific-schema-path`/`-pcssp` | string | no | Path to a JSON schema defining a consumer-specific pipeline context component. Multiple attributes of this type can be provided  | N/A |  |
| `--extra_params`/`-ex` | string | no | Additional parameters used by the Calculator for effective set generation. Multiple instances of this attribute can be provided | N/A | `DEPLOYMENT_SESSION_ID=550e8400-e29b-41d4-a716-446655440000` |

### Registry Configuration

[Registry config JSON Schema](../schemas/registry.schema.json)

[Registry config example](../schemas/registry.yml)

### Effective Set v1.0

#### [Version 1.0] Effective Set Structure

```text
...
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                ├── mapping.yml
                ├── <deployPostfix-01>
                |   ├── <application-name-01>
                |   |   ├── deployment-parameters.yaml
                |   |   ├── technical-configuration-parameters.yaml
                |   |   └── credentials.yaml
                |   └── <application-name-02>
                |       ├── deployment-parameters.yaml
                |       ├── technical-configuration-parameters.yaml
                |       └── credentials.yaml
                └── <deployPostfix-02>
                    ├── <application-name-01>
                    |   ├── deployment-parameters.yaml
                    |   ├── technical-configuration-parameters.yaml
                    |   └── credentials.yaml
                    └── <application-name-02>
                        ├── deployment-parameters.yaml
                        ├── technical-configuration-parameters.yaml
                        └── credentials.yaml
```

#### [Version 1.0] deployment-parameters.yaml

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
global: &id001
  <key-1>: <value-1>
  <key-N>: <value-N>
<service-name-1>:
  <<: *id001
  <service-key-1>: <value-1>
  <service-key-N>: <value-N>
<service-name-2>:
  <<: *id001
  <service-key-1>: <value-1>
  <service-key-N>: <value-N>
```

Each application microservice has its own dedicated section. These sections contain the same set of parameters as defined at the root level.

To avoid repetition, YAML anchors (&) are used for reusability, while aliases (*) reference them.

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

#### [Version 1.0] credentials.yaml

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

Each application microservice has its own dedicated section. These sections contain the same set of parameters as defined at the root level.

To avoid repetition, YAML anchors (&) are used for reusability, while aliases (*) reference them.

#### [Version 1.0] technical-configuration-parameters.yaml

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

#### [Version 1.0] mapping.yml

This file defines a mapping between Namespaces and their corresponding folder paths. This mapping is necessary because the Effective Set consumer requires knowledge of the specific Namespace names. However, the Effective Set is stored in the repository in a structure optimized for comparing Effective Sets across Environments.

Namespace name is taken from the `name` attribute of Namespace
Path is relative to the Instance repository (i.e., it starts with `/environments`)

```yaml
---
<namespace-name-01>: <path-to-deployPostfix-folder-01>
<namespace-name-02>: <path-to-deployPostfix-folder-02>
```

### Effective Set v2.0

#### [Version 2.0] Effective Set Structure

```text
...
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                ├── topology
                |   ├── parameters.yaml
                |   └── credentials.yaml              
                ├── pipeline
                |   ├── parameters.yaml
                |   ├── credentials.yaml
                |   ├── <consumer-name-01>-parameters.yaml
                |   ├── <consumer-name-02>-credentials.yaml
                |   ├── <consumer-name-01>-parameters.yaml
                |   └── <consumer-name-02>-credentials.yaml
                ├── deployment
                |   ├── mapping.yml
                |   ├── <deployPostfix-01>
                |   |   ├── <application-name-01>
                |   |   |   └── values
                |   |   |       ├── per-service-parameters
                |   |   |       |   ├── deployment-parameters.yaml
                |   |   |       |   ├── <service-name-01>.yaml
                |   |   |       |   └── <service-name-02>.yaml 
                |   |   |       ├── deployment-parameters.yaml
                |   |   |       ├── collision-deployment-parameters.yaml
                |   |   |       ├── credentials.yaml
                |   |   |       ├── collision-credentials.yaml
                |   |   |       └── deploy-descriptor.yaml
                |   |   └── <application-name-02>
                |   |       └── values
                |   |           ├── per-service-parameters
                |   |           |   ├── deployment-parameters.yaml
                |   |           |   ├── <service-name-01>.yaml
                |   |           |   └── <service-name-02>.yaml 
                |   |           ├── deployment-parameters.yaml
                |   |   |       ├── collision-deployment-parameters.yaml
                |   |   |       ├── credentials.yaml
                |   |   |       ├── collision-credentials.yaml
                |   |           └── deploy-descriptor.yaml
                |   └── <deployPostfix-02>
                |       ├── <application-name-01>
                |       |   └── values
                |       |       ├── per-service-parameters
                |       |       |   ├── deployment-parameters.yaml
                |       |       |   ├── <service-name-01>.yaml
                |       |       |   └── <service-name-02>.yaml 
                |       |       ├── deployment-parameters.yaml
                |       |       ├── collision-deployment-parameters.yaml
                |       |       ├── credentials.yaml
                |       |       ├── collision-credentials.yaml
                |       |       └── deploy-descriptor.yaml
                |       └── <application-name-02>
                |           └── values
                |               ├── per-service-parameters
                |               |   ├── deployment-parameters.yaml
                |               |   ├── <service-name-01>.yaml
                |               |   └── <service-name-02>.yaml 
                |               ├── deployment-parameters.yaml
                |               ├── collision-deployment-parameters.yaml
                |               ├── credentials.yaml
                |               ├── collision-credentials.yaml
                |               └── deploy-descriptor.yaml
                └── runtime
                    ├── mapping.yml
                    ├── <deployPostfix-01>
                    |   ├── <application-name-01>
                    |   |   ├── parameters.yaml
                    |   |   └── credentials.yaml
                    |   └── <application-name-02>
                    |       ├── parameters.yaml
                    |       └── credentials.yaml
                    └── <deployPostfix-02>
                        ├── <application-name-01>
                        |   ├── parameters.yaml
                        |   └── credentials.yaml
                        └── <application-name-02>
                            ├── parameters.yaml
                            └── credentials.yaml                            
```

#### [Version 2.0] Service Inclusion Criteria and Naming Convention

The services list for an individual application is generated from the Application SBOM according to the following principles.  
It includes components from the Application SBOM with these `mime-type`:

- `application/vnd.qubership.service`
- `application/vnd.qubership.configuration.smartplug`
- `application/vnd.qubership.configuration.frontend`
- `application/vnd.qubership.configuration.cdn`
- `application/vnd.qubership.configuration`
- `application/octet-stream`

The service name is derived from the `name` attribute of the Application SBOM component.

#### [Version 2.0] Handling Missing Attributes in SBOM

> [!IMPORTANT]
>
> When a required attribute is missing in the SBOM
>
> Mandatory Attributes:
> If a default exists: The default value is applied  
> If no default exists: Throws readable error
>
> Optional Attributes:
> If a default exists: The default value is applied  
> If no default exists: The attribute remains unset  

#### [Version 2.0] Deployment Parameter Context

These parameters establish a dedicated rendering context exclusively applied during application (re)deployment operations for Helm manifest rendering.

This context is formed as a result of merging parameters defined in the `deployParameters` sections of the `Tenant`, `Cloud`, `Namespace`, `Application` Environment Instance objects. Parameters from the Application SBOM and `Resource Profile` objects of the Environment Instance also contribute to the formation of this context.

For each namespace/deploy postfix, the context contains files:

##### \[Version 2.0][Deployment Parameter Context] `deployment-parameters.yaml`

This file contains non-sensitive parameters defined in the `deployParameters` sections of the `Tenant`, `Cloud`, `Namespace`, `Application` Environment Instance objects.

The structure of this file is as follows:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
global: &id001
  <key-1>: <value-1>
  <key-N>: <value-N>
<service-name-1>: *id001
<service-name-2>: *id001
```

Each application microservice has its own dedicated section. These sections contain **the same** set of parameters as defined at the root level.

To avoid repetition, YAML anchors (&) are used for reusability, while aliases (*) reference them.

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

> [!IMPORTANT]
> Parameters whose keys match the name of one of the services must be excluded from this file
> and placed in [`collision-deployParameters.yaml`](#version-20deployment-parameter-context-collision-parameters) instead

##### \[Version 2.0][Deployment Parameter Context] `credentials.yaml`

This file contains sensitive parameters defined in the `deployParameters` section. If the parameter is described in the Environment Template via EnvGene credential macro, that parameter will be placed in this file.  
The structure of this file is as follows:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
global: &id001
  <key-1>: <value-1>
  <key-N>: <value-N>
<service-name-1>: *id001
<service-name-2>: *id001
```

> [!IMPORTANT]
> Parameters whose keys match the name of one of the services must be excluded from this file
> and placed in [`collision-credentials.yaml`](#version-20deployment-parameter-context-collision-parameters) instead

##### \[Version 2.0][Deployment Parameter Context] Collision Parameters

Parameters whose key matches the name of one of the [services](#version-20-service-inclusion-criteria-and-naming-convention) are placed in the following files:

- `collision-deployment-parameters.yaml`: if the parameter is non-sensitive (i.e., not defined via a credential macro).
- `collision-credentials.yaml`: if the parameter is sensitive (i.e., defined via a credential macro).

The structure of both files is following:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

These files must only contain keys that match the name of a [services](#version-20-service-inclusion-criteria-and-naming-convention)

##### \[Version 2.0][Deployment Parameter Context] `deploy-descriptor.yaml`

This file describes the parameters of the application artifacts generated during the build process. These parameters are extracted from the Application's SBOM. The file contains a **predefined** set of parameters, and users cannot modify it.

>[!Note]
> The `DEPLOYMENT_SESSION_ID` parameter is an exception to this rule - it is taken from `extra_params`

The structure of this file is as follows:

```yaml
global: &id001
  deployDescriptor: &id003
    <service-name-1>:
      <service-predefined-key-1>: <service-predefined-value-1>
      <service-predefined-key-N>: <service-predefined-value-N>
    <service-name-2>:
      <service-predefined-key-1>: <service-predefined-value-1>
      <service-predefined-key-N>: <service-predefined-value-N>
deployDescriptor: *id003
<service-name-1>: &id002
  <common-predefined-key-1>: <common-predefined-value-1>
  <common-predefined-key-N>: <common-predefined-value-N>
  deployDescriptor: *id003
  global: *id001
<service-name-2>: *id002
<common-predefined-key-1>: <common-predefined-value-1>
<common-predefined-key-N>: <common-predefined-value-N>
```

###### Predefined `deploy-descriptor.yaml` parameters

The structure of **service predefined** parameters in deploy-descriptor.yaml depends on the service type, determined by the MIME type assigned to the service in the SBOM. There are two types:

**Image Type**. Defined in the SBOM as components with these MIME types:

- `application/vnd.qubership.service`
- `application/octet-stream`

**Config Type**. Defined in the SBOM as components with these MIME types:

- `application/vnd.qubership.configuration.smartplug`
- `application/vnd.qubership.configuration.frontend`
- `application/vnd.qubership.configuration.cdn`
- `application/vnd.qubership.configuration`

**Common predefined** parameters have the same structure for all services.
Below are the descriptions of predefined parameters.

Common Predefined Parameters:

| Attribute | Mandatory | Type | Description | Default | Source in Application SBOM |
|---|---|---|---|---|---|
| `APPLICATION_NAME` | yes | string | Name of the application | None | `.metadata.component.name` |
| `DEPLOYMENT_SESSION_ID` | yes | string | Effective Set calculation operation ID  | None | Taken from input parameter  `DEPLOYMENT_SESSION_ID` passed via `extra_params` (not from SBOM) |

**Image Type** Service Predefined Parameters:

| Attribute | Mandatory | Type | Description | Default | Source in Application SBOM |
|---|---|---|---|---|---|
| `artifacts` | yes | list | always `[]` | `[]` | None |
| `deploy_param` | yes | string | None | `""` | `.components[?name=<service-name>].properties[?name=deploy_param].value` |
| `docker_digest` | yes | string | Docker image checksum for the service, calculated using `SHA-256` algorithm | `""` | `.components[?name=<service-name>].components[?mime-type=application/vnd.docker.image].hashes[0].content` |
| `docker_registry` | yes | string | None | None | `.components[?name=<service-name>].properties[?name=docker_registry].value` |
| `docker_repository_name` | yes | string | The registry repository where the Docker image is located | None | `.components[?name=<service-name>].components[?mime-type=application/vnd.docker.image].group` |
| `docker_tag` | yes | string | Docker image version | None | `.components[?name=<service-name>].components[?mime-type=application/vnd.docker.image].version` |
| `full_image_name` | yes | string | None | None | `.components[?name=<service-name>].properties[?name=full_image_name].value` |
| `git_branch` | yes | string | Source code branch name used for service build | None | `.components[?name=<service-name>].properties[?name=git_branch].value` |
| `git_revision` | yes | string | Git revision of the repository used for the build | None | `.components[?name=<service-name>].properties[?name=git_revision].value` |
| `git_url` | yes | string | None | None | `.components[?name=<service-name>].properties[?name=git_url].value` |
| `image` | yes | string | The same as `full_image_name` | None | `.components[?name=<service-name>].properties[?name=full_image_name].value` |
| `image_name` | yes | string | Docker image name | None | `.components[?name=<service-name>].components[?mime-type=application/vnd.docker.image].name` |
| `image_type` | yes | string | None | None | `.components[?name=<service-name>].properties[?name=image_type].value` |
| `name` | yes | string | Service name | None | `<service-name>` |
| `promote_artifacts` | yes | bool | None | None | `.components[?name=<service-name>].properties[?name=promote_artifacts].value` |
| `qualifier` | yes | string | None | None | `.components[?name=<service-name>].properties[?name=qualifier].value` |
| `version` | yes | string | Service version | None | `.components[?name=<service-name>].version` |

**Config Type** Service Predefined Parameters:

| Attribute | Mandatory | Type | Description | Default | Source in Application SBOM |
|---|---|---|---|---|---|
| `artifact` | no | string | [Primary Service Artifact](#version-20-primary-service-artifact) | None | None |
| `artifact.artifactId` | no | string | artifact ID of [Primary Service Artifact](#version-20-primary-service-artifact) | None | `<primary-service-artifact>.name`|
| `artifact.groupId` | no | string | group ID of [Primary Service Artifact](#version-20-primary-service-artifact)  | None | `<primary-service-artifact>.group` |
| `artifact.version` | no | string | version of [Primary Service Artifact](#version-20-primary-service-artifact)  | None | `<primary-service-artifact>.version`|
| `artifacts` | yes | list | This section defines microservice artifacts. Artifacts are only populated for services/SBOM components that meet [specified conditions](#version-20-service-artifacts). All other cases should return `[]` | `[]` | None |
| `artifacts[].artifact_id` | yes | string | always `''` | `''` | None |
| `artifacts[].artifact_path` | yes | string | always `''` | `''` | None |
| `artifacts[].artifact_type` | yes | string | always `''` | `''` | None |
| `artifacts[].classifier` | yes | string | None | None | `.components[?name=<service-name>].components[].properties[?name=classifier].value` |
| `artifacts[].deploy_params` | yes | string | always `''` | `''` | None |
| `artifacts[].gav` | yes | string | always `''` | `''` | None |
| `artifacts[].group_id` | yes | string | always `''` | `''` | None |
| `artifacts[].id` | yes | string | GAV coordinates of the artifact. Constructed by concatenating the `group`, `name`, and `version` attributes using `:` as separator | None | `.components[?name=<service-name>].components[].group`:`.components[?name=<service-name>].components[].name`:`.components[?name=<service-name>].components[].version` |
| `artifacts[].name` | yes | string | Constructed by concatenating the `name`, `version` and `type` attributes using `-` and `.`  as separator | None | `.components[?name=<service-name>].components[].name`-`.components[?name=<service-name>].components[].version`.`.components[?name=<service-name>].components[].properties[?name=type].value` |
| `artifacts[].repository` | yes | string | always `''` | `''` | None |
| `artifacts[].type` | yes | string | None | None | `.components[?name=<service-name>].components[].properties[?name=type].value` |
| `artifacts[].url` | yes | string | always `''` | `''` | None |
| `artifacts[].version` | yes | string | always `''` | `''` | None |
| `build_id_dtrust` | yes | string | None | None | `.components[?name=<service-name>].components[].properties[?name=build_id_dtrust].value` |
| `git_branch` | yes | string | Source code branch name used for service build | None | `.components[?name=<service-name>].properties[?name=git_branch].value` |
| `git_revision` | yes | string | Git revision of the repository used for the build | None | `.components[?name=<service-name>].properties[?name=git_revision].value` |
| `git_url` | yes | string | None | None | `.components[?name=<service-name>].components[].properties[?name=git_url].value` |
| `maven_repository` | yes | string | None | None | `.components[?name=<service-name>].components[].properties[?name=maven_repository].value` |
| `name` | yes | string | Service name | None | `<service-name>` |
| `service_name` | yes | string | Service name | None | `<service-name>` |
| `tArtifactNames` | yes | hashmap | always `{}` | `{}` | None |
| `type` | no | string | None | None | `.components[?name=<service-name>].components[].properties[?name=type].value` |
| `version` | yes | string | Service version | None | `.components[?name=<service-name>].version` |

###### [Version 2.0] Service Artifacts

Only services in the SBOM that have these MIME types may contain artifacts:

- `application/vnd.qubership.configuration.smartplug`  
- `application/vnd.qubership.configuration.frontend`  
- `application/vnd.qubership.configuration.cdn`  
- `application/vnd.qubership.configuration`

If such SBOM components contain child components of these types, an `artifacts[]` element is created for each child component:

- `application/xml`
- `application/zip`
- `application/vnd.osgi.bundle`
- `application/java-archive`

###### [Version 2.0] Primary Service Artifact

Among the artifacts of service, one primary artifact is identified that requires special processing during service deployment. The selection criteria are as follows:

- For `application/vnd.qubership.configuration.smartplug` select the `application/vnd.osgi.bundle` component:  
  `.components[?name=<service-name>].components[?mime-type=application/vnd.osgi.bundle]`

- For `application/vnd.qubership.configuration.frontend` select the `application/zip` component:  
  `.components[?name=<service-name>].components[?mime-type=application/zip]`

- For `application/vnd.qubership.configuration.cdn` select the `application/zip` component:  
  `.components[?name=<service-name>].components[?mime-type=application/zip]`

- For `application/vnd.qubership.configuration` select the `application/zip` component:  
  `.components[?name=<service-name>].components[?mime-type=application/zip]`

> [!IMPORTANT]
>
> 1. For each such service, only one artifact should meet these criteria. Otherwise, the generation process must fail with a clear error message.
> 2. For unspecified `mime-type`, there is no primary artifact

##### \[Version 2.0][Deployment Parameter Context] Per Service parameters

Per-service parameters contain service-specific parameters, generated by combining **Application SBOM** and **Resource Profile Overrides** from the Environment Instance, and are stored across multiple files:  

- `deployment-parameters.yaml`
- `<service-name>.yaml`

`deployment-parameters.yaml` contains parameters for **all application services** in a single file. Structure:

```yaml
<service-name-1>:
  <per-service-key-1>: <service-value-1>
  <per-service-key-N>: <service-value-N>
<service-name-2>:
  <per-service-key-1>: <service-value-1>
  <per-service-key-N>: <service-value-N>
```

`<service-name>.yaml` Contains parameters for a single service (one file per service). Structure:

```yaml
<per-service-key-1>: <service-value-1>
<per-service-key-N>: <service-value-N>
```

The set of parameter in `<service-name>.yaml` and the corresponding service section in `deployment-parameters.yaml are identical`

> [!NOTE]
> The reason for storing the same parameters in different files is to support
> various Helm chart creation cases (app chart, non-app chart, etc.)

Set of per service keys depends on the service type, determined by the MIME type assigned to the service in the SBOM. There are two types:

**Image Type**. Defined in the SBOM as components with these MIME types:

- `application/vnd.qubership.service`
- `application/octet-stream`

**Config Type**. Defined in the SBOM as components with these MIME types:

- `application/vnd.qubership.configuration.smartplug`
- `application/vnd.qubership.configuration.frontend`
- `application/vnd.qubership.configuration.cdn`
- `application/vnd.qubership.configuration`

**Image Type** Per Service Parameters:

| Attribute | Mandatory | Type | Description | Default | Source in Application SBOM |
|---|---|---|---|---|---|
| `ARTIFACT_DESCRIPTOR_VERSION` | yes | string | `.metadata.component.version` | None | None |
| `DEPLOYMENT_RESOURCE_NAME` | yes | string | Is formed by concatenating `<service-name>`-v1 | None | None |
| `DEPLOYMENT_VERSION` | yes | string | always `v1` | `v1` | None |
| `DOCKER_TAG` | yes | string | None | None | `.components[?name=<service-name>].properties[?name=full_image_name].value` |
| `IMAGE_REPOSITORY` | yes | string | None | None | `.components[?name=<service-name>].properties[?name=full_image_name].value.split(':')[0]` |
| `SERVICE_NAME` | yes | string | `<service-name>` | None | None |
| `TAG` | yes | string | Docker image version | None | `.components[?name=<service-name>].components[?mime-type=application/vnd.docker.image].version` |

**Config Type** Per Service Parameters:

| Attribute | Mandatory | Type | Description | Default | Source in Application SBOM |
|---|---|---|---|---|---|
| `ARTIFACT_DESCRIPTOR_VERSION` | yes | string | `.metadata.component.version` | None | None |
| `DEPLOYMENT_RESOURCE_NAME` | yes | string | Is formed by concatenating `<service-name>`-v1 | None | None |
| `DEPLOYMENT_VERSION` | yes | string | always `v1` | `v1` | None |
| `SERVICE_NAME` | yes | string | `<service-name>` | None | None |

###### \[Version 2.0][Deployment Parameter Context] Resource Profile Processing

Only components with the following types **optionally** contain a Resource Profile Baseline:

- `application/vnd.qubership.service`
- `application/vnd.qubership.configuration.smartplug`
- `application/vnd.qubership.configuration.frontend`
- `application/vnd.qubership.configuration.cdn`
- `application/vnd.qubership.configuration`

Per-service-specific parameters include performance parameters, generated by merging:

- Baseline Resource Profile. Located in Application SBOM in `.components[?name=<service-name>].components[?mime-type=application/vnd.qubership.resource-profile-baseline]` (Optional, if present in the SBOM for the corresponding component)
- Resource Profile Override. Located in Environment Instance

##### \[Version 2.0][Deployment Parameter Context] `mapping.yml`

This file defines a mapping between Namespaces and their corresponding folder paths. This mapping is necessary because the Effective Set consumer requires knowledge of the specific Namespace names. However, the Effective Set is stored in the repository in a structure optimized for comparing Effective Sets across Environments.

Namespace name is taken from the `name` attribute of Namespace
Path is relative to the Instance repository (i.e., it starts with `/environments`)

```yaml
---
<namespace-name-01>: <path-to-deployPostfix-folder-01>
<namespace-name-02>: <path-to-deployPostfix-folder-02>
```

#### [Version 2.0] Pipeline Parameter Context

These parameters define a dedicated parameter context used for managing environment lifecycle systems, such as deployment orchestrators or CI/CD workflows.

This context is constructed from parameters defined in the `e2eParameters` sections of the `Cloud` Environment Instance object. Such parameters are described in [`parameters.yaml`](#version-20pipeline-parameter-context-parametersyaml) and [`credentials.yaml`](#version-20pipeline-parameter-context-credentialsyaml).

Optionally, the pipeline context can include file pairs containing **consumer-specific** [sensitive](#version-20pipeline-parameter-context-consumer-credentialsyaml)/[non-sensitive](#version-20pipeline-parameter-context-consumer-parametersyaml) parameters. These parameters, derived as subsets of `parameters.yaml` and `credentials.yaml`, are generated based on a JSON schema provided by the `--pipeline-context-schema-path` attribute. Each attribute results in a separate file pair:

##### \[Version 2.0][Pipeline Parameter Context] `parameters.yaml`

This file contains non-sensitive parameters defined in the `e2eParameters` section.  
The structure of this file is as follows:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

##### \[Version 2.0][Pipeline Parameter Context] `credentials.yaml`

This file contains sensitive parameters defined in the `e2eParameters` section. If the parameter is described in the Environment Template via EnvGene credential macro, that parameter will be placed in this file.  
The structure of this file is as follows:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

##### \[Version 2.0][Pipeline Parameter Context] `<consumer>-parameters.yaml`

This file contains consumer-specific non-sensitive parameters.
The structure of this file is as follows:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

##### \[Version 2.0][Pipeline Parameter Context] `<consumer>-credentials.yaml`

This file contains consumer-specific sensitive parameters. If a consumer-specific parameter is described in the Environment Template via an EnvGene credential macro, that parameter will be placed in this file.

The `consumer` value is extracted from the filename (with `.schema.json` removed) of the JSON schema provided via the `--pipeline-context-schema-path` argument.

The structure of this file is as follows:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

The calculator forms consumer-specific parameters according to the following principles:

1. If the JSON schema contains a parameter that exists in the general parameters, it is added to the consumer-specific parameters
2. If the JSON schema contains a parameter that does not exist in the general parameters:
   1. If a default value is set for this parameter, it will be added to the consumer-specific parameters
   2. If no default value is set for this parameter and the parameter is not mandatory, the parameter will not be added
   3. If no default value is set for this parameter and the parameter is mandatory, the generation process will terminate with an error
3. These rules apply only to root-level parameters

[Example of consumer-specific pipeline context component JSON schema](../examples/consumer-v1.0.json)

#### [Version 2.0] Topology Context

The Topology Context contains information about the relationships between systems and their components. It includes two files:

- `parameters.yaml` for non-sensitive data  
- `credentials.yaml` for sensitive data  

This context only contains parameters generated by EnvGene:

| Attribute | Mandatory | Description | Default | Example |
|---|---|---|---|---|
| **composite_structure** | Mandatory | Contains the unmodified  [Composite Structure](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#environment-instance-objects) object of the Environment Instance for which the Effective Set is generated. This variable is located in `parameters.yaml` | `{}`| [example](#version-20topology-context-composite_structure-example) |
| **k8s_tokens** | Mandatory | Contains deployment tokens for each namespace in the Environment Instance. The key represents the `name` attribute of the `Namespace`. The value is derived from the `data.secret` property of the Credential specified via `defaultCredentialsId` attribute in the corresponding `Namespace` or parent `Cloud`. If the attribute is not defined at the `Namespace` level, it is inherited from the parent `Cloud`. If defined at both levels, the `Namespace` value takes precedence. Either the `Cloud` or `Namespace` must define `defaultCredentialsId`. This variable is located in `credentials.yaml` | None | [example](#version-20topology-context-k8s_tokens-example) |
| **environments** | Mandatory | Contains all repository Environments, not just the one for which the Effective Set calculation was run. For each Environment, it includes the names of its contained namespaces. For each namespace, it provides a deploy postfix. The deploy postfix is taken from the namespace template name (the template filename without extension). This variable is located in `parameters.yaml`  | None | [example](#version-20topology-context-environments-example) |

##### \[Version 2.0][Topology Context] `composite_structure` Example

```yaml
composite_structure:
  name: "clusterA-env-1-composite-structure"
  baseline:
    name: "env-1-core"
    type: "namespace"
  satellites:
    - name: "env-1-bss"
      type: "namespace"
    - name: "env-1-oss"
      type: "namespace"
```

##### \[Version 2.0][Topology Context] `k8s_tokens` Example

```yaml
k8s_tokens:
  env-1-core: "ZXlKaGJHY2lPaUpTVXpJMU5pS..."
  env-1-bss: "ZXlKaGJHY2lPaUpTVXpJMU5pS..."
  env-1-oss: "URBd01EQXdNREF3TURBd01EQX..."
```

##### \[Version 2.0][Topology Context] `environments` Example

```yaml
environments:
  cluster-x/env-y:
    namespaces:
      env-1-core:
        deployPostfix: core
      env-1-bss:
        deployPostfix: bss
```

#### [Version 2.0] Runtime Parameter Context

This file's parameters define a **distinct** context for managing application behavior without redeployment. These parameters can be applied without redeploying the application.

This context is formed as a result of merging parameters defined in the `technicalConfigurationParameters` sections of the `Tenant`, `Cloud`, `Namespace`, `Application` Environment Instance objects.

For each namespace/deploy postfix, the context contains two files:

##### \[Version 2.0][Runtime Parameter Context] `parameters.yaml`

This file contains runtime non-sensitive parameters defined in the `technicalConfigurationParameters` section.
The structure of this file is as follows:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

##### \[Version 2.0][Runtime Parameter Context] `credentials.yaml`

This file contains sensitive parameters defined in the `technicalConfigurationParameters` section. If the parameter is described in the Environment Template via EnvGene credential macro, that parameter will be placed in this file  
The structure of this file is as follows:

```yaml
<key-1>: <value-1>
<key-N>: <value-N>
```

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

##### \[Version 2.0][Runtime Parameter Context] `mapping.yml`

The contents of this file are identical to [mapping.yml in the Deployment Parameter Context](#version-20deployment-parameter-context-mappingyml)

### Macros

TBD

## Use Cases

### Effective Set Calculation

TBD
