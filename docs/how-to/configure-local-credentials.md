# Configure local Credentials

- [Configure local Credentials](#configure-local-credentials)
  - [Overview](#overview)
  - [When to use local Credentials](#when-to-use-local-credentials)
  - [Set a sensitive parameter](#set-a-sensitive-parameter)
    - [Step 1: Reference a credential in the parameter](#step-1-reference-a-credential-in-the-parameter)
    - [Step 2: Build the environment](#step-2-build-the-environment)
    - [Step 3: Set the value](#step-3-set-the-value)
    - [Verify the result](#verify-the-result)
  - [Use one value in several environments](#use-one-value-in-several-environments)
  - [Related documentation](#related-documentation)

## Overview

A parameter can hold a sensitive value, such as a password or a token. Set such a parameter through a local
Credential: the parameter references the Credential by its ID, and the value lives in a credentials file of the
Instance repository.

Credentials files can be encrypted. With `crypt: true` and `crypt_backend: SOPS` in `/configuration/config.yml` and
the pre-commit hook installed, the values are encrypted before they reach Git. See
[Credential encryption](/docs/how-to/credential-encryption.md).

## When to use local Credentials

Keep Credentials in the Instance repository when the site has no Secret Store. If it has one, use
[Configure external Credentials](/docs/how-to/configure-external-credentials.md) instead. All environments of an
Instance repository use the same approach.

## Set a sensitive parameter

### Step 1: Reference a credential in the parameter

Set the value of the parameter to a credential macro. Do it in the Environment Template or in an
environment-specific ParameterSet, see [Override template parameters](/docs/how-to/environment-specific-parameters.md):

```yaml
# environments/cluster-01/env-01/Inventory/parameters/partner-integration.yml
name: partner-integration
version: 1
parameters:
  PARTNER_API_USER: "${creds.get('partner-api-cred').username}"
  PARTNER_API_PASSWORD: "${creds.get('partner-api-cred').password}"
  PARTNER_API_TOKEN: "${creds.get('partner-api-token').secret}"
```

- Choose the credential ID yourself. It must be unique in the environment. Several parameters can use one ID.
- The field after the ID sets the type of the credential:

| Field                     | Type               | Holds                     |
|---------------------------|--------------------|---------------------------|
| `.username`, `.password`  | `usernamePassword` | a username and a password |
| `.secret`                 | `secret`           | one value                 |

### Step 2: Build the environment

Run the Instance pipeline:

```yaml
ENV_NAMES: cluster-01/env-01
ENV_BUILDER: true
```

`environments/cluster-01/env-01/Credentials/credentials.yml` now holds the credentials with placeholders:

```yaml
partner-api-cred:
  type: usernamePassword
  data:
    username: envgeneNullValue
    password: envgeneNullValue
partner-api-token:
  type: secret
  data:
    secret: envgeneNullValue
```

### Step 3: Set the value

Replace each `envgeneNullValue` in `Credentials/credentials.yml` with the value, and commit the file:

```yaml
partner-api-cred:
  type: usernamePassword
  data:
    username: partner-user
    password: partner-password
partner-api-token:
  type: secret
  data:
    secret: partner-token
```

If the same credential ID is in a Shared Credentials file or in the Cloud Passport credentials file, set the value
there instead. That file overwrites `Credentials/credentials.yml` on the next build.

### Verify the result

On the next Instance pipeline run that generates the Effective Set, the parameters from Step 1 hold the values from
Step 3. If a value is still `envgeneNullValue`, the job fails and lists the credentials to fill in:

```text
Error while validating credentials:
  credId: partner-api-token - secret is not set
```

## Use one value in several environments

When several environments use the same credential, setting its value by hand in each new environment repeats the
same work. Set the value once in a Shared Credentials file instead:

1. Create the file at the level of the environments that use it: `environments/<cluster>/credentials/` for one
   cluster, `environments/credentials/` for the whole repository. See
   [Choose the level of each file](/docs/how-to/create-environment-inventory.md#choose-the-level-of-each-file).

    ```yaml
    # environments/cluster-01/credentials/cluster-01-creds.yml
    partner-api-cred:
      type: usernamePassword
      data:
        username: partner-user
        password: partner-password
    ```

2. In `env_definition.yml` of each environment, list the filename without `.yml`:

    ```yaml
    envTemplate:
      sharedMasterCredentialFiles:
        - cluster-01-creds
    ```

3. Build the environments as in [Step 2](#step-2-build-the-environment).

EnvGene copies every credential of the file to `Credentials/credentials.yml`. A credential that no parameter
references stays unused.

## Related documentation

- [Credential encryption](/docs/how-to/credential-encryption.md)
- [Configure external Credentials](/docs/how-to/configure-external-credentials.md)
- [Override template parameters](/docs/how-to/environment-specific-parameters.md)
- [Working with envgeneNullValue](/docs/tutorials/envgene-null-value.md)
- [Credential rotation](/docs/features/cred-rotation.md)
- [Template macros: local credentials](/docs/template-macros.md#local-credentials-via-credsget)
