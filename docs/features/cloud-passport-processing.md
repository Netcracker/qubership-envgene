# Cloud Passport processing

- [Cloud Passport processing](#cloud-passport-processing)
  - [Overview](#overview)
  - [Passport file](#passport-file)
  - [Resolution](#resolution)
    - [Explicit association](#explicit-association)
    - [Auto-association](#auto-association)
    - [Resolution summary](#resolution-summary)
  - [Merge into `cloud.yml`](#merge-into-cloudyml)
    - [Named service sections](#named-service-sections)
    - [All other sections](#all-other-sections)
    - [Merge behaviour](#merge-behaviour)
  - [Parameter traceability](#parameter-traceability)
  - [Related documentation](#related-documentation)

## Overview

This guide describes how EnvGene processes a Cloud Passport during an environment build: where the
passport lives, how the build resolves which passport to use, and what the passport contributes to
the environment's deployment context.

The passport itself reaches the instance repository either through the Cloud Passport Discovery
Tool or by manual editing. For those workflows, see
[Creating a cluster](https://github.com/Netcracker/qubership-envgene/blob/main/docs/how-to/create-cluster.md).
This document covers the build-time behaviour after the passport is in place.

For a deployment pattern where business and infra environments in the same cluster receive
different parameter sets, see
[Split a Cloud Passport for business and infra environments](https://github.com/Netcracker/qubership-envgene/blob/main/docs/how-to/split-cloud-passport-for-business-and-infra.md).

## Passport file

A **Cloud Passport** is a versioned configuration file that defines the deployment context for a
cluster. It is the central place where cluster-specific parameters are declared, including:

- Cluster API endpoint and connectivity settings
- Credentials references for platform services such as databases, message brokers, and object
  storage
- Runtime parameters consumed by the deployment engine during environment builds

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
---
version: 1.5

cloud:
  CLOUD_API_HOST: api.cluster-01.qubership.org
  CLOUD_API_PORT: "6443"
  CLOUD_DEPLOY_TOKEN: cloud-deploy-sa-token
  CLOUD_PUBLIC_HOST: cluster-01.qubership.org
  CLOUD_PROTOCOL: https
  PRODUCTION_MODE: false

dbaas:
  API_DBAAS_ADDRESS: http://dbaas.dbaas:8080
  DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.qubership.org

maas:
  MAAS_INTERNAL_ADDRESS: http://maas.maas:8080
  MAAS_SERVICE_ADDRESS: http://maas.cluster-01.qubership.org

consul:
  CONSUL_URL: http://consul.consul:8080
  CONSUL_ENABLED: true

storage:
  STORAGE_SERVER_URL: https://minio.cluster-01.qubership.org
  STORAGE_PROVIDER: s3
  STORAGE_REGION: eu-west-1

global:
  MONITORING_ENABLED: "true"
  TRACING_ENABLED: "false"
  TRACING_HOST: tracing-agent
```

> See [Cloud Passport](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud-passport)
> in the EnvGene Objects reference for the full object specification.

## Resolution

Every environment build goes through a passport resolution step. The system checks the
environment's [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml)
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
    ├── env-02/
    │   └── Inventory/
    │       └── env_definition.yml ← cloudPassport: <cluster-name>  (explicit)
    └── env-03/
        └── Inventory/
            └── env_definition.yml ← no cloudPassport field  (auto-association)
```

### Explicit association

If [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml)
contains a `cloudPassport` field under `inventory`, the system uses that named passport:

```yaml
# <cluster>/<env>/Inventory/env_definition.yml
inventory:
  environmentName: env-01
  tenantName: tenant
  cloudPassport: cluster-01    ← the system resolves this exact passport
```

The system searches for a file matching that name, starting from the environment's own directory
and walking upward through the folder hierarchy to the instance repository root. Exactly one match
is required. If multiple files match the same name, the build fails with a duplicate-passport
error.

### Auto-association

If the `cloudPassport` field is **not present** in
[`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml),
the system applies auto-association:

```yaml
# <cluster>/<env>/Inventory/env_definition.yml
inventory:
  environmentName: env-01
  tenantName: tenant
  # no cloudPassport field → auto-association applies
```

The system looks for a default passport in the env's parent (cluster) directory, in this order:

1. `cloud-passport/<cluster-name>.{yml|yaml}` (a file named after the cluster directory)
2. `cloud-passport/passport.{yml|yaml}` (a generic fallback name)

If neither file exists, no passport is applied and the build continues without one.

### Resolution summary

| `cloudPassport` field in [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml) | Resolution behaviour |
| --- | --- |
| Set to a name | System searches bottom-up for `<name>.{yml\|yaml}`. Exactly one match is required. Otherwise, the build fails. |
| Absent | System looks for `cloud-passport/<cluster-name>.{yml\|yaml}`, then `cloud-passport/passport.{yml\|yaml}`. |
| Absent and no matching file is found | No passport is applied. The build continues. |

## Merge into `cloud.yml`

Once a passport is resolved, the system processes it and merges its contents into the
environment's deployment context file
([`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)).
The passport sections are handled in two ways depending on the section name.

### Named service sections

The following sections are mapped into dedicated configuration blocks within
[`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud):

| Passport section | Destination in [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) | What it configures |
| --- | --- | --- |
| `cloud` | Selected top-level fields in `cloud.yml` (API host/port, protocol, dashboard URL, deploy token, production mode) | A fixed set of 8 well-known keys is mapped to dedicated fields. Any other keys in the `cloud:` section flow into `deployParameters` (see [All other sections](#all-other-sections)). |
| `dbaas` | `dbaasConfigs` block | Database aggregator URL, API address, credentials reference |
| `maas` | `maasConfig` block | Message broker internal and external addresses, credentials reference |
| `consul` | `consulConfig` block | Consul URL, enabled flag, admin token reference |
| `vault` | `vaultConfig` block | Vault URL, enabled flag, credentials reference |

### All other sections

Every section not listed above (such as `zookeeper`, `storage`, `core`, `global`, `bss`, or any
custom section) is merged **flat** into the `deployParameters` map. Each key-value pair in those
sections becomes a direct entry in `deployParameters`.

This means all parameters from all sections of the passport are present in the environment's
deployment context after the merge.

### Merge behaviour

- Parameters from the passport are written into
  [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)
  during the build.
- If a key already exists in
  [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud),
  the passport value takes precedence unless a higher-priority source (such as a per-environment
  parameter file) overrides it later in the build pipeline.
- All sections of the passport are processed. There is no filtering by section name beyond the
  named-service mappings above.

## Parameter traceability

Every parameter written from a passport into
[`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)
is annotated with its origin. The annotation is an inline comment that records the passport name
and the passport version:

```text
STORAGE_SERVER_URL: https://minio.cluster-01.qubership.org  # cloud passport: cluster-01 version: 1.5
MONITORING_ENABLED: "true"                                  # cloud passport: cluster-01 version: 1.5
```

This annotation is written automatically for every parameter and requires no additional
configuration. It allows you to open any environment's generated
[`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)
and identify the exact source of any passport-contributed value.

## Related documentation

- [Creating a cluster](https://github.com/Netcracker/qubership-envgene/blob/main/docs/how-to/create-cluster.md)
- [Split a Cloud Passport for business and infra environments](https://github.com/Netcracker/qubership-envgene/blob/main/docs/how-to/split-cloud-passport-for-business-and-infra.md)
- [EnvGene Configs: `env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml)
- [EnvGene Objects: Cloud Passport](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud-passport)
- [EnvGene Objects: Cloud (`cloud.yml`)](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)
- [`env_definition.yml` JSON Schema](https://github.com/Netcracker/qubership-envgene/blob/main/schemas/env-definition.schema.json)
