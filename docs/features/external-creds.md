# External Credentials Management

- [External Credentials Management](#external-credentials-management)
  - [Description](#description)
  - [Problem Statement](#problem-statement)
  - [Assumption](#assumption)
  - [Proposed Approach](#proposed-approach)
    - [Overview](#overview)
    - [Detailed description of objects](#detailed-description-of-objects)
      - [Credential Reference](#credential-reference)
      - [Credential Template](#credential-template)
      - [Credential](#credential)
      - [Secret Store](#secret-store)
      - [Parameter with VALS reference](#parameter-with-vals-reference)
      - [Parameter with ESO reference](#parameter-with-eso-reference)
      - [External Credential Context](#external-credential-context)
        - [External Credential Context `credentials` entry](#external-credential-context-credentials-entry)
        - [External Credential Context `secretStores` entry](#external-credential-context-secretstores-entry)
      - [EnvGene System Credentials](#envgene-system-credentials)
    - [Effective Set external credential behavior](#effective-set-external-credential-behavior)
      - [Normalization to `normalizedSecretName`](#normalization-to-normalizedsecretname)
        - [Vault](#vault)
        - [Azure Key Vault](#azure-key-vault)
        - [AWS Secrets Manager](#aws-secrets-manager)
        - [GCP Secret Manager](#gcp-secret-manager)
      - [VALS reference generation](#vals-reference-generation)
      - [ESO reference generation](#eso-reference-generation)
      - [External Credential Context `credentials` entry generation](#external-credential-context-credentials-entry-generation)
    - [KV Store Structure](#kv-store-structure)
    - [Credential in BG Deployment Cases](#credential-in-bg-deployment-cases)
    - [Use Cases](#use-cases)
      - [User facing](#user-facing)
      - [System](#system)
    - [Validation](#validation)
      - [During Environment Instance generation](#during-environment-instance-generation)
      - [During Effective Set generation](#during-effective-set-generation)
    - [To Do](#to-do)

## Description

This document specifies external credentials for EnvGene: the `credRef` Credential Reference, `external` [Credential](#credential) objects, [Secret Store](#secret-store) configuration, Effective Set outputs (VALS, ESO, External Credential Context), and per-store normalization of remote secret names.

A minimal end-to-end sample (template, instance repository, Effective Set deployment `values/credentials.yaml` and `values/external-credentials.yaml` for VALS vs ESO) lives under [/docs/samples/external-credentials/](/docs/samples/external-credentials/).

## Problem Statement

In the current implementation, EnvGene only supports Credentials that are stored inside files within the repository itself. Integration with external secret stores is not available. Because of this:

1. EnvGene cannot be used in projects where policy prohibits storing secrets in Git, even in encrypted form.
2. There is no possibility for centralized Credential rotation through external tools.

It is necessary to extend EnvGene to support management of Credentials that reside in external secret stores.

## Assumption

1. When migrating to an external secret store, it is necessary to update the EnvGene Environment template
2. Within a given `secretStore`, the remote secret is addressed by `normalizedSecretName`, derived from `remoteRefPath`, `credId`, and store type (see [Normalization to normalizedSecretName](#normalization-to-normalizedsecretname))
3. Credential uniqueness within EnvGene repository is determined by `credId`

## Proposed Approach

### Overview

![external-cred](/docs/images/external-cred.png)

The set of EnvGene objects and how they are used differ depending on which approach to managing external secrets is used in a given application: VALS or ESO.

The marker for VALS/ESO usage is the `SECRET_MACRO_HANDLER` attribute in the deployment descriptor (DD):

```yaml
SECRET_MACRO_HANDLER: enum [ vals, eso ]
```

> [!IMPORTANT]
> The deployment context content therefore differs from one application to another. In other words, VALS vs ESO is chosen at the **application** level (via the Deployment Descriptor), not on the [Credential](#credential) or any other EnvGene object.

In the EnvGene template, the user:

1. Defines sensitive parameters via [Credential Reference](#credential-reference) in Cloud, Namespace templates or ParamSet
2. Creates a [Credential Template](#credential-template) referenced by the Credential Reference for external Credentials (such templates are only used for external Credentials)

In the instance repository:

1. The same sensitive parameters with the [Credential Reference](#credential-reference) value, which end up on rendered Cloud, Namespace or Application
2. [Credential](#credential) rendered from the [Credential Template](#credential-template)
3. [Secret Store](#secret-store) object

Items 1 and 2 are generated during environment instance generation, 3 is created manually by the user.

When generating the Effective Set, the deployment context contains sensitive parameters whose values are [Parameter with VALS reference](#parameter-with-vals-reference) values when `SECRET_MACRO_HANDLER` is `vals`, or [Parameter with ESO reference](#parameter-with-eso-reference) values when `SECRET_MACRO_HANDLER` is `eso`.

In the [External Credential Context](#external-credential-context):

1. One [External Credential Context `credentials` entry](#external-credential-context-credentials-entry) for each [Credential](#credential) with `type: external` and `create: true`
2. The [Secret Store](#secret-store) definitions copied for each store referenced by those Credentials

### Detailed description of objects

#### Credential Reference

The Credential Reference (`$type: credRef`) points a parameter in an EnvGene object at an external [Credential](#credential) by `credId`. Optional `property` selects `username` or `password` when the remote secret is modeled with multiple fields. Omit `property` when the Credential has no `properties` list (single-value secret).

This reference is used **only** for `external` Credentials type.

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

#### Credential Template

A Credential Template is part of the EnvGene template, a Jinja template used for rendering external [Credentials](#credential). The following applies:

1. It must render to a valid [Credential](#credential).
2. It is created manually.
3. It is only used for external Credentials.
4. There is typically one template per external Credential.
5. The path to the Credential Template file is set in the [Template Descriptor](/docs/envgene-objects.md#template-descriptor) as `external_credential_template`. See [Credential Template](/docs/envgene-objects.md#credential-template) in EnvGene Objects.

```yaml
# Example
cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefPath: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-data-management/cdc
  properties:
    - name: username
    - name: password

consul-creds:
  type: external
  secretStore: default-store
  remoteRefPath: {{ current_env.cloud }}
```

#### Credential

The existing [Credential](/docs/envgene-objects.md#credential) is extended by introducing a new type `external`, which:

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
    {{ current_env.cloud }}/{{ current_env.name }}/{{ current_namespace.name }}
    ```
<!-- 7. **As a possible option** - if `remoteRefPath` is not specified by the user in the Credential Template and the value generated by EnvGene can be represented not as a string, but as an object.

    ```yaml
    remoteRefPath:
      cluster: {{ current_env.cloud }}
      env: {{ current_env.name }}
      namespace: {{ current_env.name }}-data-management
    ``` -->

```yaml
# AS IS Credential
<cred-id>:
  type: enum [ usernamePassword, secret ]
  data:
    username: string
    password: string
    secret: string
```

```yaml
# TO BE Credential
<cred-id>:
  # Mandatory
  type: enum [ usernamePassword, secret, external ]
  # Required when type is `external`
  secretStore: string
  # Required when type is `external` (a default may be applied at render time if omitted in the template)
  remoteRefPath: string
  # Optional
  # Only for `type: external`
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
  secretStore: default-store
  remoteRefPath: ocp-05/env-1/env-1-data-management/cdc

consul-creds:
  type: external
  secretStore: default-store
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

A **parameter with VALS reference** is the deployment-side representation of a sensitive parameter after Effective Set calculation when `SECRET_MACRO_HANDLER` is `vals`. Parameters that were defined with a [Credential Reference](#credential-reference) (`credRef`) and resolve to an [external Credential](#credential) are emitted as plain YAML string values - `ref+...` URIs.

Those references are resolved at deploy time to secret material by the Effective Set consumer. VALS Argo resolves them to plain text values.

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

A **parameter with ESO reference** is the deployment-side representation of a sensitive parameter after Effective Set calculation when `SECRET_MACRO_HANDLER` is `eso`. Parameters that were defined with a [Credential Reference](#credential-reference) (`credRef`) and resolve to an [external Credential](#credential).

Those references are resolved at deploy time to secret material by the Effective Set consumer. The Helm chart consumes them (one value per parameter path) to render `ExternalSecret` CRs.

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

**External Credential Context** is a separate Effective Set context consisting of a single YAML file that the Effective Set calculator emits for [Credential](#credential) objects with `type: external` and `create: true`, and for the [Secret Store](#secret-store) objects referenced by those Credentials.

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

An **External Credential Context `credentials` entry** is one map entry under `credentials` in the External Credential Context.

The Effective Set calculator builds each `credentials` entry from:

1. [Credential](#credential) (`type: external`, `create: true`)
2. [Secret Store](#secret-store)

The step-by-step algorithm is [External Credential Context `credentials` entry generation](#external-credential-context-credentials-entry-generation).

##### External Credential Context `secretStores` entry

An **External Credential Context `secretStores` entry** is one map entry under `secretStores` in the External Credential Context.

The Effective Set calculator copies it from the corresponding [Secret Store](#secret-store) in the instance repository for each store id referenced by a [`credentials` entry](#external-credential-context-credentials-entry) in the same file (same keys and fields as in the store definition: `type`, `url`, and type-specific settings such as `mountPath`, `vaultName`, `region`, `projectId`). Only stores that are actually referenced are included.

#### EnvGene System Credentials

EnvGene system credentials are credentials required for the operation of EnvGene itself, for example, credentials to access the registry or a GitLab token to perform commits.

Short term - the values are stored in the CI/CD variables of the EnvGene repository.

Long term - use of a library that leverages the [Secret Store](#secret-store) to retrieve the value from an external secret store.

> [!WARNING]
> A description of handling EnvGene System Credentials will be added later.

### Effective Set external credential behavior

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
4. Truncate long segments per segment cap (20 characters after truncation: 15 chars + `-` + first 5 hex chars of SHA-256 of segment)
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

This applies while the Effective Set calculator builds the **deployment context** for a given application:

1. The application’s deployment descriptor (DD) must declare `SECRET_MACRO_HANDLER: vals`.
2. Only parameters whose values are [Credential References](#credential-reference) pointing at an [external Credential](#credential) are transformed.

Each such parameter becomes one YAML string value, a **vals URI** (`ref+...`).

**Inputs (per target parameter in the deployment context):**

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

4. Emit the deployment value: `<parameter-key>: "<vals-uri>"` (string scalar). The exact key is the same path as in the source parameter (for example `global.secrets.streamingPlatform.username`).

#### ESO reference generation

This applies while the Effective Set calculator builds the **deployment context** for a given application:

1. The application’s deployment descriptor (DD) must declare `SECRET_MACRO_HANDLER: eso`.
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

1. Select every [Credential](#credential) that is `type: external`, `create: true`. If there are none, emit an empty `credentials` map or omit the file per product rules.

2. **Top-level `secretStores`:** for each distinct `secretStoreId` referenced by the selected Credentials, copy the [Secret Store](#secret-store) definition from the instance repository.

3. For each selected Credential:

   1. Compute `normalizedSecretName` using [Normalization to `normalizedSecretName`](#normalization-to-normalizedsecretname). If normalization fails, fail the Effective Set generation.

   2. Set `secretStoreId` to `Credential.secretStore`.

   3. Build the optional `properties` list:

      - **Multi-field Credential** (`Credential.properties` is present): emit one list item per entry in `Credential.properties`, each item `- name: <name>` in Credential order (for example `username`, `password`).

      - **Single-value Credential** (no `properties` on the Credential): **omit** the `properties` key on this `credentials` entry.

   4. Emit `credentials.<credId>` with `secretStoreId`, `normalizedSecretName`, and `properties` when step 3.3 produced a list.

4. Write the combined payload (`secretStores` from step 2, `credentials` from step 3) to `external-credentials.yaml` at the path defined in [External Credential Context](#external-credential-context).

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
   3. Local + External
3. Environment Instance: Cloud Passport processing
   1. Local only
   2. External only
4. Environment Instance: Env-specific paramSet processing
   1. Local only
   2. External only
   3. Local + External
5. Effective Set: Deployment Context generation

   > [!NOTE]
   > Subcases **4** and **5** below apply to a **multi-application** deployment context within a single Effective Set: each application keeps a single handler, but different applications may use different handlers, so the combined output can mix VALS-shaped and ESO-shaped external parameters (and local splits) across apps.

   1. Local only
   2. External VALS only (vault, azure, aws, gcp) * (multiple, single property)
   3. External ESO only (vault, azure, aws, gcp) * (multiple, single property)
   4. External VALS + ESO (vault, azure, aws, gcp) * (multiple, single property)
   5. Local + External VALS + ESO (vault, azure, aws, gcp) * (multiple, single property)
6. Effective Set: External Credential Context generation (vault, azure, aws, gcp) * (multiple, single property)
7. Effective Set: Secret Store configuration
   1. Single
   2. Multiple

### Validation

#### During Environment Instance generation

1. Every `creds.get` macro resolves to a [Credential](#credential) with `type: usernamePassword` or `type: secret` (local Credentials only).

2. Every external [Credential](#credential) referenced by a Credential Reference is defined in a [Credential Template](#credential-template) and present in the instance repository after Environment Instance generation.

3. The same `credId` must not denote both a local Credential (`usernamePassword` / `secret`) and an external Credential in the same environment. Local definitions come from Environment Instance generation for `${creds.get(...)}`; external definitions come from the Credential Template and [Environment Credentials File](/docs/envgene-objects.md#environment-credentials-file) as described in this document.

#### During Effective Set generation

1. Every `credId` referenced by a [Credential Reference](#credential-reference) resolves to an existing [Credential](#credential).

2. When a reference includes `property`, that `property` matches a `name` in `Credential.properties` for that Credential (and single-value Credentials must not use `property`).

3. Every [Credential Reference](#credential-reference) (`credRef`) resolves to a [Credential](#credential) with `type: external`.

### To Do

1. Support Blue-Green deployment cases
2. Support system-level external credentials
3. Support external credentials in the runtime context
4. Support template composition
