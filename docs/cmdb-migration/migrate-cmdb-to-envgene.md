# Migrate CMDB environments to EnvGene

- [Migrate CMDB environments to EnvGene](#migrate-cmdb-environments-to-envgene)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [1. Export the CMDB configuration](#1-export-the-cmdb-configuration)
  - [2. Build the environment template](#2-build-the-environment-template)
    - [2.1 Group environments into types by their Full Solution Descriptors](#21-group-environments-into-types-by-their-full-solution-descriptors)
    - [2.2 Create environment template per environment type](#22-create-environment-template-per-environment-type)
  - [3. Create the environment inventories](#3-create-the-environment-inventories)
    - [3.1 Create the cluster folders](#31-create-the-cluster-folders)
    - [3.2 Create the Cloud Passport](#32-create-the-cloud-passport)
    - [3.3 Identify the environments](#33-identify-the-environments)
    - [3.4 Create one inventory per environment](#34-create-one-inventory-per-environment)
    - [3.5 Attach cloud inline parameters](#35-attach-cloud-inline-parameters)
    - [3.6 Attach cloud referenced ParameterSets](#36-attach-cloud-referenced-parametersets)
    - [3.7 Attach cloud application parameters](#37-attach-cloud-application-parameters)
    - [3.8 Attach the cloud Resource Profile Override](#38-attach-the-cloud-resource-profile-override)
    - [3.9 Attach namespace inline parameters](#39-attach-namespace-inline-parameters)
    - [3.10 Attach namespace referenced ParameterSets](#310-attach-namespace-referenced-parametersets)
    - [3.11 Attach namespace application parameters](#311-attach-namespace-application-parameters)
    - [3.12 Attach the namespace Resource Profile Override](#312-attach-the-namespace-resource-profile-override)
    - [3.13 Export the credentials](#313-export-the-credentials)
    - [3.14 Add the Solution Descriptor](#314-add-the-solution-descriptor)
    - [3.15 Create the Artifact Definition](#315-create-the-artifact-definition)
  - [4. Run generation to verify](#4-run-generation-to-verify)

## Description

This guide moves CMDB environments to EnvGene as a lift-and-shift. The guide has two phases, do them in order:

1. Build one template per environment type.
2. Create an inventory for each environment, copying parameters from CMDB as they are.

Copying the parameters as they are gets each environment generating from a template fast. Cleaning them up is a
separate guide: [Refactor migrated parameters](/docs/cmdb-migration/refactor-migrated-parameters.md).

The source is a file export of CMDB objects with the folder layout
`Tenants/<tenant>/Clouds/<cloud>/Namespaces/<namespace>/`. Many of the files you create have a generic blank
next to this guide under [blanks](/docs/cmdb-migration/blanks/). Copy a blank as-is, then fill in your values.

## Prerequisites

- A template repository and a region instance repository, provided to you, already set up with the EnvGene
  pipeline. There is one instance repository per region, and each cluster belongs to one region. The region is
  derived from the cluster URL.
- Access to each CMDB instance (URL, username, and token) and the CMDB export tool.
- A Solution Descriptor for each solution type. It lists the applications and their `deployPostfix` values.

> [!NOTE]
> The cluster-URL-to-region mapping is not yet defined. Use `<region>` as a placeholder until the mapping is
> agreed, then replace it everywhere it appears.

## 1. Export the CMDB configuration

Produce the file export with the CMDB export tool. The tool needs the CMDB URL, a username, and a token:

```bash
<export-tool> --url <cmdb-url> --username <cmdb-username> --token <cmdb-token> --out cmdb-export/
```

> [!NOTE]
> The configuration can span several CMDB instances. Run the export against each one. This guide follows a single
> export, but the steps are the same for several.

Then validate the export. Remove stale or leftover Clouds and Namespaces that are no longer in use: delete their
folders under `Tenants/<tenant>/Clouds/` so they are not migrated or considered in the following steps.

## 2. Build the environment template

### 2.1 Group environments into types by their Full Solution Descriptors

1. In each Full Solution Descriptor, read the `deployPostfix` of every entry under `applications`, and remove
   duplicates. Several applications share one `deployPostfix`. The deduplicated list is the set of namespaces
   that Solution Descriptor deploys into.
2. Compare the deduplicated lists. Full Solution Descriptors with the same list are one environment type. Each
   distinct list is one type.
3. Name each environment type. This guide uses `dev`.

### 2.2 Create environment template per environment type

1. In the cloud CMDB, create an Application Definition for the env-template artifact.

2. Create one Namespace Template per `deployPostfix` in the set. Copy the
   [Namespace Template blank](/docs/cmdb-migration/blanks/namespace.yml.j2) to
   `templates/env_templates/dev/<deployPostfix>.yml.j2`, naming the file after the namespace `deployPostfix`.
   Then set `name` so it renders to the real namespace name in the cluster. The common pattern is
   `{{ current_env.name }}-<deployPostfix>`. The generated `name` must match the real namespace.

   > [!NOTE]
   > If your namespace names do not follow this pattern, that is out of scope for this guide. Contact the EnvGene
   > team to work out that case.

3. Copy the [Cloud Template blank](/docs/cmdb-migration/blanks/cloud.yml.j2) to
   `templates/env_templates/dev/cloud.yml.j2` unchanged.

4. Copy the [Tenant Template blank](/docs/cmdb-migration/blanks/tenant.yml.j2) to
   `templates/env_templates/dev/tenant.yml.j2` unchanged.

5. Copy the [Template Descriptor blank](/docs/cmdb-migration/blanks/template-descriptor.yaml) to
   `templates/env_templates/dev.yaml`. List the tenant, cloud, and one entry per namespace template. The
   namespace file name is the deploy postfix, so you do not set `deploy_postfix` explicitly.

6. If the CMDB export has a composite structure, copy the
   [Composite Structure Template blank](/docs/cmdb-migration/blanks/composite-structure.yml.j2) to
   `templates/env_templates/dev/composite-structure.yml.j2` and set the deploy postfixes in `baseline` and
   `satellites`. Then uncomment the `composite_structure` line in the Template Descriptor `dev.yaml`:

   ```yaml
   composite_structure: "{{ templates_dir }}/env_templates/dev/composite-structure.yml.j2"
   ```

7. Check the CMDB export for Blue-Green Domains. Blue-Green Domain solutions are out of scope for this guide. If any
   namespace of the type belongs to a Blue-Green Domain, or the composite baseline is itself a Blue-Green Domain,
   contact the EnvGene team to work out that case.

8. Add the Application Definitions and Registry Definitions the templates need, then parameterize the registry.

    - Collect an AppDef for every application that appears in the Solution Descriptors of all templates in the
      repository. Take the base files from the centralized definitions repository.
    - Collect the RegDefs that those AppDefs reference.
    - Place each AppDef at `templates/appdefs/<application-name>.yml.j2` and each RegDef at
      `templates/regdefs/<registry-name>.yml.j2`. The `.yml.j2` extension marks them as templates.
    - In each AppDef, replace the hardcoded `registryName` with
      `{{ appdefs.overrides.registryName | default('<original-registry>') }}`.

9. Commit and publish the template artifact. Note its `name:version` for the inventory.

## 3. Create the environment inventories

### 3.1 Create the cluster folders

Go through the Clouds in the CMDB export. Each Cloud is `Tenants/<tenant>/Clouds/<cloud>/`, with its record at
`<cloud>.yml`. For each Cloud, read `apiUrl` from that record and derive the cluster name: take the host, drop
the `api.` prefix and the base domain. Create the folder `/environments/<cluster>/`.

For example, `https://api.cluster-01.example.com:6443` gives `/environments/cluster-01/`.

> [!NOTE]
> If several Clouds describe the same cluster, that is out of scope for this guide. Contact the EnvGene team to
> work out that case.

### 3.2 Create the Cloud Passport

Do this once for each Cloud `Tenants/<tenant>/Clouds/<cloud>/`.

Copy the [Cloud Passport blank](/docs/cmdb-migration/blanks/cloud-passport.yml) to
`environments/<cluster>/cloud-passport/<cluster>.yml`.

Fill the `cloud` block of `<cluster>.yml` from the Cloud record `<cloud>.yml`. Each value below is the source
attribute to copy:

```yaml
cloud:
  CLOUD_API_HOST: <apiUrl>
  CLOUD_API_PORT: "<apiPort>"
  CLOUD_PRIVATE_HOST: <privateUrl>
  CLOUD_PUBLIC_HOST: <publicUrl>
  CLOUD_DASHBOARD_URL: <dashboardUrl>
  CLOUD_DEPLOY_TOKEN: <defaultCredentialsId>
```

Copy the [Cloud Passport credentials blank](/docs/cmdb-migration/blanks/cloud-passport-creds.yml) to
`environments/<cluster>/cloud-passport/<cluster>-creds.yml`.

Copy only the attributes shown above for now. Other cloud parameters move in
[Refactor migrated parameters](/docs/cmdb-migration/refactor-migrated-parameters.md).

### 3.3 Identify the environments

1. In the CMDB export, open `Tenants/<tenant>/Clouds/`. Each `<cloud>` folder is a cluster.
2. For each cluster, list the folders under `Namespaces/`. Each folder is a namespace.
3. Split each namespace name into its environment-name part and its `deployPostfix` part. For example,
   `env-01-billing` is environment `env-01` with postfix `billing`. Group the namespaces by their
   environment-name part.
4. Each group is one environment, and its set of `deployPostfix` values matches one of the types from 2.1.

> [!NOTE]
> If your namespace names do not follow the `<env-name>-<deployPostfix>` convention, that is out of scope for
> this guide. Contact the EnvGene team to work out that case.

### 3.4 Create one inventory per environment

For each environment from 3.3, create a folder named after the environment under its cluster,
`environments/<cluster>/<env>/`. Put the
[Environment Inventory blank](/docs/cmdb-migration/blanks/env_definition.yml) into it as
`Inventory/env_definition.yml`.

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

If the Cloud record has a `profile`, create a Resource Profile Override at
`environments/<cluster>/<env>/Inventory/resource_profiles/cloud-profile.yml` from its `name` and `baseline`.
Then reference it by file name without the `.yml` extension, as a single value under the `cloud` key in
`envSpecificResourceProfiles`:

```yaml
envTemplate:
  envSpecificResourceProfiles:
    cloud: cloud-profile
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

If the Namespace record has a `profile`, create a Resource Profile Override at
`environments/<cluster>/<env>/Inventory/resource_profiles/<deployPostfix>-profile.yml` from its `name` and
`baseline`. Then reference it by file name without the `.yml` extension, as a single value under the
`<deployPostfix>` key in `envSpecificResourceProfiles`:

```yaml
envTemplate:
  envSpecificResourceProfiles:
    bss: bss-profile
```

### 3.13 Export the credentials

Export every credential from the Jenkins credential store into a single shared credential file, then associate
that file with every environment in the repository.

1. Export all credentials from the Jenkins credential store into one repository-wide file at
   `environments/credentials/shared-credentials.yml`.

   > [!NOTE]
   > The credential export mechanism is not yet defined. This guide is updated with it once it is available.

2. In each environment's `env_definition.yml`, reference the file by name, without the `.yml` extension, in
   `sharedMasterCredentialFiles`:

   ```yaml
   envTemplate:
     sharedMasterCredentialFiles:
       - shared-credentials
   ```

### 3.14 Add the Solution Descriptor

Copy the environment's Solution Descriptor to
`environments/<cluster>/<env>/Inventory/solution-descriptor/sd.yml`. There is one Full Solution Descriptor per
environment.

### 3.15 Create the Artifact Definition

Once per instance repository, copy the
[Artifact Definition blank](/docs/cmdb-migration/blanks/artifact-definition.yml) to
`configuration/artifact_definitions/<name>.yaml`. The file name must match the `name` attribute inside it.

## 4. Run generation to verify

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
