# Report on Implemented Tests

This document lists the integration test cases that are implemented, active, and successfully executed as part of the Qubership EnvGene pipeline testing.

| Test Case | Status | Description |
| :--- | :--- | :--- |
| **UC-BG-1** | ? Active | Init Domain |
| **UC-BG-2** | ? Active | Warmup |
| **UC-BG-3** | ? Active | Promote |
| **UC-BG-4** | ? Active | Commit |
| **UC-BG-5** | ? Active | Rollback |
| **UC-BG-6** | ? Active | Reverse Warmup |
| **UC-BG-7** | ? Active | Reverse Promote |
| **UC-BG-8** | ? Active | Reverse Commit |
| **UC-BG-9** | ? Active | Reverse Rollback |
| **UC-EINV-ED-1** | ? Active | Create env_definition.yml |
| **UC-EINV-ED-3** | ? Active | Delete env_definition.yml |
| **UC-EINV-PS-1** | ? Active | Create paramset file |
| **UC-EINV-CR-1** | ? Active | Create credentials file |
| **UC-EINV-AT-ALL-1** | ? Active | Rollback all Inventory changes if any operation fails |
| **UC-EINV-ED-2** | ? Active | Update env_definition.yml |
| **UC-EINV-PS-2** | ? Active | Update paramset file |
| **UC-EINV-PS-3** | ? Active | Delete paramset file |
| **UC-EINV-CR-2** | ? Active | Update credentials file |
| **UC-EINV-CR-3** | ? Active | Delete credentials file |
| **UC-EINV-RP-1** | ? Active | Create resource profile file |
| **UC-EINV-RP-2** | ? Active | Update resource profile file |
| **UC-EINV-RP-3** | ? Active | Delete resource profile file |
| **UC-EINV-STV-1** | ? Active | Create specific template version file |
| **UC-EINV-STV-2** | ? Active | Update specific template version file |
| **UC-EINV-STV-3** | ? Active | Delete specific template version file |
| **UC-EINV-TV-1** | ? Active | Create template variable file |
| **UC-01** | ? Active | Environment inherits cluster Cloud Passport automatically |
| **UC-02** | ? Active | Environment uses explicitly named Cloud Passport |
| **UC-03** | ? Active | Environment builds without Cloud Passport |
| **UC-04** | ? Active | Environment uses passport from custom location |
| **UC-05** | ? Active | Parameter source traceability |
| **UC-06** | ? Active | Business environments auto-associate the business passport in a mixed cluster |
| **UC-07** | ? Active | Infra environments use an explicit infra passport in a mixed cluster |
| **UC-09** | ? Active | Backward compatibility for existing business environments |
| **UC-08** | ? Active | Mixed cluster failure when infra relies on auto-association |
| **UC-ES-DEP-14** | ? Active | deploy_param image keys |
| **UC-ES-DEP-15** | ? Active | DEPLOYMENT_SESSION_ID from pipeline |
| **UC-ES-DEP-16** | ? Active | Predefined identity, MANAGED_BY default, and mandatory deployment keys |
| **UC-ES-DEP-20** | ? Active | Service-name collision routing |
| **UC-ES-DEP-22** | ? Active | DBaaS and Vault disabled omit optional deployment URLs |
| **UC-ES-DEP-23** | ? Active | Public and private gateway URLs from deployment context |
| **UC-ES-DEP-A6** | ? Active | Deployment credentials, feature secrets, and SSL bundle macros |
| **UC-ES-DEP-A8** | ? Active | custom-params.yaml from CUSTOM_PARAMS |
| **UC-ES-DEP-A9** | ? Active | deploy-descriptor.yaml structure and configuration artifacts |
| **UC-ES-DEP-A11** | ? Active | Per-service layout and resource profiles |
| **UC-ES-DEP-A14** | ? Active | deployment mapping.yaml |
| **UC-ES-DEP-A15** | ? Active | Blue-green predefined deployment parameters |
| **UC-ES-DEP-A16** | ? Active | App chart validation fails when enabled |
| **UC-ES-DEP-A18** | ? Active | App chart validation skipped when disabled |
| **TC-004-001** | ? Active | Encryption Enabled with Supported Fields |
| **TC-004-002** | ? Active | Encryption Skipped When Disabled |
| **TC-004-003** | ? Active | Secret Key Mandatory for Fernet |
| **TC-004-004** | ? Active | Successful Encryption Using Fernet |
| **TC-004-005** | ? Active | Skip Encryption if File Already Encrypted Using Fernet |
| **TC-004-006** | ? Active | age_key Mandatory for SOPS |
| **TC-004-007** | ? Active | Successful Encryption Using SOPS |
| **TC-004-008** | ? Active | Skip Encryption if File Already Encrypted Using SOPS |
| **UC-GSF-TMP-1** | ? Active | Initialize Template Repository via GSF |
| **UC-GSF-TMP-2** | ? Active | Upgrade Template Repository via GSF |
| **UC-GSF-TMP-2.1: Upgrade legacy Template Repository (versions before 2.85.0)** | ? Active |  |
| **UC-GSF-TMP-3** | ? Active | Downgrade Template Repository via GSF |
| **UC-GSF-INST-1** | ? Active | Initialize Instance Repository via GSF |
| **UC-GSF-INST-2** | ? Active | Upgrade Instance Repository via GSF |
| **UC-GSF-INST-3** | ? Active | Downgrade Instance Repository via GSF |
| **UC-SBOM-MIG-1** | ? Active | First run after upgrade |
| **UC-TI-PT-1** | ? Active | Build child template using a single parent template |
| **UC-TI-PT-2** | ? Active | Build child template composed from multiple parent templates |
| **UC-TI-CS-1** | ? Active | Use explicit composite_structure from child Template Descriptor |
| **UC-TI-OV-1** | ? Active | Override parent parameters for Cloud template |
| **UC-TI-OV-2** | ? Active | Override parent parameters for Namespace template |
| **TC-003-001** | ? Active | Using templates_dir |
| **TC-003-002** | ? Active | Using current_env.name |
| **TC-003-003** | ? Active | Using current_env.tenant |
| **TC-003-004** | ? Active | Using current_env.cloud. inventory.cloudName set in Environment Inventory |
| **TC-003-006** | ? Active | Using current_env.cloudNameWithCluster. inventory.cloudName set in Environment Inventory |
| **TC-003-007** | ? Active | Using current_env.cloudNameWithCluster. inventory.cloudPassport set in Environment Inventory |
| **TC-003-009** | ? Active | Using current_env.cmdb_name. inventory.deployer set in Environment Inventory |
| **TC-003-011** | ? Active | Using current_env.cmdb_url. inventory.deployer set in Environment Inventory |
| **TC-003-013** | ? Active | Using current_env.description. inventory.description set in Environment Inventory |
| **TC-003-015** | ? Active | Using current_env.owners. inventory.owners set in Environment Inventory |
| **TC-003-017** | ? Active | Using current_env.env_template |
| **TC-003-018** | ? Active | Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables set in Environment Inventory |
| **TC-003-020** | ? Active | Using current_env.cloud_passport. inventory.cloudPassport set in Environment Inventory |
| **TC-003-022** | ? Active | Using current_env.solution_structure. SD exist in Instance repository |
| **TC-003-005** | ? Active | Using current_env.cloud. inventory.cloudName NOT set in Environment Inventory |
| **TC-003-008** | ? Active | Using current_env.cloudNameWithCluster. inventory.cloudName and inventory.cloudPassport NOT set in Environment Inventory |
| **TC-003-010** | ? Active | Using current_env.cmdb_name. inventory.deployer NOT set in Environment Inventory |
| **TC-003-012** | ? Active | Using current_env.cmdb_url. inventory.deployer NOT set in Environment Inventory |
| **TC-003-014** | ? Active | Using current_env.description. inventory.description NOT set in Environment Inventory |
| **TC-003-016** | ? Active | Using current_env.owners. inventory.owners NOT set in Environment Inventory |
| **TC-003-019** | ? Active | Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables NOT set in Environment Inventory |
| **TC-003-021** | ? Active | Using current_env.cloud_passport. inventory.cloudPassport NOT set in Environment Inventory |
| **TC-003-023** | ? Active | Using current_env.solution_structure. SD NOT in Instance repository |
| **TC-002-001** | ? Active | Template override on Cloud and Namespace level. Override includes paramsets with comments |
| **UC-AD-ERR-1** | ? Active | Handle missing application definition |
| **UC-AD-ERR-2** | ? Active | Handle missing registry definition |
| **UC-AD-ERR-3** | ? Active | Handle authentication failure |
| **UC-AD-ERR-4** | ? Active | Handle missing artifact definition |
| **UC-AEN-END-4** | ? Active | Invalid folder structure for environment |
| **UC-NVV-1** | ? Active | Unresolved parameter blocks pipeline |
| **UC-NVV-2** | ? Active | Unresolved credential blocks pipeline |
| **UC-ARD-TR-1** | ? Active | Basic AppDef/RegDef template rendering |
| **UC-ARD-TR-2** | ? Active | Basic AppDef/RegDef template delete |
| **UC-ARD-TR-3** | ? Active | Shared template repository, off-site instance rendering |
| **UC-ARD-TR-4** | ? Active | Shared template repository, on-site instance rendering |
| **UC-ARD-UD-1** | ? Active | Replace template-rendered definition with user-provided file |
| **UC-ARD-UD-2** | ? Active | Delete user-provided file |
| **UC-ARD-UD-3** | ? Active | Add new definition via user-provided file with no matching template |
| **UC-ARD-PM-1** | ? Active | Root mode behavior (auto-migration from legacy layout) |
| **UC-ARD-PM-2** | ? Active | Dual mode behavior (upgrade with no cleanup) |
| **UC-ARD-CI-1** | ? Active | Export definitions to CMDB |
| **UC-AD-SD-1** | ? Active | Download SD from Artifactory with User/Password (AppDef v1 + RegDef v1) |
| **UC-AD-SD-2** | ? Active | Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v1) |
| **UC-AD-SD-3** | ? Active | Download SD from Nexus with User/Password (AppDef v1 + RegDef v1) |
| **UC-AD-SD-4** | ? Active | Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v1) |
| **UC-AD-SD-5** | ? Active | Download SD from Artifactory with User/Password (AppDef v1 + RegDef v2) |
| **UC-AD-SD-6** | ? Active | Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v2) |
| **UC-AD-SD-7** | ? Active | Download SD from Nexus with User/Password (AppDef v1 + RegDef v2) |
| **UC-AD-SD-8** | ? Active | Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v2) |
| **UC-AD-SD-9** | ? Active | Download SD from AWS CodeArtifact with Secret (AppDef v1 + RegDef v2) |
| **UC-AD-SD-10** | ? Active | Download SD from GCP Artifact Registry with Service Account (AppDef v1 + RegDef v2) |
| **UC-AD-SD-11** | ? Active | Download Specific Version SD |
| **UC-AD-ENV-9** | ? Active | Download Template from Artifactory with GAV notation |
| **UC-AD-ENV-10** | ? Active | Download Template from Artifactory with GAV notation and Anonymous Access |
| **UC-AD-ENV-11** | ? Active | Download Template from Nexus with GAV notation |
| **UC-SC-NEX-1** | ? Active | Download template artifact from Nexus with custom CA certificate |
| **UC-AD-ENV-12** | ? Active | Download Template from Nexus with GAV notation and Anonymous Access |
| **UC-AD-ENV-13** | ? Active | Download Template with app ver notation from Artifactory (ArtDef v1) |
| **UC-AD-ENV-14** | ? Active | Download Template with app ver notation from Artifactory and Anonymous Access (ArtDef v1) |
| **UC-AD-ENV-15** | ? Active | Download Template with app ver notation from Nexus (ArtDef v1) |
| **UC-AD-ENV-16** | ? Active | Download Template with app ver notation from Nexus and Anonymous Access (ArtDef v1) |
| **UC-AD-ENV-17** | ? Active | Download Template from Artifactory with app ver notation (ArtDef v2) |
| **UC-AD-ENV-18** | ? Active | Download Template from Artifactory with app ver notation and Anonymous Access (ArtDef v2) |
| **UC-AD-ENV-19** | ? Active | Download Template from Nexus with app ver notation (ArtDef v2) |
| **UC-AD-ENV-20** | ? Active | Download Template from Nexus with app ver notation and Anonymous Access (ArtDef v2) |
| **UC-AD-ENV-21** | ? Active | Download Template from AWS CodeArtifact with app ver notation (ArtDef v2) |
| **UC-AD-ENV-22** | ? Active | Download Template from GCP Artifact Registry with app ver notation (ArtDef v2) |
| **UC-AD-ENV-23** | ? Active | Download SNAPSHOT Template Version |
| **UC-AD-ENV-24** | ? Active | Download Specific Template Version |
| **UC-AD-ERR-4** | ? Active | Handle Missing Artifact Definition |
| **UC-AEN-END-1** | ? Active | Environment with no explicit environmentName defined |
| **UC-AEN-END-2** | ? Active | Environment with explicit environmentName defined |
| **UC-AEN-END-3** | ? Active | Environment with explicit environmentName different from folder name |
| **UC-AEN-END-5** | ? Active | Template rendering with derived environment name |
| **UC-BG-1** | ? Active | Init Domain |
| **UC-BG-2** | ? Active | Warmup |
| **UC-BG-3** | ? Active | Promote |
| **UC-BG-4** | ? Active | Commit |
| **UC-BG-5** | ? Active | Rollback |
| **UC-BG-7** | ? Active | Reverse Promote |
| **UC-BG-8** | ? Active | Reverse Commit |
| **UC-BG-9** | ? Active | Reverse Rollback |
| **UC-CC-DP-1** | ? Active | Exact Match |
| **UC-CC-DP-2** | ? Active | BG Domain Match |
| **UC-CC-DP-3** | ? Active | No Exact Match Found |
| **UC-CC-DP-4** | ? Active | No BG Domain Match Found |
| **UC-CC-MR-1** | ? Active | Simple Type Resolution |
| **UC-CC-MR-2** | ? Active | Complex Structure Resolution |
| **UC-CC-HR-1** | ? Active | Namespace to Cloud Reference |
| **UC-CC-HR-2** | ? Active | Namespace to Tenant Reference |
| **UC-CC-HR-3** | ? Active | Cloud to Tenant Reference |
| **UC-CC-HR-4** | ? Active | Cloud to Namespace Reference Error |
| **UC-CC-HR-5** | ? Active | Tenant to Cloud Reference Error |
| **UC-CC-HR-6** | ? Active | Tenant to Namespace Reference Error |
| **UC-CC-CR-1** | ? Active | DeployParameters to E2EParameters Reference Error |
| **UC-CC-CR-2** | ? Active | DeployParameters to TechnicalConfigurationParameters Reference Error |
| **UC-CC-CR-3** | ? Active | E2EParameters to DeployParameters Reference Error |
| **UC-CC-CR-4** | ? Active | E2EParameters to TechnicalConfigurationParameters Reference Error |
| **UC-CC-CR-5** | ? Active | TechnicalConfigurationParameters to DeployParameters Reference Error |
| **UC-CC-CR-6** | ? Active | TechnicalConfigurationParameters to E2EParameters Reference Error |
| **UC-CR-TPR-1** | ? Active | Update Credential from Pipeline Parameter |
| **UC-CR-TPR-2** | ? Active | Update Credential from Deployment Parameter |
| **UC-CR-TPR-3** | ? Active | Update Credentials from Multiple rotation_items |
| **UC-CR-LCH-1** | ? Active | Reject Affected Credential Update |
| **UC-CR-LCH-2** | ? Active | Update Affected Credentials in Force Mode |
| **UC-CR-VAL-1** | ? Active | Fail When No Affected Parameters Found |
| **UC-CR-ENC-1** | ? Active | Update Credentials with Plaintext Payload when Encryption Is Enabled |
| **UC-CR-ENC-2** | ? Active | Update Credentials with Encrypted Payload when Encryption Is Enabled |
| **UC-CR-ENC-3** | ? Active | Update Credentials with Plaintext Payload when Encryption Is Disabled |
| **UC-CR-ENC-4** | ? Active | Update Credentials with Encrypted Payload when Encryption Is Disabled |
| **UC-NVV-3** | ? Active | All values resolved |
| **UC-NVV-4** | ? Active | Ignore null values when validation is disabled |
| **UC-EIG-NF-1** | ? Active | Namespace NOT in BG Domain with deploy_postfix |
| **UC-EIG-NF-2** | ? Active | Namespace NOT in BG Domain without deploy_postfix |
| **UC-EIG-NF-3** | ? Active | Controller Namespace in BG Domain with deploy_postfix |
| **UC-EIG-NF-4** | ? Active | Controller Namespace in BG Domain without deploy_postfix |
| **UC-EIG-NF-5** | ? Active | Origin Namespace in BG Domain with deploy_postfix |
| **UC-EIG-NF-6** | ? Active | Origin Namespace in BG Domain without deploy_postfix |
| **UC-EIG-NF-7** | ? Active | Peer Namespace in BG Domain with deploy_postfix |
| **UC-EIG-NF-8** | ? Active | Peer Namespace in BG Domain without deploy_postfix |
| **UC-EIG-TA-1** | ? Active | Environment Instance Generation with `artifact` only |
| **UC-EIG-TA-2** | ? Active | Environment Instance Generation with `artifact` and `bgNsArtifacts` and BG Domain |
| **UC-EIG-TA-3** | ? Active | Environment Instance Generation with `artifact` and `bgNsArtifacts` and without BG Domain |
| **UC-EIG-ES-4** | ? Active | Ignore `CUSTOM_PARAMS` when `GENERATE_EFFECTIVE_SET` is false |
| **UC-EIG-ES-1** | ? Active | Generate Effective Set without SD_DATA or SD_VERSION |
| **UC-EIG-ES-2** | ? Active | Generate Effective Set with SD_DATA or SD_VERSION |
| **UC-EIG-ES-3** | ? Active | Apply CUSTOM_PARAMS when GENERATE_EFFECTIVE_SET is true |
| **UC-EIG-ME-1** | ? Active | Parallel Environment Instance Generation for Multiple Environments |
| **UC-SBOM-1** | ? Active | SBOM retention disabled - no cleanup |
| **UC-SBOM-2** | ? Active | All applications within per-application limit - no files deleted |
| **UC-SBOM-3** | ? Active | Per-application retention keeps 10 most recent versions |
| **UC-SBOM-4** | ? Active | Per-application retention with custom version count |
| **UC-SBOM-5** | ? Active | Total /sboms/ size exceeds 1200 MB - keeps newest per application |
| **UC-SD-1** | ? Active | Single SD_VERSION with `replace` mode |
| **UC-SD-2** | ? Active | Single SD_VERSION with `extended-merge` mode |
| **UC-SD-2a** | ? Active | Single SD_VERSION with `extended-merge` mode when Full SD does not exist |
| **UC-SD-3** | ? Active | Single SD_VERSION with `basic-merge` mode |
| **UC-SD-3a** | ? Active | Single SD_VERSION with `basic-merge` mode when Full SD does not exist |
| **UC-SD-4** | ? Active | Single SD_VERSION with `basic-exclusion-merge` mode |
| **UC-SD-4a** | ? Active | Single SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist |
| **UC-SD-5** | ? Active | Multiple SD_VERSION with `basic-merge` mode |
| **UC-SD-5a** | ? Active | Multiple SD_VERSION with `basic-merge` mode when Full SD does not exist |
| **UC-SD-6** | ? Active | Multiple SD_VERSION with `basic-exclusion-merge` mode |
| **UC-SD-6a** | ? Active | Multiple SD_VERSION with `basic-exclusion-merge` mode when Full SD does not exist |
| **UC-SD-8** | ? Active | Multiple SD_VERSION with `replace` mode |
| **UC-SD-9** | ? Active | Single SD_VERSION with SD_DELTA=true |
| **UC-SD-9a** | ? Active | Single SD_VERSION with SD_DELTA=true when Full SD does not exist |
| **UC-SD-10** | ? Active | Single SD_VERSION with SD_DELTA=false |
| **UC-SD-11** | ? Active | Single SD_DATA with `replace` mode |
| **UC-SD-12** | ? Active | Single SD_DATA with `extended-merge` mode |
| **UC-SD-12a** | ? Active | Single SD_DATA with `extended-merge` mode when Full SD does not exist |
| **UC-SD-13** | ? Active | Single SD_DATA with `basic-merge` mode |
| **UC-SD-13a** | ? Active | Single SD_DATA with `basic-merge` mode when Full SD does not exist |
| **UC-SD-14** | ? Active | Single SD_DATA with `basic-exclusion-merge` mode |
| **UC-SD-14a** | ? Active | Single SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist |
| **UC-SD-15** | ? Active | Multiple SD_DATA with `basic-merge` mode |
| **UC-SD-15a** | ? Active | Multiple SD_DATA with `basic-merge` mode when Full SD does not exist |
| **UC-SD-16** | ? Active | Multiple SD_DATA with `basic-exclusion-merge` mode |
| **UC-SD-16a** | ? Active | Multiple SD_DATA with `basic-exclusion-merge` mode when Full SD does not exist |
| **UC-SD-17** | ? Active | Multiple SD_DATA with `extended-merge` mode |
| **UC-SD-17a** | ? Active | Multiple SD_DATA with `extended-merge` mode when Full SD does not exist |
| **UC-SD-18** | ? Active | Multiple SD_DATA with `replace` mode |
| **UC-SD-19** | ? Active | Single SD_DATA with SD_DELTA=true |
| **UC-SD-19a** | ? Active | Single SD_DATA with SD_DELTA=true when Full SD does not exist |
| **UC-SD-20** | ? Active | Single SD_DATA with SD_DELTA=false |
| **UC-SD-7** | ? Active | Single SD_VERSION with asic-exclusion-merge mode when Full SD does not exist |

