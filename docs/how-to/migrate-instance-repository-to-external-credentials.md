# Migrate an instance repository to external Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1: Convert the credentials files of the environment](#step-1-convert-the-credentials-files-of-the-environment)
- [Step 2: Replace the credential macros of the environment](#step-2-replace-the-credential-macros-of-the-environment)
- [Step 3: Convert the System Credentials](#step-3-convert-the-system-credentials)
- [Step 4: Build the environment without provisioning](#step-4-build-the-environment-without-provisioning)
- [Step 5: Set the values in the Secret Store](#step-5-set-the-values-in-the-secret-store)
- [Step 6: Run the Instance pipeline with provisioning](#step-6-run-the-instance-pipeline-with-provisioning)
- [Verify the result](#verify-the-result)
- [Rollback](#rollback)
- [See also](#see-also)

## Description

Move the credentials of an Instance repository from Git to a Secret Store. After the migration, every environment and
the System Credentials use external Credentials, the values are stored in the Secret Store, and the repository holds
only references to them.

A new environment does not need this migration, see
[Configure external Credentials](/docs/how-to/configure-external-credentials.md).

> [!WARNING]
> Save every real value before you replace its credential. After the migration, EnvGene no longer reads values from
> Git. Never put secret values in Git, merge requests, or notes.

## Prerequisites

- The Instance repository uses a No-CMDB [deployment architecture](/docs/deployment-architecture.md).
- The template is migrated and published as a new version, see
  [Migrate a template repository to external Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md).
- The Instance repository has a Secret Store configured, see
  [Configure a Secret Store](/docs/how-to/configure-secret-store.md).
- You have the [External Credentials provisioning CLI](/modules/external-cred-provision/README.md) installed and access
  to the Secret Store from your machine.
- If credential encryption is enabled, you can decrypt the credentials files of the repository, see
  [Credential Encryption](/docs/how-to/credential-encryption.md).

## Step 1: Convert the credentials files of the environment

Open the credentials files that the environment uses:

- the Cloud Passport credentials file of the cluster, `environments/<cluster>/cloud-passport/*-creds.yml`
- the Shared Credentials files listed in `envTemplate.sharedMasterCredentialFiles` of `env_definition.yml`

In each file, save the real value of each credential outside Git, then replace the credential with an external one.
A credential that holds `envgeneNullValue` or an empty value has nothing to save.

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

Set the fields of each credential:

| Field           | Value                                                                                               |
|-----------------|-----------------------------------------------------------------------------------------------------|
| `type`          | Always `external`                                                                                   |
| `secretStore`   | The identifier of the Secret Store from `secret-stores.yml`                                         |
| `remoteRefPath` | The folder of the secret in the store, see the table below                                          |
| `create`        | Omit it for a credential whose value you saved. Set it to `true` if EnvGene must generate the value |
| `properties`    | `- name: username` and `- name: password` for `type: usernamePassword`. Omit it for `type: secret`  |

Set `remoteRefPath` according to the file that holds the credential:

| File                                  | Location                                              | `remoteRefPath`   |
|---------------------------------------|-------------------------------------------------------|-------------------|
| Cloud Passport credentials            | `environments/<cluster>/cloud-passport/`              | `<cluster>`       |
| Shared Credentials of the environment | `environments/<cluster>/<env>/Inventory/credentials/` | `<cluster>/<env>` |
| Shared Credentials of the cluster     | `environments/<cluster>/credentials/`                 | `external`        |
| Shared Credentials of the repository  | `environments/credentials/`                           | `external`        |

EnvGene stores the secret at `<remoteRefPath>/<credId>`, for example `cluster-01/dbaas`, so do not include the
`credId` in `remoteRefPath`. For the rules of every field, see [Credential](/docs/features/external-creds.md#credential).

Also save the real values from `environments/<cluster>/<env>/Credentials/credentials.yml`. Do not convert this file:
EnvGene regenerates it on the next run.

## Step 2: Replace the credential macros of the environment

Replace the credential macros with `$type: credRef`, as in
[Migrate a template repository to external Credentials, Step 3](/docs/how-to/migrate-template-repository-to-external-credentials.md#step-3-replace-the-credential-macros),
in:

- the Cloud Passport of the cluster, such as `environments/<cluster>/cloud-passport/passport.yml`
- the environment-specific `deployParameters` and `e2eParameters`
- the ParameterSets in `environments/<cluster>/<env>/Inventory/parameters/`, `environments/<cluster>/parameters/`, and
  `environments/parameters/`

Leave built-in fields such as `credentialsId` unchanged: they keep a plain `credId`.

## Step 3: Convert the System Credentials

Perform this step once per Instance repository. System Credentials are the Git token, the registry credentials, and
the deployer credentials in `configuration/credentials/credentials.yml` and in `deployer-creds.yml` next to each
`deployer.yml`.

1. Save the real values outside Git and replace the credentials as in Step 1, with `remoteRefPath: external` and
   without `create`.
2. Replace the macros in `/configuration/deployer.yml` and `/configuration/integration.yml`:

    ```yaml
    # configuration/integration.yml
    self_token:
      $type: credRef
      credId: self-token-cred
    ```

    `credentialsId` fields in Artifact and Registry Definitions stay plain strings.

3. EnvGene does not add System Credentials to the External Credential Context. Outside the repository, create a
   context file for the [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
   with one entry per System Credential:

    ```yaml
    credentials:
      self-token-cred:
        vals: "ref+vault://secret/external/self-token-cred"
        strategy: create_if_absent
        data:
          value: <token>
    ```

    For Vault and OpenBao, `vals` is `ref+<type>://<mountPath>/<remoteRefPath>/<credId>`. For the other store types
    and for the shape of `data`, see [Input format](/docs/features/external-creds-provisioning-cli.md#input-format).

4. Set the variables from
   [Configure a Secret Store](/docs/how-to/configure-secret-store.md#step-2-give-the-instance-pipeline-access-to-the-secret-store)
   in your shell, and run the CLI:

    ```bash
    external-cred-provision system-credentials.yaml
    ```

5. Delete the file: it contains the values in plain text.

See [EnvGene System Credentials](/docs/features/external-creds.md#envgene-system-credentials).

## Step 4: Build the environment without provisioning

Start with a non-production environment. Run the Instance pipeline with the template version that you published
during the template migration:

```text
ENV_NAMES=<cluster-name>/<environment-name>
ENV_TEMPLATE_VERSION=<artifactId>:<version>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
EXTERNAL_CREDENTIAL_PROVISIONING=skip
```

With `EXTERNAL_CREDENTIAL_PROVISIONING=skip`, EnvGene generates the Effective Set without checking the Secret Store,
so the run does not fail while the store does not contain the values yet. Do not deploy from this Effective Set.

## Step 5: Set the values in the Secret Store

EnvGene creates the secrets with `create: true` in Step 6. Set the values of the other credentials with the
[External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md):

1. Copy `environments/<cluster>/<env>/effective-set/external-credential/external-credentials.yaml` outside the
   repository. In the copy, for each credential with `strategy: fail_if_absent`, set `strategy: create_if_absent` and
   add `data` with the saved value:

    ```yaml
    credentials:
      dbaas:
        vals: "ref+vault://secret/cluster-01/dbaas"
        strategy: create_if_absent
        data:
          username: <username>
          password: <password>
    ```

    Do not change `vals`: it holds the path of the secret in the store. For the shape of `data` for one value, see
    [Input format](/docs/features/external-creds-provisioning-cli.md#input-format).

2. Set the variables from
   [Configure a Secret Store](/docs/how-to/configure-secret-store.md#step-2-give-the-instance-pipeline-access-to-the-secret-store)
   in your shell, and run the CLI:

    ```bash
    external-cred-provision external-credentials.yaml
    ```

3. Delete the copy: it contains the values in plain text.

## Step 6: Run the Instance pipeline with provisioning

Run the Instance pipeline with the parameters from Step 4, without `EXTERNAL_CREDENTIAL_PROVISIONING`. EnvGene checks
that every secret exists in the store and creates the secrets with `create: true`.

## Verify the result

1. `environments/<cluster>/<env>/Credentials/credentials.yml` holds only `type: external` entries.
2. The files under `effective-set/deployment/` of the environment hold VALS or ESO references instead of values.
3. A test deployment of the environment starts, and the applications authenticate to their dependencies.

If a check fails, fix the configuration and repeat from
[Step 4](#step-4-build-the-environment-without-provisioning).

For each remaining environment, repeat Steps 1, 2, 4, 5, and 6. Skip the files that you have already converted.

## Rollback

1. Switch the environments back to the previous template version.
2. Revert the changes in the Instance repository.
3. Run the Instance pipeline with `ENV_BUILDER=true` and `GENERATE_EFFECTIVE_SET=true`.

Keep the secrets in the store until you are sure that nothing uses them.

## See also

- [Migrate a template repository to external Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
- [Configure external Credentials](/docs/how-to/configure-external-credentials.md)
- [External Credentials](/docs/features/external-creds.md)
- [Sample External Credentials](/docs/samples/external-credentials/)
