# Analysis Results: Missing Implementations and Documentation

## Summary
- **Total spreadsheet tests:** 276
- **Total implemented scenarios:** 144
- **Total documented UCs/TCs:** 175
- **Missing Implementation:** 150
- **Missing Documentation:** 108

## Missing Implementations
| Feature | Sub-feature | Test Name |
|---------|-------------|-----------|
| Effective set Generation | Effective set | UC-EIG-ES-1: Generate Effective Set without SD_DATA or SD_VERSION |
| Effective set Generation | Effective set | UC-EIG-ES-3: Apply CUSTOM_PARAMS when GENERATE_EFFECTIVE_SET is true |
| Effective set Generation | deployPostfix Matching Logic | deployPostfix Matching Logic |
| Effective set Generation | Parameter Type Preservation in Macro Resolution | Parameter Type Preservation in Macro Resolution |
| Effective set Generation | Cross-Level Parameter References | Cross-Level Parameter References |
| Effective set Generation | Cross-Context Parameter References | Cross-Context Parameter References |
| Effective set Generation | SBOM Processing | UC-ES-DEP-14: deploy_param image keys |
| Effective set Generation | SBOM Processing | UC-ES-DEP-A16: App chart validation fails when enabled |
| Effective set Generation | SBOM Processing | UC-ES-DEP-A18: App chart validation skipped when disabled |
| Effective set Generation | Deployment Context | UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline |
| Effective set Generation | Deployment Context | UC-ES-DEP-16: Predefined identity, MANAGED_BY default, and mandatory deployment keys |
| Effective set Generation | Deployment Context | UC-ES-DEP-22: DBaaS and Vault disabled omit optional deployment URLs |
| Effective set Generation | Deployment Context | UC-ES-DEP-23: Public and private gateway URLs from deployment context |
| Effective set Generation | Deployment Context | UC-ES-DEP-A15: Blue-green predefined deployment parameters |
| Effective set Generation | Deployment Context | UC-ES-DEP-A8: custom-params.yaml from CUSTOM_PARAMS |
| Effective set Generation | Sensitive Parameters Processing | UC-ES-DEP-A6: Deployment credentials, feature secrets, and SSL bundle macros |
| Effective set Generation | Collision Routing | UC-ES-DEP-20: Service-name collision routing |
| Effective set Generation | Deploy Descriptor | UC-ES-DEP-A9: deploy-descriptor.yaml structure and configuration artifacts |
| Effective set Generation | Deploy Descriptor | UC-ES-DEP-A11: Per-service layout and resource profiles |
| Effective set Generation | Cross-Context Effective Set Consistency | Cross-Context Effective Set Consistency |
| Effective set Generation | Cross-Context Effective Set Consistency | UC-ES-DEP-A14: deployment mapping.yaml |
| Effective set Generation | Cross-Context Effective Set Consistency | UC-ES-RUN-3: runtime mapping.yaml key set |
| Effective set Generation | Cross-Context Effective Set Consistency | UC-ES-CLN-3: cleanup mapping.yaml key set |
| Effective set Generation | Pipeline Context | UC-ES-PIPE-1: pipeline parameters and credentials from Cloud e2eParameters |
| Effective set Generation | Pipeline Context | UC-ES-PIPE-4: Consumer copies root keys from pipeline context |
| Effective set Generation | Pipeline Context | UC-ES-PIPE-5: Consumer schema default only |
| Effective set Generation | Pipeline Context | UC-ES-PIPE-6: Consumer omits optional schema-only key |
| Effective set Generation | Runtime Context | UC-ES-PIPE-7: Consumer mandatory key without value fails |
| Effective set Generation | Runtime Context | UC-ES-RUN-1: runtime/parameters.yaml from technicalConfigurationParameters |
| Effective set Generation | Runtime Context | UC-ES-RUN-2: runtime/credentials.yaml includes sensitive and custom runtime |
| Effective set Generation | Cleanup Context | UC-ES-CLN-1: cleanup/parameters.yaml from deployParameters |
| Effective set Generation | Cleanup Context | UC-ES-CLN-2: cleanup/credentials.yaml includes sensitive and custom runtime |
| Effective set Generation | Cleanup Context | UC-ES-NOSBOM-1: Only Pipeline and Topology contexts generated |
| Effective set Generation | Traceability Comments | UC-ES-TR-1: Traceability comments enabled - source annotation per parameter |
| Effective set Generation | Traceability Comments | UC-ES-TR-2: Traceability comments disabled by default |
| Effective set Generation | Traceability Comments | UC-ES-TR-3: Multiline value gets comment on preceding line |
| Effective set Generation | Traceability Comments | UC-ES-TR-4: deploy-descriptor.yaml uses file-level header comment |
| Effective set Generation | Traceability Comments | UC-ES-TR-5: mapping.yaml and external-credentials.yaml have no comments |
| Effective set Generation | Topology Context | UC-ES-TOP-1: Cluster endpoint from Cloud Passport |
| Effective set Generation | Topology Context | UC-ES-TOP-2: Cluster endpoint from Environment Inventory clusterUrl |
| Effective set Generation | Topology Context | UC-ES-TOP-3: Environment Inventory clusterUrl parsing variants |
| Effective set Generation | Topology Context | UC-ES-TOP-6: Cloud Passport overrides Environment Inventory clusterUrl |
| Environment Instance Generation | Basic | TC-EIG-NEG-001: Build Instance with Wrong Cluster |
| Environment Instance Generation | Basic | TC-EIG-NEG-002: Build Instance with Wrong EnvGene Project |
| Environment Instance Generation | Basic | TC-EIG-NEG-003: Build Instance with Wrong Environment |
| Environment Instance Generation | Template | TC-EIG-NEG-004: Build Instance with Wrong Template |
| Environment Instance Generation | Basic | TC-EIG-POS-001: Build Instance (Basic Build) |
| Environment Instance Generation | cloud-passport | TC-EIG-POS-001: Build Instance (Basic Build) |
| Environment Instance Generation | effective-set with SD | TC-EIG-POS-003: Build Instance with Effective Set and Single SD Data |
| Environment Instance Generation | CMBD | TC-EIG-POS-005: Build Instance with CMDB Import |
| Environment Instance Generation | Inventory init with multiple SD | TC-EIG-POS-006: Build Instance with Inventory Init and Multiple SD Versions |
| Environment Instance Generation | Inventory init with single SD | TC-EIG-POS-007: Build Instance with Inventory Init and Single SD Data |
| Environment Instance Generation | SD | TC-EIG-POS-008: Build Instance with SD Delta and SD Merge |
| Environment Instance Generation |  | TC-EIG-PARAM-001: Build Instance with ENV_TEMPLATE_VERSION override |
| Environment Instance Generation |  | TC-EIG-PARAM-002: Build Instance with ENV_TEMPLATE_VERSION_ORIGIN override (BG origin) |
| Environment Instance Generation |  | TC-EIG-PARAM-003: Build Instance with ENV_TEMPLATE_VERSION_PEER override (BG peer) |
| Environment Instance Generation |  | TC-EIG-PARAM-004: Build Instance with ENV_SPECIFIC_PARAMS applied |
| Environment Instance Generation |  | TC-EIG-PARAM-006: Build Instance with external APP_REG_DEFS_JOB (App/Reg defs from job) |
| Environment Inventory Generation |  | environment specific parameters (Enviroment generation) |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-ED-2: Replace env_definition.yml (create_or_replace, file exists) |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-PS-2: Replace paramset file (create_or_replace, file exists) |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-PS-3: Delete paramSet file |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-CR-2: Replace credentials file (create_or_replace, file exists) |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-CR-3: Delete credentials file |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-RP-1: Create resource profile override file (create_or_replace, file does not exist) |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-RP-2: Replace resource profile override file (create_or_replace, file exists) |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-RP-3: Delete resource profile override file |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-STV-1: Create Shared Template Variable file (create_or_replace, file does not exist) |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-STV-2: Replace Shared Template Variable file (create_or_replace, file exists) |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-STV-3: Delete Shared Template Variable file |
| Environment Inventory Generation | ENV_CONTENT | UC-EINV-TV-1: Apply ENV_TEMPLATE_VERSION (PERSISTENT vs TEMPORARY) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-BASIC-1: Generate minimal Environment Inventory (init) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-INIT-1: Init inventory when env_definition.yml does not exist |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-INIT-2: Init inventory when env_definition.yml already exists (behavior/validation) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-1: Update inventory with ENV_SPECIFIC_PARAMS (merge/override) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-2: Override inventory.clusterUrl via clusterParams.clusterEndpoint |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-3: Add cluster token credential via clusterParams.clusterToken (no override if exists) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-4: Merge additionalTemplateVariables into envTemplate.additionalTemplateVariables |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-6: Override inventory.tenantName via ENV_SPECIFIC_PARAMS.tenantName |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-7: Override inventory.deployer via ENV_SPECIFIC_PARAMS.deployer |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-8: Merge envSpecificParamsets into envTemplate.envSpecificParamsets |
| GSF maintenance | Template Repository Maintenance via GSF | UC-GSF-TMP-1: Initialize Template Repository via GSF |
| GSF maintenance | Template Repository Maintenance via GSF | UC-GSF-TMP-2: Upgrade Template Repository via GSF |
| GSF maintenance | Instance Repository Maintenance via GSF | UC-GSF-INST-1: Initialize Instance Repository via GSF |
| GSF maintenance | Instance Repository Maintenance via GSF | UC-GSF-INST-2: Upgrade Instance Repository via GSF |
| artifact-downloading | SD/DD Artifact Download | UC-AD-SD-7: Download SD from Nexus with User/Password (AppDef v1 + RegDef v2) |
| Environment Instance Generation |  | TC-EIG-PARAM-010: Build Instance with DEPLOYMENT_SESSION_ID propagation |
| Environment Instance Generation | PR processing | Resource Profiles |
| Solution Descriptor Processing | Multiple SD_VERSION | UC-SD-7: Multiple SD_VERSION with extended-merge mode |
| Solution Descriptor Processing | Multiple SD_VERSION | UC-SD-7a: Multiple SD_VERSION with extended-merge mode when Full SD does not exist |
| Application and Registry Definition | User-provided definitions | UC-ARD-UD-1: Replace template-rendered definition with user-provided file |
| Application and Registry Definition | User-provided definitions | UC-ARD-UD-2: Delete user-provided file |
| Application and Registry Definition | User-provided definitions | UC-ARD-UD-3: Add new definition via user-provided file with no matching template |
| Application and Registry Definition | Placement modes | UC-ARD-PM-1: Root mode behavior (auto-migration from legacy layout) |
| Application and Registry Definition | Placement modes | UC-ARD-PM-2: Dual mode behavior (upgrade with no cleanup) |
| Application and Registry Definition | CMDB integration | UC-ARD-CI-1: Export definitions to CMDB |
| Automatic Environment Name Derivation |  | TC-003-001: Environment with no explicit environmentName defined |
| Automatic Environment Name Derivation |  | TC-003-002: Environment with explicit environmentName defined |
| Automatic Environment Name Derivation |  | TC-003-003: Environment with explicit environmentName different from folder name |
| Automatic Environment Name Derivation |  | TC-003-004: Invalid folder structure for environment |
| Automatic Environment Name Derivation |  | TC-003-005: Template rendering with derived environment name |
| Credential Encryption |  | TC-004-001: Encryption Enabled with Supported Fields |
| Credential Encryption |  | TC-004-002: Encryption Skipped When Disabled |
| Credential Encryption |  | TC-004-003: Secret Key Mandatory for Fernet |
| Credential Encryption |  | TC-004-004: Successful Encryption Using Fernet |
| Credential Encryption |  | TC-004-005: Skip Encryption if File Already Encrypted Using Fernet |
| Credential Encryption |  | TC-004-006: age_key Mandatory for SOPS |
| Credential Encryption |  | TC-004-007: Successful Encryption Using SOPS |
| Credential Encryption |  | TC-004-008: Skip Encryption if File Already Encrypted Using SOPS |
| Environment Instance Generation |  | TC-EIG-PARAM-011: Build Instance with CRED_ROTATION_PAYLOAD (trigger cred rotation) |
| Environment Instance Generation |  | TC-EIG-PARAM-012: Build Instance with CRED_ROTATION_FORCE (force cred rotation) |
| Environment Instance Generation |  | TC-EIG-PARAM-014: Build Instance with BG_MANAGE enabled (bg_manage job runs) |
| Environment Instance Generation |  | TC-EIG-PARAM-015: Build Instance with BG_STATE provided (state validation/update) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-5: Override inventory.cloudName via ENV_SPECIFIC_PARAMS.cloudName |
| GSF maintenance | Template Repository Maintenance via GSF | UC-GSF-TMP-3: Downgrade Template Repository via GSF |
| GSF maintenance | Instance Repository Maintenance via GSF | UC-GSF-INST-3: Downgrade Instance Repository via GSF |
| Template Override | Basic | TC-003-001: Using templates_dir |
| Template Override | Basic | TC-003-002: Using current_env.name |
| Template Override | Basic | TC-003-003: Using current_env.tenant |
| Template Override | Cloud | TC-003-004: Using current_env.cloud. inventory.cloudName set in Environment Inventory |
| Template Override | Cloud | TC-003-005: Using current_env.cloud. inventory.cloudName NOT set in Environment Inventory |
| Template Override | Cloud | TC-003-006: Using current_env.cloudNameWithCluster. inventory.cloudName set in Environment Inventory |
| Template Override | Cloud | TC-003-007: Using current_env.cloudNameWithCluster. inventory.cloudPassport set in Environment Inventory |
| Template Override | Cloud | TC-003-008: Using current_env.cloudNameWithCluster. inventory.cloudName and inventory.cloudPassport NOT set in Environment Inventory |
| Template Override | CMDB | TC-003-009: Using current_env.cmdb_name. inventory.deployer set in Environment Inventory |
| Template Override | CMDB | TC-003-010: Using current_env.cmdb_name. inventory.deployer NOT set in Environment Inventory |
| Template Override | CMDB | TC-003-011: Using current_env.cmdb_url. inventory.deployer set in Environment Inventory |
| Template Override | CMDB | TC-003-012: Using current_env.cmdb_url. inventory.deployer NOT set in Environment Inventory |
| Template Override | Inventory | TC-003-013: Using current_env.description. inventory.description set in Environment Inventory |
| Template Override | Inventory | TC-003-014: Using current_env.description. inventory.description NOT set in Environment Inventory |
| Template Override | Inventory | TC-003-015: Using current_env.owners. inventory.owners set in Environment Inventory |
| Template Override | Inventory | TC-003-016: Using current_env.owners. inventory.owners NOT set in Environment Inventory |
| Template Override |  | TC-003-017: Using current_env.env_template |
| Template Override | Additional Template Variables | TC-003-018: Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables set in Environment Inventory |
| Template Override | Additional Template Variables | TC-003-019: Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables NOT set in Environment Inventory |
| Template Override | Cloud | TC-003-020: Using current_env.cloud_passport. inventory.cloudPassport set in Environment Inventory |
| Template Override | Cloud | TC-003-021: Using current_env.cloud_passport. inventory.cloudPassport NOT set in Environment Inventory |
| Template Override | Solution structure | TC-003-022: Using current_env.solution_structure. SD exist in Instance repository |
| Template Override | Solution structure | TC-003-023: Using current_env.solution_structure. SD NOT in Instance repository |
| Template Override | Template override | TC-002-001: Template override on Cloud and Namespace level. Override includes paramsets with comments |
| Environment Instance Generation |  | TC-EIG-PARAM-007: Build Instance with APP_DEFS_PATH (custom AppDefs path) |
| Environment Instance Generation |  | TC-EIG-PARAM-008: Build Instance with REG_DEFS_PATH (custom RegDefs path) |
| Environment Instance Generation |  | TC-EIG-PARAM-009: Build Instance with NS_BUILD_FILTER (build filtered namespaces only) |
| Environment Instance Generation |  | TC-EIG-PARAM-013: Build Instance with GH_ADDITIONAL_PARAMS (GitHub additional params) |
| GSF maintenance | Template Repository Maintenance via GSF | UC-GSF-TMP-2.1: Upgrade legacy Template Repository (versions before 2.85.0) |
| SBOM Storage Migration |  | UC-SBOM-MIG-1: First run after upgrade |
| envgeneNullValue validation |  | UC-NVV-1: Unresolved parameter blocks pipeline |
| envgeneNullValue validation |  | UC-NVV-2: Unresolved credential blocks pipeline |
| envgeneNullValue validation |  | UC-NVV-4: Multiple unresolved values reported together |
| customer E2E Test Scenarios |  | customer E2E Test Scenarios |

## Missing Documentation
| Feature | Sub-feature | Test Name |
|---------|-------------|-----------|
| Effective set Generation | SBOM Processing | UC-ES-DEP-14: deploy_param image keys |
| Effective set Generation | SBOM Processing | UC-ES-DEP-A16: App chart validation fails when enabled |
| Effective set Generation | SBOM Processing | UC-ES-DEP-A18: App chart validation skipped when disabled |
| Effective set Generation | Deployment Context | UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline |
| Effective set Generation | Deployment Context | UC-ES-DEP-16: Predefined identity, MANAGED_BY default, and mandatory deployment keys |
| Effective set Generation | Deployment Context | UC-ES-DEP-22: DBaaS and Vault disabled omit optional deployment URLs |
| Effective set Generation | Deployment Context | UC-ES-DEP-23: Public and private gateway URLs from deployment context |
| Effective set Generation | Deployment Context | UC-ES-DEP-A15: Blue-green predefined deployment parameters |
| Effective set Generation | Deployment Context | UC-ES-DEP-A8: custom-params.yaml from CUSTOM_PARAMS |
| Effective set Generation | Sensitive Parameters Processing | UC-ES-DEP-A6: Deployment credentials, feature secrets, and SSL bundle macros |
| Effective set Generation | Collision Routing | UC-ES-DEP-20: Service-name collision routing |
| Effective set Generation | Deploy Descriptor | UC-ES-DEP-A9: deploy-descriptor.yaml structure and configuration artifacts |
| Effective set Generation | Deploy Descriptor | UC-ES-DEP-A11: Per-service layout and resource profiles |
| Effective set Generation | Cross-Context Effective Set Consistency | UC-ES-DEP-A14: deployment mapping.yaml |
| Effective set Generation | Cross-Context Effective Set Consistency | UC-ES-RUN-3: runtime mapping.yaml key set |
| Effective set Generation | Cross-Context Effective Set Consistency | UC-ES-CLN-3: cleanup mapping.yaml key set |
| Effective set Generation | Pipeline Context | UC-ES-PIPE-1: pipeline parameters and credentials from Cloud e2eParameters |
| Effective set Generation | Pipeline Context | UC-ES-PIPE-4: Consumer copies root keys from pipeline context |
| Effective set Generation | Pipeline Context | UC-ES-PIPE-5: Consumer schema default only |
| Effective set Generation | Pipeline Context | UC-ES-PIPE-6: Consumer omits optional schema-only key |
| Effective set Generation | Runtime Context | UC-ES-PIPE-7: Consumer mandatory key without value fails |
| Effective set Generation | Runtime Context | UC-ES-RUN-1: runtime/parameters.yaml from technicalConfigurationParameters |
| Effective set Generation | Runtime Context | UC-ES-RUN-2: runtime/credentials.yaml includes sensitive and custom runtime |
| Effective set Generation | Cleanup Context | UC-ES-CLN-1: cleanup/parameters.yaml from deployParameters |
| Effective set Generation | Cleanup Context | UC-ES-CLN-2: cleanup/credentials.yaml includes sensitive and custom runtime |
| Effective set Generation | Cleanup Context | UC-ES-NOSBOM-1: Only Pipeline and Topology contexts generated |
| Effective set Generation | Traceability Comments | UC-ES-TR-1: Traceability comments enabled - source annotation per parameter |
| Effective set Generation | Traceability Comments | UC-ES-TR-2: Traceability comments disabled by default |
| Effective set Generation | Traceability Comments | UC-ES-TR-3: Multiline value gets comment on preceding line |
| Effective set Generation | Traceability Comments | UC-ES-TR-4: deploy-descriptor.yaml uses file-level header comment |
| Effective set Generation | Traceability Comments | UC-ES-TR-5: mapping.yaml and external-credentials.yaml have no comments |
| Effective set Generation | Topology Context | UC-ES-TOP-1: Cluster endpoint from Cloud Passport |
| Effective set Generation | Topology Context | UC-ES-TOP-2: Cluster endpoint from Environment Inventory clusterUrl |
| Effective set Generation | Topology Context | UC-ES-TOP-3: Environment Inventory clusterUrl parsing variants |
| Effective set Generation | Topology Context | UC-ES-TOP-6: Cloud Passport overrides Environment Inventory clusterUrl |
| Environment Instance Generation | Basic | TC-EIG-NEG-001: Build Instance with Wrong Cluster |
| Environment Instance Generation | Basic | TC-EIG-NEG-002: Build Instance with Wrong EnvGene Project |
| Environment Instance Generation | Basic | TC-EIG-NEG-003: Build Instance with Wrong Environment |
| Environment Instance Generation | Template | TC-EIG-NEG-004: Build Instance with Wrong Template |
| Environment Instance Generation | Basic | TC-EIG-POS-001: Build Instance (Basic Build) |
| Environment Instance Generation | cloud-passport | TC-EIG-POS-001: Build Instance (Basic Build) |
| Environment Instance Generation | effective-set with SD | TC-EIG-POS-003: Build Instance with Effective Set and Single SD Data |
| Environment Instance Generation | CMBD | TC-EIG-POS-005: Build Instance with CMDB Import |
| Environment Instance Generation | Inventory init with multiple SD | TC-EIG-POS-006: Build Instance with Inventory Init and Multiple SD Versions |
| Environment Instance Generation | Inventory init with single SD | TC-EIG-POS-007: Build Instance with Inventory Init and Single SD Data |
| Environment Instance Generation | SD | TC-EIG-POS-008: Build Instance with SD Delta and SD Merge |
| Environment Instance Generation |  | TC-EIG-PARAM-001: Build Instance with ENV_TEMPLATE_VERSION override |
| Environment Instance Generation |  | TC-EIG-PARAM-002: Build Instance with ENV_TEMPLATE_VERSION_ORIGIN override (BG origin) |
| Environment Instance Generation |  | TC-EIG-PARAM-003: Build Instance with ENV_TEMPLATE_VERSION_PEER override (BG peer) |
| Environment Instance Generation |  | TC-EIG-PARAM-004: Build Instance with ENV_SPECIFIC_PARAMS applied |
| Environment Instance Generation |  | TC-EIG-PARAM-006: Build Instance with external APP_REG_DEFS_JOB (App/Reg defs from job) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-BASIC-1: Generate minimal Environment Inventory (init) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-INIT-1: Init inventory when env_definition.yml does not exist |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-INIT-2: Init inventory when env_definition.yml already exists (behavior/validation) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-1: Update inventory with ENV_SPECIFIC_PARAMS (merge/override) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-2: Override inventory.clusterUrl via clusterParams.clusterEndpoint |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-3: Add cluster token credential via clusterParams.clusterToken (no override if exists) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-4: Merge additionalTemplateVariables into envTemplate.additionalTemplateVariables |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-6: Override inventory.tenantName via ENV_SPECIFIC_PARAMS.tenantName |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-7: Override inventory.deployer via ENV_SPECIFIC_PARAMS.deployer |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-8: Merge envSpecificParamsets into envTemplate.envSpecificParamsets |
| Environment Instance Generation |  | TC-EIG-PARAM-010: Build Instance with DEPLOYMENT_SESSION_ID propagation |
| Automatic Environment Name Derivation |  | TC-003-001: Environment with no explicit environmentName defined |
| Automatic Environment Name Derivation |  | TC-003-002: Environment with explicit environmentName defined |
| Automatic Environment Name Derivation |  | TC-003-003: Environment with explicit environmentName different from folder name |
| Automatic Environment Name Derivation |  | TC-003-004: Invalid folder structure for environment |
| Automatic Environment Name Derivation |  | TC-003-005: Template rendering with derived environment name |
| Credential Encryption |  | TC-004-001: Encryption Enabled with Supported Fields |
| Credential Encryption |  | TC-004-002: Encryption Skipped When Disabled |
| Credential Encryption |  | TC-004-003: Secret Key Mandatory for Fernet |
| Credential Encryption |  | TC-004-004: Successful Encryption Using Fernet |
| Credential Encryption |  | TC-004-005: Skip Encryption if File Already Encrypted Using Fernet |
| Credential Encryption |  | TC-004-006: age_key Mandatory for SOPS |
| Credential Encryption |  | TC-004-007: Successful Encryption Using SOPS |
| Credential Encryption |  | TC-004-008: Skip Encryption if File Already Encrypted Using SOPS |
| Environment Instance Generation |  | TC-EIG-PARAM-011: Build Instance with CRED_ROTATION_PAYLOAD (trigger cred rotation) |
| Environment Instance Generation |  | TC-EIG-PARAM-012: Build Instance with CRED_ROTATION_FORCE (force cred rotation) |
| Environment Instance Generation |  | TC-EIG-PARAM-014: Build Instance with BG_MANAGE enabled (bg_manage job runs) |
| Environment Instance Generation |  | TC-EIG-PARAM-015: Build Instance with BG_STATE provided (state validation/update) |
| Environment Inventory Generation | environment specific parameters (Enviroment generation) | UC-EINV-ESP-5: Override inventory.cloudName via ENV_SPECIFIC_PARAMS.cloudName |
| Template Override | Basic | TC-003-001: Using templates_dir |
| Template Override | Basic | TC-003-002: Using current_env.name |
| Template Override | Basic | TC-003-003: Using current_env.tenant |
| Template Override | Cloud | TC-003-004: Using current_env.cloud. inventory.cloudName set in Environment Inventory |
| Template Override | Cloud | TC-003-005: Using current_env.cloud. inventory.cloudName NOT set in Environment Inventory |
| Template Override | Cloud | TC-003-006: Using current_env.cloudNameWithCluster. inventory.cloudName set in Environment Inventory |
| Template Override | Cloud | TC-003-007: Using current_env.cloudNameWithCluster. inventory.cloudPassport set in Environment Inventory |
| Template Override | Cloud | TC-003-008: Using current_env.cloudNameWithCluster. inventory.cloudName and inventory.cloudPassport NOT set in Environment Inventory |
| Template Override | CMDB | TC-003-009: Using current_env.cmdb_name. inventory.deployer set in Environment Inventory |
| Template Override | CMDB | TC-003-010: Using current_env.cmdb_name. inventory.deployer NOT set in Environment Inventory |
| Template Override | CMDB | TC-003-011: Using current_env.cmdb_url. inventory.deployer set in Environment Inventory |
| Template Override | CMDB | TC-003-012: Using current_env.cmdb_url. inventory.deployer NOT set in Environment Inventory |
| Template Override | Inventory | TC-003-013: Using current_env.description. inventory.description set in Environment Inventory |
| Template Override | Inventory | TC-003-014: Using current_env.description. inventory.description NOT set in Environment Inventory |
| Template Override | Inventory | TC-003-015: Using current_env.owners. inventory.owners set in Environment Inventory |
| Template Override | Inventory | TC-003-016: Using current_env.owners. inventory.owners NOT set in Environment Inventory |
| Template Override |  | TC-003-017: Using current_env.env_template |
| Template Override | Additional Template Variables | TC-003-018: Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables set in Environment Inventory |
| Template Override | Additional Template Variables | TC-003-019: Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables NOT set in Environment Inventory |
| Template Override | Cloud | TC-003-020: Using current_env.cloud_passport. inventory.cloudPassport set in Environment Inventory |
| Template Override | Cloud | TC-003-021: Using current_env.cloud_passport. inventory.cloudPassport NOT set in Environment Inventory |
| Template Override | Solution structure | TC-003-022: Using current_env.solution_structure. SD exist in Instance repository |
| Template Override | Solution structure | TC-003-023: Using current_env.solution_structure. SD NOT in Instance repository |
| Template Override | Template override | TC-002-001: Template override on Cloud and Namespace level. Override includes paramsets with comments |
| Environment Instance Generation |  | TC-EIG-PARAM-007: Build Instance with APP_DEFS_PATH (custom AppDefs path) |
| Environment Instance Generation |  | TC-EIG-PARAM-008: Build Instance with REG_DEFS_PATH (custom RegDefs path) |
| Environment Instance Generation |  | TC-EIG-PARAM-009: Build Instance with NS_BUILD_FILTER (build filtered namespaces only) |
| Environment Instance Generation |  | TC-EIG-PARAM-013: Build Instance with GH_ADDITIONAL_PARAMS (GitHub additional params) |
