# Configure External Credentials

- [Configure External Credentials](#configure-external-credentials)
  - [Overview](#overview)
  - [When to use External Credentials](#when-to-use-external-credentials)
  - [Prerequisites](#prerequisites)
  - [Part 1: Template repository](#part-1-template-repository)
    - [Step 1: List the credentials of the template](#step-1-list-the-credentials-of-the-template)
    - [Step 2: Choose the fields of each credential](#step-2-choose-the-fields-of-each-credential)
    - [Step 3: Create the Credential Template](#step-3-create-the-credential-template)
    - [Step 4: Point the Template Descriptor at it](#step-4-point-the-template-descriptor-at-it)
    - [Step 5: Reference the credentials in parameters](#step-5-reference-the-credentials-in-parameters)
    - [Step 6: Publish the template](#step-6-publish-the-template)
  - [Part 2: Instance repository](#part-2-instance-repository)
    - [Step 7: Describe the Secret Store](#step-7-describe-the-secret-store)
    - [Step 8: Set the Secret Store authentication variables](#step-8-set-the-secret-store-authentication-variables)
    - [Step 9: Write the Cloud Passport credentials](#step-9-write-the-cloud-passport-credentials)
    - [Step 10: Write the Shared Credentials](#step-10-write-the-shared-credentials)
    - [Step 11: Put the values in the store and generate the Effective Set](#step-11-put-the-values-in-the-store-and-generate-the-effective-set)
    - [Step 12: Verify the result](#step-12-verify-the-result)
  - [Related documentation](#related-documentation)

## Overview

Create a new environment that keeps its credentials in a Secret Store from the start. At the end, the secret values
live in the store, and the Instance repository and the deployment hold only references to them. Supported Secret
Stores: Vault, OpenBao, Azure Key Vault, AWS Secrets Manager, and GCP Secret Manager.

For every field used below, see [External Credentials](/docs/features/external-creds.md). For a complete file set,
see the [external credentials samples](/docs/samples/external-credentials/).

## When to use External Credentials

These steps are for a new environment. If the environment or its Environment Template already uses local
credentials, migrate them instead, see
[Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
and
[Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

> [!IMPORTANT]
> An environment uses either local or External Credentials, never both. The Credential Template, the Cloud Passport,
> and the Shared Credentials must all be external.

## Prerequisites

- The environment uses a No-CMDB [deployment architecture](/docs/deployment-architecture.md). CMDB import is not
  supported for External Credentials.
- The environment exists, see [Create an Environment Inventory](/docs/how-to/create-environment-inventory.md).
- The Secret Store is installed and reachable from the Instance pipeline. EnvGene does not install or operate it.
- You know the identifier of the Secret Store in the Instance repository. With one store, it is `default_store`.
- You can set CI/CD variables of the Instance repository.

## Part 1: Template repository

### Step 1: List the credentials of the template

Open the Cloud, Namespace, Tenant, and ParameterSet templates and find every credential the parameters use. For
each `credId`, note what the secret holds:

- a username and a password, when the parameters read both
- one value, such as a token or a key

### Step 2: Choose the fields of each credential

Every external credential has the same fields. Choose each value as follows:

| Field           | How to choose the value                                                                                                   |
|-----------------|---------------------------------------------------------------------------------------------------------------------------|
| `type`          | Always `external`. An external credential has no `data` block                                                              |
| `secretStore`   | The identifier of the Secret Store in the Instance repository. With one store, `default_store`                             |
| `remoteRefPath` | The folder in the store. In the Credential Template, use `{{ current_env.cloud }}/{{ current_env.name }}`. In the Instance repository, use `<cluster>` for Cloud Passport credentials and `<cluster>/<env>` for the others. Do not add the `credId`: EnvGene appends it |
| `create`        | `true` if EnvGene may generate the value, such as an internal password nobody else uses. Leave it out if the value comes from outside, such as a token from a partner. Then you put it in the store yourself in Step 11 |
| `properties`    | For a username and a password, list `- name: username` and `- name: password`. For one value, leave it out                 |

Example: a database user that EnvGene may generate, and a token issued by a partner:

```yaml
app-db-cred:                # username and password, EnvGene may generate
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
  properties:
    - name: username
    - name: password
partner-api-token:          # one value, comes from the partner
  type: external
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
```

EnvGene stores each credential under `remoteRefPath` plus the `credId`, for example
`cluster-01/env-01/partner-api-token`. Azure and GCP replace `/` with `--`, and Azure, AWS, and GCP shorten long
names. The exact path is in the Effective Set, see Step 11.

### Step 3: Create the Credential Template

Create `templates/env_templates/<solution>/external-credentials.yml.j2` next to the Cloud, Namespace, and Tenant
templates. Add one entry per credential from Step 1, with the fields from Step 2.

### Step 4: Point the Template Descriptor at it

Add `external_credential_template` to the Template Descriptor:

```yaml
tenant: "{{ templates_dir }}/env_templates/<solution>/tenant.yml.j2"
cloud: "{{ templates_dir }}/env_templates/<solution>/cloud.yml.j2"
external_credential_template: "{{ templates_dir }}/env_templates/<solution>/external-credentials.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/<solution>/ns.yml.j2"
```

### Step 5: Reference the credentials in parameters

In `deployParameters`, `e2eParameters`, and their ParameterSets, reference each credential with `$type: credRef`.
For a username and a password, `property` picks the field. For one value, leave `property` out:

```yaml
DB_USER:
  $type: credRef
  credId: app-db-cred
  property: username
DB_PASSWORD:
  $type: credRef
  credId: app-db-cred
  property: password
PARTNER_API_TOKEN:
  $type: credRef
  credId: partner-api-token
```

Built-in fields such as `credentialsId` keep a plain `credId`. `$type: credRef` does not work in
`technicalConfigurationParameters`.

### Step 6: Publish the template

Run the template build pipeline and publish a new version, for example `project-env-template:2.0.0`. Use this version
in `envTemplate.artifact` in Step 10.

## Part 2: Instance repository

### Step 7: Describe the Secret Store

Create `/configuration/secret-stores.yml` in the Instance repository:

```yaml
# configuration/secret-stores.yml
default_store:
  type: vault
  mountPath: secret
```

The key, `default_store` here, is the store identifier that the credentials use in `secretStore`. Each store type
needs its own fields: `mountPath` for `vault` and `openbao`, `vaultName` for `azure`, `region` for `aws`, `projectId`
for `gcp`. See [Secret Store](/docs/features/external-creds.md#secret-store).

### Step 8: Set the Secret Store authentication variables

Add the variables of your store type as masked CI/CD variables of the Instance repository:

| Store type          | `type`    | CI/CD variables                                                                                                                  |
|---------------------|-----------|----------------------------------------------------------------------------------------------------------------------------------|
| Vault               | `vault`   | `VAULT_ADDR`, `VAULT_TOKEN`                                                                                                      |
| OpenBao             | `openbao` | `VAULT_ADDR`, `VAULT_TOKEN`                                                                                                      |
| Azure Key Vault     | `azure`   | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`                                                                      |
| AWS Secrets Manager | `aws`     | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`                                                                                     |
| GCP Secret Manager  | `gcp`     | `GOOGLE_APPLICATION_CREDENTIALS` (path to the key file) or `GOOGLE_APPLICATION_CREDENTIALS_CONTENT` (key JSON, takes precedence) |

For a store other than `default_store`, prefix each variable with the store identifier and `_`. For a store
`backup_store` of type `vault`, the variables are `backup_store_VAULT_ADDR` and `backup_store_VAULT_TOKEN`.

Never commit these values to Git.

### Step 9: Write the Cloud Passport credentials

1. Add the credentials of the cluster to the passport credentials file, with the fields from Step 2:

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

2. In the passport, reference them with `$type: credRef`:

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

3. Commit both files.

For the rest of the passport, see [Create a cluster](/docs/how-to/create-cluster.md).

### Step 10: Write the Shared Credentials

Write your credentials to the Shared Credentials file of the environment in this format:

```yaml
# environments/cluster-01/env-01/Inventory/credentials/env-01-creds.yml
integration-cred:
  type: external
  secretStore: default_store
  remoteRefPath: cluster-01/env-01
  properties:
    - name: username
    - name: password
```

List the file in `env_definition.yml`, without `.yml`, and set the template version from Step 6:

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
envTemplate:
  artifact: "project-env-template:2.0.0"
  sharedMasterCredentialFiles:
    - env-01-creds
```

### Step 11: Put the values in the store and generate the Effective Set

1. Run the Instance pipeline:

    ```yaml
    ENV_NAMES: cluster-01/env-01
    ENV_BUILDER: true
    GENERATE_EFFECTIVE_SET: true
    EXTERNAL_CREDENTIAL_PROVISIONING: skip
    ```

2. In `environments/cluster-01/env-01/effective-set/external-credential/external-credentials.yaml`, find the
   credentials with `strategy: fail_if_absent`. Create each of them in the store at the path from its `vals` field:

    ```yaml
    credentials:
      integration-cred:
        vals: "ref+vault://secret/cluster-01/env-01/integration-cred"
        strategy: fail_if_absent      # create it in the store
      app-db-cred:
        vals: "ref+vault://secret/cluster-01/env-01/app-db-cred"
        strategy: create_if_absent    # EnvGene creates it
    ```

    Inside the secret, use the keys from `properties`, such as `username` and `password`. For one value in Vault or
    OpenBao, use the key `value`.

    Take the path only from `vals`. A secret at a slightly different path is reported as missing.

3. Run the pipeline again without `EXTERNAL_CREDENTIAL_PROVISIONING`. EnvGene creates the secrets with
   `create: true`.

### Step 12: Verify the result

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
