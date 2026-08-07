# Calculator CLI Use Cases

- [Calculator CLI Use Cases](#calculator-cli-use-cases)
  - [Overview](#overview)
  - [deployPostfix Matching Logic](#deploypostfix-matching-logic)
    - [UC-CC-DP-1: Exact Match](#uc-cc-dp-1-exact-match)
    - [UC-CC-DP-2: BG Domain Match](#uc-cc-dp-2-bg-domain-match)
    - [UC-CC-DP-3: No Exact Match Found](#uc-cc-dp-3-no-exact-match-found)
    - [UC-CC-DP-4: No BG Domain Match Found](#uc-cc-dp-4-no-bg-domain-match-found)
  - [Parameter Merge Hierarchy](#parameter-merge-hierarchy)
    - [UC-CC-PM-1: Namespace Overrides Cloud Parameter](#uc-cc-pm-1-namespace-overrides-cloud-parameter)
    - [UC-CC-PM-2: Cloud Overrides Tenant Parameter](#uc-cc-pm-2-cloud-overrides-tenant-parameter)
    - [UC-CC-PM-3: Namespace Overrides Tenant Parameter Directly](#uc-cc-pm-3-namespace-overrides-tenant-parameter-directly)
  - [Parameter Type Preservation in Macro Resolution](#parameter-type-preservation-in-macro-resolution)
    - [UC-CC-MR-1: Simple Type Resolution](#uc-cc-mr-1-simple-type-resolution)
    - [UC-CC-MR-2: Complex Structure Resolution](#uc-cc-mr-2-complex-structure-resolution)
    - [UC-CC-MR-3: Multi-Step Macro Chain Resolution](#uc-cc-mr-3-multi-step-macro-chain-resolution)
    - [UC-CC-MR-4: Macro Reference Resolved Across Hierarchy Levels](#uc-cc-mr-4-macro-reference-resolved-across-hierarchy-levels)
  - [Custom Parameters Injection](#custom-parameters-injection)
    - [UC-CC-CP-1: CUSTOM_PARAMS Injected into Deployment Parameters](#uc-cc-cp-1-custom_params-injected-into-deployment-parameters)
    - [UC-CC-CP-2: CUSTOM_PARAMS with Unknown Namespace Fails](#uc-cc-cp-2-custom_params-with-unknown-namespace-fails)
    - [UC-CC-CP-3: CUSTOM_PARAMS with Both Top-Level and Namespace Keys Fails](#uc-cc-cp-3-custom_params-with-both-top-level-and-namespace-keys-fails)
  - [Generation ID Types](#generation-id-types)
    - [UC-CC-GI-1: UniqForRun Application Gets Unique Generation Directory](#uc-cc-gi-1-uniqforrun-application-gets-unique-generation-directory)
    - [UC-CC-GI-2: UniqForVersion Application Gets Version-Derived Generation Directory](#uc-cc-gi-2-uniqforversion-application-gets-version-derived-generation-directory)
  - [Cross-Level Parameter References](#cross-level-parameter-references)
    - [UC-CC-HR-1: Namespace to Cloud Reference](#uc-cc-hr-1-namespace-to-cloud-reference)
    - [UC-CC-HR-2: Namespace to Tenant Reference](#uc-cc-hr-2-namespace-to-tenant-reference)
    - [UC-CC-HR-3: Cloud to Tenant Reference](#uc-cc-hr-3-cloud-to-tenant-reference)
    - [UC-CC-HR-4: Cloud to Namespace Reference Error](#uc-cc-hr-4-cloud-to-namespace-reference-error)
    - [UC-CC-HR-5: Tenant to Cloud Reference Error](#uc-cc-hr-5-tenant-to-cloud-reference-error)
    - [UC-CC-HR-6: Tenant to Namespace Reference Error](#uc-cc-hr-6-tenant-to-namespace-reference-error)
  - [Cross-Context Parameter References](#cross-context-parameter-references)
    - [UC-CC-CR-1: DeployParameters to E2EParameters Reference Error](#uc-cc-cr-1-deployparameters-to-e2eparameters-reference-error)
    - [UC-CC-CR-2: DeployParameters to TechnicalConfigurationParameters Reference Error](#uc-cc-cr-2-deployparameters-to-technicalconfigurationparameters-reference-error)
    - [UC-CC-CR-3: E2EParameters to DeployParameters Reference Error](#uc-cc-cr-3-e2eparameters-to-deployparameters-reference-error)
    - [UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters Reference Error](#uc-cc-cr-4-e2eparameters-to-technicalconfigurationparameters-reference-error)
    - [UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters Reference Error](#uc-cc-cr-5-technicalconfigurationparameters-to-deployparameters-reference-error)
    - [UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error](#uc-cc-cr-6-technicalconfigurationparameters-to-e2eparameters-reference-error)

## Overview

This document covers use cases for [Calculator CLI](/docs/features/calculator-cli.md) operations related to Effective Set v2.0 generation.

> [!NOTE]
> These use cases apply only to Effective Set v2.0. Use cases for Effective Set v1.0 are not planned.

The Calculator CLI reads the Environment Instance (Tenant, Cloud, Namespace objects) and the deploy plan, merges parameters according to the hierarchy Tenant → Cloud → Namespace (lower levels override higher), resolves `${...}` macro references, validates cross-level and cross-context reference rules, and writes the Effective Set output files.

## deployPostfix Matching Logic

This section covers use cases for [deployPostfix Matching Logic](/docs/features/calculator-cli.md#version-20-deploypostfix-matching-logic). The matching logic matches `deployPostfix` values from the deploy plan to Namespace folders in the Environment Instance. Exact match is always tried first; BG Domain match is the fallback.

### UC-CC-DP-1: Exact Match

**Pre-requisites:**

1. Environment Instance exists with a Namespace folder whose name exactly matches the `deployPostfix` value from the deploy plan
2. Deploy plan contains an application entry with that `deployPostfix` value

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` runs
2. For each deploy plan entry: attempts exact match of `deployPostfix` against Namespace folder names
3. Finds exact match; uses that Namespace folder

**Results:**

1. Effective Set is generated successfully
2. Application is associated with the matched Namespace folder in the output

### UC-CC-DP-2: BG Domain Match

> [!NOTE]
> Currently results in a NullPointerException inside `splitBgDomainParams()` — tracked as a known bug (`@xfail_cli_npe`).

**Pre-requisites:**

1. Environment Instance exists with a BG Domain where:
   - Origin Namespace folder name = `<postfix>-origin` (e.g. `bss-origin`)
   - Peer Namespace folder name = `<postfix>-peer` (e.g. `bss-peer`)
2. No Namespace folder has a name exactly equal to `<postfix>` (e.g. `bss`)
3. Deploy plan contains an application entry with `deployPostfix: <postfix>`

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` runs
2. Exact match fails for `<postfix>`
3. BG Domain fallback: checks whether `<postfix>-origin` or `<postfix>-peer` matches any BG namespace folder
4. Finds a match in the BG Domain; uses that Namespace folder

**Results:**

1. Effective Set is generated successfully
2. Application is associated with the matched BG Namespace folder (`-origin` or `-peer` suffixed)

### UC-CC-DP-3: No Exact Match Found

**Pre-requisites:**

1. Environment Instance has no Namespace folder whose name matches the `deployPostfix` value
2. No BG Domain is present (or BG Domain exists but also does not match)
3. Deploy plan contains an application entry with that non-matching `deployPostfix` value

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` runs
2. Exact match fails; no BG Domain fallback succeeds
3. CLI exits with a non-zero code

**Results:**

1. Effective Set generation fails
2. Log contains the unmatched `deployPostfix` value (e.g. `nonexistent`)

### UC-CC-DP-4: No BG Domain Match Found

**Pre-requisites:**

1. Environment Instance has a BG Domain present
2. No Namespace folder matches the `deployPostfix` value exactly
3. Neither `<postfix>-origin` nor `<postfix>-peer` matches any BG Domain namespace folder
4. Deploy plan contains an application with that `deployPostfix` value

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` runs
2. Exact match fails; BG Domain fallback also fails for both `-origin` and `-peer` suffixes
3. CLI exits with a non-zero code

**Results:**

1. Effective Set generation fails
2. Log contains all unmatched `deployPostfix` values (e.g. `xyz`)

## Parameter Merge Hierarchy

This section covers the parameter merge priority stack for `deployParameters` (same rules apply to `e2eParameters` and `technicalConfigurationParameters`). The stack in ascending priority order is: **Tenant → Cloud → Namespace**. A parameter defined at Namespace level with the same key as a Tenant or Cloud parameter wins; a Cloud-level parameter wins over a Tenant-level one.

All three cases below set the pipeline parameter `GENERATE_EFFECTIVE_SET: true` and do not use SD / CUSTOM_PARAMS. Assertions check the value of a specific key in `effective-set/deployment/<ns>/<app>/values/deployment-parameters.yaml`.

### UC-CC-PM-1: Namespace Overrides Cloud Parameter

**Pre-requisites:**

1. Tenant object has `deployParameters: {shared_key: "from-tenant"}`
2. Cloud object has `deployParameters: {shared_key: "from-cloud"}`
3. Namespace object has `deployParameters: {shared_key: "from-namespace"}`
4. Deploy plan references one application in that Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` merges Tenant → Cloud → Namespace deploy parameters
2. At each layer the same key `shared_key` is present; each layer overrides the previous

**Results:**

1. Effective Set is generated successfully
2. `deployment-parameters.yaml` for the application contains `shared_key: from-namespace`
3. Neither `from-tenant` nor `from-cloud` appears as the value for `shared_key`

### UC-CC-PM-2: Cloud Overrides Tenant Parameter

**Pre-requisites:**

1. Tenant object has `deployParameters: {shared_key: "from-tenant"}`
2. Cloud object has `deployParameters: {shared_key: "from-cloud"}`
3. Namespace object has **no** `shared_key` in its `deployParameters`
4. Deploy plan references one application in that Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` merges Tenant → Cloud → Namespace
2. Cloud layer overrides Tenant for `shared_key`; Namespace layer does not define it

**Results:**

1. Effective Set is generated successfully
2. `deployment-parameters.yaml` for the application contains `shared_key: from-cloud`
3. `from-tenant` does not appear as the value for `shared_key`

### UC-CC-PM-3: Namespace Overrides Tenant Parameter Directly

**Pre-requisites:**

1. Tenant object has `deployParameters: {shared_key: "from-tenant"}`
2. Cloud object has **no** `shared_key` in its `deployParameters`
3. Namespace object has `deployParameters: {shared_key: "from-namespace"}`
4. Deploy plan references one application in that Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` merges Tenant → Cloud → Namespace
2. Cloud layer passes through the Tenant value unchanged; Namespace layer overrides it

**Results:**

1. Effective Set is generated successfully
2. `deployment-parameters.yaml` for the application contains `shared_key: from-namespace`
3. `from-tenant` does not appear as the value for `shared_key`

## Parameter Type Preservation in Macro Resolution

This section covers use cases for [Macro Parameter Resolution](/docs/template-macros.md#calculator-command-line-tool-macros). The Calculator CLI resolves `${param}` references while preserving the original YAML type of the referenced value (integer, boolean, string, mapping, list).

### UC-CC-MR-1: Simple Type Resolution

**Pre-requisites:**

1. Namespace `deployParameters` contains:
   - `server_port: 8080` (integer)
   - `app_version: "3.0"` (string)
   - `ssl_enabled: true` (boolean)
   - `debug_mode: "true"` (string that looks like boolean)
2. Namespace `deployParameters` also contains references to the above:
   - `api_port: ${server_port}`
   - `service_version: ${app_version}`
   - `use_ssl: ${ssl_enabled}`
   - `log_level: ${debug_mode}`
3. Deploy plan references one application in that Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` resolves each `${...}` reference using type-preserving logic
2. For simple single-variable references the original YAML type of the source value is kept

**Results:**

1. Effective Set is generated successfully
2. `deployment-parameters.yaml` contains:
   - `api_port: 8080` (integer, not string `"8080"`)
   - `service_version: "3.0"` (string)
   - `use_ssl: true` (boolean, not string `"true"`)
   - `log_level: "true"` (string)

### UC-CC-MR-2: Complex Structure Resolution

**Pre-requisites:**

1. Namespace `deployParameters` contains:
   ```yaml
   database_config:
     connection:
       host: db.example.com
       port: 5432
   api_config: ${database_config}
   yaml_template: |
     services:
       api:
         image: api:latest
   rendered_template: ${yaml_template}
   ```
2. Deploy plan references one application in that Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` resolves `${database_config}` — a mapping value
2. Resolves `${yaml_template}` — a literal block scalar string

**Results:**

1. Effective Set is generated successfully
2. `api_config` in `deployment-parameters.yaml` is a nested mapping identical to `database_config`
3. `rendered_template` is a multi-line string identical to `yaml_template`
4. No flattening or reformatting of the structures occurs

### UC-CC-MR-3: Multi-Step Macro Chain Resolution

**Pre-requisites:**

1. Namespace `deployParameters` contains a three-level reference chain:
   - `base_url: "https://api.example.com"`
   - `service_url: ${base_url}`
   - `final_url: ${service_url}`
2. Deploy plan references one application in that Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` resolves `${service_url}` to `"https://api.example.com"`
2. Then resolves `${final_url}` by first resolving `${service_url}`
3. Iterative resolution continues until no `${...}` patterns remain (up to 50 iterations)

**Results:**

1. Effective Set is generated successfully
2. `final_url` in `deployment-parameters.yaml` equals `"https://api.example.com"`
3. `service_url` in `deployment-parameters.yaml` equals `"https://api.example.com"`

### UC-CC-MR-4: Macro Reference Resolved Across Hierarchy Levels

**Pre-requisites:**

1. Tenant `deployParameters` contains: `global_timeout: 30`
2. Cloud `deployParameters` contains: `cloud_timeout: ${global_timeout}`
3. Namespace `deployParameters` contains: `ns_timeout: ${cloud_timeout}`
4. Deploy plan references one application in that Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` merges Tenant → Cloud → Namespace
2. `${global_timeout}` in Cloud is resolved during merge
3. `${cloud_timeout}` in Namespace is resolved after Cloud value is merged in

**Results:**

1. Effective Set is generated successfully
2. `ns_timeout` in `deployment-parameters.yaml` equals `30` (integer type preserved through the chain)

## Custom Parameters Injection

This section covers use cases for the `CUSTOM_PARAMS` pipeline parameter. `CUSTOM_PARAMS` injects additional key-value pairs into the effective set at runtime, taking precedence over all statically defined parameters. The value is a JSON string passed as `--custom-params` to the CLI.

### UC-CC-CP-1: CUSTOM_PARAMS Injected into Deployment Parameters

**Pre-requisites:**

1. Environment Instance exists with a Namespace and at least one application in the deploy plan
2. Namespace `deployParameters` contains `override_key: "original-value"`

**Trigger:**

Instance pipeline is started with:
- `ENV_NAMES: <env_name>`
- `GENERATE_EFFECTIVE_SET: true`
- `CUSTOM_PARAMS: override_key=injected-value`

**Steps:**

1. `generate_effective_set` receives `--custom-params=override_key=injected-value`
2. Custom params are applied on top of all merged static parameters

**Results:**

1. Effective Set is generated successfully
2. `deployment-parameters.yaml` contains `override_key: injected-value`
3. `original-value` does not appear for `override_key`

### UC-CC-CP-2: CUSTOM_PARAMS with Unknown Namespace Fails

**Pre-requisites:**

1. Environment Instance exists with a Namespace named `core`
2. Deploy plan references one application

**Trigger:**

Instance pipeline is started with:
- `ENV_NAMES: <env_name>`
- `GENERATE_EFFECTIVE_SET: true`
- `CUSTOM_PARAMS: {"namespaces": {"nonexistent-ns": {"key": "value"}}}`

**Steps:**

1. `generate_effective_set` receives namespace-scoped custom params
2. CLI validates that every namespace key in `CUSTOM_PARAMS.namespaces` exists in the Environment Instance
3. `nonexistent-ns` is not found

**Results:**

1. Effective Set generation fails
2. Log contains `nonexistent-ns`

### UC-CC-CP-3: CUSTOM_PARAMS with Both Top-Level and Namespace Keys Fails

**Pre-requisites:**

1. Environment Instance exists with a Namespace and one application in deploy plan

**Trigger:**

Instance pipeline is started with:
- `ENV_NAMES: <env_name>`
- `GENERATE_EFFECTIVE_SET: true`
- `CUSTOM_PARAMS: {"deployment": {"key": "val"}, "namespaces": {"core": {"key": "val"}}}`

**Steps:**

1. `generate_effective_set` receives custom params containing both `deployment` and `namespaces` top-level keys
2. CLI detects the ambiguous combination and rejects it

**Results:**

1. Effective Set generation fails
2. Log indicates that mixing top-level deployment/runtime keys with `namespaces` key is not allowed

## Generation ID Types

This section covers how the `generationType` field on deploy plan entries controls the output directory structure under `effective-set/deployment/`. Three types exist: `UniqForApp` (default, no extra nesting), `UniqForRun` (UUID-based subdirectory, stable within a run), `UniqForVersion` (version-suffix-based subdirectory, stable across runs for the same version).

### UC-CC-GI-1: UniqForRun Application Gets Unique Generation Directory

**Pre-requisites:**

1. Deploy plan contains an application entry with `generationType: UniqForRun` and a `generationId` UUID value
2. Environment Instance has the corresponding Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` processes the deploy plan entry
2. Detects `generationType: UniqForRun`; uses the `generationId` UUID as a subdirectory name
3. Writes output to `effective-set/deployment/<ns>/<app>/<uuid>/values/`

**Results:**

1. Effective Set is generated successfully
2. The output directory for the application includes the UUID-named subdirectory
3. The standard `effective-set/deployment/<ns>/<app>/values/` path is not created for this entry

### UC-CC-GI-2: UniqForVersion Application Gets Version-Derived Generation Directory

**Pre-requisites:**

1. Deploy plan contains an application entry with `generationType: UniqForVersion` and `version: appName:1.2.3`
2. Environment Instance has the corresponding Namespace

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` processes the deploy plan entry
2. Detects `generationType: UniqForVersion`; extracts the version suffix after `:` (`1.2.3`) as the directory name
3. Writes output to `effective-set/deployment/<ns>/<app>/1.2.3/values/`

**Results:**

1. Effective Set is generated successfully
2. The output directory for the application is `<ns>/<app>/1.2.3/values/`
3. Rerunning with the same version produces output in the same directory (idempotent)

## Cross-Level Parameter References

This section covers use cases for cross-level parameter references. EnvGene has a hierarchical parameter structure: [Tenant](/docs/envgene-objects.md#tenant) → [Cloud](/docs/envgene-objects.md#cloud) → [Namespace](/docs/envgene-objects.md#namespace). Parameters at a given level can reference parameters from higher levels (upward references), but not from lower levels (downward references are forbidden). The Calculator CLI enforces these rules during macro resolution.

### UC-CC-HR-1: Namespace to Cloud Reference

**Pre-requisites:**

1. Cloud `deployParameters`: `cloud_api_url: "https://api.example.com"`, `e2eParameters`: `cloud_test_url: "https://test.example.com"`, `technicalConfigurationParameters`: `cloud_config_url: "https://config.example.com"`
2. Namespace references all three: `service_url: ${cloud_api_url}`, `test_endpoint: ${cloud_test_url}`, `config_endpoint: ${cloud_config_url}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` resolves upward references from Namespace to Cloud across all three parameter contexts

**Results:**

1. Effective Set is generated successfully
2. `service_url` resolves to `"https://api.example.com"`, `test_endpoint` to `"https://test.example.com"`, `config_endpoint` to `"https://config.example.com"`

### UC-CC-HR-2: Namespace to Tenant Reference

**Pre-requisites:**

1. Tenant `deployParameters`: `tenant_id: "acme-corp"`, `e2eParameters`: `tenant_test_id: "acme-test"`, `technicalConfigurationParameters`: `tenant_config_id: "acme-config"`
2. Namespace references all three: `organization: ${tenant_id}`, `test_org: ${tenant_test_id}`, `config_org: ${tenant_config_id}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` resolves upward references from Namespace to Tenant across all three parameter contexts

**Results:**

1. Effective Set is generated successfully
2. `organization` resolves to `"acme-corp"`, `test_org` to `"acme-test"`, `config_org` to `"acme-config"`

### UC-CC-HR-3: Cloud to Tenant Reference

**Pre-requisites:**

1. Tenant `deployParameters`: `tenant_name: "acme-corp"`, `e2eParameters`: `tenant_test_name: "acme-test"`, `technicalConfigurationParameters`: `tenant_config_name: "acme-config"`
2. Cloud references all three: `cloud_label: ${tenant_name}`, `cloud_test_label: ${tenant_test_name}`, `cloud_config_label: ${tenant_config_name}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` resolves upward references from Cloud to Tenant across all three parameter contexts

**Results:**

1. Effective Set is generated successfully
2. `cloud_label` resolves to `"acme-corp"`, `cloud_test_label` to `"acme-test"`, `cloud_config_label` to `"acme-config"`

### UC-CC-HR-4: Cloud to Namespace Reference Error

**Pre-requisites:**

1. Namespace `deployParameters`: `namespace_db_url: "postgres://db.local"`, `e2eParameters`: `namespace_test_url: "https://test.local"`, `technicalConfigurationParameters`: `namespace_config_url: "https://config.local"`
2. Cloud references all three (downward): `cloud_config: ${namespace_db_url}`, `cloud_test_config: ${namespace_test_url}`, `cloud_config_param: ${namespace_config_url}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve downward references from Cloud to Namespace
2. Detects the violation and fails

**Results:**

1. Effective Set generation fails
2. Log contains the offending parameter name (e.g. `namespace_test_url`)

### UC-CC-HR-5: Tenant to Cloud Reference Error

> [!NOTE]
> Not yet enforced by the Calculator CLI — tracked as a known gap (`@xfail_cli_no_hierarchy_rule`).

**Pre-requisites:**

1. Cloud `deployParameters`: `cloud_region: "us-east-1"`, `e2eParameters`: `cloud_test_region: "us-west-1"`, `technicalConfigurationParameters`: `cloud_config_region: "eu-central-1"`
2. Tenant references all three (downward): `tenant_config: ${cloud_region}`, `tenant_test_config: ${cloud_test_region}`, `tenant_config_param: ${cloud_config_region}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve downward references from Tenant to Cloud
2. Expected: detects the violation and fails

**Results:**

1. Effective Set generation fails
2. Log contains `"Tenant level parameters cannot reference Cloud level parameters"`

### UC-CC-HR-6: Tenant to Namespace Reference Error

> [!NOTE]
> Not yet enforced by the Calculator CLI — tracked as a known gap (`@xfail_cli_no_hierarchy_rule`).

**Pre-requisites:**

1. Namespace `deployParameters`: `namespace_name: "core"`, `e2eParameters`: `namespace_test_name: "test-core"`, `technicalConfigurationParameters`: `namespace_config_name: "config-core"`
2. Tenant references all three (downward): `tenant_label: ${namespace_name}`, `tenant_test_label: ${namespace_test_name}`, `tenant_config_label: ${namespace_config_name}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve downward references from Tenant to Namespace
2. Expected: detects the violation and fails

**Results:**

1. Effective Set generation fails
2. Log contains `"Tenant level parameters cannot reference Namespace level parameters"`

## Cross-Context Parameter References

This section covers use cases for cross-context parameter references. Parameters can only reference other parameters within the same parameter type (`deployParameters`, `e2eParameters`, `technicalConfigurationParameters`). Cross-context references are forbidden regardless of the hierarchy level. The Calculator CLI enforces these rules during macro resolution.

### UC-CC-CR-1: DeployParameters to E2EParameters Reference Error

**Pre-requisites:**

1. Namespace `e2eParameters`: `test_url: "https://test.example.com"`
2. Namespace `deployParameters`: `service_url: ${test_url}` (references across context)
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve `${test_url}` from within `deployParameters`
2. Detects that `test_url` is defined in `e2eParameters` — a different context
3. Fails with an error

**Results:**

1. Effective Set generation fails
2. Log contains both the referencing parameter name (`service_url`) and the referenced parameter name (`test_url`)

### UC-CC-CR-2: DeployParameters to TechnicalConfigurationParameters Reference Error

**Pre-requisites:**

1. Namespace `technicalConfigurationParameters`: `config_url: "https://config.example.com"`
2. Namespace `deployParameters`: `service_config: ${config_url}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve `${config_url}` from within `deployParameters`
2. Detects cross-context reference; fails

**Results:**

1. Effective Set generation fails
2. Log contains `service_config` and `config_url`

### UC-CC-CR-3: E2EParameters to DeployParameters Reference Error

> [!NOTE]
> Not yet enforced by the Calculator CLI — tracked as a known gap (`@xfail_cli_no_context_rule`).

**Pre-requisites:**

1. Namespace `deployParameters`: `api_url: "https://api.example.com"`
2. Namespace `e2eParameters`: `test_endpoint: ${api_url}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve `${api_url}` from within `e2eParameters`
2. Expected: detects cross-context reference; fails

**Results:**

1. Effective Set generation fails
2. Log contains `"e2eParameters"` and `"deployParameters"`

### UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters Reference Error

> [!NOTE]
> Not yet enforced by the Calculator CLI — tracked as a known gap (`@xfail_cli_no_context_rule`).

**Pre-requisites:**

1. Namespace `technicalConfigurationParameters`: `config_endpoint: "https://config.example.com"`
2. Namespace `e2eParameters`: `test_config: ${config_endpoint}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve `${config_endpoint}` from within `e2eParameters`
2. Expected: detects cross-context reference; fails

**Results:**

1. Effective Set generation fails
2. Log contains `"e2eParameters"` and `"technicalConfigurationParameters"`

### UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters Reference Error

> [!NOTE]
> Not yet enforced by the Calculator CLI — tracked as a known gap (`@xfail_cli_no_context_rule`).

**Pre-requisites:**

1. Namespace `deployParameters`: `deploy_url: "https://deploy.example.com"`
2. Namespace `technicalConfigurationParameters`: `runtime_config: ${deploy_url}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve `${deploy_url}` from within `technicalConfigurationParameters`
2. Expected: detects cross-context reference; fails

**Results:**

1. Effective Set generation fails
2. Log contains `"technicalConfigurationParameters"` and `"deployParameters"`

### UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error

**Pre-requisites:**

1. Namespace `e2eParameters`: `e2e_endpoint: "https://e2e.example.com"`
2. Namespace `technicalConfigurationParameters`: `runtime_endpoint: ${e2e_endpoint}`
3. Deploy plan references one application

**Trigger:**

Instance pipeline is started with `ENV_NAMES: <env_name>`, `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. `generate_effective_set` attempts to resolve `${e2e_endpoint}` from within `technicalConfigurationParameters`
2. Detects cross-context reference; fails

**Results:**

1. Effective Set generation fails
2. Log contains `runtime_endpoint` and `e2e_endpoint`
