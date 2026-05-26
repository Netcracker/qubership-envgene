# External Credentials Management

- [External Credentials Management](#external-credentials-management)
  - [Description](#description)
  - [Problem Statement](#problem-statement)
  - [Assumption](#assumption)
  - [Proposed Approach](#proposed-approach)
    - [Overview](#overview)
    - [Objects](#objects)
      - [Credential Reference](#credential-reference)
      - [Built-in credential references](#built-in-credential-references)
      - [Credential Template](#credential-template)
      - [Credential](#credential)
      - [Secret Store](#secret-store)
      - [Parameter with VALS reference](#parameter-with-vals-reference)
      - [Parameter with ESO reference](#parameter-with-eso-reference)
      - [External Credential Context](#external-credential-context)
        - [External Credential Context `credentials` entry](#external-credential-context-credentials-entry)
        - [External Credential Context `secretStores` entry](#external-credential-context-secretstores-entry)
      - [Pipeline context](#pipeline-context)
      - [Topology context](#topology-context)
      - [EnvGene System Credentials](#envgene-system-credentials)
        - [Authentication to the Secret Store](#authentication-to-the-secret-store)
      - [`eso_support` attribute](#eso_support-attribute)
      - [`SECRET_FLOW` attribute](#secret_flow-attribute)
    - [Environment Instance generation](#environment-instance-generation)
      - [Placeholder Credential auto-generation](#placeholder-credential-auto-generation)
      - [Credential sources and merging](#credential-sources-and-merging)
    - [Effective Set generation](#effective-set-generation)
      - [Deciding between VALS and ESO references](#deciding-between-vals-and-eso-references)
      - [Normalization to `normalizedSecretName`](#normalization-to-normalizedsecretname)
        - [Vault](#vault)
        - [Azure Key Vault](#azure-key-vault)
        - [AWS Secrets Manager](#aws-secrets-manager)
        - [GCP Secret Manager](#gcp-secret-manager)
      - [VALS reference generation](#vals-reference-generation)
      - [ESO reference generation](#eso-reference-generation)
      - [External Credential Context `credentials` entry generation](#external-credential-context-credentials-entry-generation)
      - [Pipeline context generation](#pipeline-context-generation)
      - [Topology context generation](#topology-context-generation)
    - [KV Store Structure](#kv-store-structure)
    - [Credential in BG Deployment Cases](#credential-in-bg-deployment-cases)
    - [Use Cases](#use-cases)
      - [User facing](#user-facing)
      - [System](#system)
    - [Validation](#validation)
      - [During Environment Instance generation](#during-environment-instance-generation)
      - [During Effective Set generation](#during-effective-set-generation)
      - [During CMDB import](#during-cmdb-import)
      - [During Credential Rotation](#during-credential-rotation)
    - [To Do](#to-do)
  - [Open questions](#open-questions)

## Description

This document specifies external credentials for EnvGene: object schemas, Effective Set outputs, and the
generation algorithms.

A minimal end-to-end sample (template, instance repository, Effective Set deployment `values/credentials.yaml`
and `values/external-credentials.yaml` for VALS vs ESO) lives under
[/docs/samples/external-credentials/](/docs/samples/external-credentials/).

## Problem Statement

In the current implementation, EnvGene only supports Credentials that are stored inside files within the repository itself. Integration with external secret stores is not available. Because of this:

1. EnvGene cannot be used in projects where policy prohibits storing secrets in Git, even in encrypted form.
2. There is no possibility for centralized Credential rotation through external tools.

It is necessary to extend EnvGene to support management of Credentials that reside in external secret stores.

## Assumption

1. When migrating to an external secret store, it is necessary to update the EnvGene Environment template
2. Within a given Secret Store, the remote secret is addressed by `normalizedSecretName`, derived from `remoteRefPath`, `credId`, and store type (see [Normalization to normalizedSecretName](#normalization-to-normalizedsecretname))
3. Credential uniqueness within EnvGene repository is determined by `credId`
4. A single Environment Instance uses **either** local Credentials (`usernamePassword`, `secret`) **or** external Credentials (`type: external`) - mixing local and external Credentials in the same Environment Instance is not a supported case. Different Environment Instances in the same repository may differ.
5. CMDB import is not supported for Environment Instances that contain external Credentials. CMDB integration currently expects resolved credential values or local Credentials only.
6. System credentials of the EnvGene template repository are local-only. External Credentials are not
   supported for template-repository system credentials.
7. External Secret Store entries for system credentials are pre-created somehow. EnvGene reads them
   but does not create them.
8. All external Credentials reside in the default Secret Store. Multi-store support is a future step (see
   [To Do](#to-do)).

## Proposed Approach

### Overview

![external-cred](/docs/images/external-cred.png)

The set of EnvGene objects and how they are used differ depending on which approach to managing external secrets is used in a given application: VALS or ESO.

The choice between VALS and ESO at Effective Set generation time is driven by two attributes:

- [`SECRET_FLOW`](#secret_flow-attribute) - environment-side attribute discovered from the Cloud Passport. It selects the secret delivery flow: `helm-values` (VALS) or `external-values` (ESO). The user may override it at the Cloud level.
- [`eso_support`](#eso_support-attribute) - application-side capability marker carried in the Application SBOM. It declares whether the application can be deployed via ESO.

`SECRET_FLOW` decides the shape; `eso_support` is a capability gate used to validate that decision. See [Deciding between VALS and ESO references](#deciding-between-vals-and-eso-references) for the full decision logic.

> [!IMPORTANT]
> The deployment context content therefore differs from one application to another. VALS vs ESO is chosen per application through the effective `SECRET_FLOW` (environment side) constrained by `eso_support` (application side), not on the [Credential](#credential) or any other EnvGene object.

In the EnvGene template, the user:

1. Defines sensitive parameters via [Credential Reference](#credential-reference) in Cloud, Namespace templates or ParamSet
2. Creates a [Credential Template](#credential-template) referenced by the Credential Reference for external Credentials (such templates are only used for external Credentials)

In the instance repository:

1. The same sensitive parameters with the [Credential Reference](#credential-reference) value, which end up on rendered Cloud, Namespace or Application
2. [Credential](#credential) rendered from the [Credential Template](#credential-template)
3. [Secret Store](#secret-store) object

Items 1 and 2 are generated during environment instance generation, 3 is created manually by the user.

When generating the Effective Set, the deployment context contains sensitive parameters whose values are [Parameter with VALS reference](#parameter-with-vals-reference) values when the effective `SECRET_FLOW` for the application is `helm-values`, or [Parameter with ESO reference](#parameter-with-eso-reference) values when the effective `SECRET_FLOW` is `external-values`. See [Deciding between VALS and ESO references](#deciding-between-vals-and-eso-references).

The pipeline context emits sensitive `e2eParameters` whose values resolve to external Credentials into [Pipeline context](#pipeline-context), grouped by the Credential's `secretStore`.

In the [External Credential Context](#external-credential-context):

1. One [External Credential Context `credentials` entry](#external-credential-context-credentials-entry) for each [Credential](#credential) with `type: external` and `create: true`
2. The [Secret Store](#secret-store) definitions copied for each store referenced by those Credentials

### Objects

#### Credential Reference

The Credential Reference (`$type: credRef`) points a parameter in an EnvGene object at an external [Credential](#credential) by `credId`. Optional `property` selects `username` or `password` when the remote secret is modeled with multiple fields. Omit `property` when the Credential has no `properties` list (single-value secret).

This reference is used **only** for `external` Credentials type.

Credential References (`$type: credRef`) are honored in `deployParameters` (deployment context) and
`e2eParameters` (pipeline context). Occurrences in `technicalConfigurationParameters` are not supported:
the runtime context does not accept sensitive parameters via external Credentials.

For backward compatibility, `creds.get()` is still fully supported for working with local Credentials.

The same macro is valid in the environment template and in the instance repository after rendering.

<!-- Or add support for $type: credRef for local Credentials as well? -->

```yaml
# Internal Credential reference
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"
```

```yaml
# External Credential Reference
<parameter-key>:
  # Mandatory
  # Macro type
  $type: credRef
  # Mandatory
  # Pointer to EnvGene Credential
  credId: string
  # Optional: key inside the remote secret
  property: enum [ username, password ]

# Example
global.secrets.streamingPlatform.username:
  $type: credRef
  credId: cdc-streaming-cred
  property: username

global.secrets.streamingPlatform.password:
  $type: credRef
  credId: cdc-streaming-cred
  property: password

# Single-value (Credential has no `properties`)
CONSUL_ADMIN_TOKEN:
  $type: credRef
  credId: postgres-password
```

#### Built-in credential references

Built-in credential references are `credId` string pointers in predefined schema fields of
[Cloud](/docs/envgene-objects.md#cloud), [Namespace](/docs/envgene-objects.md#namespace),
[Tenant](/docs/envgene-objects.md#tenant), and [BG Domain](/docs/envgene-objects.md#bg-domain) objects, as opposed
to free-form [Credential References](#credential-reference) in parameter values.

Each holds a `credId` string. Resolution to a [Credential](#credential) entry happens against the merged
credentials file produced according to [Credential sources and merging](#credential-sources-and-merging).

The catalog and the contexts each reference feeds at Effective Set generation:

| Built-in credential reference              | deploy context                                                                                                                               | topology context                                                         |
|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| `Cloud.defaultCredentialsId`               | -                                                                                                                                            | `k8s_tokens.<namespace>` (fallback when Namespace lacks `credentialsId`) |
| `Cloud.maasConfig.credentialsId`           | `MAAS_CREDENTIALS_USERNAME`, `MAAS_CREDENTIALS_PASSWORD`                                                                                     | -                                                                        |
| `Cloud.dbaasConfigs[].credentialsId`       | `DBAAS_AGGREGATOR_USERNAME`, `DBAAS_AGGREGATOR_PASSWORD`, `DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME`, `DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD` | -                                                                        |
| `Cloud.vaultConfig.credentialsId`          | `VAULT_TOKEN`                                                                                                                                | -                                                                        |
| `Cloud.consulConfig.tokenSecret`           | `CONSUL_ADMIN_TOKEN`                                                                                                                         | -                                                                        |
| `Namespace.credentialsId`                  | -                                                                                                                                            | `k8s_tokens.<namespace>`                                                 |
| `Tenant.credential`                        | -                                                                                                                                            | -                                                                        |
| `BGDomain.controllerNamespace.credentials` | `BG_CONTROLLER_LOGIN`, `BG_CONTROLLER_PASSWORD`                                                                                              | `bg_domain.controllerNamespace.{username,password}`                      |

#### Credential Template

A Credential Template is part of the EnvGene template, a Jinja template used for rendering external [Credentials](#credential). The following applies:

1. There is a **single** Credential Template file per EnvGene template. Its rendered output is a map of `<cred-id>` entries, one entry per external [Credential](#credential).
2. Each rendered entry must conform to the [Credential](#credential) object for `type: external`.
3. It is created manually.
4. It is only used for external Credentials.
5. The path to the Credential Template file is set in the [Template Descriptor](/docs/envgene-objects.md#template-descriptor) as `external_credential_template`. See [Credential Template](/docs/envgene-objects.md#credential-template) in EnvGene Objects.

```yaml
# Example
cdc-streaming-cred:
  type: external
  create: true
  remoteRefPath: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-data-management/cdc
  properties:
    - name: username
    - name: password

consul-creds:
  type: external
  remoteRefPath: {{ current_env.cloud }}
```

#### Credential

A [Credential](/docs/envgene-objects.md#credential) of `type: external`:

1. Describes:
   1. Which external secret store it is located in
   2. Its location in the external secret stores
   3. The creation flag - whether the credential should be idempotently created or not
2. Is generated by EnvGene during Environment Instance generation based on the [Credential Template](#credential-template) (only Jinja rendering without additional processing)
3. Is stored in the Instance repository in the [Credential file](/docs/envgene-objects.md#credential-file) as part of the Environment Instance
4. When generated, the Credential ID does not get a uniqueness prefix - [`inventory.config.updateCredIdsWithEnvName`](/docs/envgene-configs.md#env_definitionyml) is not applied
5. The `properties` attribute describes the structure of the remote secret:

   - Absence of `properties` means the secret has a simple single value structure.
   - When `properties` is present, each item `name` may only be `username` or `password`.
6. If the [Credential Template](#credential-template) does not include the `remoteRefPath` attribute, a default value is used for rendering as:

    ```yaml
    {{ current_env.cloud }}/{{ current_env.name }}
    ```
<!-- 7. **As a possible option** - if `remoteRefPath` is not specified by the user in the Credential Template and the value generated by EnvGene can be represented not as a string, but as an object.

    ```yaml
    remoteRefPath:
      cluster: {{ current_env.cloud }}
      env: {{ current_env.name }}
      namespace: {{ current_env.name }}-data-management
    ``` -->

```yaml
<cred-id>:
  # Mandatory
  type: enum [ usernamePassword, secret, external ]
  # Optional
  # Only for `type: external`
  # Default: default-store
  secretStore: string
  # Required when type is `external` (a default may be applied at render time if omitted in the template)
  remoteRefPath: string
  # Optional
  # Only for `type: external`
  # Default: false
  create: boolean
  # Required when type is `external` and has multiple fields
  # Omit when single-value
  properties:
    - name: enum [ username, password ]
  # Required when type is `usernamePassword` or `secret`
  data:
    username: string
    password: string
    secret: string

# Example
cdc-streaming-cred:
  type: external
  create: true
  remoteRefPath: ocp-05/env-1/env-1-data-management/cdc

consul-creds:
  type: external
  remoteRefPath: ocp-05
```

#### Secret Store

The secret store is configured manually by the user in the instance repository. It is located at `/configuration/secret-stores.yml`.

It may contain several secret store objects:

```yaml
<secret-store-name>:
  type: enum [ vault, azure, aws, gcp ]
  url: URL
  # Required when type is vault
  mountPath: string
  # Required when type is azure
  vaultName: string
  # Required when type is aws
  region: string
  # Required when type is gcp
  projectId: string
```

> [!WARNING]
> A detailed description of the Secret Store, its location, and the principles of interacting with it will be added later.

#### Parameter with VALS reference

A **parameter with VALS reference** is the deployment-side representation of a sensitive parameter after
Effective Set calculation when the effective [`SECRET_FLOW`](#secret_flow-attribute) for the application is
`helm-values`. Parameters that were defined with a [Credential Reference](#credential-reference) (`credRef`)
and resolve to an [external Credential](#credential) are emitted as plain YAML string values - `ref+...` URIs.

Those references are resolved at deploy time to secret material by the Effective Set consumer. A consumer that
supports the VALS URI scheme (for example, `vals` or `argocd-vault-plugin`) resolves them to plain text values.

VALS references are also emitted in the [Pipeline context](#pipeline-context) and
[Topology context](#topology-context). Those sections describe the corresponding file paths and shapes.

Parameters that resolve to VALS references are written under:

```text
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                └── deployment
                    └── <namespace-folder>
                        └── <application-name>
                            └── values
                                └── external-credentials.yaml
```

The Effective Set calculator builds VALS reference from:

1. [Credential Reference](#credential-reference)
2. [Credential](#credential)
3. [Secret Store](#secret-store) metadata for the Credential's `secretStore`

```yaml
# The <vals-uri> form is store-specific.
<parameter-key>: <vals-uri>
```

```yaml
# Example
global.secrets.streamingPlatform.username: ref+gcpsecrets://468649328578/ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred#/username

global.secrets.streamingPlatform.password: ref+gcpsecrets://468649328578/ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred#/password

CONSUL_ADMIN_TOKEN: ref+gcpsecrets://468649328578/ocp-05--postgres-password
```

#### Parameter with ESO reference

A **parameter with ESO reference** is the deployment-side representation of a sensitive parameter after
Effective Set calculation when the effective [`SECRET_FLOW`](#secret_flow-attribute) for the application is
`external-values`. Parameters that were defined with a [Credential Reference](#credential-reference)
(`credRef`) and resolve to an [external Credential](#credential).

Those references are resolved at deploy time to secret material by the Effective Set consumer. The Helm chart
consumes them (one value per parameter path) to render `ExternalSecret` CRs.

Parameters that resolve to ESO references are written under:

```text
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                └── deployment
                    └── <namespace-folder>
                        └── <application-name>
                            └── values
                                └── external-credentials.yaml
```

The Effective Set calculator builds each ESO reference value from:

1. [Credential Reference](#credential-reference)
2. [Credential](#credential)
3. [Secret Store](#secret-store) metadata for the Credential's `secretStore`

```yaml
<parameter-key>:
  # Mandatory
  # id of the Secret Store in EnvGene
  secretStoreId: <secret-store-id>
  # Mandatory
  # Remote secret name after normalization
  normalizedSecretName: <secret-name>
  # Optional
  # Which fields to fetch (one list item per field)
  secretKeys:
    - # Mandatory
      # Backend key name: username, password
      remoteKeyName: enum [ username, password ]
```

```yaml
# Example (multi-field credential: one parameter per property)
global.secrets.streamingPlatform.username:
  secretStoreId: default-store
  normalizedSecretName: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred
  secretKeys:
    - remoteKeyName: username

global.secrets.streamingPlatform.password:
  secretStoreId: default-store
  normalizedSecretName: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred
  secretKeys:
    - remoteKeyName: password

CONSUL_ADMIN_TOKEN:
  secretStoreId: default-store
  normalizedSecretName: ocp-05/postgres-password
```

#### External Credential Context

**External Credential Context** is a separate Effective Set context consisting of a single YAML file that the
Effective Set calculator emits for [Credential](#credential) objects with `type: external` and `create: true`,
and for the [Secret Store](#secret-store) objects referenced by those Credentials.

This context is located at:

```text
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                └── external-credential
                    └── external-credentials.yaml
```

This context, like the others, is produced by the Effective Set calculator.

```yaml
# Only Secret Stores that are referenced
secretStores:
  <secret-store-name>:
    type: enum [ vault, azure, aws, gcp ]
    url: URL
    # Required when type is vault
    mountPath: string
    # Required when type is azure
    vaultName: string
    # Required when type is aws
    region: string
    # Required when type is gcp
    projectId: string
# Only Credential entries with type: external and create: true
credentials:
  <cred-id>:
    secretStoreId: string
    normalizedSecretName: string
    # Omit when the Credential is single-value (no `properties` in the Credential)
    properties:
      - name: enum [ username, password ]
```

##### External Credential Context `credentials` entry

An **External Credential Context `credentials` entry** is one map entry under `credentials` in the External
Credential Context.

The Effective Set calculator builds each `credentials` entry from:

1. External [Credential](#credential) with `create: true`
2. [Secret Store](#secret-store)

The step-by-step algorithm is
[External Credential Context `credentials` entry generation](#external-credential-context-credentials-entry-generation).

##### External Credential Context `secretStores` entry

An **External Credential Context `secretStores` entry** is one map entry under `secretStores` in the External
Credential Context.

The Effective Set calculator copies it from the corresponding [Secret Store](#secret-store) in the instance
repository for each store ID referenced by a
[`credentials` entry](#external-credential-context-credentials-entry) in the same file (same keys and fields
as in the store definition: `type`, `url`, and type-specific settings such as `mountPath`, `vaultName`,
`region`, `projectId`). Only stores that are actually referenced are included.

#### Pipeline context

Sensitive `e2eParameters` resolving to an [external Credential](#credential) are written as VALS references
to two file shapes in the
[Pipeline Parameter Context](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context):

- `effective-set/pipeline/external-credentials.yaml` - the global file, containing every `e2eParameter`
  resolving to an external Credential.
- `effective-set/pipeline/<consumer-name>-external-credentials.yaml` - one file per consumer declared under
  `contexts.pipeline.consumers[]` in the Effective Set config. Contains the subset of `e2eParameters` that
  match the consumer's schema (same selector used for `<consumer-name>-credentials.yaml`).

Both shapes are flat maps of `e2eParameter` key to VALS URI:

```yaml
<parameter-key>: <vals-uri>
<parameter-key>: <vals-uri>
```

Entries are ordered alphabetically by parameter key.

The file locations are:

```text
└── environments
    └── <cluster-name>
        └── <env-name>
            └── effective-set
                └── pipeline
                    ├── external-credentials.yaml
                    └── <consumer-name>-external-credentials.yaml
```

The global file is always emitted. When no `e2eParameter` references an external Credential, it is empty.

#### Topology context

Sensitive fields whose source [Built-in credential reference](#built-in-credential-references) resolves to
an [external Credential](#credential) are written as VALS references to
`effective-set/topology/external-credentials.yaml` - a file in the
[Topology Context](/docs/features/calculator-cli.md#version-20-topology-context).

The file mirrors the shape of `effective-set/topology/credentials.yaml`, with VALS URIs in place of
plain values:

```yaml
k8s_tokens:
  <namespace>: <vals-uri>
bg_domain:
  controllerNamespace:
    username: <vals-uri>
    password: <vals-uri>
```

The [Built-in credential references](#built-in-credential-references) that feed into the Topology
context are:

| Built-in credential reference              | Topology field                                                           |
|--------------------------------------------|--------------------------------------------------------------------------|
| `Namespace.credentialsId`                  | `k8s_tokens.<namespace>`                                                 |
| `Cloud.defaultCredentialsId`               | `k8s_tokens.<namespace>` (fallback when Namespace lacks `credentialsId`) |
| `BGDomain.controllerNamespace.credentials` | `bg_domain.controllerNamespace.{username,password}`                      |

The file location is:

```text
└── environments
    └── <cluster-name>
        └── <env-name>
            └── effective-set
                └── topology
                    └── external-credentials.yaml
```

The file is always emitted.

#### EnvGene System Credentials

System credentials are credentials EnvGene jobs consume for their own operation (registry access, Git
commit and others):

| Parameter                                                                                                      | CI/CD variable                  |
|----------------------------------------------------------------------------------------------------------------|---------------------------------|
| [`self_token`](/docs/envgene-configs.md#integrationyml)                                                        | `GITHUB_TOKEN` / `GITLAB_TOKEN` |
| [`cp_discovery.gitlab.token`](/docs/envgene-configs.md#integrationyml)                                         | none                            |
| [`docker_registry_auth`](/docs/envgene-configs.md#integrationyml)                                              | `GCP_SA_KEY`                    |
| [`<registry>.{username,password}`](/docs/envgene-configs.md#registryyml)                                       | none                            |
| [`<deployer>.{username,token}`](/docs/envgene-configs.md#deployeryml)                                          | none                            |
| [`<artifact-def>.registry.credentialsId`](/docs/envgene-objects.md#artifact-definition)                        | none                            |
| [`<artifact-def>.registry.authConfig.<auth-name>.credentialsId`](/docs/envgene-objects.md#artifact-definition) | none                            |
| [`<reg-def>.credentialsId`](/docs/envgene-objects.md#registry-definition)                                      | none                            |
| [`<reg-def>.authConfig.<auth-name>.credentialsId`](/docs/envgene-objects.md#registry-definition)               | none                            |

The Credential entries live in `/configuration/credentials/credentials.yml`, except for
`<deployer>.{username,token}` whose Credential entries may also live in `deployer-creds.yml` within the
same directory as the referencing `deployer.yml`.

For parameters that have a CI/CD variable, EnvGene resolves the value by source priority:

1. From the configuration file, if the parameter is set there.
2. From the listed CI/CD variable, otherwise.

The integration, registry, and deployer parameters use the [Credential Reference](#credential-reference)
form for external Credentials, or the `envgen.creds.get('<id>').<field>` macro for local Credentials.

The Artifact Definition and Registry Definition `credentialsId` fields use the
[Built-in credential reference](#built-in-credential-references) form (bare `credId` string) regardless
of the referenced Credential's `type`.

System credentials may be local, external, or supplied directly through a CI/CD variable, mixed freely across
parameters. The single-category rule that applies to Environment Instance Credentials does not apply to system
credentials. For the two parameters that have a CI/CD variable, the environment-variable value is treated as
local-equivalent: the value is supplied directly, without a Credential object.

Example for `self_token` referencing an external Credential:

```yaml
# /configuration/integration.yml
self_token:
  $type: credRef
  credId: self-token-cred
```

```yaml
# /configuration/credentials/credentials.yml
self-token-cred:
  type: external
  remoteRefPath: /vcs/envgene-bot
```

Example for an Artifact Definition and a Registry Definition referencing the same external Credential. The
v1.0 form is shown. The v2.0 form uses `authConfig.<auth-name>.credentialsId` in the same way.

```yaml
# /configuration/artifact_definitions/env-template.yaml
registry:
  credentialsId: artifactory-cred
```

```yaml
# /regdefs/sandbox.yml
credentialsId: artifactory-cred
```

```yaml
# /configuration/credentials/credentials.yml
artifactory-cred:
  type: external
  remoteRefPath: /artifactory/qubership
  properties:
    - name: username
    - name: password
```

##### Authentication to the Secret Store

To read system credentials, EnvGene authenticates to the Secret Store. Each Credential entry selects its
store through the `secretStore` field on the [Credential](#credential) (default: `default-store`).
Authentication parameters for that store come from two sources:

- the [Secret Store](#secret-store) object in `/configuration/secret-stores.yml` for non-sensitive values.
- CI/CD variables for sensitive values.

Vault auth:

| Parameter        | Source              | Description                                 |
|------------------|---------------------|---------------------------------------------|
| `type`           | Secret Store object | `vault`                                     |
| `url`            | Secret Store object | Vault server URL                            |
| `VAULT_TOKEN`    | CI/CD variable      | Token-based authentication                  |

GCP auth:

| Parameter                        | Source              | Description                          |
|----------------------------------|---------------------|--------------------------------------|
| `type`                           | Secret Store object | `gcp`                                |
| `GOOGLE_APPLICATION_CREDENTIALS` | CI/CD variable      | Path to the service account key file |

AWS Secrets Manager and Azure Key Vault are not supported as Secret Stores for system credentials.

#### `eso_support` attribute

`eso_support` is an application-side capability marker carried in the Application SBOM. It declares whether the application can be deployed via External Secrets Operator (ESO).

| Attribute   | Value                                                               |
|-------------|---------------------------------------------------------------------|
| Type        | boolean                                                             |
| Scope       | Application                                                         |
| Source      | Application SBOM                                                    |
| Required    | No                                                                  |
| Default     | `false`                                                             |
| Overridable | No - sourced from the Application SBOM and not overridden elsewhere |

See [Deciding between VALS and ESO references](#deciding-between-vals-and-eso-references) for how `eso_support` interacts with `SECRET_FLOW`.

#### `SECRET_FLOW` attribute

`SECRET_FLOW` is an environment-side attribute that selects the secret delivery flow used at deploy time for a given application.

| Attribute       | Value                                                    |
|-----------------|----------------------------------------------------------|
| Type            | enum `[ helm-values, external-values ]`                  |
| Scope           | Cloud, Namespace, Application                            |
| Discovered from | Cloud Passport                                           |
| Override levels | Cloud, Namespace, Application (in increasing precedence) |
| Required        | No                                                       |
| Default         | `helm-values` when the attribute is not set at any level |

Values:

- `helm-values` - sensitive parameters are emitted as **VALS references**
- `external-values` - sensitive parameters are emitted as **ESO references**

> [!NOTE]
> The effective `SECRET_FLOW` is computed per application. Different applications in the same environment may end up with different effective values, so a single Effective Set can mix VALS-shaped and ESO-shaped external parameters across applications.

### Environment Instance generation

#### Placeholder Credential auto-generation

When the [Template Descriptor](/docs/envgene-objects.md#template-descriptor) does not declare an
`external_credential_template` field, EnvGene auto-generates a placeholder local Credential for every
`credId` referenced by a `${creds.get('<credId>')...}` macro or by a
[Built-in credential reference](#built-in-credential-references). The placeholder carries
`data: envgeneNullValue`. If a source (see [Credential sources and merging](#credential-sources-and-merging))
supplies a real Credential for the same `credId`, the source-supplied entry overrides the placeholder in the
merged result.

When the Template Descriptor declares an `external_credential_template` field, auto-generation is disabled.
Every `credId` reachable through a [Built-in credential reference](#built-in-credential-references), a
[`$type: credRef`](#credential-reference) macro, or a `${creds.get(...)}` macro must be explicitly declared by
a source. Missing declarations fail Environment Instance generation with a targeted error.

The Template Descriptor is read per Environment Instance, so different Instances in the same repository may
behave differently.

#### Credential sources and merging

Credential entries in the [Environment Credentials File](/docs/envgene-objects.md#credential-file) are populated
from three sources during Environment Instance generation:

1. **[Credential Template](#credential-template)** - rendered during Environment Instance generation. External
   Credentials only.
2. **Cloud Passport credentials file** (when a Cloud Passport is present) - local or external as declared in
   the Cloud Passport.
3. **[Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file)** - manually authored by the
   user in the instance repository at Environment, Cluster, or Site scope.

All three sources merge into a single [Credential file](/docs/envgene-objects.md#credential-file) per Environment
Instance.

**Precedence on duplicate `credId`.** When the same `credId` is declared in more than one source, the entry from
the higher-precedence source wins. Precedence order (lowest to highest):

1. Credential Template
2. Cloud Passport credentials file
3. [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file)

**Cross-source references are allowed.** A [Credential Reference](#credential-reference) or
[Built-in credential reference](#built-in-credential-references) defined in one source can resolve to a Credential
entry contributed by another source.

Semantic validation (single-category, orphan check, built-in resolution) runs on the **merged result**, not on
individual sources.

### Effective Set generation

#### Deciding between VALS and ESO references

The Effective Set calculator decides between VALS and ESO reference shapes per application using the effective [`SECRET_FLOW`](#secret_flow-attribute) and the application's [`eso_support`](#eso_support-attribute):

| Effective `SECRET_FLOW` | `eso_support`     | Emitted reference shape                          |
|-------------------------|-------------------|--------------------------------------------------|
| `helm-values`           | `false` (default) | [VALS reference](#parameter-with-vals-reference) |
| `helm-values`           | `true`            | [VALS reference](#parameter-with-vals-reference) |
| not set (default)       | not set (default) | [VALS reference](#parameter-with-vals-reference) |
| `external-values`       | `true`            | [ESO reference](#parameter-with-eso-reference)   |
| `external-values`       | `false` (default) | Effective Set generation fails                   |

#### Normalization to `normalizedSecretName`

**Input:**

1. Rendered `remoteRefPath` and `credId` from the [Credential](#credential)
2. `type` from the [Secret Store](#secret-store) referenced by that Credential. It selects which normalization rules apply. Other Secret Store fields are not inputs to `normalizedSecretName`.

**Output:**

1. `normalizedSecretName` used in [VALS reference](#parameter-with-vals-reference), in [ESO reference](#parameter-with-eso-reference), and in [External Credential Context](#external-credential-context).

The algorithm is vendor-specific. Effective Set calculator applies the rules for the target store.

##### Vault

**Constraints:** Long paths are allowed. Allowed characters are `a-zA-Z0-9-/_`. Hierarchical `/` is native.

**Algorithm:**

1. Validate characters
2. `<normalizedSecretName> = <remoteRefPath>/<credId>` (no segment truncation)

##### Azure Key Vault

**Constraints:**

1. Max name length is 127 characters
2. Allowed `a-zA-Z0-9-` (no `/`)
3. Flat names
4. `credId` length at most 32 characters

**Algorithm:**

1. Validate characters
2. Split `remoteRefPath` by `/` (up to four segments)
3. Replace `/` with `--` between segments
4. Truncate long segments per segment cap (20 characters after truncation: 14 chars + `-` + first 5 hex chars of SHA-256 of segment)
5. `<normalizedSecretName> = <normalized-remoteRefPath>--<credId>`
6. Validate total length

##### AWS Secrets Manager

**Constraints:**

1. Max name length is 512 characters
2. Allowed `a-zA-Z0-9-/_+=.@!`
3. Hierarchical `/`
4. `credId` length at most 32 characters

**Algorithm:**

1. Validate characters
2. Keep `/` between segments
3. Truncate segments longer than 119 characters (113 + `-` + SHA-256[0:5])
4. `<normalizedSecretName> = <normalized-remoteRefPath>/<credId>`
5. Validate total length

##### GCP Secret Manager

**Constraints:**

1. Max name length is 255 characters
2. Allowed `a-zA-Z0-9_-` (no `/`)
3. Flat names
4. `credId` length at most 32 characters

**Algorithm:**

1. Validate characters
2. Split by `/` and join segments with `--`
3. Truncate segments longer than 53 characters (47 + `-` + SHA-256[0:5])
4. `<normalizedSecretName> = <normalized-path>--<credId>`
5. Validate total length

#### VALS reference generation

This algorithm constructs a **vals URI** (`ref+...`) for a sensitive parameter resolving to an external
[Credential](#credential). It is invoked by the Effective Set calculator while building:

- **Deployment context** - for each parameter in `deployParameters` whose value is a
  [Credential Reference](#credential-reference) pointing at an external Credential, when the
  application's effective [`SECRET_FLOW`](#secret_flow-attribute) is `helm-values` (see
  [Deciding between VALS and ESO references](#deciding-between-vals-and-eso-references)).
- **Pipeline context** - for each sensitive `e2eParameter` of the Cloud Environment Instance whose
  value is a Credential Reference pointing at an external Credential. The `SECRET_FLOW`
  applicability check does not apply to this context.
- **Topology context** - for each Topology field whose source
  [Built-in credential reference](#built-in-credential-references) resolves to an external Credential. The
  `SECRET_FLOW` applicability check does not apply.

Each input parameter becomes one YAML string value, a vals URI. The placement of the URI within the
Effective Set output is determined by the invoking context.

**Inputs (per target parameter):**

1. The parameter key.
2. The resolved [Credential Reference](#credential-reference): `credId`, optional `property` (`username` or `password` when the Credential declares multiple fields).
3. The rendered [Credential](#credential) for that `credId`: `remoteRefPath`, `secretStore`, and whether the Credential has a `properties` list (multi-field vs single-value secret).
4. The [Secret Store](#secret-store) entry `secretStores[<secretStoreId>]` for `Credential.secretStore`, including `type` and type-specific fields (`mountPath`, `vaultName`, `region`, `projectId`).

**Algorithm:**

1. Compute `normalizedSecretName` using [Normalization to `normalizedSecretName`](#normalization-to-normalizedsecretname). If normalization fails, fail the Effective Set generation.

2. Determine the **URI fragment** (or absence of fragment) from the Credential shape and the [Credential Reference](#credential-reference):

   - **The reference has `property`** (multi-field credentials):
     - Validate that `property` equals one of the `name` values in `Credential.properties`. If it does not, fail the Effective Set generation.
     - Build the fragment from that **reference** value: `#/<property>` (for example `#/username`, `#/password`). Do not invent the fragment from `Credential.properties` alone without the Credential Reference.
   - **The reference has no `property`** (single-value credentials):
     - Validate that referenced Credential has **no** `properties`. If it has, fail the Effective Set generation.
     - Choose the fragment from the [Secret Store](#secret-store) `type` (the reference does not supply `property`):
       - **`vault`**: use `#/value` as the logical key for the single JSON field vals should read.
       - **`azure`, `aws`, `gcp`**: the secret is treated as plain text. **Omit** the `#/...` fragment entirely.

3. Build the **vals URI** by concatenating a **base URI** (scheme, host path, and store-specific segments) with the **fragment suffix** from step 2, if any:

   - **Base URI** depends on the [Secret Store](#secret-store) `type` (use `normalizedSecretName` from step 1 and fields from the Secret Store):
     - **`vault`:** `ref+vault://<mountPath>/data/<normalizedSecretName>` (`mountPath` = KV mount, for example `secret`).
     - **`azure`:** `ref+azurekeyvault://<vaultName>/<normalizedSecretName>` (`vaultName` from the Secret Store).
     - **`aws`:** `ref+awssecrets://<normalizedSecretName>?region=<region>` (`region` from the Secret Store as a query parameter).
     - **`gcp`:** `ref+gcpsecrets://<projectId>/<normalizedSecretName>` (`projectId` from the Secret Store).

   - **Fragment suffix:** whatever step 2 produced as the string starting with `#` (for example `#/username` or `#/value`). If step 2 said to **omit** the fragment (single-value plain text on Azure, AWS, or GCP), the suffix is empty - the final URI is exactly the base URI with no `#/...` part.

   - **Final URI:** `base URI` + `fragment suffix`.

4. Produce `<parameter-key>: "<vals-uri>"` (string scalar). The exact key is the same path as in the
   source parameter (for example `global.secrets.streamingPlatform.username`). Placement in the
   Effective Set output is the responsibility of the invoking context (deployment context: per-application
   `external-credentials.yaml`. Pipeline context: under the `<secret-store-id>` group in
   `effective-set/pipeline/external-credentials.yaml`).

#### ESO reference generation

This applies while the Effective Set calculator builds the **deployment context** for a given application:

1. The effective [`SECRET_FLOW`](#secret_flow-attribute) for the application must be `external-values`, and the application must declare [`eso_support: true`](#eso_support-attribute) in its SBOM (see [Deciding between VALS and ESO references](#deciding-between-vals-and-eso-references)).
2. Only parameters whose values are [Credential References](#credential-reference) pointing at an [external Credential](#credential) are transformed.

The emitted shape per parameter is the object described under [Parameter with ESO reference](#parameter-with-eso-reference).

**Inputs (per target parameter in the deployment context):**

1. The parameter key.
2. The resolved [Credential Reference](#credential-reference): `credId`, optional `property` (`username` or `password` when the Credential declares multiple fields).
3. The rendered [Credential](#credential) for that `credId`: `remoteRefPath`, `secretStore`, and whether the Credential has a `properties` list (multi-field vs single-value secret).
4. The [Secret Store](#secret-store) entry `secretStores[<secretStoreId>]` for `Credential.secretStore`, including `type` and type-specific fields.

**Algorithm:**

1. Compute `normalizedSecretName` using [Normalization to `normalizedSecretName`](#normalization-to-normalizedsecretname). If normalization fails, fail the Effective Set generation.

2. Set `secretStoreId` to `Credential.secretStore`.

3. Set `secretKeys` according to the Credential shape and the [Credential Reference](#credential-reference):

   - **The reference has `property`** (multi-field credentials):
     - Validate that `property` equals one of the `name` values in `Credential.properties`. If it does not, fail the Effective Set generation.
     - Set `secretKeys` to a one-element list using that **reference** value: `- remoteKeyName: <property>`.

   - **The reference has no `property`** (single-value credentials):
     - Validate that referenced Credential has **no** `properties`. If it has, fail the Effective Set generation.
     - Do **not** set a `secretKeys` block.

4. Emit the deployment value at the same path as the source parameter. For multi-field credentials include `secretKeys`; for single-value credentials emit only `secretStoreId` and `normalizedSecretName`.

   ```yaml
   # Multi-field
   <parameter-key>:
     secretStoreId: <from step 2>
     normalizedSecretName: <from step 1>
     secretKeys: <from step 3>

   # Single-value
   <parameter-key>:
     secretStoreId: <from step 2>
     normalizedSecretName: <from step 1>
   ```

#### External Credential Context `credentials` entry generation

This applies while the Effective Set calculator builds the **[External Credential Context](#external-credential-context)**.

1. The Effective Set External Credential Context includes [Credentials](#credential) with `type: external` and `create: true`.
2. Credential References are **not** inputs: each `credentials` entry is derived from [Credential](#credential) and [Secret Store](#secret-store) data only.

The emitted shape per `credId` is the object described under [External Credential Context `credentials` entry](#external-credential-context-credentials-entry).

**Inputs (per Credential):**

1. The rendered [Credential](#credential): `remoteRefPath`, `credId`, `secretStore`, optional `properties`, and `create: true`.
2. The [Secret Store](#secret-store) entry `secretStores[<secretStoreId>]` for `Credential.secretStore`, including `type`.

**Algorithm:**

1. Select every [Credential](#credential) that is `type: external`, `create: true`. If there are none, emit an empty `credentials` map.

2. **Top-level `secretStores`:** for each distinct `secretStoreId` referenced by the selected Credentials, copy the [Secret Store](#secret-store) definition from the instance repository.

3. For each selected Credential, emit the following at `credentials.<credId>`:

   ```yaml
   # Multi-field Credential
   <credId>:
     secretStoreId: <Credential.secretStore>
     normalizedSecretName: <computed>
     properties: <Credential.properties>

   # Single-value Credential
   <credId>:
     secretStoreId: <Credential.secretStore>
     normalizedSecretName: <computed>
   ```

   - `normalizedSecretName` is computed via [Normalization to `normalizedSecretName`](#normalization-to-normalizedsecretname). If normalization fails, fail the Effective Set generation.
   - The `properties` key is present only when `Credential.properties` is defined (multi-field); it is omitted for single-value Credentials.

4. Write the combined payload (`secretStores` from step 2, `credentials` from step 3) to `external-credentials.yaml` at the path defined in [External Credential Context](#external-credential-context).

#### Pipeline context generation

For each sensitive `e2eParameter` whose value is a [Credential Reference](#credential-reference)
resolving to an external Credential, the Effective Set calculator constructs a VALS URI (see
[VALS reference generation](#vals-reference-generation)) and places it at the parameter key in:

1. The global file `effective-set/pipeline/external-credentials.yaml`.
2. Each per-consumer file `effective-set/pipeline/<consumer-name>-external-credentials.yaml` where the
   parameter key matches the consumer's schema. The selector is the same one used for the per-consumer
   local credentials file `<consumer-name>-credentials.yaml`.

Output ordering is deterministic. Each file is emitted regardless of whether any `e2eParameter` resolves
to an external Credential.

#### Topology context generation

For each Topology field whose source [Built-in credential reference](#built-in-credential-references)
resolves to an external Credential, the Effective Set calculator constructs a VALS URI (see
[VALS reference generation](#vals-reference-generation)) and places it at the field path defined in
[Topology context](#topology-context).

The file is emitted at `effective-set/topology/external-credentials.yaml` regardless of whether any
Topology field resolves to an external Credential.

### KV Store Structure

The location of a Credential within the KV Store structure is determined at the moment the Credential is created, i.e., during the deployment of the system/application that the Credential describes.

```text
├── services
└── <cluster-name>
    └── <environment-name>
          └── <namespace>
              └── <application>
```

Example:

```text
├── services
|   └── artfactoryqs-admin
└── ocp-05
    └── platform-01
          └── platform-01-dbaas
              └── dbaas
```

### Credential in BG Deployment Cases

> [!WARNING]
> A description of handling external Credentials in BG Deployment Cases will be added later.

### Use Cases

#### User facing

1. Adding a sensitive parameter
2. Deleting a sensitive parameter
3. Modifying the value of a sensitive parameter (out of scope for EnvGene)
4. Migration from local to VALS/ESO
5. Migration from VALS to ESO
6. Secret store adding

#### System

1. Environment Instance: External Credential Template rendering
   1. `remoteRefPath` is set
   2. `remoteRefPath` default value is used
2. Environment Instance: Credential file generation
   1. Local only
   2. External only
3. Environment Instance: Cloud Passport processing
   1. Local only
   2. External only (including `SECRET_FLOW` discovery from the Cloud Passport)
4. Environment Instance: Env-specific paramSet processing
   1. Local only
   2. External only
5. Effective Set: Deployment Context generation

   > [!NOTE]
   > Subcase **4** below applies to a **multi-application** deployment context within a single Effective Set.
   > Each application is local-only or external-only, and for external applications the effective [`SECRET_FLOW`](#secret_flow-attribute)
   > may differ across applications, so the combined output of one Effective Set can mix VALS-shaped and ESO-shaped external parameters across applications.

   1. Local only
   2. External VALS only (vault, Azure, aws, gcp) * (multiple, single property)
   3. External ESO only (vault, Azure, aws, gcp) * (multiple, single property)
   4. External VALS + ESO across applications (vault, Azure, aws, gcp) * (multiple, single property)
6. Effective Set: External Credential Context generation (vault, Azure, aws, gcp) * (multiple, single property)
7. Effective Set: Secret Store configuration
   1. Single
   2. Multiple
8. Effective Set: `SECRET_FLOW` resolution
   1. Discovered from Cloud Passport only
   2. Override at Cloud level

### Validation

> [!NOTE]
> Schema validation of all EnvGene objects and configuration files referenced in this document is assumed (per
> their JSON schemas under `/schemas/`). The rules below are semantic checks applied on top of schema validation.
>
> Violations of any rule below fail the corresponding generation stage, unless the rule is explicitly marked as
> a warning.
>
> When a rule fails, EnvGene emits a human-readable error identifying the offending object(s), the violated rule,
> and enough context to act on it. This is implied for every rule below and is not repeated per rule.

#### During Environment Instance generation

1. **Reference resolution.** Every [Credential Reference](#credential-reference) in `deployParameters` or
   `e2eParameters`, and every [Built-in credential reference](#built-in-credential-references), resolves to a
   [Credential](#credential) entry in the [Environment Credentials File](/docs/envgene-objects.md#credential-file).

2. **Single category.** Every Environment Instance contains [Credentials](#credential) of only one
   category: either local or external. System credentials (see
   [EnvGene System Credentials](#envgene-system-credentials)) are exempt and may be mixed. Different
   Environment Instances in the same repository may differ.

3. **Orphan check (warning).** Every rendered external [Credential](#credential) is referenced by at least one
   [Credential Reference](#credential-reference) or
   [Built-in credential reference](#built-in-credential-references). Violation surfaces a warning and does not
   fail Environment Instance generation.

4. **No external credentials in runtime context.** No [Credential Reference](#credential-reference)
   (`$type: credRef`) appears in `technicalConfigurationParameters`. The runtime context does not support
   sensitive parameters via external Credentials.

5. **Default store only.** Every external [Credential](#credential) has `secretStore` unset or equal to
   `default-store`. Multi-store support is a future step (see [To Do](#to-do)).

#### During Effective Set generation

1. **Secret store binding.** Every `Credential.secretStore` matches an entry in
   `/configuration/secret-stores.yml`.

2. **Normalization.** Normalization to `normalizedSecretName` succeeds for every used [Credential](#credential)
   under the character-set, per-segment, and total-length constraints of the target [Secret Store](#secret-store)
   type.

3. **SECRET_FLOW domain.** The effective [`SECRET_FLOW`](#secret_flow-attribute) of every application is a value
   from `[ helm-values, external-values ]`.

4. **ESO capability gate.** Every application with effective `SECRET_FLOW = external-values` has
   [`eso_support`](#eso_support-attribute) set to `true`.

5. **Credential Reference property shape.** Every [Credential Reference](#credential-reference) with
   `property: <p>` resolves to a [Credential](#credential) whose `properties` list contains an entry with
   `name: <p>`. Every Credential Reference without `property` resolves to a Credential without `properties`
   (single-value).

6. **System Credential creation flag.** No [system Credential](#envgene-system-credentials) declares
   `create: true`. System credentials are pre-created by the user in the external Secret Store, so they are
   not included in the [External Credential Context](#external-credential-context) creation entries.

7. **System Credential Secret Store type.** Every [system Credential](#envgene-system-credentials) with
   `type: external` references a [Secret Store](#secret-store) of type `vault` or `gcp`. `aws` and `azure`
   are not supported as Secret Stores for system credentials.

8. **Built-in credential reference property shape.** Every
   [Built-in credential reference](#built-in-credential-references) resolving to an external
   [Credential](#credential) whose consumer expects multi-field resolves to a Credential whose `properties` list
   contains an entry for each required `name`. Every Built-in credential reference whose consumer expects a
   single value resolves to a Credential without `properties`. Required shapes per reference are documented in
   the destinations tables in the [Built-in credential references](#built-in-credential-references) section and,
   for references consumed by the artifact-searcher (AppDef/RegDef), in the AppDef v2.0 / RegDef v2.0
   `authConfig` schema (per `provider` + `authMethod`).

#### During CMDB import

1. **No external credentials.** The Environment Instance being imported contains no [Credentials](#credential)
   with `type: external`.

#### During Credential Rotation

1. **No external credentials.** The target [Credential](#credential) has `type: usernamePassword` or
   `type: secret`. External Credentials are not rotatable by EnvGene. Rotation must be performed at the
   [Secret Store](#secret-store) directly.

### To Do

1. Support Blue-Green deployment cases
2. Support template composition
3. Support AWS Secrets Manager as a Secret Store for system credentials
4. Support Azure Key Vault as a Secret Store for system credentials
5. Support multi-store for external Credentials. Encode store identity in the VALS URL via a
   `?secret_store_id=<store-id>` query parameter, extending
   [VALS reference generation](#vals-reference-generation) to emit it for non-default stores. Applies to
   the deploy, pipeline, and topology contexts.
6. Revisit the [External Credential Context](#external-credential-context) shape after the multi-store
   decision lands. With per-Credential `secret_store_id` in the VALS URL, the current `secretStores` map
   and `secretStoreId` field may need restructuring.

## Open questions

1. Whether to skip encryption for values in `effective-set/pipeline/credentials.yaml` when those values are
   VALS reference strings rather than actual secret material.
2. Notation unification. Today the `envgen.creds.get('<id>').<field>` macro is used for local Credentials
   and `$type: credRef` is used for external Credentials. Whether to converge on a single notation, and if
   so, in which direction.
