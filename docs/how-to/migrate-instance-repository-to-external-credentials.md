# Migrate Instance Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1: Inventory the Instance Repository](#step-1-inventory-the-instance-repository)
- [Step 2: Decide create and remoteRefPath](#step-2-decide-create-and-remoterefpath)
- [Step 3: Configure Secret Store](#step-3-configure-secret-store)
- [Step 4: Convert Cloud Passport Credentials and main file](#step-4-convert-cloud-passport-credentials-and-main-file)
- [Step 5: Convert Shared Credentials](#step-5-convert-shared-credentials)
- [Step 6: Convert System Credentials (optional)](#step-6-convert-system-credentials-optional)
- [Step 7: Update environment-specific parameters](#step-7-update-environment-specific-parameters)
- [Step 8: Remove stale generated Credentials files](#step-8-remove-stale-generated-credentials-files)
- [Step 9: Validate before the pipeline](#step-9-validate-before-the-pipeline)
- [Step 10: Run the Instance pipeline (first run - skip)](#step-10-run-the-instance-pipeline-first-run---skip)
- [Step 11: Transfer credential values and provision the Store](#step-11-transfer-credential-values-and-provision-the-store)
- [Step 12: Run the Instance pipeline again (apply)](#step-12-run-the-instance-pipeline-again-apply)
- [Step 13: Verify the generated result](#step-13-verify-the-generated-result)
- [Step 14: Run a test deployment](#step-14-run-a-test-deployment)
- [Rollback](#rollback)
- [See also](#see-also)

## Description

Use this guide to move the credentials of an Instance repository from Git to a Secret Store. At the end, every
environment uses External Credentials, the secret values live in the store, and the repository holds only
references.

For a new environment, you do not need this migration, see
[Configure External Credentials](/docs/how-to/configure-external-credentials.md).

> [!WARNING]
> Do not remove `data` from a credential before you have saved its value. After the migration EnvGene no longer
> reads values from Git, and a credential with `create: true` and no secret gets a new value: the old password,
> token, or key is lost. Never put secret values in Git, merge requests, or notes.

### Credential value transfer

Values move into the Secret Store in two parts:

| When                                | What                                                   | Where                                                                  |
|-------------------------------------|--------------------------------------------------------|------------------------------------------------------------------------|
| Before Steps 4-6 remove `data`      | Save each real value to a secure place outside Git     | [Step 4](#step-4-convert-cloud-passport-credentials-and-main-file)     |
| After Step 10 generates the Context | Put the saved values into the store at EnvGene's paths | [Step 11](#step-11-transfer-credential-values-and-provision-the-store) |

### Rules

- After the migration, each environment uses only External Credentials. System Credentials are an exception: they
  may stay local. See [EnvGene System Credentials](/docs/features/external-creds.md#envgene-system-credentials).
- If the same `credId` is declared in several places, the Shared Credentials win over the Cloud Passport, and the
  Cloud Passport wins over the Credential Template.

## Prerequisites

- The Instance repository uses a No-CMDB [deployment architecture](/docs/deployment-architecture.md).
- EnvGene is upgraded to a version that supports External Credentials.
- The template is migrated and published as a new version, see
  [Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md).
- You can decrypt the credentials files of the repository, if credential encryption is enabled. See
  [Credential Encryption](/docs/how-to/credential-encryption.md).

## Step 1: Inventory the Instance Repository

List every local credential (`type: usernamePassword` or `type: secret`) in these files:

| File                                                       | What it holds                           |
|------------------------------------------------------------|-----------------------------------------|
| `environments/<cluster>/cloud-passport/*-creds.yml`        | Cloud Passport credentials              |
| `environments/<cluster>/<env>/Inventory/credentials/*.yml` | environment-level Shared Credentials    |
| `environments/<cluster>/credentials/*.yml`                 | cluster-level Shared Credentials        |
| `environments/credentials/*.yml`                           | repository-level Shared Credentials     |
| `configuration/credentials/credentials.yml`                | System Credentials: Git token, registry |
| `environments/<cluster>/app-deployer/deployer-creds.yml`   | System Credentials: deployer            |

Older repositories may keep Shared Credentials in deprecated folders such as `shared-credentials/`, see
[File resolution for shared entities](/docs/envgene-configs.md#file-resolution-for-shared-entities). Include files
that no `env_definition.yml` references.

Record each credential in a table:

| credId    | File                                                       | Value in `data`           |
|-----------|------------------------------------------------------------|---------------------------|
| dbaas     | `cluster-01/cloud-passport/passport-creds.yml`             | real value                |
| api-token | `cluster-01/env-01/Inventory/credentials/env-01-creds.yml` | stub (`envgeneNullValue`) |

A real value must be saved before Steps 4-6 remove it. A stub such as `envgeneNullValue` or an empty string has
nothing to save.

**Result:** a table of every local credential, its file, and whether it holds a real value.

## Step 2: Decide create and remoteRefPath

For each credential, decide two values.

### `create`

| Who creates the value                               | In the credential      |
|-----------------------------------------------------|------------------------|
| EnvGene may generate a new value                    | `create: true`         |
| The secret already exists, or a provider creates it | omit `create`          |
| You do not know                                     | stop and ask the owner |

A credential with a real value from Step 1 keeps that value: omit `create`, and put the value into the store in
Step 11. System Credentials never get `create: true`.

### `remoteRefPath`

| Source                       | `remoteRefPath`           |
|------------------------------|---------------------------|
| Cloud Passport               | `<cluster>`               |
| Environment-level Shared     | `<cluster>/<environment>` |
| Cluster or repository Shared | `external`                |
| System Credentials           | `external`                |

Do not append the `credId`: EnvGene adds it.

**Result:** a `create` value and a `remoteRefPath` for every credential.

## Step 3: Configure Secret Store

1. Create or update `/configuration/secret-stores.yml`:

    ```yaml
    default_store:
      type: vault
      mountPath: secret
    ```

    See [Secret Store](/docs/features/external-creds.md#secret-store) for the fields of each store type.

2. Set the authentication variables of the store as CI/CD variables of the Instance repository, see
   [Configure External Credentials, Step 4](/docs/how-to/configure-external-credentials.md#step-4-set-the-secret-store-authentication-variables).

## Step 4: Convert Cloud Passport Credentials and main file

> [!IMPORTANT]
> Save every real value from Step 1 before you remove its `data`. Decrypt the file first if it is encrypted.

1. In `environments/<cluster>/cloud-passport/*-creds.yml`, replace each credential with an external one, using the
   values from Step 2.

    Before:

    ```yaml
    dbaas:
      type: usernamePassword
      data:
        username: <username>
        password: <password>
    ```

    After:

    ```yaml
    dbaas:
      type: external
      secretStore: default_store
      remoteRefPath: cluster-01
      properties:
        - name: username
        - name: password
    ```

    For a single value (`type: secret`), leave out `properties`. For the rules of every field, see
    [Credential](/docs/features/external-creds.md#credential).

2. In the matching passport file, such as `passport.yml`, replace each credential macro with `$type: credRef`, as in
   [Migrate Template Repository to External Credentials, Step 5](/docs/how-to/migrate-template-repository-to-external-credentials.md#step-5-replace-macros).

Leave built-in fields such as `credentialsId` unchanged: they keep a plain `credId`.

**Result:** the Cloud Passports use External Credentials.

## Step 5: Convert Shared Credentials

> [!IMPORTANT]
> Save every real value from Step 1 before you remove its `data`.

1. Convert each Shared Credentials file from Step 1 the same way as in Step 4, with the values from Step 2:

    ```yaml
    ID_TOCP_CLIENT_CREDS:
      type: external
      secretStore: default_store
      remoteRefPath: external
      properties:
        - name: username
        - name: password
    ```

2. In each `env_definition.yml`, list the files in `envTemplate.sharedMasterCredentialFiles` without the `.yml`
   extension: `shared-credentials`, not `shared-credentials.yml`.

**Result:** the Shared Credentials use External Credentials.

## Step 6: Convert System Credentials (optional)

System Credentials are the Git token, the registry credentials, and the deployer credentials in
`configuration/credentials/credentials.yml` and `environments/<cluster>/app-deployer/deployer-creds.yml`. They may stay
local. Convert them only if you want these values in the Secret Store too.

1. Put their values into the Secret Store with the store's own tools. Step 11 does not cover System Credentials.
2. Convert the entries the same way as in Step 4, without `create`.
3. Replace the macros in `/configuration/deployer.yml` and `/configuration/integration.yml`:

    ```yaml
    # configuration/integration.yml
    self_token:
      $type: credRef
      credId: self-token-cred
    ```

    `credentialsId` fields in Artifact and Registry Definitions stay plain strings.

See [EnvGene System Credentials](/docs/features/external-creds.md#envgene-system-credentials).

**Result:** the System Credentials you chose are in the Secret Store.

## Step 7: Update environment-specific parameters

Replace the credential macros with `$type: credRef`, as in
[Migrate Template Repository to External Credentials, Step 5](/docs/how-to/migrate-template-repository-to-external-credentials.md#step-5-replace-macros), in:

- the environment-specific `deployParameters` and `e2eParameters`
- the ParameterSets in `environments/<cluster>/<env>/Inventory/parameters/`, `environments/<cluster>/parameters/`, and
  `environments/parameters/`

Do not use `$type: credRef` in `technicalConfigurationParameters`.

**Result:** the environment-specific parameters reference the credentials with `$type: credRef`.

## Step 8: Remove stale generated Credentials files

Delete `environments/<cluster>/<env>/Credentials/credentials.yml` of every environment you migrate. It was generated
from the old template, holds local credentials, and fails the next run with `Only external credentials allowed`. The
pipeline creates it again with external credentials only.

**Result:** no generated Credentials files from the old template.

## Step 9: Validate before the pipeline

Check that:

- every real value from Step 1 is saved outside the repository
- no converted credential has a `data` block
- every `secretStore` in the credentials is defined in `/configuration/secret-stores.yml`
- every `property` in a `$type: credRef` matches a name in the credential's `properties`
- `sharedMasterCredentialFiles` lists names without `.yml`

## Step 10: Run the Instance pipeline (first run - skip)

Start with a non-production environment:

```text
ENV_NAMES=<cluster-name>/<environment-name>
ENV_TEMPLATE_VERSION=<artifactId>:<version>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
EXTERNAL_CREDENTIAL_PROVISIONING=skip
CMDB_IMPORT=false
```

`EXTERNAL_CREDENTIAL_PROVISIONING=skip` generates the Environment Instance and the Effective Set without touching the
Secret Store, so the run does not fail while the values are not there yet. Do not deploy from this Effective Set.

**Result:** `environments/<cluster>/<env>/effective-set/external-credential/external-credentials.yaml` lists every
credential with its path in the store.

## Step 11: Transfer credential values and provision the Store

1. Open `environments/<cluster>/<env>/effective-set/external-credential/external-credentials.yaml`.
2. For each credential with `strategy: fail_if_absent`, create the secret in the store at the path in its `vals`
   field. Use the value you saved in Steps 4-5, or, for a value that came from Jenkins CMDB, the value from Jenkins.
3. Inside the secret, use the keys from `properties`, such as `username` and `password`. For a single-value
   credential in Vault or OpenBao, use the key `value`.

Take each path from `vals`, do not build it yourself: a secret at a slightly different path is reported as missing.
EnvGene creates the credentials with `strategy: create_if_absent` in Step 12.

**Result:** every secret without `create: true` is in the Secret Store.

## Step 12: Run the Instance pipeline again (apply)

Run the parameters from Step 10 without `EXTERNAL_CREDENTIAL_PROVISIONING`:

```text
ENV_NAMES=<cluster-name>/<environment-name>
ENV_TEMPLATE_VERSION=<artifactId>:<version>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

EnvGene checks that every secret exists and creates the ones with `create: true`.

**Result:** the Effective Set references real values in the Secret Store.

## Step 13: Verify the generated result

1. `environments/<cluster>/<env>/Credentials/credentials.yml` holds only `type: external` entries.
2. The files under `effective-set/deployment/` hold VALS or ESO references instead of values.

If a check fails, fix the configuration and run again from
[Step 10](#step-10-run-the-instance-pipeline-first-run---skip).

## Step 14: Run a test deployment

Deploy the environment and check that the applications start and authenticate to their dependencies. Then migrate
the remaining environments the same way, from Step 10.

## Rollback

1. Switch the environments back to the previous template version.
2. Revert the changes in the Instance repository.
3. Run the Instance pipeline with `ENV_BUILDER=true` and `GENERATE_EFFECTIVE_SET=true`.

Keep the secrets in the store until you are sure nothing uses them.

## See also

- [Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
- [Configure External Credentials](/docs/how-to/configure-external-credentials.md)
- [External Credentials](/docs/features/external-creds.md)
- [Sample External Credentials](/docs/samples/external-credentials/)
