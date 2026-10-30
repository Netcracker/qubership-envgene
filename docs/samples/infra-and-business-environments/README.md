# Infra and business environments

Use these templates to set up one cluster with an infra and a business environment. Replace the `<placeholders>`
with the values of your project.

- an **infra environment** deploys the infrastructure Solution Descriptor of the cluster, such as databases and
  message brokers
- a **business environment** deploys the business solution on top of it

Both live in one Instance repository under the same cluster folder, and each uses its own Cloud Passport:

```text
environments/
└── cluster-01/
    ├── cloud-passport/
    │   ├── passport.yml               ← business passport, cluster default
    │   ├── passport-creds.yml
    │   ├── passport-infra.yml         ← infra passport
    │   └── passport-infra-creds.yml
    ├── env-infra/Inventory/env_definition.yml
    └── env-business/Inventory/env_definition.yml
```

| Folder                                       | Content                                                                    |
|----------------------------------------------|----------------------------------------------------------------------------|
| `instance-repository/`                       | Cloud Passports, credentials files, and Environment Inventories            |
| `env-inventory-content/`                     | Values of the `ENV_INVENTORY_CONTENT` pipeline parameter that create them  |

The credentials in this set are local. See
[Configure local credentials](/docs/how-to/configure-local-credentials.md). To keep them in a Secret Store, see
[Configure external credentials](/docs/how-to/configure-external-credentials.md).

## What differs

The two environments differ only in the Environment Template and the Cloud Passport:

| Field                          | Infra                          | Business                                   |
|--------------------------------|--------------------------------|--------------------------------------------|
| `envTemplate.name`, `artifact` | the infra Environment Template | the business Environment Template          |
| `inventory.cloudPassport`      | `passport-infra`               | absent: the cluster default `passport.yml` |

## Create them through the pipeline

Pass `env-inventory-content/env-infra.json` or `env-inventory-content/env-business.json` as
[`ENV_INVENTORY_CONTENT`](/docs/instance-pipeline-parameters.md#env_inventory_content). For the steps, see
[Create an Environment Inventory](/docs/how-to/create-environment-inventory.md#create-an-environment-through-the-pipeline-recommended).
