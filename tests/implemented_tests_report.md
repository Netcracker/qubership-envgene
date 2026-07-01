# Report on Implemented Tests

This document lists the integration test groups (Cucumber Feature Files) that are implemented, active, and successfully executed as part of the Qubership EnvGene pipeline testing.

## 1. Unified Pipeline Success
This group covers the basic successful execution scenarios of the pipeline:

* **App & Reg Defs Template Rendering** (`app_reg_defs_template_rendering.feature`): Verifies the correct rendering of Jinja templates for `AppDefs` and `RegDefs` (Application and Registry definitions).
  * *Example Test Cases:* `UC-ARD-TR-1: Basic AppDef/RegDef template rendering`, `UC-ARD-TR-2: Basic AppDef/RegDef template delete`

* **Artifact Downloading** (`artifact-downloading.feature`): Validates the process of downloading SBOMs and Helm charts based on data from `AppDefs`.
  * *Example Test Cases:* `UC-AD-SD-1: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v1)`, `UC-AD-SD-2: Download SD from Artifactory with Anonymous Access`

* **Auto Environment Name** (`auto-environment-name.feature`): Checks the logic for automatically determining the environment name based on the Git branch or provided variables.
  * *Example Test Cases:* `UC-AEN-END-1: Environment with no explicit environmentName defined`, `UC-AEN-END-2: Environment with explicit environmentName defined`

* **Blue-Green Deployment** (`blue-green-deployment.feature`): Verifies the generation of configurations for Blue/Green namespaces (Active, Idle) based on the input state.
  * *Example Test Cases:* `UC-BG-1: Init Domain`, `UC-BG-2: Warmup`, `UC-BG-3: Promote`

* **Calculator CLI** (`calculator-cli.feature`): Tests the invocation of the external CLI to calculate resource parameters and configurations.
  * *Example Test Cases:* `UC-CC-DP-1: Exact Match`, `UC-CC-DP-2: BG Domain Match`

* **Credential Rotation** (`credential-rotation.feature`): Verifies the secrets rotation logic (adding new ones, changing passwords, saving to `credentials.yml`).
  * *Example Test Cases:* `UC-CR-TPR-1: Update Credential from Pipeline Parameter`, `UC-CR-TPR-2: Update Credential from Deployment Parameter`

* **EnvGene Null Value Validation** (`envgene-null-value-validation.feature`): Checks the protection against leaks of `envgeneNullValue` stubs into the final generated configuration files.
  * *Example Test Cases:* `UC-NVV-3: All values resolved`, `UC-NVV-4: Ignore null values when validation is disabled`

* **Environment Instance Generation** (`environment-instance-generation.feature`): Comprehensively checks the process of building the environment structure on disk (merging inventory, deploy, and E2E parameters).
  * *Example Test Cases:* `UC-EIG-NF-1: Namespace NOT in BG Domain with deploy_postfix`, `UC-EIG-NF-3: Controller Namespace in BG Domain with deploy_postfix`

* **SBOM Retention** (`sbom-retention.feature`): Validates the retention policies for downloaded SBOMs (deleting outdated/unused ones).
  * *Example Test Cases:* `UC-SBOM-1: SBOM retention disabled - no cleanup`, `UC-SBOM-3: Per-application retention keeps 10 most recent versions`

* **SD Processing** (`sd-processing.feature`): Checks the parsing of Solution Descriptors (SD) and nested artifact downloads based on them.
  * *Example Test Cases:* `UC-SD-1: Single SD_VERSION with replace mode`, `UC-SD-2: Single SD_VERSION with extended-merge mode`

## 2. Unified Pipeline Failure
This group of tests verifies the correct pipeline response (expected errors and non-zero exit codes) when provided with invalid input data:

* **Artifact Download Negative** (`artifact_download_negative.feature`): The pipeline fails when the registry is unavailable or download errors occur.
  * *Example Test Cases:* `UC-AD-ERR-1: Handle missing application definition`, `UC-AD-ERR-2: Handle missing registry definition`

* **Auto Environment Name Failure** (`auto-environment-name-failure.feature`): The pipeline fails with conflicting/missing environment variables.
  * *Example Test Cases:* `UC-AEN-END-4: Invalid folder structure for environment`

* **EnvGene Null Value Validation Failure** (`envgene-null-value-validation-failure.feature`): The pipeline fails if the `envgeneNullValue` stub leaks into the final config.
  * *Example Test Cases:* `UC-NVV-1: Unresolved parameter blocks pipeline`, `UC-NVV-2: Unresolved credential blocks pipeline`

## 3. Effective Set Generation - Deployment Context (UC-ES-DEP)
**Associated File:** `effective-set-deployment.feature`
Tests in the `UC-ES-DEP` group cover the final part of the pipeline — the generation of the `effective-set`. 
* Validates the correct assembly of `topology/credentials.yaml`, `topology/parameters.yaml`, `pipeline/parameters.yaml`, and other generated configurations.
* Verifies the correct forwarding of keys, Image Names, routing parameters, URLs (DBaaS/Vault), custom JSON parameters, and SSL bundle macros.
* Validates the reaction of the Java CLI `effective-set-generator` to broken Helm charts (flag `app_chart_validation`).
  * *Example Test Cases:* `UC-ES-DEP-14: deploy_param image keys`, `UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline`, `UC-ES-DEP-A16: app_chart_validation fails when enabled`

## 4. Environment Inventory Generation
**Associated File:** `environment-inventory-generation.feature`
* Verifies the mechanism for generating inventory files, their structure (tenant, cloud, bg_domain, namespaces), and the correct inheritance of variables at the inventory level.
  * *Example Test Cases:* `UC-EINV-ED-1: Create env_definition.yml`, `UC-EINV-ED-3: Delete env_definition.yml`

## 5. Cloud Passport Processing
**Associated Files:** `cloud-passport.feature`, `cloud_passport_negative.feature`
* Verifies the mechanism for merging Cloud Passport configurations (loading external cloud parameters into the local context) and error handling in case of an invalid passport.
  * *Example Test Cases:* `UC-01: Environment inherits cluster Cloud Passport automatically`, `UC-02: Environment uses explicitly named Cloud Passport`, `UC-08: Mixed cluster failure when infra relies on auto-association`

## 6. SBOM Storage Migration
**Associated File:** `sbom-storage-migration.feature`
* Verifies the logic for migrating the old SBOM storage format to the new one (flat structure) for backward compatibility.
  * *Example Test Cases:* `UC-SBOM-MIG-1: First run after upgrade`
