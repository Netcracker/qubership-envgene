# Migration Blueprint: CMDB Objects → EnvGene Objects

---

## Table of Contents

1. [Explanation — Why and What](#1-explanation--why-and-what)
   - 1.1 [What is EnvGene?](#11-what-is-envgene)
   - 1.2 [Why migrate from CMDB Objects to EnvGene Objects?](#12-why-migrate-from-cmdb-objects-to-envgene-objects)
   - 1.3 [Conceptual differences](#13-conceptual-differences)
   - 1.4 [High-level architecture](#14-high-level-architecture)
   - 1.5 [When NOT to migrate](#15-when-not-to-migrate)
2. [Tutorial — Migrate one CMDB Object end-to-end](#2-tutorial--migrate-one-cmdb-object-end-to-end)
3. [How-to Guides](#3-how-to-guides)
   - 3.1 [Map CMDB Object types to EnvGene Object types](#31-map-cmdb-object-types-to-envgene-object-types)
   - 3.2 [Configure the template repository for migration](#32-configure-the-template-repository-for-migration)
   - 3.3 [Configure the instance repository](#33-configure-the-instance-repository)
   - 3.4 [Trigger and validate instance generation](#34-trigger-and-validate-instance-generation)
   - 3.5 [Handle CMDB Objects with no direct EnvGene equivalent](#35-handle-cmdb-objects-with-no-direct-envgene-equivalent)
   - 3.6 [Troubleshoot common migration errors](#36-troubleshoot-common-migration-errors)
4. [Reference](#4-reference)
   - 4.1 [CMDB Object → EnvGene Object mapping table](#41-cmdb-object--envgene-object-mapping-table)
   - 4.2 [EnvGene object schema reference](#42-envgene-object-schema-reference)
   - 4.3 [Required repository folder structure](#43-required-repository-folder-structure)
   - 4.4 [Instance pipeline job reference](#44-instance-pipeline-job-reference)
   - 4.5 [Configuration file parameters reference](#45-configuration-file-parameters-reference)

---

## 1. Explanation — Why and What

### 1.1 What is EnvGene?

EnvGene (Environment Generator) is a GitOps-native platform that turns parameterised Jinja templates into fully-rendered environment configuration objects stored in a Git repository. It is the successor to the manual, record-by-record CMDB workflow.

EnvGene operates across three Git repositories:

| Repository | Purpose |
|---|---|
| **Template repository** | Holds Jinja templates describing the *structure* of a solution (which namespaces exist, what parameters they carry by default). Versioned as a Maven artifact. |
| **Instance repository** | Holds environment-specific inputs (Cloud Passports, ParameterSets, credentials, `env_definition.yml`) and the *generated* Environment Instance objects produced by running the pipeline. |
| **Discovery repository** (optional) | Runs cloud discovery pipelines that publish Cloud Passports automatically. |

When the instance pipeline runs, it downloads the template artifact, merges it with instance-specific inputs, and writes the rendered Environment Instance back to the instance repository.

### 1.2 Why migrate from CMDB Objects to EnvGene Objects?

**Problems with the CMDB approach:**

- Parameters are stored inline in Cloud and Namespace YAML files. Sensitive values such as JWT private keys, TLS certificates, database passwords, and LDAP passwords are plaintext inside `deployParameters`.
- There is no template layer. Every environment is a fully independent record. A cross-cutting change requires touching every affected record individually.
- ParameterSets live at the Tenant level and carry only pipeline-tool parameters. There is no mechanism to compose, override, or scope them per environment type.
- Application objects under Namespaces are mostly empty shells; application-level parameters are stuffed into Namespace `deployParameters` as multi-kilobyte YAML-in-string blobs.

**What EnvGene adds:**

- A **template layer** that factors out all common structure and parameters. A single Jinja template replaces dozens of identical CMDB Cloud/Namespace records.
- **Layered ParameterSets**: template-level (common to all environments of a type) and instance-level (environment-specific overrides), with clear precedence and source traceability comments in every generated file.
- **Cloud Passport** as a first-class object. Platform connection parameters (API URL, MaaS, DBaaS, Consul, credentials) are published once per cluster and consumed by all environments on that cluster.
- **Credential objects** with placeholder generation and optional encryption, replacing plaintext secrets in parameter values.
- **Effective Set generation**: a consumer-ready parameter bundle (for ArgoCD / Helm) derived from the Environment Instance.
- **Full audit trail**: every generated parameter carries a `# paramset: <name> version: <v> source: template|instance` comment.

### 1.3 Conceptual differences

| Concept | CMDB | EnvGene |
|---|---|---|
| **Unit of configuration** | One record per environment in the database | One folder per environment in Git |
| **Parameter reuse** | ParameterSets referenced by name, but content is static | Jinja-parameterised Template ParameterSets + instance-specific override ParameterSets |
| **Cluster connectivity** | Embedded in every Cloud record (`apiUrl`, `apiPort`, `maasConfig`, …) | Factored out into a shared Cloud Passport file per cluster |
| **Secrets** | Plaintext in `deployParameters` or `technicalConfigurationParameters` | Credential objects (`usernamePassword`, `secret`, `external`) with placeholder values and optional encryption |
| **Environment types** | Implicit (naming convention only) | Explicit Template Descriptor per type (e.g., `simple.yaml`, `composite-prod.yaml`) |
| **Change propagation** | Manual: edit every affected record | Automatic: bump the template artifact version and regenerate |
| **Namespace hierarchy** | `Tenant → Cloud → Namespace` (flat, CMDB-internal) | `cluster-name/env-name/Namespaces/deploy-postfix/` in Git |
| **Application parameters** | Mixed into Namespace `deployParameters` as strings | Dedicated `Application` objects generated from ParameterSet `applications` sections |

### 1.4 High-level architecture

**CMDB Object hierarchy (source)**

```
CMDB
  └── Tenants/
        └── <TenantName>/                         ← Tenant (folder only, no record file)
              ├── ParameterSets/
              │     └── <paramset-name>.yml        ← ParameterSet record
              │           name: ...
              │           parameters:              ← flat key-value map (DCL_*, PAAS_*, …)
              │             KEY: value
              │           applications:            ← optional list of Application entries
              │             - appName: ...
              │               deployParameters: {}
              └── Clouds/
                    └── <CloudName>/
                          ├── <CloudName>.yml      ← Cloud record
                          │     name, tenantName
                          │     apiUrl, apiPort, protocol
                          │     publicUrl, privateUrl, dashboardUrl
                          │     defaultCredentialsId
                          │     deployParameters:  ← cluster-wide constants (e.g. PAAS_PLATFORM)
                          │     e2eParameters: {}
                          │     e2eParameterSets:  ← references to ParameterSet names
                          │     maasConfig: {}
                          │     consulConfig: {}
                          │     dbaasConfigs: []
                          │     productionMode: false
                          └── Namespaces/
                                └── <NamespaceName>/
                                      ├── <NamespaceName>.yml   ← Namespace record
                                      │     name, tenantName, cloudName
                                      │     credentialsId
                                      │     cleanInstallApprovalRequired
                                      │     isServerSideMerge
                                      │     mergeDeployParametersAndE2EParameters
                                      │     deployParameters:   ← env-specific params
                                      │       KEY: value        ← may contain plaintext secrets
                                      │       YAML_BLOB: |      ← multi-line YAML-in-string
                                      │         ...
                                      │     e2eParameters: {}
                                      └── Applications/
                                            └── <AppName>.yml   ← Application record
                                                  name
                                                  deployParameters: {}
                                                  technicalConfigurationParameters: {}
```

> Every environment is a standalone record — no shared template layer. Cluster connectivity
> (`apiUrl`, `maasConfig`, …) is duplicated in every Cloud record. Secrets are plaintext inside
> `deployParameters`. Cross-cutting changes require editing every affected record individually.

---

**EnvGene repository structure (target)**

```
Template Repository
  └── templates/
        ├── env_templates/
        │     ├── <template-name>.yaml        ← Template Descriptor
        │     ├── tenant.yml.j2               ← Tenant Template
        │     ├── cloud.yml.j2                ← Cloud Template
        │     └── Namespaces/
        │           └── <ns>.yml.j2           ← Namespace Template
        ├── parameters/
        │     └── <paramset>.yml              ← Template ParameterSet
        └── resource_profiles/
              └── <profile>.yml               ← Template Resource Profile Override
  [CI builds → Maven artifact: my-template:1.2.3]

Instance Repository
  ├── configuration/
  │     ├── artifact_definitions/             ← How to download the template artifact
  │     ├── credentials/credentials.yml       ← System credentials (registry, GitLab token)
  │     └── config.yml                        ← Encryption mode, generation strategy
  └── environments/
        ├── <cluster-name>/
        │     ├── cloud-passport/             ← Cloud Passport (cluster connectivity)
        │     ├── credentials/                ← Shared credentials (cluster scope)
        │     └── <env-name>/
        │           ├── Inventory/
        │           │     ├── env_definition.yml   ← THE RECIPE (mandatory)
        │           │     └── parameters/          ← Env-specific ParameterSets
        │           ├── cloud.yml            ← GENERATED
        │           ├── tenant.yml           ← GENERATED
        │           ├── Credentials/         ← GENERATED credentials
        │           └── Namespaces/
        │                 └── <ns>/
        │                       └── namespace.yml  ← GENERATED

[Instance pipeline runs → generates Environment Instance from template + env_definition.yml]

Effective Set (consumer-ready output)
  └── environments/<cluster>/<env>/effective-set/
        ├── pipeline/parameters.yaml
        └── topology/parameters.yaml
```

The `env_definition.yml` is the single file a configurator writes per environment. Everything else under that environment folder is generated.

### 1.5 When NOT to migrate

- **Environments managed by a system that writes directly to CMDB** — if an external orchestrator owns the CMDB record and overwrites it on each deployment, migrating to EnvGene requires also migrating that orchestrator's integration.
- **Environments where every parameter is unique** — if two environments share no common structure, template reuse is low and the overhead of a template repository may not pay off.
- **Short-lived ephemeral environments** — if an environment lives less than one deployment cycle, the one-time setup cost (Cloud Passport, `env_definition.yml`, credentials) may exceed the benefit.
- **CMDB Objects with no cluster binding** — Application and Registry Definitions that describe only Maven/Docker coordinates and carry no cluster-specific parameters can remain in CMDB or be migrated independently without touching environments.
- **ParameterSets whose parameters are only understood by an external pipeline** — these can be migrated as Template ParameterSets referenced in `e2eParameterSets`, but their values must still be correct for the consuming toolchain.

---

## 2. Tutorial — Migrate one CMDB Object end-to-end

**Goal:** Take a CMDB Cloud record with one Namespace and produce a working EnvGene environment that generates the same Cloud and Namespace objects.

**Time required:** ~30 minutes  
**Prerequisites:** A GitLab/GitHub instance with two empty repositories (template and instance), EnvGene pipeline configured in the instance repo.

---

### Step 1 — Examine the source CMDB Objects

Open your CMDB Cloud export file (typically `cmdbExport/Tenants/<tenantName>/Clouds/<cloudName>/<cloudName>.yml`). A minimal Cloud record looks like:

```yaml
name: "<cloudName>"
apiUrl: "<k8s-api-host>"
apiPort: "6443"
publicUrl: "<public-host>"
defaultCredentialsId: "<cloudName>-admin"
protocol: "HTTPS"
deployParameters:
  PAAS_PLATFORM: "KUBERNETES"
e2eParameterSets:
  - "<common-paramset-name>"
maasConfig:
  enable: false
consulConfig:
  enabled: false
tenantName: "<tenantName>"
```

Open the Namespace export file (`Clouds/<cloudName>/Namespaces/<envName>/<envName>.yml`):

```yaml
name: "<envName>"
credentialsId: "<cloudName>-admin"
cleanInstallApprovalRequired: true
mergeDeployParametersAndE2EParameters: true
deployParameters:
  LOG_LEVEL: "INFO"
  MONITORING_ENABLED: "'false'"
  PAAS_VERSION: "\"1.32\""
  # ... any env-specific parameters; large YAML-in-string blobs or secret values
  #     should be extracted in the steps below
```

**What you observe:**
- Cluster connectivity (`apiUrl`, `apiPort`, `protocol`) lives inside the Cloud object — these will move to a Cloud Passport.
- Cluster-wide constants in `deployParameters` (e.g., `PAAS_PLATFORM`) belong in a Template ParameterSet.
- Any `e2eParameterSets` entries will become Template ParameterSets in the template repo.
- Large YAML-in-string blobs and secret values in `deployParameters` should move to an instance-level ParameterSet and Credential objects respectively.

**Expected output of this step:** a clear list of what goes where in EnvGene.

---

### Step 2 — Create the Cloud Passport

In the instance repository, create:

```
environments/<cloudName>/cloud-passport/<cloudName>.yml
```

```yaml
version: 1.5
cloud:
  CLOUD_API_HOST: <k8s-api-host>
  CLOUD_API_PORT: "6443"
  CLOUD_DEPLOY_TOKEN: <cloudName>-admin
  CLOUD_PUBLIC_HOST: <public-host>
  CLOUD_PRIVATE_HOST: <private-host>
  CLOUD_DASHBOARD_URL: ""
  CLOUD_PROTOCOL: HTTPS
  PRODUCTION_MODE: false
maas:
  MAAS_ENABLED: false
consul:
  CONSUL_ENABLED: false
```

Also create the credentials file for the Cloud Passport (sensitive values):

```
environments/<cloudName>/cloud-passport/<cloudName>-creds.yml
```

```yaml
<cloudName>-admin:
  type: secret
  data:
    secret: "envgeneNullValue"
```

> Replace `envgeneNullValue` with the actual token before running the pipeline.

**Expected output:** Two files committed to the instance repository. No pipeline run yet.

---

### Step 3 — Create the Template ParameterSet and Cloud Template

In the **template repository**, create a ParameterSet for parameters that are common to all environments of this type. The name should describe its scope (e.g., cluster-level constants, e2e tooling parameters):

```
templates/parameters/<common-paramset-name>.yml
```

```yaml
name: <common-paramset-name>
parameters:
  PAAS_PLATFORM: "KUBERNETES"
  # add any other parameters shared by every environment of this type
  # e.g. registry URLs, pipeline tool settings, cluster-specific constants
```

Also create a Cloud Template at `templates/env_templates/<templateName>/cloud.yml.j2`:

```yaml
name: "{{ current_env.cloudNameWithCluster }}"
apiUrl: "{{ current_env.cluster.cloud_api_url }}"
apiPort: "{{ current_env.cluster.cloud_api_port }}"
publicUrl: "{{ current_env.cluster.cloud_public_url }}"
privateUrl: "{{ current_env.cluster.cloud_private_url }}"
dashboardUrl: "{{ current_env.cluster.cloud_dashboard_url | default('') }}"
labels: []
defaultCredentialsId: "{{ current_env.cluster.cloud_deploy_token }}"
protocol: "{{ current_env.cluster.cloud_api_protocol }}"
maasConfig:
  enable: false
vaultConfig:
  enable: false
consulConfig:
  enabled: false
dbaasConfigs:
  - enable: false
deployParameters: {}
e2eParameters: {}
technicalConfigurationParameters: {}
deployParameterSets: []
e2eParameterSets:
  - <common-paramset-name>
technicalConfigurationParameterSets: []
```

**Expected output:** The template repo now has a Cloud Template that references the ParameterSet. Commit and publish the template artifact (e.g., `<productName>-template:1.0.0`).

---

### Step 4 — Create the Namespace Template

In the template repo, create `templates/env_templates/<templateName>/Namespaces/<namespaceName>.yml.j2`.

Include only parameters that are **identical across every environment** of this type. Leave out environment-specific values and secrets — those go in the instance repo (Step 5).

```yaml
name: "{{ current_env.name }}"
credentialsId: "{{ current_env.cluster.cloud_deploy_token }}"
labels: []
isServerSideMerge: false
cleanInstallApprovalRequired: true
mergeDeployParametersAndE2EParameters: true
deployParameters:
  # place parameters that are the same for all environments of this type
  LOG_LEVEL: "INFO"
  MONITORING_ENABLED: "'false'"
e2eParameters: {}
technicalConfigurationParameters: {}
deployParameterSets: []
e2eParameterSets: []
technicalConfigurationParameterSets: []
```

> Parameters that are environment-specific, vary per cluster, or contain secrets must **not** go here. Move them to an instance-level ParameterSet or Credential objects (Step 5).

Create the Template Descriptor at `templates/env_templates/<templateName>.yaml`:

```yaml
tenant: <templateName>/tenant.yml.j2
cloud: <templateName>/cloud.yml.j2
namespaces:
  - template_path: <templateName>/Namespaces/<namespaceName>.yml.j2
    deploy_postfix: <envName>
```

**Expected output:** A valid Template Descriptor committed to the template repo.

---

### Step 5 — Create the Environment Inventory

In the instance repository, create:

```
environments/<cloudName>/<envName>/Inventory/env_definition.yml
```

```yaml
inventory:
  environmentName: "<envName>"
  tenantName: "<tenantName>"
  cloudName: "<cloudName>"
  cloudPassport: "<cloudName>"
  config:
    updateCredIdsWithEnvName: true   # recommended for production environments
envTemplate:
  name: "<templateName>"
  artifact: "<productName>-template:1.0.0"
  envSpecificParamsets:
    <envName>:
      - <envName>-deploy
```

Then create the environment-specific ParameterSet for values that differ from the template defaults:

```
environments/<cloudName>/<envName>/Inventory/parameters/<envName>-deploy.yml
```

```yaml
name: <envName>-deploy
parameters:
  # environment-specific parameters that override or extend template defaults
  SOME_ENV_PARAM: "value"
  # for parameters containing secrets, reference a Credential object instead
  # of putting the value here:
  DB_PASSWORD: "${creds.get(\"<envName>-db-cred\").password}"
```

And add a Credential placeholder for any secret values:

```
environments/<cloudName>/<envName>/Credentials/credentials.yml
```

```yaml
<envName>-db-cred:
  type: usernamePassword
  data:
    username: "<db-username>"
    password: "envgeneNullValue"
```

> Replace all `envgeneNullValue` entries with real secret values before or after the pipeline run, depending on your credential management workflow.

**Expected output:** All files committed. The environment is fully described. Pipeline is ready to run.

---

### Step 6 — Run the pipeline

Trigger the instance pipeline with these parameters:

| Parameter | Value |
|---|---|
| `ENV_NAMES` | `<cloudName>/<envName>` |
| `ENV_BUILD` | `true` |
| `GENERATE_EFFECTIVE_SET` | `true` |

**Expected output:** The pipeline runs the `env_build` job, then `generate_effective_set`, then `git_commit`. After the pipeline completes, the following files are present in the instance repo:

```
environments/<cloudName>/<envName>/
  cloud.yml          ← generated, contains apiUrl from Cloud Passport
  tenant.yml         ← generated
  Namespaces/
    <envName>/
      namespace.yml  ← generated, contains merged deployParameters
  Credentials/
    credentials.yml  ← generated placeholders
  effective-set/
    pipeline/parameters.yaml
    topology/parameters.yaml
```

Open `cloud.yml` and verify it contains a comment like:
```yaml
apiUrl: "<k8s-api-host>" # cloud passport: <cloudName> version: 1.5
```

Open `namespace.yml` and verify your expected parameters appear, each with a comment indicating the source ParameterSet.

**Congratulations — you have migrated one CMDB environment to EnvGene.**

---

## 3. How-to Guides

---

### 3.1 Map CMDB Object types to EnvGene Object types

See the full mapping table in [Section 4.1](#41-cmdb-object--envgene-object-mapping-table).

**Decision rules for each CMDB field:**

**Cloud record fields:**

| CMDB field | Decision |
|---|---|
| `apiUrl`, `apiPort`, `protocol`, `publicUrl`, `privateUrl`, `dashboardUrl` | → Cloud Passport `cloud.*` section |
| `defaultCredentialsId` | → Cloud Passport `cloud.CLOUD_DEPLOY_TOKEN` (key name); actual credential → `cloud-passport/<name>-creds.yml` |
| `maasConfig.*` | → Cloud Passport `maas.*` section |
| `vaultConfig.*` | → Cloud Passport or Cloud Template `vaultConfig` |
| `consulConfig.*` | → Cloud Passport `consul.*` section |
| `dbaasConfigs.*` | → Cloud Passport `dbaas.*` section |
| `deployParameters` (cluster-wide constants) | → Template ParameterSet referenced in Cloud Template `deployParameterSets` |
| `e2eParameters` (cluster-wide) | → Template ParameterSet referenced in Cloud Template `e2eParameterSets` |
| `e2eParameterSets` (list of CMDB paramset names) | → Same paramset names in Template repo `deployParameterSets` / `e2eParameterSets` |
| `tenantName` | → `inventory.tenantName` in `env_definition.yml` |
| `productionMode` | → Cloud Passport `cloud.PRODUCTION_MODE`; also `inventory.config.updateCredIdsWithEnvName` if true |
| `dbMode`, `databases` (deprecated in CMDB) | Drop — not processed by EnvGene |

**Namespace record fields:**

| CMDB field | Decision |
|---|---|
| `name` | → Namespace Template `name` field; also the folder name under `Namespaces/` |
| `credentialsId` | → Namespace Template `credentialsId`; credential object → `Credentials/credentials.yml` |
| `labels` | → Namespace Template `labels` |
| `cleanInstallApprovalRequired` | → Namespace Template `cleanInstallApprovalRequired` |
| `isServerSideMerge` | → Namespace Template `isServerSideMerge` |
| `mergeDeployParametersAndE2EParameters` | → Namespace Template `mergeDeployParametersAndE2EParameters` |
| `deployParameters` (common across envs of same type) | → Template ParameterSet `parameters` (deploy scope) |
| `deployParameters` (env-specific) | → Instance ParameterSet in `Inventory/parameters/` |
| `deployParameters` containing secrets | → Extract to Credential objects; reference via `${creds.get("<id>").<field>}` |
| `technicalConfigurationParameters` | → Template or instance ParameterSet for technical scope |
| `e2eParameters` | → Template or instance ParameterSet for e2e scope |
| `tenantName`, `cloudName` | → `inventory.tenantName`, `inventory.cloudName` in `env_definition.yml` |
| `dirty` | Drop — internal CMDB state flag, not used in EnvGene |

**ParameterSet record fields:**

| CMDB field | Decision |
|---|---|
| `name` | → ParameterSet `name` (must match filename) |
| `parameters` | → ParameterSet `parameters` map |
| `applications` (list) | → ParameterSet `applications` section (same structure) |

If the ParameterSet is shared across all environments of a given type, place it in the **template repo** at `templates/parameters/`. If it is specific to one cluster or environment, place it in the **instance repo** at the appropriate scope level.

**Application record (under Namespace):**

The CMDB Application object (`name`, `deployParameters`, `technicalConfigurationParameters`) maps directly to the EnvGene Application object. The cleanest migration path is to add an `applications` section to the relevant ParameterSet rather than creating standalone Application files.

---

### 3.2 Configure the template repository for migration

**Goal:** Set up a template repository that covers the CMDB environments you are migrating.

1. **Identify environment types.** Group CMDB Cloud+Namespace combinations that share the same structure. Each group becomes one Template Descriptor. For example, all clusters running the same product version with identical namespace layouts form one type.

2. **Create the folder structure:**

   ```
   templates/
     env_templates/
       <type-name>.yaml           ← Template Descriptor
       <type-name>/
         tenant.yml.j2
         cloud.yml.j2
         Namespaces/
           <ns-name>.yml.j2
     parameters/
       <paramset-name>.yml
     resource_profiles/
       <profile-name>.yml
   configuration/
     credentials/credentials.yml  ← system credentials (registry access)
   ```

3. **Write the Cloud Template.** Use `current_env.cluster.*` variables for all connectivity fields. These are populated from the Cloud Passport at generation time. See the Reference section for the full variable list.

4. **Extract common `deployParameters` and `e2eParameters`** into Template ParameterSets. Reference them from the Cloud or Namespace template via `deployParameterSets` / `e2eParameterSets`.

5. **Build and publish the template artifact.** The CI pipeline in the template repo must produce a Maven artifact. Reference it in the instance repo's `artifact_definitions/` file using `groupId:artifactId` coordinates.

6. **Validate** by running the template pipeline with `ENV_TEMPLATE_TEST: true` against a test environment before rolling out.

---

### 3.3 Configure the instance repository

**Goal:** Add a new cluster and environment to the instance repository.

**Per cluster (do once per cluster):**

1. Create the Cloud Passport:

   ```
   environments/<cluster-name>/cloud-passport/<cluster-name>.yml
   environments/<cluster-name>/cloud-passport/<cluster-name>-creds.yml
   ```

   Populate the main file with non-sensitive connectivity data from the CMDB Cloud record (see Step 2 of the Tutorial). Populate the creds file with Credential objects whose `data` values are initially `envgeneNullValue`.

2. Create the `artifact_definitions/` entry for the template:

   ```
   configuration/artifact_definitions/<template-name>.yml
   ```

   This tells EnvGene where to download the template Maven artifact.

3. Create system credentials (`configuration/credentials/credentials.yml`) for registry access.

**Per environment (do once per environment):**

1. Create `environments/<cluster>/<env-name>/Inventory/env_definition.yml`. Minimum required fields:

   ```yaml
   inventory:
     tenantName: "<CMDB tenantName>"
     cloudPassport: "<cluster-name>"
   envTemplate:
     name: "<template-descriptor-name>"
     artifact: "<template-name>:<version>"
   ```

2. If the environment has parameters that differ from the template defaults (most CMDB environments will), create environment-specific ParameterSets under:

   ```
   environments/<cluster>/<env>/Inventory/parameters/<paramset-name>.yml
   ```

   Reference them in `env_definition.yml` under `envTemplate.envSpecificParamsets`.

3. If multiple environments on the same cluster share credential values, create a shared credentials file:

   ```
   environments/<cluster>/credentials/<shared-creds-name>.yml
   ```

   Reference it in `env_definition.yml` under `envTemplate.sharedMasterCredentialFiles`.

---

### 3.4 Trigger and validate instance generation

**Goal:** Run the instance pipeline and verify the generated objects match the original CMDB data.

1. **Trigger the pipeline** with parameters:

   ```
   ENV_NAMES:              <cluster-name>/<env-name>
   ENV_BUILD:              true
   GENERATE_EFFECTIVE_SET: true
   ```

2. **Check the `env_build` job log** for errors. Common fatal errors are missing ParameterSet files, schema validation failures, and unresolved Jinja variables.

3. **Inspect generated objects** in the instance repository after `git_commit` runs:
   - `cloud.yml` — verify `apiUrl`, `apiPort`, `protocol` match the original CMDB Cloud record.
   - `Namespaces/<ns>/namespace.yml` — verify `deployParameters` contains all expected keys with correct values.
   - `Credentials/credentials.yml` — verify Credential objects were generated for every `${creds.get(…)}` reference.

4. **Verify the Effective Set** (if `GENERATE_EFFECTIVE_SET: true` was set):
   - `effective-set/pipeline/parameters.yaml` — should contain the flattened key-value map consumed by ArgoCD/Helm.

5. **Compare with CMDB** parameter by parameter. A useful diff approach:
   - Export the CMDB Namespace as YAML.
   - Export the generated `namespace.yml` (strip comment lines with `grep -v '^#'`).
   - Diff the two files.

6. **Fill in credential placeholders.** The generated `Credentials/credentials.yml` will have `envgeneNullValue` for all secrets. Replace these with real values and commit.

---

### 3.5 Handle CMDB Objects with no direct EnvGene equivalent

**`productionMode` field (Cloud level)**

CMDB stores `productionMode: true/false` on the Cloud record. EnvGene has no `productionMode` field on the Cloud object. Options:
- Store it as `PRODUCTION_MODE` in the Cloud Passport and have the Cloud Template write it into `deployParameters`.
- Set `inventory.config.updateCredIdsWithEnvName: true` for production environments (which causes credential IDs to be prefixed with `<tenant>-<cloud>-<env>-`, preventing credential collisions across envs).

**`supportedBy` field (Cloud level)**

EnvGene has no equivalent. If needed, add it as a custom key in `deployParameters` or in the `metadata` block of `env_definition.yml` (the `metadata` block is not processed by EnvGene and is free-form).

**`dirty` flag (Namespace level)**

Internal CMDB state. Drop it entirely.

**`dbMode` and `databases` array (Cloud level)**

Marked deprecated in the EnvGene Cloud schema. Do not migrate.

**Large multi-line YAML-in-string parameter values**

These blobs typically mix connection strings, secrets, and application configuration. Decompose them:
- Connection strings that vary per environment → instance-level ParameterSet.
- Secrets (passwords, private keys, access tokens) → Credential objects, referenced via `${creds.get(…)}`.
- Fixed application configuration → Template ParameterSet.

If decomposition is not feasible in the short term, the entire blob can go into an instance-level ParameterSet as a literal YAML scalar. This is valid but loses the benefits of template-level reuse.

**Credential ID parameters expected by external pipeline tools**

Some CMDB ParameterSets contain credential ID parameters consumed by external pipelines (not by EnvGene itself). Keep these in a Template ParameterSet in the `e2eParameterSets` scope. The corresponding Credential objects must exist in `Credentials/credentials.yml`.

**Tenant-level ParameterSets (CMDB)**

In CMDB, ParameterSets are defined at the Tenant level and applied to Clouds. In EnvGene, there is no Tenant-level ParameterSet. The equivalent is:
- A Template ParameterSet in the template repo (applied to all environments using that template).
- A cluster-level ParameterSet placed at `environments/<cluster>/parameters/` (applied to all environments in that cluster).

---

### 3.6 Troubleshoot common migration errors

**`ParameterSet name does not match filename`**

The `name` field inside a ParameterSet YAML must exactly match the filename (without extension).

```
# Wrong: file is named "my-env-deploy.yml" but name field says:
name: my_env_deploy   ← underscore vs hyphen
```

Fix: rename the file or change the `name` field to match.

---

**`Template Descriptor references a file that does not exist`**

The `template_path` in the Template Descriptor is relative to the `templates/env_templates/` folder. If the file is missing from the template artifact, `env_build` fails.

Fix: verify the template artifact was built with the latest commit and the file path is spelled correctly (case-sensitive).

---

**`Cloud Passport not found`**

`env_definition.yml` references a Cloud Passport by name (e.g., `cloudPassport: <cloudName>`) but EnvGene cannot find the file.

EnvGene searches the following locations in order:
1. `environments/<cluster>/<env>/Inventory/cloud-passport/`
2. `environments/<cluster>/cloud-passport/` ← recommended location

Fix: ensure the file is at `environments/<cluster>/cloud-passport/<name>.yml`.

---

**`Jinja rendering error: 'current_env.cluster' is undefined`**

The Cloud Template uses `current_env.cluster.*` variables but no Cloud Passport was found or the passport key does not match the variable name.

Cloud Passport keys map to `current_env.cluster.*` as follows:

| Cloud Passport key | `current_env.cluster.*` variable |
|---|---|
| `cloud.CLOUD_API_HOST` | `cloud_api_url` |
| `cloud.CLOUD_API_PORT` | `cloud_api_port` |
| `cloud.CLOUD_PUBLIC_HOST` | `cloud_public_url` |
| `cloud.CLOUD_PRIVATE_HOST` | `cloud_private_url` |
| `cloud.CLOUD_PROTOCOL` | `cloud_api_protocol` |
| `cloud.CLOUD_DASHBOARD_URL` | `cloud_dashboard_url` |

Fix: verify the Cloud Passport file uses the correct key names (all uppercase, prefixed with `CLOUD_`).

---

**`Credential placeholder not replaced`**

The generated `namespace.yml` contains `${creds.get("some-cred").password}` literally, not an actual value. This is expected — EnvGene writes credential references, not plaintext values. The Effective Set generator resolves them at Effective Set generation time.

This becomes a problem only if the credential object itself is missing. Fix: ensure the Credential object with the matching ID exists in `Credentials/credentials.yml` or a shared credentials file.

---

**`Schema validation failed: field 'dirty' is not allowed`**

The CMDB Namespace export contains a `dirty` field that is not part of the EnvGene Namespace schema. Fix: remove `dirty` from any ParameterSet or direct copy of the CMDB YAML you added to the instance repo.

---

## 4. Reference

---

### 4.1 CMDB Object → EnvGene Object mapping table

All CMDB Object types and their EnvGene equivalents:

| CMDB Object type | Location in CMDB export | EnvGene Object type(s) | Location in EnvGene | Notes |
|---|---|---|---|---|
| **Tenant** | `Tenants/<TenantName>/` (folder) | `inventory.tenantName` in `env_definition.yml` | `environments/<cluster>/<env>/Inventory/env_definition.yml` | No standalone Tenant file in instance repo |
| **Cloud** | `Tenants/<T>/Clouds/<CloudName>/<CloudName>.yml` | Cloud (generated) + Cloud Passport | `environments/<cluster>/<env>/cloud.yml` (generated); `environments/<cluster>/cloud-passport/<name>.yml` | Connectivity fields → Cloud Passport; parameter fields → Template ParameterSet |
| **Namespace** | `Tenants/<T>/Clouds/<C>/Namespaces/<NS>/<NS>.yml` | Namespace (generated) | `environments/<cluster>/<env>/Namespaces/<deploy-postfix>/namespace.yml` | Generated from Namespace Template + ParameterSets |
| **ParameterSet** | `Tenants/<T>/ParameterSets/<name>.yml` | Template ParameterSet or Instance ParameterSet | `templates/parameters/<name>.yml` (template repo) or `environments/.../parameters/<name>.yml` (instance repo) | Common paramsets → template repo; cluster/env-specific → instance repo |
| **Application** | `Tenants/<T>/Clouds/<C>/Namespaces/<NS>/Applications/<App>.yml` | Application (generated) | `environments/<cluster>/<env>/Namespaces/<ns>/Applications/<app>.yml` (generated) | Generated from ParameterSet `applications` section |

---

### 4.2 EnvGene object schema reference

#### Cloud object (generated, `cloud.yml`)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Combines cluster and env name |
| `apiUrl` | string | Yes | K8s API server host |
| `apiPort` | integer\|string | Yes | K8s API server port |
| `privateUrl` | string | No | Internal cluster URL |
| `publicUrl` | string | No | External cluster URL |
| `dashboardUrl` | string | Yes | K8s dashboard URL |
| `labels` | list | Yes | Tagging labels |
| `defaultCredentialsId` | string | Yes | Default deploy credential ID |
| `protocol` | string | Yes | `http` or `https` |
| `maasConfig.enable` | boolean | Yes | Enable MaaS integration |
| `maasConfig.credentialsId` | string | No | MaaS credential ID |
| `maasConfig.maasUrl` | string | No | External MaaS URL |
| `maasConfig.maasInternalAddress` | string | No | Internal MaaS URL |
| `vaultConfig.enable` | boolean | Yes | Enable Vault integration |
| `vaultConfig.url` | string | No | Vault URL |
| `vaultConfig.credentialsId` | string | No | Vault credential ID |
| `consulConfig.enabled` | boolean | Yes | Enable Consul integration |
| `consulConfig.publicUrl` | string | No | External Consul URL |
| `consulConfig.internalUrl` | string | No | Internal Consul URL |
| `consulConfig.tokenSecret` | string | No | Consul token credential ID |
| `dbaasConfigs[].enable` | boolean | Yes | Enable DBaaS integration |
| `dbaasConfigs[].credentialsId` | string | No | DBaaS credential ID |
| `dbaasConfigs[].apiUrl` | string | No | Internal DBaaS API URL |
| `dbaasConfigs[].aggregatorUrl` | string | No | External DBaaS aggregator URL |
| `deployParameters` | hashmap | No | Deploy-scope parameters |
| `e2eParameters` | hashmap | No | Pipeline/e2e-scope parameters |
| `technicalConfigurationParameters` | hashmap | No | Runtime-scope parameters |
| `deployParameterSets` | list | No | Referenced deploy ParameterSet names |
| `e2eParameterSets` | list | No | Referenced e2e ParameterSet names |
| `technicalConfigurationParameterSets` | list | No | Referenced technical ParameterSet names |

#### Namespace object (generated, `namespace.yml`)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Kubernetes namespace name |
| `credentialsId` | string | No | Deploy credential ID for this namespace |
| `labels` | list | No | Tagging labels |
| `isServerSideMerge` | boolean | Yes | Server-side Helm merge |
| `cleanInstallApprovalRequired` | boolean | Yes | Approval gate for clean installs |
| `mergeDeployParametersAndE2EParameters` | boolean | Yes | Merge deploy+e2e params during Effective Set |
| `profile.name` | string | No | Resource profile override name |
| `profile.baseline` | string | No | Baseline profile name |
| `deployParameters` | hashmap | No | Deploy-scope parameters |
| `e2eParameters` | hashmap | No | Pipeline/e2e-scope parameters |
| `technicalConfigurationParameters` | hashmap | No | Runtime-scope parameters |
| `deployParameterSets` | list | No | Referenced deploy ParameterSet names |
| `e2eParameterSets` | list | No | Referenced e2e ParameterSet names |
| `technicalConfigurationParameterSets` | list | No | Referenced technical ParameterSet names |

#### Tenant object (generated, `tenant.yml`)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Tenant name |
| `registryName` | string | Yes | Deprecated; leave empty |
| `description` | string | No | Tenant description |
| `owners` | string | No | Owner contact |
| `credential` | string | No | Default credential ID |
| `labels` | list | No | Tagging labels |

#### ParameterSet object (template or instance)

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Must match filename without extension |
| `parameters` | hashmap | Yes | Key-value parameter pairs |
| `applications[].appName` | string | No | Application name (creates Application object) |
| `applications[].parameters` | hashmap | No | Application-level parameters |

#### Cloud Passport (main file)

| Section | Key prefix | Description |
|---|---|---|
| `version` | — | Passport schema version (use `1.5`) |
| `cloud` | `CLOUD_*` | Cluster connectivity parameters |
| `maas` | `MAAS_*` | MaaS connection parameters |
| `consul` | `CONSUL_*` | Consul connection parameters |
| `dbaas` | `*DBAAS*` | DBaaS connection parameters |

#### `env_definition.yml`

| Field | Type | Required | Description |
|---|---|---|---|
| `inventory.environmentName` | string | No | Env name (derived from folder if absent) |
| `inventory.tenantName` | string | No | Tenant name for template rendering |
| `inventory.cloudName` | string | No | Cloud name for template rendering |
| `inventory.cloudPassport` | string | No | Cloud Passport filename (no extension) |
| `inventory.deployer` | string | No | Deployer config key for CMDB import |
| `inventory.config.updateCredIdsWithEnvName` | boolean | No | Prefix cred IDs with env path (default: false) |
| `inventory.config.updateRPOverrideNameWithEnvName` | boolean | No | Prefix RP override names with env path (default: false) |
| `inventory.config.mergeEnvSpecificResourceProfiles` | boolean | No | Merge vs replace resource profiles (default: true) |
| `envTemplate.name` | string | Yes | Template Descriptor name inside artifact |
| `envTemplate.artifact` | string | Yes | Template artifact in `name:version` notation |
| `envTemplate.additionalTemplateVariables` | hashmap | No | Extra variables for Jinja rendering |
| `envTemplate.sharedTemplateVariables` | array | No | Filenames of shared template variable files |
| `envTemplate.envSpecificParamsets` | hashmap | No | Keys: namespace deploy-postfix or `cloud`; values: list of ParameterSet filenames |
| `envTemplate.envSpecificE2EParamsets` | hashmap | No | Same structure for e2e scope |
| `envTemplate.envSpecificTechnicalParamsets` | hashmap | No | Same structure for technical scope |
| `envTemplate.envSpecificResourceProfiles` | hashmap | No | Keys: namespace/cloud; values: list of profile filenames |
| `envTemplate.sharedMasterCredentialFiles` | array | No | Filenames of shared credential files |

---

### 4.3 Required repository folder structure

#### Template repository

```
templates/
  env_templates/
    <template-name>.yaml|yml|yml.j2|yaml.j2    ← Template Descriptor (mandatory)
    <template-name>/
      tenant.yml.j2                             ← Tenant Template
      cloud.yml.j2                              ← Cloud Template
      Namespaces/
        <ns-name>.yml.j2                        ← Namespace Template (one per namespace)
      [bg_domain.yml.j2]                        ← BG Domain Template (optional)
      [composite_structure.yml.j2]              ← Composite Structure Template (optional)
  parameters/
    <paramset-name>.yml                         ← Template ParameterSet
  resource_profiles/
    <profile-name>.yml                          ← Template Resource Profile Override
  [appdefs/
    <appdef-name>.yml.j2]                       ← Application Definition Template
  [regdefs/
    <regdef-name>.yml.j2]                       ← Registry Definition Template
configuration/
  credentials/
    credentials.yml                             ← System credentials (registry, GitLab)
```

#### Instance repository

```
configuration/
  config.yml                                    ← Encryption, generation strategy
  integration.yml                               ← GitLab/GitHub integration tokens
  artifact_definitions/
    <artifact-name>.yml                         ← Template artifact download config
  credentials/
    credentials.yml                             ← System credentials
  [secret-stores.yml]                           ← External secret store definitions
environments/
  [credentials/]                                ← Site-wide shared credentials
  [parameters/]                                 ← Site-wide shared ParameterSets
  <cluster-name>/
    cloud-passport/
      <passport-name>.yml                       ← Cloud Passport (non-sensitive)
      <passport-name>-creds.yml                 ← Cloud Passport (sensitive)
    [credentials/]                              ← Cluster-wide shared credentials
    [parameters/]                               ← Cluster-wide shared ParameterSets
    [app-deployer/deployer.yml]                 ← Deployer configuration
    <env-name>/
      Inventory/
        env_definition.yml                      ← MANDATORY: env recipe
        parameters/
          <paramset-name>.yml                   ← Env-specific ParameterSet
        resource_profiles/
          <profile-name>.yml                    ← Env-specific Resource Profile Override
        credentials/
          <shared-creds-name>.yml               ← Env-specific shared credentials
      [cloud.yml]                               ← GENERATED
      [tenant.yml]                              ← GENERATED
      [bg_domain.yml]                           ← GENERATED
      [composite_structure.yml]                 ← GENERATED
      Namespaces/
        <deploy-postfix>/
          namespace.yml                         ← GENERATED
          [Applications/
            <app-name>.yml]                     ← GENERATED
      Credentials/
        credentials.yml                         ← GENERATED
      effective-set/
        pipeline/
          parameters.yaml                       ← GENERATED (Effective Set)
        topology/
          parameters.yaml                       ← GENERATED (Effective Set)
```

---

### 4.4 Instance pipeline job reference

Jobs run sequentially. A job failure stops the pipeline.

| Job | Condition to run | What it does |
|---|---|---|
| `trigger_passport` | `GET_PASSPORT: true` | Triggers the Discovery repository pipeline |
| `get_passport` | `GET_PASSPORT: true` | Downloads the discovered Cloud Passport into the instance repo |
| `bg_manage` | `BG_MANAGE: true` | Manages Blue-Green Domain state transitions |
| `env_inventory_generation` | `ENV_INVENTORY_CONTENT` set, or `ENV_INVENTORY_INIT: true`, or `ENV_SPECIFIC_PARAMS` set, or `ENV_TEMPLATE_NAME` set | Auto-generates or patches `env_definition.yml` |
| `credential_rotation` | `CRED_ROTATION_PAYLOAD` provided | Rotates specified credentials |
| `app_reg_def_process` | `ENV_BUILD: true` | Renders Application and Registry Definition templates; handles system certificate updates |
| `process_sd` | `SD_SOURCE_TYPE: json` + `SD_DATA` provided, or `SD_SOURCE_TYPE: artifact` + `SD_VERSION` provided | Processes the Solution Descriptor |
| `env_build` | `ENV_BUILD: true` | Downloads template artifact; renders all environment objects (Cloud, Tenant, Namespaces, Profiles, Credentials) from Jinja templates + env-specific inputs |
| `generate_effective_set` | `GENERATE_EFFECTIVE_SET: true` | Generates the consumer-ready Effective Set (ArgoCD/Helm parameter bundle) |
| `git_commit` | Any prior job produced changes AND `ENV_TEMPLATE_TEST: false` | Commits and pushes generated files to the instance repo |
| `cmdb_import` | Deployer configured in `env_definition.yml` | Imports the generated Environment Instance objects back into an external CMDB |

**Key pipeline input parameters:**

| Parameter | Type | Description |
|---|---|---|
| `ENV_NAMES` | string | Space- or comma-separated list of `<cluster>/<env>` paths to process |
| `ENV_BUILD` | boolean | Run `env_build` job (default: true) |
| `GENERATE_EFFECTIVE_SET` | boolean | Run `generate_effective_set` job |
| `ENV_TEMPLATE_VERSION` | string | Override the template artifact version in `env_definition.yml` |
| `GET_PASSPORT` | boolean | Trigger Cloud Passport discovery |
| `SD_VERSION` | string | Solution Descriptor artifact version |
| `SD_SOURCE_TYPE` | enum (`json`\|`artifact`) | Source of the Solution Descriptor |
| `ENV_TEMPLATE_TEST` | boolean | Dry-run mode: skip `git_commit` |

---

### 4.5 Configuration file parameters reference

#### `config.yml` (instance repository, `/configuration/config.yml`)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `crypt` | boolean | `true` | Enable credential encryption |
| `crypt_backend` | enum | `Fernet` | Encryption backend: `Fernet` or `SOPS` |
| `artifact_definitions_discovery_mode` | enum | `auto` | `auto` \| `true` \| `false` — whether to discover artifact definitions from CMDB |
| `app_reg_def_mode` | enum | `auto` | `auto` \| `cmdb` \| `local` — source for Application/Registry Definitions |
| `app_reg_defs_placement` | enum | `dual` | `dual` \| `root` — where rendered app/reg defs are written |
| `effective_set_generation_strategy` | enum | `partial` | `partial` \| `full` — partial generation is triggered automatically when applicable |
| `sbom_retention.enabled` | boolean | `false` | Enable SBOM cleanup |
| `sbom_retention.keep_versions_per_app` | integer | — | Number of SBOM versions to keep per application |

#### `integration.yml` (instance repository, `/configuration/integration.yml`)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `cp_discovery.gitlab.project` | string | Yes (if CP discovery used) | Full GitLab project path of Discovery repo |
| `cp_discovery.gitlab.branch` | string | Yes | Branch name |
| `cp_discovery.gitlab.token` | string | Yes | Auth token (use `${creds.get(…).secret}`) |
| `self_token` | string | Yes | Token for EnvGene to commit to the instance repo |

#### `deployer.yml`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `<name>.username` | string | Yes | Username for CMDB API |
| `<name>.token` | string | Yes | Token for CMDB API |
| `<name>.deployerUrl` | string | Yes | Base URL of the CMDB system |

#### Artifact Definition v1.0

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Must match filename without extension |
| `groupId` | string | Yes | Maven group ID |
| `artifactId` | string | Yes | Maven artifact ID |
| `registry.name` | string | Yes | Registry logical name |
| `registry.credentialsId` | string | Yes | Credential ID for registry auth |
| `registry.mavenConfig.repositoryDomainName` | string | Yes | Registry base URL |
| `registry.mavenConfig.targetSnapshot` | string | Yes | Snapshot repo name |
| `registry.mavenConfig.targetStaging` | string | Yes | Staging repo name |
| `registry.mavenConfig.targetRelease` | string | Yes | Release repo name |
