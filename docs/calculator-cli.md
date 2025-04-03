
# Calculator CLI

- [Calculator CLI](#calculator-cli)
  - [Requirements](#requirements)
  - [Proposed Approach](#proposed-approach)
    - [Calculator CLI execution attributes](#calculator-cli-execution-attributes)
    - [Registry Configuration](#registry-configuration)
    - [Effective Set v1.0](#effective-set-v10)
      - [\[Version 1.0\] Effective Set Structure](#version-10-effective-set-structure)
      - [\[Version 1.0\] deployment-parameters.yaml](#version-10-deployment-parametersyaml)
      - [\[Version 1.0\] technical-configuration-parameters.yaml](#version-10-technical-configuration-parametersyaml)
      - [\[Version 1.0\] mapping.yml](#version-10-mappingyml)
    - [Effective Set v2.0](#effective-set-v20)
      - [\[Version 2.0\] Effective Set Structure](#version-20-effective-set-structure)
      - [\[Version 2.0\] Deployment Parameter Context](#version-20-deployment-parameter-context)
        - [\[Version 2.0\] mapping.yml](#version-20-mappingyml)
      - [\[Version 2.0\] Operational Parameter Context](#version-20-operational-parameter-context)
        - [Operational Parameter Context Injected Parameters](#operational-parameter-context-injected-parameters)
          - [`composite_structure` Example](#composite_structure-example)
          - [`k8s_tokens` Example](#k8s_tokens-example)
      - [\[Version 2.0\] Runtime Parameter Context](#version-20-runtime-parameter-context)
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

## Proposed Approach

![sbom-generation.png](./images/effective-set-calculation.png)

### Calculator CLI execution attributes

Below is a **complete** list of attributes

| Attribute | Type | Mandatory | Description | Default | Example |
|---|---|---|---|---|--|
| `--env-id`/`-e` | string | yes | Environment id in `<cluster-name>/<environment-name>` notation | N/A | `"cluster/platform-00"` |
| `--envs-path`/`-ep` | string | yes | Path to `/environments` folder | N/A |  `/environments` |
| `--sboms-path`/`-sp`| string | yes | Path to the folder with Application and Environment Template SBOMs. In Solution SBOM, the path to Application SBOM and Environment Template SBOM is specified relative to this folder. | N/A |`/sboms` |
| `--solution-sbom-path`/`-ssp`| string | yes | Path to the Solution SBOM. | N/A | `/environments/cluster/platform-00/Inventory/solution-descriptor/solution.sbom.json` |
| `--registries`/`-r`| string | yes | Path to the [registry configuration](#registry-configuration) | N/A | `/configuration/registry.yml` |
| `--output`/`-o` | string | yes | Folder where the result will be put by Calculator CLI | N/A | `"/environments/cluster/platform-00/effective-set"` |
| `--effective-set-version`/`-esv` | string | no | The version of the effective set to be generated. Available options are `v1.0` and `v2.0` | `v1.0` | `v1.0` |
| `--operational-consumer-specific-schema-path`/`-ocssp` | string | no | Path to a JSON schema defining a consumer-specific operational context component. Multiple attributes of this type can be provided  | N/A |  |

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
global:
  <key>: <value>

<service-name>:
  <key>: <value>
```

#### [Version 1.0] technical-configuration-parameters.yaml

```yaml
<key>: <value>
```

#### [Version 1.0] mapping.yml

This file defines a mapping between namespaces and the corresponding paths to their respective folders. The need for this mapping arises from the fact that the effective set consumer requires information about the specific names of namespaces. However, the effective set is stored in the repository in a structure that facilitates comparisons between effective sets for environments of the same type."

```yaml
---
<namespace-name-01>: <path-to-deployPostfix-folder-01> # <namespace-name> should be get from 'name' attribute of namespace object
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
                ├── operational
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
                |   |   |   ├── parameters.yaml
                |   |   |   └── credentials.yaml
                |   |   └── <application-name-02>
                |   |       ├── parameters.yaml
                |   |       └── credentials.yaml
                |   └── <deployPostfix-02>
                |       ├── <application-name-01>
                |       |   ├── parameters.yaml
                |       |   └── credentials.yaml
                |       └── <application-name-02>
                |           ├── parameters.yaml
                |           └── credentials.yaml
                └── runtime
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

#### [Version 2.0] Deployment Parameter Context

These parameters establish a dedicated rendering context exclusively applied during application (re)deployment operations for Helm manifest rendering.

This context is formed as a result of merging parameters defined in the `deployParameters` sections of the `Tenant`, `Cloud`, `Namespace`, `Application` Environment Instance objects. Parameters from the Application SBOM and `Resource Profile` objects of the Environment Instance also contribute to the formation of this context.

For each namespace/deploy postfix, the context contains two files:

1. **parameters.yaml**: This file contains non-sensitive parameters.
2. **credentials.yaml**: This file contains sensitive parameters. If a parameter is described in the Environment Template via EnvGene credential macro, that parameter will be placed in this file.

The structure of each of these files is as follows:

```yaml
global:
  <key>: <value>

<service-name>:
  <key>: <value>
```

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

##### [Version 2.0] mapping.yml

This file defines a mapping between namespaces and the corresponding paths to their respective folders. The need for this mapping arises from the fact that the effective set consumer requires information about the specific names of namespaces. However, the effective set is stored in the repository in a structure that facilitates comparisons between effective sets for environments of the same type

```yaml
---
<namespace-name-01>: <path-to-deployPostfix-folder-01> # <namespace-name> should be get from 'name' attribute of namespace object
<namespace-name-02>: <path-to-deployPostfix-folder-02>
```

#### [Version 2.0] Operational Parameter Context

These parameters define a dedicated parameter context used for managing environment lifecycle systems, such as deployment orchestrators or CI/CD workflows.

This context is constructed from parameters defined in the `e2eParameters` sections of the `Cloud` Environment Instance object. Additionally, the following parameters are included:

##### Operational Parameter Context Injected Parameters

| Attribute | Mandatory | Description | Default | Example |
|---|---|---|---|---|
| **composite_structure** | Mandatory | Contains the unmodified  [Composite Structure](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#environment-instance-objects) object of the Environment Instance for which the Effective Set is generated. This variable is located in `parameters.yaml` | `{}`| [example](#composite_structure-example) |
| **k8s_tokens** | Mandatory | Contains deployment tokens for each namespace in the Environment Instance. The value is derived from the `data.secret` property of the Credential specified via `defaultCredentialsId` attribute in the corresponding `Namespace` or parent `Cloud`. If the attribute is not defined at the `Namespace` level, it is inherited from the parent `Cloud`. If defined at both levels, the `Namespace` value takes precedence. Either the `Cloud` or `Namespace` must define `defaultCredentialsId`. This variable is located in `credentials.yaml`.  | None | [example](#k8s_tokens-example) |

###### `composite_structure` Example

```yaml
composite_structure:
  name: "clusterA-env-1-composite-structure"
  version: 0
  id: "env-1-core"
  baseline:
    name: "env-1-core"
    type: "namespace"
  satellites:
    - name: "env-1-bss"
      type: "namespace"
    - name: "env-1-oss"
      type: "namespace"
```

###### `k8s_tokens` Example

```yaml
k8s_tokens:
  env-1-core: "ZXlKaGJHY2lPaUpTVXpJMU5pS..."
  env-1-bss: "ZXlKaGJHY2lPaUpTVXpJMU5pS..."
  env-1-oss: "URBd01EQXdNREF3TURBd01EQX..."
```

These **general** parameters are described in two files:

- **parameters.yaml**: This file contains non-sensitive parameters.
- **credentials.yaml**: This file contains sensitive parameters. If a operational parameter is described in the Environment Template via an EnvGene credential macro, that parameter will be placed in this file.

Optionally, the operational context can include file pairs containing **consumer-specific** sensitive/non-sensitive parameters. These parameters, derived as subsets of `parameters.yaml` and `credentials.yaml`, are generated based on a JSON schema provided by the `--operational-context-schema-path` attribute. Each attribute results in a separate file pair:

- **\<consumer\>-parameters.yaml**: This file contains consumer-specific non-sensitive parameters.
- **\<consumer\>-credentials.yaml**: This file contains consumer-specific sensitive parameters. If a consumer-specific parameter is described in the Environment Template via an EnvGene credential macro, that parameter will be placed in this file.

The `consumer` value is extracted from the filename (with `.schema.json` removed) of the JSON schema provided via the `--operational-context-schema-path` argument.

The structure of each of these files is as follows:

```yaml
<key>: <value>
```

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

The calculator forms consumer-specific parameters according to the following principles:

1. If the JSON schema contains a parameter that exists in the general parameters, it is added to the consumer-specific parameters
2. If the JSON schema contains a parameter that does not exist in the general parameters:
   1. If a default value is set for this parameter, it will be added to the consumer-specific parameters
   2. If no default value is set for this parameter and the parameter is not mandatory, the parameter will not be added
   3. If no default value is set for this parameter and the parameter is mandatory, the generation process will terminate with an error
3. These rules apply only to root-level parameters

[Example of consumer-specific operational context component JSON schema](../examples/consumer-v1.0.json)

#### [Version 2.0] Runtime Parameter Context

This file's parameters define a **distinct** context for managing application behavior without redeployment. These parameters can be applied without redeploying the application.

This context is formed as a result of merging parameters defined in the `technicalConfigurationParameters` sections of the `Tenant`, `Cloud`, `Namespace`, `Application` Environment Instance objects.

For each namespace/deploy postfix, the context contains two files:

- **parameters.yaml**: This file contains runtime non-sensitive parameters.
- **credentials.yaml**: This file contains runtime sensitive parameters. If a parameter is described in the Environment Template via EnvGene credential macro, that parameter will be placed in this file.

The structure of each of these files is as follows:

```yaml
global: # Optional
  <key>: <value>

<service-name>:
  <key>: <value>
```

### Macros

TBD

## Use Cases

### Effective Set Calculation

TBD
