Feature: CLEAN sub-flows - clean.md
  As an EnvGene pipeline orchestrator
  I want to run the CLEAN operation against a whole environment or a subset of its namespaces
  So that downstream tooling can undeploy the marked namespaces from the effective set, while a
  Blue-Green side namespace is cleaned like any other namespace and the deploy plan reflects only
  what remains

  Background:
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy"
    And the pipeline parameter "PIPELINE_TYPE" is set to "GITLAB_DEPLOY"
    And the pipeline parameter "OPERATION_TYPE" is set to "CLEAN"

  # ── CLEAN a whole environment ─────────────────────────────────────────────────
  # NAMESPACE_NAMES is empty, so every namespace of the environment is cleaned and the
  # repository deploy plan is reduced to nothing.

  Scenario: CLEAN a whole environment marks every namespace as cleaned and empties the deploy plan
    # NAMESPACE_NAMES is intentionally not set here - an absent value is equivalent to the
    # empty-string value from the launch parameters table (both are falsy to reduce_deployment_plan
    # and set_cleaned_mark), and the shared "pipeline parameter ... is set to" step cannot express
    # an empty quoted value (parsers.parse requires at least one character for "{value}").
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "process_deployment_plan" has status "SUCCESS"
    And the pipeline step "env_build" has status "SUCCESS"
    And the pipeline step "generate_effective_set" has status "SUCCESS"
    And the pipeline step "git_commit" has status "SUCCESS"
    And the pipeline step "deploy_postfix_namespace_map" has status "SKIPPED"
    And the pipeline step "warmup" has status "SKIPPED"
    And the pipeline step "change_bg_state" has status "SKIPPED"
    And the namespace "core" is marked as cleaned
    And the namespace "bss-origin" is marked as cleaned
    And the namespace "bss-peer" is marked as cleaned
    And the deploy plan is empty

  # ── CLEAN selected namespaces ───────────────────────────────────────────────────
  # NAMESPACE_NAMES lists the namespaces to clean; reduce_deployment_plan removes only the
  # matching entries and set_cleaned_mark only marks the listed namespaces.

  Scenario: CLEAN selected namespaces marks only the listed namespaces and leaves the rest of the plan
    Given the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core;test-env-bss-peer"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "core" is marked as cleaned
    And the namespace "bss-peer" is marked as cleaned
    And the namespace "bss-origin" is not marked as cleaned
    And the deploy plan does not contain an entry for namespace "test-env-core"
    And the deploy plan does not contain an entry for namespace "test-env-bss-peer"
    And the deploy plan contains 1 entry

  # A Blue-Green side namespace (origin or peer) is cleaned as any other namespace; the other
  # side and the BG state files are not touched - CLEAN is not a state operation.

  Scenario: CLEAN of a single Blue-Green side namespace leaves the other side and the BG state untouched
    Given the BG state files are origin "active" and peer "idle"
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-bss-origin"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "bss-origin" is marked as cleaned
    And the namespace "bss-peer" is not marked as cleaned
    And the namespace "core" is not marked as cleaned
    And the BG state files are origin "active" and peer "idle"
    And the deploy plan does not contain an entry for namespace "test-env-bss-origin"
    And the deploy plan contains 2 entries

  # bdg-test's "controller" namespace is COMMON-role (it names neither the BG Domain's
  # originNamespace nor peerNamespace), so it is cleaned like "core" - not like the BG sides -
  # and it carries no deploy-plan.yml entry of its own in this fixture, so reducing the plan for
  # it is a no-op.

  Scenario: CLEAN of the BG controller namespace leaves the origin/peer namespaces and the BG state untouched
    Given the BG state files are origin "active" and peer "idle"
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-controller"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "controller" is marked as cleaned
    And the namespace "bss-origin" is not marked as cleaned
    And the namespace "bss-peer" is not marked as cleaned
    And the namespace "core" is not marked as cleaned
    And the BG state files are origin "active" and peer "idle"
    And the deploy plan contains 3 entries

  # ── CLEAN error case ────────────────────────────────────────────────────────────
  # set_cleaned_mark (build_env.py) fails fast instead of silently skipping a namespace name
  # that names nothing in the rendered environment.

  Scenario: CLEAN fails when a named namespace does not exist
    Given the pipeline parameter "NAMESPACE_NAMES" is set to "does-not-exist"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline step "env_build" has status "FAILED"
    And the pipeline log contains "does-not-exist"

  # ── CLEAN without a Blue-Green Domain ───────────────────────────────────────────
  # CLEAN does not require a Blue-Green Domain at all: an env_template with no bg_domain
  # renders a plain set of namespaces (no origin/peer split), and CLEAN behaves exactly the
  # same as the BGD scenarios above minus the BG-side bookkeeping.

  Scenario: CLEAN a whole environment without a Blue-Green Domain marks every namespace as cleaned and empties the deploy plan
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy_no_bgd"
    # NAMESPACE_NAMES is intentionally not set here - see the equivalent BGD scenario above.
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline step "process_deployment_plan" has status "SUCCESS"
    And the pipeline step "env_build" has status "SUCCESS"
    And the pipeline step "generate_effective_set" has status "SUCCESS"
    And the pipeline step "git_commit" has status "SUCCESS"
    And the pipeline step "deploy_postfix_namespace_map" has status "SKIPPED"
    And the pipeline step "warmup" has status "SKIPPED"
    And the pipeline step "change_bg_state" has status "SKIPPED"
    And the namespace "core" is marked as cleaned
    And the namespace "bss" is marked as cleaned
    And the deploy plan is empty

  Scenario: CLEAN selected namespaces without a Blue-Green Domain marks only the listed namespace and leaves the rest of the plan
    Given the workspace is initialized with test data from "e2e/uc_clean_deploy_no_bgd"
    And the pipeline parameter "NAMESPACE_NAMES" is set to "test-env-core"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the namespace "core" is marked as cleaned
    And the namespace "bss" is not marked as cleaned
    And the deploy plan does not contain an entry for namespace "test-env-core"
    And the deploy plan contains 1 entry
