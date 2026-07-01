# E2E Test Logs and Use Cases Analysis Report

## 1. Summary
- **Total Documented UCs:** 175
- **Total Tests Found in Logs:** 168
- **Tests mapped to UCs:** 168
- **Unmapped Tests:** 0

### Mapped Tests Statuses
- **PASSED:** 154
- **FAILED:** 14
- **SKIPPED:** 0

## 2. Failed Tests (Mapped to UCs)
| Use Case | Test Function | Status | Reason |
|----------|---------------|--------|--------|
| UC-AEN-END-4 | `test_ucaenend4_invalid_folder_structure_for_environment` | ❌ FAILED |  |
| UC-NVV-1 | `test_ucnvv1_validation_failure_on_missing_required_key` | ❌ FAILED |  |
| UC-NVV-2 | `test_ucnvv2_validation_failure_on_explicitly_null_value` | ❌ FAILED |  |
| UC-EIG-ES-1 | `test_uceiges1_generate_effective_set_without_sd_data_or_sd_version` | ❌ FAILED |  |
| UC-EIG-ES-2 | `test_uceiges2_generate_effective_set_with_sd_data_or_sd_version` | ❌ FAILED |  |
| UC-EIG-ES-3 | `test_uceiges3_apply_custom_params_when_generate_effective_set_is_true` | ❌ FAILED |  |
| UC-EIG-ME-1 | `test_uceigme1_parallel_environment_instance_generation_for_multiple_environments` | ❌ FAILED |  |
| UC-EINV-PS-3 | `test_uceinvps3_delete_paramset_file` | ❌ FAILED |  |
| UC-EINV-CR-3 | `test_uceinvcr3_delete_credentials_file` | ❌ FAILED |  |
| UC-EINV-RP-1 | `test_uceinvrp1_create_resource_profile_file` | ❌ FAILED |  |
| UC-EINV-RP-3 | `test_uceinvrp3_delete_resource_profile_file` | ❌ FAILED |  |
| UC-EINV-STV-1 | `test_uceinvstv1_create_specific_template_version_file` | ❌ FAILED |  |
| UC-EINV-STV-3 | `test_uceinvstv3_delete_specific_template_version_file` | ❌ FAILED |  |
| UC-EINV-TV-1 | `test_uceinvtv1_create_template_variable_file` | ❌ FAILED |  |

## 3. Passed Tests (Mapped to UCs)
| Use Case | Test Function | Status |
|----------|---------------|--------|
| UC-ARD-TR-1 | `test_ucardtr1_basic_appdefregdef_template_rendering` | ✅ PASSED |
| UC-ARD-TR-2 | `test_ucardtr2_basic_appdefregdef_template_delete` | ✅ PASSED |
| UC-ARD-TR-3 | `test_ucardtr3_shared_template_repository_offsite_instance_rendering` | ✅ PASSED |
| UC-ARD-TR-4 | `test_ucardtr4_shared_template_repository_onsite_instance_rendering` | ✅ PASSED |
| UC-AD-ERR-1 | `test_ucaderr1_handle_missing_application_definition` | ✅ PASSED |
| UC-AD-ERR-2 | `test_ucaderr2_handle_missing_registry_definition` | ✅ PASSED |
| UC-AD-ERR-3 | `test_ucaderr3_handle_authentication_failure` | ✅ PASSED |
| UC-AD-ERR-4 | `test_ucaderr4_handle_missing_artifact_definition` | ✅ PASSED |
| UC-AD-SD-1 | `test_ucadsd1_download_sd_from_artifactory_with_userpassword_appdef_v1__regdef_v1` | ✅ PASSED |
| UC-AD-SD-2 | `test_ucadsd2_download_sd_from_artifactory_with_anonymous_access_appdef_v1__regdef_v1` | ✅ PASSED |
| UC-AD-SD-3 | `test_ucadsd3_download_sd_from_nexus_with_userpassword_appdef_v1__regdef_v1` | ✅ PASSED |
| UC-AD-SD-4 | `test_ucadsd4_download_sd_from_nexus_with_anonymous_access_appdef_v1__regdef_v1` | ✅ PASSED |
| UC-AD-SD-5 | `test_ucadsd5_download_sd_from_artifactory_with_userpassword_appdef_v1__regdef_v2` | ✅ PASSED |
| UC-AD-SD-6 | `test_ucadsd6_download_sd_from_artifactory_with_anonymous_access_appdef_v1__regdef_v2` | ✅ PASSED |
| UC-AD-SD-8 | `test_ucadsd8_download_sd_from_nexus_with_anonymous_access_appdef_v1__regdef_v2` | ✅ PASSED |
| UC-AD-SD-9 | `test_ucadsd9_download_sd_from_aws_codeartifact_with_secret_appdef_v1__regdef_v2` | ✅ PASSED |
| UC-AD-SD-10 | `test_ucadsd10_download_sd_from_gcp_artifact_registry_with_service_account_appdef_v1__regdef_v2` | ✅ PASSED |
| UC-AD-SD-11 | `test_ucadsd11_download_specific_version_sd` | ✅ PASSED |
| UC-AD-ENV-9 | `test_ucadenv9_download_template_from_artifactory_with_gav_notation` | ✅ PASSED |
| UC-AD-ENV-10 | `test_ucadenv10_download_template_from_artifactory_with_gav_notation_and_anonymous_access` | ✅ PASSED |
| UC-AD-ENV-11 | `test_ucadenv11_download_template_from_nexus_with_gav_notation` | ✅ PASSED |
| UC-SC-NEX-1 | `test_ucscnex1_download_template_artifact_from_nexus_with_custom_ca_certificate` | ✅ PASSED |
| UC-AD-ENV-12 | `test_ucadenv12_download_template_from_nexus_with_gav_notation_and_anonymous_access` | ✅ PASSED |
| UC-AD-ENV-13 | `test_ucadenv13_download_template_with_app_ver_notation_from_artifactory_artdef_v1` | ✅ PASSED |
| UC-AD-ENV-14 | `test_ucadenv14_download_template_with_app_ver_notation_from_artifactory_and_anonymous_access_artdef_v1` | ✅ PASSED |
| UC-AD-ENV-15 | `test_ucadenv15_download_template_with_app_ver_notation_from_nexus_artdef_v1` | ✅ PASSED |
| UC-AD-ENV-16 | `test_ucadenv16_download_template_with_app_ver_notation_from_nexus_and_anonymous_access_artdef_v1` | ✅ PASSED |
| UC-AD-ENV-17 | `test_ucadenv17_download_template_from_artifactory_with_app_ver_notation_artdef_v2` | ✅ PASSED |
| UC-AD-ENV-18 | `test_ucadenv18_download_template_from_artifactory_with_app_ver_notation_and_anonymous_access_artdef_v2` | ✅ PASSED |
| UC-AD-ENV-19 | `test_ucadenv19_download_template_from_nexus_with_app_ver_notation_artdef_v2` | ✅ PASSED |
| UC-AD-ENV-20 | `test_ucadenv20_download_template_from_nexus_with_app_ver_notation_and_anonymous_access_artdef_v2` | ✅ PASSED |
| UC-AD-ENV-21 | `test_ucadenv21_download_template_from_aws_codeartifact_with_app_ver_notation_artdef_v2` | ✅ PASSED |
| UC-AD-ENV-22 | `test_ucadenv22_download_template_from_gcp_artifact_registry_with_app_ver_notation_artdef_v2` | ✅ PASSED |
| UC-AD-ENV-23 | `test_ucadenv23_download_snapshot_template_version` | ✅ PASSED |
| UC-AD-ENV-24 | `test_ucadenv24_download_specific_template_version` | ✅ PASSED |
| UC-AEN-END-1 | `test_ucaenend1_environment_with_no_explicit_environmentname_defined` | ✅ PASSED |
| UC-AEN-END-2 | `test_ucaenend2_environment_with_explicit_environmentname_defined` | ✅ PASSED |
| UC-AEN-END-3 | `test_ucaenend3_environment_with_explicit_environmentname_different_from_folder_name` | ✅ PASSED |
| UC-AEN-END-5 | `test_ucaenend5_template_rendering_with_derived_environment_name` | ✅ PASSED |
| UC-BG-1 | `test_ucbg1_init_domain` | ✅ PASSED |
| UC-BG-2 | `test_ucbg2_warmup` | ✅ PASSED |
| UC-BG-3 | `test_ucbg3_promote` | ✅ PASSED |
| UC-BG-4 | `test_ucbg4_commit` | ✅ PASSED |
| UC-BG-5 | `test_ucbg5_rollback` | ✅ PASSED |
| UC-BG-6 | `test_ucbg6_reverse_warmup` | ✅ PASSED |
| UC-BG-7 | `test_ucbg7_reverse_promote` | ✅ PASSED |
| UC-BG-8 | `test_ucbg8_reverse_commit` | ✅ PASSED |
| UC-BG-9 | `test_ucbg9_reverse_rollback` | ✅ PASSED |
| UC-CC-DP-1 | `test_ucccdp1_exact_match` | ✅ PASSED |
| UC-CC-DP-2 | `test_ucccdp2_bg_domain_match` | ✅ PASSED |
| UC-CC-DP-3 | `test_ucccdp3_no_exact_match_found` | ✅ PASSED |
| UC-CC-DP-4 | `test_ucccdp4_no_bg_domain_match_found` | ✅ PASSED |
| UC-CC-MR-1 | `test_ucccmr1_simple_type_resolution` | ✅ PASSED |
| UC-CC-MR-2 | `test_ucccmr2_complex_structure_resolution` | ✅ PASSED |
| UC-CC-HR-1 | `test_uccchr1_namespace_to_cloud_reference` | ✅ PASSED |
| UC-CC-HR-2 | `test_uccchr2_namespace_to_tenant_reference` | ✅ PASSED |
| UC-CC-HR-3 | `test_uccchr3_cloud_to_tenant_reference` | ✅ PASSED |
| UC-CC-HR-4 | `test_uccchr4_cloud_to_namespace_reference_error` | ✅ PASSED |
| UC-CC-HR-5 | `test_uccchr5_tenant_to_cloud_reference_error` | ✅ PASSED |
| UC-CC-HR-6 | `test_uccchr6_tenant_to_namespace_reference_error` | ✅ PASSED |
| UC-CC-CR-1 | `test_uccccr1_deployparameters_to_e2eparameters_reference_error` | ✅ PASSED |
| UC-CC-CR-2 | `test_uccccr2_deployparameters_to_technicalconfigurationparameters_reference_error` | ✅ PASSED |
| UC-CC-CR-3 | `test_uccccr3_e2eparameters_to_deployparameters_reference_error` | ✅ PASSED |
| UC-CC-CR-4 | `test_uccccr4_e2eparameters_to_technicalconfigurationparameters_reference_error` | ✅ PASSED |
| UC-CC-CR-5 | `test_uccccr5_technicalconfigurationparameters_to_deployparameters_reference_error` | ✅ PASSED |
| UC-CC-CR-6 | `test_uccccr6_technicalconfigurationparameters_to_e2eparameters_reference_error` | ✅ PASSED |
| UC-01 | `test_uc01_environment_inherits_cluster_cloud_passport_automatically` | ✅ PASSED |
| UC-02 | `test_uc02_environment_uses_explicitly_named_cloud_passport` | ✅ PASSED |
| UC-03 | `test_uc03_environment_builds_without_cloud_passport` | ✅ PASSED |
| UC-04 | `test_uc04_environment_uses_passport_from_custom_location` | ✅ PASSED |
| UC-05 | `test_uc05_parameter_source_traceability` | ✅ PASSED |
| UC-06 | `test_uc06_business_environments_autoassociate_the_business_passport_in_a_mixed_cluster` | ✅ PASSED |
| UC-07 | `test_uc07_infra_environments_use_an_explicit_infra_passport_in_a_mixed_cluster` | ✅ PASSED |
| UC-09 | `test_uc09_backward_compatibility_for_existing_business_environments` | ✅ PASSED |
| UC-08 | `test_uc08_mixed_cluster_failure_when_infra_relies_on_autoassociation` | ✅ PASSED |
| UC-CR-TPR-1 | `test_uccrtpr1_update_credential_from_pipeline_parameter` | ✅ PASSED |
| UC-CR-TPR-2 | `test_uccrtpr2_update_credential_from_deployment_parameter` | ✅ PASSED |
| UC-CR-TPR-3 | `test_uccrtpr3_update_credentials_from_multiple_rotation_items` | ✅ PASSED |
| UC-CR-LCH-1 | `test_uccrlch1_reject_affected_credential_update` | ✅ PASSED |
| UC-CR-LCH-2 | `test_uccrlch2_update_affected_credentials_in_force_mode` | ✅ PASSED |
| UC-CR-VAL-1 | `test_uccrval1_fail_when_no_affected_parameters_found` | ✅ PASSED |
| UC-CR-ENC-1 | `test_uccrenc1_update_credentials_with_plaintext_payload_when_encryption_is_enabled` | ✅ PASSED |
| UC-CR-ENC-2 | `test_uccrenc2_update_credentials_with_encrypted_payload_when_encryption_is_enabled` | ✅ PASSED |
| UC-CR-ENC-3 | `test_uccrenc3_update_credentials_with_plaintext_payload_when_encryption_is_disabled` | ✅ PASSED |
| UC-CR-ENC-4 | `test_uccrenc4_update_credentials_with_encrypted_payload_when_encryption_is_disabled` | ✅ PASSED |
| UC-NVV-3 | `test_ucnvv3_all_values_resolved` | ✅ PASSED |
| UC-EIG-NF-1 | `test_uceignf1_namespace_not_in_bg_domain_with_deploy_postfix` | ✅ PASSED |
| UC-EIG-NF-2 | `test_uceignf2_namespace_not_in_bg_domain_without_deploy_postfix` | ✅ PASSED |
| UC-EIG-NF-3 | `test_uceignf3_controller_namespace_in_bg_domain_with_deploy_postfix` | ✅ PASSED |
| UC-EIG-NF-4 | `test_uceignf4_controller_namespace_in_bg_domain_without_deploy_postfix` | ✅ PASSED |
| UC-EIG-NF-5 | `test_uceignf5_origin_namespace_in_bg_domain_with_deploy_postfix` | ✅ PASSED |
| UC-EIG-NF-6 | `test_uceignf6_origin_namespace_in_bg_domain_without_deploy_postfix` | ✅ PASSED |
| UC-EIG-NF-7 | `test_uceignf7_peer_namespace_in_bg_domain_with_deploy_postfix` | ✅ PASSED |
| UC-EIG-NF-8 | `test_uceignf8_peer_namespace_in_bg_domain_without_deploy_postfix` | ✅ PASSED |
| UC-EIG-TA-1 | `test_uceigta1_environment_instance_generation_with_artifact_only` | ✅ PASSED |
| UC-EIG-TA-2 | `test_uceigta2_environment_instance_generation_with_artifact_and_bgnsartifacts_and_bg_domain` | ✅ PASSED |
| UC-EIG-TA-3 | `test_uceigta3_environment_instance_generation_with_artifact_and_bgnsartifacts_and_without_bg_domain` | ✅ PASSED |
| UC-EIG-ES-4 | `test_uceiges4_ignore_custom_params_when_generate_effective_set_is_false` | ✅ PASSED |
| UC-EINV-ED-1 | `test_uceinved1_create_env_definitionyml` | ✅ PASSED |
| UC-EINV-ED-3 | `test_uceinved3_delete_env_definitionyml` | ✅ PASSED |
| UC-EINV-PS-1 | `test_uceinvps1_create_paramset_file` | ✅ PASSED |
| UC-EINV-CR-1 | `test_uceinvcr1_create_credentials_file` | ✅ PASSED |
| UC-EINV-AT-ALL-1 | `test_uceinvatall1_rollback_all_inventory_changes_if_any_operation_fails` | ✅ PASSED |
| UC-SBOM-1 | `test_ucsbom1_sbom_retention_disabled__no_cleanup` | ✅ PASSED |
| UC-SBOM-2 | `test_ucsbom2_all_applications_within_perapplication_limit__no_files_deleted` | ✅ PASSED |
| UC-SBOM-3 | `test_ucsbom3_perapplication_retention_keeps_10_most_recent_versions` | ✅ PASSED |
| UC-SBOM-4 | `test_ucsbom4_perapplication_retention_with_custom_version_count` | ✅ PASSED |
| UC-SBOM-5 | `test_ucsbom5_total_sboms_size_exceeds_1200_mb__keeps_newest_per_application` | ✅ PASSED |
| UC-SD-1 | `test_ucsd1_single_sd_version_with_replace_mode` | ✅ PASSED |
| UC-SD-2 | `test_ucsd2_single_sd_version_with_extendedmerge_mode` | ✅ PASSED |
| UC-SD-2 | `test_ucsd2a_single_sd_version_with_extendedmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-3 | `test_ucsd3_single_sd_version_with_basicmerge_mode` | ✅ PASSED |
| UC-SD-3 | `test_ucsd3a_single_sd_version_with_basicmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-4 | `test_ucsd4_single_sd_version_with_basicexclusionmerge_mode` | ✅ PASSED |
| UC-SD-4 | `test_ucsd4a_single_sd_version_with_basicexclusionmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-5 | `test_ucsd5_multiple_sd_version_with_basicmerge_mode` | ✅ PASSED |
| UC-SD-5 | `test_ucsd5a_multiple_sd_version_with_basicmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-6 | `test_ucsd6_multiple_sd_version_with_basicexclusionmerge_mode` | ✅ PASSED |
| UC-SD-6 | `test_ucsd6a_multiple_sd_version_with_basicexclusionmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-8 | `test_ucsd8_multiple_sd_version_with_replace_mode` | ✅ PASSED |
| UC-SD-9 | `test_ucsd9_single_sd_version_with_sd_deltatrue` | ✅ PASSED |
| UC-SD-9 | `test_ucsd9a_single_sd_version_with_sd_deltatrue_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-10 | `test_ucsd10_single_sd_version_with_sd_deltafalse` | ✅ PASSED |
| UC-SD-11 | `test_ucsd11_single_sd_data_with_replace_mode` | ✅ PASSED |
| UC-SD-12 | `test_ucsd12_single_sd_data_with_extendedmerge_mode` | ✅ PASSED |
| UC-SD-12 | `test_ucsd12a_single_sd_data_with_extendedmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-13 | `test_ucsd13_single_sd_data_with_basicmerge_mode` | ✅ PASSED |
| UC-SD-13 | `test_ucsd13a_single_sd_data_with_basicmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-14 | `test_ucsd14_single_sd_data_with_basicexclusionmerge_mode` | ✅ PASSED |
| UC-SD-14 | `test_ucsd14a_single_sd_data_with_basicexclusionmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-15 | `test_ucsd15_multiple_sd_data_with_basicmerge_mode` | ✅ PASSED |
| UC-SD-15 | `test_ucsd15a_multiple_sd_data_with_basicmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-16 | `test_ucsd16_multiple_sd_data_with_basicexclusionmerge_mode` | ✅ PASSED |
| UC-SD-16 | `test_ucsd16a_multiple_sd_data_with_basicexclusionmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-17 | `test_ucsd17_multiple_sd_data_with_extendedmerge_mode` | ✅ PASSED |
| UC-SD-17 | `test_ucsd17a_multiple_sd_data_with_extendedmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-18 | `test_ucsd18_multiple_sd_data_with_replace_mode` | ✅ PASSED |
| UC-SD-19 | `test_ucsd19_single_sd_data_with_sd_deltatrue` | ✅ PASSED |
| UC-SD-19 | `test_ucsd19a_single_sd_data_with_sd_deltatrue_when_full_sd_does_not_exist` | ✅ PASSED |
| UC-SD-20 | `test_ucsd20_single_sd_data_with_sd_deltafalse` | ✅ PASSED |
| UC-ARD-UD-1 | `test_ucardud1_replace_templaterendered_definition_with_userprovided_file` | ✅ PASSED |
| UC-ARD-UD-2 | `test_ucardud2_delete_userprovided_file` | ✅ PASSED |
| UC-ARD-UD-3 | `test_ucardud3_add_new_definition_via_userprovided_file_with_no_matching_template` | ✅ PASSED |
| UC-ARD-PM-1 | `test_ucardpm1_root_mode_behavior_automigration_from_legacy_layout` | ✅ PASSED |
| UC-ARD-PM-2 | `test_ucardpm2_dual_mode_behavior_upgrade_with_no_cleanup` | ✅ PASSED |
| UC-ARD-CI-1 | `test_ucardci1_export_definitions_to_cmdb` | ✅ PASSED |
| UC-AD-SD-7 | `test_ucadsd7_download_sd_from_nexus_with_userpassword_appdef_v1__regdef_v2` | ✅ PASSED |
| UC-NVV-4 | `test_ucnvv4_ignore_null_values_when_validation_is_disabled` | ✅ PASSED |
| UC-EINV-ED-2 | `test_uceinved2_update_env_definitionyml` | ✅ PASSED |
| UC-EINV-PS-2 | `test_uceinvps2_update_paramset_file` | ✅ PASSED |
| UC-EINV-CR-2 | `test_uceinvcr2_update_credentials_file` | ✅ PASSED |
| UC-EINV-RP-2 | `test_uceinvrp2_update_resource_profile_file` | ✅ PASSED |
| UC-EINV-STV-2 | `test_uceinvstv2_update_specific_template_version_file` | ✅ PASSED |
| UC-SD-7 | `test_ucsd7_single_sd_version_with_asicexclusionmerge_mode_when_full_sd_does_not_exist` | ✅ PASSED |

## 4. Unmapped Tests (Found in logs but not matched to docs UCs)
*All tests were successfully mapped to Use Cases!*

## 5. Documented UCs without Tests in Logs
Found 20 UCs without explicit tests in logs:
- **UC-GSF-INST-1** (in gsf-repository-maintenance.md)
- **UC-GSF-INST-2** (in gsf-repository-maintenance.md)
- **UC-GSF-INST-3** (in gsf-repository-maintenance.md)
- **UC-GSF-TMP-1** (in gsf-repository-maintenance.md)
- **UC-GSF-TMP-2** (in gsf-repository-maintenance.md)
- **UC-GSF-TMP-3** (in gsf-repository-maintenance.md)
- **UC-SBOM-MIG-1** (in sbom-storage-migration.md)
- **UC-TI-CS-1** (in template-inheritance.md)
- **UC-TI-OV-1** (in template-inheritance.md)
- **UC-TI-OV-2** (in template-inheritance.md)
- **UC-TI-PT-1** (in template-inheritance.md)
- **UC-TI-PT-2** (in template-inheritance.md)
- **UC-XXX-1** (in README.md)
- **UC-XXX-2** (in README.md)
- **UC-XXX-3** (in README.md)
- **UC-XXX-5** (in README.md)
- **UC-XXX-6** (in README.md)
- **UC-XXX-GROUP-1** (in README.md)
- **UC-XXX-GROUP-2** (in README.md)
- **UC-XXX-GROUP-3** (in README.md)
