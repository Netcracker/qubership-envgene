Title: Live Content

Description: Fetched live

Source: https://docs.google.com/spreadsheets/d/1HeWGsvGTNiIBb-qJQam82bcGEkRsJdNJgHXephqogWk/export?format=csv&gid=0

---

Feature,Sub-feature,Test Name,Type,UC status ,E2E,Comments,Priority
Effective set Generation,Effective set,UC-EIG-ES-1: Generate Effective Set without SD_DATA or SD_VERSION,,IMPLEMENTED,yes,,1
Effective set Generation,Effective set,UC-EIG-ES-2: Generate Effective Set with SD_DATA or SD_VERSION,,READY_FOR_DEV,,,1
Effective set Generation,Effective set,UC-EIG-ES-3: Apply CUSTOM_PARAMS when GENERATE_EFFECTIVE_SET is true,,IMPLEMENTED,yes,,1
Effective set Generation,Effective set,UC-EIG-ES-4: Ignore CUSTOM_PARAMS when GENERATE_EFFECTIVE_SET is false,,IMPLEMENTED,yes,,1
Effective set Generation,deployPostfix Matching Logic,deployPostfix Matching Logic,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,deployPostfix Matching Logic,UC-CC-DP-1: Exact Match,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,deployPostfix Matching Logic,UC-CC-DP-2: BG Domain Match,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,deployPostfix Matching Logic,UC-CC-DP-3: No Exact Match Found,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,deployPostfix Matching Logic,UC-CC-DP-4: No BG Domain Match Found,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Parameter Type Preservation in Macro Resolution,Parameter Type Preservation in Macro Resolution,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Parameter Type Preservation in Macro Resolution,UC-CC-MR-1: Simple Type Resolution,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Parameter Type Preservation in Macro Resolution,UC-CC-MR-2: Complex Structure Resolution,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Level Parameter References,Cross-Level Parameter References,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Level Parameter References,UC-CC-HR-1: Namespace to Cloud Reference,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Level Parameter References,UC-CC-HR-2: Namespace to Tenant Reference,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Level Parameter References,UC-CC-HR-3: Cloud to Tenant Reference,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Level Parameter References,UC-CC-HR-4: Cloud to Namespace Reference - Deploy and Technical Resolution,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Level Parameter References,UC-CC-HR-5: Tenant to Cloud Reference,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Level Parameter References,UC-CC-HR-6: Tenant to Namespace Reference,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Parameter References,Cross-Context Parameter References,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Parameter References,UC-CC-CR-3: E2EParameters to DeployParameters - Silent Drop,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Parameter References,UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters - Silent Drop,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Parameter References,UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters - Resolves Successfully,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Parameter References,UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,SBOM Processing,UC-ES-DEP-14: deploy_param image keys,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,SBOM Processing,UC-ES-DEP-A16: App chart validation fails when enabled,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,SBOM Processing,UC-ES-DEP-A18: App chart validation skipped when disabled,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Deployment Context,UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Deployment Context,"UC-ES-DEP-16: Predefined identity, MANAGED_BY default, and mandatory deployment keys",integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Deployment Context,UC-ES-DEP-22: DBaaS and Vault disabled omit optional deployment URLs,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Deployment Context,UC-ES-DEP-23: Public and private gateway URLs from deployment context,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Deployment Context,UC-ES-DEP-A15: Blue-green predefined deployment parameters,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Deployment Context,UC-ES-DEP-A8: custom-params.yaml from CUSTOM_PARAMS,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Sensitive Parameters Processing,"UC-ES-DEP-A6: Deployment credentials, feature secrets, and SSL bundle macros",integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Collision Routing,UC-ES-DEP-20: Service-name collision routing,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Deploy Descriptor,UC-ES-DEP-A9: deploy-descriptor.yaml structure and configuration artifacts,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Deploy Descriptor,UC-ES-DEP-A11: Per-service layout and resource profiles,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Effective Set Consistency,Cross-Context Effective Set Consistency,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Effective Set Consistency,UC-ES-DEP-A14: deployment mapping.yaml,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Effective Set Consistency,UC-ES-RUN-3: runtime mapping.yaml key set,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cross-Context Effective Set Consistency,UC-ES-CLN-3: cleanup mapping.yaml key set,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Pipeline Context,UC-ES-PIPE-1: pipeline parameters and credentials from Cloud e2eParameters,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Pipeline Context,UC-ES-PIPE-4: Consumer copies root keys from pipeline context,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Pipeline Context,UC-ES-PIPE-5: Consumer schema default only,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Pipeline Context,UC-ES-PIPE-6: Consumer omits optional schema-only key,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Runtime Context,UC-ES-PIPE-7: Consumer mandatory key without value fails,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Runtime Context,UC-ES-RUN-1: runtime/parameters.yaml from technicalConfigurationParameters,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Runtime Context,UC-ES-RUN-2: runtime/credentials.yaml includes sensitive and custom runtime,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cleanup Context,UC-ES-CLN-1: cleanup/parameters.yaml from deployParameters,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cleanup Context,UC-ES-CLN-2: cleanup/credentials.yaml includes sensitive and custom runtime,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Cleanup Context,UC-ES-NOSBOM-1: Only Pipeline and Topology contexts generated,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Traceability Comments,UC-ES-TR-1: Traceability comments enabled - source annotation per parameter,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Traceability Comments,UC-ES-TR-2: Traceability comments disabled by default,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Traceability Comments,UC-ES-TR-3: Multiline value gets comment on preceding line,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Traceability Comments,UC-ES-TR-4: deploy-descriptor.yaml uses file-level header comment,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Traceability Comments,UC-ES-TR-5: mapping.yaml and external-credentials.yaml have no comments,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Topology Context,UC-ES-TOP-1: Cluster endpoint from Cloud Passport,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Topology Context,UC-ES-TOP-2: Cluster endpoint from Environment Inventory clusterUrl,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Topology Context,UC-ES-TOP-3: Environment Inventory clusterUrl parsing variants,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Effective set Generation,Topology Context,UC-ES-TOP-6: Cloud Passport overrides Environment Inventory clusterUrl,integration_tests,IN_DEVELOPMENT,,Блокирует задача по CLI git compare,1
Environment Instance Generation,,,neg,TO_BE_DEFINED,,Необходимо написать Отсутсвует негативные сценарий,1
Environment Instance Generation,BD Domain,UC-EIG-NF-1: Namespace NOT in BG Domain with deploy_postfix,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-NF-2: Namespace NOT in BG Domain without deploy_postfix,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-NF-3: Controller Namespace in BG Domain with deploy_postfix,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-NF-4: Controller Namespace in BG Domain without deploy_postfix,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-NF-5: Origin Namespace in BG Domain with deploy_postfix,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-NF-6: Origin Namespace in BG Domain without deploy_postfix,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-NF-7: Peer Namespace in BG Domain with deploy_postfix,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-NF-8: Peer Namespace in BG Domain without deploy_postfix,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-TA-1: Environment Instance Generation with artifact only,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-TA-2: Environment Instance Generation with artifact and bgNsArtifacts and BG Domain,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,BD Domain,UC-EIG-TA-3: Environment Instance Generation with artifact and bgNsArtifacts and without BG Domain,pos,NEED_UPDATE,,Актуализировать старые сценарии,1
Environment Instance Generation,Basic,TC-EIG-NEG-001: Build Instance with Wrong Cluster,neg,TO_BE_DEFINED,,,1
Environment Instance Generation,Basic,TC-EIG-NEG-002: Build Instance with Wrong EnvGene Project,neg,TO_BE_DEFINED,,,1
Environment Instance Generation,Basic,TC-EIG-NEG-003: Build Instance with Wrong Environment,neg,TO_BE_DEFINED,,,1
Environment Instance Generation,Template,TC-EIG-NEG-004: Build Instance with Wrong Template,neg,TO_BE_DEFINED,,,1
Environment Instance Generation,Basic,TC-EIG-POS-001: Build Instance (Basic Build),pos,TO_BE_DEFINED,,,1
Environment Instance Generation,cloud-passport,TC-EIG-POS-001: Build Instance (Basic Build),pos,TO_BE_DEFINED,,,1
Environment Instance Generation,effective-set with SD,TC-EIG-POS-003: Build Instance with Effective Set and Single SD Data,pos,TO_BE_DEFINED,,,1
Environment Instance Generation,CMBD,TC-EIG-POS-005: Build Instance with CMDB Import,pos,TO_BE_DEFINED,,,1
Environment Instance Generation,Inventory init with multiple SD,TC-EIG-POS-006: Build Instance with Inventory Init and Multiple SD Versions,pos,TO_BE_DEFINED,,,1
Environment Instance Generation,Inventory init with single SD,TC-EIG-POS-007: Build Instance with Inventory Init and Single SD Data,pos,TO_BE_DEFINED,,,1
Environment Instance Generation,SD,TC-EIG-POS-008: Build Instance with SD Delta and SD Merge,pos,TO_BE_DEFINED,,,1
Environment Instance Generation,,TC-EIG-PARAM-001: Build Instance with ENV_TEMPLATE_VERSION override,pos,TO_BE_DEFINED,,,1
Environment Instance Generation,,TC-EIG-PARAM-002: Build Instance with ENV_TEMPLATE_VERSION_ORIGIN override (BG origin),pos,TO_BE_DEFINED,,,1
Environment Instance Generation,,TC-EIG-PARAM-003: Build Instance with ENV_TEMPLATE_VERSION_PEER override (BG peer),pos,TO_BE_DEFINED,,,1
Environment Instance Generation,,TC-EIG-PARAM-004: Build Instance with ENV_SPECIFIC_PARAMS applied,pos,TO_BE_DEFINED,,,1
Environment Instance Generation,,TC-EIG-PARAM-006: Build Instance with external APP_REG_DEFS_JOB (App/Reg defs from job),pos,TO_BE_DEFINED,,,1
Environment Inventory Generation,,environment specific parameters (Enviroment generation),,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-ED-1: Create env_definition.yml (create_or_replace, file does not exist)",pos,IMPLEMENTED,yes,,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-ED-2: Replace env_definition.yml (create_or_replace, file exists)",pos,IMPLEMENTED,,Алексей,1
Environment Inventory Generation,ENV_CONTENT,UC-EINV-ED-3: Delete env_definition.yml,pos,IMPLEMENTED,,Алексей,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-PS-1: Create paramset file (create_or_replace, file does not exist)",pos,IMPLEMENTED,,Алексей,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-PS-2: Replace paramset file (create_or_replace, file exists)",pos,IMPLEMENTED,,Алексей,1
Environment Inventory Generation,ENV_CONTENT,UC-EINV-PS-3: Delete paramSet file,,IMPLEMENTED,yes,Алексей,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-CR-1: Create credentials file (create_or_replace, file does not exist)",pos,IMPLEMENTED,,Алексей,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-CR-2: Replace credentials file (create_or_replace, file exists)",pos,IMPLEMENTED,,Алексей,1
Environment Inventory Generation,ENV_CONTENT,UC-EINV-CR-3: Delete credentials file,pos,IMPLEMENTED,,Алексей,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-RP-1: Create resource profile override file (create_or_replace, file does not exist)",pos,READY_FOR_DEV,,QA,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-RP-2: Replace resource profile override file (create_or_replace, file exists)",pos,READY_FOR_DEV,,QA,1
Environment Inventory Generation,ENV_CONTENT,UC-EINV-RP-3: Delete resource profile override file,pos,READY_FOR_DEV,,QA,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-STV-1: Create Shared Template Variable file (create_or_replace, file does not exist)",pos,READY_FOR_DEV,,QA,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-STV-2: Replace Shared Template Variable file (create_or_replace, file exists)",pos,READY_FOR_DEV,,QA,1
Environment Inventory Generation,ENV_CONTENT,UC-EINV-STV-3: Delete Shared Template Variable file,pos,READY_FOR_DEV,,QA,1
Environment Inventory Generation,ENV_CONTENT,"UC-EINV-AT-ALL-1: Rollback all Inventory changes if any operation fails (negative, atomic processing)",pos,READY_FOR_DEV,,QA,1
Environment Inventory Generation,ENV_CONTENT,UC-EINV-TV-1: Apply ENV_TEMPLATE_VERSION (PERSISTENT vs TEMPORARY),,READY_FOR_DEV,,QA,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-BASIC-1: Generate minimal Environment Inventory (init),,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-INIT-1: Init inventory when env_definition.yml does not exist,,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-INIT-2: Init inventory when env_definition.yml already exists (behavior/validation),,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-ESP-1: Update inventory with ENV_SPECIFIC_PARAMS (merge/override),,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-ESP-2: Override inventory.clusterUrl via clusterParams.clusterEndpoint,,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-ESP-3: Add cluster token credential via clusterParams.clusterToken (no override if exists),,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-ESP-4: Merge additionalTemplateVariables into envTemplate.additionalTemplateVariables,,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-ESP-6: Override inventory.tenantName via ENV_SPECIFIC_PARAMS.tenantName,,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-ESP-7: Override inventory.deployer via ENV_SPECIFIC_PARAMS.deployer,,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-ESP-8: Merge envSpecificParamsets into envTemplate.envSpecificParamsets,,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-PS-1: Create paramset files from ENV_SPECIFIC_PARAMS.paramsets (override if exists),,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-CR-1: Add/override credentials from ENV_SPECIFIC_PARAMS.credentials and link via sharedMasterCredentialFiles,,TO_BE_DEFINED,,Необходимо написать,1
Environment Inventory Generation,,,neg,TO_BE_DEFINED,,Необходимо написать Отсутсвует негативные сценарий,1
GSF maintenance,Template Repository Maintenance via GSF,UC-GSF-TMP-1: Initialize Template Repository via GSF,,IMPLEMENTED,yes,,1
GSF maintenance,Template Repository Maintenance via GSF,UC-GSF-TMP-2: Upgrade Template Repository via GSF,,NEED_UPDATE,,,1
GSF maintenance,Instance Repository Maintenance via GSF,UC-GSF-INST-1: Initialize Instance Repository via GSF,,IMPLEMENTED,yes,,1
GSF maintenance,Instance Repository Maintenance via GSF,UC-GSF-INST-2: Upgrade Instance Repository via GSF,,NEED_UPDATE,,,1
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-1: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v1),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-2: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v1),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-3: Download SD from Nexus with User/Password (AppDef v1 + RegDef v1),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-4: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v1),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-5: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-6: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-7: Download SD from Nexus with User/Password (AppDef v1 + RegDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-8: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-9: Download SD from AWS CodeArtifact with Secret (AppDef v1 + RegDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-10: Download SD from GCP Artifact Registry with Service Account (AppDef v1 + RegDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,SD/DD Artifact Download,UC-AD-SD-11: Download Specific Version SD,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-9: Download Template from Artifactory with GAV notation,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-10: Download Template from Artifactory with GAV notation and Anonymous Access,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-11: Download Template from Nexus with GAV notation,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-12: Download Template from Nexus with GAV notation and Anonymous Access,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-13: Download Template with app ver notation from Artifactory (ArtDef v1),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-14: Download Template with app ver notation from Artifactory and Anonymous Access (ArtDef v1),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-15: Download Template with app ver notation from Nexus (ArtDef v1),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-16: Download Template with app ver notation from Nexus and Anonymous Access (ArtDef v1),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-17: Download Template from Artifactory with app ver notation (ArtDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-18: Download Template from Artifactory with app ver notation and Anonymous Access (ArtDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-19: Download Template from Nexus with app ver notation (ArtDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-20: Download Template from Nexus with app ver notation and Anonymous Access (ArtDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-21: Download Template from AWS CodeArtifact with app ver notation (ArtDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-22: Download Template from GCP Artifact Registry with app ver notation (ArtDef v2),integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-23: Download SNAPSHOT Template Version,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ENV-24: Download Specific Template Version,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ERR-1: Handle Missing Application Definition,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ERR-2: Handle Missing Registry Definition,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ERR-3: Handle Authentication Failure,integration_tests,IN_DEVELOPMENT,,,2
artifact-downloading,Environment Template Artifact Download,UC-AD-ERR-4: Handle Missing Artifact Definition,integration_tests,IN_DEVELOPMENT,,,2
Blue-Green Deployment,,UC-BG-1: Init Domain,pos,IMPLEMENTED,yes,,2
Blue-Green Deployment,,UC-BG-2: Warmup,pos,IMPLEMENTED,yes,,2
Blue-Green Deployment,,UC-BG-3: Promote,pos,IN_DEVELOPMENT,,QA,2
Blue-Green Deployment,,UC-BG-4: Commit,pos,IN_DEVELOPMENT,,QA,2
Blue-Green Deployment,,UC-BG-5: Rollback,pos,IN_DEVELOPMENT,,QA,2
Blue-Green Deployment,,UC-BG-6: Reverse Warmup,pos,IN_DEVELOPMENT,,QA,2
Blue-Green Deployment,,UC-BG-7: Reverse Promote,pos,IN_DEVELOPMENT,,QA,2
Blue-Green Deployment,,UC-BG-8: Reverse Commit,pos,IN_DEVELOPMENT,,QA,2
Blue-Green Deployment,,UC-BG-9: Reverse Rollback,pos,IN_DEVELOPMENT,,QA,2
Cloud Passport Processing,,,,TO_BE_DEFINED,,Необходима валидация,2
Environment Instance Generation,,TC-EIG-PARAM-010: Build Instance with DEPLOYMENT_SESSION_ID propagation,pos,TO_BE_DEFINED,,,2
Environment Instance Generation,Paramset processing,,pos,TO_BE_DEFINED,,Необходимо написать,2
Environment Instance Generation,Template variables,,pos,TO_BE_DEFINED,,Необходимо написать,2
Environment Instance Generation,Template Override,,pos,TO_BE_DEFINED,,Необходимо написать,2
Environment Instance Generation,crea processing,,,TO_BE_DEFINED,,,2
Environment Instance Generation,PR processing,Resource Profiles,pos,TO_BE_DEFINED,,Необходимо написать,2
registry_discovery,,,,TO_BE_DEFINED,,Написать UC,2
Solution Descriptor Processing,Single SD_VERSION,UC-SD-1: Single SD_VERSION with replace mode,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Single SD_VERSION,UC-SD-2: Single SD_VERSION with extended-merge mode,pos,IN_DEVELOPMENT,,QA,2
Solution Descriptor Processing,Single SD_VERSION,UC-SD-2a: Single SD_VERSION with extended-merge mode when Full SD does not exist,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Single SD_VERSION,UC-SD-3: Single SD_VERSION with basic-merge mode,pos,IMPLEMENTED,yes,Алексей,2
Solution Descriptor Processing,Single SD_VERSION,UC-SD-3a: Single SD_VERSION with basic-merge mode when Full SD does not exist,pos,IMPLEMENTED,,Алексей(заблокировано нет возможности удалить sd файл),2
Solution Descriptor Processing,Single SD_VERSION,UC-SD-4: Single SD_VERSION with basic-exclusion-merge mode,pos,IMPLEMENTED,,Алексей,2
Solution Descriptor Processing,Single SD_VERSION,UC-SD-4a: Single SD_VERSION with basic-exclusion-merge mode when Full SD does not exist,pos,IMPLEMENTED,,Алексей(заблокировано нет возможности удалить sd файл),2
Solution Descriptor Processing,Multiple SD_VERSION,UC-SD-5: Multiple SD_VERSION with basic-merge mode,pos,IMPLEMENTED,,Алексей,2
Solution Descriptor Processing,Multiple SD_VERSION,UC-SD-5a: Multiple SD_VERSION with basic-merge mode when Full SD does not exist,pos,IMPLEMENTED,,Алексей(заблокировано нет возможности удалить sd файл),2
Solution Descriptor Processing,Multiple SD_VERSION,UC-SD-6: Multiple SD_VERSION with basic-exclusion-merge mode,pos,IMPLEMENTED,,Алексей,2
Solution Descriptor Processing,Multiple SD_VERSION,UC-SD-6a: Multiple SD_VERSION with basic-exclusion-merge mode when Full SD does not exist,pos,IMPLEMENTED,,Алексей(заблокировано нет возможности удалить sd файл),2
Solution Descriptor Processing,Multiple SD_VERSION,UC-SD-7: Multiple SD_VERSION with extended-merge mode,pos,IMPLEMENTED,,Алексей(нужен механизм валидации негативных кейсов),2
Solution Descriptor Processing,Multiple SD_VERSION,UC-SD-7a: Multiple SD_VERSION with extended-merge mode when Full SD does not exist,pos,READY_FOR_DEV,,Алексей(заблокировано нет возможности удалить sd файл),2
Solution Descriptor Processing,Multiple SD_VERSION,UC-SD-8: Multiple SD_VERSION with replace mode,pos,IMPLEMENTED,,Алексей,2
Solution Descriptor Processing,SD_VERSION,UC-SD-9: Single SD_VERSION with SD_DELTA=true,pos,IMPLEMENTED,,Алексей,2
Solution Descriptor Processing,SD_VERSION,UC-SD-9a: Single SD_VERSION with SD_DELTA=true when Full SD does not exist,pos,READY_FOR_DEV,,Алексей(заблокировано нет возможности удалить sd файл),2
Solution Descriptor Processing,SD_VERSION,UC-SD-10: Single SD_VERSION with SD_DELTA=false,pos,IMPLEMENTED,,Алексей,2
Solution Descriptor Processing,Single SD_DATA,UC-SD-11: Single SD_DATA with replace mode,pos,IMPLEMENTED,,Алексей,2
Solution Descriptor Processing,Single SD_DATA,UC-SD-12: Single SD_DATA with extended-merge mode,pos,IMPLEMENTED,,Алексей,2
Solution Descriptor Processing,Single SD_DATA,UC-SD-12a: Single SD_DATA with extended-merge mode when Full SD does not exist,pos,READY_FOR_DEV,,Алексей(заблокировано нет возможности удалить sd файл),2
Solution Descriptor Processing,Single SD_DATA,UC-SD-13: Single SD_DATA with basic-merge mode,pos,IMPLEMENTED,,Завести задачу на разработку,2
Solution Descriptor Processing,Single SD_DATA,UC-SD-13a: Single SD_DATA with basic-merge mode when Full SD does not exist,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Single SD_DATA,UC-SD-14: Single SD_DATA with basic-exclusion-merge mode,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Single SD_DATA,UC-SD-14a: Single SD_DATA with basic-exclusion-merge mode when Full SD does not exist,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Multiple SD_DATA,UC-SD-15: Multiple SD_DATA with basic-merge mode,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Multiple SD_DATA,UC-SD-15a: Multiple SD_DATA with basic-merge mode when Full SD does not exist,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Multiple SD_DATA,UC-SD-16: Multiple SD_DATA with basic-exclusion-merge mode,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Multiple SD_DATA,UC-SD-16a: Multiple SD_DATA with basic-exclusion-merge mode when Full SD does not exist,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Multiple SD_DATA,UC-SD-17: Multiple SD_DATA with extended-merge mode,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Multiple SD_DATA,UC-SD-17a: Multiple SD_DATA with extended-merge mode when Full SD does not exist,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,Multiple SD_DATA,UC-SD-18: Multiple SD_DATA with replace mode,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,SD_DATA,UC-SD-19: Single SD_DATA with SD_DELTA=true,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,SD_DATA,UC-SD-19a: Single SD_DATA with SD_DELTA=true when Full SD does not exist,pos,READY_FOR_DEV,,,2
Solution Descriptor Processing,SD_DATA,UC-SD-20: Single SD_DATA with SD_DELTA=false,pos,READY_FOR_DEV,,,2
SSL,,UC-SC-NEX-1: Download template artifact from Nexus with custom CA certificate,,IMPLEMENTED,yes,,2
System Certificate Configuration,,,pos,TO_BE_DEFINED,,Необходимо написать. Чать легла в скачиваение артифактвактов часть будет в импортте CMDB,2
Template build,Template Inheritance/composition,,,TO_BE_DEFINED,,Необходимо написать,2
Template Composition ,,,pos,TO_BE_DEFINED,,Необходимо написать,2
Application and Registry Definition,Template rendering,UC-ARD-TR-1: Basic AppDef/RegDef template rendering,pos,READY_FOR_DEV,,Завести задачу на разработку,1
Application and Registry Definition,Template rendering,UC-ARD-TR-2: Basic AppDef/RegDef template delete,pos,READY_FOR_DEV,,QA,3
Application and Registry Definition,Template rendering,"UC-ARD-TR-3: Shared template repo, off-site instance rendering",pos,READY_FOR_DEV,,QA,3
Application and Registry Definition,Template rendering,"UC-ARD-TR-4: Shared template repo, on-site instance rendering",pos,READY_FOR_DEV,,QA,3
Application and Registry Definition,User-provided definitions,UC-ARD-UD-1: Replace template-rendered definition with user-provided file,pos,READY_FOR_DEV,,Завести задачу на разработку,1
Application and Registry Definition,User-provided definitions,UC-ARD-UD-2: Delete user-provided file,pos,READY_FOR_DEV,,QA,3
Application and Registry Definition,User-provided definitions,UC-ARD-UD-3: Add new definition via user-provided file with no matching template,pos,READY_FOR_DEV,,QA,3
Application and Registry Definition,Placement modes,UC-ARD-PM-1: Root mode behavior (auto-migration from legacy layout),pos,READY_FOR_DEV,,QA,3
Application and Registry Definition,Placement modes,UC-ARD-PM-2: Dual mode behavior (upgrade with no cleanup),pos,READY_FOR_DEV,,Завести задачу на разработку,1
Application and Registry Definition,CMDB integration,UC-ARD-CI-1: Export definitions to CMDB,neg,READY_FOR_DEV,,QA,3
Application and Registry Definition,,,,TO_BE_DEFINED,,В рамках https://tms.netcracker.com/browse/PDPLDEVOPS-24963 будет дополнены UC,3
Automatic Environment Name Derivation,,TC-003-001: Environment with no explicit environmentName defined,,IMPLEMENTED,yes,,3
Automatic Environment Name Derivation,,TC-003-002: Environment with explicit environmentName defined,neg,READY_FOR_DEV,,,3
Automatic Environment Name Derivation,,TC-003-003: Environment with explicit environmentName different from folder name,neg,READY_FOR_DEV,,,3
Automatic Environment Name Derivation,,TC-003-004: Invalid folder structure for environment,neg,READY_FOR_DEV,,,3
Automatic Environment Name Derivation,,TC-003-005: Template rendering with derived environment name,neg,READY_FOR_DEV,,,3
cmdb_import,,,,NEED_UPDATE,,Баг,3
Credential Encryption,,TC-004-001: Encryption Enabled with Supported Fields,pos,NEED_UPDATE,,,3
Credential Encryption,,TC-004-002: Encryption Skipped When Disabled,pos,NEED_UPDATE,,,3
Credential Encryption,,TC-004-003: Secret Key Mandatory for Fernet,pos,NEED_UPDATE,,,3
Credential Encryption,,TC-004-004: Successful Encryption Using Fernet,pos,NEED_UPDATE,,,3
Credential Encryption,,TC-004-005: Skip Encryption if File Already Encrypted Using Fernet,pos,NEED_UPDATE,,,3
Credential Encryption,,TC-004-006: age_key Mandatory for SOPS,pos,NEED_UPDATE,,,3
Credential Encryption,,TC-004-007: Successful Encryption Using SOPS,pos,NEED_UPDATE,,,3
Credential Encryption,,TC-004-008: Skip Encryption if File Already Encrypted Using SOPS,pos,NEED_UPDATE,,,3
Credential Rotation,,UC-CR-TPR-1: Update Credential from Pipeline Parameter,,READY_FOR_DEV,,,3
Credential Rotation,,UC-CR-TPR-2: Update Credential from Deployment Parameter,,READY_FOR_DEV,,,3
Credential Rotation,,UC-CR-TPR-3: Update Credentials from Multiple rotation_items,,IN_DEVELOPMENT,,Передано в разработку. Надо перепроверить ,3
Credential Rotation,,UC-CR-LCH-1: Reject Affected Credential Update,,READY_FOR_DEV,,,3
Credential Rotation,,UC-CR-LCH-2: Update Affected Credentials in Force Mode,,IN_DEVELOPMENT,,Передано в разработку,3
Credential Rotation,,UC-CR-VAL-1: Fail When No Affected Parameters Found,,READY_FOR_DEV,,,3
Credential Rotation,,UC-CR-ENC-1: Update Credentials with Plaintext Payload when Encryption Is Enabled,,READY_FOR_DEV,,,3
Credential Rotation,,UC-CR-ENC-2: Update Credentials with Encrypted Payload when Encryption Is Enabled,,READY_FOR_DEV,,,3
Environment Instance Generation,,TC-EIG-PARAM-011: Build Instance with CRED_ROTATION_PAYLOAD (trigger cred rotation),pos,TO_BE_DEFINED,,,3
Environment Instance Generation,,TC-EIG-PARAM-012: Build Instance with CRED_ROTATION_FORCE (force cred rotation),pos,TO_BE_DEFINED,,,3
Environment Instance Generation,,TC-EIG-PARAM-014: Build Instance with BG_MANAGE enabled (bg_manage job runs),pos,TO_BE_DEFINED,,,3
Environment Instance Generation,,TC-EIG-PARAM-015: Build Instance with BG_STATE provided (state validation/update),pos,TO_BE_DEFINED,,,3
Environment Inventory Generation,environment specific parameters (Enviroment generation),UC-EINV-ESP-5: Override inventory.cloudName via ENV_SPECIFIC_PARAMS.cloudName,,TO_BE_DEFINED,,Необходимо написать,3
GSF maintenance,Template Repository Maintenance via GSF,UC-GSF-TMP-3: Downgrade Template Repository via GSF,,READY_FOR_DEV,,,3
GSF maintenance,Instance Repository Maintenance via GSF,UC-GSF-INST-3: Downgrade Instance Repository via GSF,,READY_FOR_DEV,,,3
Namespace Render Filter,,,pos,TO_BE_DEFINED,,Необходимо написать Отсутсвует сценарий,3
Template Override,Basic,TC-003-001: Using templates_dir,pos,NEED_UPDATE,,,3
Template Override,Basic,TC-003-002: Using current_env.name,pos,NEED_UPDATE,,,3
Template Override,Basic,TC-003-003: Using current_env.tenant,pos,NEED_UPDATE,,,3
Template Override,Cloud,TC-003-004: Using current_env.cloud. inventory.cloudName set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Cloud,TC-003-005: Using current_env.cloud. inventory.cloudName NOT set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Cloud,TC-003-006: Using current_env.cloudNameWithCluster. inventory.cloudName set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Cloud,TC-003-007: Using current_env.cloudNameWithCluster. inventory.cloudPassport set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Cloud,TC-003-008: Using current_env.cloudNameWithCluster. inventory.cloudName and inventory.cloudPassport NOT set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,CMDB,TC-003-009: Using current_env.cmdb_name. inventory.deployer set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,CMDB,TC-003-010: Using current_env.cmdb_name. inventory.deployer NOT set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,CMDB,TC-003-011: Using current_env.cmdb_url. inventory.deployer set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,CMDB,TC-003-012: Using current_env.cmdb_url. inventory.deployer NOT set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Inventory,TC-003-013: Using current_env.description. inventory.description set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Inventory,TC-003-014: Using current_env.description. inventory.description NOT set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Inventory,TC-003-015: Using current_env.owners. inventory.owners set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Inventory,TC-003-016: Using current_env.owners. inventory.owners NOT set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,,TC-003-017: Using current_env.env_template,pos,NEED_UPDATE,,,3
Template Override,Additional Template Variables,TC-003-018: Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Additional Template Variables,TC-003-019: Using current_env.additionalTemplateVariables. envTemplate.additionalTemplateVariables NOT set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Cloud,TC-003-020: Using current_env.cloud_passport. inventory.cloudPassport set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Cloud,TC-003-021: Using current_env.cloud_passport. inventory.cloudPassport NOT set in Environment Inventory,pos,NEED_UPDATE,,,3
Template Override,Solution structure,TC-003-022: Using current_env.solution_structure. SD exist in Instance repository,pos,NEED_UPDATE,,,3
Template Override,Solution structure,TC-003-023: Using current_env.solution_structure. SD NOT in Instance repository,pos,NEED_UPDATE,,,3
Template Override,Template override,TC-002-001: Template override on Cloud and Namespace level. Override includes paramsets with comments,pos,NEED_UPDATE,,,3
Environment Instance Generation,,TC-EIG-PARAM-007: Build Instance with APP_DEFS_PATH (custom AppDefs path),pos,TO_BE_DEFINED,,,4
Environment Instance Generation,,TC-EIG-PARAM-008: Build Instance with REG_DEFS_PATH (custom RegDefs path),pos,TO_BE_DEFINED,,,4
Environment Instance Generation,,TC-EIG-PARAM-009: Build Instance with NS_BUILD_FILTER (build filtered namespaces only),pos,TO_BE_DEFINED,,,4
SBOM/Application Manifest v1 generating,,,pos,TO_BE_DEFINED,,"тут нужно юниты тесты пишет Крис, y",4
Environment Instance Generation,,TC-EIG-PARAM-013: Build Instance with GH_ADDITIONAL_PARAMS (GitHub additional params),pos,TO_BE_DEFINED,,неизвестно как через атлас запускать гитхаб пайплайны,5
GSF maintenance,Template Repository Maintenance via GSF,UC-GSF-TMP-2.1: Upgrade legacy Template Repository (versions before 2.85.0),integration_tests,READY_FOR_DEV,,,1
 SBOM retention,,UC-SBOM-1: SBOM retention disabled - no cleanup,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-24888 Станислав,3
 SBOM retention,,UC-SBOM-2: All applications within per-application limit - no files deleted,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-24888 Станислав,3
 SBOM retention,,UC-SBOM-3: Per-application retention with default settings,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-24888 Станислав,3
 SBOM retention,,UC-SBOM-4: Per-application retention with custom version count,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-24888 Станислав,3
 SBOM retention,,UC-SBOM-5: Total /sboms/ size exceeds 1200 MB after per-application retention - full cache wipe,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-24888 Станислав,3
SBOM Storage Migration,,UC-SBOM-MIG-1: First run after upgrade,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-25639  Станислав,3
envgeneNullValue validation,,UC-NVV-1: Unresolved parameter blocks pipeline,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-25638 Станислав,1
envgeneNullValue validation,,UC-NVV-2: Unresolved credential blocks pipeline,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-25638 Станислав,1
envgeneNullValue validation,,UC-NVV-3: All values resolved,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-25638 Станислав,2
envgeneNullValue validation,,UC-NVV-4: Multiple unresolved values reported together,integration_tests,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-25638 Станислав,2
customer E2E Test Scenarios,,customer E2E Test Scenarios,,IN_DEVELOPMENT,,https://tms.netcracker.com/browse/PDPLDEVOPS-25661 Диас,

