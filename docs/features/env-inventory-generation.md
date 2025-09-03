# Environment Inventory Generation

## Table of Contents

- [Environment Inventory Generation](#environment-inventory-generation)
  - [Table of Contents](#table-of-contents)
  - [Problem Statements](#problem-statements)
    - [Goals](#goals)
  - [Proposed Approach](#proposed-approach)
    - [Instance Repository Pipeline Parameters](#instance-repository-pipeline-parameters)
      - [ENV\_SPECIFIC\_PARAMS](#env_specific_params)
        - [ENV\_SPECIFIC\_PARAMS Example](#env_specific_params-example)
    - [Generated Environment Inventory Examples](#generated-environment-inventory-examples)
      - [Minimal Environment Inventory](#minimal-environment-inventory)
      - [Environment Inventory with env-specific parameters](#environment-inventory-with-env-specific-parameters)

## Problem Statements

Current implementations of EnvGene require manual creation of Environment Inventories via working directly with repositories. While external systems can abstract this complexity for their users, EnvGene lacks interface to support such automation for external systems.

### Goals

Develop a interface in EnvGene that enables external systems to create Environment Inventories without direct repository manipulation

## Proposed Approach

It is proposed implementing an EnvGene feature for Environment Inventory generation with a corresponding interface that will allow external systems to create Environment Inventories.

The external system will initiate Environment Inventory generation by triggering the instance pipeline, passing required variables via the newly introduced [parameters](#instance-repository-pipeline-parameters). The target Environment for Inventory generation is determined by the `ENV_NAMES` attribute. Generating Inventories for multiple Environments in a single pipeline run is not supported.

The solution supports creation of:

- Environment Inventory
- Environment-specific Parameter Sets
- Credentials

The created objects are validated according to the corresponding schemes.

Generation will occur in a dedicated job within the Instance repository pipeline.
The generated Environment Inventory must be reused by other jobs in the same pipeline. In order to be able to generate an Environment Inventory and get an Environment Instance or Effective Set in a single run of the pipeline. To make this possible, it must be executed before any jobs that consume the inventory.

When the inventory already exists, update rules vary depending on parameters. See details in [ENV_SPECIFIC_PARAMS](#env_specific_params)

### Instance Repository Pipeline Parameters

| Parameter | Type | Mandatory | Description | Example |
|-----------|-------------|------|---------|----------|
| `ENV_INVENTORY_INIT` | string | no | If `true`, the new Env Inventory will be generated in the path `/environments/<CLUSTER-NAME>/<ENV-NAME>/Inventory/env_definition.yml`. If `false` can be updated only | `true` OR `false` |
| `ENV_SPECIFIC_PARAMS` | json in string | no | If specified, Env Inventory is updated. See details in [ENV_SPECIFIC_PARAMS](#env_specific_params) | See [example below](#env_specific_params-example) |

#### ENV_SPECIFIC_PARAMS

| Field | Type | Mandatory | Description | Example |
|-------|-------------|------|---------|----------|
| `clusterParams` | hashmap | no | Cluster connection parameters | None |
| `clusterParams.clusterEndpoint` | string | no | System **overrides** the value of `inventory.clusterUrl` in corresponding Env Inventory | `https://api.cluster.example.com:6443` |
| `clusterParams.clusterToken` | string | no | System **adds** Credential in the `/environments/<cluster-name>/<env-name>/Credentials/inventory_generation_creds.yml`. If Credential already exists, the value will **not be overridden**. System also creates an association with the credential file in corresponding Env Inventory via `envTemplate.sharedMasterCredentialFiles` | None |
| `additionalTemplateVariables` | hashmap | no | System **merges** the value into `envTemplate.additionalTemplateVariables` in corresponding Env Inventory | `{"keyA": "valueA", "keyB": "valueB"}` |
| `cloudName` | string | no | System **overrides** the value of `inventory.cloudName` in corresponding Env Inventory | `cloud01` |
| `tenantName` | string | no | System **overrides** the value of `inventory.tenantName` in corresponding Env Inventory | `Application` |
| `deployer` | string | no | System **overrides** the value of `inventory.deployer` in corresponding Env Inventory | `abstract-CMDB-1` |
| `envSpecificParamsets` | hashmap | no | System **merges** the value into envTemplate.envSpecificParamsets in corresponding Env Inventory | See [example](#env_specific_params-example) |
| `paramsets` | hashmap | no | System creates Parameter Set file for each first level key in the path `environments/<cluster-name>/<env-name>/Inventory/parameters/KEY-NAME.yml`. If Parameter Set already exists, the value will be **overridden** | See [example](#env_specific_params-example) |
| `credentials` | hashmap | no | System **adds** Credential object for each first level key in the `/environments/<cluster-name>/<env-name>/credentials/inventory_generation_creds.yml`. If Credential already exists, the value will be **overridden**. System also creates an association with the credential file in corresponding Env Inventory via `envTemplate.sharedMasterCredentialFiles` | See [example](#env_specific_params-example) |

##### ENV_SPECIFIC_PARAMS Example

```json
  {
    "clusterParams": {
      "clusterEndpoint": "<value>",
      "clusterToken": "<value>"
    },
    "additionalTemplateVariables": {
      "<key>": "<value>"
    },
    "cloudName": "<value>",
    "tenantName": "<value>",
    "deployer": "<value>",
    "envSpecificParamsets": {
      "<ns-template-name>": [
        "paramsetA"
      ],
      "cloud": [
        "paramsetB"
      ]
    },
    "paramsets": {
      "paramsetA": {
        "version": "<paramset-version>",
        "name": "<paramset-name>",
        "parameters": {
          "<key>": "<value>"
        },
        "applications": [
          {
            "appName": "<app-name>",
            "parameters": {
              "<key>": "<value>"
            }
          }
        ]
      },
      "paramsetB": {
        "version": "<paramset-version>",
        "name": "<paramset-name>",
        "parameters": {
          "<key>": "<value>"
        },
        "applications": []
      }
    },
    "credentials": {
      "credX": {
        "type": "<credential-type>",
        "data": {
          "username": "<value>",
          "password": "<value>"
        }
      },
      "credY": {
        "type": "<credential-type>",
        "data": {
          "secret": "<value>"
        }
      }
    }
  }
```

### Generated Environment Inventory Examples

#### Minimal Environment Inventory

```yaml
# /environments/<cloud-name>/<env-name>/Inventory/env_definition.yml
inventory:
  environmentName: <env-name>
  clusterUrl: <cloud>
envTemplate:
  name: <env-template-name>
  artifact: <app:ver>
```

#### Environment Inventory with env-specific parameters

```yaml
# /environments/<cloud-name>/<env-name>/Inventory/env_definition.yml
inventory:
  environmentName: <env-name>
  clusterUrl: <cloud>
envTemplate:
  additionalTemplateVariables:
    <key>: <value>
  envSpecificParamsets:
    cloud: [ "paramsetA" ]
    <ns-template-name>: [ "paramsetB" ]
  sharedMasterCredentialFiles: [ "inventory_generation_creds" ]
  name: <env-template-name>
  artifact: <app:ver>
```

```yaml
# /environments/<cloud-name>/<env-name>/Credentials/credentials.yml
cloud-admin-token:
  type: "secret"
  data:
    secret: <cloud-token>
```

```yaml
# environments/<cloud-name>/<env-name>/Inventory/parameters/paramsetA.yml
paramsetA:
  version: <paramset-ver>
  name: <paramset-name>
  parameters:
    <key>: <value>
  applications:
    - appName: <app-name>
      parameters:
        <key>: <value>
```

```yaml
# environments/<cloud-name>/<env-name>/Inventory/parameters/paramsetB.yml
paramsetB:
  version: <paramset-ver>
  name: <paramset-name>
  parameters:
    <key>: <value>
  applications: []
```

```yaml
# environments/<cloud-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml
credX:
  type: <credential-type>
  data:
    username: <value>
    password: <value>
credY:
  type: <credential-type>
  data:
    secret: <value>
```
