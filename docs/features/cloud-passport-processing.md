# Cloud Passport processing

- [Cloud Passport processing](#cloud-passport-processing)
  - [Overview](#overview)
  - [Passport file](#passport-file)
  - [Resolution](#resolution)
    - [Explicit association](#explicit-association)
    - [Auto-association](#auto-association)
    - [Resolution summary](#resolution-summary)
  - [Merge into Cloud](#merge-into-cloud)
    - [Merge behaviour](#merge-behaviour)
  - [Parameter traceability](#parameter-traceability)
  - [Related documentation](#related-documentation)

## Overview

This guide describes how EnvGene processes a Cloud Passport during environment generation: where
the passport lives, how EnvGene resolves which passport to use, and what the passport contributes
to the environment's deployment context.

The passport itself reaches the instance repository either through the Cloud Passport Discovery
Tool or by manual editing. For those workflows, see
[Creating a cluster](/docs/how-to/create-cluster.md).
This document covers what happens during environment generation, once the passport is in place.

For a deployment pattern where business and infra environments in the same cluster receive
different parameter sets, see
[Split a Cloud Passport for business and infra environments](/docs/how-to/split-cloud-passport-for-business-and-infra.md).

## Passport file

A **Cloud Passport** is a contracted set of parameters describing a cluster and the platform
applications installed in it (such as databases, message brokers, object storage, and
observability tooling). It forms a key-based contract: platform applications publish the keys
that describe their endpoints and credentials, business applications consume those keys from
their deployment context to access platform services. During environment generation, the
passport's parameters are merged into the business environment's [Cloud](/docs/envgene-objects.md#cloud) object.

A Cloud Passport lives inside a dedicated folder at the cluster level of your instance repository:

```text
<instance-repo>/
└── environments/
    └── <cluster-name>/
        └── cloud-passport/
            ├── <passport-name>.yml        ← main passport file
            └── <passport-name>-creds.yml  ← credential entries used by the passport
```

EnvGene accepts both `.yml` and `.yaml` extensions. How `<passport-name>` is chosen and resolved
is described in [Resolution](#resolution).

The passport file is a YAML document with a `version` field and a set of named sections. Each
section is a flat map of parameter keys to values:

```yaml
version: 1.5

cloud:
  CLOUD_API_HOST: api.cluster-01.qubership.org
  CLOUD_API_PORT: "6443"
  CLOUD_PRIVATE_HOST: cluster-01.qubership.org
  CLOUD_PUBLIC_HOST: cluster-01.qubership.org
  CLOUD_DASHBOARD_URL: https://dashboard.cluster-01.qubership.org
  CLOUD_DEPLOY_TOKEN: cloud-deploy-cred
  CLOUD_PROTOCOL: https
  PRODUCTION_MODE: false

dbaas:
  API_DBAAS_ADDRESS: http://dbaas.dbaas:8080
  DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.qubership.org
  DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: dbaas-dba-cred

maas:
  MAAS_INTERNAL_ADDRESS: http://maas.maas:8080
  MAAS_SERVICE_ADDRESS: http://maas.cluster-01.qubership.org
  MAAS_CREDENTIALS_USERNAME: maas-cred

vault:
  VAULT_ADDR: https://vault.cluster-01.qubership.org
  VAULT_AUTH_ROLE_ID: vault-auth-cred

consul:
  CONSUL_URL: http://consul.consul:8080
  CONSUL_ENABLED: true
  CONSUL_PUBLIC_URL: https://consul.cluster-01.qubership.org
  CONSUL_ADMIN_TOKEN: consul-admin-cred

# Free-form sections - all keys merged flat into `deployParameters`.
storage:
  STORAGE_SERVER_URL: https://minio.cluster-01.qubership.org
  STORAGE_PROVIDER: s3

global:
  MONITORING_ENABLED: "true"
  TRACING_ENABLED: "false"
```

## Resolution

Every environment generation goes through a passport resolution step. The system checks the
environment's [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml)
file and follows one of two paths.

A Cloud Passport placed in `cloud-passport/` at the cluster directory level can be resolved by all
environments in that cluster, either explicitly via the `cloudPassport` field or through
auto-association:

```text
environments/
└── <cluster-name>/
    ├── cloud-passport/
    │   └── <cluster-name>.yml     ← passport at cluster scope
    ├── env-01/
    │   └── Inventory/
    │       └── env_definition.yml ← cloudPassport: <cluster-name>  (explicit)
    └── env-02/
        └── Inventory/
            └── env_definition.yml ← no cloudPassport field  (auto-association)
```

### Explicit association

If [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml)
contains a `cloudPassport` field under `inventory`, the system uses that named passport:

```yaml
# <cluster>/<env>/Inventory/env_definition.yml
inventory:
  environmentName: env-01
  cloudPassport: cluster-01    # the system resolves this exact passport
```

The system searches for a file matching that name, starting from the environment's own directory
and walking upward through the folder hierarchy to the instance repository root. Exactly one
match is required. If no file matches, generation fails with a not-found error. If multiple
files match the same name, generation fails with a duplicate-passport error.

### Auto-association

If the `cloudPassport` field is **not present** in
[`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml),
the system applies auto-association:

```yaml
# <cluster>/<env>/Inventory/env_definition.yml
inventory:
  environmentName: env-01
  # no `cloudPassport` field → auto-association applies
```

The system looks for a default passport in the env's parent (cluster) directory, in this order:

1. `cloud-passport/<cluster-name>.{yml|yaml}` (a file named after the cluster directory)
2. `cloud-passport/passport.{yml|yaml}` (a generic fallback name)

If neither file exists, no passport is applied and generation continues without one.

### Resolution summary

Decision flow:

1. `cloudPassport` set → bottom-up search for `<name>.{yml|yaml}`. Resolved on exactly one match.
   Generation fails on zero matches (not-found) or multiple matches (duplicate).
2. `cloudPassport` absent → try `cloud-passport/<cluster-name>.{yml|yaml}`, then
   `cloud-passport/passport.{yml|yaml}`. Generation fails on multiple matches (duplicate).
3. Nothing matched → no passport applied, generation continues.

## Merge into Cloud

The [Cloud](/docs/envgene-objects.md#cloud) object is assembled during environment generation
from two sources:

1. **[Cloud Template](/docs/envgene-objects.md#cloud-template)** - the static base, always
   present.
2. **Cloud Passport** - the dynamic, cluster-specific overlay, applied when a passport is
   resolved (optional, see [Resolution](#resolution)).

When a passport is present, its values take precedence over the template for the same Cloud
attribute. The table below maps each passport key to its destination Cloud attribute and to the
Effective Set parameter.

| Cloud Passport key                             | Cloud object attribute                     | Effective Set parameter                     |
|------------------------------------------------|--------------------------------------------|---------------------------------------------|
| `cloud.CLOUD_API_HOST`                         | `apiUrl`                                   | `CLOUD_API_HOST`                            |
| `cloud.CLOUD_API_PORT`                         | `apiPort`                                  | `CLOUD_API_PORT`                            |
| `cloud.CLOUD_PRIVATE_HOST`                     | `privateUrl`                               | `CLOUD_PRIVATE_HOST`                        |
| `cloud.CLOUD_PUBLIC_HOST`                      | `publicUrl`                                | `CLOUD_PUBLIC_HOST`                         |
| `cloud.CLOUD_DASHBOARD_URL`                    | `dashboardUrl`                             | `CLOUD_DASHBOARD_URL`                       |
| `cloud.CLOUD_DEPLOY_TOKEN`                     | `defaultCredentialsId`                     | None                                        |
| `cloud.CLOUD_PROTOCOL`                         | `protocol`                                 | `CLOUD_PROTOCOL`                            |
| `cloud.PRODUCTION_MODE`                        | `productionMode`                           | `PRODUCTION_MODE`                           |
| `dbaas.API_DBAAS_ADDRESS`                      | `dbaasConfigs[0].apiUrl`                   | `API_DBAAS_ADDRESS`                         |
| `dbaas.DBAAS_AGGREGATOR_ADDRESS`               | `dbaasConfigs[0].aggregatorUrl`            | `DBAAS_AGGREGATOR_ADDRESS`                  |
| `dbaas.DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME` | `dbaasConfigs[0].credentialsId` (cred ref) | `DBAAS_AGGREGATOR_USERNAME` (cred.username) |
| `dbaas.DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD` | `dbaasConfigs[0].credentialsId` (cred ref) | `DBAAS_AGGREGATOR_PASSWORD` (cred.password) |
| `dbaas` section present                        | `dbaasConfigs[0].enable: true`             | `DBAAS_ENABLED`                             |
| `maas.MAAS_INTERNAL_ADDRESS`                   | `maasConfig.maasInternalAddress`           | `MAAS_INTERNAL_ADDRESS`                     |
| `maas.MAAS_SERVICE_ADDRESS`                    | `maasConfig.maasUrl`                       | `MAAS_EXTERNAL_ROUTE`                       |
| `maas.MAAS_CREDENTIALS_USERNAME`               | `maasConfig.credentialsId` (cred ref)      | `MAAS_CREDENTIALS_USERNAME` (cred.username) |
| `maas.MAAS_CREDENTIALS_PASSWORD`               | `maasConfig.credentialsId` (cred ref)      | `MAAS_CREDENTIALS_PASSWORD` (cred.password) |
| `maas` section present                         | `maasConfig.enable: true`                  | `MAAS_ENABLED`                              |
| `vault.VAULT_ADDR`                             | `vaultConfig.url`                          | `VAULT_ADDR`, `PUBLIC_VAULT_URL`            |
| `vault.VAULT_AUTH_ROLE_ID`                     | `vaultConfig.credentialsId` (cred ref)     | `VAULT_TOKEN` (cred.secret)                 |
| `vault.VAULT_ADDR` set                         | `vaultConfig.enable: true`                 | `VAULT_ENABLED`                             |
| `consul.CONSUL_URL`                            | `consulConfig.internalUrl`                 | `CONSUL_URL`                                |
| `consul.CONSUL_PUBLIC_URL`                     | `consulConfig.publicUrl`                   | `CONSUL_PUBLIC_URL`                         |
| `consul.CONSUL_ENABLED`                        | `consulConfig.enabled`                     | `CONSUL_ENABLED`                            |
| `consul.CONSUL_ADMIN_TOKEN`                    | `consulConfig.tokenSecret` (cred ref)      | `CONSUL_ADMIN_TOKEN` (cred.secret)          |
| `<other-section>.<KEY>`                        | `deployParameters.<KEY>`                   | `<KEY>`                                     |

Free-form sections (`storage`, `global`, `core`, `zookeeper`, or any custom section)
flow flat into `deployParameters` - see the last row of the table for the pattern.

**Notation used in the table:**

- **(cred ref)** - the Cloud attribute stores a credentials reference (cred ID, a pointer to an
  entry in the credentials file), not the secret itself.
- **(cred.username)**, **(cred.password)**, **(cred.secret)** - the Effective Set parameter
  resolves to the corresponding field of the referenced credential entry.

### Merge behaviour

- Passport values override Cloud Template values for the same attribute.
- Higher-priority sources later in the generation pipeline (such as per-environment parameter
  files) can override passport values.
- Every section in the passport is processed per the mapping table above.

## Parameter traceability

Every parameter written from a passport into the [Cloud](/docs/envgene-objects.md#cloud) object
is annotated with its origin. The annotation is an inline comment that records the passport name
and the passport version:

```text
STORAGE_SERVER_URL: https://minio.cluster-01.qubership.org  # cloud passport: cluster-01 version: 1.5
MONITORING_ENABLED: "true"                                  # cloud passport: cluster-01 version: 1.5
```

This annotation is written automatically for every parameter and requires no additional
configuration. It allows you to open any environment's generated
[Cloud](/docs/envgene-objects.md#cloud) object and identify the exact source of any
passport-contributed value.

## Related documentation

- [Creating a cluster](/docs/how-to/create-cluster.md)
- [Split a Cloud Passport for business and infra environments](/docs/how-to/split-cloud-passport-for-business-and-infra.md)
- [Cloud Passport association: use cases](/docs/use-cases/cloud-passport.md)
- [EnvGene Configs: `env_definition.yml`](/docs/envgene-configs.md#env_definitionyml)
- [EnvGene Objects: Cloud Passport](/docs/envgene-objects.md#cloud-passport)
- [EnvGene Objects: Cloud](/docs/envgene-objects.md#cloud)
- [`env_definition.yml` JSON Schema](/schemas/env-definition.schema.json)
