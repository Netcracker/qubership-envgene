# Migrate CMDB environments to EnvGene

- [Migrate CMDB environments to EnvGene](#migrate-cmdb-environments-to-envgene)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [1. Build the environment template](#1-build-the-environment-template)
    - [1.1 Group namespaces into environments by Solution Descriptor](#11-group-namespaces-into-environments-by-solution-descriptor)
    - [1.2 Create one template per deploy postfix set](#12-create-one-template-per-deploy-postfix-set)
  - [2. Create the environment inventories](#2-create-the-environment-inventories)
    - [2.1 Create the Cloud Passport](#21-create-the-cloud-passport)
    - [2.2 Create one inventory per environment](#22-create-one-inventory-per-environment)
    - [2.3 Attach cloud-level inputs](#23-attach-cloud-level-inputs)
    - [2.4 Attach namespace-level inputs](#24-attach-namespace-level-inputs)
    - [2.5 Export tenant credentials](#25-export-tenant-credentials)
    - [2.6 Add the Solution Descriptor](#26-add-the-solution-descriptor)
    - [2.7 Run generation to verify](#27-run-generation-to-verify)
  - [Field mapping](#field-mapping)
  - [Troubleshoot common errors](#troubleshoot-common-errors)
  - [Results](#results)

## Description

This guide moves CMDB environments to EnvGene as a lift-and-shift. Work through sections 1 and 2 in order:

1. Build one template per environment shape.
2. Create an inventory for each environment, copying parameters as they are.

Copying the parameters as they are gets each environment generating from a template fast. Cleaning them up is a
separate guide: [Refactor migrated parameters](/docs/cmdb-migration/refactor-migrated-parameters.md). Do not
refactor before generation works.

The source is a file export of CMDB objects with the folder layout
`Tenants/<tenant>/Clouds/<cloud>/Namespaces/<namespace>/`. A generic blank for every file you create lives next
to this guide under [blanks](/docs/cmdb-migration/blanks/). Copy a blank as-is, then fill in your values.

## Prerequisites

- A template repository and a region instance repository, provided to you, already set up with the EnvGene
  pipeline. There is one instance repository per region, and each cluster belongs to one region. The region is
  derived from the cluster URL.
- A file export of the CMDB objects for the environments you migrate.
- A Solution Descriptor for each solution instance. It lists the applications and their `deployPostfix` values.

> [!NOTE]
> The cluster-URL-to-region mapping is not yet defined. Use `<region>` as a placeholder until the mapping is
> agreed, then replace it everywhere it appears.

## 1. Build the environment template

### 1.1 Group namespaces into environments by Solution Descriptor

A Solution Descriptor deploys one solution instance into a set of namespaces, each named by its `deployPostfix`.
That set of namespaces is one environment. Read the `deployPostfix` values from each Solution Descriptor to find
the namespaces of each environment.

Environments whose Solution Descriptors cover the same set of `deployPostfix` values use one template. They share
it even when their parameter values or application versions differ. Those differences belong in the inventory,
not the template.

Give the template a short, simple name. EnvGene uses it only as the key the inventory points to, so any clear
label works. This guide uses `dev`. A template with a different set of deploy postfixes just needs a different
name, for example `prod`.

### 1.2 Create one template per deploy postfix set

Create one environment template per distinct set of `deployPostfix` values. Copy the Tenant, Cloud, and Namespace
[blanks](/docs/cmdb-migration/blanks/) as-is, then edit only what these steps list. Put the files under
`templates/env_templates/dev/`, using the name from 1.1.

1. Create one Namespace Template per `deployPostfix` in the set. Copy the
   [Namespace Template blank](/docs/cmdb-migration/blanks/namespace.yml.j2) to
   `templates/env_templates/dev/<deployPostfix>.yml.j2`, naming the file after the namespace `deployPostfix`.
   Then edit:

    - Set `name` so it renders to the real namespace name in the cluster. The common pattern is
      `{{ current_env.name }}-<deployPostfix>`. If your namespaces follow a different rule, set the exact value
      that reproduces the deployed name. The generated `name` must match the real namespace.
    - Set `profile.baseline` and leave `profile.name` empty. An empty override with a baseline is the safe
      default. Add a named override later only if the namespace needs one. For a named override, copy the
      [Resource Profile Override blank](/docs/cmdb-migration/blanks/resource-profile.yml) into
      `templates/resource_profiles/` and point `profile.name` at it.

2. Copy the [Cloud Template blank](/docs/cmdb-migration/blanks/cloud.yml.j2) to
   `templates/env_templates/dev/cloud.yml.j2` unchanged. Connectivity is filled from the Cloud Passport during
   generation. You create the passport in [2.1 Create the Cloud Passport](#21-create-the-cloud-passport).

3. Copy the [Tenant Template blank](/docs/cmdb-migration/blanks/tenant.yml.j2) to
   `templates/env_templates/dev/tenant.yml.j2` unchanged.

4. Copy the [Template Descriptor blank](/docs/cmdb-migration/blanks/template-descriptor.yaml) to
   `templates/env_templates/dev.yaml`. List the tenant, cloud, and one entry per namespace template. The
   namespace file name is the deploy postfix, so you do not set `deploy_postfix` explicitly.

5. Commit and publish the template artifact. Copy the
   [Artifact Definition blank](/docs/cmdb-migration/blanks/artifact-definition.yml) to
   `configuration/artifact_definitions/<name>.yml` so EnvGene can download it, and use its `name:version` in the
   inventory.

## 2. Create the environment inventories

### 2.1 Create the Cloud Passport

Create the Cloud Passport from the Cloud record connectivity fields. Do this once per cluster, before the
environments on it.

- Copy the [Cloud Passport blank](/docs/cmdb-migration/blanks/cloud-passport.yml) to
  `environments/<cluster>/cloud-passport/<cluster>.yml` and fill in the connectivity values.
- Copy the [Cloud Passport credentials blank](/docs/cmdb-migration/blanks/cloud-passport-creds.yml) to
  `environments/<cluster>/cloud-passport/<cluster>-creds.yml`.

Take only the connectivity fields now. Other cloud parameters move in
[Refactor migrated parameters](/docs/cmdb-migration/refactor-migrated-parameters.md). For the field-to-key
mapping, see [Field mapping](#field-mapping).

### 2.2 Create one inventory per environment

Each environment found in 1.1 (one Solution Descriptor) needs one inventory.

For each environment, copy the [Environment Inventory blank](/docs/cmdb-migration/blanks/env_definition.yml) to
`environments/<cluster>/<env>/Inventory/env_definition.yml`. Point it at the Cloud Passport from 2.1 with
`inventory.cloudPassport`, name the template artifact, and list the environment-specific inputs. For the full
field list, see the
[`env_definition.yml` reference](/docs/envgene-configs.md#env_definitionyml).

### 2.3 Attach cloud-level inputs

Read these from the CMDB Cloud record. The inventory key is `cloud` for every cloud-level input.

- **Deploy, e2e, or technical parameters.** Put them in a ParameterSet, one per context, under
  `environments/<cluster>/<env>/Inventory/parameters/<name>.yml`. Link by context in `env_definition.yml`:
  `envSpecificParamsets` for deploy, `envSpecificE2EParamsets` for e2e, `envSpecificTechnicalParamsets` for
  technical, each keyed by `cloud`.
- **Resource Profile Override.** Put it under `environments/<cluster>/<env>/Inventory/resource_profiles/<name>.yml`
  and link it in `env_definition.yml` under `envSpecificResourceProfiles`, keyed by `cloud`.
- **Referenced ParameterSets.** Place each one as above and link it the same way.

Copy the [ParameterSet blank](/docs/cmdb-migration/blanks/paramset.yml) and the
[Resource Profile Override blank](/docs/cmdb-migration/blanks/resource-profile.yml) as starting points.

### 2.4 Attach namespace-level inputs

For each namespace in the environment, read these from the CMDB Namespace record. The inventory key is the
namespace `deployPostfix`.

- **Deploy, e2e, or technical parameters.** Same as the cloud level, keyed by the `deployPostfix`.
- **Resource Profile Override.** Same as the cloud level, keyed by the `deployPostfix`.
- **Referenced ParameterSets.** Same as the cloud level, keyed by the `deployPostfix`.

### 2.5 Export tenant credentials

Export the credentials from the CMDB tenant. Copy the
[Credentials blank](/docs/cmdb-migration/blanks/credentials.yml) to
`environments/<cluster>/<env>/Credentials/credentials.yml`, or to a shared file linked by
`sharedMasterCredentialFiles`. Set each secret value to `envgeneNullValue` until you fill in the real value.

### 2.6 Add the Solution Descriptor

Copy the environment's Solution Descriptor to
`environments/<cluster>/<env>/Inventory/solution-descriptor/sd.yml`. There is one Full Solution Descriptor per
environment. It lists the applications and their `deployPostfix` values. For its structure, see the
[Solution Descriptor object](/docs/envgene-objects.md#solution-descriptor).

### 2.7 Run generation to verify

Trigger the instance pipeline to confirm the environment generates.

| Parameter                | Value             |
|--------------------------|-------------------|
| `ENV_NAMES`              | `<cluster>/<env>` |
| `ENV_BUILD`              | `true`            |
| `GENERATE_EFFECTIVE_SET` | `true`            |

After the pipeline commits, open `environments/<cluster>/<env>/cloud.yml` and
`Namespaces/<deploy-postfix>/namespace.yml`. Confirm the values match the CMDB source. Each generated value
carries a comment naming its source. The Effective Set under `effective-set/` lists the applications from the
Solution Descriptor. For the SD pipeline inputs, see
[Generate an Effective Set](/docs/how-to/generate-effective-set.md).

## Field mapping

Connectivity fields move to the Cloud Passport. EnvGene writes them back into the generated `cloud.yml`, so the
template carries placeholders only. The passport key for each field is fixed.

| CMDB Cloud field       | Cloud Passport key          |
|------------------------|-----------------------------|
| `apiUrl`               | `cloud.CLOUD_API_HOST`      |
| `apiPort`              | `cloud.CLOUD_API_PORT`      |
| `privateUrl`           | `cloud.CLOUD_PRIVATE_HOST`  |
| `publicUrl`            | `cloud.CLOUD_PUBLIC_HOST`   |
| `dashboardUrl`         | `cloud.CLOUD_DASHBOARD_URL` |
| `defaultCredentialsId` | `cloud.CLOUD_DEPLOY_TOKEN`  |
| `protocol`             | `cloud.CLOUD_PROTOCOL`      |
| `productionMode`       | `cloud.PRODUCTION_MODE`     |

These CMDB fields are dropped. They are not part of the EnvGene schema.

| CMDB field  | Reason                    |
|-------------|---------------------------|
| `dirty`     | Internal CMDB state.      |
| `dbMode`    | Deprecated in the schema. |
| `databases` | Deprecated in the schema. |

A CMDB Application record under a Namespace becomes an `applications` entry inside a ParameterSet. EnvGene
generates the Application object from that entry. Prefer the `applications` section over standalone Application
files.

For production environments, set `inventory.config.updateCredIdsWithEnvName: true` so credential IDs are prefixed
with the environment path. This prevents credential collisions across environments.

## Troubleshoot common errors

> [!NOTE]
> Every error below stops the `env_build` or `generate_effective_set` job and reports the failing object.

- **ParameterSet name does not match filename.** The `name` field must equal the filename without the
  extension. Rename the file or change the field.
- **Template Descriptor references a missing file.** The `template_path` is relative to
  `templates/env_templates/`. Confirm the artifact was rebuilt and the path is spelled correctly.
- **Cloud Passport not found.** `env_definition.yml` names the passport in `inventory.cloudPassport`. Place the
  file at `environments/<cluster>/cloud-passport/<name>.yml`.
- **Jinja error, `current_env.cluster` is undefined.** No Cloud Passport resolved, or a passport key name is
  wrong. Confirm the keys are uppercase and prefixed with `CLOUD_`.
- **Schema validation failed on `dirty`.** The CMDB `dirty` field is not in the EnvGene schema. Remove it from
  any file you copied from the export.

## Results

- Each environment regenerates from the template artifact and `env_definition.yml`.
- Cluster connectivity lives in one Cloud Passport, shared by every environment on that cluster.
- A common change is one template version bump, not a per-record edit.
- The parameters are still a literal copy of the CMDB values. Clean them up with
  [Refactor migrated parameters](/docs/cmdb-migration/refactor-migrated-parameters.md).
