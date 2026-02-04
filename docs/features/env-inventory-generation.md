# Environment Inventory Generation

## Table of Contents

- [Environment Inventory Generation](#environment-inventory-generation)
  - [Table of Contents](#table-of-contents)
  - [Problem Statements](#problem-statements)
    - [Goals](#goals)
  - [Proposed Approach](#proposed-approach)
    - [Instance Repository Pipeline Parameters](#instance-repository-pipeline-parameters)
      - [`ENV_INVENTORY_CONTENT`](#env_inventory_content)
        - [Actions](#actions)
        - [Paths by place](#paths-by-place)
        - [Processing Model](#processing-model)
        - [Validations](#validations)
        - [Full `ENV_INVENTORY_CONTENT` Example](#full-env_inventory_content-example)
        - [ENV\_INVENTORY\_CONTENT in JSON-in-string format](#env_inventory_content-in-json-in-string-format)
      - [`ENV_SPECIFIC_PARAMS`](#env_specific_params)
        - [`ENV_SPECIFIC_PARAMS` Example](#env_specific_params-example)
    - [Example of Generated Result with `ENV_INVENTORY_CONTENT`](#example-of-generated-result-with-env_inventory_content)
      - [Generated Result with `ENV_INVENTORY_CONTENT` (new files)](#generated-result-with-env_inventory_content-new-files)
        - [Environment Inventory (`env_definition.yml`)](#environment-inventory-env_definitionyml)
        - [Parameter Sets](#parameter-sets)
        - [Credentials](#credentials)
        - [Resource Profile Overrides](#resource-profile-overrides)
        - [Shared Template Variable Files](#shared-template-variable-files)
      - [Generated Result when the target file already exists](#generated-result-when-the-target-file-already-exists)
        - [env\_definition file already exists](#env_definition-file-already-exists)
          - [Existing env\_definition file](#existing-env_definition-file)
          - [Input request (ENV\_INVENTORY\_CONTENT)](#input-request-env_inventory_content)
          - [Result `env_definition.yml`](#result-env_definitionyml)
        - [Parameter Sets file already exists](#parameter-sets-file-already-exists)
          - [Existing Parameter Set file](#existing-parameter-set-file)
          - [Input request (paramSets)](#input-request-paramsets)
          - [Result Parameter Sets](#result-parameter-sets)
    - [Example of Generated Result with `ENV_SPECIFIC_PARAMS`](#example-of-generated-result-with-env_specific_params)
      - [Minimal Environment Inventory](#minimal-environment-inventory)
      - [Environment Inventory with env-specific parameters](#environment-inventory-with-env-specific-parameters)

## Problem Statements

Current implementations of EnvGene require manual creation of Environment Inventories via working directly with repositories, and also related Inventory objects such as Parameter Sets, Credentials, Resource Profile Overrides and Shared Template Variable Files. While external systems can abstract this complexity for their users, EnvGene lacks an interface to support such automation for external systems.

### Goals

Develop an interface in EnvGene that enables external systems to create/replace and delete Environment Inventory and related objects without direct manual repository manipulation, including support for placing files on different levels (site/cluster/env).

## Proposed Approach

It is proposed to implement an EnvGene feature for Environment Inventory generation with a corresponding interface that will allow external systems to create Environment Inventories.

The external system will initiate Environment Inventory generation by triggering the Instance pipeline, passing required variables via the newly introduced [parameters](#instance-repository-pipeline-parameters). The target Environment for Inventory generation is determined by the `ENV_NAMES` attribute. Generating Inventories for multiple Environments in a single pipeline run **is not supported**.

The solution supports creation/replace and delete of:

- [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) (`env_definition.yml`)
- [Environment-specific Parameter Sets](/docs/envgene-objects.md#environment-specific-parameterset)
- [Shared Credentials](/docs/envgene-objects.md#shared-credentials-file)
- [Resource Profile Overrides](/docs/envgene-objects.md#resource-profile-override)
- [Shared Template Variable Files](/docs/envgene-objects.md#shared-template-variable-files)

Generation will occur in a dedicated job within the Instance repository pipeline.
The generated Environment Inventory must be reused by other jobs in the same pipeline. In order to be able to generate an Environment Inventory and get an Environment Instance or Effective Set in a single run of the pipeline. To make this possible, it must be executed before any jobs that consume the inventory.

`ENV_INVENTORY_CONTENT` is the primary way to manage Inventory via pipeline. It allows external systems to create, fully replace and delete `env_definition.yml` and related Inventory objects. The parameter also supports creating files on different levels (`site`, `cluster`, `env`) via the `place` field.

> **Note**
> If `ENV_TEMPLATE_VERSION` is provided in the instance pipeline, it has higher priority than the template version specified in `env_definition.yml`

`ENV_SPECIFIC_PARAMS` and `ENV_INVENTORY_INIT` are legacy parameters and are deprecated. They do not cover the full set of Inventory management scenarios, therefore new integrations should use `ENV_INVENTORY_CONTENT`.

### Instance Repository Pipeline Parameters

| Parameter | Type | Mandatory | Description | Example |
| ----------- | ------------- | ------ | --------- | ---------- |
| `ENV_INVENTORY_CONTENT` | JSON in string | no | Allows to create/ replace, delete `env_definition.yml` and related Inventory objects. Must be valid according to [JSON schema](/schemas/env-inventory-content.schema.json). See details in [ENV_INVENTORY_CONTENT](#env_inventory_content) | See [example below](#full-env_inventory_content-example) |
| `ENV_INVENTORY_INIT` | string | no | **Deprecated**. If `true`, the new Environment Inventory will be generated in the path `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`. If `false` can be updated only | `true` OR `false` |
| `ENV_SPECIFIC_PARAMS` | JSON in string | no | **Deprecated**. If specified, Environment Inventory is updated. See details in [ENV_SPECIFIC_PARAMS](#env_specific_params) | See [example below](#env_specific_params-example) |

#### `ENV_INVENTORY_CONTENT`

| Field | Type | Mandatory | Description | Example |
| --- | --- | --- | --- | --- |
| `envDefinition` | object | no | Block that controls `env_definition.yml` | |
| `envDefinition.action` | enum [`create_or_replace`, `delete`] | yes | Operation mode for `env_definition.yml`. See [Actions](#actions) | `create_or_replace` |
| `envDefinition.content` | object | no | Full content of `env_definition.yml`. Must be valid according [schema](/schemas/env-definition.schema.json). See details in [env_definition](/docs/envgene-configs.md#env_definitionyml) | See [example below](#full-env_inventory_content-example) |
| `paramSets` | array | no | Block that controls Parameter Set file operations. | See [example below](#full-env_inventory_content-example) |
| `paramSets[].action` | enum [`create_or_replace`, `delete`] | yes | Operation mode for the target Parameter Set file. See [Actions](#actions) | `create_or_replace` |
| `paramSets[].place` | enum[`site`,`cluster`,`env`] | yes | Defines where the Parameter Set file is stored. See [Paths by place](#paths-by-place) | `env` |
| `paramSets[].content` | hashmap | no | Parameter Set definition as file content. Must be valid according [schema](/schemas/paramset.schema.json) | See [example below](#full-env_inventory_content-example) |
| `credentials` | array | no | Block that controls Shared Credentials operations | See [example below](#full-env_inventory_content-example) |
| `credentials[].action` | enum [`create_or_replace`, `delete`] | yes | Operation mode for the Shared Credentials file. See [Actions](#actions) | `create_or_replace` |
| `credentials[].place` | enum[`site`,`cluster`,`env`] | yes | Defines where the Shared Credentials file is stored. See [Paths by place](#paths-by-place) | `site` |
| `credentials[].content` | hashmap | no | Shared Credential as file content. Must be valid according [schema](/schemas/credential.schema.json) | See [example below](#full-env_inventory_content-example) |
| `resourceProfiles` | array | no | List of Resource Profile Override operations | See [example below](#full-env_inventory_content-example) |
| `resourceProfiles[].action` | enum [`create_or_replace`, `delete`] | yes | Operation mode for the Resource Profile Override file. See [Actions](#actions) | `create_or_replace` |
| `resourceProfiles[].place` | enum[`site`,`cluster`,`env`] | yes | Defines where the Resource Profile Override file is stored. See [Paths by place](#paths-by-place) | `cluster` |
| `resourceProfiles[].content` | hashmap | no | Resource Profile Override as file content. Must be valid according [schema](/schemas/resource-profile.schema.json) | See [example below](#full-env_inventory_content-example) |
| `sharedTemplateVariables` | array | no | Block that controls Shared Template Variable File operations | See [example below](#full-env_inventory_content-example) |
| `sharedTemplateVariables[].action` | enum [`create_or_replace`, `delete`] | yes | Operation mode for the Shared Template Variable File. See [Actions](#actions) | `create_or_replace` |
| `sharedTemplateVariables[].place` | enum[`site`,`cluster`,`env`] | yes | Defines where the Shared Template Variable File is stored. See [Paths by place](#paths-by-place) | `site` |
| `sharedTemplateVariables[].name` | string | yes | Name of the Shared Template Variable File (without extension). The file will be saved as `<name>.yml` | `prod-template-variables` |
| `sharedTemplateVariables[].content` | hashmap | no | Shared Template Variable File content as key-value hashmap. Must NOT be located in a `parameters` directory | See [example below](#full-env_inventory_content-example) |

##### Actions

The `action` field defines the operation mode for Inventory objects.

| Action | Description |
| --- | --- |
| `create_or_replace` | Creates the file if not exist; if the file exists, fully replaces it. All required directories in the path are created automatically if they don't exist |
| `delete` | Deletes the target file if it exists. For `envDefinition`, the entire environment directory `/environments/<cluster-name>/<env-name>/` is removed. For other object types, only the file is deleted; directories are not removed |

##### Paths by place

The pipeline handles Inventory files in the **Instance repository**.  
The exact target folder depends on the object type and the `place` value.

| Object | place=env | place=cluster | place=site |
| --- | --- | --- | --- |
| `envDefinition` | `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` (fixed) | n/a | n/a |
| Parameter Set file | `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml` | `/environments/<cluster-name>/parameters/<paramset-name>.yml` | `/environments/parameters/<paramset-name>.yml` |
| Shared Credentials file | `/environments/<cluster-name>/<env-name>/Inventory/credentials/<credentials-file-name>.yml` | `/environments/<cluster-name>/credentials/<credentials-file-name>.yml` | `/environments/credentials/<credentials-file-name>.yml` |
| Resource Profile Override file | `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<override-name>.yml` | `/environments/<cluster-name>/resource_profiles/<override-name>.yml` | `/environments/resource_profiles/<override-name>.yml` |
| Shared Template Variable File | `/environments/<cluster-name>/<env-name>/shared-template-variables/<file-name>.yml` | `/environments/<cluster-name>/shared-template-variables/<file-name>.yml` | `/environments/shared-template-variables/<file-name>.yml` |

##### Processing Model

All operations specified in `ENV_INVENTORY_CONTENT` are processed atomically: either all requested changes are applied successfully, or none of them are applied. If any validation fails or any operation encounters an error, the entire transaction is rolled back and no files are modified.

The order in which different object types are processed is not guaranteed and may vary. Objects within the same type (e.g., multiple items in `paramSets` array) are also processed in an arbitrary order.

##### Validations

Before processing any files, the system performs the following validations:

**Parameter exclusivity validation:**

If both `ENV_INVENTORY_CONTENT` and any of `ENV_INVENTORY_INIT` or `ENV_SPECIFIC_PARAMS` are provided, validation fails

**JSON schema validation:**

`ENV_INVENTORY_CONTENT` is validated against the [JSON schema](/schemas/env-inventory-content.schema.json)

If any validation fails, the pipeline stops with a readable validation error in logs and no files are modified.

##### Full `ENV_INVENTORY_CONTENT` Example

This example shows how to generate a new Environment Inventory (`env_definition.yml`) and create related objects in the Instance repository: Parameter Sets, Credentials, Resource Profile Overrides, and Shared Template Variable Files.

```json
{
    "envDefinition": {
        "action": "create_or_replace",
        "content": {
            "inventory": {
                "environmentName": "env-1",
                "tenantName": "Applications",
                "cloudName": "cluster-1",
                "description": "Full sample",
                "owners": "Qubership team",
                "config": {
                    "updateRPOverrideNameWithEnvName": false,
                    "updateCredIdsWithEnvName": true
                }
            },
            "envTemplate": {
                "name": "composite-prod",
                "artifact": "project-env-template:master_20231024-080204",
                "additionalTemplateVariables": {
                    "ci": {
                        "CI_PARAM_1": "ci-param-val-1",
                        "CI_PARAM_2": "ci-param-val-2"
                    },
                    "e2eParameters": {
                        "E2E_PARAM_1": "e2e-param-val-1",
                        "E2E_PARAM_2": "e2e-param-val-2"
                    }
                },
                "sharedTemplateVariables": [
                    "prod-template-variables",
                    "sample-cloud-template-variables"
                ],
                "envSpecificParamsets": {
                    "bss": [
                        "env-specific-bss"
                    ]
                },
                "envSpecificTechnicalParamsets": {
                    "bss": [
                        "env-specific-tech"
                    ]
                },
                "envSpecificE2EParamsets": {
                    "cloud": [
                        "cloud-level-params"
                    ]
                },
                "sharedMasterCredentialFiles": [
                    "prod-integration-creds"
                ],
                "envSpecificResourceProfiles": {
                    "cloud": [
                        "cloud-specific-profile"
                    ]
                }
            }
        }
    },
    "paramSets": [
        {
            "action": "create_or_replace",
            "place": "env",
            "content": {
                "version": "<paramset-version>",
                "name": "env-specific-bss",
                "parameters": {
                    "key": "value"
                },
                "applications": []
            }
        }
    ],
    "credentials": [
        {
            "action": "create_or_replace",
            "place": "site",
            "content": {
                "prod-integration-creds": {
                    "type": "<credential-type>",
                    "data": {
                        "username": "<value>",
                        "password": "<value>"
                    }
                }
            }
        }
    ],
    "resourceProfiles": [
        {
            "action": "create_or_replace",
            "place": "cluster",
            "content": {
                "name": "cloud-specific-profile",
                "baseline": "dev",
                "description": "",
                "applications": [
                    {
                        "name": "core",
                        "version": "release-20241103.225817",
                        "sd": "",
                        "services": [
                            {
                                "name": "operator",
                                "parameters": [
                                    {
                                        "name": "GATEWAY_MEMORY_LIMIT",
                                        "value": "96Mi"
                                    },
                                    {
                                        "name": "GATEWAY_CPU_REQUEST",
                                        "value": "50m"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "version": 0
            }
        }
    ],
    "sharedTemplateVariables": [
        {
            "action": "create_or_replace",
            "place": "site",
            "name": "prod-template-variables",
            "content": {
                "TEMPLATE_VAR_1": "prod-value-1",
                "TEMPLATE_VAR_2": "prod-value-2",
                "nested": {
                    "key1": "nested-prod-value-1",
                    "key2": "nested-prod-value-2"
                }
            }
        },
        {
            "action": "create_or_replace",
            "place": "cluster",
            "name": "sample-cloud-template-variables",
            "content": {
                "CLOUD_VAR_1": "cloud-value-1",
                "CLOUD_VAR_2": "cloud-value-2"
            }
        }
    ]
}
```

##### ENV_INVENTORY_CONTENT in JSON-in-string format

```json
"{\"envDefinition\":{\"action\":\"create_or_replace\",\"content\":{\"inventory\":{\"environmentName\":\"env-1\",\"tenantName\":\"Applications\",\"cloudName\":\"cluster-1\",\"description\":\"Fullsample\",\"owners\":\"Qubershipteam\",\"config\":{\"updateRPOverrideNameWithEnvName\":false,\"updateCredIdsWithEnvName\":true}},\"envTemplate\":{\"name\":\"composite-prod\",\"artifact\":\"project-env-template:master_20231024-080204\",\"additionalTemplateVariables\":{\"ci\":{\"CI_PARAM_1\":\"ci-param-val-1\",\"CI_PARAM_2\":\"ci-param-val-2\"},\"e2eParameters\":{\"E2E_PARAM_1\":\"e2e-param-val-1\",\"E2E_PARAM_2\":\"e2e-param-val-2\"}},\"sharedTemplateVariables\":[\"prod-template-variables\",\"sample-cloud-template-variables\"],\"envSpecificParamsets\":{\"bss\":[\"env-specific-bss\"]},\"envSpecificTechnicalParamsets\":{\"bss\":[\"env-specific-tech\"]},\"envSpecificE2EParamsets\":{\"cloud\":[\"cloud-level-params\"]},\"sharedMasterCredentialFiles\":[\"prod-integration-creds\"],\"envSpecificResourceProfiles\":{\"cloud\":[\"cloud-specific-profile\"]}}}},\"paramSets\":[{\"action\":\"create_or_replace\",\"place\":\"env\",\"content\":{\"version\":\"<paramset-version>\",\"name\":\"env-specific-bss\",\"parameters\":{\"key\":\"value\"},\"applications\":[]}}],\"credentials\":[{\"action\":\"create_or_replace\",\"place\":\"site\",\"content\":{\"prod-integration-creds\":{\"type\":\"<credential-type>\",\"data\":{\"username\":\"<value>\",\"password\":\"<value>\"}}}}],\"resourceProfiles\":[{\"action\":\"create_or_replace\",\"place\":\"cluster\",\"content\":{\"name\":\"cloud-specific-profile\",\"baseline\":\"dev\",\"description\":\"\",\"applications\":[{\"name\":\"core\",\"version\":\"release-20241103.225817\",\"sd\":\"\",\"services\":[{\"name\":\"operator\",\"parameters\":[{\"name\":\"GATEWAY_MEMORY_LIMIT\",\"value\":\"96Mi\"},{\"name\":\"GATEWAY_CPU_REQUEST\",\"value\":\"50m\"}]}]}],\"version\":0}}],\"sharedTemplateVariables\":[{\"action\":\"create_or_replace\",\"place\":\"site\",\"name\":\"prod-template-variables\",\"content\":{\"TEMPLATE_VAR_1\":\"prod-value-1\",\"TEMPLATE_VAR_2\":\"prod-value-2\",\"nested\":{\"key1\":\"nested-prod-value-1\",\"key2\":\"nested-prod-value-2\"}}},{\"action\":\"create_or_replace\",\"place\":\"cluster\",\"name\":\"sample-cloud-template-variables\",\"content\":{\"CLOUD_VAR_1\":\"cloud-value-1\",\"CLOUD_VAR_2\":\"cloud-value-2\"}}]}"
```

#### `ENV_SPECIFIC_PARAMS`

| Field | Type | Mandatory | Description | Example |
| ------- | ------------- | ------ | --------- | ---------- |
| `clusterParams` | hashmap | no | Cluster connection parameters | None |
| `clusterParams.clusterEndpoint` | string | no | System **overrides** the value of `inventory.clusterUrl` in corresponding Environment Inventory | `https://api.cluster.example.com:6443` |
| `clusterParams.clusterToken` | string | no | System **adds** Credential in the `/environments/<cluster-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml`. If Credential already exists, the value will **not be overridden**. System also creates an association with the credential file in corresponding Environment Inventory via `envTemplate.sharedMasterCredentialFiles` | None |
| `additionalTemplateVariables` | hashmap | no | System **merges** the value into `envTemplate.additionalTemplateVariables` in corresponding Environment Inventory | `{"keyA": "valueA", "keyB": "valueB"}` |
| `cloudName` | string | no | System **overrides** the value of `inventory.cloudName` in corresponding Environment Inventory | `cloud01` |
| `tenantName` | string | no | System **overrides** the value of `inventory.tenantName` in corresponding Environment Inventory | `Application` |
| `deployer` | string | no | System **overrides** the value of `inventory.deployer` in corresponding Environment Inventory | `abstract-CMDB-1` |
| `envSpecificParamsets` | hashmap | no | System **merges** the value into `envTemplate.envSpecificParamsets` in corresponding Environment Inventory | See [example](#env_specific_params-example) |
| `paramsets` | hashmap | no | System creates Parameter Set file for each first level key in the path `/environments/<cluster-name>/<env-name>/Inventory/parameters/KEY-NAME.yml`. If Parameter Set already exists, the value will be **overridden** | See [example](#env_specific_params-example) |
| `credentials` | hashmap | no | System **adds** Credential object for each first level key in the `/environments/<cluster-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml`. If Credential already exists, the value will be **overridden**. System also creates an association with the credential file in corresponding Environment Inventory via `envTemplate.sharedMasterCredentialFiles` | See [example](#env_specific_params-example) |

##### `ENV_SPECIFIC_PARAMS` Example

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

### Example of Generated Result with `ENV_INVENTORY_CONTENT`

#### Generated Result with `ENV_INVENTORY_CONTENT` (new files)

##### Environment Inventory (`env_definition.yml`)

**Result:** `env_definition.yml` is generated from envDefinition.content.

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/env_definition.yml

inventory:
  environmentName: "env-1"
  tenantName: "Applications"
  cloudName: "cluster-1"
  description: "Full sample"
  owners: "Qubership team"
  config:
    updateRPOverrideNameWithEnvName: false
    updateCredIdsWithEnvName: true

envTemplate:
  name: "composite-prod"
  artifact: "project-env-template:master_20231024-080204"

  additionalTemplateVariables:
    ci:
      CI_PARAM_1: "ci-param-val-1"
      CI_PARAM_2: "ci-param-val-2"
    e2eParameters:
      E2E_PARAM_1: "e2e-param-val-1"
      E2E_PARAM_2: "e2e-param-val-2"

  sharedTemplateVariables:
    - "prod-template-variables"
    - "sample-cloud-template-variables"

  envSpecificParamsets:
    bss:
      - "env-specific-bss"

  envSpecificTechnicalParamsets:
    bss:
      - "env-specific-tech"

  envSpecificE2EParamsets:
    cloud:
      - "cloud-level-params"

  sharedMasterCredentialFiles:
    - "prod-integration-creds"

  envSpecificResourceProfiles:
    cloud:
      - "cloud-specific-profile"
```

##### Parameter Sets

**Result**: a Parameter Set file is generated from paramSets[].content and stored based on paramSets[].place.

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/parameters/env-specific-bss.yml

version: "<paramset-version>"
name: "env-specific-bss"
parameters:
  key: "value"
applications: []
```

##### Credentials

**Result**: a Credentials file is generated from credentials[].content and stored based on credentials[].place.

```yaml
# /environments/credentials/prod-integration-creds.yml

prod-integration-creds:
  type: <credential-type>
  data:
    username: "<value>"
    password: "<value>"

```

##### Resource Profile Overrides

**Result**: a Resource Profile Override file is generated from resourceProfiles[].content and stored based on resourceProfiles[].place.

```yaml
# /environments/<cluster-name>/Inventory/resource_profiles/cloud-specific-profile.yml

name: "cloud-specific-profile"
baseline: "dev"
description: ""
applications:
- name: "core"
  version: "release-20241103.225817"
  sd: ""
  services:
  - name: "operator"
    parameters:
    - name: "GATEWAY_MEMORY_LIMIT"
      value: "96Mi"
    - name: "GATEWAY_CPU_REQUEST"
      value: "50m"
```

##### Shared Template Variable Files

**Result**: a Shared Template Variable File is generated from sharedTemplateVariables[].content and stored based on sharedTemplateVariables[].place.

```yaml
# /environments/shared-template-variables/prod-template-variables.yml

TEMPLATE_VAR_1: "prod-value-1"
TEMPLATE_VAR_2: "prod-value-2"
nested:
  key1: "nested-prod-value-1"
  key2: "nested-prod-value-2"
```

```yaml
# /environments/<cluster-name>/shared-template-variables/sample-cloud-template-variables.yml

CLOUD_VAR_1: "cloud-value-1"
CLOUD_VAR_2: "cloud-value-2"
```

#### Generated Result when the target file already exists

##### env_definition file already exists

###### Existing env_definition file

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/env_definition.yml
inventory:
  environmentName: "env-1"
  tenantName: "Applications"
  cloudName: "cluster-1"

envTemplate:
  name: "composite-prod"
  artifact: "project-env-template:old"
  envSpecificParamsets:
    bss:
      - "env-specific-bss"
```

###### Input request (ENV_INVENTORY_CONTENT)

```json
{
  "envDefinition": {
    "action": "create_or_replace",
    "content": {
      "inventory": {
        "environmentName": "env-1",
        "tenantName": "Applications",
        "cloudName": "cluster-1",
        "description": "Updated description",
        "config": {
          "updateCredIdsWithEnvName": true
        }
      },
      "envTemplate": {
        "name": "composite-prod",
        "artifact": "project-env-template:new",
        "envSpecificE2EParamsets": {
          "cloud": [
            "cloud-level-params"
          ]
        },
        "sharedMasterCredentialFiles": [
          "prod-integration-creds"
        ]
      }
    }
  }
}
```

###### Result `env_definition.yml`

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/env_definition.yml
inventory:
  environmentName: "env-1"
  tenantName: "Applications"
  cloudName: "cluster-1"
  description: "Updated description"
  config:
    updateCredIdsWithEnvName: true

envTemplate:
  name: "composite-prod"
  artifact: "project-env-template:new"
  envSpecificE2EParamsets:
    cloud:
      - "cloud-level-params"
  sharedMasterCredentialFiles:
    - "prod-integration-creds"
```

##### Parameter Sets file already exists

###### Existing Parameter Set file

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/parameters/env-specific-bss.yml
name: "env-specific-bss"
parameters:
  featureFlag: "false"
applications: []
```

###### Input request (paramSets)

```json
{
  "paramSets": [
    {
      "action": "create_or_replace",
      "place": "env",
      "content": {
        "version": "1.1",
        "name": "env-specific-bss",
        "parameters": {
          "featureFlag": "true"
        },
        "applications": []
      }
    }
  ]
}
```

###### Result Parameter Sets

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/parameters/env-specific-bss.yml
name: "env-specific-bss"
parameters:
  featureFlag: "true"
applications: []
```

### Example of Generated Result with `ENV_SPECIFIC_PARAMS`

#### Minimal Environment Inventory

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/env_definition.yml
inventory:
  environmentName: <env-name>
  clusterUrl: <cloud>
envTemplate:
  name: <env-template-name>
  artifact: <app:ver>
```

#### Environment Inventory with env-specific parameters

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/env_definition.yml
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
# /environments/<cluster-name>/<env-name>/Credentials/credentials.yml
cloud-admin-token:
  type: "secret"
  data:
    secret: <cloud-token>
```

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/parameters/paramsetA.yml
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
# /environments/<cluster-name>/<env-name>/Inventory/parameters/paramsetB.yml
paramsetB:
  version: <paramset-ver>
  name: <paramset-name>
  parameters:
    <key>: <value>
  applications: []
```

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/credentials/inventory_generation_creds.yml
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
