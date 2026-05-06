# Cloud Passport Auto-Association in Mixed Clusters

- [Cloud Passport Auto-Association in Mixed Clusters](#cloud-passport-auto-association-in-mixed-clusters)
  - [What You Will Learn](#what-you-will-learn)
  - [Prerequisites](#prerequisites)
  - [Scenario](#scenario)
  - [Step 1: Understand What a Cloud Passport Is](#step-1-understand-what-a-cloud-passport-is)
  - [Step 2: See How Environments Share a Cluster](#step-2-see-how-environments-share-a-cluster)
  - [Step 3: Check How a Passport Is Resolved (Explicit vs Auto-Association)](#step-3-check-how-a-passport-is-resolved-explicit-vs-auto-association)
    - [3.1 Path 1 - Explicit Association](#31-path-1---explicit-association)
    - [3.2 Path 2 - Auto-Association](#32-path-2---auto-association)
    - [3.3 Resolution Summary](#33-resolution-summary)
  - [Step 4: Inspect What the Passport Contributes to an Environment](#step-4-inspect-what-the-passport-contributes-to-an-environment)
    - [4.1 Named Sections](#41-named-sections)
    - [4.2 Other Sections](#42-other-sections)
    - [4.3 Merge Behavior](#43-merge-behavior)
  - [Step 5: Use Traceability to See Where Values Came From](#step-5-use-traceability-to-see-where-values-came-from)
  - [Step 6: Decide What Is Safe at Cluster-Level vs Per-Environment](#step-6-decide-what-is-safe-at-cluster-level-vs-per-environment)
    - [6.1 Safe to Place at Cluster Level](#61-safe-to-place-at-cluster-level)
    - [6.2 Keep Out of the Cluster-Level Passport](#62-keep-out-of-the-cluster-level-passport)
  - [Step 7: Configure Environment-Specific Passports](#step-7-configure-environment-specific-passports)
    - [7.1 When to Use Environment-Specific Passports](#71-when-to-use-environment-specific-passports)
    - [7.2 Configure the Business Passport (Default)](#72-configure-the-business-passport-default)
    - [7.3 Configure the Infra Passport (Explicit)](#73-configure-the-infra-passport-explicit)
    - [Result](#result)
    - [7.4 Mixed Cluster Result](#74-mixed-cluster-result)
  - [Summary](#summary)

## What You Will Learn

By the end of this tutorial you will be able to:

- Explain how Cloud Passport auto-association works in EnvGene.
- Predict which passport a given environment will resolve in a mixed cluster.
- See exactly what a passport contributes to an environment's deployment context.
- Use traceability comments to find the source of any passport-derived parameter.
- Decide which parameters belong in a **cluster-level** passport vs **environment-specific** passports.
- Configure **separate passports for business and infra environments** in one cluster without breaking existing business envs.

## Prerequisites

- An instance repository with at least one cluster:
  - `/environments/<cluster-name>/`

- At least two environments in that cluster:
  - one **business** environment (for example `env-business-payments`)
  - one **infra** environment (for example `env-infra-monitoring`)

- For each environment, an `env_definition.yml`:
  - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`

- Basic familiarity with:
  - [`env_definition.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-configs.md#env_definitionyml)
  - [Cloud Passport object](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud-passport)
  - [Cloud object (`cloud.yml`)](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)

You do **not** need to change code for this tutorial; all steps are about configuration and understanding behaviour.

## Scenario

You have a cluster `cluster-01` that hosts:

- **Business environments** — application workloads
- **Infra environments** — platform workloads

You want:

- Business environments to keep using a **rich, default Cloud Passport** via auto-association.
- Infra environments to use a **minimal passport** that does not contain business-only parameters.
- A clear understanding of how auto-association works and where parameters end up.

## Step 1: Understand What a Cloud Passport Is

First, open the cluster-level `cloud-passport/` folder:

```text
<instance-repo>/
└── environments/
    └── cluster-01/
        └── cloud-passport/
            ├── cluster-01.yml
            └── cluster-01-creds.yml
```

Inspect cluster-01.yml. It is a YAML document with a version and a set of sections, each a flat map of keys:

Example passport:

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

**Key idea:**

This single file is the **central place** where cluster-specific deployment parameters are defined. Later steps will show how these sections flow into an environment.

## Step 2: See How Environments Share a Cluster

In the same cluster-01 directory, list environments:

```text
cluster-01/
├── cloud-passport/
│   ├── cluster-01.yml
│   └── cluster-01-creds.yml
├── env-business-payments/
│   └── Inventory/
│       └── env_definition.yml
└── env-infra-monitoring/
    └── Inventory/
        └── env_definition.yml
```

Open each `env_definition.yml`:

```yaml
# cluster-01/env-business-payments/Inventory/env_definition.yml
inventory:
  environmentName: env-business-payments
  tenantName: tenant
  # Note: no cloudPassport field

# cluster-01/env-infra-monitoring/Inventory/env_definition.yml
inventory:
  environmentName: env-infra-monitoring
  tenantName: infra-ops
  # For now also without cloudPassport - we will change this in Step 7
```

At this point, both envs are in the **same cluster** and both can auto-resolve the same passport. The rest of the tutorial explains how that resolution works and how to separate them safely.

## Step 3: Check How a Passport Is Resolved (Explicit vs Auto-Association)

Every environment build needs to decide which passport to use (if any). That decision is based only on `env_definition.yml`.

### 3.1 Path 1 - Explicit Association

If `env_definition.yml` has `inventory.cloudPassport`, that name is used:

```yaml
# <cluster>/<env>/Inventory/env_definition.yml
inventory:
  environmentName: env-01
  tenantName: tenant
  cloudPassport: cluster-01    # system resolves this exact passport
```

Resolution behavior:

- The system searches for `<name>.yml` starting at the environment folder and moving upwards to the repository root.
- The first matching file is chosen.

### 3.2 Path 2 - Auto-Association

If `inventory.cloudPassport` is absent, auto-association is used:

```yaml
inventory:
  environmentName: env-01
  tenantName: tenant
  # no cloudPassport field → auto-association applies
```

Resolution behavior:

- Look for `cloud-passport/<cluster-name>.yml`
- If missing, look for `passport.yml`
- If neither exists, no passport is applied.

### 3.3 Resolution Summary

| Case       | Behavior                   |
| ---------- | -------------------------- |
| Explicit   | Uses named passport        |
| Auto       | Uses cluster default       |
| None found | Continues without passport |

In the current state of the scenario, both envs would auto-associate the same cluster-01.yml. The next steps show the impact of this.

## Step 4: Inspect What the Passport Contributes to an Environment

In this step you look at the generated Cloud object and see what the passport actually adds.

After running an environment build for env-business-payments, open its generated cloud.yml (path depends on your instance layout, see [Cloud object docs](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud)).

### 4.1 Named Sections

Confirm that these passport sections have been mapped to specific parts of `cloud.yml`:

| Passport section | Destination in [`cloud.yml`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#cloud) | What it configures |
| --- | --- | --- |
| `cloud` | Top-level connectivity fields | API host, port, protocol, dashboard URL, deploy token, production mode flag |
| `dbaas` | `dbaasConfigs` block | Database aggregator URL, API address, credentials reference |
| `maas` | `maasConfig` block | Message broker internal and external addresses, credentials reference |
| `consul` | `consulConfig` block | Consul URL, enabled flag, admin token reference |
| `vault` | `vaultConfig` block | Vault URL, enabled flag, credentials reference |

These fields are populated from the passport and then participate in further merges.

### 4.2 Other Sections

Now look for parameters derived from other sections such as `storage`, `global`, `bss`, `core`, `zookeeper`, etc.

All keys from these sections are merged flat into deployParameters in cloud.yml. That means:

Every key defined in `storage`, `core`, `bss`, etc. becomes a top-level deployment parameter.
There is no additional filtering by section name at this stage.
This is the behaviour that can leak **business-only keys into infra environments** if they share the same passport.

### 4.3 Merge Behavior

Keep in mind:

- Passport values are written into the Cloud object during the build.
- Later, higher-priority sources may override them, but all passport keys are present initially.
- For mixed clusters, this means every environment that resolves a given passport will see all its sections unless you introduce separation (Step 7).

## Step 5: Use Traceability to See Where Values Came From

```yaml
STORAGE_SERVER_URL: https://minio.cluster-01.qubership.org  # cloud passport: cluster-01 version: 1.5
MONITORING_ENABLED: "true"                                  # cloud passport: cluster-01 version: 1.5
```

This tells you:

- Parameter was written from a Cloud Passport.
- Which passport file was used (`cluster-01`).
- Which version of the passport file contributed the value.
If your infra environment is failing due to an unexpected parameter, traceability makes it clear that the value came from the cluster-level passport, not from env-specific config.

## Step 6: Decide What Is Safe at Cluster-Level vs Per-Environment

Now that you understand where values go, you can decide what to keep at cluster scope and what to move into env-specific passports.

### 6.1 Safe to Place at Cluster Level

These sections are generally safe to share between **business** and **infra** environments because they describe cluster-wide infrastructure:

| Section | Example parameters | Why safe for all env types |
| --- | --- | --- |
| `cloud` | `CLOUD_API_HOST`, `CLOUD_API_PORT`, `CLOUD_DEPLOY_TOKEN`, `CLOUD_PROTOCOL` | Required by all deployers to connect to the cluster |
| `global` | `MONITORING_ENABLED`, `TRACING_ENABLED`, `TRACING_HOST` | Observability switches applicable to all workload types |
| `consul` | `CONSUL_URL`, `CONSUL_ENABLED` | Safe when all environments in the cluster use Consul |
| `vault` | `VAULT_URL`, `VAULT_ENABLED` | Safe when all environments use Vault for secrets management |

### 6.2 Keep Out of the Cluster-Level Passport

These sections contain parameters that are meaningful only to specific workload types. When placed at cluster level, they are inherited by all environments regardless of workload type:

| Section | Example parameters | Intended for |
| --- | --- | --- |
| `bss` | `DOC_STORAGE_TEMPORARY_BUCKET_NAME`, `DOC_STORAGE_PERSISTENT_BUCKET_NAME` | Business applications only |
| `core` | `DEFAULT_TENANT_ADMIN_LOGIN`, `DEFAULT_TENANT_ADMIN_PASSWORD`, `MAVEN_REPO_URL` | Business application runtime |
| `storage` | `STORAGE_SERVER_URL`, `STORAGE_PROVIDER`, `CDN_STORAGE_*`, `DOC_STORAGE_*` | Business application object storage |
| `maas` | `MAAS_SERVICE_ADDRESS`, `MAAS_CREDENTIALS_USERNAME` | Business application message broker |
| `dbaas` | `API_DBAAS_ADDRESS`, `DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME` | Business application database provisioning |
| `zookeeper` | `ZOOKEEPER_ADDRESS`, `ZOOKEEPER_URL` | Business application coordination service |

## Step 7: Configure Environment-Specific Passports

In this step you will:

- Keep auto-association for business envs (no cloudPassport field required).
- Introduce a minimal infra passport and reference it explicitly.

### 7.1 When to Use Environment-Specific Passports

Use this pattern when:

- One cluster hosts both business and infra environments.
- Business envs need a rich parameter set (DBaaS, MaaS, storage, BSS).
- Infra envs should use only cluster connectivity + observability, not business-specific keys.

You will end up with two passport files in cloud-passport/:

```text
environments/
└── cluster-01/
    └── cloud-passport/
        ├── cluster-01.yml            ← business passport — full parameter set
        ├── cluster-01-creds.yml
        ├── cluster-01-infra.yml      ← infra passport — minimal parameter set
        └── cluster-01-infra-creds.yml
```

### 7.2 Configure the Business Passport (Default)

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

Business environments keep using auto-association:

```yaml
# cluster-01/env-business-payments/Inventory/env_definition.yml
inventory:
  environmentName: env-business-payments
  tenantName: tenant
  # cloudPassport field absent → auto-association resolves cluster-01.yml
```

### 7.3 Configure the Infra Passport (Explicit)

Now create a minimal infra passport, for example `cluster-01-infra.yml`, containing only cluster-wide infra-safe parameters:

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

Then change the infra environment’s env_definition.yml to explicitly request this passport:

```yaml
# cluster-01/env-infra-monitoring/Inventory/env_definition.yml
inventory:
  environmentName: env-infra-monitoring
  tenantName: infra-ops
  cloudPassport: cluster-01-infra   # resolves cluster-01-infra.yml
```

### Result

- Infra uses minimal config and it will no longer auto-associates the full business passport.
- It receives only the minimal, infra-safe subset.
- Business remains unchanged.

### 7.4 Mixed Cluster Result

After these changes, your cluster layout looks like this:

```text
cluster-01/
├── cloud-passport/
│   ├── cluster-01.yml           ← default passport for business envs (auto-association)
│   ├── cluster-01-creds.yml
│   ├── cluster-01-infra.yml     ← explicit infra passport
│   └── cluster-01-infra-creds.yml
│
├── env-business-payments/
│   └── Inventory/
│       └── env_definition.yml   ← no cloudPassport → uses cluster-01.yml
│
└── env-infra-monitoring/
    └── Inventory/
        └── env_definition.yml   ← cloudPassport: cluster-01-infra
```

- Business envs (no cloudPassport) continue to use cluster-01.yml via auto-association.
- Infra envs explicitly use cluster-01-infra.yml.
- Backward compatibility for existing business envs is preserved.
- Infra envs stop inheriting business-only parameters.

## Summary

In this tutorial, you:

- Learned how Cloud Passport resolution works, with and without `inventory.cloudPassport`
- Saw how all sections of a passport are merged into the Cloud object and deployment parameters
- Used traceability comments to confirm which values come from which passport
- Classified which sections are safe at cluster level and which should be scoped to business-only
- Implemented a practical pattern for mixed clusters:
  - Business environments keep default auto-association
  - Infra environments use an explicit minimal passport
