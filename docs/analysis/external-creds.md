# External Credentials Management

- [External Credentials Management](#external-credentials-management)
  - [Problem Statement](#problem-statement)
  - [Assumption](#assumption)
  - [Proposed Approach](#proposed-approach)
    - [`credRef` Credential Macro in Environment Template](#credref-credential-macro-in-environment-template)
    - [Credential Template](#credential-template)
    - [Credential](#credential)
    - [`extCredRef` Credential Macro in Effective Set](#extcredref-credential-macro-in-effective-set)
      - [`remoteRefKey` Normalization](#remoterefkey-normalization)
    - [Secret Macro Handler in DD](#secret-macro-handler-in-dd)
    - [EnvGene System Credentials](#envgene-system-credentials)
    - [Secret Store](#secret-store)
    - [KV Store Structure](#kv-store-structure)
    - [Credential in BG Deployment Cases](#credential-in-bg-deployment-cases)
    - [Transformation](#transformation)
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
2. Credential uniqueness within a `secretStore` is determined by `remoteRefKey`
3. Credential uniqueness within EnvGene repository is determined by `credId`
4. Secret store type is a global configuration at the repository level in EnvGene

## Proposed Approach

![external-cred](/docs/images/external-cred.png)

### `credRef` Credential Macro in Environment Template

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
  # Optional
  # Path to the specific value inside the secret
  # For Vault only. Other external credential stores do not allow using this attribute
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

### Credential Template

A Credential Template is part of the EnvGene template, a Jinja template used for rendering external [Credentials](#credential), which:

1. It must produce a valid [Credential](#credential)
2. It is created manually
3. It is created only for external credentials
4. It is created for each external credential
5. Is associated with a template in the [Template Descriptor](/docs/envgene-objects.md#template-descriptor)

```yaml
# Example
cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}/{{ current_env.name }}/{{ current_env.name }}-data-management/cdc

app-cred:
  type: external
  secretStore: custom-store
  remoteRefKey: very/special/path

dbaas-creds:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: {{ current_env.cloud }}

artfactoryqs-admin:
  type: external
  secretStore: default-store
  remoteRefKey: services
```

### Credential

The existing [Credential](/docs/envgene-objects.md#credential) is extended by introducing a new type `external`, which:

1. Describes:
   1. Which external secret store it is located in
   2. Its location in the external secret stores
   3. The creation flag – whether the credential should be idempotently created or not
2. Is generated by EnvGene during Environment Instance generation based on the [Credential Template](#credential-template)
3. Is stored in the Instance repository in the [Credential file](/docs/envgene-objects.md#credential-file) as part of the Environment Instance
4. When generated, the Credential ID does not get a uniqueness prefix - [`inventory.config.updateCredIdsWithEnvName`](/docs/envgene-configs.md#env_definitionyml) is not applied
5. If the [Credential Template](#credential-template) does not include the `remoteRefKey` attribute, a default value is used for rendering as:

    ```yaml
    {{ current_env.cloud }}/{{ current_env.name }}/{{ current_namespace.name }}
    ```

6. **As a possible option** – if `remoteRefKey` is not specified by the user in the Credential Template and the value generated by EnvGene can be represented not as a string, but as an object.

    ```yaml
    remoteRefKey:
      cluster: {{ current_env.cloud }}
      env: {{ current_env.name }}
      namespace: {{ current_env.name }}-data-management
    ```

```yaml
# AS IS Credential
<cred-id>:
  type: usernamePassword|secret
  data:
    username: string
    password: string
    secret: string
```

```yaml
# TO BE Credential
<cred-id>:
  # Mandatory
  type: usernamePassword|secret|external
  # Optional
  # Used only for type: external
  # Mandatory for type: external
  secretStore: string
  # Optional
  # Used only for type: external
  # Mandatory for type: external
  remoteRefKey: string
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
  remoteRefKey: ocp-05/platform-01/platform-01-dbaas/dbaas

cdc-streaming-cred:
  type: external
  create: true
  secretStore: default-store
  remoteRefKey: ocp-05/env-1/env-1-data-management/cdc

app-cred:
  type: external
  secretStore: custom-store
  remoteRefKey: very/special/path

artfactoryqs-admin:
  type: external
  secretStore: default-store
  remoteRefKey: services
```

### `extCredRef` Credential Macro in Effective Set

The `extCredRef` Credential macro (`$type: extCredRef`) links any parameter in the [Effective Set](/docs/features/calculator-cli.md#effective-set-v20) to a credential that is stored in an external secret store.

1. EnvGene generates the `extCredRef` macro based on:
   1. An external [Credential](#credential)
   2. The `credRef` Credential macro
2. The `remoteRefKey` is generated according to the type of external secret store, as described in [`remoteRefKey` Normalization](#remoterefkey-normalization).

Parameters described using `extCredRef` Credential macro are included in:

1. Deployment context
   1. The Credential macro is resolved/handled into an actual value by either:
      1. Argo Vault Plugin – in this case, the context in which the Helm chart is rendered receives the value of the sensitive parameter **OR**
      2. External Secret Operator – in this case, the context in which the Helm chart is rendered receives the unchanged `extCredRef` macro
   2. The handler (ArgoCD or ESO) is specified in the DD, as described in [Secret Macro Handler in DD](#secret-macro-handler-in-dd)
   3. When EnvGene processes the DD while generating the Effective Set, it places the parameter in different Effective Set files:
      1. `credentials.yaml` – the macro will be handled by Argo Vault Plugin **OR**
      2. `parameters.yaml` – the macro will be handled by External Secret Operator

2. Pipeline context
   1. To be used by the pipelines themselves
   2. For creation
      1. Such Credential macros are grouped under a parameter with a contract name
      2. Only those formed from [Credentials](#credential) with `type: external` and `create: true` are included there

```yaml
# TO BE Credential macro.
<parameter-key>:
  # Mandatory
  $type: extCredRef
  # Mandatory
  secretStore: string
  # Mandatory
  remoteRefKey: string

# Vault example
global.secrets.streamingPlatform.username:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred-username

global.secrets.streamingPlatform.password:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: ocp-05/env-1/env-1-data-management/cdc/cdc-streaming-cred-password

TOKEN:
  $type: extCredRef
  secretStore: custom-store
  remoteRefKey: very/special/path/app-cred

DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: ocp-05/platform-01/platform-01-dbaas/dbaas/dbaas-creds-username

DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: ocp-05/platform-01/platform-01-dbaas/dbaas/dbaas-creds-password

DCL_CONFIG_REGISTRY:
  $type: extCredRef
  secretStore: default-store
  remoteRefKey: services/artfactoryqs-admin
```

#### `remoteRefKey` Normalization

Different external secret stores have different requirements for the `remoteRefKey`:

1. **Azure**: 127 character limit. Only `0-9, a-z, A-Z` allowed. [Documentation](https://learn.microsoft.com/en-us/azure/key-vault/general/about-keys-secrets-certificates)
2. **GCP**: 255 character limit. Only `[a-zA-Z0-9-_]+` allowed. [Documentation](https://docs.cloud.google.com/secret-manager/docs/creating-and-accessing-secrets#create-secret-console)
3. **AWS**: 512 character limit. Only `0-9, a-z, A-Z, /_+=.@-` allowed. [Documentation](https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_CreateSecret.html#API_CreateSecret_RequestSyntax)
4. **Vault**: No name limits. [Documentation](https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2)

For each external secret store type, normalization of the `remoteRefKey` is performed during the Effective Set generation stage in EnvGene to meet the requirements of the specific external secret store.

<!-- 1. Vault: `<remoteRefKey>/<credId>-<property>`
2. AWS: `<remoteRefKey>/<credId>` +512 char
3. GCP: `<remoteRefKey>/<credId>` 255 char
4. Azure: `<remoteRefKey>/<credId>` 127 char -->

> [!WARNING]
> A detailed description of the normalization algorithm, including handling of the `property`, will be added later.

<!-- ### `ExternalSecret` CR

```yaml
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: credId
spec:
  secretStoreRef:
    name: <secret-store>
    kind: SecretStore
  target:
    ...
  data:
    - # When <property> is not present - secretKey: <cred-id>
      secretKey: <cred-id>.<property>
      remoteRef:
        key: <remote-ref-key>
        # Optional
        # Used only if <property> is specified
        property: <property>

# Example. Username + Password
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: dbaas-creds
spec:
  secretStoreRef:
    name: default-store
    kind: SecretStore
  target:
    ...
  data:
    - secretKey: dbaas-creds.username
      remoteRef:
        key: ocp-05/platform-01/platform-01-dbaas/dbaas
        property: username
    - secretKey: dbaas-creds.password  
      remoteRef:
        key: ocp-05/platform-01/platform-01-dbaas/dbaas
        property: password

---
# Example. No <property>
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: consul-cred
spec:
  secretStoreRef:
    name: default-store
    kind: SecretStore
  target:
    ...
  data:
    - secretKey: consul-cred
      remoteRef:
        key: ocp-05
``` -->

### Secret Macro Handler in DD

In DD, the `SECRET_MACRO_HANDLER` attribute is introduced. It is set during the application's build phase and describes whether the application can work with the External Secret Operator or if ArgoCD should resolve the value using the Argo Vault Plugin.

```yaml
SECRET_MACRO_HANDLER: enum [argo, eso]
```

### EnvGene System Credentials

EnvGene system credentials are credentials required for the operation of EnvGene itself, for example, credentials to access the registry or a GitLab token to perform commits.

Short term – the values are stored in the CI/CD variables of the EnvGene repository.

Long term – use of a library that leverages the [Secret Store](#secret-store) to retrieve the value from an external secret store.

### Secret Store

```yaml
secretStore:
  name: string
  type: enum [azure, vault, aws, gcp]
  url: URL
  auth: map
```

> [!WARNING]
> A detailed description of the Secret Store, its location, and the principles of interacting with it will be added later.

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

### Transformation

![external-cred-transformation](/docs/images/external-cred-transformation.png)

### Use Cases

1. Adding a sensitive parameter
2. Deleting a sensitive parameter
3. Modifying the value of a sensitive parameter (out of scope for EnvGene)
4. Migration from local to external Credential storage
