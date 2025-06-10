
# Instance Pipeline Parameters

- [Instance Pipeline Parameters](#instance-pipeline-parameters)
  - [Parameters](#parameters)
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
    - [`SD_DATA`](#sd_data)
    - [`SD_MULTIPLE_MERGE_MODE`](#sd_multiple_merge_mode)
    - [`SD_REPO_MERGE_MODE`](#sd_repo_merge_mode)
  - [Deprecated Parameters](#deprecated-parameters)
    - [`SD_DELTA`](#sd_delta)
  - [Archived Parameters](#archived-parameters)

The following are the launch parameters for the instance repository pipeline. These parameters influence, the execution of specific jobs within the pipeline.

All parameters are of the string data type

## Parameters

### `ENV_NAMES`

**Description**: Specifies the environment(s) for which processing will be triggered. Uses the `<cluster-name>/<env-name>` notation. If multiple environments are provided, they must be separated by a `\n` (newline) delimiter. In multi-environment case, each environment will trigger its own independent pipeline flow. All environments will use the same set of pipeline parameters (as documented in this spec)

**Default Value**: None

**Mandatory**: Yes

**Example**:
  
- Single environment: `ocp-01/platform`
- Multiple environments (separated by \n) `k8s-01/env-1\nk8s-01/env2`

### `ENV_BUILDER`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

If `true`:  
In the pipeline, Environment Instance generation job is executed. Environment Instance generation will be launched.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`  

### `GET_PASSPORT`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

If `true`:  
  In the pipeline, Cloud Passport discovery job is executed. Cloud Passport discovery will be launched.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`  

### `DEPLOYMENT_TICKET_ID`

**Description**: Used as commit message prefix for commit into Instance repository.

**Default Value**: None

**Mandatory**: No

**Example**: `TICKET-ID-12345`

### `ENV_TEMPLATE_VERSION`

**Description**: If provided system update Environment Template version in the Environment Inventory. System overrides `envTemplate.templateArtifact.artifact.version` OR `envTemplate.artifact` at `/environments/<ENV_NAME>/Inventory/env_definition.yml`

**Default Value**: None

**Mandatory**: No

**Example**: `env-template:v1.2.3`

### `ENV_INVENTORY_INIT`

**Description**:

If `true`:  
  In the pipeline, a job for generating the environment inventory is executed. The new Environment Inventory will be generated in the path `/environments/<ENV_NAME>/Inventory/env_definition.yml`. See details in [Environment Inventory Generation](/docs/env-inventory-generation.md)

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `ENV_TEMPLATE_NAME`

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

### `ENV_SPECIFIC_PARAMS`

**Description**: Specifies Environment Inventory and env-specific parameters. This is can used together with `ENV_INVENTORY_INIT`. **JSON in string** format. See details in [Environment Inventory Generation](/docs/env-inventory-generation.md)

**Default Value**: None

**Mandatory**: No

**Example**:

```text
'{"clusterParams":{"clusterEndpoint":"<value>","clusterToken":"<value>"},"additionalTemplateVariables":{"<key>":"<value>"},"cloudName":"<value>","envSpecificParamsets":{"<ns-template-name>":["paramsetA"],"cloud":["paramsetB"]},"paramsets":{"paramsetA":{"version":"<paramset-version>","name":"<paramset-name>","parameters":{"<key>":"<value>"},"applications":[{"appName":"<app-name>","parameters":{"<key>":"<value>"}}]},"paramsetB":{"version":"<paramset-version>","name":"<paramset-name>","parameters":{"<key>":"<value>"},"applications":[]}},"credentials":{"credX":{"type":"<credential-type>","data":{"username":"<value>","password":"<value>"}},"credY":{"type":"<credential-type>","data":{"secret":"<value>"}}}}'
```

### `GENERATE_EFFECTIVE_SET`

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

### `SD_VERSION`

**Description**: Specifies one or more SD artifacts in `application:version` notation passed via a `\n` separator.

EnvGene downloads and sequentially merges them in the mode described in `SD_MULTIPLE_MERGE_MODE`, where subsequent `application:version` takes priority over the previous one. Saves the result to [Delta SD](/docs/sd-processing.md#delta-sd), then merges with [Full SD](/docs/sd-processing.md#full-sd) using `SD_REPO_MERGE_MODE` merge mode

See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**:

- Single SD: `MONITORING:0.64.1`
- Multiple SD (separated by \n) `solution-part-1:0.64.2\nsolution-part-2:0.44.1`

### `SD_DATA`

**Description**: Specifies the **list** of contents of one or more SD in JSON-in-string format.

EnvGene sequentially merges them in the mode described in `SD_MULTIPLE_MERGE_MODE`, where subsequent element takes priority over the previous one. Saves the result to [Delta SD](/docs/sd-processing.md#delta-sd), then merges with [Full SD](/docs/sd-processing.md#full-sd) using `SD_REPO_MERGE_MODE` merge mode

See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**:

- Single SD:

```text
'[{"version":2.1,"type":"solutionDeploy","deployMode":"composite","applications":[{"version":"MONITORING:0.64.1","deployPostfix":"platform-monitoring"},{"version":"postgres:1.32.6","deployPostfix":"postgresql"}]},{"version":2.1,"type":"solutionDeploy","deployMode":"composite","applications":[{"version":"postgres-services:1.32.6","deployPostfix":"postgresql"},{"version":"postgres:1.32.3","deployPostfix":"postgresql-dbaas"}]}]'
```

- Multiple SD:

```text
'[{[{"version": 2.1, "type": "solutionDeploy", "deployMode": "composite", "applications": [{"version": "MONITORING:0.64.1", "deployPostfix": "platform-monitoring"}, {"version": "postgres:1.32.6", "deployPostfix": "postgresql"}]}, {"version": 2.1, "type": "solutionDeploy", "deployMode": "composite", "applications": [{"version": "postgres-services:1.32.6", "deployPostfix": "postgresql"}, {"version": "postgres:1.32.6", "deployPostfix": "postgresql-dbaas"}]}]}]'
```

### `SD_MULTIPLE_MERGE_MODE`

**Description**: Defines SD merge mode between SDs passed in `SD_VERSION`/`SD_DATA`. See details in [SD Merge](/docs/sd-processing.md#sd-merge)

Available values:

- `basic-merge`
- `extended-merge`

See details in [SD processing](/docs/sd-processing.md)

**Default Value**: `basic-merge`

**Mandatory**: No

**Example**: `extended-merge`

### `SD_REPO_MERGE_MODE`

**Description**: Defines SD merge mode between incoming SD and already existed in repository SD. See details in [SD Merge](/docs/sd-processing.md#sd-merge)

Available values:

- `basic-merge`
- `basic-exclusion-merge`
- `extended-merge`
- `replace`

See details in [SD processing](/docs/sd-processing.md)

**Default Value**: `basic-merge`

**Mandatory**: No

**Example**: `extended-merge`

## Deprecated Parameters

The following parameters are planned for removal

### `SD_DELTA`

**Description**: Deprecated

If `true`: behaves identically to `SD_REPO_MERGE_MODE: extended-merge`

If `false`: behaves identically to `SD_REPO_MERGE_MODE: replace`

See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**: `true`

## Archived Parameters

These parameters are no longer in use and are maintained for historical reference
