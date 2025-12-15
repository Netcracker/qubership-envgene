# Calculator CLI Use Cases

- [Calculator CLI Use Cases](#calculator-cli-use-cases)
  - [Overview](#overview)
  - [Parameter Type Preservation in Macro Resolution](#parameter-type-preservation-in-macro-resolution)
    - [UC-CC-MR-1: Simple Type Resolution](#uc-cc-mr-1-simple-type-resolution)
    - [UC-CC-MR-2: Complex Structure Resolution](#uc-cc-mr-2-complex-structure-resolution)
  - [deployPostfix Matching Logic](#deploypostfix-matching-logic)
    - [UC-CC-DP-1: Exact Match](#uc-cc-dp-1-exact-match)
    - [UC-CC-DP-2: BG Domain Match](#uc-cc-dp-2-bg-domain-match)
    - [UC-CC-DP-3: No Exact Match Found](#uc-cc-dp-3-no-exact-match-found)
    - [UC-CC-DP-4: No BG Domain Match Found](#uc-cc-dp-4-no-bg-domain-match-found)
  - [Cross-Level Parameter References](#cross-level-parameter-references)
    - [UC-CC-HR-1: Namespace to Cloud Reference](#uc-cc-hr-1-namespace-to-cloud-reference)
    - [UC-CC-DP-2: BG Domain Match](#uc-cc-dp-2-bg-domain-match-1)
    - [UC-CC-HR-2: Namespace to Tenant Reference](#uc-cc-hr-2-namespace-to-tenant-reference)
    - [UC-CC-DP-3: No Exact Match Found](#uc-cc-dp-3-no-exact-match-found-1)
    - [UC-CC-HR-3: Cloud to Tenant Reference](#uc-cc-hr-3-cloud-to-tenant-reference)
    - [UC-CC-DP-4: No BG Domain Match Found](#uc-cc-dp-4-no-bg-domain-match-found-1)
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

## Parameter Type Preservation in Macro Resolution

This section covers use cases for [Macro Parameter Resolution](/docs/features/calculator-cli.md#version-20-macros) in Effective Set v2.0. The Calculator CLI resolves parameter references while preserving the original parameter types according to [Parameter type conversion](/docs/features/calculator-cli.md#version-20-parameter-type-conversion) rules.

### UC-CC-MR-1: Simple Type Resolution

**Pre-requisites:**

1. Environment Instance exists with parameters that reference other parameters using `${...}` macro syntax:
   1. Integer type parameter: `server_port: 8080`
   2. String type parameter: `app_version: "3.0"`
   3. Boolean type parameter: `ssl_enabled: true`
   4. String boolean parameter: `debug_mode: "true"`
2. Environment Instance contains parameters that reference the above parameters:
   1. `api_port: ${server_port}` (references integer)
   2. `service_version: ${app_version}` (references string)
   3. `use_ssl: ${ssl_enabled}` (references boolean)
   4. `log_level: ${debug_mode}` (references string boolean)
3. Solution SBOM exists with application elements
4. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Resolves parameter references using `${...}` macro syntax
   3. For each parameter reference:
      1. Locates the referenced parameter in Environment Instance
      2. Extracts the parameter value
      3. Preserves the original type of the referenced parameter (integer, string, boolean)
      4. Replaces the macro reference with the parameter value, maintaining the original type

**Results:**

1. All parameter references are resolved to their referenced values
2. Parameter types are preserved exactly as defined in Environment Instance:
   1. `api_port: 8080` (integer type, not string "8080")
   2. `service_version: "3.0"` (string type)
   3. `use_ssl: true` (boolean type, not string "true")
   4. `log_level: "true"` (string type)
3. Effective Set files contain resolved parameters with correct types preserved
4. No implicit type conversions occur during macro resolution

### UC-CC-MR-2: Complex Structure Resolution

## deployPostfix Matching Logic

This section covers use cases for [deployPostfix Matching Logic](/docs/features/calculator-cli.md#version-20-deploypostfix-matching-logic). The matching logic matches `deployPostfix` values from Solution Descriptor(SD) to Namespace folders in Environment Instance.

### UC-CC-DP-1: Exact Match

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace objects
   2. A Namespace folder whose name exactly matches the `deployPostfix` value from Solution Descriptor
2. SD exists with `deployPostfix` values in application elements

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads SD and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from SD:
      1. Attempts exact match: searches for a Namespace folder in Environment Instance whose name exactly matches the `deployPostfix` value
      2. Finds exact match
      3. Uses that Namespace folder

**Results:**

1. `deployPostfix` value from SD is matched to the Namespace folder with exact name match
2. Applications from SD are associated with the matching Namespace folder in Effective Set

### UC-CC-DP-2: BG Domain Match

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace objects
   2. BG Domain object exists with `origin` and `peer` namespaces with corresponding folders in Environment Instance that match `deployPostfix` values:
      1. `origin` Namespace (from BG Domain object) folder name equals `deployPostfix` + `-origin` (e.g., `bss-origin`)
      2. `peer` Namespace (from BG Domain object) folder name equals `deployPostfix` + `-peer` (e.g., `bss-peer`)
2. SD exists with `deployPostfix` values in application elements:
   1. A `deployPostfix` value that matches `origin` Namespace folder (e.g., `deployPostfix: "bss"` matches `bss-origin`)
   2. A `deployPostfix` value that matches `peer` Namespace folder (e.g., `deployPostfix: "bss"` matches `bss-peer`)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads SD and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from SD:
      1. Attempts exact match: searches for a Namespace folder in Environment Instance whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. Searches for a Namespace folder in BG Domain:
         1. Searches for a Namespace folder with role `origin` (from BG Domain object) whose name equals `deployPostfix` + `-origin`
         2. Searches for a Namespace folder with role `peer` (from BG Domain object) whose name equals `deployPostfix` + `-peer`
      4. Finds matching Namespace folder (either `origin` or `peer`)
      5. Uses that Namespace folder

**Results:**

1. `deployPostfix` value from SD is matched to either the `origin` or `peer` Namespace folder in BG Domain (with `-origin` or `-peer` suffix, depending on which match is found)
2. Applications from SD are associated with the matching Namespace folder (`origin` or `peer`) in Effective Set

### UC-CC-DP-3: No Exact Match Found

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace objects
   2. No Namespace folder whose name exactly matches the `deployPostfix` value from SD
2. SD exists with `deployPostfix` values in application elements

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads SD and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from SD:
      1. Attempts exact match: searches for a Namespace folder whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. No matching Namespace folder is found for the `deployPostfix` value
   3. Effective Set generation fails with an error

**Results:**

1. No Namespace folder is matched to the `deployPostfix` value from SD
2. Applications from SD with this `deployPostfix` value are not associated with any Namespace folder in Effective Set
3. Effective Set generation fails with an error indicating that no matching Namespace folder was found in Environment Instance for the `deployPostfix` value from SD (e.g., `Error: Cannot find Namespace folder in Environment Instance for deployPostfix: "<deployPostfix>"`)

### UC-CC-DP-4: No BG Domain Match Found

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace objects
   2. No Namespace folder whose name exactly matches the `deployPostfix` value from SD
   3. BG Domain object exists with `origin` and `peer` namespaces and corresponding folders in Environment Instance, but no matching BG Domain namespace folder exists for the `deployPostfix` value from SD:
      - `deployPostfix` + `-origin` does not match the `origin` Namespace folder name, **OR**
      - `deployPostfix` + `-peer` does not match the `peer` Namespace folder name, **OR**
      - Both do not match
2. SD exists with `deployPostfix` values in application elements

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads SD and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from SD:
      1. Attempts exact match: searches for a Namespace folder whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. Searches for a Namespace folder in BG Domain:
         1. Searches for a Namespace folder with role `origin` (from BG Domain object) whose name equals `deployPostfix` + `-origin`
         2. Searches for a Namespace folder with role `peer` (from BG Domain object) whose name equals `deployPostfix` + `-peer`
      4. No matching BG Domain namespace folder is found
   3. No matching Namespace folder is found for the `deployPostfix` value
   4. Effective Set generation fails with an error

**Results:**

1. No Namespace folder is matched to the `deployPostfix` value from SD
2. Applications from SD with this `deployPostfix` value are not associated with any Namespace folder in Effective Set
3. Effective Set generation fails with an error indicating that no matching Namespace folder was found in Environment Instance for the `deployPostfix` value(s) from SD. The error message lists all `deployPostfix` values that could not be matched (e.g., `Cannot find Namespace folder in Environment Instance for deployPostfix: "<deployPostfix>", "<deployPostfix>"`)

## Cross-Level Parameter References

This section covers use cases for cross-level parameter references in Effective Set v2.0. EnvGene has a hierarchical parameter structure: [Tenant](/docs/envgene-objects.md#tenant) → [Cloud](/docs/envgene-objects.md#cloud) → [Namespace](/docs/envgene-objects.md#namespace). Parameters can reference other parameters from higher levels in the hierarchy, but not from lower levels. The Calculator CLI enforces these rules during macro resolution.

### UC-CC-HR-1: Namespace to Cloud Reference

   1. Reads Solution SBOM and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from Solution SBOM:
      1. Attempts exact match: searches for a Namespace folder in Environment Instance whose name exactly matches the `deployPostfix` value
      2. Finds exact match
      3. Uses that Namespace folder

**Results:**

1. `deployPostfix` value from Solution SBOM is matched to the Namespace folder with exact name match
2. Applications from Solution SBOM are associated with the matching Namespace folder in Effective Set

### UC-CC-DP-2: BG Domain Match

**Pre-requisites:**

1. Environment Instance exists with:
   1. Cloud object with:
      1. `deployParameters` containing: `cloud_api_url: "https://api.example.com"`
      2. `e2eParameters` containing: `cloud_test_url: "https://test.example.com"`
      3. `technicalConfigurationParameters` containing: `cloud_config_url: "https://config.example.com"`
   2. Namespace object with:
      1. `deployParameters` containing: `service_url: ${cloud_api_url}`
      2. `e2eParameters` containing: `test_endpoint: ${cloud_test_url}`
      3. `technicalConfigurationParameters` containing: `config_endpoint: ${cloud_config_url}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM
   1. Namespace objects
   2. BG Domain object exists with `origin` and `peer` namespaces with corresponding folders in Environment Instance that match `deployPostfix` values:
      1. `origin` Namespace (from BG Domain object) folder name equals `deployPostfix` + `-origin` (e.g., `bss-origin`)
      2. `peer` Namespace (from BG Domain object) folder name equals `deployPostfix` + `-peer` (e.g., `bss-peer`)
4. Solution SBOM exists with `deployPostfix` values in application elements:
   1. A `deployPostfix` value that matches `origin` Namespace folder (e.g., `deployPostfix: "bss"` matches `bss-origin`)
   2. A `deployPostfix` value that matches `peer` Namespace folder (e.g., `deployPostfix: "bss"` matches `bss-peer`)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Resolves parameter references:
      1. Resolves `${cloud_api_url}` reference from Cloud `deployParameters`
      2. Resolves `${cloud_test_url}` reference from Cloud `e2eParameters`
      3. Resolves `${cloud_config_url}` reference from Cloud `technicalConfigurationParameters`

**Results:**

1. References from Namespace to Cloud level are successfully resolved for all parameter types:
   1. Namespace parameter `service_url` is resolved to `"https://api.example.com"`
   2. Namespace parameter `test_endpoint` is resolved to `"https://test.example.com"`
   3. Namespace parameter `config_endpoint` is resolved to `"https://config.example.com"`

### UC-CC-HR-2: Namespace to Tenant Reference

   1. Reads Solution SBOM and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from Solution SBOM:
      1. Attempts exact match: searches for a Namespace folder in Environment Instance whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. Searches for a Namespace folder in BG Domain:
         1. Searches for a Namespace folder with role `origin` (from BG Domain object) whose name equals `deployPostfix` + `-origin`
         2. Searches for a Namespace folder with role `peer` (from BG Domain object) whose name equals `deployPostfix` + `-peer`
      4. Finds matching Namespace folder (either `origin` or `peer`)
      5. Uses that Namespace folder

**Results:**

1. `deployPostfix` value from Solution SBOM is matched to either the `origin` or `peer` Namespace folder in BG Domain (with `-origin` or `-peer` suffix, depending on which match is found)
2. Applications from Solution SBOM are associated with the matching Namespace folder (`origin` or `peer`) in Effective Set

### UC-CC-DP-3: No Exact Match Found

**Pre-requisites:**

1. Environment Instance exists with:
   1. Tenant object with:
      1. `deployParameters` containing: `tenant_id: "acme-corp"`
      2. `e2eParameters` containing: `tenant_test_id: "acme-test"`
      3. `technicalConfigurationParameters` containing: `tenant_config_id: "acme-config"`
   2. Namespace object with:
      1. `deployParameters` containing: `organization: ${tenant_id}`
      2. `e2eParameters` containing: `test_org: ${tenant_test_id}`
      3. `technicalConfigurationParameters` containing: `config_org: ${tenant_config_id}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM
   1. Namespace objects
   2. No Namespace folder whose name exactly matches the `deployPostfix` value from Solution SBOM
4. Solution SBOM exists with `deployPostfix` values in application elements

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Resolves parameter references:
      1. Resolves `${tenant_id}` reference from Tenant `deployParameters`
      2. Resolves `${tenant_test_id}` reference from Tenant `e2eParameters`
      3. Resolves `${tenant_config_id}` reference from Tenant `technicalConfigurationParameters`

**Results:**

1. References from Namespace to Tenant level are successfully resolved for all parameter types:
   1. Namespace parameter `organization` is resolved to `"acme-corp"`
   2. Namespace parameter `test_org` is resolved to `"acme-test"`
   3. Namespace parameter `config_org` is resolved to `"acme-config"`

### UC-CC-HR-3: Cloud to Tenant Reference

   1. Reads Solution SBOM and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from Solution SBOM:
      1. Attempts exact match: searches for a Namespace folder whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. No matching Namespace folder is found for the `deployPostfix` value
   3. Effective Set generation fails with an error

**Results:**

1. No Namespace folder is matched to the `deployPostfix` value from Solution SBOM
2. Applications from Solution SBOM with this `deployPostfix` value are not associated with any Namespace folder in Effective Set
3. Effective Set generation fails with an error indicating that no matching Namespace folder was found in Environment Instance for the `deployPostfix` value from Solution SBOM (e.g., `Error: Cannot find Namespace folder in Environment Instance for deployPostfix: "<deployPostfix>"`)

### UC-CC-DP-4: No BG Domain Match Found

**Pre-requisites:**

1. Environment Instance exists with:
   1. Tenant object with:
      1. `deployParameters` containing: `tenant_name: "acme-corp"`
      2. `e2eParameters` containing: `tenant_test_name: "acme-test"`
      3. `technicalConfigurationParameters` containing: `tenant_config_name: "acme-config"`
   2. Cloud object with:
      1. `deployParameters` containing: `cloud_label: ${tenant_name}`
      2. `e2eParameters` containing: `cloud_test_label: ${tenant_test_name}`
      3. `technicalConfigurationParameters` containing: `cloud_config_label: ${tenant_config_name}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM
   1. Namespace objects
   2. No Namespace folder whose name exactly matches the `deployPostfix` value from Solution SBOM
   3. BG Domain object exists with `origin` and `peer` namespaces and corresponding folders in Environment Instance, but no matching BG Domain namespace folder exists for the `deployPostfix` value from Solution SBOM:
      - `deployPostfix` + `-origin` does not match the `origin` Namespace folder name, **OR**
      - `deployPostfix` + `-peer` does not match the `peer` Namespace folder name, **OR**
      - Both do not match
4. Solution SBOM exists with `deployPostfix` values in application elements

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Resolves parameter references:
      1. Resolves `${tenant_name}` reference from Tenant `deployParameters`
      2. Resolves `${tenant_test_name}` reference from Tenant `e2eParameters`
      3. Resolves `${tenant_config_name}` reference from Tenant `technicalConfigurationParameters`

**Results:**

1. References from Cloud to Tenant level are successfully resolved for all parameter types:
   1. Cloud parameter `cloud_label` is resolved to `"acme-corp"`
   2. Cloud parameter `cloud_test_label` is resolved to `"acme-test"`
   3. Cloud parameter `cloud_config_label` is resolved to `"acme-config"`

### UC-CC-HR-4: Cloud to Namespace Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace object with:
      1. `deployParameters` containing: `namespace_db_url: "postgres://db.local"`
      2. `e2eParameters` containing: `namespace_test_url: "https://test.local"`
      3. `technicalConfigurationParameters` containing: `namespace_config_url: "https://config.local"`
   2. Cloud object with:
      1. `deployParameters` containing: `cloud_config: ${namespace_db_url}`
      2. `e2eParameters` containing: `cloud_test_config: ${namespace_test_url}`
      3. `technicalConfigurationParameters` containing: `cloud_config_param: ${namespace_config_url}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${namespace_db_url}` reference
      2. Attempts to resolve `${namespace_test_url}` reference
      3. Attempts to resolve `${namespace_config_url}` reference
   3. Detects that the references target a lower level (Namespace) from a higher level (Cloud)
   4. Effective Set generation fails with an error indicating that cross-level references from Cloud to Namespace are not allowed

**Results:**

1. Effective Set generation fails with error messages indicating that references from Cloud level to Namespace level are prohibited for all parameter types (e.g., `Invalid parameter reference '${namespace_db_url}' in Cloud '<cloud-name>': Cloud level parameters cannot reference Namespace level parameters`)

### UC-CC-HR-5: Tenant to Cloud Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Cloud object with:
      1. `deployParameters` containing: `cloud_region: "us-east-1"`
      2. `e2eParameters` containing: `cloud_test_region: "us-west-1"`
      3. `technicalConfigurationParameters` containing: `cloud_config_region: "eu-central-1"`
   2. Tenant object with:
      1. `deployParameters` containing: `tenant_config: ${cloud_region}`
      2. `e2eParameters` containing: `tenant_test_config: ${cloud_test_region}`
      3. `technicalConfigurationParameters` containing: `tenant_config_param: ${cloud_config_region}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${cloud_region}` reference
      2. Attempts to resolve `${cloud_test_region}` reference
      3. Attempts to resolve `${cloud_config_region}` reference
   3. Detects that the references target a lower level (Cloud) from a higher level (Tenant)
   4. Effective Set generation fails with an error indicating that cross-level references from Tenant to Cloud are not allowed

**Results:**

1. Effective Set generation fails with error messages indicating that references from Tenant level to Cloud level are prohibited for all parameter types (e.g., `Invalid parameter reference '${cloud_region}' in Tenant '<tenant-name>': Tenant level parameters cannot reference Cloud level parameters`)

### UC-CC-HR-6: Tenant to Namespace Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace object with:
      1. `deployParameters` containing: `namespace_name: "core"`
      2. `e2eParameters` containing: `namespace_test_name: "test-core"`
      3. `technicalConfigurationParameters` containing: `namespace_config_name: "config-core"`
   2. Tenant object with:
      1. `deployParameters` containing: `tenant_label: ${namespace_name}`
      2. `e2eParameters` containing: `tenant_test_label: ${namespace_test_name}`
      3. `technicalConfigurationParameters` containing: `tenant_config_label: ${namespace_config_name}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${namespace_name}` reference
      2. Attempts to resolve `${namespace_test_name}` reference
      3. Attempts to resolve `${namespace_config_name}` reference
   3. Detects that the references target a lower level (Namespace) from a higher level (Tenant)
   4. Effective Set generation fails with an error indicating that cross-level references from Tenant to Namespace are not allowed

**Results:**

1. Effective Set generation fails with error messages indicating that references from Tenant level to Namespace level are prohibited for all parameter types (e.g., `Invalid parameter reference '${namespace_name}' in Tenant '<tenant-name>': Tenant level parameters cannot reference Namespace level parameters`)

## Cross-Context Parameter References

This section covers use cases for cross-context parameter references in Effective Set v2.0. Parameters can only reference other parameters within the same parameter type context. References between different parameter types (`deployParameters`, `e2eParameters`, and `technicalConfigurationParameters`) are not allowed. The Calculator CLI enforces these rules during macro resolution.

### UC-CC-CR-1: DeployParameters to E2EParameters Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace object with:
      1. `e2eParameters` containing: `test_url: "https://test.example.com"`
      2. `deployParameters` containing: `service_url: ${test_url}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${test_url}` reference from `deployParameters`
   3. Detects that the reference targets a different parameter type context (`e2eParameters`) from `deployParameters`
   4. Effective Set generation fails with an error indicating that cross-context references from `deployParameters` to `e2eParameters` are not allowed

**Results:**

1. Effective Set generation fails with an error message indicating that references from `deployParameters` to `e2eParameters` are prohibited (e.g., `Invalid parameter reference '${test_url}' in Namespace '<namespace-name>': Parameters in 'deployParameters' cannot reference parameters from 'e2eParameters'`)

### UC-CC-CR-2: DeployParameters to TechnicalConfigurationParameters Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace object with:
      1. `technicalConfigurationParameters` containing: `config_url: "https://config.example.com"`
      2. `deployParameters` containing: `service_config: ${config_url}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${config_url}` reference from `deployParameters`
   3. Detects that the reference targets a different parameter type context (`technicalConfigurationParameters`) from `deployParameters`
   4. Effective Set generation fails with an error indicating that cross-context references from `deployParameters` to `technicalConfigurationParameters` are not allowed

**Results:**

1. Effective Set generation fails with an error message indicating that references from `deployParameters` to `technicalConfigurationParameters` are prohibited (e.g., `Invalid parameter reference '${config_url}' in Namespace '<namespace-name>': Parameters in 'deployParameters' cannot reference parameters from 'technicalConfigurationParameters'`)

### UC-CC-CR-3: E2EParameters to DeployParameters Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace object with:
      1. `deployParameters` containing: `api_url: "https://api.example.com"`
      2. `e2eParameters` containing: `test_endpoint: ${api_url}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${api_url}` reference from `e2eParameters`
   3. Detects that the reference targets a different parameter type context (`deployParameters`) from `e2eParameters`
   4. Effective Set generation fails with an error indicating that cross-context references from `e2eParameters` to `deployParameters` are not allowed

**Results:**

1. Effective Set generation fails with an error message indicating that references from `e2eParameters` to `deployParameters` are prohibited (e.g., `Invalid parameter reference '${api_url}' in Namespace '<namespace-name>': Parameters in 'e2eParameters' cannot reference parameters from 'deployParameters'`)

### UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace object with:
      1. `technicalConfigurationParameters` containing: `config_endpoint: "https://config.example.com"`
      2. `e2eParameters` containing: `test_config: ${config_endpoint}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${config_endpoint}` reference from `e2eParameters`
   3. Detects that the reference targets a different parameter type context (`technicalConfigurationParameters`) from `e2eParameters`
   4. Effective Set generation fails with an error indicating that cross-context references from `e2eParameters` to `technicalConfigurationParameters` are not allowed

**Results:**

1. Effective Set generation fails with an error message indicating that references from `e2eParameters` to `technicalConfigurationParameters` are prohibited (e.g., `Invalid parameter reference '${config_endpoint}' in Namespace '<namespace-name>': Parameters in 'e2eParameters' cannot reference parameters from 'technicalConfigurationParameters'`)

### UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace object with:
      1. `deployParameters` containing: `deploy_url: "https://deploy.example.com"`
      2. `technicalConfigurationParameters` containing: `runtime_config: ${deploy_url}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${deploy_url}` reference from `technicalConfigurationParameters`
   3. Detects that the reference targets a different parameter type context (`deployParameters`) from `technicalConfigurationParameters`
   4. Effective Set generation fails with an error indicating that cross-context references from `technicalConfigurationParameters` to `deployParameters` are not allowed

**Results:**

1. Effective Set generation fails with an error message indicating that references from `technicalConfigurationParameters` to `deployParameters` are prohibited (e.g., `Invalid parameter reference '${deploy_url}' in Namespace '<namespace-name>': Parameters in 'technicalConfigurationParameters' cannot reference parameters from 'deployParameters'`)

### UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace object with:
      1. `e2eParameters` containing: `e2e_endpoint: "https://e2e.example.com"`
      2. `technicalConfigurationParameters` containing: `runtime_endpoint: ${e2e_endpoint}`
2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Attempts to resolve parameter references:
      1. Attempts to resolve `${e2e_endpoint}` reference from `technicalConfigurationParameters`
   3. Detects that the reference targets a different parameter type context (`e2eParameters`) from `technicalConfigurationParameters`
   4. Effective Set generation fails with an error indicating that cross-context references from `technicalConfigurationParameters` to `e2eParameters` are not allowed

**Results:**

1. Effective Set generation fails with an error message indicating that references from `technicalConfigurationParameters` to `e2eParameters` are prohibited (e.g., `Invalid parameter reference '${e2e_endpoint}' in Namespace '<namespace-name>': Parameters in 'technicalConfigurationParameters' cannot reference parameters from 'e2eParameters'`)
   1. Reads Solution SBOM and extracts `deployPostfix` values from application elements
   2. For each `deployPostfix` value from Solution SBOM:
      1. Attempts exact match: searches for a Namespace folder whose name exactly matches the `deployPostfix` value
      2. No exact match is found
      3. Searches for a Namespace folder in BG Domain:
         1. Searches for a Namespace folder with role `origin` (from BG Domain object) whose name equals `deployPostfix` + `-origin`
         2. Searches for a Namespace folder with role `peer` (from BG Domain object) whose name equals `deployPostfix` + `-peer`
      4. No matching BG Domain namespace folder is found
   3. No matching Namespace folder is found for the `deployPostfix` value
   4. Effective Set generation fails with an error

**Results:**

1. No Namespace folder is matched to the `deployPostfix` value from Solution SBOM
2. Applications from Solution SBOM with this `deployPostfix` value are not associated with any Namespace folder in Effective Set
3. Effective Set generation fails with an error indicating that no matching Namespace folder was found in Environment Instance for the `deployPostfix` value(s) from Solution SBOM. The error message lists all `deployPostfix` values that could not be matched (e.g., `Cannot find Namespace folder in Environment Instance for deployPostfix: "<deployPostfix>", "<deployPostfix>"`)
