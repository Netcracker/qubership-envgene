# External Credentials Management

- [External Credentials Management](#external-credentials-management)
  - [Problem Statement](#problem-statement)
  - [Assumption](#assumption)
  - [Proposed Approach](#proposed-approach)
    - [VALS](#vals)
    - [ESO](#eso)
    - [Detailed description of objects](#detailed-description-of-objects)
      - [`credRef` Credential Macro in Environment Template](#credref-credential-macro-in-environment-template)
      - [Credential Template](#credential-template)
      - [Credential](#credential)
      - [Secret Store](#secret-store)
      - [Parameter with VALS reference](#parameter-with-vals-reference)
      - [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry)
      - [External credential Context](#external-credential-context)
      - [External credential Context `credentials` entry](#external-credential-context-credentials-entry)
      - [EnvGene System Credentials](#envgene-system-credentials)
    - [Effective Set external credential behavior](#effective-set-external-credential-behavior)
      - [Normalization to `normalizedSecretName`](#normalization-to-normalizedsecretname)
        - [Vault](#vault)
        - [Azure Key Vault](#azure-key-vault)
        - [AWS Secrets Manager](#aws-secrets-manager)
        - [GCP Secret Manager](#gcp-secret-manager)
      - [Handling the `property` field on `credRef` Credential Macros](#handling-the-property-field-on-credref-credential-macros)
        - [Parameters with VALS reference in deployment context](#parameters-with-vals-reference-in-deployment-context)
        - [Deployment context `externalSecrets` for ESO](#deployment-context-externalsecrets-for-eso)
        - [External credential Context `credentials`](#external-credential-context-credentials)
      - [Shared E2E inputs (Environment Template)](#shared-e2e-inputs-environment-template)
      - [Group 1: Deployment context](#group-1-deployment-context)
        - [Case D1: VALS and Vault](#case-d1-vals-and-vault)
        - [Case D2: VALS and Azure Key Vault](#case-d2-vals-and-azure-key-vault)
        - [Case D3: VALS and AWS Secrets Manager](#case-d3-vals-and-aws-secrets-manager)
        - [Case D4: VALS and GCP Secret Manager](#case-d4-vals-and-gcp-secret-manager)
        - [Case D5: ESO and Vault](#case-d5-eso-and-vault)
        - [Case D6: ESO and Azure Key Vault](#case-d6-eso-and-azure-key-vault)
        - [Case D7: ESO and AWS Secrets Manager](#case-d7-eso-and-aws-secrets-manager)
        - [Case D8: ESO and GCP Secret Manager](#case-d8-eso-and-gcp-secret-manager)
      - [Group 2: External credential Context](#group-2-external-credential-context)
        - [Case G1: External credential Context (Vault)](#case-g1-external-credential-context-vault)
        - [Case G2: External credential Context (Azure Key Vault)](#case-g2-external-credential-context-azure-key-vault)
        - [Case G3: External credential Context (AWS Secrets Manager)](#case-g3-external-credential-context-aws-secrets-manager)
        - [Case G4: External credential Context (GCP Secret Manager)](#case-g4-external-credential-context-gcp-secret-manager)
    - [KV Store Structure](#kv-store-structure)
    - [Credential in BG Deployment Cases](#credential-in-bg-deployment-cases)
    - [Use Cases](#use-cases)

## Problem Statement

In the current implementation, EnvGene only supports Credentials that are stored inside files within the repository itself. Integration with external secret stores is not available. Because of this:

1. EnvGene cannot be used in projects where policy prohibits storing secrets in Git, even in encrypted form.
2. There is no possibility for centralized Credential rotation through external tools.

It is necessary to extend EnvGene to support management of Credentials that reside in external secret stores.

Success criteria:

- EnvGene is able to use external secret stores for storing and retrieving its Credentials (for example, Credentials for accessing a registry when loading templates).
- Integration with external Credentials is implemented in a way that does not break existing handling of local Credentials.
- In the Effective Set, links to external Credentials are properly generated, sufficient for:
  - automatic generation of ExternalSecret CR;
  - enabling integration with the Argo Vault Plugin.
- Support for the following secret stores is implemented:
  - Vault
  - AWS Secrets Manager
  - Azure Key Vault

## Assumption

1. When migrating to an external secret store, it is necessary to update the EnvGene Environment template
2. Within a given `secretStore`, the remote secret is addressed by `normalizedSecretName`, derived from `remoteRefPath`, `credId`, and store type (see [Normalization to normalizedSecretName](#normalization-to-normalizedsecretname))
3. Credential uniqueness within EnvGene repository is determined by `credId`
4. Secret store type is a global configuration at the repository level in EnvGene

## Proposed Approach

![external-cred](/docs/images/external-cred.png)

The set of EnvGene objects and how they are used differ depending on which approach to managing external secrets is used in a given application: VALS or ESO.

The marker for VALS/ESO usage is the `SECRET_MACRO_HANDLER` attribute in the deployment descriptor (DD):

```yaml
SECRET_MACRO_HANDLER: enum [vals, eso]
```

> [!IMPORTANT]
> The deployment context content therefore differs from one application to another. In other words, VALS vs ESO is chosen at the **application** level (via the deployment descriptor), not on the [Credential](#credential) or any other EnvGene object.

### VALS

In the EnvGene template, the user:

1. Defines sensitive parameters via `credRef` [Credential Macro](#credref-credential-macro-in-environment-template) in Cloud, Namespace, and ParamSet templates
2. Creates a [Credential Template](#credential-template) referenced by the `credRef` Credential Macro

In the instance repository:

1. The same sensitive parameters with the `credRef` [Credential Macro](#credref-credential-macro-in-environment-template) value, which end up on rendered Cloud, Namespace, and Application
2. Credential rendered from the [Credential Template](#credential-template)
3. [Secret Store](#secret-store) object

Items 1 and 2 are generated during environment instance generation, 3 is created manually by the user.

When generating the Effective Set, the deployment context contains:

1. Sensitive parameters whose value is a [VALS reference](#parameter-with-vals-reference)

In the [External credential Context](#external-credential-context):

1. [Secret Store](#secret-store) object
2. [External credential Context `credentials` entry](#external-credential-context-credentials-entry) for each `credId` with `create: true`

### ESO

In the ESO scenario:

In the EnvGene template, the user:

1. Creates a [Credential Template](#credential-template)

In the instance repository:

1. Credential rendered from the [Credential Template](#credential-template)
2. [Secret Store](#secret-store) object

As with VALS, 1 is generated during environment instance generation; 2 is created manually by the user.

When generating the Effective Set, the deployment context contains:

1. [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) (`externalSecrets` in Helm values

In the [External credential Context](#external-credential-context):

1. [External credential Context `credentials` entry](#external-credential-context-credentials-entry), derived from the [Credential](#credential) and [Secret Store](#secret-store)
2. [Secret Store](#secret-store) object

For both VALS and ESO, credential generation follows the same rules.

### Detailed description of objects

#### `credRef` Credential Macro in Environment Template

The `credRef` Credential macro (`$type: credRef`) links any parameter in an EnvGene object to a [Credential](#credential).

This macro is used for all types of Credentials (`usernamePassword`, `secret`, `external`).

For backward compatibility, `creds.get()` is still fully supported for working with local Credentials.

```yaml
# AS IS Credential macro
<parameter-key>: "${creds.get('<cred-id>').secret|username|password}"
```

```yaml
# TO BE Credential macro.
<parameter-key>:
  # Mandatory
  # Macro type
  $type: credRef
  # Mandatory
  # Pointer to EnvGene Credential
  credId: string
  # Optional: key inside the remote secret
  property: enum [username, password]

# Example
global.secrets.streamingPlatform.username:
  $type: credRef
  credId: cdc-streaming-cred
  property: username

global.secrets.streamingPlatform.password:
  $type: credRef
  credId: cdc-streaming-cred
  property: password

TOKEN:
  $type: credRef
  credId: app-cred

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
  $type: credRef
  credId: dbaas-creds
  property: username

DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
  $type: credRef
  credId: dbaas-creds
  property: password

DCL_CONFIG_REGISTRY:
  $type: credRef
  credId: artfactoryqs-admin
```

#### Credential Template

A Credential Template is part of the EnvGene template, a Jinja template used for rendering external [Credentials](#credential), which:

1. It must produce a valid [Credential](#credential)
2. It is created manually
3. It is created only for external credentials
4. It is created for each external credential

```yaml
# Example
cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefPath: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-data-management/cdc

app-cred:
  type: external
  secretStore: custom-store
  remoteRefPath: very/special/path

dbaas-creds:
  type: external
  create: true
  secretStore: default-store
  remoteRefPath: {{ current_env.cloud }}

artfactoryqs-admin:
  type: external
  secretStore: default-store
  remoteRefPath: services
```

#### Credential

The existing [Credential](/docs/envgene-objects.md#credential) is extended by introducing a new type `external`, which:

1. Describes:
   1. Which external secret store it is located in
   2. Its location in the external secret stores
   3. The creation flag – whether the credential should be idempotently created or not
2. Is generated by EnvGene during Environment Instance generation based on the [Credential Template](#credential-template)
3. Is stored in the Instance repository in the [Credential file](/docs/envgene-objects.md#credential-file) as part of the Environment Instance
4. When generated, the Credential ID does not get a uniqueness prefix - [`inventory.config.updateCredIdsWithEnvName`](/docs/envgene-configs.md#env_definitionyml) is not applied
5. If the [Credential Template](#credential-template) does not include the `remoteRefPath` attribute, a default value is used for rendering as:

    ```yaml
    {{ current_env.cloud }}/{{ current_env.name }}/{{ current_namespace.name }}
    ```

6. **As a possible option** – if `remoteRefPath` is not specified by the user in the Credential Template and the value generated by EnvGene can be represented not as a string, but as an object.

    ```yaml
    remoteRefPath:
      cluster: {{ current_env.cloud }}
      env: {{ current_env.name }}
      namespace: {{ current_env.name }}-data-management
    ```

```yaml
# AS IS Credential
<cred-id>:
  type: enum[ usernamePassword, secret ]
  data:
    username: string
    password: string
    secret: string
```

```yaml
# TO BE Credential
<cred-id>:
  # Mandatory
  type: enum[ usernamePassword, secret, external ]
  # Optional
  # Used only for type: external
  # Mandatory for type: external
  secretStore: string
  # Optional
  # Used only for type: external
  # Mandatory for type: external
  remoteRefPath: string
  # Optional
  # Used only for type: external
  # Optional for type: external
  create: boolean
  # Optional
  # Used only for type: usernamePassword, secret
  # Mandatory for type: usernamePassword, secret
  data:
    username: string
    password: string
    secret: string

# Example
dbaas-creds:
  type: external
  create: true
  secretStore: default-store
  remoteRefPath: ocp-05/platform-01/platform-01-dbaas/dbaas

cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefPath: ocp-05/env-1/env-1-data-management/cdc

app-cred:
  type: external
  secretStore: custom-store
  remoteRefPath: very/special/path

artfactoryqs-admin:
  type: external
  secretStore: default-store
  remoteRefPath: services
```

#### Secret Store

The secret store is configured manually by the user in the instance repository. It is located at `/configuration/secret-stores.yml`.

It may contain several secret store objects:

```yaml
<secret-store-name>:
  type: enum [vault, azure, aws, gcp]
  url: URL
  # For `vault` only 
  mountPath: string
  # For `azure` only
  vaultName: string
  # For `aws` only
  region: string
  # For `gcp` only
  projectId: string
```

> [!WARNING]
> A detailed description of the Secret Store, its location, and the principles of interacting with it will be added later.

#### Parameter with VALS reference

A **parameter with VALS reference** is the deployment-side representation of a sensitive parameter after Effective Set calculation when `SECRET_MACRO_HANDLER` is `vals`. Parameters that were defined with the [`credRef` Credential Macro](#credref-credential-macro-in-environment-template) and resolve to an [external Credential](#credential) are emitted as plain YAML string values - `ref+...` URIs. Those URIs are resolved at deploy time to secret material.

This is not a separate object file in the instance repository. It is the shape of entries inside the Effective Set deployment context.

Effective Set v2.0 path:

```text
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                └── deployment
                    └── <namespace-folder>
                        └── <application-name>
                            └── values
                                └── deployment-parameters.yaml
```

The Effective Set calculator builds each VALS reference from:

1. [Secret Store](#secret-store) metadata for the Credential's `secretStore`
2. [Credential](#credential)
3. [Credential Macro](#credref-credential-macro-in-environment-template)

```yaml
# one scalar per sensitive parameter; <vals-uri> is store-specific.
<parameter-key>: <vals-uri>
```

```yaml
# Example (GCP Secret Manager; username field inside JSON secret payload)
global.secrets.streamingPlatform.username: ref+gcpsecrets://468649328578/ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred#/username
```

#### Deployment context `externalSecrets` entry

A **Deployment context `externalSecrets` entry** is the deployment-side shape of external credentials when `SECRET_MACRO_HANDLER` is `eso`. The calculator places a top-level `externalSecrets` map in the Effective Set deployment context. The Helm chart consumes that map (for example `range .Values.externalSecrets`) to render `ExternalSecret` CRs.

Effective Set v2.0 path:

```text
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                └── deployment
                    └── <namespace-folder>
                        └── <application-name>
                            └── values
                                └── deployment-parameters.yaml # top-level key `externalSecrets`
```

The Effective Set calculator builds each `externalSecrets` entry from:

1. [Credential](#credential) (`type: external`)
2. [Secret Store](#secret-store)

```yaml
# One map entry per credId. Repeat the list item for each credRef property.
externalSecrets:
  <cred-id>:
    # Mandatory
    secretStoreId: <secret-store-id>
    # Mandatory
    normalizedSecretName: <secret-name>
    # Mandatory
    secretKeys:
      - # Mandatory
        secretKeyName: string
        # Optional
        remoteKeyName: string
```

```yaml
# Example
externalSecrets:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred
    secretKeys:
      - secretKeyName: username
        remoteKeyName: username
      - secretKeyName: password
        remoteKeyName: password
```

#### External credential Context

**External credential Context** is a separate Effective Set context consisting of a single YAML file that the Effective Set calculator emits for Credentials with `create: true` and for the [Secret Store](#secret-store) objects referenced by those Credentials.

Effective Set v2.0 path:

```text
└── environments
    └── <cluster-name-01>
        └── <environment-name-01>
            └── effective-set
                └── external-credential
                    └── external-credential.yaml # top-level key `externalSecrets`
```

This context, like the others, is produced by the Effective Set calculator from Credentials in the EnvGene instance and Secret Stores in the instance repository.

#### External credential Context `credentials` entry

An **External credential Context `credentials` entry** is one map entry under `credentials` in the External credential Context (one per `credId` with `create: true`). The Effective Set calculator sets `secretStoreId`, `normalizedSecretName`, and `properties` when it emits that entry.

```yaml
# Only Secret Stores that are referenced
secretStores: 
  <secret-store-name>:
    type: enum [vault, azure, aws, gcp]
    url: URL
    # For `vault` only 
    mountPath: string
    # For `azure` only
    vaultName: string
    # For `aws` only
    region: string
    # For `gcp` only
    projectId: string
# Only Credential entries with create: true
credentials:
  <cred-id>:
    secretStoreId: string
    normalizedSecretName: string
    properties:
      - name: string
        type: string
```

#### EnvGene System Credentials

EnvGene system credentials are credentials required for the operation of EnvGene itself, for example, credentials to access the registry or a GitLab token to perform commits.

Short term – the values are stored in the CI/CD variables of the EnvGene repository.

Long term – use of a library that leverages the [Secret Store](#secret-store) to retrieve the value from an external secret store.

> [!WARNING]
> A description of handling EnvGene System Credentials will be added later

### Effective Set external credential behavior

This section defines normalization, property handling for external Credentials

#### Normalization to `normalizedSecretName`

**Input:** rendered `remoteRefPath`, `credId`, and `store.type` from the [Credential](#credential) and [Secret Store](#secret-store).

**Output:** `normalizedSecretName` used in [parameters with VALS reference](#parameter-with-vals-reference) , in the [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry), and in the [External credential Context `credentials` entry](#external-credential-context-credentials-entry). The algorithm is vendor-specific. Effective Set calculator applies the rules for the target store.

##### Vault

**Constraints:** Long paths allowed; allowed characters `a-zA-Z0-9-/_`; hierarchical `/` is native.

**Algorithm:**

1. Validate characters
2. `<normalizedSecretName> = <remoteRefPath>/<credId>` (no segment truncation)

##### Azure Key Vault

**Constraints:**

1. Max name length 127
2. Allowed `a-zA-Z0-9-` (no `/`)
3. Flat names
4. `credId` length at most 32 characters

**Algorithm:**

1. Validate characters
2. Split `remoteRefPath` by `/` (up to four segments)
3. Replace `/` with `--` between segments
4. Truncate long segments per segment cap (20 characters after truncation: 15 chars + `-` + first 5 hex chars of SHA-256 of segment)
5. `<normalizedSecretName> = <normalized-path>--<credId>`
6. Validate total length

##### AWS Secrets Manager

**Constraints:**

1. Max name length 512
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

1. Max name length 255
2. Allowed `a-zA-Z0-9_-` (no `/`)
3. Flat names
4. `credId` length at most 32 characters

**Algorithm:**

1. Validate characters
2. Split by `/` and join segments with `--`
3. Truncate segments longer than 53 characters (47 + `-` + SHA-256[0:5])
4. `<normalizedSecretName> = <normalized-path>--<credId>`
5. Validate total length

#### Handling the `property` field on `credRef` Credential Macros

For the same [`credRef` Credential Macros](#credref-credential-macro-in-environment-template) and [Secret Store](#secret-store), the Effective Set calculator can emit up to three kinds of output:

1. [Parameters with VALS reference](#parameter-with-vals-reference) when `SECRET_MACRO_HANDLER` is `vals`.
2. [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) when `SECRET_MACRO_HANDLER` is `eso`.
3. [External credential Context `credentials` entry](#external-credential-context-credentials-entry) when the `create: true` on the [Credential](#credential)

How `property` on the macro is interpreted:

- Set: multiple macros with the same `credId` but different `property` values refer to one backend secret with multiple keys.
- Omitted: the macro targets the whole secret as a single value.

##### Parameters with VALS reference in deployment context

This subsection describes how `property` on [`credRef` Credential Macros](#credref-credential-macro-in-environment-template) affects generation of [parameters with VALS reference](#parameter-with-vals-reference) per `credId` and per [Secret Store](#secret-store) type.

- **Vault**

  - When `property` is set: URI fragment `#/<property>` (for example `#/username`, `#/password`).
  - When `property` is omitted: KV JSON contract key `value`; use fragment `#/value` on the [parameter with VALS reference](#parameter-with-vals-reference).

- **AWS**

  - When `property` is set: URI fragment `#/<property>` (JSON key in the secret payload).
  - When `property` is omitted: plain text secret; VALS URI has no `#/…` fragment.

- **Azure**

  - When `property` is set: URI fragment `#/<property>` (JSON key inside the Key Vault secret).
  - When `property` is omitted: plain text secret; VALS URI has no `#/…` fragment.

- **GCP**

  - When `property` is set: URI fragment `#/<property>` (JSON key in the secret payload).
  - When `property` is omitted: plain text secret; VALS URI has no `#/…` fragment.

##### Deployment context `externalSecrets` for ESO

This subsection describes how `property` on [Credential](#credential) affects generation of the [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) per `credId` and per [Secret Store](#secret-store) type.

- **Vault**

  - When `property` is set: for each `property` value on the [Credential](#credential) for that `credId`, append one `secretKeys` item and set `remoteKeyName` to that `property`.
  - When `property` is omitted: append a single `secretKeys` item with `secretKeyName: value` and `remoteKeyName: value`.

- **AWS**

  - When `property` is set: for each `property` value on the [Credential](#credential) for that `credId`, append one `secretKeys` item and set `remoteKeyName` to that `property`.
  - When `property` is omitted: append one `secretKeys` item with `secretKeyName` only; omit `remoteKeyName`.

- **Azure**

  - When `property` is set: for each `property` value on the [Credential](#credential) for that `credId`, append one `secretKeys` item and set `remoteKeyName` to that `property`.
  - When `property` is omitted: append `secretKeys` items without `remoteKeyName`.

- **GCP**

  - When `property` is set: same as Azure; for each `property` value on the [Credential](#credential) for that `credId`, append one `secretKeys` item and set `remoteKeyName` to that `property`.
  - When `property` is omitted: same as Azure; append `secretKeys` items without `remoteKeyName`.

##### External credential Context `credentials`

This subsection describes how `property` on the [Credential](#credential) affects generation of the `properties` list in the [External credential Context `credentials` entry](#external-credential-context-credentials-entry) per `credId`.

- When `property` is set: for each `property` value on the [Credential](#credential) for that `credId`, append one item to `properties` with `name` set to that `property` (and matching `type` where applicable).
- When `property` is omitted: append a single `properties` item with `name: value` (and `type` as appropriate).

#### Shared E2E inputs (Environment Template)

The following [Credential Macro](#credref-credential-macro-in-environment-template) and [Credential Template](#credential-template) fragments are used across the examples below.

```yaml
# cdc-streaming-cred: Credential Macros with property + Credential Template
global.secrets.streamingPlatform.username:
  $type: credRef
  credId: cdc-streaming-cred
  property: username
global.secrets.streamingPlatform.password:
  $type: credRef
  credId: cdc-streaming-cred
  property: password

cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefPath: ocp-05/env-1/env-1-data-management/cdc
```

```yaml
# postgresql-cred: Credential Macro without property + Credential Template
postgresPassword:
  $type: credRef
  credId: postgresql-cred

postgresql-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefPath: ocp-05/platform-00/platform-00-postgresql/postgres
```

#### Group 1: Deployment context

Deployment context is the Effective Set output consumed at deploy time: either [parameters with VALS reference](#parameter-with-vals-reference) (`vals`) or [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) (`eso`). Inputs are always [Credential Macro](#credref-credential-macro-in-environment-template), rendered [Credential](#credential), and [Secret Store](#secret-store).

##### Case D1: VALS and Vault

**Description:** Each sensitive parameter becomes a [parameter with VALS reference](#parameter-with-vals-reference): a `ref+vault://…` string. Vault KV v2 path uses `<mountPath>/data/<normalizedSecretName>`; JSON keys are selected with URI fragment `#/<property>` (or `#/value` when the [Credential Macro](#credref-credential-macro-in-environment-template) omits `property`).

**Effective Set calculation:**

1. Resolve `secretStore` on the [Credential](#credential) to `secretStores[storeId]` with `type: vault` and read `mountPath`.
2. Compute `normalizedSecretName` from rendered `remoteRefPath`, `credId`, and store type (see [Normalization to normalizedSecretName](#normalization-to-normalizedsecretname)).
3. For each [`credRef` Credential Macro](#credref-credential-macro-in-environment-template) row, emit `<parameter-key>: ref+vault://<mountPath>/data/<normalizedSecretName>#/<property>` where `<property>` is the macro's `property` field or `value` when omitted.

**E2E example:** [Shared E2E inputs (Environment Template)](#shared-e2e-inputs-environment-template); `SECRET_MACRO_HANDLER: vals`.

```yaml
# Secret Store (instance repo) and handler
secretStores:
  default-store:
    type: vault
    url: https://vault.example.com:8200
    mountPath: secret
SECRET_MACRO_HANDLER: vals
```

```yaml
# Effective Set deployment context (parameters with VALS reference: with and without property)
global.secrets.streamingPlatform.username: ref+vault://secret/data/ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred#/username
global.secrets.streamingPlatform.password: ref+vault://secret/data/ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred#/password
postgresPassword: ref+vault://secret/data/ocp-05/platform-00/platform-00-postgresql/postgres/postgresql-cred#/value
```

##### Case D2: VALS and Azure Key Vault

**Description:** Sensitive parameters become [parameters with VALS reference](#parameter-with-vals-reference). URIs are `ref+azurekeyvault://<vaultName>/<normalizedSecretName>`. Secrets with several `property` fields are JSON in Key Vault; fragment `#/<property>` selects a key. When the [Credential Macro](#credref-credential-macro-in-environment-template) has no `property`, the secret is plain text and the URI has no fragment (see [Parameters with VALS reference in deployment context](#parameters-with-vals-reference-in-deployment-context)).

**Effective Set calculation:**

1. Read `vaultName` from `secretStores[storeId]` for `type: azure`.
2. Compute `normalizedSecretName` (Azure rules: `/` to `--`, segment limits; see [Azure Key Vault](#azure-key-vault) under Normalization).
3. Emit `ref+azurekeyvault://<vaultName>/<normalizedSecretName>#/<property>` when `property` is set, or the same URI with no `#/<key>` fragment when it is not.

**E2E example:** same credential shapes as Case D1; [Shared E2E inputs](#shared-e2e-inputs-environment-template).

```yaml
secretStores:
  default-store:
    type: azure
    url: https://vault.azure.net
    vaultName: vaulttests24270
SECRET_MACRO_HANDLER: vals
```

```yaml
global.secrets.streamingPlatform.username: ref+azurekeyvault://vaulttests24270/ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred#/username
global.secrets.streamingPlatform.password: ref+azurekeyvault://vaulttests24270/ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred#/password
postgresPassword: ref+azurekeyvault://vaulttests24270/ocp-05--platform-00--platform-00-postgresql--postgres--postgresql-cred
```

##### Case D3: VALS and AWS Secrets Manager

**Description:** Sensitive parameters become [parameters with VALS reference](#parameter-with-vals-reference): `ref+awssecrets://<normalizedSecretName>?region=<region>`. JSON payloads with multiple keys use fragment `#/<jsonKey>`; when the [Credential Macro](#credref-credential-macro-in-environment-template) has no `property`, the fragment is omitted.

**Effective Set calculation:**

1. Read `region` from `secretStores[storeId]` for `type: aws`.
2. Compute `normalizedSecretName` (AWS path rules; see [AWS Secrets Manager](#aws-secrets-manager) under Normalization).
3. Append `?region=<region>` to the VALS URI; add `#/<jsonKey>` only when multiple JSON keys apply.

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template).

```yaml
secretStores:
  default-store:
    type: aws
    url: https://secretsmanager.amazonaws.com
    region: us-east-1
SECRET_MACRO_HANDLER: vals
```

```yaml
global.secrets.streamingPlatform.username: ref+awssecrets://ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred?region=us-east-1#/username
global.secrets.streamingPlatform.password: ref+awssecrets://ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred?region=us-east-1#/password
postgresPassword: ref+awssecrets://ocp-05/platform-00/platform-00-postgresql/postgres/postgresql-cred?region=us-east-1
```

##### Case D4: VALS and GCP Secret Manager

**Description:** Sensitive parameters become [parameters with VALS reference](#parameter-with-vals-reference): `ref+gcpsecrets://<projectId>/<normalizedSecretName>`. Multiple `property` fields use a JSON payload and `#/<property>`; when the [Credential Macro](#credref-credential-macro-in-environment-template) has no `property`, the fragment is omitted.

**Effective Set calculation:**

1. Read `projectId` from `secretStores[storeId]` for `type: gcp`.
2. Compute `normalizedSecretName` (GCP flat name rules; see [GCP Secret Manager](#gcp-secret-manager) under Normalization).
3. Build `ref+gcpsecrets://<projectId>/<normalizedSecretName>` and add `#/<property>` only when required for JSON with multiple keys.

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template).

```yaml
secretStores:
  default-store:
    type: gcp
    url: https://secretmanager.googleapis.com
    projectId: 468649328578
SECRET_MACRO_HANDLER: vals
```

```yaml
global.secrets.streamingPlatform.username: ref+gcpsecrets://468649328578/ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred#/username
global.secrets.streamingPlatform.password: ref+gcpsecrets://468649328578/ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred#/password
postgresPassword: ref+gcpsecrets://468649328578/ocp-05--platform-00--platform-00-postgresql--postgres--postgresql-cred
```

##### Case D5: ESO and Vault

**Description:** The deployment context contains the [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) (`externalSecrets` in Helm values). The application Helm chart renders `ExternalSecret` CRs with `remoteRef.key` = `normalizedSecretName` and optional `remoteRef.property` for JSON keys. A `SecretStore` CR whose name matches `secretStoreId` must exist in the namespace.

**Effective Set calculation:**

1. Set `SECRET_MACRO_HANDLER: eso`.
2. For each `credId`, group [`credRef` Credential Macros](#credref-credential-macro-in-environment-template) and emit one [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) with `secretStoreId`, `normalizedSecretName`, and `secretKeys` (`secretKeyName`, `remoteKeyName` when the backend needs a property path).

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template); `externalSecrets` Helm values and rendered `ExternalSecret` fragment (`postgresql-cred` without `property`).

```yaml
secretStores:
  default-store:
    type: vault
    url: https://vault.example.com:8200
    mountPath: secret
SECRET_MACRO_HANDLER: eso
```

```yaml
# Deployment context externalSecrets (Credential Macros with property)
externalSecrets:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred
    secretKeys:
      - secretKeyName: username
        remoteKeyName: username
      - secretKeyName: password
        remoteKeyName: password
```

```yaml
# Deployment context externalSecrets (Credential Macro without property)
externalSecrets:
  postgresql-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/platform-00/platform-00-postgresql/postgres/postgresql-cred
    secretKeys:
      - secretKeyName: value
        remoteKeyName: value
```

```yaml
# Rendered ExternalSecret (excerpt after Helm)
spec:
  data:
    - secretKey: value
      remoteRef:
        key: ocp-05/platform-00/platform-00-postgresql/postgres/postgresql-cred
        property: value
```

##### Case D6: ESO and Azure Key Vault

**Description:** Same [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) shape as Case D5; `normalizedSecretName` follows Azure limits and delimiter rules (may differ from the VALS URI for the same logical path). When the [Credential Macro](#credref-credential-macro-in-environment-template) has no `property`, Helm items omit `remoteKeyName` for plain text (see [Deployment context externalSecrets for ESO](#deployment-context-externalsecrets-for-eso)).

**Effective Set calculation:** Same as Case D5 with Azure normalization for `normalizedSecretName` (see [Azure Key Vault](#azure-key-vault) under Normalization).

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template); YAML below.

```yaml
secretStores:
  default-store:
    type: azure
    url: https://vault.azure.net
    vaultName: vaulttests24270
SECRET_MACRO_HANDLER: eso
```

```yaml
externalSecrets:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05--env-1--env-1-data-manag-805d2--cdc--cdc-streaming-cred
    secretKeys:
      - secretKeyName: username
        remoteKeyName: username
      - secretKeyName: password
        remoteKeyName: password
  postgresql-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05--platform-00--platform-00-post-be108--postgres--postgresql-cred
    secretKeys:
      - secretKeyName: value
```

##### Case D7: ESO and AWS Secrets Manager

**Description:** Same [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) shape; AWS uses hierarchical `normalizedSecretName` with `/` (Azure uses `--` and flat names; see [AWS Secrets Manager](#aws-secrets-manager) vs [Azure Key Vault](#azure-key-vault) under Normalization).

**Effective Set calculation:** Same as Case D5 with AWS normalization (see [AWS Secrets Manager](#aws-secrets-manager) under Normalization).

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template); YAML below.

```yaml
secretStores:
  default-store:
    type: aws
    url: https://secretsmanager.amazonaws.com
    region: us-east-1
SECRET_MACRO_HANDLER: eso
```

```yaml
externalSecrets:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred
    secretKeys:
      - secretKeyName: username
        remoteKeyName: username
      - secretKeyName: password
        remoteKeyName: password
  postgresql-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/platform-00/platform-00-postgresql/postgres/postgresql-cred
    secretKeys:
      - secretKeyName: value
```

##### Case D8: ESO and GCP Secret Manager

**Description:** Same [Deployment context `externalSecrets` entry](#deployment-context-externalsecrets-entry) shape; `normalizedSecretName` follows GCP flat naming and segment truncation rules.

**Effective Set calculation:** Same as Case D5 with GCP normalization (see [GCP Secret Manager](#gcp-secret-manager) under Normalization).

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template); YAML below.

```yaml
secretStores:
  default-store:
    type: gcp
    url: https://secretmanager.googleapis.com
    projectId: 468649328578
SECRET_MACRO_HANDLER: eso
```

```yaml
externalSecrets:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred
    secretKeys:
      - secretKeyName: username
        remoteKeyName: username
      - secretKeyName: password
        remoteKeyName: password
  postgresql-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05--platform-00--platform-00-postgresql--postgres--postgresql-cred
    secretKeys:
      - secretKeyName: value
```

#### Group 2: External credential Context

The Effective Set calculator emits [External credential Context](#external-credential-context) as a separate YAML artifact: [Secret Store](#secret-store) configuration and an [External credential Context `credentials` entry](#external-credential-context-credentials-entry) for each [Credential](#credential) with `create: true`.

##### Case G1: External credential Context (Vault)

**Description:** The calculator emits **External credential Context** YAML: [Secret Store](#secret-store) configuration and an [External credential Context `credentials` entry](#external-credential-context-credentials-entry) per `credId` with `normalizedSecretName` and `properties` (see [External credential Context `credentials`](#external-credential-context-credentials)).

**Effective Set calculation:**

1. Select [Credentials](#credential) rendered from the [Credential Template](#credential-template) with `create: true`.
2. Group all [`credRef` Credential Macros](#credref-credential-macro-in-environment-template) by `credId`; map each `property` to `properties[].name` / `type` (when `property` is omitted, use `name: value`).
3. Copy store config into `secretStores`; set `credentials[credId].secretStoreId` from the Credential's `secretStore`.
4. Compute `normalizedSecretName` = `normalize(remoteRefPath, credId, vault)` (see [Vault](#vault) under Normalization).

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template); [External credential Context `credentials` entry](#external-credential-context-credentials-entry) below (`cdc-streaming-cred`, `postgresql-cred`).

```yaml
secretStores:
  default-store:
    type: vault
    url: https://vault.example.com:8200
    mountPath: secret

credentials:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred
    properties:
      - name: username
        type: username
      - name: password
        type: password
  postgresql-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/platform-00/platform-00-postgresql/postgres/postgresql-cred
    properties:
      - name: value
        type: password
```

##### Case G2: External credential Context (Azure Key Vault)

**Description:** Same [External credential Context `credentials` entry](#external-credential-context-credentials-entry) shape as Case G1. `normalizedSecretName` follows Azure normalization (flattened path; see [Azure Key Vault](#azure-key-vault) under Normalization).

**Effective Set calculation:** Steps 1 to 3 as Case G1; step 4 uses Azure normalization for `normalizedSecretName`.

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template); [External credential Context `credentials` entry](#external-credential-context-credentials-entry) below.

```yaml
secretStores:
  default-store:
    type: azure
    url: https://vault.azure.net
    vaultName: vaulttests24270

credentials:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05--env-1--env-1-data-manag-7b2e1--cdc--cdc-streaming-cred
    properties:
      - name: username
        type: username
      - name: password
        type: password
  postgresql-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05--platform-00--platform-00-post-c4f3a--postgres--postgresql-cred
    properties:
      - name: value
        type: password
```

##### Case G3: External credential Context (AWS Secrets Manager)

**Description:** Same [External credential Context `credentials` entry](#external-credential-context-credentials-entry) shape as Case G1. `normalizedSecretName` follows AWS normalization (see [AWS Secrets Manager](#aws-secrets-manager) under Normalization).

**Effective Set calculation:** Steps 1 to 3 as Case G1; step 4 uses AWS normalization for `normalizedSecretName`.

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template); [External credential Context `credentials` entry](#external-credential-context-credentials-entry) below.

```yaml
secretStores:
  default-store:
    type: aws
    url: https://secretsmanager.amazonaws.com
    region: us-east-1

credentials:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred
    properties:
      - name: username
        type: username
      - name: password
        type: password
  postgresql-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05/platform-00/platform-00-postgresql/postgres/postgresql-cred
    properties:
      - name: value
        type: password
```

##### Case G4: External credential Context (GCP Secret Manager)

**Description:** Same [External credential Context `credentials` entry](#external-credential-context-credentials-entry) shape as Case G1. `normalizedSecretName` follows GCP normalization (see [GCP Secret Manager](#gcp-secret-manager) under Normalization).

**Effective Set calculation:** Steps 1 to 3 as Case G1; step 4 uses GCP normalization for `normalizedSecretName`.

**E2E example:** [Shared E2E inputs](#shared-e2e-inputs-environment-template); [External credential Context `credentials` entry](#external-credential-context-credentials-entry) below.

```yaml
secretStores:
  default-store:
    type: gcp
    url: https://secretmanager.googleapis.com
    projectId: 468649328578

credentials:
  cdc-streaming-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05--env-1--env-1-data-management--cdc--cdc-streaming-cred
    properties:
      - name: username
        type: username
      - name: password
        type: password
  postgresql-cred:
    secretStoreId: default-store
    normalizedSecretName: ocp-05--platform-00--platform-00-postgresql--postgres--postgresql-cred
    properties:
      - name: value
        type: password
```

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
> A description of handling external Credentials in BG Deployment Cases will be added later

### Use Cases

1. Adding a sensitive parameter
2. Deleting a sensitive parameter
3. Modifying the value of a sensitive parameter (out of scope for EnvGene)
4. Migration from local to VALS/ESO
   1. Migration from VALS to ESO
5. Secret store adding
