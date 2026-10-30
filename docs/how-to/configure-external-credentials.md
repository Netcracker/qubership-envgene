# Configure External Credentials

- [Configure External Credentials](#configure-external-credentials)
  - [Overview](#overview)
  - [When to use External Credentials](#when-to-use-external-credentials)
  - [Prerequisites](#prerequisites)
  - [Layout](#layout)
  - [Steps](#steps)
    - [Step 1: Check the Environment Template](#step-1-check-the-environment-template)
    - [Step 2: Decide who creates each value](#step-2-decide-who-creates-each-value)
    - [Step 3: Describe the Secret Store](#step-3-describe-the-secret-store)
    - [Step 4: Set the Secret Store authentication variables](#step-4-set-the-secret-store-authentication-variables)
    - [Step 5: Write the Cloud Passport credentials as external](#step-5-write-the-cloud-passport-credentials-as-external)
    - [Step 6: Prepare the Shared Credentials](#step-6-prepare-the-shared-credentials)
    - [Step 7: Create the environment](#step-7-create-the-environment)
    - [Step 8: Put the values in the store and generate the Effective Set](#step-8-put-the-values-in-the-store-and-generate-the-effective-set)
    - [Step 9: Verify the result](#step-9-verify-the-result)
  - [Related documentation](#related-documentation)

## Overview

Create a new environment that uses External Credentials from the start. At the end, the secret values live in a
Secret Store, and the Instance repository and the deployment hold only references to them. Supported Secret Stores:
Vault, OpenBao, Azure Key Vault, AWS Secrets Manager, and GCP Secret Manager.

For the fields used below, see [External Credentials](/docs/features/external-creds.md). For a complete file set, see
the [external credentials samples](/docs/samples/external-credentials/).

## When to use External Credentials

These steps are for a new environment. If the environment or its Environment Template already uses local
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

### Step 1: Check the Environment Template

External Credentials need support in the Environment Template. Check that the template version you deploy has the
following. If it does not, ask the template owner to add it, see
[Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md).

1. A Credential Template that declares the credentials the template owns:

    ```yaml
    # templates/env_templates/<solution>/external-credentials.yml.j2
    app-db-cred:
      type: external
      create: true
      secretStore: default_store
      remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
      properties:
        - name: username
        - name: password
    ```

2. The Template Descriptor points to it:

    ```yaml
    external_credential_template: "{{ templates_dir }}/env_templates/<solution>/external-credentials.yml.j2"
    ```

3. Sensitive parameters in `deployParameters`, `e2eParameters`, and their ParameterSets use `$type: credRef`
   instead of `${creds.get(...)}`:

    ```yaml
    DB_USER:
      $type: credRef
      credId: app-db-cred
      property: username
    ```

   Built-in fields such as `credentialsId` keep a plain `credId`.

Write down every `credId` the template references and does not declare in its Credential Template. You declare
them in the Cloud Passport (Step 5) or in the Shared Credentials (Step 6).

### Step 2: Decide who creates each value

The Credential Template of the Environment Template sets `create` for its own credentials. Set it for the Cloud
Passport credentials and the Shared Credentials:

| Who creates the value                              | `create`       | If the secret is missing, EnvGene |
|----------------------------------------------------|----------------|-----------------------------------|
| EnvGene may generate a new value                   | `create: true` | creates it                        |
| You, or an external provider, before the first run | omit the field | fails the run                     |

### Step 3: Describe the Secret Store

Create `/configuration/secret-stores.yml` in the Instance repository:

```yaml
# configuration/secret-stores.yml
default_store:
  type: vault
  mountPath: secret
```

Each store type needs its own fields: `mountPath` for `vault` and `openbao`, `vaultName` for `azure`, `region` for
`aws`, `projectId` for `gcp`. See [Secret Store](/docs/features/external-creds.md#secret-store).

### Step 4: Set the Secret Store authentication variables

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

### Step 5: Write the Cloud Passport credentials as external

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

### Step 6: Prepare the Shared Credentials

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
| `create`        | `true` or omitted, from Step 2                                                                    |
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
[Step 8](#step-8-put-the-values-in-the-store-and-generate-the-effective-set).

The file can live at the environment, cluster, or repository level, see
[Choose the level of each file](/docs/how-to/create-environment-inventory.md#choose-the-level-of-each-file).

### Step 7: Create the environment

Create the environment and add the Shared Credentials to it in the same run. For the content of
`env_definition.yml`, see [Create an Environment Inventory](/docs/how-to/create-environment-inventory.md). Do it in
one of two ways:

- **Through the Instance pipeline:** put `env_definition.yml` in the `envDefinition` block of
  `ENV_INVENTORY_CONTENT`, the Shared Credentials file from Step 6 in the `credentials` block, and its name in
  `envTemplate.sharedMasterCredentialFiles`. Pass the content in Step 8:

    ```json
    {
      "envDefinition": {
        "action": "create_or_replace",
        "content": {
          "inventory": {},
          "envTemplate": {
            "name": "<template-name>",
            "artifact": "<template-artifact>:<version>",
            "sharedMasterCredentialFiles": ["env-01-creds"]
          }
        }
      },
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
    }
    ```

- **By hand:** commit `env_definition.yml` and the file from Step 6. List the file name, without `.yml`, in
  `env_definition.yml`:

    ```yaml
    # environments/cluster-01/env-01/Inventory/env_definition.yml
    inventory: {}
    envTemplate:
      name: "<template-name>"
      artifact: "<template-artifact>:<version>"
      sharedMasterCredentialFiles:
        - env-01-creds
    ```

### Step 8: Put the values in the store and generate the Effective Set

Every credential without `create: true`, from the Credential Template, the Cloud Passport, and the Shared Credentials,
must exist in the Secret Store at its path from the Effective Set. Choose one way:

- **The values are already in the store.** Run the Instance pipeline:

    ```yaml
    ENV_NAMES: cluster-01/env-01
    ENV_INVENTORY_CONTENT: <JSON from Step 7>          # only if you create the environment through the pipeline
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

### Step 9: Verify the result

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
