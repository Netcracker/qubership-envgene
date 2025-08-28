
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
    - [`APP_REG_DEFS_JOB`](#app_reg_defs_job)
    - [`SD_SOURCE_TYPE`](#sd_source_type)
    - [`SD_VERSION`](#sd_version)
    - [`SD_DATA`](#sd_data)
    - [`SD_REPO_MERGE_MODE`](#sd_repo_merge_mode)
    - [`CRED_ROTATION_PAYLOAD`](#cred_rotation_payload)
      - [Affected Parameters and Troubleshooting](#affected-parameters-and-troubleshooting)
    - [`CRED_ROTATION_FORCE`](#cred_rotation_force)
  - [Archived Parameters](#archived-parameters)
  - [Deprecated Parameters](#deprecated-parameters)
    - [`SD_DELTA`](#sd_delta)

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

### `APP_REG_DEFS_JOB`

**Description**: Controls the source of AppDef/RegDef files for environment generation. This parameter can be used in two ways:

1. **External Job Artifacts** (when set to a job name): The system will retrieve AppDef/RegDef files from the specified job's artifacts. It will download and unpack a `definitions.zip` file from the specified job and use the files from the paths specified by `app_defs_path` and `reg_defs_path` parameters. This is useful when AppDef/RegDef files are generated by a separate pipeline or process.

2. **Local Template Rendering** (when not set or empty): The system will discover and render AppDef/RegDef templates from the template repository. Templates are located in `/templates/appdefs/` and `/templates/regdefs/` directories and can be either static files (`.yaml`/`.yml`) or Jinja2 templates (`.j2`).

When using local template rendering, the process is further controlled by the `app_reg_def_mode` setting in `config.yml` (values: `auto`, or `local`), which determines whether data is sourced from local templates.

**Default Value**: `false`

**Mandatory**: No

**Example Values**:

- `appdef-generation-job` - Use AppDef/RegDef files from the specified job's artifacts
- `` (empty) - Use local template rendering from the template repository

### `SD_SOURCE_TYPE`

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

EnvGene downloads and sequentially merges them in the `basic-merge` mode, where subsequent `application:version` takes priority over the previous one. Optionally saves the result to [Delta SD](/docs/sd-processing.md#delta-sd), then merges with [Full SD](/docs/sd-processing.md#full-sd) using `SD_REPO_MERGE_MODE` merge mode

See details in [SD processing](/docs/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**:

- Single SD: `MONITORING:0.64.1`
- Multiple SD (separated by \n) `solution-part-1:0.64.2\nsolution-part-2:0.44.1`

### `SD_DATA`

**Description**: Specifies the **list** of contents of one or more SD in JSON-in-string format.

EnvGene sequentially merges them in the `basic-merge` mode, where subsequent element takes priority over the previous one. Optionally saves the result to [Delta SD](/docs/sd-processing.md#delta-sd), then merges with [Full SD](/docs/sd-processing.md#full-sd) using `SD_REPO_MERGE_MODE` merge mode

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

### `CRED_ROTATION_PAYLOAD`

**Description**: A parameter used to dynamically update sensitive parameters (those defined via the [cred macro](/docs/template-macros.md#credential-macros)). It modifies values across different contexts within a specified namespace and optional application. The value can be provided as plain text or encrypted. **JSON in string** format. See details in [feature description](/docs/features/cred-rotation.md)

```json
{
  "rotation_items": [
    {
      "namespace": "<namespace>",
      "application": "<application-name>",
      "context": "enum[`pipeline`,`deployment`, `runtime`]",
      "parameter_key": "<parameter-key>",
      "parameter_value": "<new-parameter-value>"
    }
  ]
}
```

| Attribute         | Mandatory | Description                                                                                                                                                                                                 | Default | Example |
|-------------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|---------|
| `namespace`       | Mandatory | The name of the Namespace where the parameter to be modified is defined                                                                                               | None    | `env-1-platform-monitoring` |
| `application`     | Optional  | The name of the Application (sub-resource under `namespace`) where the parameter to be modified is defined. Cannot be used with `pipeline` context                   | None    | `MONITORING` |
| `context`         | Mandatory | The context of the parameter being modified. Valid values: `pipeline`, `deployment`, `runtime`                                                                       | None    | `deployment` |
| `parameter_key`   | Mandatory | The name (key) of the parameter to be modified | None    | `login` or `db.connection.password` |
| `parameter_value` | Mandatory | New value (plaintext or encrypted). Envgene, depending on the value of the [`crypt`](/docs/envgene-configs.md#configyml) attribute, will either decrypt, encrypt, or leave the value unchanged. If an encrypted value is passed, it must be encrypted with a key that Envgene can decrypt. | None    | `admin` |

**Default Value**: None

**Mandatory**: No

**Example**:

```json
{
  "rotation_items": [
    {
      "namespace": "env-1-platform-monitoring",
      "application": "MONITORING",
      "context": "deployment",
      "parameter_key": "db_login",
      "parameter_value": "s3cr3tN3wLogin"
    },
    {
      "namespace": "env-1-platform-monitoring",
      "application": "MONITORING",
      "context": "deployment",
      "parameter_key": "db_password",
      "parameter_value": "s3cr3tN3wP@ss"
    },
    {
      "namespace": "env-1-platform-monitoring",
      "context": "deployment",
      "parameter_key": "db_password",
      "parameter_value": "s3cr3tN3wP@ss"
    },
    {
      "namespace": "env-1-platform-monitoring",
      "context": "deployment",
      "parameter_key": "global.secrets.password",
      "parameter_value": "user"
    },
    {
      "namespace": "env-1-platform-monitoring",
      "context": "deployment",
      "parameter_key": "a.b.c.d",
      "parameter_value": "somevalue"
    }
  ]
}
```

#### Affected Parameters and Troubleshooting

When rotating sensitive parameters, EnvGene checks if the Credential is [shared](https://github.com/Netcracker/qubership-envgene/blob/feature/cred-rotation/docs/features/cred-rotation.md#affected-parameters) (used by multiple parameters or Environments). If shared Credentials are detected and force mode is not enabled, the credential_rotation job will fail to prevent accidental mass updates.

- In this case, the job will generate an [`affected-sensitive-parameters.yaml`](https://github.com/Netcracker/qubership-envgene/blob/feature/cred-rotation/docs/features/cred-rotation.md#affected-parameters-reporting) file as an artifact. This file lists all parameters and locations affected by the Credential change, including those in shared Credentials files and all Environments that reference this credential.
- To resolve:
  - Review `affected-sensitive-parameters.yaml` to see which parameters and environments are linked by the shared Credential.
  - Either:
    - Manually split the shared Credential in the repository so each parameter uses its own Credential, **or**
    - Rerun the Credential rotation job with force mode enabled (`CRED_ROTATION_FORCE=true`) to update all linked parameters.

> **Note:** When rotating a shared credential, all parameters in all Environments that reference this credential will be updated. This is why force mode is required for such operations to avoid accidental mass changes. The `affected-sensitive-parameters.yaml` file will list all such parameters and environments.

### `CRED_ROTATION_FORCE`

**Description**: Enables force mode for updating sensitive parameter values. In force mode, the sensitive parameter value will be changed even if it affects other sensitive parameters that may be linked through the same credential. See details in [Credential Rotation](/docs/cred-rotation.md)

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

## Archived Parameters

These parameters are no longer in use and are maintained for historical reference

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
