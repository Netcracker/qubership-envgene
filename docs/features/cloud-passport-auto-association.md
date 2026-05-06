# Cloud Passport Auto-Association — How It Works

- [Cloud Passport Auto-Association — How It Works](#cloud-passport-auto-association--how-it-works)
  - [Overview](#overview)
  - [1. What Is a Cloud Passport?](#1-what-is-a-cloud-passport)
  - [2. Environment Types in a Mixed Cluster](#2-environment-types-in-a-mixed-cluster)
  - [3. How a Passport Is Resolved](#3-how-a-passport-is-resolved)
    - [3.1 Path 1 — Explicit Association](#31-path-1--explicit-association)
    - [3.2 Path 2 — Auto-Association](#32-path-2--auto-association)
    - [3.3 Resolution Summary](#33-resolution-summary)
  - [4. What the Passport Contributes to an Environment](#4-what-the-passport-contributes-to-an-environment)
    - [4.1 Named Service Sections](#41-named-service-sections)
    - [4.2 All Other Sections](#42-all-other-sections)
    - [4.3 Merge Behaviour](#43-merge-behaviour)
  - [5. Parameter Traceability](#5-parameter-traceability)
  - [6. Passport Scope](#6-passport-scope)
  - [7. Cloud Passport Content Guidance](#7-cloud-passport-content-guidance)
    - [7.1 Safe to Place at Cluster Level](#71-safe-to-place-at-cluster-level)
    - [7.2 Keep Out of the Cluster-Level Passport](#72-keep-out-of-the-cluster-level-passport)
  - [8. Environment-Specific Passports (Business and Infra)](#8-environment-specific-passports-business-and-infra)
    - [8.1 When to Use Environment-Specific Passports](#81-when-to-use-environment-specific-passports)
    - [8.2 Business Passport](#82-business-passport)
    - [8.3 Infra Passport](#83-infra-passport)
    - [8.4 Mixed Cluster with Both Passport Types](#84-mixed-cluster-with-both-passport-types)
  - [Related Documentation](#related-documentation)

## Overview

This guide explains how Cloud Passport auto-association works in `Envgene` — what it is, what triggers it, how a passport is resolved, and what it contributes to an environment's deployment context. It also covers how passport scope applies when a cluster hosts both **business environments** and **infrastructure (infra) environments**.

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

## 2. Environment Types in a Mixed Cluster

A cluster directory can host two types of environments. Both live under the same cluster folder and share cluster-level configuration, including the Cloud Passport.

| Environment type | Purpose | Typical workloads |
| --- | --- | --- |
| **Business** | Runs application workloads | Payments service, orders service, BSS applications |
| **Infrastructure (infra)** | Runs platform workloads | Monitoring stack, logging, ingress controllers |

Both environment types resolve the Cloud Passport through the same mechanism described in [Section 3](#3-how-a-passport-is-resolved). If a cluster requires each type to receive a different parameter set, see [Section 8](#8-environment-specific-passports-business-and-infra).

## 3. How a Passport Is Resolved

Every environment build goes through a passport resolution step. The system checks the environment's [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml) file and follows one of two paths.

### 3.1 Path 1 — Explicit Association

If [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml) contains a `cloudPassport` field under `inventory`, the system uses that named passport:

```yaml
# <cluster>/<env>/Inventory/env_definition.yml
inventory:
  environmentName: env-01
  tenantName: tenant
  cloudPassport: cluster-01    ← the system resolves this exact passport
```

The system searches for a file matching that name, starting from the environment's own directory and walking upward through the folder hierarchy to the instance repository root. The first match found is used.

### 3.2 Path 2 — Auto-Association

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

### 3.3 Resolution Summary

| `cloudPassport` field in [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml) | Resolution behaviour |
| --- | --- |
| Set to a name | System searches bottom-up for `<name>.yml` and uses the first match |
| Absent | System looks for `cloud-passport/<cluster-name>.yml`, then `cloud-passport/passport.yml` |
| Absent and no `cloud-passport/` folder exists | No passport applied — build continues |

## 4. What the Passport Contributes to an Environment

Once a passport is resolved, the system processes it and merges its contents into the environment's deployment context file ([`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)). The passport sections are handled in two ways depending on the section name.

### 4.1 Named Service Sections

The following sections are mapped into dedicated configuration blocks within [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud):

| Passport section | Destination in [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) | What it configures |
| --- | --- | --- |
| `cloud` | Top-level connectivity fields | API host, port, protocol, dashboard URL, deploy token, production mode flag |
| `dbaas` | `dbaasConfigs` block | Database aggregator URL, API address, credentials reference |
| `maas` | `maasConfig` block | Message broker internal and external addresses, credentials reference |
| `consul` | `consulConfig` block | Consul URL, enabled flag, admin token reference |
| `vault` | `vaultConfig` block | Vault URL, enabled flag, credentials reference |

### 4.2 All Other Sections

Every section not listed above — such as `zookeeper`, `storage`, `core`, `global`, `bss`, or any custom section — is merged **flat** into the `deployParameters` map. Each key-value pair in those sections becomes a direct entry in `deployParameters`.

This means all parameters from all sections of the passport are present in the environment's deployment context after the merge.

### 4.3 Merge Behaviour

- Parameters from the passport are written into [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) during the build.
- If a key already exists in [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud), the passport value takes precedence unless a higher-priority source (such as a per-environment parameter file) overrides it later in the build pipeline.
- All sections of the passport are processed — there is no filtering by section name beyond the named-service mappings above.

## 5. Parameter Traceability

Every parameter written from a passport into [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) is annotated with its origin. The annotation is an inline comment that records the passport name and the passport version:

```text
STORAGE_SERVER_URL: https://minio.cluster-01.qubership.org  # cloud passport: cluster-01 version: 1.5
MONITORING_ENABLED: "true"                                  # cloud passport: cluster-01 version: 1.5
```

This annotation is written automatically for every parameter and requires no additional configuration. It allows you to open any environment's generated [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) and identify the exact source of any passport-contributed value.

## 6. Passport Scope

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

## 7. Cloud Passport Content Guidance

Because the cluster-scoped passport is resolved for every environment that does not set an explicit `cloudPassport` field, its contents are applied cluster-wide. The following guidance helps you decide what belongs at this level.

### 7.1 Safe to Place at Cluster Level

These sections contain parameters that are safe and meaningful for all environment types:

| Section | Example parameters | Why safe for all env types |
| --- | --- | --- |
| `cloud` | `CLOUD_API_HOST`, `CLOUD_API_PORT`, `CLOUD_DEPLOY_TOKEN`, `CLOUD_PROTOCOL` | Required by all deployers to connect to the cluster |
| `global` | `MONITORING_ENABLED`, `TRACING_ENABLED`, `TRACING_HOST` | Observability switches applicable to all workload types |
| `consul` | `CONSUL_URL`, `CONSUL_ENABLED` | Safe when all environments in the cluster use Consul |
| `vault` | `VAULT_URL`, `VAULT_ENABLED` | Safe when all environments use Vault for secrets management |

### 7.2 Keep Out of the Cluster-Level Passport

These sections contain parameters that are meaningful only to specific workload types. When placed at cluster level, they are inherited by all environments regardless of workload type:

| Section | Example parameters | Intended for |
| --- | --- | --- |
| `bss` | `DOC_STORAGE_TEMPORARY_BUCKET_NAME`, `DOC_STORAGE_PERSISTENT_BUCKET_NAME` | Business applications only |
| `core` | `DEFAULT_TENANT_ADMIN_LOGIN`, `DEFAULT_TENANT_ADMIN_PASSWORD`, `MAVEN_REPO_URL` | Business application runtime |
| `storage` | `STORAGE_SERVER_URL`, `STORAGE_PROVIDER`, `CDN_STORAGE_*`, `DOC_STORAGE_*` | Business application object storage |
| `maas` | `MAAS_SERVICE_ADDRESS`, `MAAS_CREDENTIALS_USERNAME` | Business application message broker |
| `dbaas` | `API_DBAAS_ADDRESS`, `DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME` | Business application database provisioning |
| `zookeeper` | `ZOOKEEPER_ADDRESS`, `ZOOKEEPER_URL` | Business application coordination service |

> If your cluster hosts both business and infra environments and you need each type to receive a different parameter set, see [Section 8](#8-environment-specific-passports-business-and-infra).

---

## 8. Environment-Specific Passports (Business and Infra)

This section applies when a mixed cluster requires business and infra environments to receive **different parameter sets**. If all environments in your cluster share the same passport, you do not need this section.

### 8.1 When to Use Environment-Specific Passports

Use environment-specific passports when:

- Your cluster hosts both business and infra environments
- The infra environments should not receive business-specific parameters (`bss`, `core`, `storage`, etc.)
- You want each environment type to resolve its own minimal, correct parameter set

The approach uses two passport files in the same `cloud-passport/` directory:

```text
<instance-repo>/
└── <cluster-name>/
    └── cloud-passport/
        ├── <cluster-name>.yml            ← business passport — full parameter set
        ├── <cluster-name>-creds.yml      ← credentials for the business passport
        ├── <cluster-name>-infra.yml      ← infra passport — minimal parameter set
        └── <cluster-name>-infra-creds.yml ← credentials for the infra passport
```

### 8.2 Business Passport

The business passport is the cluster default. Any environment without a `cloudPassport` field resolves this passport via auto-association. It contains all sections required by business application workloads:

**File:** `cloud-passport/<cluster-name>.yml`

```yaml
---
version: 1.5

cloud:
  CLOUD_API_HOST: api.cluster-01.qubership.org
  CLOUD_API_PORT: "6443"
  CLOUD_DEPLOY_TOKEN: cloud-deploy-sa-token
  CLOUD_PUBLIC_HOST: cluster-01.qubership.org
  CLOUD_PRIVATE_HOST: cluster-01.qubership.org
  CLOUD_DASHBOARD_URL: https://dashboard.cluster-01.qubership.org
  CLOUD_PROTOCOL: https
  PRODUCTION_MODE: false

dbaas:
  API_DBAAS_ADDRESS: http://dbaas.dbaas:8080
  DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.qubership.org
  DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: ${creds.get("dbaas-cred").username}
  DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: ${creds.get("dbaas-cred").password}

maas:
  MAAS_INTERNAL_ADDRESS: http://maas.maas:8080
  MAAS_SERVICE_ADDRESS: http://maas.cluster-01.qubership.org
  MAAS_CREDENTIALS_USERNAME: ${creds.get("maas-cred").username}
  MAAS_CREDENTIALS_PASSWORD: ${creds.get("maas-cred").password}

consul:
  CONSUL_URL: http://consul.consul:8080
  CONSUL_ENABLED: true
  CONSUL_PUBLIC_URL: http://consul.consul:8080
  CONSUL_ADMIN_TOKEN: ${creds.get("consul-cred").secret}

storage:
  STORAGE_SERVER_URL: https://minio.cluster-01.qubership.org
  STORAGE_PROVIDER: s3
  STORAGE_REGION: eu-west-1
  STORAGE_USERNAME: ${creds.get("minio-cred").username}
  STORAGE_PASSWORD: ${creds.get("minio-cred").password}

core:
  DEFAULT_TENANT_NAME: tenant
  DEFAULT_TENANT_ADMIN_LOGIN: admin
  DEFAULT_TENANT_ADMIN_PASSWORD: password
  MAVEN_REPO_URL: https://artifactory.qubership.org
  MAVEN_REPO_NAME: mvn.group

global:
  MONITORING_ENABLED: "true"
  TRACING_ENABLED: "false"
  TRACING_HOST: tracing-agent

bss:
  DOC_STORAGE_TEMPORARY_BUCKET_NAME: temporary-bucket
  DOC_STORAGE_PERSISTENT_BUCKET_NAME: permanent-bucket
```

**`env_definition.yml` for a business environment** — no `cloudPassport` field needed (auto-association resolves the default):

```yaml
# cluster-01/env-business-payments/Inventory/env_definition.yml
inventory:
  environmentName: env-business-payments
  tenantName: tenant
  # cloudPassport field absent → auto-association resolves cluster-01.yml
```

### 8.3 Infra Passport

The infra passport is a minimal configuration intended for platform workloads. It contains only the parameters an infra deployer needs — cluster connectivity and observability. Infra environments must explicitly reference it via the `cloudPassport` field.

**File:** `cloud-passport/<cluster-name>-infra.yml`

```yaml
---
version: 1.0

cloud:
  CLOUD_API_HOST: api.cluster-01.qubership.org
  CLOUD_API_PORT: "6443"
  CLOUD_DEPLOY_TOKEN: cloud-deploy-sa-token
  CLOUD_PUBLIC_HOST: cluster-01.qubership.org
  CLOUD_PRIVATE_HOST: cluster-01.qubership.org
  CLOUD_DASHBOARD_URL: https://dashboard.cluster-01.qubership.org
  CLOUD_PROTOCOL: https
  PRODUCTION_MODE: false

global:
  MONITORING_ENABLED: "true"
  TRACING_ENABLED: "false"
  TRACING_HOST: tracing-agent

# Intentionally omitted — business workloads only:
#   dbaas:    database provisioning
#   maas:     message broker
#   storage:  object storage
#   core:     tenant admin credentials, Maven repo
#   bss:      BSS application config
#   zookeeper: coordination service
```

**`env_definition.yml` for an infra environment** — must explicitly set `cloudPassport` to the infra passport:

```yaml
# cluster-01/env-infra-monitoring/Inventory/env_definition.yml
inventory:
  environmentName: env-infra-monitoring
  tenantName: infra-ops
  cloudPassport: cluster-01-infra    ← explicit → resolves cluster-01-infra.yml
```

### 8.4 Mixed Cluster with Both Passport Types

With both passport files in place, business and infra environments resolve their own passport from the same `cloud-passport/` directory:

```text
cluster-01/
├── cloud-passport/
│   ├── cluster-01.yml                   ← full passport — business envs (default)
│   ├── cluster-01-creds.yml
│   ├── cluster-01-infra.yml             ← minimal passport — infra envs (explicit)
│   └── cluster-01-infra-creds.yml
│
├── business-env/               ← BUSINESS env
│   └── Inventory/
│       └── env_definition.yml           ← no cloudPassport field (auto-association)
│                                           resolves: cluster-01.yml
│                                           receives: cloud + dbaas + maas + storage + core + global + bss
│
└── infra-env/                ← INFRA env
    └── Inventory/
        └── env_definition.yml           ← cloudPassport: cluster-01-infra  (explicit)
                                            resolves: cluster-01-infra.yml
                                            receives: cloud + global only
```

Business environments require no change — auto-association continues to resolve the full passport by default. Only infra environments need a `cloudPassport` field added to their [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml).

---

## Related Documentation

- [EnvGene Configs — `env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml)
- [EnvGene Objects — Cloud Passport](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud-passport)
- [EnvGene Objects — Cloud (`cloud.yml`)](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)
- [`env_definition.yml` JSON Schema](https://github.com/Netcracker/qubership-envgene/blob/main/schemas/env-definition.schema.json)