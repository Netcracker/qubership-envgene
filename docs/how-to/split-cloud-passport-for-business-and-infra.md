# Split a Cloud Passport for business and infra environments

- [Split a Cloud Passport for business and infra environments](#split-a-cloud-passport-for-business-and-infra-environments)
  - [Overview](#overview)
  - [When to use this pattern](#when-to-use-this-pattern)
  - [Layout](#layout)
  - [Steps](#steps)
    - [1. Configure the business passport (default)](#1-configure-the-business-passport-default)
    - [2. Configure the infra passport](#2-configure-the-infra-passport)
    - [3. Verify the result](#3-verify-the-result)
  - [Related documentation](#related-documentation)

## Overview

When a single cluster hosts both business application environments and infrastructure (infra)
environments, the two workload types may need different parameter sets. The business workloads
depend on full database, messaging, and storage parameters. The infra workloads only need
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
            ├── passport.yml              ← business passport (full parameter set)
            ├── passport-creds.yml        ← credentials for the business passport
            ├── passport-infra.yml        ← infra passport (minimal parameter set)
            └── passport-infra-creds.yml  ← credentials for the infra passport
```

Business environments resolve the first file via auto-association. Infra environments reference
the second file explicitly via the `cloudPassport` field in their `env_definition.yml`.

## Steps

### 1. Configure the business passport (default)

Keep the business passport as `passport.yml`. It is the cluster default. Business environments leave
`inventory.cloudPassport` unset, and auto-association resolves `passport.yml`.

Copy the sample and replace the values:

- [passport.yml](/docs/samples/infra-and-business-environments/instance-repository/environments/cluster-01/cloud-passport/passport.yml)
- [passport-creds.yml](/docs/samples/infra-and-business-environments/instance-repository/environments/cluster-01/cloud-passport/passport-creds.yml)

EnvGene reads the credentials of a passport from `<passport-name>-creds.yml`, next to the passport.

```yaml
# cluster-01/env-business/Inventory/env_definition.yml
inventory:
  noCmdbVersion: "v2"
  # cloudPassport field absent. Auto-association resolves passport.yml.
```

### 2. Configure the infra passport

Create `passport-infra.yml` with only the parameters the infra environment needs. The sample keeps cluster
connectivity. Infra environments set `inventory.cloudPassport` to `passport-infra`.

Copy the sample and replace the values:

- [passport-infra.yml](/docs/samples/infra-and-business-environments/instance-repository/environments/cluster-01/cloud-passport/passport-infra.yml)
- [passport-infra-creds.yml](/docs/samples/infra-and-business-environments/instance-repository/environments/cluster-01/cloud-passport/passport-infra-creds.yml)

```yaml
# cluster-01/env-infra/Inventory/env_definition.yml
inventory:
  noCmdbVersion: "v2"
  cloudPassport: passport-infra
```

For the inventories and the `ENV_INVENTORY_CONTENT` values, see
[Infra and business environments samples](/docs/samples/infra-and-business-environments/README.md).

### 3. Verify the result

Regenerate the affected environments and inspect the generated
[Cloud](/docs/envgene-objects.md#cloud) object for each:

- The business environment's Cloud object contains the keys from `passport.yml`. Inline traceability comments
  name that passport.
- The infra environment's Cloud object contains the keys from `passport-infra.yml`, and not the keys that exist
  only on the business passport. Inline traceability comments name `passport-infra`.

If the infra environment's Cloud object still contains business-only keys, recheck that the
`cloudPassport` field is set to the infra passport name and that the infra passport file exists
in the expected directory.

## Related documentation

- [Cloud Passport processing](/docs/features/cloud-passport-processing.md)
- [Create a cluster](/docs/how-to/create-cluster.md)
- [Infra and business environments samples](/docs/samples/infra-and-business-environments/README.md)
- [EnvGene Configs: `env_definition.yml`](/docs/envgene-configs.md#env_definitionyml)
- [EnvGene Objects: Cloud Passport](/docs/envgene-objects.md#cloud-passport)
