
# Instance Pipeline Parameters

- [Instance Pipeline Parameters](#instance-pipeline-parameters)
  - [`ENV_NAMES`](#env_names)
  - [`ENV_BUILDER`](#env_builder)
  - [`GET_PASSPORT`](#get_passport)
  - [`CMDB_IMPORT`](#cmdb_import)
  - [`DEPLOYMENT_TICKET_ID`](#deployment_ticket_id)
  - [`ENV_TEMPLATE_VERSION`](#env_template_version)
  - [`SD_SOURCE_TYPE`](#sd_source_type)
  - [`SD_VERSION`](#sd_version)
  - [`SD_DATA`](#sd_data)
  - [`SD_DELTA`](#sd_delta)
  - [`ENV_INVENTORY_INIT`](#env_inventory_init)
  - [`ENV_TEMPLATE_NAME`](#env_template_name)
  - [`ENV_SPECIFIC_PARAMS`](#env_specific_params)
  - [`GENERATE_EFFECTIVE_SET`](#generate_effective_set)
  - [`EFFECTIVE_SET_CONFIG`](#effective_set_config)

The following are the launch parameters for the instance repository pipeline. These parameters influence, the execution of specific jobs within the pipeline.

All parameters are of the string data type

## `ENV_NAMES`

**Description**: Environment or Environments for for which processing will be launched. In `<cluster-name>/<env-name>` notation.

**Example**:  "ocp-01/platform"

## `ENV_BUILDER`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

If `true`:  
In the pipeline, Environment Instance generation job is executed. Environment Instance generation will be launched.

**Example**: `true`  

## `GET_PASSPORT`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

If `true`:  
  In the pipeline, Cloud Passport discovery job is executed. Cloud Passport discovery will be launched.

**Example**: `true`  

## `CMDB_IMPORT`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

If `true`:  
  In the pipeline, CMDB import job is executed. Environment Instance import into CMDB will be launched.

**Example**: `true`

## `DEPLOYMENT_TICKET_ID`

**Description**: Used as commit message prefix for commit into Instance repository.

**Example**: "TICKET-ID-12345"

## `ENV_TEMPLATE_VERSION`

**Description**: If provided system update Environment Template version in the Environment Inventory. System overrides `envTemplate.templateArtifact.artifact.version` OR `envTemplate.artifact` at `/environments/<ENV_NAME>/Inventory/env_definition.yml`

**Example**: "env-template:v1.2.3"

## `SD_SOURCE_TYPE`

**Description**: Defines the method by which SD is passed in the `SD_DATA` or `SD_VERSION` attributes. Valid values ​​are `artifact` OR `json`.

If `artifact`:  
  An SD artifact is expected in `SD_VERSION` in `application:version` notation. The system should download the artifact, transform it into YAML format, and save it to the repository.

If `json`:  
  SD content is expected in `SD_DATA`. The system should transform it into YAML format, and save it to the repository.

**Example**: `artifact`

## `SD_VERSION`

**Description**: Defines the SD artifact in `application:version` notation

System downloads the artifact and overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml` with the content provided in the artifact. If the file is absent, it will be generated.

**Example**: "dft:release-2024-1-2.02.002-RELEASE"

## `SD_DATA`

**Description**: Defines the content of SD. **JSON in string** format.

System overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml` with the content provided in `SD_DATA`. If the file is absent, it will be generated.

**Example**:

```yaml
version: 2.1
type: solutionDeploy
deployMode: composite
applications:
  - version: dpc:release-fortnight-2024.3-2.02.021-20240729.075218-RELEASE
    deployPostfix: data-management
  - version: dft:release-2024-1-2.02.002-RELEASE
    deployPostfix: data-management
  - version: data-slicing:release-fortnight-2024.3-3.01.023-20240729.121232-RELEASE
    deployPostfix: data-management
  - version: cloud-hds:release-2024-1-1.04.012-RELEASE
    deployPostfix: data-management
  - version: Data-Anonymization-Tool:release-2024.1-application-20240219.094437-3-RELEASE
    deployPostfix: data-management
  - version: dst-oob-bss-account-management:release-2023-1-2.01.003-RELEASE
    deployPostfix: data-management
userData:
  cci:
    systemConfiguration:
      id: 4175
      name: ETBSS 2024.2 Product Scope (24.2 Fix14)
      version: 79
    deploymentSchema:
      id: 56
      name: Etisalat BSS CSE MS Deployment Schema

```

## `SD_DELTA`

**Description**: Defines if SD provided in `SD_DATA` is Delta SD. Valid values ​​are `true` or `false`.

If `true`:  
  System overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/delta_sd.yml` with the content provided in `SD_DATA`. If the file is absent, it will be generated.
  System merges the content provided in `SD_DATA` into the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml`.

If `false` or not provided:  
  System overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml` with the content provided in `SD_DATA`. If the file is absent, it will be generated.

**Example**: `true`

## `ENV_INVENTORY_INIT`

**Description**:

If `true`:  
  In the pipeline, a job for generating the environment inventory is executed. The new Environment Inventory will be generated in the path `/environments/<ENV_NAME>/Inventory/env_definition.yml`

**Example**: `true`

## `ENV_TEMPLATE_NAME`

**Description**: Specifies the template artifact value within the generated Environment Inventory. This is used together with `ENV_INVENTORY_INIT`.

System overrides `envTemplate.name` at `/environments/<ENV_NAME>/Inventory/env_definition.yml`:

```yaml
envTemplate:
    name: <ENV_TEMPLATE_NAME>
    ...
...
```

**Example**: "env-template:v1.2.3"

## `ENV_SPECIFIC_PARAMS`

**Description**: Specifies Environment Inventory and env-specific parameters. This is used together with `ENV_INVENTORY_INIT`. **JSON in string** format.

**Example**:

```yaml
clusterParams:
  clusterEndpoint: <value>
  clusterToken: <value>
additionalTemplateVariables:
  <key>: <value>
cloudName: <value>
envSpecificParamsets:
  <ns-template-name>:
    - paramsetA
  cloud:
    - paramsetB
paramsets:
  paramsetA:
    version: <paramset-version>
    name: <paramset-name>
    parameters:
      <key>: <value>
    applications:
      - appName: <app-name>
        parameters:
          <key>: <value>
  paramsetB:
    version: <paramset-version>
    name: <paramset-name>
    parameters:
      <key>: <value>
    applications: []
credentials:
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

## `GENERATE_EFFECTIVE_SET`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

If `true`:  
  In the pipeline, Effective Set generation job is executed. Effective Parameter set generation will be launched

**Example**: `true`

## `EFFECTIVE_SET_CONFIG`

**Description**: Settings for effective set configuration. This is used together with `GENERATE_EFFECTIVE_SET`. **JSON in string** format.

```yaml
version: <v1.0|v2.0>
effective_set_expiry: <effective-set-expiry-time>
contexts:
  operational:
    consumers:
      - name: <consumer-component-name>
        version: <consumer-component-version>
        schema: <json-schema-in-string>
```

| Attribute | Mandatory | Description | Default | Example |
|---|---|---|---|---|
| **version** | Optional | The version of the effective set to be generated. Available options are `v1.0` and `v2.0`. EnvGene uses `--effective-set-version` to pass this attribute to the Calculator CLI. | `v1.0` | `v2.0` |
| **effective_set_expiry** | Optional | The duration for which the effective set (stored as a job artifact) will remain available for download. Envgene passes this value unchanged to: 1) The `retention-days` job attribute in case of GitHub pipeline. 2) The `expire_in` job attribute in case of GitLab pipeline. The exact syntax and constraints differ between platforms. Refer to the GitHub and GitLab documentation for details. | GitLab: `1 hours`, GitHub: `1` (day) | GitLab: `2 hours`, GitHub: `2` |
| **contexts.operational.consumers** | Optional | Each entry in this list adds a [consumer-specific operational context component](/docs/calculator-cli.md#version-20-operational-parameter-context) to the Effective Set. EnvGene passes the path to the corresponding JSON schema file to the Calculator CLI using the `--operational-consumer-specific-schema-path` argument. Each list element is passed as a separate argument. | None | None |
| **contexts.operational.consumers[].name** | Mandatory | The name of the [consumer-specific operational context component](/docs/calculator-cli.md#version-20-operational-parameter-context). If used without `contexts.operational.consumers[].schema`, the component must be pre-registered in EnvGene | None | `dcl` |
| **contexts.operational.consumers[].version** | Mandatory | The version of the [consumer-specific operational context component](/docs/calculator-cli.md#version-20-operational-parameter-context). If used without `contexts.operational.consumers[].schema`, the component must be pre-registered in EnvGene. | None | `v1.0`|
| **contexts.operational.consumers[].schema** | Optional | The content of the consumer-specific operational context component JSON schema transformed into a string. It is used to generate a consumer-specific operational context for a consumer not registered in EnvGene. EnvGene saves the value as a JSON file with the name `<contexts.operational[].name>-<contexts.operational[].version>.schema.json` and passes the path to it to the Calculator CLI via `--operational-consumer-specific-schema-path` attribute. The schema obtained in this way is not saved between pipeline runs and must be passed for each run. | None | [consumer-v1.0.json](/examples/consumer-v1.0.json) |

Registered component JSON schemas are stored in the EnvGene Docker image as JSON files named: `<consumers-name>-<consumer-version>.schema.json`

Consumer-specific operational context components registered in EnvGene:

1. None
