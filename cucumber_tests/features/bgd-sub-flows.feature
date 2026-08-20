Feature: BGD sub-flows - bgd-sub-flows.md
  As an EnvGene pipeline orchestrator
  I want to run the correct subset of pipeline steps for each Blue-Green Deployment operation
  So that state-only operations stay cheap, warmup replicates the active namespace, and a
  regular deploy can target either the active or the candidate physical side

  Background:
    Given the workspace is initialized with test data from "e2e/uc_bgd_state"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"

  # ── Sub-flow 1 - BGD state operations ─────────────────────────────────────────
  # init-domain, promote, rollback and commit only flip the BG state files; the
  # deployment plan and the effective set are not touched.

  Scenario: Sub-flow 1 - init-domain flips the BG state without touching the deploy plan
    Given the pipeline parameter "OPERATION_TYPE" is set to "BGD"
    And the pipeline parameter "BGD_OPERATION" is set to "init-domain"
    And the pipeline parameter "BG_STATE" targets origin "active" and peer "idle"
    And the deploy plan is recorded as a baseline
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the BG state files are origin "active" and peer "idle"
    And the deploy plan file is unchanged
    And the pipeline step "change_bg_state" has status "SUCCESS"
    And the pipeline step "warmup" has status "SKIPPED"
    And the pipeline step "deploy_postfix_namespace_map" has status "SKIPPED"
    And the pipeline step "process_deployment_plan" has status "SKIPPED"
    And the pipeline step "env_build" has status "SKIPPED"
    And the pipeline step "generate_effective_set" has status "SKIPPED"
    And the pipeline step "git_commit" has status "SUCCESS"
    # Not part of the documented flow for this sub-flow, but this is real, current
    # orchestrator behaviour: appregdef_render runs on every GITLAB_DEPLOY run
    # regardless of OPERATION_TYPE. Pinned here so a change either way is caught.
    And the pipeline step "appregdef_render" has status "SUCCESS"

  Scenario: Sub-flow 1 - promote flips origin to legacy and peer to active
    Given the BG state files are origin "active" and peer "candidate"
    And the pipeline parameter "OPERATION_TYPE" is set to "BGD"
    And the pipeline parameter "BGD_OPERATION" is set to "promote"
    And the pipeline parameter "BG_STATE" targets origin "legacy" and peer "active"
    And the deploy plan is recorded as a baseline
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the BG state files are origin "legacy" and peer "active"
    And the deploy plan file is unchanged
    And the pipeline step "generate_effective_set" has status "SKIPPED"

  Scenario: Sub-flow 1 - rollback reverts origin to idle after a failed promotion
    Given the BG state files are origin "legacy" and peer "active"
    And the pipeline parameter "OPERATION_TYPE" is set to "BGD"
    And the pipeline parameter "BGD_OPERATION" is set to "rollback"
    And the pipeline parameter "BG_STATE" targets origin "idle" and peer "active"
    And the deploy plan is recorded as a baseline
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the BG state files are origin "idle" and peer "active"
    And the deploy plan file is unchanged
    And the pipeline step "generate_effective_set" has status "SKIPPED"

  Scenario: Sub-flow 1 - commit settles origin to idle after a successful promotion
    Given the BG state files are origin "legacy" and peer "active"
    And the pipeline parameter "OPERATION_TYPE" is set to "BGD"
    And the pipeline parameter "BGD_OPERATION" is set to "commit"
    And the pipeline parameter "BG_STATE" targets origin "idle" and peer "active"
    And the deploy plan is recorded as a baseline
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the BG state files are origin "idle" and peer "active"
    And the deploy plan file is unchanged
    And the pipeline step "generate_effective_set" has status "SKIPPED"

  # ── Sub-flow 2 - BGD warmup ────────────────────────────────────────────────────
  # warmup replicates the active namespace into the candidate and generates the
  # effective set over the copy; env_build deliberately does not fire because
  # there is nothing new to render.

  Scenario: Sub-flow 2 - warmup replicates the active namespace into the candidate
    Given the workspace is initialized with test data from "e2e/uc_bgd_warmup"
    And the BG state files are origin "active" and peer "idle"
    And the pipeline parameter "OPERATION_TYPE" is set to "BGD"
    And the pipeline parameter "BGD_OPERATION" is set to "warmup"
    And the pipeline parameter "BG_STATE" targets origin "active" and peer "candidate"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the BG state files are origin "active" and peer "candidate"
    And the pipeline step "warmup" has status "SUCCESS"
    And the pipeline step "env_build" has status "SKIPPED"
    And the pipeline step "generate_effective_set" has status "SUCCESS"
    # Not part of the documented flow for this sub-flow either, but real current behaviour.
    And the pipeline step "appregdef_render" has status "SUCCESS"
    And the namespace "bss-peer" application "crm" deploy parameter "PARAM_1" equals "active-value"
    And the namespace directories "bss-origin" and "bss-peer" have identical content except the namespace name
    And the environment inventory field "envTemplate.bgNsArtifacts.peer" equals "test-artifact:v1"
    And the deploy plan contains an entry for namespace "test-env-bss-peer" with version "crm:1.0"

  # ── Sub-flow 3 - deploy to active or candidate ────────────────────────────────
  # A regular DEPLOY scoped by BG_NS_TARGET. Unlike warmup this is the full deploy
  # chain, including env_build, and it deploys the versions from
  # APPLICATION_VERSIONS rather than a copy of the active side.

  Scenario: Sub-flow 3 - deploy targets the origin namespace when BG_NS_TARGET is ORIGIN
    Given the workspace is initialized with test data from "e2e/uc_bgd_deploy"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "BG_NS_TARGET" is set to "ORIGIN"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to "bss-origin:app1:1.0"
    And the pipeline parameter "LOCAL_APPDEFS_PATH" is set to "environments/test-cluster/test-env/AppDefs"
    And the pipeline parameter "LOCAL_REGDEFS_PATH" is set to "environments/test-cluster/test-env/RegDefs"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "env_build" has status "SUCCESS"
    And the pipeline step "generate_effective_set" has status "SUCCESS"
    And the namespace map contains "bss" bound to "bss-origin"
    And the deploy plan contains an entry for namespace "bss-origin" with version "app1:1.0"

  Scenario: Sub-flow 3 - deploy targets the peer namespace when BG_NS_TARGET is PEER
    Given the workspace is initialized with test data from "e2e/uc_bgd_deploy"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "BG_NS_TARGET" is set to "PEER"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to "bss-peer:app1:1.0"
    And the pipeline parameter "LOCAL_APPDEFS_PATH" is set to "environments/test-cluster/test-env/AppDefs"
    And the pipeline parameter "LOCAL_REGDEFS_PATH" is set to "environments/test-cluster/test-env/RegDefs"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "env_build" has status "SUCCESS"
    And the pipeline step "generate_effective_set" has status "SUCCESS"
    And the namespace map contains "bss" bound to "bss-peer"
    And the deploy plan contains an entry for namespace "bss-peer" with version "app1:1.0"

  Scenario: Sub-flow 3 - deploy fails when APPLICATION_VERSIONS targets a namespace BG_NS_TARGET did not resolve
    # BG_NS_TARGET gates which physical side gets rendered into namespace-map.yml
    # (see "the namespace map contains ..." above). An explicit namespace in
    # APPLICATION_VERSIONS that belongs to the other, unresolved side has no
    # entry to bind against and the deployment plan step fails loudly instead of
    # silently deploying to the wrong side.
    Given the workspace is initialized with test data from "e2e/uc_bgd_deploy"
    And the pipeline parameter "OPERATION_TYPE" is set to "DEPLOY"
    And the pipeline parameter "BG_NS_TARGET" is set to "PEER"
    And the pipeline parameter "APPLICATION_VERSIONS" is set to "bss-origin:app1:1.0"
    And the pipeline parameter "LOCAL_APPDEFS_PATH" is set to "environments/test-cluster/test-env/AppDefs"
    And the pipeline parameter "LOCAL_REGDEFS_PATH" is set to "environments/test-cluster/test-env/RegDefs"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline step "process_deployment_plan" has status "FAILED"
    And the pipeline log contains "KeyError: 'bss-origin'"
