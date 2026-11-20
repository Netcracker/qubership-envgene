# Configure a Secret Store

- [Configure a Secret Store](#configure-a-secret-store)
  - [Overview](#overview)
  - [Prerequisites](#prerequisites)
  - [Step 1: Describe the Secret Store](#step-1-describe-the-secret-store)
  - [Step 2: Give the Instance pipeline access to the Secret Store](#step-2-give-the-instance-pipeline-access-to-the-secret-store)
  - [Next steps](#next-steps)
  - [Related documentation](#related-documentation)

## Overview

Describe the Secret Store in the Instance repository and give the Instance pipeline access to it. After that,
environments can use external Credentials: EnvGene builds the references to the secrets from the store description,
and the Instance pipeline checks the secrets and creates the ones with `create: true`.

Supported Secret Stores: Vault, OpenBao, Azure Key Vault, AWS Secrets Manager, and GCP Secret Manager.

> [!IMPORTANT]
> `/configuration/secret-stores.yml` switches the whole Instance repository to external mode. Every environment of the
> repository then uses external Credentials. Without this file, the repository uses local Credentials.

## Prerequisites

- The Secret Store is installed and reachable from the Instance pipeline. EnvGene does not install or operate it.

## Step 1: Describe the Secret Store

Create `/configuration/secret-stores.yml` in the Instance repository:

```yaml
# configuration/secret-stores.yml
default_store:
  type: vault
  mountPath: secret
```

`default_store` is the identifier of the store. A Credential refers to the store by this identifier in its
`secretStore` field.

Set the field that your store type needs:

| `type`             | Field       | Value                            |
|--------------------|-------------|----------------------------------|
| `vault`, `openbao` | `mountPath` | Mount path of the secrets engine |
| `azure`            | `vaultName` | Name of the key vault            |
| `aws`              | `region`    | AWS region of Secrets Manager    |
| `gcp`              | `projectId` | ID of the GCP project            |

For all fields, see [Secret Store](/docs/features/external-creds.md#secret-store).

To use several stores, add one entry per store. An identifier other than `default_store` becomes part of the variable
names in Step 2, so use only letters, digits, and `_`.

## Step 2: Give the Instance pipeline access to the Secret Store

Add the variables of your store type as masked CI/CD variables of the Instance repository:

| Store type          | `type`    | Variables                                                                                                      |
|---------------------|-----------|----------------------------------------------------------------------------------------------------------------|
| Vault               | `vault`   | `VAULT_ADDR`, `VAULT_TOKEN`                                                                                    |
| OpenBao             | `openbao` | `BAO_ADDR`, `BAO_TOKEN`                                                                                        |
| Azure Key Vault     | `azure`   | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`                                                    |
| AWS Secrets Manager | `aws`     | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`                                             |
| GCP Secret Manager  | `gcp`     | `GOOGLE_APPLICATION_CREDENTIALS_CONTENT` (key JSON) or `GOOGLE_APPLICATION_CREDENTIALS` (path to the key file) |

For a store other than `default_store`, prefix each variable with the store identifier and `_`. For a store
`prod_store` of type `gcp`, the variable is `prod_store_GOOGLE_APPLICATION_CREDENTIALS_CONTENT`.

Never commit these values to Git.

## Next steps

- To set a sensitive parameter through an external Credential, see
  [Configure external Credentials](/docs/how-to/configure-external-credentials.md).
- To move existing local Credentials to the Secret Store, see
  [Migrate a template repository to external Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
  and
  [Migrate an instance repository to external Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

## Related documentation

- [External Credentials](/docs/features/external-creds.md)
- [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
