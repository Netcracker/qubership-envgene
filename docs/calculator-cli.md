
# Calculator CLI

- [Calculator CLI](#calculator-cli)
  - [Requirements](#requirements)
  - [Assumptions](#assumptions)
  - [Proposed Approach](#proposed-approach)
    - [Calculator CLI execution attributes](#calculator-cli-execution-attributes)
    - [Registry Configuration](#registry-configuration)
    - [Effective Set](#effective-set)
      - [Effective Set Structure](#effective-set-structure)
      - [deployment-parameters.yaml](#deployment-parametersyaml)
      - [credentials.yaml](#credentialsyaml)
      - [technical-configuration-parameters.yaml](#technical-configuration-parametersyaml)
      - [mapping.yml](#mappingyml)
    - [Macros](#macros)
    - [Parameters in Effective Set don't Originate from Environment Instance](#parameters-in-effective-set-dont-originate-from-environment-instance)
  - [Use Cases](#use-cases)
    - [Effective Set Calculation](#effective-set-calculation)
  - [Validation](#validation)
  - [Tests](#tests)
    - [Unit Tests](#unit-tests)
    - [e2e Tests](#e2e-tests)

## Requirements

1. Calculator CLI must generate [Effective Set](#effective-set)
   1. Calculator CLI must generate Effective Set with deployment parameters (deployment-parameters.yaml)
   2. Calculator CLI must generate Effective Set with technical parameters (technical-configuration-parameters.yaml)
   3. ~~Calculator CLI must generate Effective Set with e2e parameters (???)~~
   4. Calculator CLI must generate Effective Set with sensitive parameters (credentials.yaml)
2. Calculator CLI must process [execution attributes](#calculator-cli-execution-attributes)  
3. Calculator CLI must not encrypt or decrypt sensitive parameters (credentials.yaml)
4. Calculator CLI must resolve [macros](#macros)
5. Calculator CLI should not process Parameter Sets
6. Calculator CLI must not cast parameters type
7. Calculator CLI must display reason of error
8. Calculator CLI must must not lookup, download and process any artifacts from a registry.
9. ~~Effective Set must includes deployment token in sensitive parameters (credentials.yaml)~~
   1. ~~Deployment token, stored as sensitive parameters, are selected based on the defining object's priority. Tokens can be defined at both the Cloud and Namespace levels. The highest-priority (Namespace) token available is used.~~
10. ~~Effective Set must includes ssl certificate in sensitive parameters (credentials.yaml)~~
11. The Calculator CLI must support loading and parsing SBOM files, extracting parameters for calculating the Effective Set
       1. [Solution SBOM](https://github.com/netcracker/qubership-envgene/blob/main/schemas/solution.sbom.schema.json)
   2. [Application SBOM](https://github.com/netcracker/qubership-envgene/blob/main/schemas/application.sbom.schema.json)
   3. [Env Template SBOM](https://github.com/netcracker/qubership-envgene/blob/main/schemas/env-template.sbom.schema.json)
12. Calculator CLI should generate Effective Set for one environment no more than 1 minute

## Assumptions

1. Calculator CLI is not support SNAPSHOT versions of Deployment Descriptor and Solution Descriptor artifacts

## Proposed Approach

![sbom-generation.png](./images/effective-set-calculation.png)

### Calculator CLI execution attributes

Below is a **complete** list of attributes

| Attribute | Type | Mandatory | Description | Example |
|---|---|---|---|---|
| ```--env-id```/```-e``` | string | yes | Environment id in ```<cluster-name>/<environment-name>``` notation | `"cluster/platform-00"` |
| ```--envs-path```/```-ep``` | string | yes | Path to `/environments` folder | ```/environments``` |
| ```--sboms-path```/```-sp```| string | yes | Path to the folder with Application and Environment Template SBOMs. In Solution SBOM, the path to Application SBOM and Environment Template SBOM is specified relative to this folder. | ```/sboms``` |
| ```--solution-sbom-path```/```-ssp```| string | yes | Path to the Solution SBOM. | ```/environments/cluster/platform-00/Inventory/solution-descriptor/solution.sbom.json``` |
| ```--registries```/```-r```| string | yes | Path to the [registry configuration](#registry-configuration) | ```/configuration/registry.yml``` |
| ```--output```/```-o``` | string | yes | Folder where the result will be put by Calculator CLI | `"/environments/cluster/platform-00/effective-set"` |

### Registry Configuration

[Registry config JSON Schema](https://github.com/netcracker/qubership-envgene/blob/main/schemas/registry.schema.json)

[Registry config example](https://github.com/netcracker/qubership-envgene/blob/main/examples/registry.yml)

### Effective Set

#### Effective Set Structure

```text
...
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                ├── mapping.yml
                ├── <deployPostfix-01> # from Solution Descriptor
                |   ├── <application-name-01>
                |   |   ├── deployment-parameters.yaml
                |   |   ├── technical-configuration-parameters.yaml
                |   |   └── credentials.yaml
                |   └── <application-name-02>
                |       ├── deployment-parameters.yaml
                |       ├── technical-configuration-parameters.yaml
                |       └── credentials.yaml
                └── <deployPostfix-02> # from Solution Descriptor
                    ├── <application-name-01>
                    |   ├── deployment-parameters.yaml
                    |   ├── technical-configuration-parameters.yaml
                    |   └── credentials.yaml
                    └── <application-name-02>
                        ├── deployment-parameters.yaml
                        ├── technical-configuration-parameters.yaml
                        └── credentials.yaml
```

#### deployment-parameters.yaml

```yaml
<key-1>: <value-1>
<key-2>: <value-2>
global: &id001
  <key-1>: <value-1>
  <key-2>: <value-2>
<service-name-1>:
  <<: *id001
  <service-key-1>: <value-1>
  <service-key-2>: <value-2>
<service-name-2>:
  <<: *id001
  <service-key-1>: <value-1>
  <service-key-2>: <value-2>
```

Each application microservice has its own dedicated section. These sections contain the same set of parameters as defined at the root level.

To avoid repetition, YAML anchors (&) are used for reusability, while aliases (*) reference them.

The `<value>` can be complex, such as a map or a list, whose elements can also be complex.

#### credentials.yaml

```yaml
<key-1>: <value-1>
<key-2>: <value-2>
```

Each application microservice has its own dedicated section. These sections contain the same set of parameters as defined at the root level.

To avoid repetition, YAML anchors (&) are used for reusability, while aliases (*) reference them.

#### technical-configuration-parameters.yaml

```yaml
<key>: <value>
```

#### mapping.yml

This file defines a mapping between namespaces and the corresponding paths to their respective folders. The need for this mapping arises from the fact that the effective set consumer requires information about the specific names of namespaces. However, the effective set is stored in the repository in a structure that facilitates comparisons between effective sets for environments of the same type."

```yaml
---
<namespace-name-01>: <path-to-deployPostfix-folder-01> # <namespace-name> should be get from 'name' attribute of namespace object
<namespace-name-02>: <path-to-deployPostfix-folder-02>
```

### Macros

TBD

### Parameters in Effective Set don't Originate from Environment Instance

TBD

## Use Cases

### Effective Set Calculation

TBD

## Validation

TBD

## Tests

TBD

### Unit Tests

TBD

### e2e Tests

TBD
