# Split a Cloud Passport for business and infra environments

- [Split a Cloud Passport for business and infra environments](#split-a-cloud-passport-for-business-and-infra-environments)
  - [Overview](#overview)
  - [When to use this pattern](#when-to-use-this-pattern)
  - [Layout](#layout)
  - [Steps](#steps)
    - [1. Configure the business passport (default)](#1-configure-the-business-passport-default)
    - [2. Configure the infra passport (minimal)](#2-configure-the-infra-passport-minimal)
    - [3. Verify the result](#3-verify-the-result)
  - [Result](#result)
  - [Related documentation](#related-documentation)

## Overview

When a single cluster hosts both business application environments and infrastructure (infra)
environments, the two workload types may need different parameter sets. The business workloads
depend on full database, messaging, storage. The infra workloads only need
cluster connectivity.

This how-to describes a pattern that uses two Cloud Passport files in the same `cloud-passport/`
directory: a business passport as the cluster default (resolved via auto-association) and a
minimal infra passport that infra environments reference explicitly.

For the processing rules that make this pattern work, see
[Cloud Passport processing](/docs/features/cloud-passport-processing.md).

## When to use this pattern

Use this pattern when your cluster hosts both business and infra environments. In EnvGene, a
cluster is a directory under `/environments/` that groups related environments.

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

## Steps

### 1. Configure the business passport (default)

Keep your existing full passport as the **business default**, for example `cluster-01.yml`:

```yaml
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
```

Business environments require no change to their `env_definition.yml`. With no `cloudPassport`
field set, auto-association resolves the business passport by default:

```yaml
# cluster-01/env-business-payments/Inventory/env_definition.yml
inventory:
  environmentName: env-business-payments
  # cloudPassport field absent → auto-association resolves cluster-01.yml
```

### 2. Configure the infra passport (minimal)

Create a minimal infra passport, for example `cluster-01-infra.yml`, with only the `cloud` and
`global` sections (cluster connectivity + observability):

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
#   dbaas, maas, storage, core, zookeeper
```

Update the infra environment's `env_definition.yml` to reference the infra passport explicitly:

```yaml
# cluster-01/env-infra/Inventory/env_definition.yml
inventory:
  environmentName: env-infra
  cloudPassport: cluster-01-infra    # explicit, resolves cluster-01-infra.yml
```

### 3. Verify the result

Regenerate the affected environments and inspect the generated
[Cloud](/docs/envgene-objects.md#cloud) object for each:

- The business environment's Cloud object contains keys from the business passport
  (`cloud + dbaas + maas + storage + core + global`). Inline traceability comments reference
  `cloud passport: <cluster-name> version: <passport-version>`.
- The infra environment's Cloud object contains only the keys from the infra passport
  (`cloud + global`). Inline traceability comments reference
  `cloud passport: <cluster-name>-infra version: <passport-version>`.

If the infra environment's Cloud object still contains business-only keys, recheck that the
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
    │                                           receives: cloud + dbaas + maas + storage + core + global
    │
    └── env-infra/                ← INFRA env
        └── Inventory/
            └── env_definition.yml           ← cloudPassport: cluster-01-infra (explicit)
                                                resolves: cluster-01-infra.yml
                                                receives: cloud + global only
```

Existing business environments continue to work without modification. Auto-association keeps
resolving the cluster default passport, and their effective parameter set is unchanged.

## Related documentation

- [Cloud Passport processing](/docs/features/cloud-passport-processing.md)
- [Creating a cluster](/docs/how-to/create-cluster.md)
- [EnvGene Configs: `env_definition.yml`](/docs/envgene-configs.md#env_definitionyml)
- [EnvGene Objects: Cloud Passport](/docs/envgene-objects.md#cloud-passport)
