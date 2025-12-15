
# Credential Rotation

- [Credential Rotation](#credential-rotation)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Assumptions \& Limitation](#assumptions--limitation)
    - [Requirements](#requirements)
    - [Instance Repository Pipeline Parameters](#instance-repository-pipeline-parameters)
      - [`CRED_ROTATION_PAYLOAD`](#cred_rotation_payload)
        - [`CRED_ROTATION_PAYLOAD` example](#cred_rotation_payload-example)
    - [`credential_rotation` Job Workflow Principle](#credential_rotation-job-workflow-principle)
    - [Dot-Notation Keys Processing](#dot-notation-keys-processing)
    - [Encryption](#encryption)
      - [Processing Flow](#processing-flow)
    - [Affected parameters](#affected-parameters)
    - [Force mode](#force-mode)
    - [Affected Parameters Reporting](#affected-parameters-reporting)
      - [`affected-sensitive-parameters.yaml` File](#affected-sensitive-parametersyaml-file)
    - [Test Cases](#test-cases)

## Problem Statement

Sensitive parameter rotation is a multi-stage process that involves interaction with EnvGene as the Environment parameter management system. Manual rotation:

- Consumes excessive staff resources
- Requires specialized expertise
- Introduces potential for human errors

Automating this procedure necessitates implementing an interface in EnvGene that would allow external orchestration systems to modify sensitive parameter values

## Proposed Approach

EnvGene uses the `CRED_ROTATION_PAYLOAD` Instance pipeline parameter for credentials rotation. It contains:

- The name of a sensitive parameter
- Its new value
- Attributes that allow parameter localization within the environment instance structure

When EnvGene receives this parameter. It launches a dedicated job. The job performs the parameter value rotation.

During value modification validation is performed for affected credentials. Depending on the `CRED_ROTATION_FORCE` if affected credentials exist the operation either fails or proceeds. In both cases, the list of affected credentials is saved in the job artifacts.

Supports working with SOPS encryption.

### Assumptions & Limitation

1. Only sensitive parameters defined at the Namespace level or its child Applications can be rotated. It is assumed that:
   1. Defining sensitive parameters at the Tenant level is considered an antipattern
   2. Cloud level sensitive parameters must be rotated via Credential rotation in the underlying environment, and subsequent Cloud or Infra Passport discovery
2. Only existing credentials can be rotated; creating new ones through `CRED_ROTATION_PAYLOAD` is not possible
3. Only `SOPS` `crypt_backend` is supported
4. An external system is responsible for triggering Effective Set generation
5. An external system is responsible for triggering Cloud Passport rediscovery
6. Credential rotation can only be run for a single Environment at a time
7. Credential rotation in a single operation for multiple Environments is not supported. `ENV_NAMES` can only contain a single Environment ID.

### Requirements

1. Credential rotation operation is performed in a separate `credential_rotation` job
   1. The job must be launched after the `env_inventory_generation_job` and before the `env_build_job`
2. Credential rotation operation must complete within 1 second (excluding GitLab/GitHub runner span time) for `CRED_ROTATION_PAYLOAD` with 10 elements
3. Job logs must clearly show how long the job took to execute
4. The operation must fail if there are [affected parameters](#affected-parameters) and `CRED_ROTATION_FORCE` is `false` or not specified
5. Job artifacts must include a file containing [affected parameters](#affected-parameters)
   1. The file must contain all affected parameters for each parameter from `CRED_ROTATION_PAYLOAD`
6. The operation must support the following [Credential](/docs/envgene-objects.md#credential) types:
   1. `usernamePassword`
   2. `secret`
7. Encryption principles described in [Encryptio](#encryption) section must be followed
8. If any error occurs during the processing of a single key in `CRED_ROTATION_PAYLOAD`, the system shall:
   - Preserve the system state prior to the failed operation
   - Terminate the entire credential rotation job with a failure status
   - Throw readable error in the logs

### Instance Repository Pipeline Parameters

| Attribute | Type | Mandatory | Description | Default | Example |
|---|---|---|---|---|---|
| `CRED_ROTATION_PAYLOAD` | string | no | A parameter used to dynamically update sensitive parameters (those defined via the [cred macro](/docs/template-macros.md#credential-macro)). It modifies values across different contexts within a specified namespace and optional application. The value can be provided as plain text or encrypted. **JSON in string** format | None | [example](#cred_rotation_payload-example) |
| `CRED_ROTATION_FORCE` | string | no | Enables force mode for updating sensitive parameter values. In force mode, the sensitive parameter value will be changed even if it affects other sensitive parameters that may be linked through the same credential | `false` | `true` |

#### `CRED_ROTATION_PAYLOAD`

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
| `namespace`       | Mandatory | The name of the namespace where the parameter to be modified is defined                                                                                               | None    | `env-1-platform-monitoring` |
| `application`     | Optional  | The name of the application (sub-resource under `namespace`) where the parameter to be modified is defined. Cannot be used with `pipeline` context                   | None    | `MONITORING` |
| `context`         | Mandatory | The context of the parameter being modified. Valid values: `pipeline`, `deployment`, `runtime`                                                                       | None    | `deployment` |
| `parameter_key`   | Mandatory | The name (key) of the parameter to be modified. | None    | `login` or `db.connection.password` |
| `parameter_value` | Mandatory | New value (plaintext or encrypted). Envgene, depending on the value of the [`crypt`](/docs/envgene-configs.md#configyml) attribute, will either decrypt, encrypt, or leave the value unchanged. If an encrypted value is passed, it must be encrypted with a key that Envgene can decrypt. | None    | `admin` |

A sensitive parameter can be defined within a complex parameter structure. In such cases during rotation, the `parameter_key` should use dot notation (e.g., `key1.key2.username`)

##### `CRED_ROTATION_PAYLOAD` example

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
    }
  ]
}
```

### `credential_rotation` Job Workflow Principle

Per-Item Processing (for each item in `CRED_ROTATION_PAYLOAD`):

1. In the Environment Instance passed in `ENV_NAMES`, find the object containing the parameter to be modified:
   1. It is Namespace if the item's `application` is not specified. The Namespace's `name` must match the item's `namespace`
   2. It is Application if the item's `application` is specified. The Application's `name` must match the item's `application`. This Application must be a child of the Namespace matching the item's `namespace`
2. Find the context containing the parameter to be modified on the object from step 1:
   1. It is `e2eParameters` if item's context is `pipeline`
   2. It is `deployParameters` if item's context is `deployment`
   3. It is `technicalConfigurationParameters` if item's context is `runtime`
3. Find the cred-id linked (via the [cred macro](/docs/template-macros.md#credential-macro)) to the parameter matching the item's `parameter_key` on the object from step 1 in the context from step 2
4. Find all [affected parameters](#affected-parameters) for this parameter
5. Save affected parameters in job artifacts
6. Perform [force mode](#force-mode) check
7. Replace the Credential with cred-id from step 3 value with item's `parameter_value` (taking into account [encryption](#encryption)) in:
   1. [Environment Credentials file](/docs/envgene-objects.md#environment-credentials-file) of the Environment for which the operation is being performed
   2. All affected [Shared Credentials file](/docs/envgene-objects.md#shared-credentials-file)
   3. Environment Credentials files of all affected Environments

> [!NOTE]
> The above description represents a high-level abstraction of the workflow logic, not an exact algorithmic specification

### Dot-Notation Keys Processing

1. Literal Search: First, search for the exact key as a literal string (including dots)
2. Recursive Map Traversal: If not found, split the key at the first dot:
3. Use the part before the dot as a map key
4. Search for the remaining part (after the dot) as a literal within that map
5. Iterative Process: If still not found, repeat the process for each subsequent dot in the key
6. Error Handling: If no match is found after processing all dots, return an error

Example: For key `a.b.c`:

First try: search for literal `a.b.c`
Second try: search for `b.c` within map `a`
Third try: search for `c` within map `a.b`

### Encryption

The credential encryption mode in EnvGene is determined by the `crypt` configuration attribute in [`config.yml`](/docs/envgene-configs.md#configyml). If the value is `true` or not specified, encryption mode is enabled.

In encryption mode **all Credential in the repository must be encrypted**. EnvGene decrypts values in runtime when it needed usage.

Credential rotation is only compatible with `SOPS` `crypt_backend`. Key characteristics of this mode:

- The entire Credential file is encrypted as a single unit
- Any encrypted Credential file update requires:
  1. Full file decryption
  2. Value modification
  3. Full file re-encryption

#### Processing Flow

**When encryption is enabled AND `CRED_ROTATION_PAYLOAD` is encrypted:**

1. Decrypt `CRED_ROTATION_PAYLOAD` using `ENVGENE_AGE_PUBLIC_KEY` key
2. Decrypt credential files using `ENVGENE_AGE_PUBLIC_KEY` key
3. Update value in credential files
4. Encrypt credential files using `ENVGENE_AGE_PRIVATE_KEY` key

**When encryption is enabled AND `CRED_ROTATION_PAYLOAD` is NOT encrypted:**

1. Decrypt credential files using `ENVGENE_AGE_PUBLIC_KEY` key
2. Update value in credential files
3. Encrypt credential files using `ENVGENE_AGE_PRIVATE_KEY` key

**When encryption is disabled AND `CRED_ROTATION_PAYLOAD` is encrypted:**

1. Decrypt `CRED_ROTATION_PAYLOAD` using `ENVGENE_AGE_PUBLIC_KEY` key
2. Update value in credential files

**When encryption is disabled AND `CRED_ROTATION_PAYLOAD` is NOT encrypted:**

1. Update value in credential files

> [!NOTE]
> credential files are [Environment Credentials file](/docs/envgene-objects.md#environment-credentials-file) and [Shared Credentials file](/docs/envgene-objects.md#shared-credentials-file)

### Affected parameters

Sensitive parameters defined across one or more objects in one or more Environment Instances can be linked. Changing a Credential's value for one parameter will update **all linked parameters in all Environments that reference this credential**.

This linkage occurs when multiple parameters reference the same:

1. Credential ID (`cred-id`)
AND
2. Credential field (`username`, `password`, or `secret`)

Parameters can be linked through common credential in:

1. [Environment Credentials file](/docs/envgene-objects.md#environment-credentials-file)
2. [Shared Credentials file](/docs/envgene-objects.md#shared-credentials-file)

The diagram below illustrates three scenarios:

- No linkage between parameters
- Linkage through a Environment Credentials file
- Linkage through a Shared Credentials file

![cred-affection.png](/docs/images/cred-affection.png)

### Force mode

EnvGene only permits rotation of credentials with affected parameters in **force mode**, determined by the Instance pipeline parameter `CRED_ROTATION_FORCE`. In non-force mode, the `credential_rotation` job fails and no value changes occur.

### Affected Parameters Reporting

For user and external system awareness, an `affected-sensitive-parameters.yaml` file is generated whenever affected parameters exist, regardless of force mode. This file is saved in the `credential_rotation` job artifacts.

The `affected-sensitive-parameters.yaml` is created using the reverse logic described in the [`credential_rotation` Job Workflow Principle](#credential_rotation-job-workflow-principle).

> **Note:** If the credential is shared, this file will list all parameters and environments that will be updated by the rotation operation.

#### `affected-sensitive-parameters.yaml` File

```yaml
- # Mandatory
  # Taken from `CRED_ROTATION_PAYLOAD` item
  target_parameter:
    environment: string
    namespace: string
    application: string
    context: enum[`pipeline`,`deployment`,`runtime`]
    parameter_key: string
    cred_field: enum[`username`,`password`,`secret`]
  affected_parameters:
    - # Mandatory
      # Environment ID (in cluster-name/env-name notation) where affected parameter is located
      environment: string
      # Mandatory
      # Namespace where affected parameter is located
      namespace: string
      # Mandatory. Default `None`
      # Application where affected parameter is located
      application: string
      # Mandatory
      # Effective Set context where the parameter is located.
      context: enum[`pipeline`,`deployment`,`runtime`]
      # Mandatory
      # Affected parameter key
      parameter_key: string
      # Mandatory
      # Affected Credential ID
      cred_id: string
      # Mandatory
      # Path to Environment Credentials File with affected cred
      environment_creds_filepath: string
      # Mandatory. Default `[]`
      # Path to all Shared Credentials Files with affected cred
      shared_creds_filepath:
        - string
        - string
- ...
```

### Test Cases

  1. [cred-rotation](/docs/test-cases/cred-rotation.md)
