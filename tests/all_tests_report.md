# Comprehensive Test Cases Report

This document lists all known test cases across BDD features, documentation, and missing backlogs.

| Test Case | Status | Description |
| :--- | :--- | :--- |
| **Cross-Context Effective Set Consistency** | ❌ Missing | - |
| **Cross-Context Parameter References** | ❌ Missing | - |
| **Cross-Level Parameter References** | ❌ Missing | - |
| **customer E2E Test Scenarios** | ❌ Missing | - |
| **deployPostfix Matching Logic** | ❌ Missing | - |
| **environment specific parameters (Enviroment generation)** | ❌ Missing | - |
| **Parameter Type Preservation in Macro Resolution** | ❌ Missing | - |
| **Resource Profiles** | ❌ Missing | - |
| **TC-002-001: Template override on Cloud and Namespace level. Override includes paramsets with comments** | ✅ Active (BDD) | Template override on Cloud and Namespace level. Override includes paramsets with comments |
| **TC-003-001: Environment with no explicit environmentName defined** | ✅ Active (BDD) | Environment with no explicit environmentName defined |
| **TC-003-002: Environment with explicit environmentName defined** | ✅ Active (BDD) | Environment with explicit environmentName defined |
| **TC-003-003: Environment with explicit environmentName different from folder name** | ✅ Active (BDD) | Environment with explicit environmentName different from folder name |
| **TC-003-004: Invalid folder structure for environment** | ✅ Active (BDD) | Invalid folder structure for environment |
| **TC-003-005: Template rendering with derived environment name** | ✅ Active (BDD) | Template rendering with derived environment name |
| **TC-003-006: Using `current_env.cloudNameWithCluster`. `inventory.cloudName` set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cloudNameWithCluster`. `inventory.cloudName` set in Environment Inventory |
| **TC-003-007: Using `current_env.cloudNameWithCluster`. `inventory.cloudPassport` set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cloudNameWithCluster`. `inventory.cloudPassport` set in Environment Inventory |
| **TC-003-008: Using `current_env.cloudNameWithCluster`. `inventory.cloudName` and `inventory.cloudPassport` NOT set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cloudNameWithCluster`. `inventory.cloudName` and `inventory.cloudPassport` NOT set in Environment Inventory |
| **TC-003-009: Using `current_env.cmdb_name`. `inventory.deployer` set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cmdb_name`. `inventory.deployer` set in Environment Inventory |
| **TC-003-010: Using `current_env.cmdb_name`. `inventory.deployer` NOT set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cmdb_name`. `inventory.deployer` NOT set in Environment Inventory |
| **TC-003-011: Using `current_env.cmdb_url`. `inventory.deployer` set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cmdb_url`. `inventory.deployer` set in Environment Inventory |
| **TC-003-012: Using `current_env.cmdb_url`. `inventory.deployer` NOT set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cmdb_url`. `inventory.deployer` NOT set in Environment Inventory |
| **TC-003-013: Using `current_env.description`. `inventory.description` set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.description`. `inventory.description` set in Environment Inventory |
| **TC-003-014: Using `current_env.description`. `inventory.description` NOT set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.description`. `inventory.description` NOT set in Environment Inventory |
| **TC-003-015: Using `current_env.owners`. `inventory.owners` set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.owners`. `inventory.owners` set in Environment Inventory |
| **TC-003-016: Using `current_env.owners`. `inventory.owners` NOT set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.owners`. `inventory.owners` NOT set in Environment Inventory |
| **TC-003-017: Using `current_env.env_template`** | ✅ Active (BDD) | Using `current_env.env_template` |
| **TC-003-018: Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` set in Environment Inventory |
| **TC-003-019: Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` NOT set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.additionalTemplateVariables`. `envTemplate.additionalTemplateVariables` NOT set in Environment Inventory |
| **TC-003-020: Using `current_env.cloud_passport`. `inventory.cloudPassport` set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cloud_passport`. `inventory.cloudPassport` set in Environment Inventory |
| **TC-003-021: Using `current_env.cloud_passport`. `inventory.cloudPassport` NOT set in Environment Inventory** | ✅ Active (BDD) | Using `current_env.cloud_passport`. `inventory.cloudPassport` NOT set in Environment Inventory |
| **TC-003-022: Using `current_env.solution_structure`. SD exist in Instance repository** | ✅ Active (BDD) | Using `current_env.solution_structure`. SD exist in Instance repository |
| **TC-003-023: Using `current_env.solution_structure`. SD NOT in Instance repository** | ✅ Active (BDD) | Using `current_env.solution_structure`. SD NOT in Instance repository |
| **TC-004-001: Encryption Enabled with Supported Fields** | ✅ Active (BDD) | Encryption Enabled with Supported Fields |
| **TC-004-002: Encryption Skipped When Disabled** | ✅ Active (BDD) | Encryption Skipped When Disabled |
| **TC-004-003: Secret Key Mandatory for Fernet** | ✅ Active (BDD) | Secret Key Mandatory for Fernet |
| **TC-004-004: Successful Encryption Using Fernet** | ✅ Active (BDD) | Successful Encryption Using Fernet |
| **TC-004-005: Skip Encryption if File Already Encrypted Using Fernet** | ✅ Active (BDD) | Skip Encryption if File Already Encrypted Using Fernet |
| **TC-004-006: age_key Mandatory for SOPS** | ✅ Active (BDD) | age_key Mandatory for SOPS |
| **TC-004-007: Successful Encryption Using SOPS** | ✅ Active (BDD) | Successful Encryption Using SOPS |
| **TC-004-008: Skip Encryption if File Already Encrypted Using SOPS** | ✅ Active (BDD) | Skip Encryption if File Already Encrypted Using SOPS |
| **TC-CETC-001: Cluster Endpoint Information with Cloud Passport** | ✅ Active (BDD) | Cluster Endpoint Information with Cloud Passport |
| **TC-CETC-002: Cluster Endpoint Information without Cloud Passport** | ✅ Active (BDD) | Cluster Endpoint Information without Cloud Passport |
| **TC-CETC-003: Cluster Endpoint Information with Non-Standard Port** | ✅ Active (BDD) | Cluster Endpoint Information with Non-Standard Port |
| **TC-CETC-004: Cluster Endpoint Information with HTTP Protocol** | ✅ Active (BDD) | Cluster Endpoint Information with HTTP Protocol |
| **TC-CETC-005: Cluster Endpoint Information with Non-Standard Hostname** | ✅ Active (BDD) | Cluster Endpoint Information with Non-Standard Hostname |
| **TC-CETC-006: Cluster Endpoint Information with Cloud Passport Overriding clusterUrl** | ✅ Active (BDD) | Cluster Endpoint Information with Cloud Passport Overriding clusterUrl |
| **TC-CETC-007: Missing Cluster Information** | ✅ Active (BDD) | Missing Cluster Information |
| **TC-EIG-NEG-001: Build Instance with Wrong Cluster** | ❌ Missing | Build Instance with Wrong Cluster |
| **TC-EIG-NEG-002: Build Instance with Wrong EnvGene Project** | ❌ Missing | Build Instance with Wrong EnvGene Project |
| **TC-EIG-NEG-003: Build Instance with Wrong Environment** | ❌ Missing | Build Instance with Wrong Environment |
| **TC-EIG-NEG-004: Build Instance with Wrong Template** | ❌ Missing | Build Instance with Wrong Template |
| **TC-EIG-PARAM-001: Build Instance with ENV_TEMPLATE_VERSION override** | ❌ Missing | Build Instance with ENV_TEMPLATE_VERSION override |
| **TC-EIG-PARAM-002: Build Instance with ENV_TEMPLATE_VERSION_ORIGIN override (BG origin)** | ❌ Missing | Build Instance with ENV_TEMPLATE_VERSION_ORIGIN override (BG origin) |
| **TC-EIG-PARAM-003: Build Instance with ENV_TEMPLATE_VERSION_PEER override (BG peer)** | ❌ Missing | Build Instance with ENV_TEMPLATE_VERSION_PEER override (BG peer) |
| **TC-EIG-PARAM-004: Build Instance with ENV_SPECIFIC_PARAMS applied** | ❌ Missing | Build Instance with ENV_SPECIFIC_PARAMS applied |
| **TC-EIG-PARAM-006: Build Instance with external APP_REG_DEFS_JOB (App/Reg defs from job)** | ❌ Missing | Build Instance with external APP_REG_DEFS_JOB (App/Reg defs from job) |
| **TC-EIG-PARAM-007: Build Instance with APP_DEFS_PATH (custom AppDefs path)** | ❌ Missing | Build Instance with APP_DEFS_PATH (custom AppDefs path) |
| **TC-EIG-PARAM-008: Build Instance with REG_DEFS_PATH (custom RegDefs path)** | ❌ Missing | Build Instance with REG_DEFS_PATH (custom RegDefs path) |
| **TC-EIG-PARAM-009: Build Instance with NS_BUILD_FILTER (build filtered namespaces only)** | ❌ Missing | Build Instance with NS_BUILD_FILTER (build filtered namespaces only) |
| **TC-EIG-PARAM-010: Build Instance with DEPLOYMENT_SESSION_ID propagation** | ❌ Missing | Build Instance with DEPLOYMENT_SESSION_ID propagation |
| **TC-EIG-PARAM-011: Build Instance with CRED_ROTATION_PAYLOAD (trigger cred rotation)** | ❌ Missing | Build Instance with CRED_ROTATION_PAYLOAD (trigger cred rotation) |
| **TC-EIG-PARAM-012: Build Instance with CRED_ROTATION_FORCE (force cred rotation)** | ❌ Missing | Build Instance with CRED_ROTATION_FORCE (force cred rotation) |
| **TC-EIG-PARAM-013: Build Instance with GH_ADDITIONAL_PARAMS (GitHub additional params)** | ❌ Missing | Build Instance with GH_ADDITIONAL_PARAMS (GitHub additional params) |
| **TC-EIG-PARAM-014: Build Instance with BG_MANAGE enabled (bg_manage job runs)** | ❌ Missing | Build Instance with BG_MANAGE enabled (bg_manage job runs) |
| **TC-EIG-PARAM-015: Build Instance with BG_STATE provided (state validation/update)** | ❌ Missing | Build Instance with BG_STATE provided (state validation/update) |
| **TC-EIG-POS-001: Build Instance (Basic Build)** | ❌ Missing | Build Instance (Basic Build) |
| **TC-EIG-POS-003: Build Instance with Effective Set and Single SD Data** | ❌ Missing | Build Instance with Effective Set and Single SD Data |
| **TC-EIG-POS-005: Build Instance with CMDB Import** | ❌ Missing | Build Instance with CMDB Import |
| **TC-EIG-POS-006: Build Instance with Inventory Init and Multiple SD Versions** | ❌ Missing | Build Instance with Inventory Init and Multiple SD Versions |
| **TC-EIG-POS-007: Build Instance with Inventory Init and Single SD Data** | ❌ Missing | Build Instance with Inventory Init and Single SD Data |
| **TC-EIG-POS-008: Build Instance with SD Delta and SD Merge** | ❌ Missing | Build Instance with SD Delta and SD Merge |
| **TC-XXX-XXX: [Brief Test Case Name]** | ?? [New/Active/Archived] | [Brief Test Case Name] |
| **UC-01: Environment inherits cluster Cloud Passport automatically** | ✅ Active (BDD) | Environment inherits cluster Cloud Passport automatically |
| **UC-02: Environment uses explicitly named Cloud Passport** | ✅ Active (BDD) | Environment uses explicitly named Cloud Passport |
| **UC-03: Environment builds without Cloud Passport** | ✅ Active (BDD) | Environment builds without Cloud Passport |
| **UC-04: Environment uses passport from custom location** | ✅ Active (BDD) | Environment uses passport from custom location |
| **UC-05: Parameter source traceability** | ✅ Active (BDD) | Parameter source traceability |
| **UC-06: Business environments auto-associate the business passport in a mixed cluster** | ✅ Active (BDD) | Business environments auto-associate the business passport in a mixed cluster |
| **UC-07: Infra environments use an explicit infra passport in a mixed cluster** | ✅ Active (BDD) | Infra environments use an explicit infra passport in a mixed cluster |
| **UC-08: Mixed cluster failure when infra relies on auto-association** | ✅ Active (BDD) | Mixed cluster failure when infra relies on auto-association |
| **UC-09: Backward compatibility for existing business environments** | ✅ Active (BDD) | Backward compatibility for existing business environments |
| **UC-AD-ENV-10: Download Template from Artifactory with GAV notation and Anonymous Access** | ✅ Active (BDD) | Download Template from Artifactory with GAV notation and Anonymous Access |
| **UC-AD-ENV-11: Download Template from Nexus with GAV notation** | ✅ Active (BDD) | Download Template from Nexus with GAV notation |
| **UC-AD-ENV-12: Download Template from Nexus with GAV notation and Anonymous Access** | ✅ Active (BDD) | Download Template from Nexus with GAV notation and Anonymous Access |
| **UC-AD-ENV-13: Download Template with app ver notation from Artifactory (ArtDef v1)** | ✅ Active (BDD) | Download Template with app ver notation from Artifactory (ArtDef v1) |
| **UC-AD-ENV-14: Download Template with app ver notation from Artifactory and Anonymous Access (ArtDef v1)** | ✅ Active (BDD) | Download Template with app ver notation from Artifactory and Anonymous Access (ArtDef v1) |
| **UC-AD-ENV-15: Download Template with app ver notation from Nexus (ArtDef v1)** | ✅ Active (BDD) | Download Template with app ver notation from Nexus (ArtDef v1) |
| **UC-AD-ENV-16: Download Template with app ver notation from Nexus and Anonymous Access (ArtDef v1)** | ✅ Active (BDD) | Download Template with app ver notation from Nexus and Anonymous Access (ArtDef v1) |
| **UC-AD-ENV-17: Download Template from Artifactory with app ver notation (ArtDef v2)** | ✅ Active (BDD) | Download Template from Artifactory with app ver notation (ArtDef v2) |
| **UC-AD-ENV-18: Download Template from Artifactory with app ver notation and Anonymous Access (ArtDef v2)** | ✅ Active (BDD) | Download Template from Artifactory with app ver notation and Anonymous Access (ArtDef v2) |
| **UC-AD-ENV-19: Download Template from Nexus with app ver notation (ArtDef v2)** | ✅ Active (BDD) | Download Template from Nexus with app ver notation (ArtDef v2) |
| **UC-AD-ENV-20: Download Template from Nexus with app ver notation and Anonymous Access (ArtDef v2)** | ✅ Active (BDD) | Download Template from Nexus with app ver notation and Anonymous Access (ArtDef v2) |
| **UC-AD-ENV-21: Download Template from AWS CodeArtifact with app ver notation (ArtDef v2)** | ✅ Active (BDD) | Download Template from AWS CodeArtifact with app ver notation (ArtDef v2) |
| **UC-AD-ENV-22: Download Template from GCP Artifact Registry with app ver notation (ArtDef v2)** | ✅ Active (BDD) | Download Template from GCP Artifact Registry with app ver notation (ArtDef v2) |
| **UC-AD-ENV-23: Download SNAPSHOT Template Version** | ✅ Active (BDD) | Download SNAPSHOT Template Version |
| **UC-AD-ENV-24: Download Specific Template Version** | ✅ Active (BDD) | Download Specific Template Version |
| **UC-AD-ENV-9: Download Template from Artifactory with GAV notation** | ✅ Active (BDD) | Download Template from Artifactory with GAV notation |
| **UC-AD-ERR-1: Handle missing application definition** | ✅ Active (BDD) | Handle missing application definition |
| **UC-AD-ERR-2: Handle missing registry definition** | ✅ Active (BDD) | Handle missing registry definition |
| **UC-AD-ERR-3: Handle authentication failure** | ✅ Active (BDD) | Handle authentication failure |
| **UC-AD-ERR-4: Handle Missing Artifact Definition** | ✅ Active (BDD) | Handle Missing Artifact Definition |
| **UC-AD-SD-1: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v1)** | ✅ Active (BDD) | Download SD from Artifactory with User/Password (AppDef v1 + RegDef v1) |
| **UC-AD-SD-10: Download SD from GCP Artifact Registry with Service Account (AppDef v1 + RegDef v2)** | ✅ Active (BDD) | Download SD from GCP Artifact Registry with Service Account (AppDef v1 + RegDef v2) |
| **UC-AD-SD-11: Download Specific Version SD** | ✅ Active (BDD) | Download Specific Version SD |
| **UC-AD-SD-2: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v1)** | ✅ Active (BDD) | Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v1) |
| **UC-AD-SD-3: Download SD from Nexus with User/Password (AppDef v1 + RegDef v1)** | ✅ Active (BDD) | Download SD from Nexus with User/Password (AppDef v1 + RegDef v1) |
| **UC-AD-SD-4: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v1)** | ✅ Active (BDD) | Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v1) |
| **UC-AD-SD-5: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v2)** | ✅ Active (BDD) | Download SD from Artifactory with User/Password (AppDef v1 + RegDef v2) |
| **UC-AD-SD-6: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v2)** | ✅ Active (BDD) | Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v2) |
| **UC-AD-SD-7: Download SD from Nexus with User/Password (AppDef v1 + RegDef v2)** | ✅ Active (BDD) | Download SD from Nexus with User/Password (AppDef v1 + RegDef v2) |
| **UC-AD-SD-8: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v2)** | ✅ Active (BDD) | Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v2) |
| **UC-AD-SD-9: Download SD from AWS CodeArtifact with Secret (AppDef v1 + RegDef v2)** | ✅ Active (BDD) | Download SD from AWS CodeArtifact with Secret (AppDef v1 + RegDef v2) |
| **UC-AEN-END-1: Environment with no explicit environmentName defined** | ✅ Active (BDD) | Environment with no explicit environmentName defined |
| **UC-AEN-END-2: Environment with explicit environmentName defined** | ✅ Active (BDD) | Environment with explicit environmentName defined |
| **UC-AEN-END-3: Environment with explicit environmentName different from folder name** | ✅ Active (BDD) | Environment with explicit environmentName different from folder name |
| **UC-AEN-END-4: Invalid folder structure for environment** | ✅ Active (BDD) | Invalid folder structure for environment |
| **UC-AEN-END-5: Template rendering with derived environment name** | ✅ Active (BDD) | Template rendering with derived environment name |
| **UC-ARD-CI-1: Export definitions to CMDB** | ✅ Active (BDD) | Export definitions to CMDB |
| **UC-ARD-PM-1: Root mode behavior (auto-migration from legacy layout)** | ✅ Active (BDD) | Root mode behavior (auto-migration from legacy layout) |
| **UC-ARD-PM-2: Dual mode behavior (upgrade with no cleanup)** | ✅ Active (BDD) | Dual mode behavior (upgrade with no cleanup) |
| **UC-ARD-TR-1: Basic AppDef/RegDef template rendering** | ✅ Active (BDD) | Basic AppDef/RegDef template rendering |
| **UC-ARD-TR-2: Basic AppDef/RegDef template delete** | ✅ Active (BDD) | Basic AppDef/RegDef template delete |
| **UC-ARD-TR-3: Shared template repository, off-site instance rendering** | ✅ Active (BDD) | Shared template repository, off-site instance rendering |
| **UC-ARD-TR-4: Shared template repository, on-site instance rendering** | ✅ Active (BDD) | Shared template repository, on-site instance rendering |
| **UC-ARD-UD-1: Replace template-rendered definition with user-provided file** | ✅ Active (BDD) | Replace template-rendered definition with user-provided file |
| **UC-ARD-UD-2: Delete user-provided file** | ✅ Active (BDD) | Delete user-provided file |
| **UC-ARD-UD-3: Add new definition via user-provided file with no matching template** | ✅ Active (BDD) | Add new definition via user-provided file with no matching template |
| **UC-BG-1: Init Domain** | ✅ Active (BDD) | Init Domain |
| **UC-BG-2: Warmup** | ✅ Active (BDD) | Warmup |
| **UC-BG-3: Promote** | ✅ Active (BDD) | Promote |
| **UC-BG-4: Commit** | ✅ Active (BDD) | Commit |
| **UC-BG-5: Rollback** | ✅ Active (BDD) | Rollback |
| **UC-BG-6: Reverse Warmup** | ✅ Active (BDD) | Reverse Warmup |
| **UC-BG-7: Reverse Promote** | ✅ Active (BDD) | Reverse Promote |
| **UC-BG-8: Reverse Commit** | ✅ Active (BDD) | Reverse Commit |
| **UC-BG-9: Reverse Rollback** | ✅ Active (BDD) | Reverse Rollback |
| **UC-CC-CR-1: DeployParameters to E2EParameters Reference Error** | ✅ Active (BDD) | DeployParameters to E2EParameters Reference Error |
| **UC-CC-CR-2: DeployParameters to TechnicalConfigurationParameters Reference Error** | ✅ Active (BDD) | DeployParameters to TechnicalConfigurationParameters Reference Error |
| **UC-CC-CR-3: E2EParameters to DeployParameters Reference Error** | ✅ Active (BDD) | E2EParameters to DeployParameters Reference Error |
| **UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters Reference Error** | ✅ Active (BDD) | E2EParameters to TechnicalConfigurationParameters Reference Error |
| **UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters Reference Error** | ✅ Active (BDD) | TechnicalConfigurationParameters to DeployParameters Reference Error |
| **UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error** | ✅ Active (BDD) | TechnicalConfigurationParameters to E2EParameters Reference Error |
| **UC-CC-DP-1: Exact Match** | ✅ Active (BDD) | Exact Match |
| **UC-CC-DP-2: BG Domain Match** | ✅ Active (BDD) | BG Domain Match |
| **UC-CC-DP-3: No Exact Match Found** | ✅ Active (BDD) | No Exact Match Found |
| **UC-CC-DP-4: No BG Domain Match Found** | ✅ Active (BDD) | No BG Domain Match Found |
| **UC-CC-HR-1: Namespace to Cloud Reference** | ✅ Active (BDD) | Namespace to Cloud Reference |
| **UC-CC-HR-2: Namespace to Tenant Reference** | ✅ Active (BDD) | Namespace to Tenant Reference |
| **UC-CC-HR-3: Cloud to Tenant Reference** | ✅ Active (BDD) | Cloud to Tenant Reference |
| **UC-CC-HR-4: Cloud to Namespace Reference Error** | ✅ Active (BDD) | Cloud to Namespace Reference Error |
| **UC-CC-HR-5: Tenant to Cloud Reference Error** | ✅ Active (BDD) | Tenant to Cloud Reference Error |
| **UC-CC-HR-6: Tenant to Namespace Reference Error** | ✅ Active (BDD) | Tenant to Namespace Reference Error |
| **UC-CC-MR-1: Simple Type Resolution** | ✅ Active (BDD) | Simple Type Resolution |
| **UC-CC-MR-2: Complex Structure Resolution** | ✅ Active (BDD) | Complex Structure Resolution |
| **UC-CR-ENC-1: Update Credentials with Plaintext Payload when Encryption Is Enabled** | ✅ Active (BDD) | Update Credentials with Plaintext Payload when Encryption Is Enabled |
| **UC-CR-ENC-2: Update Credentials with Encrypted Payload when Encryption Is Enabled** | ✅ Active (BDD) | Update Credentials with Encrypted Payload when Encryption Is Enabled |
| **UC-CR-ENC-3: Update Credentials with Plaintext Payload when Encryption Is Disabled** | ✅ Active (BDD) | Update Credentials with Plaintext Payload when Encryption Is Disabled |
| **UC-CR-ENC-4: Update Credentials with Encrypted Payload when Encryption Is Disabled** | ✅ Active (BDD) | Update Credentials with Encrypted Payload when Encryption Is Disabled |
| **UC-CR-LCH-1: Reject Affected Credential Update** | ✅ Active (BDD) | Reject Affected Credential Update |
| **UC-CR-LCH-2: Update Affected Credentials in Force Mode** | ✅ Active (BDD) | Update Affected Credentials in Force Mode |
| **UC-CR-TPR-1: Update Credential from Pipeline Parameter** | ✅ Active (BDD) | Update Credential from Pipeline Parameter |
| **UC-CR-TPR-2: Update Credential from Deployment Parameter** | ✅ Active (BDD) | Update Credential from Deployment Parameter |
| **UC-CR-TPR-3: Update Credentials from Multiple rotation_items** | ✅ Active (BDD) | Update Credentials from Multiple rotation_items |
| **UC-CR-VAL-1: Fail When No Affected Parameters Found** | ✅ Active (BDD) | Fail When No Affected Parameters Found |
| **UC-EIG-ES-1: Generate Effective Set without SD_DATA or SD_VERSION** | ✅ Active (BDD) | Generate Effective Set without SD_DATA or SD_VERSION |
| **UC-EIG-ES-2: Generate Effective Set with SD_DATA or SD_VERSION** | ✅ Active (BDD) | Generate Effective Set with SD_DATA or SD_VERSION |
| **UC-EIG-ES-3: Apply CUSTOM_PARAMS when GENERATE_EFFECTIVE_SET is true** | ✅ Active (BDD) | Apply CUSTOM_PARAMS when GENERATE_EFFECTIVE_SET is true |
| **UC-EIG-ES-4: Ignore `CUSTOM_PARAMS` when `GENERATE_EFFECTIVE_SET` is false** | ✅ Active (BDD) | Ignore `CUSTOM_PARAMS` when `GENERATE_EFFECTIVE_SET` is false |
| **UC-EIG-ME-1: Parallel Environment Instance Generation for Multiple Environments** | ✅ Active (BDD) | Parallel Environment Instance Generation for Multiple Environments |
| **UC-EIG-NF-1: Namespace NOT in BG Domain with deploy_postfix** | ✅ Active (BDD) | Namespace NOT in BG Domain with deploy_postfix |
| **UC-EIG-NF-2: Namespace NOT in BG Domain without deploy_postfix** | ✅ Active (BDD) | Namespace NOT in BG Domain without deploy_postfix |
| **UC-EIG-NF-3: Controller Namespace in BG Domain with deploy_postfix** | ✅ Active (BDD) | Controller Namespace in BG Domain with deploy_postfix |
| **UC-EIG-NF-4: Controller Namespace in BG Domain without deploy_postfix** | ✅ Active (BDD) | Controller Namespace in BG Domain without deploy_postfix |
| **UC-EIG-NF-5: Origin Namespace in BG Domain with deploy_postfix** | ✅ Active (BDD) | Origin Namespace in BG Domain with deploy_postfix |
| **UC-EIG-NF-6: Origin Namespace in BG Domain without deploy_postfix** | ✅ Active (BDD) | Origin Namespace in BG Domain without deploy_postfix |
| **UC-EIG-NF-7: Peer Namespace in BG Domain with deploy_postfix** | ✅ Active (BDD) | Peer Namespace in BG Domain with deploy_postfix |
| **UC-EIG-NF-8: Peer Namespace in BG Domain without deploy_postfix** | ✅ Active (BDD) | Peer Namespace in BG Domain without deploy_postfix |
| **UC-EIG-TA-1: Environment Instance Generation with `artifact` only** | ✅ Active (BDD) | Environment Instance Generation with `artifact` only |
| **UC-EIG-TA-2: Environment Instance Generation with `artifact` and `bgNsArtifacts` and BG Domain** | ✅ Active (BDD) | Environment Instance Generation with `artifact` and `bgNsArtifacts` and BG Domain |
| **UC-EIG-TA-3: Environment Instance Generation with `artifact` and `bgNsArtifacts` and without BG Domain** | ✅ Active (BDD) | Environment Instance Generation with `artifact` and `bgNsArtifacts` and without BG Domain |
| **UC-EINV-AT-ALL-1: Rollback all Inventory changes if any operation fails** | ✅ Active (BDD) | Rollback all Inventory changes if any operation fails |
| **UC-EINV-BASIC-1: Generate minimal Environment Inventory (init)** | ❌ Missing | Generate minimal Environment Inventory (init) |
| **UC-EINV-CR-1: Create credentials file** | ✅ Active (BDD) | Create credentials file |
| **UC-EINV-CR-2: Update credentials file** | ✅ Active (BDD) | Update credentials file |
| **UC-EINV-CR-3: Delete credentials file** | ✅ Active (BDD) | Delete credentials file |
| **UC-EINV-ED-1: Create env_definition.yml** | ✅ Active (BDD) | Create env_definition.yml |
| **UC-EINV-ED-2: Update env_definition.yml** | ✅ Active (BDD) | Update env_definition.yml |
| **UC-EINV-ED-3: Delete env_definition.yml** | ✅ Active (BDD) | Delete env_definition.yml |
| **UC-EINV-ESP-1: Update inventory with ENV_SPECIFIC_PARAMS (merge/override)** | ❌ Missing | Update inventory with ENV_SPECIFIC_PARAMS (merge/override) |
| **UC-EINV-ESP-2: Override inventory.clusterUrl via clusterParams.clusterEndpoint** | ❌ Missing | Override inventory.clusterUrl via clusterParams.clusterEndpoint |
| **UC-EINV-ESP-3: Add cluster token credential via clusterParams.clusterToken (no override if exists)** | ❌ Missing | Add cluster token credential via clusterParams.clusterToken (no override if exists) |
| **UC-EINV-ESP-4: Merge additionalTemplateVariables into envTemplate.additionalTemplateVariables** | ❌ Missing | Merge additionalTemplateVariables into envTemplate.additionalTemplateVariables |
| **UC-EINV-ESP-5: Override inventory.cloudName via ENV_SPECIFIC_PARAMS.cloudName** | ❌ Missing | Override inventory.cloudName via ENV_SPECIFIC_PARAMS.cloudName |
| **UC-EINV-ESP-6: Override inventory.tenantName via ENV_SPECIFIC_PARAMS.tenantName** | ❌ Missing | Override inventory.tenantName via ENV_SPECIFIC_PARAMS.tenantName |
| **UC-EINV-ESP-7: Override inventory.deployer via ENV_SPECIFIC_PARAMS.deployer** | ❌ Missing | Override inventory.deployer via ENV_SPECIFIC_PARAMS.deployer |
| **UC-EINV-ESP-8: Merge envSpecificParamsets into envTemplate.envSpecificParamsets** | ❌ Missing | Merge envSpecificParamsets into envTemplate.envSpecificParamsets |
| **UC-EINV-INIT-1: Init inventory when env_definition.yml does not exist** | ❌ Missing | Init inventory when env_definition.yml does not exist |
| **UC-EINV-INIT-2: Init inventory when env_definition.yml already exists (behavior/validation)** | ❌ Missing | Init inventory when env_definition.yml already exists (behavior/validation) |
| **UC-EINV-PS-1: Create paramset file** | ✅ Active (BDD) | Create paramset file |
| **UC-EINV-PS-2: Update paramset file** | ✅ Active (BDD) | Update paramset file |
| **UC-EINV-PS-3: Delete paramset file** | ✅ Active (BDD) | Delete paramset file |
| **UC-EINV-RP-1: Create resource profile file** | ✅ Active (BDD) | Create resource profile file |
| **UC-EINV-RP-2: Update resource profile file** | ✅ Active (BDD) | Update resource profile file |
| **UC-EINV-RP-3: Delete resource profile file** | ✅ Active (BDD) | Delete resource profile file |
| **UC-EINV-STV-1: Create specific template version file** | ✅ Active (BDD) | Create specific template version file |
| **UC-EINV-STV-2: Update specific template version file** | ✅ Active (BDD) | Update specific template version file |
| **UC-EINV-STV-3: Delete specific template version file** | ✅ Active (BDD) | Delete specific template version file |
| **UC-EINV-TV-1: Create template variable file** | ✅ Active (BDD) | Create template variable file |
| **UC-ES-CLN-1: cleanup/parameters.yaml from deployParameters** | ❌ Missing | cleanup/parameters.yaml from deployParameters |
| **UC-ES-CLN-2: cleanup/credentials.yaml includes sensitive and custom runtime** | ❌ Missing | cleanup/credentials.yaml includes sensitive and custom runtime |
| **UC-ES-CLN-3: cleanup mapping.yaml key set** | ❌ Missing | cleanup mapping.yaml key set |
| **UC-ES-DEP-14: deploy_param image keys** | ✅ Active (BDD) | deploy_param image keys |
| **UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline** | ✅ Active (BDD) | DEPLOYMENT_SESSION_ID from pipeline |
| **UC-ES-DEP-16: Predefined identity, MANAGED_BY default, and mandatory deployment keys** | ✅ Active (BDD) | Predefined identity, MANAGED_BY default, and mandatory deployment keys |
| **UC-ES-DEP-20: Service-name collision routing** | ✅ Active (BDD) | Service-name collision routing |
| **UC-ES-DEP-22: DBaaS and Vault disabled omit optional deployment URLs** | ✅ Active (BDD) | DBaaS and Vault disabled omit optional deployment URLs |
| **UC-ES-DEP-23: Public and private gateway URLs from deployment context** | ✅ Active (BDD) | Public and private gateway URLs from deployment context |
| **UC-ES-DEP-A11: Per-service layout and resource profiles** | ✅ Active (BDD) | Per-service layout and resource profiles |
| **UC-ES-DEP-A14: deployment mapping.yaml** | ✅ Active (BDD) | deployment mapping.yaml |
| **UC-ES-DEP-A15: Blue-green predefined deployment parameters** | ✅ Active (BDD) | Blue-green predefined deployment parameters |
| **UC-ES-DEP-A16: App chart validation fails when enabled** | ✅ Active (BDD) | App chart validation fails when enabled |
| **UC-ES-DEP-A18: App chart validation skipped when disabled** | ✅ Active (BDD) | App chart validation skipped when disabled |
| **UC-ES-DEP-A6: Deployment credentials, feature secrets, and SSL bundle macros** | ✅ Active (BDD) | Deployment credentials, feature secrets, and SSL bundle macros |
| **UC-ES-DEP-A8: custom-params.yaml from CUSTOM_PARAMS** | ✅ Active (BDD) | custom-params.yaml from CUSTOM_PARAMS |
| **UC-ES-DEP-A9: deploy-descriptor.yaml structure and configuration artifacts** | ✅ Active (BDD) | deploy-descriptor.yaml structure and configuration artifacts |
| **UC-ES-NOSBOM-1: Only Pipeline and Topology contexts generated** | ❌ Missing | Only Pipeline and Topology contexts generated |
| **UC-ES-PIPE-1: pipeline parameters and credentials from Cloud e2eParameters** | ❌ Missing | pipeline parameters and credentials from Cloud e2eParameters |
| **UC-ES-PIPE-4: Consumer copies root keys from pipeline context** | ❌ Missing | Consumer copies root keys from pipeline context |
| **UC-ES-PIPE-5: Consumer schema default only** | ❌ Missing | Consumer schema default only |
| **UC-ES-PIPE-6: Consumer omits optional schema-only key** | ❌ Missing | Consumer omits optional schema-only key |
| **UC-ES-PIPE-7: Consumer mandatory key without value fails** | ❌ Missing | Consumer mandatory key without value fails |
| **UC-ES-RUN-1: runtime/parameters.yaml from technicalConfigurationParameters** | ❌ Missing | runtime/parameters.yaml from technicalConfigurationParameters |
| **UC-ES-RUN-2: runtime/credentials.yaml includes sensitive and custom runtime** | ❌ Missing | runtime/credentials.yaml includes sensitive and custom runtime |
| **UC-ES-RUN-3: runtime mapping.yaml key set** | ❌ Missing | runtime mapping.yaml key set |
| **UC-ES-TOP-1: Cluster endpoint from Cloud Passport** | ❌ Missing | Cluster endpoint from Cloud Passport |
| **UC-ES-TOP-2: Cluster endpoint from Environment Inventory clusterUrl** | ❌ Missing | Cluster endpoint from Environment Inventory clusterUrl |
| **UC-ES-TOP-3: Environment Inventory clusterUrl parsing variants** | ❌ Missing | Environment Inventory clusterUrl parsing variants |
| **UC-ES-TOP-6: Cloud Passport overrides Environment Inventory clusterUrl** | ❌ Missing | Cloud Passport overrides Environment Inventory clusterUrl |
| **UC-ES-TR-1: Traceability comments enabled - source annotation per parameter** | ❌ Missing | Traceability comments enabled - source annotation per parameter |
| **UC-ES-TR-2: Traceability comments disabled by default** | ❌ Missing | Traceability comments disabled by default |
| **UC-ES-TR-3: Multiline value gets comment on preceding line** | ❌ Missing | Multiline value gets comment on preceding line |
| **UC-ES-TR-4: deploy-descriptor.yaml uses file-level header comment** | ❌ Missing | deploy-descriptor.yaml uses file-level header comment |
| **UC-ES-TR-5: mapping.yaml and external-credentials.yaml have no comments** | ❌ Missing | mapping.yaml and external-credentials.yaml have no comments |
| **UC-GSF-INST-1: Initialize Instance Repository via GSF** | ✅ Active (BDD) | Initialize Instance Repository via GSF |
| **UC-GSF-INST-2: Upgrade Instance Repository via GSF** | ✅ Active (BDD) | Upgrade Instance Repository via GSF |
| **UC-GSF-INST-3: Downgrade Instance Repository via GSF** | ✅ Active (BDD) | Downgrade Instance Repository via GSF |
| **UC-GSF-TMP-1: Initialize Template Repository via GSF** | ✅ Active (BDD) | Initialize Template Repository via GSF |
| **UC-GSF-TMP-2: Upgrade Template Repository via GSF** | ✅ Active (BDD) | Upgrade Template Repository via GSF |
| **UC-GSF-TMP-2.1: Upgrade legacy Template Repository (versions before 2.85.0)** | ✅ Active (BDD) | Upgrade legacy Template Repository (versions before 2.85.0) |
| **UC-GSF-TMP-3: Downgrade Template Repository via GSF** | ✅ Active (BDD) | Downgrade Template Repository via GSF |
| **UC-NVV-1: Unresolved parameter blocks pipeline** | ✅ Active (BDD) | Unresolved parameter blocks pipeline |
| **UC-NVV-2: Unresolved credential blocks pipeline** | ✅ Active (BDD) | Unresolved credential blocks pipeline |
| **UC-NVV-3: All values resolved** | ✅ Active (BDD) | All values resolved |
| **UC-NVV-4: Ignore null values when validation is disabled** | ✅ Active (BDD) | Ignore null values when validation is disabled |
| **UC-SBOM-1: SBOM retention disabled - no cleanup** | ✅ Active (BDD) | SBOM retention disabled - no cleanup |
| **UC-SBOM-2: All applications within per-application limit - no files deleted** | ✅ Active (BDD) | All applications within per-application limit - no files deleted |
| **UC-SBOM-3: Per-application retention keeps 10 most recent versions** | ✅ Active (BDD) | Per-application retention keeps 10 most recent versions |
| **UC-SBOM-4: Per-application retention with custom version count** | ✅ Active (BDD) | Per-application retention with custom version count |
| **UC-SBOM-5: Total /sboms/ size exceeds 1200 MB - keeps newest per application** | ✅ Active (BDD) | Total /sboms/ size exceeds 1200 MB - keeps newest per application |
| **UC-SBOM-MIG-1: First run after upgrade** | ✅ Active (BDD) | First run after upgrade |
| **UC-SC-NEX-1: Download template artifact from Nexus with custom CA certificate** | ✅ Active (BDD) | Download template artifact from Nexus with custom CA certificate |
| **UC-SD-1: Single SD_VERSION with `replace` mode** | ✅ Active (BDD) | Single SD_VERSION with `replace` mode |
| **UC-SD-10: Single SD_VERSION with SD_DELTA=false** | ✅ Active (BDD) | Single SD_VERSION with SD_DELTA=false |
| **UC-SD-11: Single SD_DATA with `replace` mode** | ✅ Active (BDD) | Single SD_DATA with `replace` mode |
| **UC-SD-12: Single SD_DATA with `extended-merge` mode** | ✅ Active (BDD) | Single SD_DATA with `extended-merge` mode |
| **UC-SD-12a: Single SD_DATA with `extended-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Single SD_DATA with `extended-merge` mode when Full SD does not exist |
| **UC-SD-13: Single SD_DATA with `basic-merge` mode** | ✅ Active (BDD) | Single SD_DATA with `basic-merge` mode |
| **UC-SD-13a: Single SD_DATA with `basic-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Single SD_DATA with `basic-merge` mode when Full SD does not exist |
| **UC-SD-14: Single SD_DATA with `basic-exclusion-merge` mode** | ✅ Active (BDD) | Single SD_DATA with `basic-exclusion-merge` mode |
| **UC-SD-14a: Single SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Single SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist |
| **UC-SD-15: Multiple SD_DATA with `basic-merge` mode** | ✅ Active (BDD) | Multiple SD_DATA with `basic-merge` mode |
| **UC-SD-15a: Multiple SD_DATA with `basic-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Multiple SD_DATA with `basic-merge` mode when Full SD does not exist |
| **UC-SD-16: Multiple SD_DATA with `basic-exclusion-merge` mode** | ✅ Active (BDD) | Multiple SD_DATA with `basic-exclusion-merge` mode |
| **UC-SD-16a: Multiple SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Multiple SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist |
| **UC-SD-17: Multiple SD_DATA with `extended-merge` mode** | ✅ Active (BDD) | Multiple SD_DATA with `extended-merge` mode |
| **UC-SD-17a: Multiple SD_DATA with `extended-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Multiple SD_DATA with `extended-merge` mode when Full SD does not exist |
| **UC-SD-18: Multiple SD_DATA with `replace` mode** | ✅ Active (BDD) | Multiple SD_DATA with `replace` mode |
| **UC-SD-19: Single SD_DATA with SD_DELTA=true** | ✅ Active (BDD) | Single SD_DATA with SD_DELTA=true |
| **UC-SD-19a: Single SD_DATA with SD_DELTA=true when Full SD does not exist** | ✅ Active (BDD) | Single SD_DATA with SD_DELTA=true when Full SD does not exist |
| **UC-SD-2: Single SD_VERSION with `extended-merge` mode** | ✅ Active (BDD) | Single SD_VERSION with `extended-merge` mode |
| **UC-SD-20: Single SD_DATA with SD_DELTA=false** | ✅ Active (BDD) | Single SD_DATA with SD_DELTA=false |
| **UC-SD-2a: Single SD_VERSION with `extended-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Single SD_VERSION with `extended-merge` mode when Full SD does not exist |
| **UC-SD-3: Single SD_VERSION with `basic-merge` mode** | ✅ Active (BDD) | Single SD_VERSION with `basic-merge` mode |
| **UC-SD-3a: Single SD_VERSION with `basic-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Single SD_VERSION with `basic-merge` mode when Full SD does not exist |
| **UC-SD-4: Single SD_VERSION with `basic-exclusion-merge` mode** | ✅ Active (BDD) | Single SD_VERSION with `basic-exclusion-merge` mode |
| **UC-SD-4a: Single SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Single SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist |
| **UC-SD-5: Multiple SD_VERSION with `basic-merge` mode** | ✅ Active (BDD) | Multiple SD_VERSION with `basic-merge` mode |
| **UC-SD-5a: Multiple SD_VERSION with `basic-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Multiple SD_VERSION with `basic-merge` mode when Full SD does not exist |
| **UC-SD-6: Multiple SD_VERSION with `basic-exclusion-merge` mode** | ✅ Active (BDD) | Multiple SD_VERSION with `basic-exclusion-merge` mode |
| **UC-SD-6a: Multiple SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist** | ✅ Active (BDD) | Multiple SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist |
| **UC-SD-7: Single SD_VERSION with asic-exclusion-merge mode when Full SD does not exist** | ✅ Active (BDD) | Single SD_VERSION with asic-exclusion-merge mode when Full SD does not exist |
| **UC-SD-7a: Multiple SD_VERSION with extended-merge mode when Full SD does not exist** | ❌ Missing | Multiple SD_VERSION with extended-merge mode when Full SD does not exist |
| **UC-SD-8: Multiple SD_VERSION with `replace` mode** | ✅ Active (BDD) | Multiple SD_VERSION with `replace` mode |
| **UC-SD-9: Single SD_VERSION with SD_DELTA=true** | ✅ Active (BDD) | Single SD_VERSION with SD_DELTA=true |
| **UC-SD-9a: Single SD_VERSION with SD_DELTA=true when Full SD does not exist** | ✅ Active (BDD) | Single SD_VERSION with SD_DELTA=true when Full SD does not exist |
| **UC-TI-CS-1: Use explicit composite_structure from child Template Descriptor** | ✅ Active (BDD) | Use explicit composite_structure from child Template Descriptor |
| **UC-TI-OV-1: Override parent parameters for Cloud template** | ✅ Active (BDD) | Override parent parameters for Cloud template |
| **UC-TI-OV-2: Override parent parameters for Namespace template** | ✅ Active (BDD) | Override parent parameters for Namespace template |
| **UC-TI-PT-1: Build child template using a single parent template** | ✅ Active (BDD) | Build child template using a single parent template |
| **UC-TI-PT-2: Build child template composed from multiple parent templates** | ✅ Active (BDD) | Build child template composed from multiple parent templates |
