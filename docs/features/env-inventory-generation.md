# Environment Inventory Generation

## Table of Contents

- [Problem Statements](#problem-statements)
  - [Goals](#goals)
- [Proposed Approach](#proposed-approach)
- [Instance Repository Pipeline Parameters](#instance-repository-pipeline-parameters)
  - [ENV_INVENTORY_CONTENT](#env_inventory_content)
    - [Paths by place](#paths-by-place)
    - [Full ENV_INVENTORY_CONTENT Example](#full-env_inventory_content-example)
    - [ENV_INVENTORY_CONTENT in string format](#env_inventory_content-in-string-format)
  - [ENV_SPECIFIC_PARAMS](#env_specific_params)
    - [ENV_SPECIFIC_PARAMS Example](#env_specific_params-example)
- [Generated Environment Inventory Examples](#generated-environment-inventory-examples)
  - [Generated Result with ENV_INVENTORY_CONTENT (new files)](#generated-result-with-env_inventory_content-new-files)
    - [Environment Inventory (env_definition.yml)](#environment-inventory-env_definitionyml)
    - [Paramsets](#paramsets)
    - [Credentials](#credentials)
    - [Resource Profiles](#resource-profiles)
    - [Generated Result when the target file already exists](#generated-result-when-the-target-file-already-exists)
    - [env_definition file already exists](#env_definition-file-already-exists)
      - [Existing env_definition file](#existing-env_definition-file)
      - [Input request (ENV_INVENTORY_CONTENT)](#input-request-env_inventory_content)
      - [Result env_definition.yml](#result-env_definitionyml)
    - [Paramsets file already exists](#paramsets-file-already-exists)
      - [Existing paramset file](#existing-paramset-file)
      - [Input request (paramsets)](#input-request-paramsets)
      - [Result paramsets](#result-paramsets)
  - [Generated Result with ENV_SPECIFIC_PARAMS](#generated-result-with-env_specific_params)
    - [Minimal Environment Inventory](#minimal-environment-inventory)
    - [Environment Inventory with env-specific parameters](#environment-inventory-with-env-specific-parameters)

## Problem Statements

Current implementations of EnvGene require manual creation of Environment Inventories via working directly with repositories, and also related Inventory artifacts such as paramsets, credentials, resource profile overrides. While external systems can abstract this complexity for their users, EnvGene lacks an interface to support such automation for external systems.

### Goals

Develop an interface in EnvGene that enables external systems to create and replace Environment Inventory and related artifacts (paramsets, credentials, resource profiles) without direct manual repository manipulation, including support for placing files on different levels (site / cluster / env).

## Proposed Approach

It is proposed to implement an EnvGene feature for Environment Inventory generation with a corresponding interface that will allow external systems to create Environment Inventories.

The external system will initiate Environment Inventory generation by triggering the instance pipeline, passing required variables via the newly introduced [parameters](#instance-repository-pipeline-parameters). The target Environment for Inventory generation is determined by the `ENV_NAMES` attribute. Generating Inventories for multiple Environments in a single pipeline run is not supported.

The solution supports creation/replace of:

- Environment Inventory (`env_definition.yml`)
- Environment-specific Parameter Sets (paramset files)
- Credentials (credentials files)
- Resource Profile Overrides (resource profile override files)

Generation will occur in a dedicated job within the Instance repository pipeline.
The generated Environment Inventory must be reused by other jobs in the same pipeline. In order to be able to generate an Environment Inventory and get an Environment Instance or Effective Set in a single run of the pipeline. To make this possible, it must be executed before any jobs that consume the inventory.

`ENV_INVENTORY_CONTENT` is the primary way to manage Inventory via pipeline. It allows external systems to create or fully replace `env_definition.yml` and related Inventory files (paramsets, credentials, resource profile overrides). The parameter also supports creating files on different levels (`site`, `cluster`, `env`) via the `place` field.

> **Note**
> If `ENV_TEMPLATE_VERSION` is provided in the instance pipeline, it has higher priority than the template version specified in `env_definition.yml`

`ENV_SPECIFIC_PARAMS` and `ENV_INVENTORY_INIT` are legacy parameters and will be deprecated. They do not cover the full set of Inventory management scenarios, therefore new integrations should use `ENV_INVENTORY_CONTENT`.

### Instance Repository Pipeline Parameters

| Parameter | Type | Mandatory | Description | Example |
| ----------- | ------------- | ------ | --------- | ---------- |
| `ENV_INVENTORY_CONTENT` | JSON in string | no | Allows to create or replace env_definition.yml and generate related Inventory files (paramsets, credentials, resource profiles, template variables) on site/cluster/env levels via `place`. | See [example below](#full-env_inventory_content-example) |
| `ENV_INVENTORY_INIT` | string | no | ***Legacy parameter***. If `true`, the new Env Inventory will be generated in the path `/environments/<CLUSTER-NAME>/<ENV-NAME>/Inventory/env_definition.yml`. If `false` can be updated only | `true` OR `false` |
| `ENV_SPECIFIC_PARAMS` | JSON in string | no | ***Legacy parameter***. If specified, Env Inventory is updated. See details in [ENV_SPECIFIC_PARAMS](#env_specific_params) | See [example below](#env_specific_params-example) |

#### ENV_INVENTORY_CONTENT

| Field | Type | Mandatory | Description | Example |
| --- | --- | --- | --- | --- |
| `envDefinition` | object | no | Block that controls creation/replace of `env_definition.yml`. | |
| `envDefinition.action` | string enum | yes (if envDefinition is provided) | Operation mode for `env_definition.yml`. **Enum:** `create_or_replace` (creates the file if missing; if the file exists, fully replaces it). | `create_or_replace` |
| `envDefinition.content` | object | yes (if envDefinition is provided) | Full content written into `env_definition.yml`. See details in [env_definition](/docs/envgene-configs.md#env_definitionyml) | See [example below](#full-env_inventory_content-example) |
| `paramsets` | array | no | List of paramset file operations. | See [example below](#full-env_inventory_content-example) |
| `paramsets[].action` | string enum | yes (if paramset is provided) | Operation mode for the target paramset file. **Enum:** `create_or_replace` (creates the file if missing; if the file exists, fully replaces it). | `create_or_replace` |
| `paramsets[].place` | string enum | yes (if paramset is provided) | Defines where the paramset file is stored. **Enum:** `site`, `cluster`, `env`. See [Paths by place](#paths-by-place) | `"env"` |
| `paramsets[].content` | hashmap | yes (if paramset is provided) | Paramset definition used as file content. | See [example below](#full-env_inventory_content-example) |
| `credentials` | array | no | List of credentials operations. | See [example below](#full-env_inventory_content-example) |
| `credentials[].action` | string enum | yes (if credentials is provided) | Operation mode for the credentials file. **Enum:** `create_or_replace` (creates the credentials file if missing; if the file exists, fully replaces it). | `"create_or_replace"` |
| `credentials[].place` | string enum | yes (if credentials is provided) | Defines where the credentials file is stored. **Enum:** `site`, `cluster`, `env`. See [Paths by place](#paths-by-place) | `"site"` |
| `credentials[].content` | hashmap | yes (if credentials is provided) | Credential objects map | See [example below](#full-env_inventory_content-example) |
| `resourceProfiles` | array | no | List of resource profile override operations. | See [example below](#full-env_inventory_content-example) |
| `resourceProfiles[].action` | string enum | yes (if resourceProfiles is provided) | Operation mode for the resource profiles override file. **Enum:** `create_or_replace` (creates the resource profiles file if missing; if the file exists, fully replaces it). | `"create_or_replace"` |
| `resourceProfiles[].place` | string enum | yes (if resourceProfiles is provided) | Defines where the resource profiles  override file is stored. **Enum:** `site`, `cluster`, `env` | `"cluster"`. See [Paths by place](#paths-by-place) |
| `resourceProfiles[].content` | hashmap | yes (if resourceProfiles is provided) | Resource profile override content used as file content. | See [example below](#full-env_inventory_content-example) |

##### Paths by place

The pipeline generates (or fully replaces) Inventory files in the **Instance repository**.  
The exact target folder depends on the object type and the `place` value.

| Object | place=env | place=cluster | place=site |
| --- | --- | --- | --- |
| `envDefinition` | `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml` (fixed) | n/a | n/a |
| Paramset file | `/environments/<cluster-name>/<env-name>/Inventory/parameters/<paramset-name>.yml` | `/environments/<cluster-name>/Inventory/parameters/<paramset-name>.yml` | `/environments/Inventory/parameters/<paramset-name>.yml` |
| Credentials file | `/environments/<cluster-name>/<env-name>/Inventory/credentials/<credentials-file-name>.yml` | `/environments/<cluster-name>/Inventory/credentials/<credentials-file-name>.yml` | `/environments/credentials/<credentials-file-name>.yml` |
| Resource profile override file | `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/<override-name>.yml` | `/environments/<cluster-name>/Inventory/resource_profiles/<override-name>.yml` | `/environments/Inventory/resource_profiles/<override-name>.yml` |

##### Full ENV_INVENTORY_CONTENT Example

This example shows how to generate a new Environment Inventory (`env_definition.yml`) and create related artifacts in the Instance repository: paramsets, credentials, and a resource profile override.

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
    "paramsets": [
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
    ]
}
```

##### ENV_INVENTORY_CONTENT in string format

```json
"{\"envDefinition\":{\"action\":\"create_or_replace\",\"content\":{\"inventory\":{\"environmentName\":\"env-1\",\"tenantName\":\"Applications\",\"cloudName\":\"cluster-1\",\"description\":\"Fullsample\",\"owners\":\"Qubershipteam\",\"config\":{\"updateRPOverrideNameWithEnvName\":false,\"updateCredIdsWithEnvName\":true}},\"envTemplate\":{\"name\":\"composite-prod\",\"artifact\":\"project-env-template:master_20231024-080204\",\"additionalTemplateVariables\":{\"ci\":{\"CI_PARAM_1\":\"ci-param-val-1\",\"CI_PARAM_2\":\"ci-param-val-2\"},\"e2eParameters\":{\"E2E_PARAM_1\":\"e2e-param-val-1\",\"E2E_PARAM_2\":\"e2e-param-val-2\"}},\"sharedTemplateVariables\":[\"prod-template-variables\",\"sample-cloud-template-variables\"],\"envSpecificParamsets\":{\"bss\":[\"env-specific-bss\"]},\"envSpecificTechnicalParamsets\":{\"bss\":[\"env-specific-tech\"]},\"envSpecificE2EParamsets\":{\"cloud\":[\"cloud-level-params\"]},\"sharedMasterCredentialFiles\":[\"prod-integration-creds\"],\"envSpecificResourceProfiles\":{\"cloud\":[\"cloud-specific-profile\"]}}}},\"paramsets\":[{\"action\":\"create_or_replace\",\"place\":\"env\",\"content\":{\"version\":\"<paramset-version>\",\"name\":\"env-specific-bss\",\"parameters\":{\"key\":\"value\"},\"applications\":[]}}],\"credentials\":[{\"action\":\"create_or_replace\",\"place\":\"site\",\"content\":{\"prod-integration-creds\":{\"type\":\"<credential-type>\",\"data\":{\"username\":\"<value>\",\"password\":\"<value>\"}}}}],\"resourceProfiles\":[{\"action\":\"create_or_replace\",\"place\":\"cluster\",\"content\":{\"name\":\"cloud-specific-profile\",\"baseline\":\"dev\",\"description\":\"\",\"applications\":[{\"name\":\"core\",\"version\":\"release-20241103.225817\",\"sd\":\"\",\"services\":[{\"name\":\"operator\",\"parameters\":[{\"name\":\"GATEWAY_MEMORY_LIMIT\",\"value\":\"96Mi\"},{\"name\":\"GATEWAY_CPU_REQUEST\",\"value\":\"50m\"}]}]}],\"version\":0}}]}"
```

#### ENV_SPECIFIC_PARAMS

| Field | Type | Mandatory | Description | Example |
| ------- | ------------- | ------ | --------- | ---------- |
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

#### Generated Result with ENV_INVENTORY_CONTENT (new files)

##### Environment Inventory (env_definition.yml)

**Result:** `env_definition.yml` is generated from envDefinition.content.

```yaml
# /environments/<cloud-name>/<env-name>/Inventory/env_definition.yml

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

##### Paramsets

**Result**: a Paramset file is generated from paramsets[].content and stored based on paramsets[].place.

```yaml
#/environments/<cloud-name>/<env-name>/Inventory/parameters/env-specific-bss.yml

env-specific-bss:
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

##### Resource Profiles

**Result**: a Resource Profiles is generated from resourceProfiles[].content and stored based on resourceProfiles[].place.

```yaml
# /environments/<cloud-name>/Inventory/resource_profiles/cloud-specific-profile.yml

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
version: 0
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

##### Paramsets file already exists

###### Existing paramset file

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/parameters/env-specific-bss.yml
env-specific-bss:
  version: "1.0"
  name: "env-specific-bss"
  parameters:
    featureFlag: "false"
  applications: []
```

###### Input request (paramsets)

```json
{
  "paramsets": [
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

###### Result paramsets

```yaml
# /environments/<cluster-name>/<env-name>/Inventory/parameters/env-specific-bss.yml
env-specific-bss:
  version: "1.1"
  name: "env-specific-bss"
  parameters:
    featureFlag: "true"
  applications: []
  ```

#### Generated Result with ENV_SPECIFIC_PARAMS

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
