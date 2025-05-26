
# Instance Pipeline Parameters

- [Instance Pipeline Parameters](#instance-pipeline-parameters)
  - [`ENV_NAMES`](#env_names)
  - [`ENV_BUILDER`](#env_builder)
  - [`GET_PASSPORT`](#get_passport)
  - [`DEPLOYMENT_TICKET_ID`](#deployment_ticket_id)
  - [`ENV_TEMPLATE_VERSION`](#env_template_version)
  - [`ENV_INVENTORY_INIT`](#env_inventory_init)
  - [`ENV_TEMPLATE_NAME`](#env_template_name)
  - [`ENV_SPECIFIC_PARAMS`](#env_specific_params)
  - [`GENERATE_EFFECTIVE_SET`](#generate_effective_set)
  - [`SD_SOURCE_TYPE`](#sd_source_type)
  - [`SD_VERSION`](#sd_version)
  - [`SD_VERSION_MULTIPLE`](#sd_version_multiple)
  - [`SD_DATA`](#sd_data)
  - [`SD_DATA_MULTIPLE`](#sd_data_multiple)
  - [`SD_DELTA`](#sd_delta)
  - [`SD_MERGE_MODE`](#sd_merge_mode)

The following are the launch parameters for the instance repository pipeline. These parameters influence, the execution of specific jobs within the pipeline.

All parameters are of the string data type

## `ENV_NAMES`

**Description**: Specifies the environment(s) for which processing will be triggered. Uses the `<cluster-name>/<env-name>` notation. If multiple environments are provided, they must be separated by a `\n` (newline) delimiter. In multi-environment case, each environment will trigger its own independent pipeline flow. All environments will use the same set of pipeline parameters (as documented in this spec)

**Default Value**: None

**Mandatory**: Yes

**Example**:
  
- Single environment: `ocp-01/platform`
- Multiple environments (separated by \n) `k8s-01/env-1\nk8s-01/env2`

## `ENV_BUILDER`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

If `true`:  
In the pipeline, Environment Instance generation job is executed. Environment Instance generation will be launched.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`  

## `GET_PASSPORT`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

If `true`:  
  In the pipeline, Cloud Passport discovery job is executed. Cloud Passport discovery will be launched.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`  

## `DEPLOYMENT_TICKET_ID`

**Description**: Used as commit message prefix for commit into Instance repository.

**Default Value**: None

**Mandatory**: No

**Example**: `TICKET-ID-12345`

## `ENV_TEMPLATE_VERSION`

**Description**: If provided system update Environment Template version in the Environment Inventory. System overrides `envTemplate.templateArtifact.artifact.version` OR `envTemplate.artifact` at `/environments/<ENV_NAME>/Inventory/env_definition.yml`

**Default Value**: None

**Mandatory**: No

**Example**: `env-template:v1.2.3`

## `ENV_INVENTORY_INIT`

**Description**:

If `true`:  
  In the pipeline, a job for generating the environment inventory is executed. The new Environment Inventory will be generated in the path `/environments/<ENV_NAME>/Inventory/env_definition.yml`. See details in [Environment Inventory Generation](/docs/env-inventory-generation.md)

**Default Value**: `false`

**Mandatory**: No

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

**Default Value**: None

**Mandatory**: No

**Example**: `env-template:v1.2.3`

## `ENV_SPECIFIC_PARAMS`

**Description**: Specifies Environment Inventory and env-specific parameters. This is can used together with `ENV_INVENTORY_INIT`. **JSON in string** format. See details in [Environment Inventory Generation](/docs/env-inventory-generation.md)

**Default Value**: None

**Mandatory**: No

**Example**:

```text
'{"clusterParams":{"clusterEndpoint":"<value>","clusterToken":"<value>"},"additionalTemplateVariables":{"<key>":"<value>"},"cloudName":"<value>","envSpecificParamsets":{"<ns-template-name>":["paramsetA"],"cloud":["paramsetB"]},"paramsets":{"paramsetA":{"version":"<paramset-version>","name":"<paramset-name>","parameters":{"<key>":"<value>"},"applications":[{"appName":"<app-name>","parameters":{"<key>":"<value>"}}]},"paramsetB":{"version":"<paramset-version>","name":"<paramset-name>","parameters":{"<key>":"<value>"},"applications":[]}},"credentials":{"credX":{"type":"<credential-type>","data":{"username":"<value>","password":"<value>"}},"credY":{"type":"<credential-type>","data":{"secret":"<value>"}}}}'
```

The same in YAML:

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

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

## `SD_SOURCE_TYPE`

**Description**: Defines the method by which SD is passed in the `SD_DATA` or `SD_VERSION` attributes. Valid values ​​are `artifact` OR `json`.

If `artifact`:  
  An SD artifact is expected in `SD_VERSION` in `application:version` notation. The system should download the artifact, transform it into YAML format, and save it to the repository.

If `json`:  
  SD content is expected in `SD_DATA`. The system should transform it into YAML format, and save it to the repository.

See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**: `artifact`

## `SD_VERSION`

**Description**: Defines the SD artifact in `application:version` notation

System downloads the artifact and overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml` with the content provided in the artifact. If the file is absent, it will be generated. See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**: `MONITORING:0.64.1`

## `SD_VERSION_MULTIPLE`

**Description**: One or more app:ver of the SD artifact passed via a `\n` separator. EnvGene downloads and sequentially merges them in the mode described in `SD_MERGE_MODE`, where subsequent app:ver takes priority over the previous one. Then, depending on `SD_DELTA`, it either overrides or merges with the Full SD. If the file is absent, it will be generated. See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**: `solution-part-1:0.64.2\nsolution-part-2:0.44.1`

## `SD_DATA`

**Description**: Defines the content of SD. **JSON in string** format.

System overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml` with the content provided in `SD_DATA`. If the file is absent, it will be generated. See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**:
JSON in string:

```text
'{"version":"2.1","type":"solutionDeploy","deployMode":"composite","applications":[{"version":"MONITORING:0.64.1","deployPostfix":"platform-monitoring"},{"version":"postgres:1.32.6","deployPostfix":"postgresql"},{"version":"postgres-services:1.32.6","deployPostfix":"postgresql"},{"version":"postgres:1.32.6","deployPostfix":"postgresql-dbaas"}]}'
```

The same in YAML:

```yaml
version: 2.1
type: "solutionDeploy"
deployMode: "composite"
applications:
  - version: "MONITORING:0.64.1"
    deployPostfix: "platform-monitoring"
  - version: "postgres:1.32.6"
    deployPostfix: "postgresql"
  - version: "postgres-services:1.32.6"
    deployPostfix: "postgresql"
  - version: "postgres:1.32.6"
    deployPostfix: "postgresql-dbaas"
```

## `SD_DATA_MULTIPLE`

**Description**: List of SD content in JSON-in-string format. EnvGene sequentially merges them in the mode described in `SD_MERGE_MODE`, where subsequent app:ver takes priority over the previous one. Then, depending on `SD_DELTA`, it either overrides or merges with the Full SD. If the file is absent, it will be generated. See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**:

```text
'{[{"version": 2.1, "type": "solutionDeploy", "deployMode": "composite", "applications": [{"version": "MONITORING:0.64.1", "deployPostfix": "platform-monitoring"}, {"version": "postgres:1.32.6", "deployPostfix": "postgresql"}]}, {"version": 2.1, "type": "solutionDeploy", "deployMode": "composite", "applications": [{"version": "postgres-services:1.32.6", "deployPostfix": "postgresql"}, {"version": "postgres:1.32.6", "deployPostfix": "postgresql-dbaas"}]}]}'
```

The same in YAML:

```yaml
- version: 2.1
  type: "solutionDeploy"
  deployMode: "composite"
  applications:
    - version: "MONITORING:0.64.1"
      deployPostfix: "platform-monitoring"
    - version: "postgres:1.32.6"
      deployPostfix: "postgresql"
- version: 2.1
  type: "solutionDeploy"
  deployMode: "composite"
  applications:
    - version: "postgres-services:1.32.6"
      deployPostfix: "postgresql"
    - version: "postgres:1.32.6"
      deployPostfix: "postgresql-dbaas"
```

## `SD_DELTA`

**Description**: Defines if SD provided in `SD_DATA` is Delta SD. Valid values ​​are `true` or `false`.

If `true`:  
  System overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/delta_sd.yml` with the content provided in `SD_DATA`. If the file is absent, it will be generated.
  System merges the content provided in `SD_DATA` into the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml`.

If `false` or not provided:  
  System overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml` with the content provided in `SD_DATA`. If the file is absent, it will be generated

See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**: `true`

## `SD_MERGE_MODE`

**Description**: SD merge mode between SDs passed in `SD_VERSION_MULTIPLE`/`SD_DATA_MULTIPLE`, as well as when merging the SD already in the repo with those passed via `SD_VERSION`/`SD_VERSION_MULTIPLE`/`SD_DATA`/`SD_DATA_MULTIPLE` (if `SD_DELTA`: `true`). See details in [SD processing](/docs/sd-processing.md)

**Default Value**: `basic-merge`

**Mandatory**: No

**Example**: `extended`
