
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
  - [`EFFECTIVE_SET_CONFIG`](#effective_set_config)
  - [`SECRET_KEY`](#secret_key)
  - [`ENVGENE_AGE_PRIVATE_KEY`](#envgene_age_private_key)
  - [`ENVGENE_AGE_PUBLIC_KEY`](#envgene_age_public_key)
  - [`PUBLIC_AGE_KEYS`](#public_age_keys)
  - [`DEPLOYMENT_SESSION_ID`](#deployment_session_id)
  - [`SD_SOURCE_TYPE`](#sd_source_type)
  - [`SD_VERSION`](#sd_version)
  - [`SD_DATA`](#sd_data)
  - [`SD_DELTA`](#sd_delta)

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

JSON in string:

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

## `EFFECTIVE_SET_CONFIG`

**Description**: Settings for effective set configuration. This is used together with `GENERATE_EFFECTIVE_SET`. **JSON in string** format.

```yaml
version: <v1.0|v2.0>
effective_set_expiry: <effective-set-expiry-time>
app_chart_validation: <true|false>
contexts:
  operational:
    consumers:
      - name: <consumer-component-name>
        version: <consumer-component-version>
        schema: <json-schema-in-string>
```

| Attribute | Type | Mandatory | Description | Default | Example |
|---|---|---|---|---|---|
| **version** | string | Optional | The version of the effective set to be generated. Available options are `v1.0` and `v2.0`. EnvGene uses `--effective-set-version` to pass this attribute to the Calculator CLI. | `v2.0` | `v1.0` |
| **effective_set_expiry** | string | Optional | The duration for which the effective set (stored as a job artifact) will remain available for download. Envgene passes this value unchanged to: 1) The `retention-days` job attribute in case of GitHub pipeline. 2) The `expire_in` job attribute in case of GitLab pipeline. The exact syntax and constraints differ between platforms. Refer to the GitHub and GitLab documentation for details. | GitLab: `1 hours`, GitHub: `1` (day) | GitLab: `2 hours`, GitHub: `2` |
| **app_chart_validation** | boolean | Optional | Determines whether [app chart validation](/docs/calculator-cli.md#version-20-app-chart-validation) should be performed. If `true` validation is enabled (checks for `application/vnd.qubership.app.chart` in SBOM). If `false` validation is skipped | true | false |
| **contexts.operational.consumers** | string | Optional | Each entry in this list adds a [consumer-specific operational context component](/docs/calculator-cli.md#consumer-specific-context-of-pipeline-context) to the Effective Set. EnvGene passes the path to the corresponding JSON schema file to the Calculator CLI using the `--operational-consumer-specific-schema-path` argument. Each list element is passed as a separate argument. | None | None |
| **contexts.operational.consumers[].name** | string | Mandatory if `contexts.operational.consumers` is set | The name of the [consumer-specific operational context component](/docs/calculator-cli.md#consumer-specific-context-of-pipeline-context). If used without `contexts.operational.consumers[].schema`, the component must be pre-registered in EnvGene | None | `dcl` |
| **contexts.operational.consumers[].version** | string | Mandatory if `contexts.operational.consumers` is set | The version of the [consumer-specific operational context component](/docs/calculator-cli.md#consumer-specific-context-of-pipeline-context). If used without `contexts.operational.consumers[].schema`, the component must be pre-registered in EnvGene. | None | `v1.0`|
| **contexts.operational.consumers[].schema** | string | Optional | The content of the consumer-specific operational context component JSON schema transformed into a string. It is used to generate a consumer-specific operational context for a consumer not registered in EnvGene. EnvGene saves the value as a JSON file with the name `<contexts.operational[].name>-<contexts.operational[].version>.schema.json` and passes the path to it to the Calculator CLI via `--operational-consumer-specific-schema-path` attribute. The schema obtained in this way is not saved between pipeline runs and must be passed for each run. | None | [consumer-v1.0.json](/examples/consumer-v1.0.json) |

> [!WARNING]  
> The JSON schema passed in `contexts.operational.consumers[].schema` may contain a `$` symbol, for example in the `$schema` attribute. In this case, it must be escaped according to [GitLab's rules](https://docs.gitlab.com/ci/variables/#use-the--character-in-cicd-variables) by adding an additional `$` for escaping, for example `$$schema`.

Registered component JSON schemas are stored in the EnvGene Docker image as JSON files named: `<consumers-name>-<consumer-version>.schema.json`

Consumer-specific operational context components registered in EnvGene:

1. None

**Example**:

```json
{
  "version": "v2.0",
  "contexts": {
    "operational": {
      "consumers": [
        {
          "name": "dcl",
          "version": "v1.0",
          "schema": {
            "$schema": "http: //json-schema.org/draft-04/schema#",
            "type": "object",
            "properties": {
              "name": {
                "type": "string"
              },
              "version": {
                "type": "integer"
              },
              "group": {
                "type": "string",
                "default": "group"
              },
              "artifact": {
                "type": "string",
                "default": "artifact"
              },
              "registry": {
                "type": "string"
              }
            },
            "required": [
              "name",
              "version",
              "group"
            ]
          }
        }
      ]
    }
  }
}
```

The same in JSON in string format:

```text
{"version":"v2.0","contexts":{"operational":{"consumers":[{"name":"dcl","version":"v1.0","schema":{"$schema":"http: //json-schema.org/draft-04/schema#","type":"object","properties":{"name":{"type":"string"},"version":{"type":"integer"},"group":{"type":"string","default":"group"},"artifact":{"type":"string","default":"artifact"},"registry":{"type":"string"}},"required":["name","version","group"]}}]}}}
```

## `SECRET_KEY`

**Description**: Fernet key. Used to encrypt/decrypt credentials when `crypt_backend` s set to `Fernet` (mandatory in this case).  
Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/secret_key.txt`.

>[!Note]
> These are generally configured as GitLab CI/CD variables or GitHub environment variables.

**Default Value**: None

**Mandatory**: No

**Example**: `PjYtYZ4WnZsH2F4AxjDf_-QOSaL1kVHIkPOH7bpTFMI=`

## `ENVGENE_AGE_PRIVATE_KEY`

**Description**: Private key from EnvGene's AGE key pair. Used to encrypt credentials when `crypt_backend` is set to `SOPS` (mandatory in this case).  
Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/private-age-key.txt`.

>[!Note]
> These are generally configured as GitLab CI/CD variables or GitHub environment variables.

**Default Value**: None

**Mandatory**: No

**Example**: `AGE-SECRET-KEY-1N9APQZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY6`

## `ENVGENE_AGE_PUBLIC_KEY`

**Description**: Public key from EnvGene's AGE key pair. Added for logical completeness (not currently used in operations). For decryption, `PUBLIC_AGE_KEYS` is used instead.

**Example**: `age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p`

## `PUBLIC_AGE_KEYS`

**Description**: Contains a comma-separated list of public AGE keys from EnvGene and external systems (`<key_1>,<key_2>,...,<key_N>`). Used for credential encryption when `crypt_backend` is `SOPS` (mandatory in this case).  
Must include at least one key: EnvGene's own AGE public key.  
If an external system provides encrypted parameters, its public AGE key must also be included.  
Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/public-age-key.txt`.

>[!Note]
> These are generally configured as GitLab CI/CD variables or GitHub environment variables.

**Example**: `age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p,age113z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmca32p`

## `DEPLOYMENT_SESSION_ID`

**Description**: This parameter will be included in the deployment context of the Effective Set. The EnvGene passes it to the Calculator CLI using the `--extra_params` attribute. It is used together with `GENERATE_EFFECTIVE_SET`.

This attribute also appears in the git trailer of the commit in the instance repository for the commit made by the `git_commit_job` job.

The value must comply with [UUID Version 4](https://www.rfc-editor.org/rfc/rfc9562.html#name-uuid-version-4) format. EnvGene performs validation during Effective Set generation and fails the operation if the value is invalid.

If the parameter is not provided, EnvGene generates a value itself

**Default Value**: None

**Mandatory**: No

**Example**: "123e4567-e89b-12d3-a456-426614174000"

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
