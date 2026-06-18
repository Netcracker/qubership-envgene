# Migrate CMDB environments to EnvGene

- [Migrate CMDB environments to EnvGene](#migrate-cmdb-environments-to-envgene)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [1. Export the CMDB configuration](#1-export-the-cmdb-configuration)
  - [2. Build the environment template](#2-build-the-environment-template)
    - [2.1 Identify the environment types](#21-identify-the-environment-types)
    - [2.2 Create environment template per environment type](#22-create-environment-template-per-environment-type)
  - [3. Create the environment inventories](#3-create-the-environment-inventories)
    - [3.1 Create the cluster folders](#31-create-the-cluster-folders)
    - [3.2 Create the Cloud Passport](#32-create-the-cloud-passport)
    - [3.3 Identify the environments](#33-identify-the-environments)
    - [3.4 Create inventory per environment](#34-create-inventory-per-environment)
    - [3.5 Attach cloud inline parameters](#35-attach-cloud-inline-parameters)
    - [3.6 Attach cloud referenced ParameterSets](#36-attach-cloud-referenced-parametersets)
    - [3.7 Attach cloud application parameters](#37-attach-cloud-application-parameters)
    - [3.8 Attach the cloud Resource Profile Override](#38-attach-the-cloud-resource-profile-override)
    - [3.9 Attach namespace inline parameters](#39-attach-namespace-inline-parameters)
    - [3.10 Attach namespace referenced ParameterSets](#310-attach-namespace-referenced-parametersets)
    - [3.11 Attach namespace application parameters](#311-attach-namespace-application-parameters)
    - [3.12 Attach the namespace Resource Profile Override](#312-attach-the-namespace-resource-profile-override)
    - [3.13 Export the credentials](#313-export-the-credentials)
    - [3.14 Create the Artifact Definition](#314-create-the-artifact-definition)
  - [4. Run generation to verify](#4-run-generation-to-verify)

## Description

This guide moves CMDB environments to EnvGene as a lift-and-shift. The guide has two phases, do them in order:

1. Build one template per environment type.
2. Create an inventory for each environment, copying parameters from CMDB as they are.

Refactoring parameters is out of scope of this guide.

## Prerequisites

1. A template and instance repositories, provided to you, already set up with the EnvGene pipeline.
2. Access to each CMDB instance (URL, username, and token) and the [deploycli](<add link>)
3. In the cloud CMDB, create an Application Definition for the env-template artifact according to
  [guideline](<add link>). The recommended Application Definition values are:

<add text>

## 1. Export the CMDB configuration

Produce the file export with the deploycli. The tool needs the CMDB URL, a username, and a token:

```bash
<deploycli-binary> config export tenants --all \
--url=$CMDB_URL \
--auth=$CMDB_USERNAME:$CMDB_TOKEN \
-t ./cmdb-export-tenants <tenant-name>
```

> [!NOTE]
> The configuration can span several CMDB instances/tenants. Run the export against each one. This guide follows
> a single export, but the steps are the same for several.

Then validate the export. **Remove stale or leftover Clouds and Namespaces that are no longer in use**: delete their
folders under `Tenants/<tenant>/Clouds/` so they are not migrated or considered in the following steps.

## 2. Build the environment template

### 2.1 Identify the environment types

List the environment types in the project from the solution topologies you run. A type is the set of
namespaces, by their `deployPostfix`, that a solution deploys. For example a composite (a baseline namespace
plus satellites) and a non-composite one.

### 2.2 Create environment template per environment type

Start from the template [starter set](/docs/cmdb-migration/templates/). It ships the cloud and tenant templates,
a namespace template to clone, a composite structure template, and two
descriptors: [`single.yaml`](/docs/cmdb-migration/templates/env_templates/single.yaml) for a non-composite type
and [`composite.yaml`](/docs/cmdb-migration/templates/env_templates/composite.yaml) for a composite one.

Do this for each environment type from 2.1:

1. Copy the starter set into the template repository under `templates/`. Keep the descriptor for each type you
   have, `single.yaml` or `composite.yaml` or both, and remove any unused one.

2. Clone one namespace template per `deployPostfix` in the type. Copy the namespace template from
   [`env_templates/namespaces`](/docs/cmdb-migration/templates/env_templates/namespaces/) to
   `templates/env_templates/namespaces/<deployPostfix>.yml.j2`, then replace `<deployPostfix>` in `name` so it
   renders to the real namespace name. **The rendered `name` must match the real namespace**.

   > [!NOTE]
   > If your namespace names do not follow the `{{ current_env.name }}-<deployPostfix>` pattern, that is out of
   > scope for this guide. Contact the EnvGene team to work out that case.

3. In the descriptor, list one `template_path` entry per namespace template. Replace each placeholder with the
   namespace `deployPostfix`, and add or remove rows to match the namespace count.

4. Composite type only: in the copied
   [`composite-structure.yml.j2`](/docs/cmdb-migration/templates/env_templates/common/composite-structure.yml.j2),
   set `baseline` to the baseline namespace and add one `satellites` entry per satellite, matching the export
   `Tenants/<tenant>/Clouds/<cloud>/CompositeStructures/<name>.yml`. Replace the `<baseline-deployPostfix>` and
   `<satellite-deployPostfix-N>` placeholders.

5. Add the Application Definitions and Registry Definitions the templates need, then parameterize the registry.

   - From the [centralized definitions repository](<add link>), collect an AppDef for every application your
   solutions deploy.
   - Collect the RegDefs that those AppDefs reference.
   - Place each AppDef at `templates/appdefs/<application-name>.yml.j2` and each RegDef at
   `templates/regdefs/<registry-name>.yml.j2`. The `.yml.j2` extension marks them as templates.
   - In each AppDef, replace the hardcoded `registryName` with
   `{{ appdefs.overrides.registryName | default('<original-registry>') }}`.

6. Commit and publish the template artifact. Note its `name:version` for the inventory.

## 3. Create the environment inventories

### 3.1 Create the cluster folders

Go through the Clouds in the CMDB export. Each Cloud is `Tenants/<tenant>/Clouds/<cloud>/`, with its record at
`<cloud>.yml`. For each Cloud, read `apiUrl` from that record and derive the cluster name: take the host, drop
the `api.` prefix and the base domain. Create the folder `/environments/<cluster>/` in instance repository.

For example, `https://api.cluster-01.example.com:6443` gives `/environments/cluster-01/`.

Several Clouds can share one `apiUrl`, which means they sit on the same cluster. Deduplicate by cluster: create
each `/environments/<cluster>/` folder once, however many Clouds map to it.

### 3.2 Create the Cloud Passport

Do this once per cluster.

> [!NOTE]
> This is a minimal Cloud Passport. If you already have a Cloud Passport for the cluster, use it instead.

Copy the [Cloud Passport example](/docs/cmdb-migration/environments/cluster-01/cloud-passport/cloud-passport.yml) to
`environments/<cluster>/cloud-passport/<cluster>.yml`.

Fill the `cloud` block of `<cluster>.yml` from the Cloud record `<cloud>.yml`. Each value below is the source
attribute to copy:

```yaml
cloud:
  CLOUD_API_HOST: <Cloud.apiUrl>
  CLOUD_API_PORT: "<Cloud.apiPort>"
  CLOUD_PRIVATE_HOST: <Cloud.privateUrl>
  CLOUD_PUBLIC_HOST: <Cloud.publicUrl>
  CLOUD_DASHBOARD_URL: <Cloud.dashboardUrl>
  CLOUD_DEPLOY_TOKEN: <Cloud.defaultCredentialsId>
```

Copy the
[Cloud Passport credentials example](/docs/cmdb-migration/environments/cluster-01/cloud-passport/cloud-passport-creds.yml)
to `environments/<cluster>/cloud-passport/<cluster>-creds.yml`.

Copy only the attributes shown above for now. Other cloud parameters move in
[Refactor migrated parameters](/docs/cmdb-migration/refactor-migrated-parameters.md).

> [!NOTE]
> `defaultCredentialsId` (the `CLOUD_DEPLOY_TOKEN`) can differ between Clouds on the same cluster. One
> cluster-wide passport holds a single token. If the environments need different deploy tokens, that is out of
> scope for this guide. Contact the EnvGene team to work out that case.

### 3.3 Identify the environments

Identify the environments in the export from your knowledge of the project. A Cloud may hold one environment or
several. Each environment is a set of namespaces on the cluster you derived in 3.1, and matches one of the types
from 2.1.

### 3.4 Create inventory per environment

For each environment from 3.3, create a folder named after the environment under its cluster,
`environments/<cluster>/<env>/`. Put the
[Environment Inventory example](/docs/cmdb-migration/environments/cluster-01/env-1/Inventory/env_definition.yml)
into it as `Inventory/env_definition.yml`, then fill in:

- `envTemplate.name`: the template name for the environment's type (`single` or `composite`).
- `envTemplate.artifact`: the template artifact `name:version` you published in 2.2.

### 3.5 Attach cloud inline parameters

For each non-empty inline parameters attribute on the Cloud record
`Tenants/<tenant>/Clouds/<cloud>/<cloud>.yml`, create a ParameterSet under
`environments/<cluster>/<env>/Inventory/parameters/`, copy the attribute's contents into the ParameterSet
`parameters`, and name the file by context. Then reference it as a list under the `cloud` key in the matching
field of `env_definition.yml`:

- `deployParameters` to `cloud-deploy.yml`, referenced in `envSpecificParamsets`.
- `e2eParameters` to `cloud-e2e.yml`, referenced in `envSpecificE2EParamsets`.
- `technicalConfigurationParameters` to `cloud-tech.yml`, referenced in `envSpecificTechnicalParamsets`.

For example:

```yaml
envTemplate:
  envSpecificParamsets:
    cloud:
      - cloud-deploy
```

### 3.6 Attach cloud referenced ParameterSets

For each ParameterSet name listed in `deployParameterSets`, `e2eParameterSets`, or
`technicalConfigurationParameterSets` on the Cloud record, copy the source file
`Tenants/<tenant>/ParameterSets/<name>.yml` to `environments/<cluster>/<env>/Inventory/parameters/<name>.yml`,
keeping its name. Then reference it under the `cloud` key in the field for its context, the same way as in 3.5.

### 3.7 Attach cloud application parameters

The Cloud holds Application objects under `Tenants/<tenant>/Clouds/<cloud>/Applications/`. Each Application has a
`name` and per-application `deployParameters` and `technicalConfigurationParameters`. Collect these across all
cloud Applications into one ParameterSet per context, under the ParameterSet `applications` section keyed by the
Application `name`. Create them under `environments/<cluster>/<env>/Inventory/parameters/`, name the files by
context, and reference them under the `cloud` key, the same way as in 3.5:

- `deployParameters` to `cloud-app-deploy.yml`, referenced in `envSpecificParamsets`.
- `technicalConfigurationParameters` to `cloud-app-tech.yml`, referenced in `envSpecificTechnicalParamsets`.

Skip a context when no cloud Application has parameters for it. For example, `cloud-app-deploy.yml`:

```yaml
name: cloud-app-deploy
parameters: {}
applications:
  - appName: Cloud-Core
    parameters:
      GW_INGRESS_ANNOTATIONS: "nginx.ingress.kubernetes.io/proxy-body-size: '800m'"
```

### 3.8 Attach the cloud Resource Profile Override

If the Cloud record has a `profile`, copy the referenced profile from the export
`Tenants/<tenant>/Profiles/<profile-name>.yml` to
`environments/<cluster>/<env>/Inventory/resource_profiles/<profile-name>.yml`, keeping its name. Then reference
it by name, without the `.yml` extension, as a single value under the `cloud` key in `envSpecificResourceProfiles`:

```yaml
envTemplate:
  envSpecificResourceProfiles:
    cloud: <profile-name>
```

### 3.9 Attach namespace inline parameters

Do this for each namespace in the environment, reading from the Namespace record
`Tenants/<tenant>/Clouds/<cloud>/Namespaces/<namespace>/<namespace>.yml`. This mirrors 3.5, but the reference
key is the namespace `deployPostfix` instead of `cloud`.

For each non-empty inline parameters attribute, create a ParameterSet under
`environments/<cluster>/<env>/Inventory/parameters/`, copy the attribute's contents into the ParameterSet
`parameters`, and name the file by namespace and context:

- `deployParameters` to `<deployPostfix>-deploy.yml`, referenced in `envSpecificParamsets`.
- `e2eParameters` to `<deployPostfix>-e2e.yml`, referenced in `envSpecificE2EParamsets`.
- `technicalConfigurationParameters` to `<deployPostfix>-tech.yml`, referenced in
  `envSpecificTechnicalParamsets`.

For example, for a namespace with `deployPostfix` `bss`:

```yaml
envTemplate:
  envSpecificParamsets:
    bss:
      - bss-deploy
```

### 3.10 Attach namespace referenced ParameterSets

For each ParameterSet name listed in `deployParameterSets`, `e2eParameterSets`, or
`technicalConfigurationParameterSets` on the Namespace record, copy the source file
`Tenants/<tenant>/ParameterSets/<name>.yml` to `environments/<cluster>/<env>/Inventory/parameters/<name>.yml`,
keeping its name. Then reference it under the `<deployPostfix>` key in the field for its context, as in 3.9.

### 3.11 Attach namespace application parameters

Do this for each namespace, reading its Application objects from
`Tenants/<tenant>/Clouds/<cloud>/Namespaces/<namespace>/Applications/`. This mirrors 3.7, but the reference key
is the namespace `deployPostfix` instead of `cloud`, and the file names carry the postfix:

- `deployParameters` to `<deployPostfix>-app-deploy.yml`, referenced in `envSpecificParamsets`.
- `technicalConfigurationParameters` to `<deployPostfix>-app-tech.yml`, referenced in
  `envSpecificTechnicalParamsets`.

Collect the parameters of all the namespace Applications into the ParameterSet `applications` section, keyed by
the Application `name`. Skip a context when no Application has parameters for it.

### 3.12 Attach the namespace Resource Profile Override

If the Namespace record has a `profile`, copy the referenced profile from the export
`Tenants/<tenant>/Profiles/<profile-name>.yml` to
`environments/<cluster>/<env>/Inventory/resource_profiles/<profile-name>.yml`, keeping its name. Then reference
it by name, without the `.yml` extension, as a single value under the `<deployPostfix>` key in
`envSpecificResourceProfiles`:

```yaml
envTemplate:
  envSpecificResourceProfiles:
    bss: dev_bss_override
```

### 3.13 Export the credentials

<add text>

### 3.14 Create the Artifact Definition

Once per instance repository, copy the
[Artifact Definition example](/docs/cmdb-migration/configuration/artifact_definitions/) to
`configuration/artifact_definitions/<artifact-name>.yaml`, then fill it in to match the Application Definition
you created in Prerequisites step 3:

- `name` and `artifactId`: set both to that Application Definition's name. If you changed it in the
  prerequisites, change it here too. It must also equal the `application` part of the `envTemplate.artifact` you
  set in 3.4, so the two match.
- `groupId`, `registry`, and `mavenConfig`: use the same values as that Application Definition.

The file name must equal this `name`.

## 4. Run generation to verify

Trigger the instance pipeline to confirm the environment generates.

| Parameter                | Value                        |
|--------------------------|------------------------------|
| `ENV_NAMES`              | `<cluster>/<env>`            |
| `ENV_BUILDER`            | `true`                       |
| `GENERATE_EFFECTIVE_SET` | `true`                       |
| `SD_SOURCE_TYPE`         | `json`                       |
| `SD_DATA`                | `<solution-descriptor-yaml>` |

After the pipeline commits, open `environments/<cluster>/<env>/cloud.yml` and
`Namespaces/<deploy-postfix>/namespace.yml`. Confirm the values match the CMDB source. Each generated value
carries a comment naming its source. The Effective Set under `effective-set/` lists the applications from the
Full Solution Descriptor passed in `SD_DATA`. For the SD pipeline inputs, see
[Generate an Effective Set](/docs/how-to/generate-effective-set.md).
