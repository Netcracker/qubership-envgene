# Cloud Passport Auto-Association — How It Works

- [Cloud Passport Auto-Association — How It Works](#cloud-passport-auto-association--how-it-works)
  - [Overview](#overview)
  - [1. What Is a Cloud Passport?](#1-what-is-a-cloud-passport)
  - [2. How a Passport Is Resolved](#2-how-a-passport-is-resolved)
    - [2.1 Path 1 — Explicit Association](#21-path-1--explicit-association)
    - [2.2 Path 2 — Auto-Association](#22-path-2--auto-association)
    - [2.3 Resolution Summary](#23-resolution-summary)
  - [3. What the Passport Contributes to an Environment](#3-what-the-passport-contributes-to-an-environment)
    - [3.1 Named Service Sections](#31-named-service-sections)
    - [3.2 All Other Sections](#32-all-other-sections)
    - [3.3 Merge Behaviour](#33-merge-behaviour)
  - [4. Parameter Traceability](#4-parameter-traceability)
  - [5. Passport Scope](#5-passport-scope)

## Overview

This guide explains how Cloud Passport auto-association works in `Envgene` — what it is, what triggers it, how a passport is resolved, and what it contributes to an environment's deployment context.

## 1. What Is a Cloud Passport?

A **Cloud Passport** is a versioned configuration file that defines the deployment context for a cluster. It is the central place where cluster-specific parameters are declared, including:

- Cluster API endpoint and connectivity settings
- Credentials references for platform services such as databases, message brokers, and object storage
- Runtime parameters consumed by the deployment engine during environment builds

A Cloud Passport lives inside a dedicated folder at the cluster level of your instance repository:

```text
<instance-repo>/
└── <cluster-name>/
    └── cloud-passport/
        ├── <cluster-name>.yml        ← main passport file
        └── <cluster-name>-creds.yml  ← credential entries used by the passport
```

The passport file is a YAML document with a `version` field and a set of named sections. Each section is a flat map of parameter keys to values:

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

bss:
  DOC_STORAGE_TEMPORARY_BUCKET_NAME: temporary-bucket
  DOC_STORAGE_PERSISTENT_BUCKET_NAME: permanent-bucket
```

> See [Cloud Passport](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud-passport) in the EnvGene Objects reference for the full object specification.

## 2. How a Passport Is Resolved

Every environment build goes through a passport resolution step. The system checks the environment's [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml) file and follows one of two paths.

### 2.1 Path 1 — Explicit Association

If [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml) contains a `cloudPassport` field under `inventory`, the system uses that named passport:

```yaml
# <cluster>/<env>/Inventory/env_definition.yml
inventory:
  environmentName: env-01
  tenantName: tenant
  cloudPassport: cluster-01    ← the system resolves this exact passport
```

The system searches for a file matching that name, starting from the environment's own directory and walking upward through the folder hierarchy to the instance repository root. The first match found is used.

### 2.2 Path 2 — Auto-Association

If the `cloudPassport` field is **not present** in [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml), the system applies auto-association:

```yaml
# <cluster>/<env>/Inventory/env_definition.yml
inventory:
  environmentName: env-01
  tenantName: tenant
  # no cloudPassport field → auto-association applies
```

The system walks up from the environment directory to the cluster directory and searches for a default passport in this order:

1. `cloud-passport/<cluster-name>.yml` — a file named after the cluster directory
2. `cloud-passport/passport.yml` — a generic fallback name

If neither file exists, no passport is applied and the build continues without one.

### 2.3 Resolution Summary

| `cloudPassport` field in `env_definition.yml` | Resolution behaviour |
| --- | --- |
| Set to a name | System searches bottom-up for `<name>.yml` and uses the first match |
| Absent | System looks for `cloud-passport/<cluster-name>.yml`, then `cloud-passport/passport.yml` |
| Absent and no `cloud-passport/` folder exists | No passport applied — build continues |

## 3. What the Passport Contributes to an Environment

Once a passport is resolved, the system processes it and merges its contents into the environment's deployment context file ([`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)). The passport sections are handled in two ways depending on the section name.

### 3.1 Named Service Sections

The following sections are mapped into dedicated configuration blocks within [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud):

| Passport section | Destination in `cloud.yml` | What it configures |
| --- | --- | --- |
| `cloud` | Top-level connectivity fields | API host, port, protocol, dashboard URL, deploy token, production mode flag |
| `dbaas` | `dbaasConfigs` block | Database aggregator URL, API address, credentials reference |
| `maas` | `maasConfig` block | Message broker internal and external addresses, credentials reference |
| `consul` | `consulConfig` block | Consul URL, enabled flag, admin token reference |
| `vault` | `vaultConfig` block | Vault URL, enabled flag, credentials reference |

### 3.2 All Other Sections

Every section not listed above — such as `zookeeper`, `storage`, `core`, `global`, `bss`, or any custom section — is merged **flat** into the `deployParameters` map. Each key-value pair in those sections becomes a direct entry in `deployParameters`.

This means all parameters from all sections of the passport are present in the environment's deployment context after the merge.

### 3.3 Merge Behaviour

- Parameters from the passport are written into [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) during the build.
- If a key already exists in [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud), the passport value takes precedence unless a higher-priority source (such as a per-environment parameter file) overrides it later in the build pipeline.
- All sections of the passport are processed — there is no filtering by section name beyond the named-service mappings above.

## 4. Parameter Traceability

Every parameter written from a passport into [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) is annotated with its origin. The annotation is an inline comment that records the passport name and the passport version:

```text
STORAGE_SERVER_URL: https://minio.cluster-01.qubership.org  # cloud passport: cluster-01 version: 1.5
MONITORING_ENABLED: "true"                                  # cloud passport: cluster-01 version: 1.5
```

This annotation is written automatically for every parameter and requires no additional configuration. It allows you to open any environment's generated [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) and identify the exact source of any passport-contributed value.

## 5. Passport Scope

A Cloud Passport placed in `cloud-passport/` at the cluster directory level applies to all environments within that cluster that resolve it — either explicitly via the `cloudPassport` field or through auto-association.

```text
<cluster-name>/
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

All three environments above will have the full passport contents merged into their deployment context.
