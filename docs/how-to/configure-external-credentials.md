# Configure External Credentials

- [Configure External Credentials](#configure-external-credentials)
  - [Overview](#overview)
  - [When to use this guide](#when-to-use-this-guide)
  - [Prerequisites](#prerequisites)
  - [Layout](#layout)
  - [Steps](#steps)
    - [Step 1: Decide who creates each value](#step-1-decide-who-creates-each-value)
    - [Step 2: Describe the Secret Store](#step-2-describe-the-secret-store)
    - [Step 3: Set the Secret Store authentication variables](#step-3-set-the-secret-store-authentication-variables)
    - [Step 4: Write the Cloud Passport credentials as external](#step-4-write-the-cloud-passport-credentials-as-external)
    - [Step 5: Prepare the Shared Credentials](#step-5-prepare-the-shared-credentials)
    - [Step 6: Add the Shared Credentials to the environment](#step-6-add-the-shared-credentials-to-the-environment)
    - [Step 7: Put the values in the store and generate the Effective Set](#step-7-put-the-values-in-the-store-and-generate-the-effective-set)
    - [Step 8: Verify the result](#step-8-verify-the-result)
  - [Related documentation](#related-documentation)

## Overview

Use this guide to create a new environment that uses External Credentials from the start. At the end, the secret values live
in a Secret Store, and the Instance repository and the deployment hold only references to them. Supported Secret
Stores: Vault, OpenBao, Azure Key Vault, AWS Secrets Manager, and GCP Secret Manager.

For the fields used below, see [External Credentials](/docs/features/external-creds.md). For a complete file set, see
the [external credentials samples](/docs/samples/external-credentials/).

## When to use this guide

Use this guide for a new environment. If the environment or its Environment Template already uses local
credentials, migrate them instead:
[Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
and
[Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

> [!IMPORTANT]
> An environment uses either local or External Credentials, never both. The Credential Template, the Cloud Passport,
> and the Shared Credentials must all be external.

## Prerequisites

- The environment uses a No-CMDB [deployment architecture](/docs/deployment-architecture.md). CMDB import is not
  supported for External Credentials.
- The Environment Template supports External Credentials: its Template Descriptor sets
  `external_credential_template`, and its sensitive parameters use `$type: credRef`. The template owner prepares
  this, see [Credential Template](/docs/envgene-objects.md#credential-template).
- The Secret Store is installed and reachable from the Instance pipeline. EnvGene does not install or operate it.
- You can set CI/CD variables of the Instance repository.

## Layout

```text
configuration/
└── secret-stores.yml                     ← Secret Store
environments/
└── cluster-01/
    ├── cloud-passport/
    │   ├── passport.yml                  ← parameters with $type: credRef
    │   └── passport-creds.yml            ← type: external
    └── env-01/
        └── Inventory/
            ├── env_definition.yml
            └── credentials/
                └── env-01-creds.yml      ← Shared Credentials, type: external
```

## Steps

### Step 1: Decide who creates each value

The Environment Template already decides this for the credentials it owns, in its Credential Template. Decide it for
the Cloud Passport credentials and the Shared Credentials. The answer sets the `create` field:

| Who creates the value                              | `create`       | If the secret is missing, EnvGene |
|----------------------------------------------------|----------------|-----------------------------------|
| EnvGene may generate a new value                   | `create: true` | creates it                        |
| You, or an external provider, before the first run | omit the field | fails the run                     |

### Step 2: Describe the Secret Store

Create `/configuration/secret-stores.yml` in the Instance repository:

```yaml
# configuration/secret-stores.yml
default_store:
  type: vault
  mountPath: secret
```

Each store type needs its own fields: `mountPath` for `vault` and `openbao`, `vaultName` for `azure`, `region` for
`aws`, `projectId` for `gcp`. See [Secret Store](/docs/features/external-creds.md#secret-store).

### Step 3: Set the Secret Store authentication variables

Add the variables of your store type as masked CI/CD variables of the Instance repository:

| Store type          | `type`    | CI/CD variables                                                                                                                  |
|---------------------|-----------|----------------------------------------------------------------------------------------------------------------------------------|
| Vault               | `vault`   | `VAULT_ADDR`, `VAULT_TOKEN`                                                                                                      |
| OpenBao             | `openbao` | `VAULT_ADDR`, `VAULT_TOKEN`                                                                                                      |
| Azure Key Vault     | `azure`   | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`                                                                      |
| AWS Secrets Manager | `aws`     | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`                                                                                     |
| GCP Secret Manager  | `gcp`     | `GOOGLE_APPLICATION_CREDENTIALS` (path to the key file) or `GOOGLE_APPLICATION_CREDENTIALS_CONTENT` (key JSON, takes precedence) |

For a store other than `default_store`, prefix each variable with the store identifier from `secret-stores.yml` and
`_`. For a store `backup_store` of type `vault`, the variables are `backup_store_VAULT_ADDR` and
`backup_store_VAULT_TOKEN`.

Never commit these values to Git.

### Step 4: Write the Cloud Passport credentials as external

1. In the passport credentials file, declare every credential as `type: external`:

    ```yaml
    # environments/cluster-01/cloud-passport/passport-creds.yml
    cloud-deploy-sa-token:
      type: external
      secretStore: default_store
      remoteRefPath: cluster-01
    dbaas-cred:
      type: external
      secretStore: default_store
      remoteRefPath: cluster-01
      properties:
        - name: username
        - name: password
    ```

2. In the passport, point the sensitive parameters at them with `$type: credRef`:

    ```yaml
    # environments/cluster-01/cloud-passport/passport.yml
    dbaas:
      DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
        $type: credRef
        credId: dbaas-cred
        property: username
      DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
        $type: credRef
        credId: dbaas-cred
        property: password
    ```

3. Commit the changes to the Instance repository.

For the rest of the passport, see [Create a cluster](/docs/how-to/create-cluster.md).

### Step 5: Prepare the Shared Credentials

Shared Credentials hold the credentials an environment needs beyond the Credential Template and the Cloud Passport,
for example the credentials of an integration. Skip this step if there are none.

Write each Shared Credential in this structure:

```yaml
# environments/cluster-01/env-01/Inventory/credentials/env-01-creds.yml
integration-cred:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: cluster-01/env-01
  properties:
    - name: username
    - name: password
api-token:
  type: external
  secretStore: default_store
  remoteRefPath: cluster-01/env-01
```

| Field           | Value                                                                                             |
|-----------------|---------------------------------------------------------------------------------------------------|
| `type`          | Always `external`. No `data` block                                                                |
| `create`        | `true` or omitted, from Step 1                                                                    |
| `secretStore`   | A store identifier from `secret-stores.yml`. Defaults to `default_store`                          |
| `remoteRefPath` | Path prefix in the store. EnvGene appends the `credId` to it                                      |
| `properties`    | `- name: username` and `- name: password` for a username and password. Omit it for a single value |

EnvGene stores each credential in the Secret Store under `remoteRefPath` plus the `credId`. For `integration-cred`
above, the secret name is:

| Store type         | Secret name in the store                                         |
|--------------------|------------------------------------------------------------------|
| `vault`, `openbao` | `cluster-01/env-01/integration-cred`, under the `mountPath`      |
| `aws`              | `cluster-01/env-01/integration-cred`                             |
| `azure`, `gcp`     | `cluster-01--env-01--integration-cred`: these stores have no `/` |

Azure, AWS, and GCP shorten long names, so treat this table as a guide. The exact path is in the Effective Set, see
[Step 7](#step-7-put-the-values-in-the-store-and-generate-the-effective-set).

The file can live at the environment, cluster, or repository level, see
[Choose the level of each file](/docs/how-to/create-environment-inventory.md#choose-the-level-of-each-file).

### Step 6: Add the Shared Credentials to the environment

Do it in one of two ways, together with creating the environment, see
[Create an Environment Inventory](/docs/how-to/create-environment-inventory.md).

- **Through the Instance pipeline:** put the file content in the `credentials` block of `ENV_INVENTORY_CONTENT`, and
  the filename in `envTemplate.sharedMasterCredentialFiles` of the same content. Pass the content in Step 7:

    ```json
    "credentials": [
      {
        "action": "create_or_replace",
        "place": "env",
        "name": "env-01-creds",
        "content": {
          "integration-cred": {
            "type": "external",
            "create": true,
            "secretStore": "default_store",
            "remoteRefPath": "cluster-01/env-01",
            "properties": [{ "name": "username" }, { "name": "password" }]
          },
          "api-token": {
            "type": "external",
            "secretStore": "default_store",
            "remoteRefPath": "cluster-01/env-01"
          }
        }
      }
    ]
    ```

- **By hand:** commit the file from Step 5 and add its name, without `.yml`, to `env_definition.yml`:

    ```yaml
    # environments/cluster-01/env-01/Inventory/env_definition.yml
    envTemplate:
      sharedMasterCredentialFiles:
        - env-01-creds
    ```

### Step 7: Put the values in the store and generate the Effective Set

Every credential without `create: true`, from the Credential Template, the Cloud Passport, and the Shared Credentials,
must exist in the Secret Store at its path from the Effective Set. Choose one way:

- **The values are already in the store.** Run the Instance pipeline:

    ```yaml
    ENV_NAMES: cluster-01/env-01
    ENV_INVENTORY_CONTENT: <JSON from Step 6>          # only if you add the credentials through the pipeline
    ENV_TEMPLATE_VERSION: project-env-template:2.0.0   # the version with the Credential Template
    ENV_BUILDER: true
    GENERATE_EFFECTIVE_SET: true
    ```

- **The values are not in the store yet.**
    1. Run the same parameters with `EXTERNAL_CREDENTIAL_PROVISIONING: skip`. The run generates the Effective Set
       without touching the store.
    2. Create the secrets in the store at the paths from the Effective Set, see below.
    3. Run again without `EXTERNAL_CREDENTIAL_PROVISIONING`.

> [!IMPORTANT]
> When you create secrets by hand, take each path from the Effective Set, not from your own calculation. A secret at a
> slightly different path is reported as missing.
>
> The paths are in `environments/cluster-01/env-01/effective-set/external-credential/external-credentials.yaml`,
> one `vals` field per credential:
>
> ```yaml
> credentials:
>   integration-cred:
>     vals: "ref+vault://secret/cluster-01/env-01/integration-cred"
>     strategy: create_if_absent    # EnvGene creates it
>   api-token:
>     vals: "ref+vault://secret/cluster-01/env-01/api-token"
>     strategy: fail_if_absent      # create it by hand before the run
> ```
>
> For Vault and OpenBao, `ref+vault://secret/cluster-01/env-01/api-token` means the secret
> `cluster-01/env-01/api-token` under the mount `secret`. Inside the secret, use the keys from `properties`, such as
> `username` and `password`. For a single-value credential in Vault or OpenBao, use the key `value`.

### Step 8: Verify the result

1. `environments/cluster-01/env-01/Credentials/credentials.yml` holds only `type: external` entries: from the
   Credential Template, the passport, and `env-01-creds`.
2. `environments/cluster-01/env-01/effective-set/external-credential/external-credentials.yaml` lists the same
   credentials.
3. The secrets with `create: true` exist in the Secret Store.
4. A test deployment starts, and the applications authenticate to their dependencies.

## Related documentation

- [Configure Local Credentials](/docs/how-to/configure-local-credentials.md)
- [External Credentials](/docs/features/external-creds.md)
- [Create an Environment Inventory](/docs/how-to/create-environment-inventory.md)
- [Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
- [Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
