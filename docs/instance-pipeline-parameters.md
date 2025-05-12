
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
  - [`SECRET_KEY`](#secret_key)
  - [`ENVGENE_AGE_PRIVATE_KEY`](#envgene_age_private_key)
  - [`ENVGENE_AGE_PUBLIC_KEY`](#envgene_age_public_key)
  - [`PUBLIC_AGE_KEYS`](#public_age_keys)

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

## `DEPLOYMENT_TICKET_ID`

**Description**: Used as commit message prefix for commit into Instance repository.

**Example**: "TICKET-ID-12345"

## `ENV_TEMPLATE_VERSION`

**Description**: If provided system update Environment Template version in the Environment Inventory. System overrides `envTemplate.templateArtifact.artifact.version` OR `envTemplate.artifact` at `/environments/<ENV_NAME>/Inventory/env_definition.yml`

**Example**: "env-template:v1.2.3"

## `ENV_INVENTORY_INIT`

**Description**:

If `true`:  
  In the pipeline, a job for generating the environment inventory is executed. The new Environment Inventory will be generated in the path `/environments/<ENV_NAME>/Inventory/env_definition.yml`. See details in [Environment Inventory Generation](/docs/env-inventory-generation.md)

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

**Description**: Specifies Environment Inventory and env-specific parameters. This is can used together with `ENV_INVENTORY_INIT`. **JSON in string** format. See details in [Environment Inventory Generation](/docs/env-inventory-generation.md)

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

## `SECRET_KEY`

**Description**: Fernet key. Used to encrypt/decrypt credentials when `crypt_backend` s set to `Fernet` (mandatory in this case).  
Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/secret_key.txt`.

>[!Note]
> These are generally configured as GitLab CI/CD variables or GitHub environment variables.

**Example**: "PjYtYZ4WnZsH2F4AxjDf_-QOSaL1kVHIkPOH7bpTFMI="

## `ENVGENE_AGE_PRIVATE_KEY`

**Description**: Private key from EnvGene's AGE key pair. Used to encrypt credentials when `crypt_backend` is set to `SOPS` (mandatory in this case).  
Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/private-age-key.txt`.

>[!Note]
> These are generally configured as GitLab CI/CD variables or GitHub environment variables.

**Example**: "AGE-SECRET-KEY-1N9APQZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY6"

## `ENVGENE_AGE_PUBLIC_KEY`

**Description**: Public key from EnvGene's AGE key pair. Added for logical completeness (not currently used in operations). For decryption, `PUBLIC_AGE_KEYS` is used instead.

**Example**: "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"

## `PUBLIC_AGE_KEYS`

**Description**: Contains a comma-separated list of public AGE keys from EnvGene and external systems (`<key_1>,<key_2>,...,<key_N>`). Used for credential encryption when `crypt_backend` is `SOPS` (mandatory in this case).  
Must include at least one key: EnvGene's own AGE public key.  
If an external system provides encrypted parameters, its public AGE key must also be included.  
Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/public-age-key.txt`.

>[!Note]
> These are generally configured as GitLab CI/CD variables or GitHub environment variables.

**Example**: "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p,age113z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmca32p"
