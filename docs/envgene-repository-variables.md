
# EnvGene Repository Variables

- [EnvGene Repository Variables](#envgene-repository-variables)
  - [Instance EnvGene Repository](#instance-envgene-repository)
    - [`SECRET_KEY`](#secret_key)
    - [`ENVGENE_AGE_PRIVATE_KEY`](#envgene_age_private_key)
    - [`ENVGENE_AGE_PUBLIC_KEY`](#envgene_age_public_key)
    - [`PUBLIC_AGE_KEYS`](#public_age_keys)
    - [`IS_OFFSITE`](#is_offsite)
    - [`GITLAB_RUNNER_TAG_NAME`](#gitlab_runner_tag_name)
  - [Template EnvGene Repository](#template-envgene-repository)
    - [`IS_TEMPLATE_TEST`](#is_template_test)

The following are parameters that are set in GitLab CI/CD variables or GitHub environment variables.

All parameters are of string data type.

## Instance EnvGene Repository

### `SECRET_KEY`

**Description**: Fernet key. Used to encrypt/decrypt credentials when [`crypt_backend`](/docs/envgene-configs.md#configyml) is set to `Fernet`

Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/secret_key.txt`.

**Default Value**: None

**Mandatory**: Yes, if repository encryption is enabled with `Fernet` crypt backend

**Example**: `PjYtYZ4WnZsH2F4AxjDf_-QOSaL1kVHIkPOH7bpTFMI=`

### `ENVGENE_AGE_PRIVATE_KEY`

**Description**: Private key from EnvGene's AGE key pair. Used to encrypt credentials when [`crypt_backend`](/docs/envgene-configs.md#configyml) is set to `SOPS`

Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/private-age-key.txt`.

**Default Value**: None

**Mandatory**: Yes, if repository encryption is enabled with `SOPS` crypt backend

**Example**: `AGE-SECRET-KEY-1N9APQZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY5QZ3PZJQY6`

### `ENVGENE_AGE_PUBLIC_KEY`

**Description**: Public key from EnvGene's AGE key pair. Added for logical completeness (not currently used in operations). For decryption, `PUBLIC_AGE_KEYS` is used instead.

**Example**: `age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p`

### `PUBLIC_AGE_KEYS`

**Description**: Contains a comma-separated list of public AGE keys from EnvGene and external systems (`<key_1>,<key_2>,...,<key_N>`). Used for credential encryption when [`crypt_backend`](/docs/envgene-configs.md#configyml) is `SOPS`

Must include at least one key: EnvGene's own AGE public key.  
If an external system provides encrypted parameters, its public AGE key must also be included.  
Used by EnvGene at runtime, when using pre-commit hooks, the same value must be specified in `.git/public-age-key.txt`.

**Default Value**: None

**Mandatory**: Yes, if repository encryption is enabled with `SOPS` crypt backend

**Example**: `age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p,age113z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmca32p`

### `IS_OFFSITE`

**Description**: Determines whether this repository is located "offsite". Based on this parameter:

- The Cloud Passport is decrypted in the case of Cloud Passport discovery.

**Default Value**: `true`

**Mandatory**: No

**Example**: `false`

### `GITLAB_RUNNER_TAG_NAME`

**Description**: The tag that identifies the GitLab runner used for executing CI jobs. This tag helps specify which runner will pick up and execute the job in the CI pipeline.

**Default Value**: None

**Mandatory**: No

## Template EnvGene Repository

### `IS_TEMPLATE_TEST`

**Description**: Determines whether the generation of the Environment Instance is running in Template Testing mode.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`
