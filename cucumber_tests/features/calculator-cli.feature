Feature: Calculator CLI
  As an EnvGene pipeline
  I want to generate Effective Set v2.0 using the Calculator CLI
  So that deployPostfix matching, parameter merging, macro resolution, custom params, and reference rules all work correctly

  Background:
    Given the pipeline has GENERATE_EFFECTIVE_SET set to "true"

  # ── deployPostfix Matching (UC-CC-DP-*) ──────────────────────────────────────

  Scenario: UC-CC-DP-1: Exact deployPostfix Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "NAMESPACE: core"

  @xfail_cli_npe
  Scenario: UC-CC-DP-2: BG Domain deployPostfix Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  @xfail_cli_npe
  Scenario: UC-CC-DP-3: No Exact Match Found
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_3"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "nonexistent"

  @xfail_cli_npe
  Scenario: UC-CC-DP-4: No BG Domain Match Found
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "xyz"

  # why: DP-2 matches origin only; the deployPostfix + "-peer" branch is a separate documented rule
  @xfail_cli_npe
  Scenario: UC-CC-DP-5: BG Domain deployPostfix Peer Match
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_5"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "NAMESPACE: bss-peer"

  # why: the no-match error must list ALL unmatched postfixes; DP-4 supplies only one
  @xfail_cli_npe
  Scenario: UC-CC-DP-6: Multiple Unmatched deployPostfix Values Listed Together
    Given the workspace is initialized with test data from "e2e/uc_cc_dp_6"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "foo"
    And the pipeline log shows "bar"

  # ── Parameter Merge Hierarchy (UC-CC-PM-*) ───────────────────────────────────

  Scenario: UC-CC-PM-1: Namespace Parameter Overrides Cloud Parameter
    Given the workspace is initialized with test data from "e2e/uc_cc_pm_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "shared_key: from-namespace"

  Scenario: UC-CC-PM-2: Cloud Parameter Overrides Tenant Parameter
    Given the workspace is initialized with test data from "e2e/uc_cc_pm_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "shared_key: from-cloud"

  Scenario: UC-CC-PM-3: Namespace Parameter Overrides Tenant Parameter Directly
    Given the workspace is initialized with test data from "e2e/uc_cc_pm_3"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "shared_key: from-namespace"

  # PM covers Tenant/Cloud/Namespace only; Application level (priority rank 6) beats Namespace (rank 9).
  # The Application object must live at Namespaces/<ns>/Applications/<app>.yml - an env-root
  # Applications/<app>.yml is a Cloud-level object instead and cannot exercise this override.
  Scenario: UC-CC-PM-4: Application Parameter Overrides Namespace Parameter
    Given the workspace is initialized with test data from "e2e/uc_cc_pm_4"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "shared_key: from-application"

  # ── Parameter Type Preservation in Macro Resolution (UC-CC-MR-*) ─────────────

  Scenario: UC-CC-MR-1: Simple Type Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "api_port: 8080"
    And the effective set deployment parameters contain "use_ssl: true"

  Scenario: UC-CC-MR-2: Complex Structure Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "api_config:"
    And the effective set deployment parameters contain "host: db.example.com"

  Scenario: UC-CC-MR-3: Multi-Step Macro Chain Resolution
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_3"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "final_url: https://api.example.com"

  # why: type preservation is not transitive across a chained macro reference (D6) - a chained
  # integer reference collapses to the string '30' instead of staying an integer
  @xfail_cli_type_not_transitive
  Scenario: UC-CC-MR-4: Macro Reference Resolved Across Hierarchy Levels
    Given the workspace is initialized with test data from "e2e/uc_cc_mr_4"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "ns_timeout: 30"

  # ── Custom Parameters Injection (UC-CC-CP-*) ─────────────────────────────────

  Scenario: UC-CC-CP-1: CUSTOM_PARAMS Injected into Deployment Parameters
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_1"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"deployment\":{\"override_key\":\"injected-value\"}}"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "override_key: injected-value"

  Scenario: UC-CC-CP-2: CUSTOM_PARAMS with Unknown Namespace Fails
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_2"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"namespaces\":{\"nonexistent-ns\":{\"key\":\"value\"}}}"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "nonexistent-ns"

  Scenario: UC-CC-CP-3: CUSTOM_PARAMS with Mixed Top-Level and Namespace Keys Fails
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_3"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"deployment\":{\"key\":\"val\"},\"namespaces\":{\"core\":{\"key\":\"val\"}}}"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "namespaces"
    And the pipeline log shows "deployment"

  # why: CP-1 only injects a new key; Custom Params is rank 1 and must override an existing value
  Scenario: UC-CC-CP-4: CUSTOM_PARAMS Overrides Existing Namespace Parameter
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_4"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"deployment\":{\"shared_key\":\"from-custom\"}}"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "shared_key: from-custom"

  # why: Custom Params applies to deployment, runtime and cleanup; only deployment is covered.
  # Per docs/features/calculator-cli.md Runtime Parameter Context: --custom-params values for
  # "runtime" land in runtime/<ns>/<app>/credentials.yaml (treated as sensitive, encrypted at
  # rest), not parameters.yaml - only the key name is checked, matching SC-1/SC-2's pattern.
  Scenario: UC-CC-CP-6: CUSTOM_PARAMS Injected into Runtime Context
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_6"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"runtime\":{\"runtime_key\":\"from-custom\"}}"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set runtime parameters contain "runtime_key:"

  # why: CP-2/CP-3 cover only the namespace-scoped failure paths; the success path is uncovered
  Scenario: UC-CC-CP-7: Namespace-Scoped CUSTOM_PARAMS Injected into Target Namespace
    Given the workspace is initialized with test data from "e2e/uc_cc_cp_7"
    And the pipeline parameter "CUSTOM_PARAMS" is set to "{\"namespaces\":{\"core\":{\"deployment\":{\"scoped_key\":\"from-custom\"}}}}"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "scoped_key: from-custom"

  # ── Generation ID Types (UC-CC-GI-*) ─────────────────────────────────────────

  Scenario: UC-CC-GI-1: UniqForRun Application Gets Unique Generation Directory
    Given the workspace is initialized with test data from "e2e/uc_cc_gi_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set contains a generation id subdirectory for "test-app"

  Scenario: UC-CC-GI-2: UniqForVersion Application Gets Version-Derived Generation Directory
    Given the workspace is initialized with test data from "e2e/uc_cc_gi_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters for "test-app" exist under version "1.2.3"

  # ── Cross-Level Parameter References (UC-CC-HR-*) ────────────────────────────

  Scenario: UC-CC-HR-1: Namespace to Cloud Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "service_url: https://api.example.com"

  Scenario: UC-CC-HR-2: Namespace to Tenant Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "organization: acme-corp"

  Scenario: UC-CC-HR-3: Cloud to Tenant Reference
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_3"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "cloud_label: acme-corp"

  Scenario: UC-CC-HR-4: Cloud to Namespace Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "namespace_test_url"

  @xfail_cli_no_hierarchy_rule
  Scenario: UC-CC-HR-5: Tenant to Cloud Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_5"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "Tenant level parameters cannot reference Cloud level parameters"

  @xfail_cli_no_hierarchy_rule
  Scenario: UC-CC-HR-6: Tenant to Namespace Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_hr_6"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "Tenant level parameters cannot reference Namespace level parameters"

  # ── Cross-Context Parameter References (UC-CC-CR-*) ──────────────────────────

  Scenario: UC-CC-CR-1: DeployParameters to E2EParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_1"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "service_url"
    And the pipeline log shows "test_url"

  Scenario: UC-CC-CR-2: DeployParameters to TechnicalConfigurationParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_2"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "service_config"
    And the pipeline log shows "config_url"

  @xfail_cli_no_context_rule
  Scenario: UC-CC-CR-3: E2EParameters to DeployParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_3"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "e2eParameters"
    And the pipeline log shows "deployParameters"

  @xfail_cli_no_context_rule
  Scenario: UC-CC-CR-4: E2EParameters to TechnicalConfigurationParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_4"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "e2eParameters"
    And the pipeline log shows "technicalConfigurationParameters"

  @xfail_cli_no_context_rule
  Scenario: UC-CC-CR-5: TechnicalConfigurationParameters to DeployParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_5"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "technicalConfigurationParameters"
    And the pipeline log shows "deployParameters"

  Scenario: UC-CC-CR-6: TechnicalConfigurationParameters to E2EParameters Reference Error
    Given the workspace is initialized with test data from "e2e/uc_cc_cr_6"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "runtime_endpoint"
    And the pipeline log shows "e2e_endpoint"

  # ── Predefined Parameters (UC-CC-PD-*) ────────────────────────────────────────

  Scenario: UC-CC-PD-1: MANAGED_BY Defaults to argocd
    Given the workspace is initialized with test data from "e2e/uc_cc_pd_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "MANAGED_BY: argocd"

  # ── App Chart Validation (UC-CC-AV-*) ─────────────────────────────────────────

  # why: app chart validation is a documented calculator gate with zero coverage
  Scenario: UC-CC-AV-1: App Chart Validation Enabled Fails When Chart Component Absent
    Given the workspace is initialized with test data from "e2e/uc_cc_av_1"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline log shows "App chart validation failed"

  Scenario: UC-CC-AV-2: App Chart Validation Disabled Skips Chart Check
    Given the workspace is initialized with test data from "e2e/uc_cc_av_1"
    And the pipeline parameter "EFFECTIVE_SET_CONFIG" is set to "{\"version\":\"v2.0\",\"app_chart_validation\":\"false\"}"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully

  # ── Extra Parameters (UC-CC-EP-*) ─────────────────────────────────────────────

  # why: extra parameters are wired through the entrypoint; Requirement 14 presence is uncovered
  Scenario: UC-CC-EP-1: DEPLOYMENT_SESSION_ID Injected into Deployment Parameters
    Given the workspace is initialized with test data from "e2e/uc_cc_ep_1"
    And the pipeline parameter "DEPLOYMENT_SESSION_ID" is set to "550e8400-e29b-41d4-a716-446655440000"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "DEPLOYMENT_SESSION_ID: 550e8400-e29b-41d4-a716-446655440000"

  # ── No SBOMs Mode (UC-CC-NS-*) ─────────────────────────────────────────────────

  # why: No SBOMs Mode emits only pipeline and topology contexts; the mode is uncovered
  Scenario: UC-CC-NS-1: No SBOMs Mode Generates Only Pipeline And Topology Contexts
    Given the workspace is initialized with test data from "e2e/uc_cc_ns_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set context "pipeline" exists
    And the effective set context "topology" exists
    And the effective set context "deployment" does not exist
    And the effective set context "runtime" does not exist

  # ── Sensitive Parameter Splitting (UC-CC-SC-*) ────────────────────────────────

  # why: local sensitive split routes the secret to credentials.yaml, siblings stay in parameters
  Scenario: UC-CC-SC-1: creds.get Parameter Splits into Credentials File
    Given the workspace is initialized with test data from "e2e/uc_cc_sc_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "db_url: https://db.example.com"
    And the effective set deployment credentials contain "db_password:"
    And the effective set deployment parameters do not contain "db_password:"

  # why: the split is recursive - inside a nested map only the creds.get subfields move
  Scenario: UC-CC-SC-2: Nested Structure Splits Only Sensitive Subfields
    Given the workspace is initialized with test data from "e2e/uc_cc_sc_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "url: https://example.com"
    And the effective set deployment credentials contain "username:"
    And the effective set deployment parameters do not contain "password:"

  # ── Collision Handling (UC-CC-CO-*) ───────────────────────────────────────────

  # why: a deployParameter whose key equals a service name must move to the collision file
  Scenario: UC-CC-CO-1: Service-Named deployParameter Moved to Collision File
    Given the workspace is initialized with test data from "e2e/uc_cc_co_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And "test-app" is present in "collision-deployment-parameters.yaml" and absent from the root of "deployment-parameters.yaml"

  # ── Image Parameters (UC-CC-IM-*) ─────────────────────────────────────────────

  # why: an image parameter derived from a deploy_param SBOM property is uncovered
  Scenario: UC-CC-IM-1: deploy_param Yields Image Parameter
    Given the workspace is initialized with test data from "e2e/uc_cc_im_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters contain "MY_IMAGE_PARAM: registry.example.com/test/img:1.0.0"

  # ── Sort Order & DEPLOYMENT_SESSION_ID Consistency (UC-CC-SO-*) ───────────────

  # why: DEPLOYMENT_SESSION_ID must be identical across every effective-set file (Requirement 14)
  Scenario: UC-CC-SO-1: DEPLOYMENT_SESSION_ID Identical Across All Effective Set Files
    Given the workspace is initialized with test data from "e2e/uc_cc_so_1"
    And the pipeline parameter "DEPLOYMENT_SESSION_ID" is set to "550e8400-e29b-41d4-a716-446655440000"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the value of "DEPLOYMENT_SESSION_ID" is identical across all effective set files

  # why: parameters in every effective-set file must be sorted alphabetically (Requirement 13)
  Scenario: UC-CC-SO-2: Deployment Parameters Are Sorted Alphabetically
    Given the workspace is initialized with test data from "e2e/uc_cc_so_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters are sorted alphabetically

  # ── Composite/BG Topology Injection (UC-CC-TP-*) ──────────────────────────────
  # Target contract per issue #1691 - the calculator does not yet derive ORIGIN_NAMESPACE,
  # PEER_NAMESPACE, CONTROLLER_NAMESPACE and BASELINE_* deployment parameters from
  # composite_structure.yml/bg_domain.yml (CliParameterParser only passes them through as raw
  # topology objects), so these scenarios are pinned xfail-strict until #1691 lands.

  # why: #1691 Case 1 - composite baseline-only topology, per-namespace injection (target state)
  @xfail_topology_1691
  Scenario: UC-CC-TP-1: Composite Baseline-Only Topology Injects Baseline Namespace Parameters
    Given the workspace is initialized with test data from "e2e/uc_cc_tp_1"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters for namespace "dev-1-core" contain "ORIGIN_NAMESPACE: dev-1-core"
    And the effective set deployment parameters for namespace "dev-1-core" do not contain "PEER_NAMESPACE"
    And the effective set deployment parameters for namespace "dev-1-core" do not contain "CONTROLLER_NAMESPACE"
    And the effective set deployment parameters for namespace "dev-1-core" do not contain "BASELINE_ORIGIN"

  # why: #1691 Case 2 - composite baseline plus plain satellites, baseline references injected (target state)
  @xfail_topology_1691
  Scenario: UC-CC-TP-2: Composite With Satellites Injects Baseline References
    Given the workspace is initialized with test data from "e2e/uc_cc_tp_2"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    And the effective set deployment parameters for namespace "dev-1-core" do not contain "BASELINE_ORIGIN"
    And the effective set deployment parameters for namespace "dev-1-oss" contain "BASELINE_ORIGIN: dev-1-core"
    And the effective set deployment parameters for namespace "dev-1-oss" do not contain "BASELINE_CONTROLLER"
    And the effective set deployment parameters for namespace "dev-1-oss" do not contain "BASELINE_PEER"
    And the effective set deployment parameters for namespace "dev-1-bss" contain "BASELINE_ORIGIN: dev-1-core"

  # why: #1691 Case 3 - Blue-Green domain in a satellite, full per-namespace parameter table (target state)
  @xfail_topology_1691
  Scenario: UC-CC-TP-3: Blue-Green Domain In A Satellite Injects Per-Namespace Parameters
    Given the workspace is initialized with test data from "e2e/uc_cc_tp_3"
    When the unified pipeline orchestrator runs
    Then the effective set is generated successfully
    # baseline, plain namespace
    And the effective set deployment parameters for namespace "dev-1-core" contain "ORIGIN_NAMESPACE: dev-1-core"
    And the effective set deployment parameters for namespace "dev-1-core" do not contain "PEER_NAMESPACE"
    And the effective set deployment parameters for namespace "dev-1-core" do not contain "BASELINE_ORIGIN"
    # satellite BG origin
    And the effective set deployment parameters for namespace "dev-1-bss-origin" contain "ORIGIN_NAMESPACE: dev-1-bss-origin"
    And the effective set deployment parameters for namespace "dev-1-bss-origin" contain "PEER_NAMESPACE: dev-1-bss-peer"
    And the effective set deployment parameters for namespace "dev-1-bss-origin" contain "CONTROLLER_NAMESPACE: dev-1-controller"
    And the effective set deployment parameters for namespace "dev-1-bss-origin" contain "BASELINE_ORIGIN: dev-1-core"
    And the effective set deployment parameters for namespace "dev-1-bss-origin" do not contain "BASELINE_CONTROLLER"
    # satellite BG peer shares origin, peer and controller with origin
    And the effective set deployment parameters for namespace "dev-1-bss-peer" contain "ORIGIN_NAMESPACE: dev-1-bss-origin"
    And the effective set deployment parameters for namespace "dev-1-bss-peer" contain "PEER_NAMESPACE: dev-1-bss-peer"
    And the effective set deployment parameters for namespace "dev-1-bss-peer" contain "CONTROLLER_NAMESPACE: dev-1-controller"
    # controller namespace, carries the bluegreen-controller parameters
    And the effective set deployment parameters for namespace "dev-1-controller" contain "ORIGIN_NAMESPACE: dev-1-bss-origin"
    And the effective set deployment parameters for namespace "dev-1-controller" contain "BASELINE_ORIGIN: dev-1-core"
    And the effective set deployment parameters for namespace "dev-1-controller" contain "BG_CONTROLLER_LOGIN:"
    # plain satellite
    And the effective set deployment parameters for namespace "dev-1-oss" contain "ORIGIN_NAMESPACE: dev-1-oss"
    And the effective set deployment parameters for namespace "dev-1-oss" contain "BASELINE_ORIGIN: dev-1-core"
    And the effective set deployment parameters for namespace "dev-1-oss" do not contain "CONTROLLER_NAMESPACE"
