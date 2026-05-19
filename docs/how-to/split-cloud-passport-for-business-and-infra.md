# Split a Cloud Passport for business and infra environments

- [Split a Cloud Passport for business and infra environments](#split-a-cloud-passport-for-business-and-infra-environments)
  - [Overview](#overview)
  - [When to use this pattern](#when-to-use-this-pattern)
  - [Layout](#layout)
  - [Content guidance](#content-guidance)
    - [Safe to place at cluster level](#safe-to-place-at-cluster-level)
    - [Keep out of the cluster-level passport](#keep-out-of-the-cluster-level-passport)
  - [Steps](#steps)
    - [1. Configure the business passport (default)](#1-configure-the-business-passport-default)
    - [2. Configure the infra passport (minimal)](#2-configure-the-infra-passport-minimal)
    - [3. Verify the result](#3-verify-the-result)
  - [Result](#result)
  - [Related documentation](#related-documentation)

## Overview

When a single cluster hosts both business application environments and infrastructure (infra)
environments, the two workload types may need different parameter sets. The business workloads
depend on full database, messaging, storage, and BSS configuration. The infra workloads only need
cluster connectivity and observability.

This how-to describes a pattern that uses two Cloud Passport files in the same `cloud-passport/`
directory: a business passport as the cluster default (resolved via auto-association) and a
minimal infra passport that infra environments reference explicitly.

For the processing rules that make this pattern work, see
[Cloud Passport processing](https://github.com/Netcracker/qubership-envgene/blob/main/docs/features/cloud-passport-processing.md).

## When to use this pattern

Use this pattern when:

- Your cluster hosts both business and infra environments.
- The infra environments should not receive business-specific parameters (`bss`, `core`,
  `storage`, etc.).
- You want each environment type to resolve its own minimal, correct parameter set.

If all environments in your cluster share the same parameter set, a single Cloud Passport is
sufficient and this pattern is unnecessary.

## Layout

The pattern uses two passport files in the same `cloud-passport/` directory:

```text
<instance-repo>/
└── environments/
    └── <cluster-name>/
        └── cloud-passport/
            ├── <cluster-name>.yml            ← business passport (full parameter set)
            ├── <cluster-name>-creds.yml      ← credentials for the business passport
            ├── <cluster-name>-infra.yml      ← infra passport (minimal parameter set)
            └── <cluster-name>-infra-creds.yml ← credentials for the infra passport
```

Business environments resolve the first file via auto-association. Infra environments reference
the second file explicitly via the `cloudPassport` field in their `env_definition.yml`.

## Content guidance

Use the following guidance to decide which sections belong in each passport.

### Safe to place at cluster level

These sections contain parameters safe and meaningful for all environment types. Place them in the
business passport (cluster default). They are also fine to repeat in the infra passport when the
infra deployer needs them.

| Section | Example parameters | Why safe for all env types |
| --- | --- | --- |
| `cloud` | `CLOUD_API_HOST`, `CLOUD_API_PORT`, `CLOUD_DEPLOY_TOKEN`, `CLOUD_PROTOCOL` | Required by all deployers to connect to the cluster |
| `global` | `MONITORING_ENABLED`, `TRACING_ENABLED`, `TRACING_HOST` | Observability switches applicable to all workload types |
| `consul` | `CONSUL_URL`, `CONSUL_ENABLED` | Safe when all environments in the cluster use Consul |
| `vault` | `VAULT_ADDR`, `VAULT_AUTH_ROLE_ID` | Safe when all environments use Vault for secrets management |

### Keep out of the cluster-level passport

These sections contain parameters meaningful only to specific workload types. Place them only in
the business passport. The infra passport should omit them so infra environments do not inherit
business-only keys via auto-association.

| Section | Example parameters | Intended for |
| --- | --- | --- |
| `bss` | `DOC_STORAGE_TEMPORARY_BUCKET_NAME`, `DOC_STORAGE_PERSISTENT_BUCKET_NAME` | Business applications only |
| `core` | `DEFAULT_TENANT_ADMIN_LOGIN`, `DEFAULT_TENANT_ADMIN_PASSWORD`, `MAVEN_REPO_URL` | Business application runtime |
| `storage` | `STORAGE_SERVER_URL`, `STORAGE_PROVIDER`, `CDN_STORAGE_*`, `DOC_STORAGE_*` | Business application object storage |
| `maas` | `MAAS_SERVICE_ADDRESS`, `MAAS_CREDENTIALS_USERNAME` | Business application message broker |
| `dbaas` | `API_DBAAS_ADDRESS`, `DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME` | Business application database provisioning |
| `zookeeper` | `ZOOKEEPER_ADDRESS`, `ZOOKEEPER_URL` | Business application coordination service |

## Steps

### 1. Configure the business passport (default)

Keep your existing full passport as the **business default**, for example `cluster-01.yml`:

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

Business environments require no change to their `env_definition.yml`. With no `cloudPassport`
field set, auto-association resolves the business passport by default:

```yaml
# cluster-01/env-business-payments/Inventory/env_definition.yml
inventory:
  environmentName: env-business-payments
  tenantName: tenant
  # cloudPassport field absent → auto-association resolves cluster-01.yml
```

### 2. Configure the infra passport (minimal)

Create a minimal infra passport, for example `cluster-01-infra.yml`, containing only the sections
safe at cluster level:

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

# Intentionally omitted - business workloads only:
#   dbaas, maas, storage, core, bss, zookeeper
```

Update the infra environment's `env_definition.yml` to reference the infra passport explicitly:

```yaml
# cluster-01/env-infra-monitoring/Inventory/env_definition.yml
inventory:
  environmentName: env-infra-monitoring
  tenantName: infra-ops
  cloudPassport: cluster-01-infra    ← explicit → resolves cluster-01-infra.yml
```

### 3. Verify the result

Rebuild the affected environments and inspect the generated
[`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)
for each:

- The business environment's `cloud.yml` contains keys from the business passport
  (`cloud + dbaas + maas + storage + core + global + bss`). Inline traceability comments reference
  `cloud passport: <cluster-name> version: <passport-version>`.
- The infra environment's `cloud.yml` contains only the keys from the infra passport
  (`cloud + global`). Inline traceability comments reference
  `cloud passport: <cluster-name>-infra version: <passport-version>`.

If the infra environment's `cloud.yml` still contains business-only keys, recheck that the
`cloudPassport` field is set to the infra passport name and that the infra passport file exists
in the expected directory.

## Result

After applying the pattern, the cluster directory contains two passport files and two
environments resolving them independently:

```text
environments/
└── cluster-01/
    ├── cloud-passport/
    │   ├── cluster-01.yml                   ← full passport (business envs, default)
    │   ├── cluster-01-creds.yml
    │   ├── cluster-01-infra.yml             ← minimal passport (infra envs, explicit)
    │   └── cluster-01-infra-creds.yml
    │
    ├── env-business-payments/               ← BUSINESS env
    │   └── Inventory/
    │       └── env_definition.yml           ← no cloudPassport field (auto-association)
    │                                           resolves: cluster-01.yml
    │                                           receives: cloud + dbaas + maas + storage + core + global + bss
    │
    └── env-infra-monitoring/                ← INFRA env
        └── Inventory/
            └── env_definition.yml           ← cloudPassport: cluster-01-infra (explicit)
                                                resolves: cluster-01-infra.yml
                                                receives: cloud + global only
```

Existing business environments continue to work without modification. Auto-association keeps
resolving the cluster default passport, and their effective parameter set is unchanged.

## Related documentation

- [Cloud Passport processing](https://github.com/Netcracker/qubership-envgene/blob/main/docs/features/cloud-passport-processing.md)
- [Creating a cluster](https://github.com/Netcracker/qubership-envgene/blob/main/docs/how-to/create-cluster.md)
- [EnvGene Configs: `env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml)
- [EnvGene Objects: Cloud Passport](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud-passport)
