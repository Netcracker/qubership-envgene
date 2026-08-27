
# Instance Pipeline Parameters

- [Instance Pipeline Parameters](#instance-pipeline-parameters)
  - [Parameters](#parameters)
    - [`ENV_NAMES`](#env_names)
    - [`CLUSTER_NAME`](#cluster_name)
    - [`ENVIRONMENT_NAME`](#environment_name)
    - [`PIPELINE_TYPE`](#pipeline_type)
    - [`OPERATION_TYPE`](#operation_type)
    - [`BGD_OPERATION`](#bgd_operation)
    - [`BG_NS_TARGET`](#bg_ns_target)
    - [`BG_STATE`](#bg_state)
    - [`NAMESPACE_NAMES`](#namespace_names)
    - [`DELTA_DEPLOY`](#delta_deploy)
    - [`ENV_BUILDER`](#env_builder)
    - [`GET_PASSPORT`](#get_passport)
    - [`CMDB_IMPORT`](#cmdb_import)
    - [`CMDB_IMPORT_APP_DEFS`](#cmdb_import_app_defs)
    - [`CMDB_IMPORT_REG_DEFS`](#cmdb_import_reg_defs)
    - [`DEPLOYMENT_TICKET_ID`](#deployment_ticket_id)
    - [`ENV_TEMPLATE_VERSION`](#env_template_version)
    - [`ENV_TEMPLATE_VERSION_UPDATE_MODE`](#env_template_version_update_mode)
    - [`ENV_INVENTORY_CONTENT`](#env_inventory_content)
    - [`GENERATE_EFFECTIVE_SET`](#generate_effective_set)
    - [`EFFECTIVE_SET_CONFIG`](#effective_set_config)
    - [`EXTERNAL_CREDENTIAL_PROVISIONING`](#external_credential_provisioning)
    - [`CUSTOM_PARAMS`](#custom_params)
    - [`APPLICATION_VERSIONS`](#application_versions)
    - [`DEPLOY_POSTFIXES_FILTER`](#deploy_postfixes_filter)
    - [`NAMESPACE_NAMES_FILTER`](#namespace_names_filter)
    - [`COMPONENT_NAMES_FILTER`](#component_names_filter)
    - [`WAVE_NAMES_FILTER`](#wave_names_filter)
    - [`SD_VERSION`](#sd_version)
    - [`SD_DATA`](#sd_data)
    - [`SD_REPO_MERGE_MODE`](#sd_repo_merge_mode)
    - [`DEPLOYMENT_SESSION_ID`](#deployment_session_id)
    - [`CRED_ROTATION_PAYLOAD`](#cred_rotation_payload)
      - [Affected Parameters and Troubleshooting](#affected-parameters-and-troubleshooting)
    - [`CRED_ROTATION_FORCE`](#cred_rotation_force)
    - [`GH_ADDITIONAL_PARAMS`](#gh_additional_params)
  - [Deprecated Parameters](#deprecated-parameters)
    - [`SD_DELTA`](#sd_delta)
    - [`ENV_SPECIFIC_PARAMS`](#env_specific_params)
    - [`ENV_TEMPLATE_NAME`](#env_template_name)
    - [`ENV_INVENTORY_INIT`](#env_inventory_init)
  - [Parameter value formats](#parameter-value-formats)
  - [Multiple Values Support](#multiple-values-support)

The following are the launch parameters for the instance repository pipeline. These parameters influence, the execution
of specific jobs within the pipeline.

All parameters are of the string data type

> [!IMPORTANT]
> EnvGene recognises and processes **only the parameters listed on this page**. Passing any variable not documented here
> has no effect on pipeline behaviour and will be silently ignored.
>
> Do not rely on undocumented parameters - they are not part of the EnvGene contract and may be removed or conflict with
> future additions without notice.

## Parameters

### `ENV_NAMES`

**Description**: Specifies the environment(s) for which processing will be triggered. Uses the
`<cluster-name>/<env-name>` notation. When `CLUSTER_NAME` and `ENVIRONMENT_NAME` are both provided, they are
used for single-environment processing and take precedence over `ENV_NAMES`, which is ignored.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

If specifying more than one environment, separate them as described in [Multiple Values
Support](#multiple-values-support).
For multiple environments, each environment will initiate its own independent pipeline flow, using the same set of
pipeline parameters for all.

**Default Value**: None

**Mandatory**: No. Required when `CLUSTER_NAME` and `ENVIRONMENT_NAME` are not provided.

**Example**:

- Single environment: `ocp-01/platform`
- Multiple environments: `k8s-01/env-1,k8s-01/env2`

### `CLUSTER_NAME`

**Description**: Cluster identifier of the target environment. Together with `ENVIRONMENT_NAME` it forms an `ENV_NAMES`
entry in `<cluster-name>/<env-name>` notation. When `CLUSTER_NAME` and `ENVIRONMENT_NAME` are both provided, they are
used for single-environment processing and take precedence over `ENV_NAMES`, which is ignored.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

**Default Value**: None

**Mandatory**: No. Required when `ENV_NAMES` is not provided.

**Example**: `k8s-01`

### `ENVIRONMENT_NAME`

**Description**: Environment identifier of the target environment. Together with `CLUSTER_NAME` it forms an `ENV_NAMES`
entry in `<cluster-name>/<env-name>` notation. When `CLUSTER_NAME` and `ENVIRONMENT_NAME` are both provided, they are
used for single-environment processing and take precedence over `ENV_NAMES`, which is ignored.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

**Default Value**: None

**Mandatory**: No. Required when `ENV_NAMES` is not provided.

**Example**: `env-1`

### `PIPELINE_TYPE`

**Description**: Selects the pipeline execution model.

**Allowed values**: `GITLAB_DEPLOY`, `LEGACY`

**Default Value**: `LEGACY`

**Mandatory**: No

**Example**: `GITLAB_DEPLOY`

### `OPERATION_TYPE`

**Description**: The pipeline operation type for the environment.

Processed at both pipeline types. The `CLEAN` and `BGD` values are processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

**Allowed values**:

- `DEPLOY`
  Deploys the applications.
- `CLEAN`
  Cleans the namespaces.
- `BGD`
  Runs a Blue-Green operation selected by `BGD_OPERATION`.

**Default Value**: `DEPLOY`

**Mandatory**: No

**Example**: `CLEAN`

### `BGD_OPERATION`

**Description**: Selects the Blue-Green operation. Processed only when `OPERATION_TYPE: BGD`. The
state-transition operations consume `BG_STATE` to set the state files. Warmup does not.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

**Allowed values**: `warmup`, `commit`, `promote`, `rollback`, `init-domain`

**Default Value**: None

**Mandatory**: No

**Example**: `warmup`

### `BG_NS_TARGET`

**Description**: Selects the physical Blue-Green side, origin or peer, for the operation. Used to resolve which
`bgNsArtifacts` template version is updated with `ENV_TEMPLATE_VERSION`, and to resolve the origin or peer namespace of
a `deployPostfix` in the namespace map.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

**Allowed values**: `ORIGIN`, `PEER`

**Default Value**: None

**Mandatory**: No

**Example**: `ORIGIN`

### `BG_STATE`

**Description**: The target Blue-Green state. Its value is a BGState object under a root `BGState` key. Only
`BGState.originNamespace.state` and `BGState.peerNamespace.state` are read. All other fields (`name`,
`version`, `updateTime`, `controllerNamespace`) are ignored. The Blue-Green state-setting step writes the
origin and peer state of the state files directly from it, without validation.

Processed only when `OPERATION_TYPE: BGD`. Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

**Default Value**: None

**Mandatory**: No

**Example**:

```yaml
BGState:
  controllerNamespace: dev-14-datahub
  originNamespace:
    name: dev-14-bss-origin
    state: active
    version: v1
  peerNamespace:
    name: dev-14-bss-peer
    state: idle
    version: null
  updateTime: 2026-08-17T11:14:31Z
```

### `NAMESPACE_NAMES`

**Description**: The namespaces to clean. Active only when `OPERATION_TYPE: CLEAN`, ignored under others (a warning is
logged). An empty value means all namespaces of the environment.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

If specifying more than one, separate them as described in [Multiple Values Support](#multiple-values-support).

**Default Value**: None. Empty means all namespaces of the environment.

**Mandatory**: No

**Example**: `env-1-bss,env-1-oss`

### `DELTA_DEPLOY`

**Description**: Controls the delta deployment mode.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

**Allowed values**: `NONE`, `DIFF`, `DIFF_AND_HEAL`

**Default Value**: `NONE`

**Mandatory**: No

**Example**: `DIFF`

### `ENV_BUILDER`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

Effective only at `PIPELINE_TYPE: LEGACY`. At `PIPELINE_TYPE: GITLAB_DEPLOY` the Environment Instance is generated
based on the operation, regardless of this flag.

If `true`:
In the pipeline, Environment Instance generation job is executed. Environment Instance generation will be launched.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `GET_PASSPORT`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

If `true`:
  In the pipeline, Cloud Passport discovery job is executed. Cloud Passport discovery will be launched.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `CMDB_IMPORT`

**Description**: Feature flag. Valid values are `true` or `false`.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

If `true`:
  The Environment Instance will be exported to an external CMDB system.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `CMDB_IMPORT_APP_DEFS`

**Description**: Feature flag. Valid values are `true` or `false`.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

If `true`:
  Application Definitions are exported to an external CMDB system.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `CMDB_IMPORT_REG_DEFS`

**Description**: Feature flag. Valid values are `true` or `false`.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

If `true`:
  Registry Definitions are exported to an external CMDB system.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `DEPLOYMENT_TICKET_ID`

**Description**: Used as commit message prefix for commit into Instance repository.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

**Default Value**: None

**Mandatory**: No

**Example**: `TICKET-ID-12345`

### `ENV_TEMPLATE_VERSION`

**Description**: If provided system update Environment Template version in the Environment Inventory. System overrides
`envTemplate.templateArtifact.artifact.version` OR `envTemplate.artifact` at
`/environments/<ENV_NAME>/Inventory/env_definition.yml`

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

**Default Value**: None

**Mandatory**: No

**Example**: `env-template:v1.2.3`

### `ENV_TEMPLATE_VERSION_UPDATE_MODE`

**Description**: Controls how ENV_TEMPLATE_VERSION is applied during the pipeline run.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

**Allowed values**:

- `PERSISTENT` (default)
  Applies the standard behavior: the pipeline updates the template version in Environment Inventory by modifying
`envTemplate.artifact` (or `envTemplate.templateArtifact.artifact.version`) in `env_definition.yml`.

- `TEMPORARY`
  Applies `ENV_TEMPLATE_VERSION` **only for the current pipeline execution** and **does not** update
`envTemplate.artifact` (or `envTemplate.templateArtifact.artifact.version`) in `env_definition.yml`.
  The pipeline updates `generatedVersions.generateEnvironmentLatestVersion` in `env_definition.yml` to reflect the
template artifact version that was actually applied in this run, for example:

  ```yaml
  # env_definition.yml
  generatedVersions:
    generateEnvironmentLatestVersion: "template-project:feature-diis1125-20251125.045717-2"
  ```

**Default Value**: `PERSISTENT`

**Mandatory**: No

**Example**: `PERSISTENT`

### `ENV_INVENTORY_CONTENT`

**Description**:

Provides the Environment Inventory and related artifacts to be created or updated.
It allows external systems to manage `env_definition.yml` and additional files paramsets, credentials, resource profiles
without manual changes in the Instance repository.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

See details in Environment Inventory Generation feature documentation [Environment Inventory
Generation](/docs/features/env-inventory-generation.md)

**Default Value**: None

**Mandatory**: No

**Example**:

```yaml
envDefinition:
  action: create_or_replace
  content:
    inventory:
      environmentName: env-1
      tenantName: Applications
      cloudName: cluster-1
      description: Fullsample
      owners: Qubershipteam
      config:
        updateRPOverrideNameWithEnvName: false
        updateCredIdsWithEnvName: true
    envTemplate:
      name: composite-prod
      artifact: project-env-template:master_20231024-080204
      additionalTemplateVariables:
        ci:
          CI_PARAM_1: ci-param-val-1
          CI_PARAM_2: ci-param-val-2
        e2eParameters:
          E2E_PARAM_1: e2e-param-val-1
          E2E_PARAM_2: e2e-param-val-2
      sharedTemplateVariables:
      - prod-template-variables
      - sample-cloud-template-variables
      envSpecificParamsets:
        bss:
        - env-specific-bss
      envSpecificTechnicalParamsets:
        bss:
        - env-specific-tech
      envSpecificE2EParamsets:
        cloud:
        - cloud-level-params
      sharedMasterCredentialFiles:
      - prod-integration-creds
      envSpecificResourceProfiles:
        cloud:
        - cloud-specific-profile
paramsets:
- action: create_or_replace
  place: env
  content:
    version: <paramset-version>
    name: env-specific-bss
    parameters:
      key: value
    applications: []
credentials:
- action: create_or_replace
  place: site
  content:
    prod-integration-creds:
      type: <credential-type>
      data:
        username: <value>
        password: <value>
resourceProfiles:
- action: create_or_replace
  place: cluster
  content:
    name: cloud-specific-profile
    baseline: dev
    description: ''
    applications:
    - name: core
      version: release-20241103.225817
      sd: ''
      services:
      - name: operator
        parameters:
        - name: GATEWAY_MEMORY_LIMIT
          value: 96Mi
        - name: GATEWAY_CPU_REQUEST
          value: 50m
    version: 0
```

### `GENERATE_EFFECTIVE_SET`

**Description**: Feature flag. Valid values ​​are `true` or `false`.

Effective only at `PIPELINE_TYPE: LEGACY`. At `PIPELINE_TYPE: GITLAB_DEPLOY` the Effective Set is generated based
on the operation, regardless of this flag.

If `true`:
  In the pipeline, Effective Set generation job is executed. Effective Parameter set generation will be launched

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `EFFECTIVE_SET_CONFIG`

**Description**: Settings for effective set configuration. This is used together with `GENERATE_EFFECTIVE_SET`.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

```yaml
version: <v1.0|v2.0>
effective_set_expiry: <effective-set-expiry-time>
app_chart_validation: <boolean>
enable_traceability: <boolean>
contexts:
  pipeline:
    consumers:
      - name: <consumer-component-name>
        version: <consumer-component-version>
        schema: <json-schema-in-string>
```

| Attribute                                 | Mandatory | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Default                                | Example                                            |
|-------------------------------------------|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|----------------------------------------------------|
| **version**                               | Optional  | The version of the effective set to be generated. Available options are `v1.0` and `v2.0`. EnvGene uses `--effective-set-version` to pass this attribute to the Calculator CLI.                                                                                                                                                                                                                                                                                                                                                                                      | `v2.0`                                 | `v2.0`                                             |
| **app_chart_validation**                  | Optional  | [App chart validation](/docs/features/calculator-cli.md#version-20-app-chart-validation) feature flag. This validation checks whether all applications in the solution for which the effective set is being calculated are built using the app chart model. If at least one is not, the calculation fails. If `true`: validation is performed, if `false`: validation is skipped                                                                                                                                                                                     | `true`                                 | `false`                                            |
| **effective_set_expiry**                  | Optional  | The duration for which the effective set (stored as a job artifact) will remain available for download. Envgene passes this value unchanged to: 1) The `retention-days` job attribute in case of GitHub pipeline. 2) The `expire_in` job attribute in case of GitLab pipeline. The exact syntax and constraints differ between platforms. Refer to the GitHub and GitLab documentation for details.                                                                                                                                                                  | GitLab: `1 hours`, GitHub: `1` (day)   | GitLab: `2 hours`, GitHub: `2`                     |
| **enable_traceability**                   | Optional  | Feature flag that enables traceability functionality in the effective set generation. When set to `true`, the Calculator CLI will include additional traceability information in the generated effective set, allowing tracking of parameter sources and transformations. When set to `false`, traceability information is not included.                                                                                                                                                                                                                             | `false`                                | `true`                                             |
| **contexts.pipeline.consumers**           | Optional  | Each entry in this list adds a [consumer-specific pipeline context component](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context) to the Effective Set. EnvGene passes the path to the corresponding JSON schema file to the Calculator command-line tool using the `--pipeline-consumer-specific-schema-path` argument. Each list element is passed as a separate argument.                                                                                                                                                                     | None                                   | None                                               |
| **contexts.pipeline.consumers[].name**    | Mandatory | The name of the [consumer-specific pipeline context component](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context). If used without `contexts.pipeline.consumers[].schema`, the component must be pre-registered in EnvGene                                                                                                                                                                                                                                                                                                                      | None                                   | `dcl`                                              |
| **contexts.pipeline.consumers[].version** | Mandatory | The version of the [consumer-specific pipeline context component](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context). If used without `contexts.pipeline.consumers[].schema`, the component must be pre-registered in EnvGene.                                                                                                                                                                                                                                                                                                                  | None                                   | `v1.0`                                             |
| **contexts.pipeline.consumers[].schema**  | Optional  | The content of the consumer-specific pipeline context component JSON schema transformed into a string. It is used to generate a consumer-specific pipeline context for a consumer not registered in EnvGene. EnvGene saves the value as a JSON file with the name `<contexts.pipeline[].name>-<contexts.pipeline[].version>.schema.json` and passes the path to it to the Calculator command-line tool via `--pipeline-consumer-specific-schema-path` attribute. The schema obtained in this way is not saved between pipeline runs and must be passed for each run. | None                                   | [consumer-v1.0.json](/docs/examples/consumer-v1.0.json) |

Registered component JSON schemas are stored in the EnvGene Docker image as JSON files named:
`<consumers-name>-<consumer-version>.schema.json`

Consumer-specific pipeline context components registered in EnvGene:

1. None

**Example**:

```yaml
version: v2.0
app_chart_validation: 'false'
```

### `EXTERNAL_CREDENTIAL_PROVISIONING`

**Description**: Selects the provisioning mode for external Credentials in the `generate_effective_set` job. The
Effective Set calculator always writes the [External Credential Context](/docs/features/external-creds.md#external-credential-context),
regardless of this value. This parameter controls only whether EnvGene then invokes the
[External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md).

Valid values:

- `apply`: EnvGene invokes the CLI in apply mode. Each Credential is created or validated in its Secret Store.
- `skip`: EnvGene does not invoke the CLI. No Credential is created or validated and no Secret Store is read. Use
  this mode during migration to external Credentials, when the target Secret Store is not yet populated.

The value `dry-run` is reserved for a future validate-only mode and is not yet implemented.

See [Credential provisioning](/docs/features/external-creds.md#credential-provisioning).

**Default Value**: `apply`

**Mandatory**: No

**Example**: `skip`

### `CUSTOM_PARAMS`

**Description**: Session-scoped parameters injected into the Effective Set during parameter calculation. Custom Params
are not persisted across parameter calculation sessions, have the highest priority in the parameter resolution
hierarchy, and are treated as sensitive.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

`CUSTOM_PARAMS` is only applied when [`GENERATE_EFFECTIVE_SET`](#generate_effective_set) is `true`. If
`GENERATE_EFFECTIVE_SET` is `false`, the `generate_effective_set` job does not run and `CUSTOM_PARAMS` has no effect.

EnvGene passes the value unchanged to the Calculator CLI via `--custom-params`. See [Calculator
CLI](/docs/features/calculator-cli.md) for how Custom Params are applied to the Effective Set.

**Format**: A map conforming to the [schema](/schemas/custom-params.schema.json). See
[Parameter value formats](#parameter-value-formats).

Two modes are supported. The modes are **mutually exclusive** - a payload that contains both a top-level
`deployment`/`runtime` key and a `namespaces` key is rejected with a validation error.

**Global mode** - parameters applied to every namespace.

```yaml
deployment:
  <key>: <value>
  '...': '...'
runtime:
  <key>: <value>
  '...': '...'
```

**Namespace-scoped mode** - parameters applied only to specific namespaces. If a namespace listed in the payload does
not exist in the environment, the Calculator raises a validation error.

```yaml
namespaces:
  <namespace-name>:
    deployment:
      <key>: <value>
      '...': '...'
    runtime:
      <key>: <value>
      '...': '...'
```

> [!NOTE]
>
> 1. `<value>` can be complex, i.e. a map or a list
> 2. All keys are optional
> Passing both a top-level `deployment`/`runtime` key and a `namespaces` key in the same payload causes a validation
> error. The Calculator will fail before writing any Effective Set output.

**Default Value**: None

**Mandatory**: No

**Example**:

```yaml
deployment:
  MY_OVERRIDE: value
```

### `APPLICATION_VERSIONS`

**Description**: One or more values to be deployed. Used to build the deployment plan and passed to ArgoCD repository
generation. At `PIPELINE_TYPE: GITLAB_DEPLOY` it replaces `SD_VERSION`. Each value is either a standalone application or
a Solution
Descriptor, which is expanded into its applications.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

An application value uses one of two notations:

- `<application-name>:<version>`
  The target namespace is resolved from the application `deployPostfix`.
- `<namespace-name>:<application-name>:<version>`
  The target namespace is set explicitly. Used when the application has no `deployPostfix`.

Values may also be provided as a JSON or YAML list of objects:

```yaml
- version: <application-name>:<version>   # Mandatory
  deployPostfix: <postfix>                # Optional
  namespace: <namespace-name>             # Optional
```

If specifying more than one, separate them as described in [Multiple Values Support](#multiple-values-support).

**Default Value**: None

**Mandatory**: No

**Example**:

- `solution:0.64.2`
- `env-1-bss:app-1:1.2.3`

### `DEPLOY_POSTFIXES_FILTER`

**Description**: Filters the generated deployment plan by `deployPostfix`. Only entries whose `deployPostfix` is
listed are kept. Prefix a value with `!` to exclude it instead. When empty, no filtering is applied.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

If specifying more than one, separate them as described in [Multiple Values Support](#multiple-values-support).

**Default Value**: None

**Mandatory**: No

**Example**: `core,bss`

### `NAMESPACE_NAMES_FILTER`

**Description**: Filters the generated deployment plan by namespace. Only entries whose namespace is listed are
kept. Prefix a value with `!` to exclude it instead. When empty, no filtering is applied.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

If specifying more than one, separate them as described in [Multiple Values Support](#multiple-values-support).

**Default Value**: None

**Mandatory**: No

**Example**: `env-1-bss,env-1-oss`

### `COMPONENT_NAMES_FILTER`

**Description**: Filters the generated deployment plan by component name, the application name before `:` in the
version. Only entries whose component is listed are kept. Prefix a value with `!` to exclude it instead. When
empty, no filtering is applied.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

If specifying more than one, separate them as described in [Multiple Values Support](#multiple-values-support).

**Default Value**: None

**Mandatory**: No

**Example**: `MONITORING,postgres`

### `WAVE_NAMES_FILTER`

**Description**: Filters the generated deployment plan by wave number. Only entries whose wave is listed are
kept. Prefix a value with `!` to exclude it instead. When empty, no filtering is applied.

Processed only at `PIPELINE_TYPE: GITLAB_DEPLOY`.

If specifying more than one, separate them as described in [Multiple Values Support](#multiple-values-support).

**Default Value**: None

**Mandatory**: No

**Example**: `0,1`

### `SD_VERSION`

**Description**: Specifies one or more SD artifacts in `application:version` notation.

Processed only at `PIPELINE_TYPE: LEGACY`.

If specifying more than one environment, separate them as described in [Multiple Values
Support](#multiple-values-support).

EnvGene downloads and sequentially merges them in the `basic-merge` mode, where subsequent `application:version` takes
priority over the previous one. Optionally saves the result to [Delta SD](/docs/features/sd-processing.md#delta-sd),
then merges with [Full SD](/docs/features/sd-processing.md#full-sd) using `SD_REPO_MERGE_MODE` merge mode

See details in [SD processing](/docs/features/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**:

- Single SD: `MONITORING:0.64.1`
- Multiple SDs: `solution-part-1:0.64.2,solution-part-2:0.44.1`

### `SD_DATA`

**Description**: Specifies the contents of one or more SD. Can be either a single SD object or a list of SD objects.

Processed only at `PIPELINE_TYPE: LEGACY`.

If a single SD object is provided, it is processed directly. If a list is provided, EnvGene sequentially merges them in
the `basic-merge` mode, where subsequent element takes priority over the previous one. Optionally saves the result to
[Delta SD](/docs/features/sd-processing.md#delta-sd), then merges with [Full
SD](/docs/features/sd-processing.md#full-sd) using `SD_REPO_MERGE_MODE` merge mode

See details in [SD processing](/docs/features/sd-processing.md)

**Format**: See [Parameter value formats](#parameter-value-formats)

**Default Value**: None

**Mandatory**: No

**Example**:

- Single SD (as object):

```yaml
version: 2.1
type: solutionDeploy
deployMode: composite
applications:
- version: MONITORING:0.64.1
  deployPostfix: platform-monitoring
- version: postgres:1.32.6
  deployPostfix: postgresql
```

- Single SD (as list with one element):

```yaml
- version: 2.1
  type: solutionDeploy
  deployMode: composite
  applications:
  - version: MONITORING:0.64.1
    deployPostfix: platform-monitoring
  - version: postgres:1.32.6
    deployPostfix: postgresql
```

- Multiple SD:

```yaml
- version: 2.1
  type: solutionDeploy
  deployMode: composite
  applications:
  - version: MONITORING:0.64.1
    deployPostfix: platform-monitoring
  - version: postgres:1.32.6
    deployPostfix: postgresql
- version: 2.1
  type: solutionDeploy
  deployMode: composite
  applications:
  - version: postgres-services:1.32.6
    deployPostfix: postgresql
  - version: postgres:1.32.3
    deployPostfix: postgresql-dbaas
```

### `SD_REPO_MERGE_MODE`

**Description**: Defines SD merge mode between incoming SD and already existed in repository SD. See details in [SD
Merge](/docs/features/sd-processing.md#sd-merge)

Processed only at `PIPELINE_TYPE: LEGACY`.

Available values:

- `basic-merge`
- `basic-exclusion-merge`
- `extended-merge`
- `replace`

See details in [SD processing](/docs/features/sd-processing.md)

**Default Value**: `basic-merge`

**Mandatory**: No

**Example**: `extended-merge`

### `DEPLOYMENT_SESSION_ID`

**Description**: Operation identifier in Envgene. Must be a valid [UUID v4](https://www.rfc-editor.org/rfc/rfc4122). This parameter is used in two scenarios:

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

1. If this parameter is provided, the resulting pipeline commit will include a [Git trailer](https://git-scm.com/docs/git-commit#Documentation/git-commit.txt---trailertokenvalue) in the format: `DEPLOYMENT_SESSION_ID: <value of DEPLOYMENT_SESSION_ID>`.
2. It will also be part of the deployment context of the Effective Set. The EnvGene passes it to the Calculator
   command-line tool using the `--extra_params` attribute. In this case it is used together with
   `GENERATE_EFFECTIVE_SET`.

**Default Value**: None

**Mandatory**: No

**Example**: "123e4567-e89b-12d3-a456-426614174000"

### `CRED_ROTATION_PAYLOAD`

**Description**: A parameter used to dynamically update sensitive parameters (those defined via the [cred
macro](/docs/template-macros.md#credential-macro-and-credential-reference)). It modifies values across different
contexts within a specified namespace and optional application. The value can be provided as plain text or encrypted.
See details in [feature description](/docs/features/cred-rotation.md)

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

> [!CAUTION]
> `CRED_ROTATION_PAYLOAD` cannot be combined with `GET_PASSPORT: true` in one pipeline run.

```yaml
rotation_items:
- namespace: <namespace>
  application: <application-name>
  context: enum[`pipeline`,`deployment`, `runtime`]
  parameter_key: <parameter-key>
  parameter_value: <new-parameter-value>
```

| Attribute         | Mandatory | Description                                                                                                                                                                                                                                                                               | Default | Example                             |
|-------------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|-------------------------------------|
| `namespace`       | Mandatory | The name of the Namespace where the parameter to be modified is defined                                                                                                                                                                                                                   | None    | `env-1-platform-monitoring`         |
| `application`     | Optional  | The name of the Application (sub-resource under `namespace`) where the parameter to be modified is defined. Cannot be used with `pipeline` context                                                                                                                                        | None    | `MONITORING`                        |
| `context`         | Mandatory | The context of the parameter being modified. Valid values: `pipeline`, `deployment`, `runtime`                                                                                                                                                                                            | None    | `deployment`                        |
| `parameter_key`   | Mandatory | The name (key) of the parameter to be modified                                                                                                                                                                                                                                            | None    | `login` or `db.connection.password` |
| `parameter_value` | Mandatory | New value (plaintext or encrypted). Envgene, depending on the value of the [`crypt`](/docs/envgene-configs.md#configyml) attribute, will either decrypt, encrypt, or leave the value unchanged. If an encrypted value is passed, it must be encrypted with a key that Envgene can decrypt | None    | `admin`                             |

**Default Value**: None

**Mandatory**: No

**Example**:

```yaml
rotation_items:
- namespace: env-1-platform-monitoring
  application: MONITORING
  context: deployment
  parameter_key: db_login
  parameter_value: s3cr3tN3wLogin
- namespace: env-1-platform-monitoring
  application: MONITORING
  context: deployment
  parameter_key: db_password
  parameter_value: s3cr3tN3wP@ss
- namespace: env-1-platform-monitoring
  context: deployment
  parameter_key: db_password
  parameter_value: s3cr3tN3wP@ss
- namespace: env-1-platform-monitoring
  context: deployment
  parameter_key: global.secrets.password
  parameter_value: user
- namespace: env-1-platform-monitoring
  context: deployment
  parameter_key: a.b.c.d
  parameter_value: somevalue
```

#### Affected Parameters and Troubleshooting

When rotating sensitive parameters, EnvGene checks if the Credential is
[shared](/docs/features/cred-rotation.md#affected-parameters) (used by multiple parameters or Environments). If shared
Credentials are detected and force mode is not enabled, the credential_rotation job will fail to prevent accidental mass
updates.

- In this case, the job will generate an
  [`affected-sensitive-parameters.yaml`](/docs/features/cred-rotation.md#affected-parameters-reporting) file as an
  artifact. This file lists all parameters and locations affected by the Credential change, including those in shared
  Credentials files and all Environments that reference this credential.
- To resolve:
  - Review `affected-sensitive-parameters.yaml` to see which parameters and environments are linked by the shared
    Credential.
  - Either:
    - Manually split the shared Credential in the repository so each parameter uses its own Credential, **or**
    - Rerun the Credential rotation job with force mode enabled (`CRED_ROTATION_FORCE=true`) to update all linked
      parameters.

> **Note:** When rotating a shared credential, all parameters in all Environments that reference this credential will be
> updated. This is why force mode is required for such operations to avoid accidental mass changes. The
> `affected-sensitive-parameters.yaml` file will list all such parameters and environments.

### `CRED_ROTATION_FORCE`

**Description**: Enables force mode for updating sensitive parameter values. In force mode, the sensitive parameter
value will be changed even if it affects other sensitive parameters that may be linked through the same credential. See
details in [Credential Rotation](/docs/features/cred-rotation.md)

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `GH_ADDITIONAL_PARAMS`

**Description**: A comma-separated string of key-value pairs for GitHub pipeline. Use it to pass all pipeline parameters
except these main ones, which must be set directly:

- `ENV_NAMES`
- `DEPLOYMENT_TICKET_ID`
- `ENV_TEMPLATE_VERSION`
- `ENV_BUILDER`
- `GENERATE_EFFECTIVE_SET`
- `GET_PASSPORT`
- `CMDB_IMPORT`

The parameters must follow the parameter schema defined in this document.

This parameter is only available in the [GitHub version](/github_workflows/instance-repo-pipeline/) of the pipeline.

> [!NOTE]
> GitHub only allows 10 input parameters for the pipeline. To work around this but keep full functionality, the main
> parameters are provided at the top level, and all additional ones are sent as comma-separated key-value pairs in this
> field.

**Format**: `KEY1=VALUE1,KEY2=VALUE2,KEY3=VALUE3`

If a value contains JSON (e.g., `SD_DATA`, `EFFECTIVE_SET_CONFIG`, `CUSTOM_PARAMS`, `CRED_ROTATION_PAYLOAD`,
`BG_STATE`), the JSON must be properly escaped within the value part. For example:
`SD_DATA=[{\"version\":2.1,...}],EFFECTIVE_SET_CONFIG={\"version\": \"v2.0\"}`

**Default Value**: None

**Mandatory**: No

**Example**:
`SD_DATA=[{\"version\":2.1,\"type\":\"solutionDeploy\"}],CUSTOM_PARAMS={\"deployment\":{\"KEY\":\"value\"}}`

Example of calling EnvGene pipeline via GitHub API:

```bash
curl -X POST \
  -H "Authorization: token token-placeholder-123" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/qubership/instance-repo/actions/workflows/pipeline.yml/dispatches \
  -d '{
        "ref": "main",
        "inputs": {
            "ENV_NAMES": "test-cluster/e01",
            "ENV_BUILDER": "true",
            "GENERATE_EFFECTIVE_SET": "true",
            "DEPLOYMENT_TICKET_ID": "QBSHP-0001",
            "GH_ADDITIONAL_PARAMS":
"SD_DATA=[{\"version\":2.1,\"type\":\"solutionDeploy\"}],EFFECTIVE_SET_CONFIG={\"version\": \"v2.0\",
\"app_chart_validation\": \"false\"}"
        }
      }'
```

## Deprecated Parameters

The following parameters are planned for removal

### `SD_DELTA`

**Description**: Deprecated. Use `SD_REPO_MERGE_MODE` instead.

Processed only at `PIPELINE_TYPE: LEGACY`.

If `true`: behaves identically to `SD_REPO_MERGE_MODE: extended-merge`

If `false`: behaves identically to `SD_REPO_MERGE_MODE: replace`

See details in [SD processing](/docs/features/sd-processing.md)

**Default Value**: None

**Mandatory**: No

**Example**: `true`

### `ENV_SPECIFIC_PARAMS`

**Description**: Specifies Environment Inventory and env-specific parameters. Use `ENV_INVENTORY_CONTENT` instead. This
is can used together with
`ENV_INVENTORY_INIT`. See details in [Environment Inventory
Generation](/docs/features/env-inventory-generation.md)

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

**Default Value**: None

**Mandatory**: No

**Example**:

```yaml
clusterParams:
  clusterEndpoint: <value>
  clusterToken: <value>
additionalTemplateVariables:
  <key>: <value>
cloudName: <value>
envSpecificParamsets:
  <ns-template-name>:
  - paramsetA
  cloud:
  - paramsetB
paramsets:
  paramsetA:
    version: <paramset-version>
    name: <paramset-name>
    parameters:
      <key>: <value>
    applications:
    - appName: <app-name>
      parameters:
        <key>: <value>
  paramsetB:
    version: <paramset-version>
    name: <paramset-name>
    parameters:
      <key>: <value>
    applications: []
credentials:
  credX:
    type: <credential-type>
    data:
      username: <value>
      password: <value>
  credY:
    type: <credential-type>
    data:
      secret: <value>
```

### `ENV_TEMPLATE_NAME`

**Description**: Specifies the template artifact value within the generated Environment Inventory. Use
`ENV_INVENTORY_CONTENT` instead. This is used together
with `ENV_INVENTORY_INIT`.

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

System overrides `envTemplate.name` at `/environments/<ENV_NAME>/Inventory/env_definition.yml`:

```yaml
envTemplate:
    name: <ENV_TEMPLATE_NAME>
    ...
...
```

**Default Value**: None

**Mandatory**: No

**Example**: `env-template:v1.2.3`

### `ENV_INVENTORY_INIT`

**Description**: Use `ENV_INVENTORY_CONTENT` instead.

If `true`:
  In the pipeline, a job for generating the environment inventory is executed. The new Environment Inventory will be
generated in the path `/environments/<ENV_NAME>/Inventory/env_definition.yml`. See details in [Environment Inventory
Generation](/docs/features/env-inventory-generation.md)

Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and `PIPELINE_TYPE: LEGACY`.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

## Parameter value formats

A parameter whose value is structured, a map or a list, may be passed as YAML, JSON, or JSON-in-string.
The pipeline parses each value and normalizes a map or a list into compact JSON before use. A scalar value,
a plain string, number, or boolean, is passed through unchanged.

The three forms are equivalent:

```yaml
# YAML
deployment:
  MY_OVERRIDE: value
```

```json
{"deployment": {"MY_OVERRIDE": "value"}}
```

```text
# JSON-in-string
"{\"deployment\":{\"MY_OVERRIDE\":\"value\"}}"
```

The structured examples in this document use YAML for readability. Any of the three forms is accepted.

## Multiple Values Support

Some pipeline parameters support multiple values.
Values can be separated using one of the following delimiters:

- Newline (`\n`)
- Semicolon (`;`)
- Comma (`,`)
- Space (` `)

**Example**:

```text
# Using newline
k8s-01/env-1\nk8s-01/env-2

# Using comma
k8s-01/env-1,k8s-01/env-2

# Using semicolon
k8s-01/env-1;k8s-01/env-2

# Using space
k8s-01/env-1 k8s-01/env-2
```
