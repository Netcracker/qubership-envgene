# Infra and business environments

Templates for one cluster with an infra and a business environment on the No-CMDB v2 architecture. Replace the
`<placeholders>` with the values of your project.

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

`env-business-external.json` is the external credentials variant of the business environment. It needs Cloud
Passport credentials of `type: external`, while the passports in this set use local credentials.

## What differs

| Field                          | Infra                                                        | Business                                   |
|--------------------------------|--------------------------------------------------------------|--------------------------------------------|
| `envTemplate.name`, `artifact` | the infra Environment Template                               | the business Environment Template          |
| `additionalTemplateVariables`  | platform settings: preset, storage class, logging            | settings of the business template          |
| `envSpecificParamsets`         | one entry per infrastructure Namespace, such as `postgresql` | none: the template provides the parameters |
| `envSpecificE2EParamsets`      | DCL parameters: `dcl-configuration-common`, `-custom`        | none                                       |
| `inventory.cloudPassport`      | `passport-infra`                                             | absent: the cluster default `passport.yml` |
| `inventory.tenantName`         | absent                                                       | set                                        |

## Create them through the pipeline

Pass `env-inventory-content/env-infra.json` or `env-inventory-content/env-business.json` as
[`ENV_INVENTORY_CONTENT`](/docs/instance-pipeline-parameters.md#env_inventory_content). For the steps, see
[Create an Environment Inventory](/docs/how-to/create-environment-inventory.md#create-an-environment-through-the-pipeline-recommended).
Commit the files listed in `sharedTemplateVariables` to `configuration/` by hand.
