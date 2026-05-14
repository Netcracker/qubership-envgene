# Calculator CLI Use Cases

- [Calculator CLI Use Cases](#calculator-cli-use-cases)
  - [Overview](#overview)
  - [deployPostfix Matching Logic](#deploypostfix-matching-logic)
    - [UC-CC-DP-1: Exact Match](#uc-cc-dp-1-exact-match)
    - [UC-CC-DP-2: BG Domain Match](#uc-cc-dp-2-bg-domain-match)
    - [UC-CC-DP-3: No Exact Match Found](#uc-cc-dp-3-no-exact-match-found)
    - [UC-CC-DP-4: No BG Domain Match Found](#uc-cc-dp-4-no-bg-domain-match-found)
  - [Parameter Type Preservation in Macro Resolution](#parameter-type-preservation-in-macro-resolution)
    - [UC-CC-MR-1: Simple Type Resolution](#uc-cc-mr-1-simple-type-resolution)
    - [UC-CC-MR-2: Complex Structure Resolution](#uc-cc-mr-2-complex-structure-resolution)
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
  - [SBOM Processing](#sbom-processing)
    - [UC-ES-DEP-14: deploy_param image keys](#uc-es-dep-14-deploy_param-image-keys)
    - [UC-ES-DEP-A16: App chart validation fails when enabled](#uc-es-dep-a16-app-chart-validation-fails-when-enabled)
    - [UC-ES-DEP-A18: App chart validation skipped when disabled](#uc-es-dep-a18-app-chart-validation-skipped-when-disabled)
  - [Deployment Context](#deployment-context)
    - [UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline](#uc-es-dep-15-deployment_session_id-from-pipeline)
    - [UC-ES-DEP-16: Predefined identity, MANAGED_BY default, and mandatory deployment keys](#uc-es-dep-16-predefined-identity-managed_by-default-and-mandatory-deployment-keys)
    - [UC-ES-DEP-22: DBaaS and Vault disabled omit optional deployment URLs](#uc-es-dep-22-dbaas-and-vault-disabled-omit-optional-deployment-urls)
    - [UC-ES-DEP-23: Public and private gateway URLs from deployment context](#uc-es-dep-23-public-and-private-gateway-urls-from-deployment-context)
    - [UC-ES-DEP-A15: Blue-green predefined deployment parameters](#uc-es-dep-a15-blue-green-predefined-deployment-parameters)
    - [UC-ES-DEP-A8: custom-params.yaml from CUSTOM_PARAMS](#uc-es-dep-a8-custom-paramsyaml-from-custom_params)
  - [Sensitive Parameters Processing](#sensitive-parameters-processing)
    - [UC-ES-DEP-A6: Deployment credentials, feature secrets, and SSL bundle macros](#uc-es-dep-a6-deployment-credentials-feature-secrets-and-ssl-bundle-macros)
  - [Collision Routing](#collision-routing)
    - [UC-ES-DEP-20: Service-name collision routing](#uc-es-dep-20-service-name-collision-routing)
  - [Deploy Descriptor](#deploy-descriptor)
    - [UC-ES-DEP-A9: deploy-descriptor.yaml structure and configuration artifacts](#uc-es-dep-a9-deploy-descriptoryaml-structure-and-configuration-artifacts)
  - [Per-Service Parameters](#per-service-parameters)
    - [UC-ES-DEP-A11: Per-service layout and resource profiles](#uc-es-dep-a11-per-service-layout-and-resource-profiles)
  - [Cross-Context Effective Set Consistency](#cross-context-effective-set-consistency)
    - [UC-ES-DEP-A14: deployment mapping.yaml](#uc-es-dep-a14-deployment-mappingyaml)
    - [UC-ES-RUN-3: runtime mapping.yaml key set](#uc-es-run-3-runtime-mappingyaml-key-set)
    - [UC-ES-CLN-3: cleanup mapping.yaml key set](#uc-es-cln-3-cleanup-mappingyaml-key-set)
  - [Pipeline Context](#pipeline-context)
    - [UC-ES-PIPE-1: pipeline parameters and credentials from Cloud e2eParameters](#uc-es-pipe-1-pipeline-parameters-and-credentials-from-cloud-e2eparameters)
    - [UC-ES-PIPE-4: Consumer copies root keys from pipeline context](#uc-es-pipe-4-consumer-copies-root-keys-from-pipeline-context)
    - [UC-ES-PIPE-5: Consumer schema default only](#uc-es-pipe-5-consumer-schema-default-only)
    - [UC-ES-PIPE-6: Consumer omits optional schema-only key](#uc-es-pipe-6-consumer-omits-optional-schema-only-key)
    - [UC-ES-PIPE-7: Consumer mandatory key without value fails](#uc-es-pipe-7-consumer-mandatory-key-without-value-fails)
  - [Runtime Context](#runtime-context)
    - [UC-ES-RUN-1: runtime/parameters.yaml from technicalConfigurationParameters](#uc-es-run-1-runtimeparametersyaml-from-technicalconfigurationparameters)
    - [UC-ES-RUN-2: runtime/credentials.yaml includes sensitive and custom runtime](#uc-es-run-2-runtimecredentialsyaml-includes-sensitive-and-custom-runtime)
  - [Cleanup Context](#cleanup-context)
    - [UC-ES-CLN-1: cleanup/parameters.yaml from deployParameters](#uc-es-cln-1-cleanupparametersyaml-from-deployparameters)
    - [UC-ES-CLN-2: cleanup/credentials.yaml includes sensitive and custom runtime](#uc-es-cln-2-cleanupcredentialsyaml-includes-sensitive-and-custom-runtime)
  - [Topology Context](#topology-context)
    - [UC-ES-TOP-1: Cluster endpoint from Cloud Passport](#uc-es-top-1-cluster-endpoint-from-cloud-passport)
    - [UC-ES-TOP-2: Cluster endpoint from inventory.clusterUrl](#uc-es-top-2-cluster-endpoint-from-inventoryclusterurl)
    - [UC-ES-TOP-3: inventory.clusterUrl parsing variants](#uc-es-top-3-inventoryclusterurl-parsing-variants)
    - [UC-ES-TOP-6: Cloud Passport overrides inventory.clusterUrl](#uc-es-top-6-cloud-passport-overrides-inventoryclusterurl)
    - [UC-ES-TOP-7: Missing cluster information yields empty cluster fields](#uc-es-top-7-missing-cluster-information-yields-empty-cluster-fields)

## Overview

This document covers use cases for [Calculator CLI](/docs/features/calculator-cli.md) operations related to Effective Set v2.0 generation.

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

## Parameter Type Preservation in Macro Resolution

This section covers use cases for [Macro Parameter Resolution](/docs/template-macros.md#calculator-command-line-tool-macros) in Effective Set v2.0. The Calculator CLI resolves parameter references while preserving the original parameter types according to [Parameter type conversion](/docs/features/calculator-cli.md#version-20-parameter-type-conversion) rules.

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

**Pre-requisites:**

1. Environment Instance exists with:
   1. Complex nested parameter structure:

      ```yaml
      database_config:
        connection:
          host: db.example.com
          port: 5432
      ```

   2. Parameter that references the complex structure:

      ```yaml
      api_config: ${database_config}
      ```

   3. Alternative complex structure with literal block scalar:

      ```yaml
      yaml_template: |
        services:
          api:
            image: api:latest
            ports:
              - 8080:8080
      ```

   4. Parameter that references the literal block scalar:

      ```yaml
      rendered_template: ${yaml_template}
      ```

2. Solution SBOM exists with application elements
3. Application SBOMs exist for applications referenced in Solution SBOM

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Reads Environment Instance
   2. Resolves parameter references using `${...}` macro syntax
   3. For complex structure references:
      1. Locates the referenced parameter in Environment Instance
      2. Extracts the complete nested structure
      3. Preserves the original structure format (YAML mapping vs literal block scalar)
      4. Replaces the macro reference with the complete structure, maintaining the original format

**Results:**

1. Complex parameter references are resolved to their complete nested structures
2. Structure formats are preserved exactly as defined in Environment Instance:
   1. `api_config` contains the same nested mapping structure as `database_config`:

      ```yaml
      api_config:
        connection:
          host: db.example.com
          port: 5432
      ```

   2. `rendered_template` contains the same literal block scalar format as `yaml_template`:

      ```yaml
      rendered_template: |
        services:
          api:
            image: api:latest
            ports:
              - 8080:8080
      ```

3. Effective Set files contain resolved complex parameters with original structure and format preserved
4. No structure transformation or reformatting occurs during macro resolution

## Cross-Level Parameter References

This section covers use cases for cross-level parameter references in Effective Set v2.0. EnvGene has a hierarchical parameter structure: [Tenant](/docs/envgene-objects.md#tenant) → [Cloud](/docs/envgene-objects.md#cloud) → [Namespace](/docs/envgene-objects.md#namespace). Parameters can reference other parameters from higher levels in the hierarchy, but not from lower levels. The Calculator CLI enforces these rules during macro resolution.

### UC-CC-HR-1: Namespace to Cloud Reference

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

## SBOM Processing

This group covers SBOM-driven inputs that are not limited to a single output file: image parameters from `deploy_param`, and mandatory app chart validation behavior.

### UC-ES-DEP-14: deploy_param image keys

**Pre-requisites:**

1. Environment Instance exists with:
   1. Application SBOM for the target application that includes:
      1. Component with MIME type `application/octet-stream`, property `deploy_param: IMAGE_QA_KEY`, and `full_image_name: registry.example.local/ns/app:1.2.3`.
      2. Component with MIME type `application/octet-stream`, property `deploy_param: billing-service`, and `full_image_name: registry.example.local/ns/billing:9.0.0`.
      3. SBOM contains a service named `billing-service`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The Calculator derives root deployment parameters from SBOM components whose MIME type is `application/octet-stream`.
   2. For each such component with non-empty `deploy_param`, treat `<deploy_param value>: <full_image_name value>` as a candidate root mapping.
   3. If `deploy_param` equals an existing service name, omit that mapping from root deployment parameters.

**Results:**

1. `deployment-parameters.yaml` contains `IMAGE_QA_KEY: registry.example.local/ns/app:1.2.3`.
2. `deployment-parameters.yaml` does not contain a root key `billing-service`.

**Example (`deployment-parameters.yaml`, excerpt - root map):**

```yaml
IMAGE_QA_KEY: registry.example.local/ns/app:1.2.3
# ... other predefined keys, merged deployParameters, per-service anchors ...
```

### UC-ES-DEP-A16: App chart validation fails when enabled

**Pre-requisites:**

1. Environment Instance exists with:
   1. At least one application SBOM has no `application/vnd.qubership.app.chart` component.

**Trigger:**

Pipeline (GitLab or GitHub):

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `EFFECTIVE_SET_CONFIG` does not set `app_chart_validation` to `false` (omit or default; validation on, see [app chart validation](/docs/features/calculator-cli.md#version-20-app-chart-validation)).

**Steps:**

1. The `generate_effective_set` job runs; app chart validation fails if any application SBOM lacks `application/vnd.qubership.app.chart`.

**Results:**

1. Effective Set generation does not complete successfully.

### UC-ES-DEP-A18: App chart validation skipped when disabled

**Pre-requisites:**

1. Environment Instance exists with:
   1. At least one application SBOM has no `application/vnd.qubership.app.chart` component.
   2. SBOM application component name is `legacy-app-without-chart-validation-passed` so predefined `APPLICATION_NAME` in `deployment-parameters.yaml` matches the fixture used in the example below.
   3. Tenant, Cloud, Namespace, and Application `deployParameters` do not override `MANAGED_BY`, so the predefined default `argocd` applies.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `EFFECTIVE_SET_CONFIG` includes `"app_chart_validation": false` (or pipeline-accepted equivalent).

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The Calculator skips app chart validation.

**Results:**

1. Effective Set generation completes successfully while at least one application SBOM still omits the `application/vnd.qubership.app.chart` component.

**Example (`deployment-parameters.yaml`, excerpt after successful generation):**

```yaml
MANAGED_BY: argocd
APPLICATION_NAME: legacy-app-without-chart-validation-passed
# ... predefined keys and merges ...
```

## Deployment Context

This group covers [Deployment Parameter Context](/docs/features/calculator-cli.md#version-20-deployment-parameter-context) behaviors tied to `deployment-parameters.yaml`, session identifiers, predefined keys, blue-green fields, and `custom-params.yaml` injection. Deploy descriptor structure is covered separately under [Deploy Descriptor](#deploy-descriptor).

### UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline

**Pre-requisites:**

1. Environment Instance exists with:
   1. Target application and inventory wiring sufficient for a normal Effective Set deployment pass so `deployment-parameters.yaml` and `deploy-descriptor.yaml` are produced (including per-service anchors that repeat `DEPLOYMENT_SESSION_ID`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `DEPLOYMENT_SESSION_ID: 550e8400-e29b-41d4-a716-446655440000` (pipeline supplies the session UUID passed through to the Calculator for this run)

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job passes `DEPLOYMENT_SESSION_ID` from the instance pipeline into the Calculator.
   2. Predefined deployment parameters and session references in `deploy-descriptor.yaml` use that pipeline UUID.

**Results:**

1. `deployment-parameters.yaml` contains `DEPLOYMENT_SESSION_ID` equal to the pipeline UUID string.
2. `deploy-descriptor.yaml` uses the same session value wherever common service fields reference `DEPLOYMENT_SESSION_ID`.

**Example (`deployment-parameters.yaml`, excerpt):**

```yaml
DEPLOYMENT_SESSION_ID: "550e8400-e29b-41d4-a716-446655440000"
# ... other predefined keys ...
```

**Example (`deploy-descriptor.yaml`, excerpt - anchors align with repo fixtures):**

```yaml
global: &g
  deployDescriptor: &dd
    billing-api:
      name: billing-api
      image_type: image
      # ... SBOM-derived image fields ...
deployDescriptor: *dd
billing-api:
  APPLICATION_NAME: billing-app
  DEPLOYMENT_SESSION_ID: "550e8400-e29b-41d4-a716-446655440000"
  MANAGED_BY: argocd
  deployDescriptor: *dd
  global: *g
APPLICATION_NAME: billing-app
DEPLOYMENT_SESSION_ID: "550e8400-e29b-41d4-a716-446655440000"
MANAGED_BY: argocd
```

### UC-ES-DEP-16: Predefined identity, MANAGED_BY default, and mandatory deployment keys

**Pre-requisites:**

1. Environment Instance exists with:
   1. Tenant, Cloud, Namespace, and Application with SBOM.
   2. Cloud defines `apiUrl`, `publicUrl`, `protocol`, and `apiPort` so mandatory predefined keys can be written to root `deployment-parameters.yaml`.
   3. Tenant, Cloud, Namespace, and Application `deployParameters` do not define `MANAGED_BY`, so the predefined default applies for this run.
   4. Cloud `apiUrl: api.cluster-01.example.com`.
   5. Tenant `name: tenant-a`.
   6. SBOM application component name `billing-app`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job loads Cloud, Tenant, namespace, and SBOM metadata and resolves predefined deployment keys.

**Results:**

1. `deployment-parameters.yaml` contains `MANAGED_BY: argocd`.

2. **Identity mapping** - root-level predefined keys in `deployment-parameters.yaml`:

   1. `CLOUD_API_HOST: api.cluster-01.example.com`
   2. `TENANTNAME: tenant-a`
   3. `APPLICATION_NAME: billing-app`

3. `deployment-parameters.yaml` includes mandatory keys: `DEPLOYMENT_SESSION_ID`, `MANAGED_BY`, `CLOUD_API_HOST`, `CLOUD_PUBLIC_HOST`, `CLOUD_PROTOCOL`, `CLOUD_API_PORT`, `TENANTNAME`, `NAMESPACE`, `APPLICATION_NAME`

**Example (`deployment-parameters.yaml`, illustrative root map for Results 1-3):**

```yaml
DEPLOYMENT_SESSION_ID: "550e8400-e29b-41d4-a716-446655440000"
MANAGED_BY: argocd
APPLICATION_NAME: billing-app
TENANTNAME: tenant-a
NAMESPACE: billing-ns
CLOUD_API_HOST: api.cluster-01.example.com
CLOUD_PUBLIC_HOST: apps.cluster-01.example.com
CLOUD_PROTOCOL: https
CLOUD_API_PORT: "6443"
```

### UC-ES-DEP-22: DBaaS and Vault disabled omit optional deployment URLs

**Pre-requisites:**

1. Environment Instance exists with:
   1. Tenant, Cloud, Namespace, and Application with SBOM sufficient for root `deployment-parameters.yaml`.
   2. Cloud disables DBaaS and Vault: no enabling `dbaasConfigs` / `vaultConfig` usage (explicit `dbaasConfigs[0].enable: false` and `vaultConfig.enable: false` is acceptable).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. It evaluates DBaaS and Vault toggles from the Cloud definition.
   2. It omits DBaaS- and Vault-dependent optional URLs when those features are off.

**Results:**

1. `deployment-parameters.yaml` contains `DBAAS_ENABLED: false` and `VAULT_ENABLED: false`.
2. `deployment-parameters.yaml` omits `API_DBAAS_ADDRESS`, `DBAAS_AGGREGATOR_ADDRESS`, `VAULT_ADDR`, and `PUBLIC_VAULT_URL`.

**Example (`deployment-parameters.yaml`, excerpt):**

```yaml
DBAAS_ENABLED: false
VAULT_ENABLED: false
```

### UC-ES-DEP-23: Public and private gateway URLs from deployment context

**Pre-requisites:**

1. Environment Instance exists with:
   1. Tenant, Cloud, Namespace, and Application with SBOM sufficient for root `deployment-parameters.yaml`.
   2. Before gateway URL derivation, root-level deployment context exposes these keys and values: `CLOUD_PROTOCOL: https`, `CLOUD_PUBLIC_HOST: apps.cluster-01.example.com`, `ORIGIN_NAMESPACE: billing-origin`, `PRIVATE_GATEWAY_ROUTE_HOST: private-gw.team.example.com`, and `CLOUD_API_HOST: api.cluster-01.example.com`.
   3. `PUBLIC_GATEWAY_ROUTE_HOST` is unset.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. It computes `PUBLIC_GATEWAY_URL` using the default formula when no public gateway route host override is set and sets `PRIVATE_GATEWAY_URL` from `PRIVATE_GATEWAY_ROUTE_HOST`.

**Results:**

1. Gateway outputs:

   1. `PUBLIC_GATEWAY_URL: https://public-gateway-billing-origin.apps.cluster-01.example.com`
   2. `PRIVATE_GATEWAY_URL: https://private-gw.team.example.com`

2. `PUBLIC_GATEWAY_ROUTE_HOST` is omitted when unset (same run as Pre-requisite 3).

**Example (`deployment-parameters.yaml`, illustrative gateway keys):**

```yaml
ORIGIN_NAMESPACE: billing-origin
PRIVATE_GATEWAY_ROUTE_HOST: private-gw.team.example.com
PUBLIC_GATEWAY_URL: https://public-gateway-billing-origin.apps.cluster-01.example.com
PRIVATE_GATEWAY_URL: https://private-gw.team.example.com
```

### UC-ES-DEP-A15: Blue-green predefined deployment parameters

**Pre-requisites:**

1. Environment Instance exists with:
   1. `bg_domain` defines controller URL and credential references for username and password as described in topology and deployment predefined parameter tables.
   2. Credential store contains the referenced username-password secret with known fixture values.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job resolves BG controller URL and credential-backed login fields into deployment outputs.

**Results:**

1. `deployment-parameters.yaml` contains `BG_CONTROLLER_URL` from the BG Domain definition.
2. `BG_CONTROLLER_LOGIN` and `BG_CONTROLLER_PASSWORD` match the fixture credential; non-sensitive fields stay in `deployment-parameters.yaml`, sensitive values in `credentials.yaml`.

**Example (`deployment-parameters.yaml`, excerpt):**

```yaml
BG_CONTROLLER_URL: https://bg-controller.example.com/nonprod
BG_CONTROLLER_LOGIN: fixture-bg-user
# ...
```

**Example (`credentials.yaml`, excerpt):**

```yaml
BG_CONTROLLER_PASSWORD: fixture-bg-password
```

### UC-ES-DEP-A8: custom-params.yaml from CUSTOM_PARAMS

**Pre-requisites:**

1. Environment Instance exists with:
   1. SBOM, Solution Descriptor, Cloud, and Namespace definitions sufficient for a normal Effective Set deployment pass for the target application (so `deployment-parameters.yaml` and related deployment tree paths exist after generation).
   2. No `deployment` overrides are present in repository or Calculator inputs other than what this UC injects via the pipeline (baseline `custom-params.yaml` for deployment is empty or absent before the run, if your fixture tracks that file).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `CUSTOM_PARAMS: '{"deployment":{"CUSTOM_ROUTING_ENABLED":"true","CUSTOM_RESOURCE_LIMIT":"512Mi"}}'` (replace keys and values with your fixture strings; JSON must validate against [`/schemas/custom-params.schema.json`](/schemas/custom-params.schema.json))

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The job appends `--custom-params='<value of CUSTOM_PARAMS>'` to the Calculator invocation (same string as the pipeline variable).
   2. The Calculator emits the `deployment` object into `custom-params.yaml` under `deployment/<namespace-folder>/<application>/values/`.

**Results:**

1. `custom-params.yaml` contains exactly the keys from the `deployment` object in `CUSTOM_PARAMS`, with matching values.

**Example (`deployment/<namespace-folder>/<application>/values/custom-params.yaml`):**

```yaml
CUSTOM_ROUTING_ENABLED: "true"
CUSTOM_RESOURCE_LIMIT: 512Mi
```

## Sensitive Parameters Processing

This group covers deployment and pipeline credentials, macro-backed secret material, and SSL bundle duplication rules described under [Sensitive parameters processing](/docs/features/calculator-cli.md#version-20-sensitive-parameters-processing) and deployment credentials.

### UC-ES-DEP-A6: Deployment credentials, feature secrets, and SSL bundle macros

**Pre-requisites:**

1. Environment Instance exists with:
   1. Namespace or Cloud default credentials resolve to a cluster API token.
   2. Cloud optionally enables DBaaS, MaaS, Vault, and Consul with credential IDs pointing at stored secrets.
   3. Resolved deployment parameters include `DEFAULT_SSL_CERTIFICATES_BUNDLE` set to a fixed non-empty string at Tenant, Cloud, Namespace, or Application level.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job resolves sensitive values from Environment Instance credential bindings (including credential macro expansion where applicable).
   2. It writes deployment-context secrets to `credentials.yaml`.
   3. It copies the resolved `DEFAULT_SSL_CERTIFICATES_BUNDLE` value into secured deployment credentials alongside other sensitive predefined keys.

**Results:**

1. `credentials.yaml` includes `K8S_TOKEN`.
2. Keys such as DBaaS, MaaS, Vault, or Consul credentials appear only when the related Cloud feature is enabled and its credential reference is set.
3. `credentials.yaml` contains `SSL_SECRET_VALUE` and `CA_BUNDLE_CERTIFICATE`, both equal to the resolved `DEFAULT_SSL_CERTIFICATES_BUNDLE` value.

**Example (`deployment/<namespace-folder>/<application>/values/credentials.yaml`, excerpt):**

```yaml
K8S_TOKEN: eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJFZmJvVkYtRlNlLXBWYmMtUkJaYUdjZlZyTkNnYmNnTkZjYzJnPSJ9.example.simplified
SSL_SECRET_VALUE: |
  -----BEGIN CERTIFICATE-----
  MIIEI...
  -----END CERTIFICATE-----
CA_BUNDLE_CERTIFICATE: |
  -----BEGIN CERTIFICATE-----
  MIIEI...
  -----END CERTIFICATE-----
# Feature-backed secrets (DBaaS, MaaS, Vault, Consul) appear only when enabled (Result 2).
```

## Collision Routing

### UC-ES-DEP-20: Service-name collision routing

**Pre-requisites:**

1. **SBOM `services`:** At least one service id is present (example: `orders-api`).

2. **Root deployment parameter:** The merged deployment map has a **top-level** key equal to that service id; the value is not credential-macro-backed (non-sensitive).

3. **`deploy_param` exclusion:** That key is not the image-parameter case excluded from collision routing (see **Collision Parameters** in `docs/features/calculator-cli.md`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job identifies root-level keys whose names match entries under `services`.
   2. It removes those non-sensitive keys from the main deployment parameters output.
   3. It writes them to `collision-deployment-parameters.yaml` under `deployment/<namespace-folder>/<application>/values/`.

**Results:**

1. `collision-deployment-parameters.yaml` exists under `deployment/<namespace-folder>/<application>/values/` and lists only service-named root keys that were treated as non-sensitive, with values matching the fixture.

**Example (`deployment/<namespace-folder>/<application>/values/collision-deployment-parameters.yaml`, excerpt):**

```yaml
orders-api:
  replicaCount: 2
```

## Deploy Descriptor

### UC-ES-DEP-A9: deploy-descriptor.yaml structure and configuration artifacts

**Pre-requisites:**

1. Environment Instance exists with:
   1. SBOM lists at least one image-type service and one configuration-type service so both shapes contribute to the descriptor.
   2. SBOM defines one configuration-type service (`application/vnd.qubership.configuration.smartplug`, `application/vnd.qubership.configuration.frontend`, `application/vnd.qubership.configuration.cdn`, or `application/vnd.qubership.configuration`).
   3. Under that configuration service, child components include artifact MIME types that populate `artifacts[]`, plus two `application/zip` children: one omits classifier, and two others share the same classifier value.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job builds `deploy-descriptor.yaml` from SBOM artifact metadata by service type.
   2. The job maps smartplug services to OSGi bundle metadata for primary artifact fields; it maps frontend, CDN, and generic configuration services to zip metadata per feature documentation.
   3. It emits one `artifacts[]` element per qualifying child artifact MIME type.
   4. It builds `tArtifactNames` from zip children, using default classifier `ecl` when classifier is missing or blank.

**Results:**

1. `deploy-descriptor.yaml` contains `global`, a top-level `deployDescriptor` map, and per-service sections aligned with the Effective Set v2.0 descriptor layout.
2. `DEPLOYMENT_SESSION_ID` in this file matches the session value in root `deployment-parameters.yaml` from the same run.
3. The configuration service section inside `deploy-descriptor.yaml` has a non-empty `artifacts` list when qualifying children exist.
4. `tArtifactNames` includes `ecl: <name>-<version>.zip` when classifier is absent or empty on the zip child used for that entry.
5. Duplicate classifier keys from multiple zip children keep the last processed mapping.

**Example (`deploy-descriptor.yaml`, excerpt - configuration-type service with `artifacts` / `tArtifactNames`; anchors mirror repo fixtures):**

```yaml
global: &g
  deployDescriptor: &dd
    cfg-service:
      name: cfg-service
      artifacts:
        - artifact_id: ""
          artifact_path: ""
          artifact_type: ""
          classifier: ""
          deploy_params: ""
          gav: ""
          group_id: ""
          id: "com.example.cfg:primary-osgi:2.3.0"
          name: "primary-osgi-2.3.0.jar"
          repository: ""
          type: jar
          url: ""
          version: ""
      tArtifactNames:
        ecl: plugin-bundle-2.3.0.zip
deployDescriptor: *dd
cfg-service:
  APPLICATION_NAME: example-app
  DEPLOYMENT_SESSION_ID: "550e8400-e29b-41d4-a716-446655440000"
  MANAGED_BY: argocd
  deployDescriptor: *dd
  global: *g
APPLICATION_NAME: example-app
DEPLOYMENT_SESSION_ID: "550e8400-e29b-41d4-a716-446655440000"
MANAGED_BY: argocd
```

## Per-Service Parameters

### UC-ES-DEP-A11: Per-service layout and resource profiles

**Pre-requisites:**

1. Environment Instance exists with:
   1. **Charted SBOM:** includes `application/vnd.qubership.app.chart` and a chart name that normalizes (case or underscores).
   2. **Flat SBOM:** no app chart; at least two services.
   3. **Profiles (optional):** SBOM has `application/vnd.qubership.resource-profile-baseline` and Environment Instance overrides that service.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Charted: output is grouped by service under `per-service-parameters/<normalized-chart>/`.
   2. Flat: one folder per service under `per-service-parameters/<service>/`.
   3. Profiles: SBOM baseline merges with Environment Instance overrides.

**Results:**

1. Charted folder name is normalized, not the raw chart string from SBOM.
2. Flat layout has one directory per service.
3. Same service has the same parameter keys in charted vs flat layouts.
4. With profiles, output reflects baseline plus overrides (assert using fixture literals).

**Example (paths under `per-service-parameters/`, illustrative):**

```text
# Charted SBOM (normalized chart folder name)
per-service-parameters/
  my-chart-name/
    billing-api/
      deployment-parameters.yaml
    orders-api/
      deployment-parameters.yaml

# Flat SBOM (no app chart)
per-service-parameters/
  billing-api/
    deployment-parameters.yaml
  orders-api/
    deployment-parameters.yaml
```

**Example (`per-service-parameters/my-chart-name/billing-api/deployment-parameters.yaml`, excerpt):**

```yaml
DEPLOYMENT_SESSION_ID: "550e8400-e29b-41d4-a716-446655440000"
MANAGED_BY: argocd
SERVICE_NAME: billing-api
# ... per-service predefined keys from SBOM MIME type ...
```

## Cross-Context Effective Set Consistency

Namespace mapping keys must stay aligned across deployment, runtime, and cleanup trees as described for [mapping.yml](/docs/features/calculator-cli.md#version-20deployment-parameter-context-mappingyml) and the runtime and cleanup mapping sections.

### UC-ES-DEP-A14: deployment mapping.yaml

**Pre-requisites:**

1. Environment Instance exists with:
   1. Solution Descriptor lists the namespaces that receive deployment mapping entries.
   2. Each namespace has a `name` used as the mapping key.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The job writes `deployment/mapping.yaml` at the Effective Set root: each namespace `name` maps to a deployment path starting with `/environments`, sorted stably.

**Results:**

1. File exists.
2. Keys are exactly those namespace names; values use the expected `/environments/.../effective-set/deployment/...` prefix.
3. Same keys appear under `runtime/mapping.yaml` and `cleanup/mapping.yaml` with `.../runtime/...` and `.../cleanup/...` path prefixes respectively.

**Example (`deployment/mapping.yaml`):**

```yaml
pl-01-monitoring: /environments/cluster-01/pl-01/effective-set/deployment/monitoring-origin
pl-01-pg: /environments/cluster-01/pl-01/effective-set/deployment/pg
```

### UC-ES-RUN-3: runtime mapping.yaml key set

**Pre-requisites:**

1. Environment Instance exists with:
   1. Solution Descriptor lists the namespaces that receive deployment mapping entries.
   2. Each namespace has a `name` used as the mapping key.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job computes namespace-to-path mapping for runtime output.
   2. It writes `runtime/mapping.yaml`.

**Results:**

1. `runtime/mapping.yaml` exists.
2. The mapping keys are exactly the namespace `name` values from `deployment/mapping.yaml` for the same run.
3. Each value starts with `/environments/.../effective-set/runtime/<namespace-folder>` for the corresponding namespace.

**Example (`runtime/mapping.yaml`):**

```yaml
pl-01-monitoring: /environments/cluster-01/pl-01/effective-set/runtime/monitoring-origin
pl-01-pg: /environments/cluster-01/pl-01/effective-set/runtime/pg
```

### UC-ES-CLN-3: cleanup mapping.yaml key set

**Pre-requisites:**

1. Environment Instance exists with:
   1. Solution Descriptor lists the namespaces that receive deployment mapping entries.
   2. Each namespace has a `name` used as the mapping key.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job computes namespace-to-path mapping for cleanup output.
   2. It writes `cleanup/mapping.yaml`.

**Results:**

1. `cleanup/mapping.yaml` exists.
2. The mapping keys are exactly the namespace `name` values from `deployment/mapping.yaml` for the same run.
3. Each value starts with `/environments/.../effective-set/cleanup/<namespace-folder>` for the corresponding namespace.

**Example (`cleanup/mapping.yaml`):**

```yaml
pl-01-monitoring: /environments/cluster-01/pl-01/effective-set/cleanup/monitoring-origin
pl-01-pg: /environments/cluster-01/pl-01/effective-set/cleanup/pg
```

## Pipeline Context

This section covers use cases for [Pipeline Parameter Context](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context) in Effective Set v2.0. Cloud `e2eParameters` split into `pipeline/parameters.yaml` and `pipeline/credentials.yaml`. When the instance pipeline passes [`--pipeline-consumer-specific-schema-path`/`-pcssp`](/docs/features/calculator-cli.md#calculator-command-line-tool-execution-attributes) one or more times, the Calculator may emit `<consumer>-parameters.yaml` and `<consumer>-credentials.yaml` per [Consumer Specific Context of Pipeline Context](/docs/features/calculator-cli.md#consumer-specific-context-of-pipeline-context). The consumer name is the schema filename with the `.schema.json` suffix removed.

Unless a use case states otherwise, consumer UCs assume a schema file on disk (for example `consumer-v1.0.schema.json`) whose content matches the reference file [`/examples/consumer-v1.0.json`](/examples/consumer-v1.0.json) from the feature documentation:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "version": {
      "type": "integer"
    },
    "group": {
      "type": "string",
      "default": "group"
    },
    "artifact": {
      "type": "string",
      "default": "artifact"
    },
    "registry": {
      "type": "string"
    }
  },
  "required": [
    "name",
    "version",
    "group"
  ]
}
```

### UC-ES-PIPE-1: pipeline parameters and credentials from Cloud e2eParameters

**Pre-requisites:**

1. Environment Instance exists with:
   1. Cloud `e2eParameters` includes at least one known non-sensitive root value and one known sensitive root value.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The job splits `e2eParameters` into sensitive and non-sensitive sets and writes `pipeline/parameters.yaml` and `pipeline/credentials.yaml`.

**Results:**

1. `pipeline/parameters.yaml` has the expected non-sensitive keys and values.
2. `pipeline/credentials.yaml` has the expected sensitive keys and resolved secrets.

**Example (`pipeline/parameters.yaml`):**

```yaml
PIPE_PUBLIC_SETTING: public-value-from-cloud-e2e
```

**Example (`pipeline/credentials.yaml`):**

```yaml
PIPE_SECRET_SETTING: resolved-secret-from-credential-store
```

### UC-ES-PIPE-4: Consumer copies root keys from pipeline context

**Pre-requisites:**

1. Repository (or pipeline image) contains a consumer JSON Schema file passed to the Calculator as `-pcssp`, for example `consumer-v1.0.schema.json`, with the same structure as [`/examples/consumer-v1.0.json`](/examples/consumer-v1.0.json) (see [Pipeline Context](#pipeline-context)).
2. Environment Instance exists with:
   1. Cloud `e2eParameters` defines root keys `name`, `version`, and `group` such that, after the pipeline split, they appear in `pipeline/parameters.yaml` with fixture values (for example `name: acme-service`, `version: 1`, `group: acme-group`).
   2. Cloud `e2eParameters` defines root key `registry` such that, after the pipeline split, it appears in `pipeline/credentials.yaml` with the resolved fixture secret (sensitivity follows Environment Instance rules for that key).
3. Instance wiring passes `-pcssp` with the path to that schema file before Effective Set generation.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job builds general pipeline parameters and credentials from Cloud `e2eParameters`.
   2. For each root property declared in the consumer schema, the Calculator copies the value from the general pipeline output when that key exists ([principle 1](/docs/features/calculator-cli.md#consumer-specific-context-of-pipeline-context)).

**Results:**

1. `pipeline/consumer-v1.0-parameters.yaml` (prefix from `consumer-v1.0.schema.json`) contains `name`, `version`, and `group` with the same values as in `pipeline/parameters.yaml`.
2. `pipeline/consumer-v1.0-credentials.yaml` contains `registry` with the same value as in `pipeline/credentials.yaml`.

**Example (`pipeline/parameters.yaml`, excerpt):**

```yaml
name: acme-service
version: 1
group: acme-group
```

**Example (`pipeline/credentials.yaml`, excerpt):**

```yaml
registry: resolved-registry-secret
```

**Example (`pipeline/consumer-v1.0-parameters.yaml`, excerpt):**

```yaml
name: acme-service
version: 1
group: acme-group
```

**Example (`pipeline/consumer-v1.0-credentials.yaml`, excerpt):**

```yaml
registry: resolved-registry-secret
```

### UC-ES-PIPE-5: Consumer schema default only

**Pre-requisites:**

1. Repository (or pipeline image) contains a consumer schema file as in [UC-ES-PIPE-4](#uc-es-pipe-4-consumer-copies-root-keys-from-pipeline-context) (`consumer-v1.0.schema.json` matching [`/examples/consumer-v1.0.json`](/examples/consumer-v1.0.json)).
2. Environment Instance exists with:
   1. Cloud `e2eParameters` supplies `name`, `version`, and `group` so the general pipeline output includes those keys.
   2. Cloud `e2eParameters` omits root key `artifact`, which is optional in the consumer schema and carries default `"artifact"`.
3. Instance wiring passes `-pcssp` with the path to that schema file.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Consumer-specific files are built; the schema default is applied for `artifact` ([principle 2.1](/docs/features/calculator-cli.md#consumer-specific-context-of-pipeline-context)).

**Results:**

1. `pipeline/consumer-v1.0-parameters.yaml` includes `artifact: artifact` even though general `pipeline/parameters.yaml` omits `artifact`.
2. `pipeline/consumer-v1.0-parameters.yaml` still contains `name`, `version`, and `group` with the same values as in `pipeline/parameters.yaml` (principle 1 copy).

**Example (`pipeline/consumer-v1.0-parameters.yaml`, excerpt):**

```yaml
name: acme-service
version: 1
group: acme-group
artifact: artifact
```

### UC-ES-PIPE-6: Consumer omits optional schema-only key

**Pre-requisites:**

1. Repository (or pipeline image) contains a consumer schema file as in [UC-ES-PIPE-4](#uc-es-pipe-4-consumer-copies-root-keys-from-pipeline-context) (`consumer-v1.0.schema.json` matching [`/examples/consumer-v1.0.json`](/examples/consumer-v1.0.json)).
2. Environment Instance exists with:
   1. Cloud `e2eParameters` supplies required keys `name`, `version`, and `group` for a successful pipeline split.
   2. Cloud `e2eParameters` omits optional root `registry`, which has no default in the schema.
3. Instance wiring passes `-pcssp` with the path to that schema file.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Consumer-specific files are built; optional properties without default and without pipeline value are skipped ([principle 2.2](/docs/features/calculator-cli.md#consumer-specific-context-of-pipeline-context)).

**Results:**

1. Neither `pipeline/consumer-v1.0-parameters.yaml` nor `pipeline/consumer-v1.0-credentials.yaml` contains root key `registry`.

**Example (`pipeline/consumer-v1.0-credentials.yaml`, excerpt):**

```yaml
{}
```

### UC-ES-PIPE-7: Consumer mandatory key without value fails

**Pre-requisites:**

1. Repository (or pipeline image) contains a consumer schema file as in [UC-ES-PIPE-4](#uc-es-pipe-4-consumer-copies-root-keys-from-pipeline-context) (`consumer-v1.0.schema.json` matching [`/examples/consumer-v1.0.json`](/examples/consumer-v1.0.json)).
2. Environment Instance exists with:
   1. Cloud `e2eParameters` omits root key `name`, which is required by the consumer schema and has no default.
   2. Other keys in `e2eParameters` are insufficient to populate `name` in the general pipeline output.
3. Instance wiring passes `-pcssp` with the path to that schema file.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Consumer assembly runs and fails because the required property has no pipeline value and no default ([principle 2.3](/docs/features/calculator-cli.md#consumer-specific-context-of-pipeline-context)).

**Results:**

1. Effective Set generation does not complete successfully.
2. Failure indicates the required consumer pipeline property is missing from E2E configuration (property `name` for this schema).

## Runtime Context

This section covers use cases for [Runtime Parameter Context](/docs/features/calculator-cli.md#version-20-runtime-parameter-context) in Effective Set v2.0 (`runtime/parameters.yaml`, `runtime/credentials.yaml`, `runtime/mapping.yaml`), including technical configuration and optional `CUSTOM_PARAMS` runtime overrides. Mapping key assertions are paired with deployment and cleanup under [Cross-context Effective Set consistency](#cross-context-effective-set-consistency).

### UC-ES-RUN-1: runtime/parameters.yaml from technicalConfigurationParameters

**Pre-requisites:**

1. Environment Instance exists with:
   1. Tenant, Cloud, Namespace, or Application define non-sensitive `technicalConfigurationParameters`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job merges runtime non-sensitive parameters from technical configuration sections.
   2. It writes runtime non-sensitive output per namespace and application.

**Results:**

1. `runtime/<namespace-folder>/<application>/parameters.yaml` exists for processed applications.
2. The file contains merged non-sensitive runtime parameters.

**Example (`runtime/monitoring-origin/MONITORING/parameters.yaml`, excerpt):**

```yaml
runtime_metrics_port: "9090"
runtime_scrape_interval: 30s
```

### UC-ES-RUN-2: runtime/credentials.yaml includes sensitive and custom runtime

**Pre-requisites:**

1. Environment Instance exists with:
   1. Runtime-sensitive `technicalConfigurationParameters` are defined.
   2. `--custom-params` includes `runtime` section with at least one key.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `CUSTOM_PARAMS` passes runtime values to Calculator `--custom-params`.

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job builds runtime sensitive context.
   2. It merges runtime values from `--custom-params` into runtime credentials with higher priority.
   3. It writes runtime sensitive output.

**Results:**

1. `runtime/<namespace-folder>/<application>/credentials.yaml` exists.
2. The file contains sensitive runtime parameters.
3. For keys present in both runtime technical parameters and runtime custom params, the output value equals the custom runtime value.

**Example (`runtime/monitoring-origin/MONITORING/credentials.yaml`, excerpt):**

```yaml
RUNTIME_DB_PASSWORD: from-custom-params-overrides-technical
RUNTIME_ONLY_FROM_CUSTOM: extra-runtime-secret
```

## Cleanup Context

This section covers use cases for [Cleanup Context](/docs/features/calculator-cli.md#version-20-cleanup-context) in Effective Set v2.0 (`cleanup/parameters.yaml`, `cleanup/credentials.yaml`, `cleanup/mapping.yaml`). Cleanup reuses deploy-parameter sources; sensitive cleanup merges `CUSTOM_PARAMS` runtime entries using the same precedence rules as runtime credentials.

### UC-ES-CLN-1: cleanup/parameters.yaml from deployParameters

**Pre-requisites:**

1. Environment Instance exists with:
   1. Tenant, Cloud, or Namespace define non-sensitive `deployParameters`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job calculates cleanup non-sensitive context from deploy parameter hierarchy.
   2. It writes cleanup parameters per namespace.

**Results:**

1. `cleanup/<namespace-folder>/parameters.yaml` exists.
2. The file contains merged non-sensitive cleanup parameters from Tenant, Cloud, and Namespace deploy parameters.

**Example (`cleanup/monitoring-origin/parameters.yaml`, excerpt):**

```yaml
CLEANUP_RETENTION_DAYS: "14"
CLEANUP_PARALLEL_JOBS: "2"
```

### UC-ES-CLN-2: cleanup/credentials.yaml includes sensitive and custom runtime

**Pre-requisites:**

1. Environment Instance exists with:
   1. Cleanup-sensitive deploy parameters are defined at Tenant, Cloud, or Namespace levels.
   2. `--custom-params` includes `runtime` section with at least one key.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`
3. `CUSTOM_PARAMS` passes runtime values to Calculator `--custom-params`.

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The `generate_effective_set` job calculates cleanup sensitive context.
   2. It merges runtime custom parameters from `--custom-params` into cleanup credentials with higher priority.
   3. It writes cleanup credentials per namespace.

**Results:**

1. `cleanup/<namespace-folder>/credentials.yaml` exists.
2. The file contains sensitive cleanup parameters.
3. For keys present in both cleanup-sensitive parameters and custom runtime params, the output value equals the custom runtime value.

**Example (`cleanup/monitoring-origin/credentials.yaml`, excerpt):**

```yaml
CLEANUP_API_TOKEN: from-custom-params-overrides-cleanup
CLEANUP_ONLY_CUSTOM: cleanup-extra-secret
```

## Topology Context

This section covers use cases for [Version 2.0 Topology Context](/docs/features/calculator-cli.md#version-20-topology-context) in Effective Set v2.0, in particular the `cluster` block in `topology/parameters.yaml` (Cloud Passport when present, otherwise `inventory.clusterUrl` parsing rules in the Environment Inventory).

Executable checks with `test_data/test_environments/cluster01/...` paths are in [`docs/test-cases/cluster-endpoint-topology-context.md`](../test-cases/cluster-endpoint-topology-context.md). TC-CETC-001 through TC-CETC-007 correspond to UC-ES-TOP-1 through UC-ES-TOP-7. Output keys are `api_url`, `api_port`, `public_url`, and `protocol` (the test-case document may still reference historical label spellings in expected results).

### UC-ES-TOP-1: Cluster endpoint from Cloud Passport

**Pre-requisites:**

1. Environment Instance exists with:
   1. Target environment `cluster01/env-with-passport` exists.
   2. Cloud Passport is configured and contains cluster endpoint data.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-with-passport`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The topology context is generated and `cluster` endpoint fields are resolved from Cloud Passport data.

**Results:**

1. `topology/parameters.yaml` contains `cluster` with values from Cloud Passport:
   1. `api_url`
   2. `api_port`
   3. `public_url`
   4. `protocol`

**Example (`topology/parameters.yaml`, illustrative Passport-backed cluster):**

```yaml
cluster:
  api_url: api.passport.example.com
  api_port: "6443"
  public_url: apps.passport.example.com
  protocol: https
```

### UC-ES-TOP-2: Cluster endpoint from inventory.clusterUrl

**Pre-requisites:**

1. Environment Instance exists with:
   1. Target environment `cluster01/env-without-passport` exists.
   2. Cloud Passport is not configured.
   3. `inventory.clusterUrl` is set to `https://API.cl-03.managed.qubership.cloud:6443`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-without-passport`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The topology context derives `cluster` endpoint values from `inventory.clusterUrl`.

**Results:**

1. `topology/parameters.yaml` contains:
   1. `cluster.api_url: API.cl-03.managed.qubership.cloud`
   2. `cluster.api_port: 6443`
   3. `cluster.public_url: apps.cl-03.managed.qubership.cloud`
   4. `cluster.protocol: https`

**Example (`topology/parameters.yaml`):**

```yaml
cluster:
  api_url: API.cl-03.managed.qubership.cloud
  api_port: "6443"
  public_url: apps.cl-03.managed.qubership.cloud
  protocol: https
```

### UC-ES-TOP-3: inventory.clusterUrl parsing variants

**Pre-requisites:**

1. Environment Instance exists with:
   1. Environment Inventory fixtures for non-standard port, protocol, and hostname scenarios (`cluster01/env-nonstandard-port`, `cluster01/env-http-protocol`, and `cluster01/env-nonstandard-hostname`).
   2. Cloud Passport is not configured for those inventories.

**Trigger:**

Three instance pipeline runs (GitLab or GitHub). Each run uses mandatory `ENV_NAMES` (`docs/instance-pipeline-parameters.md`, section `ENV_NAMES`) together with `CALCULATOR_CLI: true`. Environment IDs per run:

1. Scenario port: `ENV_NAMES: cluster01/env-nonstandard-port` and `inventory.clusterUrl` is `https://API.cl-03.managed.qubership.cloud:8443`.
2. Scenario protocol: `ENV_NAMES: cluster01/env-http-protocol` and `inventory.clusterUrl` is `http://API.cl-03.managed.qubership.cloud:6443`.
3. Scenario hostname: `ENV_NAMES: cluster01/env-nonstandard-hostname` and `inventory.clusterUrl` is `https://cluster.cl-03.managed.qubership.cloud:6443`.

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The topology context derives `cluster` endpoint values from `inventory.clusterUrl`, preserving non-default port, protocol, and hostname parsing per product rules.

**Results:**

1. Scenario port: `topology/parameters.yaml` contains `cluster.api_url: API.cl-03.managed.qubership.cloud`, `cluster.api_port: 8443`, `cluster.public_url: apps.cl-03.managed.qubership.cloud`, and `cluster.protocol: https`.
2. Scenario protocol: `topology/parameters.yaml` contains `cluster.api_url: API.cl-03.managed.qubership.cloud`, `cluster.api_port: 6443`, `cluster.public_url: apps.cl-03.managed.qubership.cloud`, and `cluster.protocol: http`.
3. Scenario hostname: `topology/parameters.yaml` contains `cluster.api_url: cluster.cl-03.managed.qubership.cloud`, `cluster.api_port: 6443`, `cluster.public_url: cluster.cl-03.managed.qubership.cloud`, and `cluster.protocol: https`.

**Scenario port (`topology/parameters.yaml`):**

```yaml
cluster:
  api_url: API.cl-03.managed.qubership.cloud
  api_port: "8443"
  public_url: apps.cl-03.managed.qubership.cloud
  protocol: https
```

**Scenario protocol:**

```yaml
cluster:
  api_url: API.cl-03.managed.qubership.cloud
  api_port: "6443"
  public_url: apps.cl-03.managed.qubership.cloud
  protocol: http
```

**Scenario hostname:**

```yaml
cluster:
  api_url: cluster.cl-03.managed.qubership.cloud
  api_port: "6443"
  public_url: cluster.cl-03.managed.qubership.cloud
  protocol: https
```

### UC-ES-TOP-6: Cloud Passport overrides inventory.clusterUrl

**Pre-requisites:**

1. Environment Instance exists with:
   1. Target environment `cluster01/env-passport-override` exists.
   2. Cloud Passport is configured and contains cluster endpoint data.
   3. `inventory.clusterUrl` is set to `https://API.cl-03.managed.qubership.cloud:6443`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-passport-override`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The topology context resolves `cluster` endpoint values using Cloud Passport when both Cloud Passport and `inventory.clusterUrl` are present.

**Results:**

1. `topology/parameters.yaml` contains `cluster` values from Cloud Passport.
2. `inventory.clusterUrl` value is not used for final `cluster` fields in this scenario.

**Example (`topology/parameters.yaml`, illustrative - Passport wins over inventory URL):**

```yaml
cluster:
  api_url: api.passport.override.example.com
  api_port: "6443"
  public_url: apps.passport.override.example.com
  protocol: https
```

### UC-ES-TOP-7: Missing cluster information yields empty cluster fields

**Pre-requisites:**

1. Environment Instance exists with:
   1. Target environment `cluster01/env-missing-cluster-info` exists.
   2. Cloud Passport is not configured.
   3. `inventory.clusterUrl` is not specified.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-missing-cluster-info`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. The topology context attempts to resolve `cluster` endpoint values without Cloud Passport and without `inventory.clusterUrl`.

**Results:**

1. `topology/parameters.yaml` contains `cluster` with empty values:
   1. `cluster.api_url: ""`
   2. `cluster.api_port: ""`
   3. `cluster.public_url: ""`
   4. `cluster.protocol: ""`

**Example (`topology/parameters.yaml`):**

```yaml
cluster:
  api_url: ""
  api_port: ""
  public_url: ""
  protocol: ""
```
