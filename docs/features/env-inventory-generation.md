# Environment Inventory Generation

## Table of Contents

- [Environment Inventory Generation](#environment-inventory-generation)
  - [Table of Contents](#table-of-contents)
  - [Problem Statements](#problem-statements)
    - [Goals](#goals)
  - [Proposed Approach](#proposed-approach)
  - [Environment Inventory Generation with ENV_SPECIFIC_PARAMS](#environment-inventory-generation-with-env_specific_params)
    - [Instance Repository Pipeline Parameters](#instance-repository-pipeline-parameters)
      - [ENV\_SPECIFIC\_PARAMS](#env_specific_params)
        - [ENV\_SPECIFIC\_PARAMS Example](#env_specific_params-example)
    - [Generated Environment Inventory Examples](#generated-environment-inventory-examples)
      - [Minimal Environment Inventory](#minimal-environment-inventory)
      - [Environment Inventory with env-specific parameters](#environment-inventory-with-env-specific-parameters)
  - [Environment Inventory Generation with ENV_INVENTORY_CONTENT](#environment-inventory-generation-with-env_inventory_content)
    - [Instance Repository Pipeline Parameters](#instance-repository-pipeline-parameters-1)
      - [ENV_INVENTORY_CONTENT](#env_inventory_content)
        - [ENV_INVENTORY_CONTENT Structure](#env_inventory_content-structure)
        - [env_definition.$content Structure](#env_definitioncontent-structure)
    - [Input Request (ENV_INVENTORY_CONTENT)](#input-request-env_inventory_content)
    - [Generated Environment Inventory Examples](#generated-environment-inventory-examples-1)
      - [Environment Inventory (env_definition.yml)](#environment-inventory-env_definitionyml)
      - [Paramsets](#paramsets)
      - [Credentials](#credentials)
      - [Resource Profile Overrides](#resource-profile-overrides)
    - [OVERRIDE Examples](#override-examples)
      - [Paramsets — OVERRIDE](#paramsets--override)
      - [env_definition — OVERRIDE](#env_definition--override)
      - [Resource Profile Overrides — OVERRIDE](#resource-profile-overrides--override)
      - [Credentials — OVERRIDE](#credentials--override)
      

## Problem Statements

Current implementations of EnvGene require manual creation of Environment Inventories via working directly with repositories. While external systems can abstract this complexity for their users, EnvGene lacks interface to support such automation for external systems.

### Goals

Develop a interface in EnvGene that enables external systems to create Environment Inventories without direct repository manipulation

## Proposed Approach

It is proposed implementing an EnvGene feature for Environment Inventory generation with a corresponding interface that will allow external systems to create Environment Inventories.

The external system will initiate Environment Inventory generation by triggering the instance pipeline, passing required variables via the newly introduced [parameters](#instance-repository-pipeline-parameters). The target Environment for Inventory generation is determined by the `ENV_NAMES` attribute. Generating Inventories for multiple Environments in a single pipeline run is not supported.

The solution supports creation/update of:

- Environment Inventory
- Environment-specific Parameter Sets
- Credentials
- Resource Profile Overrides

Generation will occur in a dedicated job within the Instance repository pipeline.
The generated Environment Inventory must be reused by other jobs in the same pipeline. In order to be able to generate an Environment Inventory and get an Environment Instance or Effective Set in a single run of the pipeline. To make this possible, it must be executed before any jobs that consume the inventory.

When the inventory already exists, update rules vary depending on parameters. See details in:
- [ENV_SPECIFIC_PARAMS](#env_specific_params) -will be deprecated. Please use the [ENV_INVENTORY_CONTENT](#env_inventory_content)

[ENV_INVENTORY_CONTENT](#env_inventory_content) allows, within a single payload, to:
  - create/update env_definition.yml, paramsets, resource profile overrides
   - create/update files at different levels (site, cluster, env) depending on $place

## Environment Inventory Generation with [ENV_SPECIFIC_PARAMS](#env_specific_params)

### Instance Repository Pipeline Parameters

| Parameter | Type | Mandatory | Description | Example |
|-----------|-------------|------|---------|----------|
| `ENV_INVENTORY_INIT` | string | no | If `true`, the new Env Inventory will be generated in the path `/environments/<CLUSTER-NAME>/<ENV-NAME>/Inventory/env_definition.yml`. If `false` can be updated only | `true` OR `false` |
| `ENV_SPECIFIC_PARAMS` | JSON in string | no | If specified, Env Inventory is updated. See details in [ENV_SPECIFIC_PARAMS](#env_specific_params) | See [example below](#env_specific_params-example) |

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




## Environment Inventory Generation with [ENV_INVENTORY_CONTENT](#env_inventory_content)

### Instance Repository Pipeline Parameters

| Parameter | Type | Mandatory | Description | Example |
|---|---|---:|---|---|
| `ENV_NAMES` | string | yes | Target environment(s) to process. Defines the target path in Instance repository: `/environments/<cluster-name>/<env-name>/...`. Depending on pipeline implementation, it may support a single env (`<cluster>/<env>`) or a list (comma/space separated). | `dev-4` |
| `ENV_TEMPLATE_VERSION` | string | no | Template artifact version to be used by the pipeline when generating/updating inventory (if the pipeline supports template-based generation). Typically passed in `application:version` format. If not provided, pipeline may use the value already defined in `env_definition.yml` (e.g., `envTemplate.artifact`) or default behavior. | `project-env-template:master_20231024-080204` |
| `ENV_INVENTORY_CONTENT` | string (YAML payload) | yes | YAML payload that drives Environment Inventory generation/update. Contains actions and content for `env_definition`, plus optional blocks for generating/updating `paramsets`, `credentials`, `resource_profiles` | See example below |

#### ENV_INVENTORY_CONTENT

| Field | Type | Mandatory | Description | Allowed `$action` (with meaning) | Allowed `$place` | Example |
|---|---|---:|---|---|---|---|
| `env_definition` | object | no | Block that controls creation/update of `env_definition.yml`. | `create` (create new), `override` (replace existing), `upsert` (create if missing, or replace) | N/A | `env_definition: { $action: upsert, $content: {...} }` |
| `env_definition.$action` | enum | yes* | Operation mode for `env_definition.yml`. | `create` (create new), `override` (replace existing), `upsert` (create if missing, or replace) | N/A | `upsert` |
| `env_definition.$content` | object (`{env_definition}`) | yes* | Full content written into `env_definition.yml`. | N/A | N/A | `inventory: {...}` |
| `paramsets` | array | no | List of paramset file operations . | `create` (create new), `override` (replace existing), `upsert` (create if missing or replace) | `site`, `cluster`, `env` | `paramsets: [ { $action: upsert, $place: env, $content: {...} } ]` |
| `paramsets[].$action` | enum | yes** | Operation mode for the target paramset file. | `create` (create new), `override` (replace existing), `upsert` (create if missing or replace) | N/A | `override` |
| `paramsets[].$place` | enum | yes** | Defines where the paramset file is stored. | N/A | `site`, `cluster`, `env` | `env` |
| `paramsets[].$content` | object (`{paramset}`) | yes** | Paramset definition used as file content. | N/A | N/A | `name: "prod-shared"` |
| `credentials` | array | no | List of credentials operations  | `create` (create new), `override` (replace existing;), `upsert` (create if missing or  replace) | `site`, `cluster`, `env` | `credentials: [ { $action: upsert, $place: site, $content: {...} } ]` |
| `credentials[].$action` | enum | yes** | Operation mode for the credentials payload/file. | `create` (create new), `override` (replace existing), `upsert` (create if missing or  replace) | N/A | `create` |
| `credentials[].$place` | enum | yes** | Defines where the credentials file/payload is stored. | N/A | `site`, `cluster`, `env` | `site` |
| `credentials[].$content` | object (`{credential}`) | yes** | Credential objects map  | N/A | N/A | `prod-integration-creds: { type: "...", data: {...} }` |
| `resource_profiles` | array | no | List of resource profile override operations  | `create` (create new), `override` (replace existing), `upsert` (create if missing or replace) | `site`, `cluster`, `env` | `resource_profiles: [ { $action: upsert, $place: cluster, $content: {...} } ]` |
| `resource_profiles[].$action` | enum | yes** | Operation mode for the RP override file. | `create` (create new), `override` (replace existing), `upsert` (create if missing or replace) | N/A | `create` |
| `resource_profiles[].$place` | enum | yes** | Defines where the RP override file is stored. | N/A | `site`, `cluster`, `env` | `cluster` |
| `resource_profiles[].$content` | object (`{resource_profile}`) | yes** | Resource profile override content used as file content. | N/A | N/A | `name: "cloud-specific-profile"` |



##### env_definition.$content Structure

| Path | Type | Mandatory | Description | Example |
|---|---|---:|---|---|
| `inventory` | object | yes | Inventory metadata section. | `inventory: {...}` |
| `inventory.environmentName` | string | no | Name of the Environment, e.g. `dev01`. | `"env-1"` |
| `inventory.tenantName` | string | no | Name of the Tenant for the Environment. | `"Applications"` |
| `inventory.cloudName` | string | no | Name of the Cloud for the Environment. | `"cluster-1"` |
| `inventory.clusterUrl` | string | no | URL of the Cluster as specified in kubeconfig. | `"https://api.cluster.example.com:6443"` |
| `inventory.cloudPassport` | string | no | Reference to Cloud Passport. | `"cloud-passport-ref"` |
| `inventory.deployer` | string | no | Reference to external CMDB system where the Environment Instance can be imported. | `"abstract-CMDB-1"` |
| `inventory.description` | string | no | Environment description. | `"Full sample"` |
| `inventory.owners` | string | no | Environment owners. | `"Qubership team"` |
| `inventory.config` | object | no | Optional inventory config flags. | `config: {...}` |
| `inventory.config.updateRPOverrideNameWithEnvName` | boolean | no | If `true`, during CMDB import RP Override names are updated using pattern: `<tenant>-<cloud>-<env>-<RPO-name>`. | `false` |
| `inventory.config.updateCredIdsWithEnvName` | boolean | no | If `true`, during CMDB import credential IDs are updated using pattern: `<tenant>-<cloud>-<env>-<cred-id>`. | `true` |
| `inventory.config.mergeEnvSpecificResourceProfiles` | boolean | no | If `true`, env-specific Resource Profile Overrides are merged with template ones. If `false`, they полностью replace template RPOs. (Default: `true`) | `true` |
| `envTemplate` | object | yes | Template section that defines which template artifact to use and which env-specific inputs are attached. | `envTemplate: {...}` |
| `envTemplate.name` | string | yes | Name of the template (must match template name inside the Environment Template artifact). | `"composite-prod"` |
| `envTemplate.artifact` | string | yes | Template artifact in `application:version` notation. | `"project-env-template:master_20231024-080204"` |
| `envTemplate.additionalTemplateVariables` | hashmap | no | Additional variables available during template rendering. | `additionalTemplateVariables: {...}` |
| `envTemplate.sharedTemplateVariables` | array<string> | no | Array of filenames (key-value hashmap) that will be merged into `additionalTemplateVariables`. Files must NOT be located in `parameters/`. | `["prod-template-variables","sample-cloud-template-variables"]` |
| `envTemplate.envSpecificParamsets` | hashmap<string, array<string>> | no | Deployment paramsets mapping: key = `cloud` or namespace identifier; values = paramset file names (without extension) located in `parameters/`. | `bss: ["env-specific-bss","prod-shared"]` |
| `envTemplate.envSpecificTechnicalParamsets` | hashmap<string, array<string>> | no | Runtime/technical paramsets mapping (same rules as `envSpecificParamsets`). Files are in `parameters/`. | `bss: ["env-specific-tech"]` |
| `envTemplate.envSpecificE2EParamsets` | hashmap<string, array<string>> | no | Pipeline/e2e paramsets mapping (same rules as `envSpecificParamsets`). Files are in `parameters/`. | `cloud: ["cloud-level-params"]` |
| `envTemplate.sharedMasterCredentialFiles` | array<string> | no | Array of filenames in a `credentials` folder that override/extend instance credentials (file contains credential objects). | `["prod-integration-creds"]` |
| `envTemplate.envSpecificResourceProfiles` | hashmap<string, array<string>> | no | Environment-specific resource profile overrides mapping: key = `cloud` or namespace identifier; values = resource profile filenames (without extension) located in `resource_profiles/`. | `cloud: ["cloud-rp-override"]` |


### Input Request (ENV_INVENTORY_CONTENT)

```yaml
env_definition:
  $action: create
  $content:
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
          - "prod-shared"
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

paramsets:
  - $action: create
    $place: env
    $content:
      version: "<paramset-version>"
      name: "env-specific-bss"
      parameters:
        key: "value"
      applications: []

  - $action: create
    $place: site
    $content:
      version: "<paramset-version>"
      name: "prod-shared"
      parameters:
        key: "value"
      applications: []

  - $action: create
    $place: env
    $content:
      version: "<paramset-version>"
      name: "env-specific-tech"
      parameters:
        key: "value"
      applications: []

  - $action: create
    $place: cluster
    $content:
      version: "<paramset-version>"
      name: "cloud-level-params"
      parameters:
        key: "value"
      applications: []

credentials:
  - $action: create
    $place: site
    $content:
      prod-integration-creds:
        type: <credential-type>
        data:
          username: "<value>"
          password: "<value>"

resource_profiles:
  - $action: create
    $place: cluster
    $content:
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

### Generated Environment Inventory Examples
#### Environment Inventory (env_definition.yml)

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
      - "prod-shared"

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
      - "cloud-rp-override"
```

#### Paramsets
##### env-specific-bss, place = env

```yaml
#/environments/<cloud-name>/<env-name>/Inventory/parameters/env-specific-bss.yml

env-specific-bss:
  version: "<paramset-version>"
  name: "env-specific-bss"
  parameters:
    key: "value"
  applications: []
```

##### env-specific-tech, place = env

```yaml
#/environments/<cloud-name>/<env-name>/Inventory/parameters/env-specific-tech.yml

env-specific-tech:
  version: "<paramset-version>"
  name: "env-specific-tech"
  parameters:
    key: "value"
  applications: []
```

##### prod-shared, place = site

```yaml
#/environments/Inventory/parameters/prod-shared.yml

prod-shared:
  version: "<paramset-version>"
  name: "prod-shared"
  parameters:
    key: "value"
  applications: []
```
##### cloud-level-params, place = cluster

```yaml
#/environments/<cloud-name>/Inventory/parameters/cloud-level-params.yml

prod-shared:
  version: "<paramset-version>"
  name: "cloud-level-params"
  parameters:
    key: "value"
  applications: []
```

#### Credentials
##### prod-integration-creds, place = site

```yaml
# /environments/credentials/prod-integration-creds.yml

prod-integration-creds:
  type: <credential-type>
  data:
    username: "<value>"
    password: "<value>"

```
#### Resource Profile Overrides
##### cloud-rp-override, place = cluster
```yaml
# /environments/<cloud-name>/Inventory/resource_profiles/cloud-rp-override.yml

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

#### Paramsets — OVERRIDE

##### Existing file
```yaml
# /environments/<cluster-name>/<env-name>/Inventory/parameters/env-specific-bss.yml
env-specific-bss:
  version: "1.0"
  name: "env-specific-bss"
  parameters:
    featureFlag: "false"
  applications: []
```

### Input request ENV_INVENTORY_CONTENT
```yaml
paramsets:
  - $action: override
    $place: env
    $content:
      version: "1.1"
      name: "env-specific-bss"
      parameters:
        featureFlag: "true"
      applications: []
```
### Result
```yaml
# /environments/<cluster-name>/<env-name>/Inventory/parameters/env-specific-bss.yml
env-specific-bss:
  version: "1.1"
  name: "env-specific-bss"
  parameters:
    featureFlag: "true"
  applications: []
  ```


## env_definition — OVERRIDE


### Existing file
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

### Input request (ENV_INVENTORY_CONTENT)
```yaml
env_definition:
  $action: override
  $content:
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

## Result
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


### Resource Profile Overrides — OVERRIDE

#### Existing file
```yaml
# /environments/<cluster-name>/Inventory/resource_profiles/cloud-specific-profile.yml
name: "cloud-specific-profile"
baseline: "dev"
applications:
  - name: "core"
    services:
      - name: "operator"
        parameters:
          - name: "GATEWAY_MEMORY_LIMIT"
            value: "96Mi"
version: 0
```

#### Input request (ENV_INVENTORY_CONTENT)

```yaml
resource_profiles:
  - $action: override
    $place: cluster
    $content:
      name: "cloud-specific-profile"
      baseline: "dev"
      applications:
        - name: "core"
          services:
            - name: "operator"
              parameters:
                - name: "GATEWAY_MEMORY_LIMIT"
                  value: "128Mi"
      version: 1
```
#### Result 

```yaml
# /environments/<cluster-name>/Inventory/resource_profiles/cloud-specific-profile.yml
name: "cloud-specific-profile"
baseline: "dev"
applications:
  - name: "core"
    services:
      - name: "operator"
        parameters:
          - name: "GATEWAY_MEMORY_LIMIT"
            value: "128Mi"
version: 1
```

### Credentials — OVERRIDE 
#### Existing file
```yaml
# /environments/credentials/prod-integration-creds.yml
prod-integration-creds:
  type: "basic"
  data:
    username: "old-user"
    password: "old-pass"
```

#### Input request (ENV_INVENTORY_CONTENT)
```yaml
credentials:
  - $action: override
    $place: site
    $content:
      prod-integration-creds:
        type: "basic"
        data:
          username: "new-user"
          password: "new-pass"
```

#### Result
```yaml
### /environments/credentials/prod-integration-creds.yml
prod-integration-creds:
  type: "basic"
  data:
    username: "new-user"
    password: "new-pass"
```
