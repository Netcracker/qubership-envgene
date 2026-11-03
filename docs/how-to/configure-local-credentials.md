# Configure Local Credentials

- [Configure Local Credentials](#configure-local-credentials)
  - [Overview](#overview)
  - [When to use local credentials](#when-to-use-local-credentials)
  - [Prerequisites](#prerequisites)
  - [How local credentials work](#how-local-credentials-work)
  - [Set a sensitive parameter](#set-a-sensitive-parameter)
    - [Step 1: Reference a credential in the parameter](#step-1-reference-a-credential-in-the-parameter)
    - [Step 2: Build the environment](#step-2-build-the-environment)
    - [Step 3: Set the value](#step-3-set-the-value)
    - [Step 4: Generate the Effective Set](#step-4-generate-the-effective-set)
  - [Use one value in several environments](#use-one-value-in-several-environments)
  - [Set a system credential](#set-a-system-credential)
  - [Change a value](#change-a-value)
  - [Related documentation](#related-documentation)

## Overview

A parameter can hold a sensitive value, such as a password or a token. Set such a parameter through a credential:
the parameter references the credential by its ID, and the value lives in a credentials file of the Instance
repository.

Credentials files can be encrypted. With `crypt: true` and `crypt_backend: SOPS` in `/configuration/config.yml` and
the pre-commit hook installed, the values are encrypted before they reach Git. See
[Credential Encryption](/docs/how-to/credential-encryption.md).

## When to use local credentials

Keep credentials in the Instance repository when the site has no Secret Store. If it has one, use
[Configure External Credentials](/docs/how-to/configure-external-credentials.md) instead. An environment uses one
approach, never both.

## Prerequisites

- The environment exists, see [Create an Environment Inventory](/docs/how-to/create-environment-inventory.md).

## How local credentials work

1. A parameter in the Environment Template or in an environment-specific ParameterSet takes a credential macro as its
   value, such as `${creds.get('app-db-cred').password}`. The template and the ParameterSet hold only the macro, not
   the credential.
2. When it builds the environment, EnvGene creates one credential per credential ID in
   `environments/<cluster>/<env>/Credentials/credentials.yml`. A new credential holds the placeholder
   `envgeneNullValue`.
3. You replace the placeholder with the value. EnvGene keeps the values on the next builds.
4. When it generates the Effective Set, EnvGene puts the value of the credential into the parameter. If a placeholder
   remains, the generation fails.

A Shared Credentials file, or the credentials file of the Cloud Passport, already holds values. EnvGene applies it
to `Credentials/credentials.yml` on every build and overwrites the values of the same credential IDs.

## Set a sensitive parameter

### Step 1: Reference a credential in the parameter

Set the value of the parameter to a credential macro. Do it in the Environment Template or in an
environment-specific ParameterSet, see [Override Template Parameters](/docs/how-to/environment-specific-parameters.md):

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

### Step 4: Generate the Effective Set

Run the Instance pipeline:

```yaml
ENV_NAMES: cluster-01/env-01
ENV_BUILDER: true
GENERATE_EFFECTIVE_SET: true
```

The parameters in the Effective Set hold the values from Step 3. If a value is not set, the job fails and lists the
credentials to fill in:

```text
Error while validating credentials:
  credId: partner-api-token - secret is not set
```

## Use one value in several environments

To set a value once for several environments, put it in a Shared Credentials file:

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

2. In `env_definition.yml` of each environment, list the file name without `.yml`:

    ```yaml
    envTemplate:
      sharedMasterCredentialFiles:
        - cluster-01-creds
    ```

3. Build the environments as in [Step 2](#step-2-build-the-environment).

EnvGene copies every credential of the file to `Credentials/credentials.yml`. A credential that no parameter
references stays unused.

The file can also be created through the `credentials` block of `ENV_INVENTORY_CONTENT`, see
[Create an Environment Inventory](/docs/how-to/create-environment-inventory.md). The values then pass through the
pipeline parameter in plain text.

## Set a system credential

System credentials are the sensitive parameters of the EnvGene configuration, such as `self_token` in
`/configuration/integration.yml`. EnvGene does not generate placeholders for them: create the credential yourself.

1. Set the parameter to a credential macro:

    ```yaml
    # configuration/integration.yml
    self_token: envgen.creds.get('self-token-cred').secret
    ```

2. Add the credential with its value to `/configuration/credentials/credentials.yml`:

    ```yaml
    # configuration/credentials/credentials.yml
    self-token-cred:
      type: secret
      data:
        secret: <token>
    ```

Registry credentials work the same way, see
[Configure artifact registries](/docs/how-to/configure-cloud-artifact-registries.md). The credentials of
`deployer.yml` live in `deployer-creds.yml` next to it. For the list of system credentials, see
[EnvGene System Credentials](/docs/features/external-creds.md#envgene-system-credentials).

## Change a value

| Where the value is                    | How to change it                                                                  |
|---------------------------------------|-----------------------------------------------------------------------------------|
| `Credentials/credentials.yml`         | Edit the value in the file                                                        |
| A Shared Credentials file             | Edit the value in the file                                                        |
| The Cloud Passport credentials file   | Edit `<passport-name>-creds.yml`, or run Cloud Passport discovery again           |
| One value used in several places      | Use [Credential Rotation](/docs/features/cred-rotation.md). Works with SOPS only  |

Then generate the Effective Set as in [Step 4](#step-4-generate-the-effective-set).

## Related documentation

- [Credential Encryption](/docs/how-to/credential-encryption.md)
- [Configure External Credentials](/docs/how-to/configure-external-credentials.md)
- [Override Template Parameters](/docs/how-to/environment-specific-parameters.md)
- [Working with envgeneNullValue](/docs/tutorials/envgene-null-value.md)
- [Credential Rotation](/docs/features/cred-rotation.md)
- [Template macros: local credentials](/docs/template-macros.md#local-credentials-via-credsget)
