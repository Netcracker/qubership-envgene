Feature: Effective Set Generation - No-SD Mode
  As an EnvGene developer
  I want to ensure that when no SD is provided and no Full SD exists
  Only the topology and pipeline contexts are generated (No-SD Mode)
  So that a minimal effective set can be produced without application data

  # NOTE: @xfail because ENV_BUILD=true triggers beautifyYaml → jschon_tools.process_json_doc
  # which is missing from the installed jschon_tools package (known environment issue).
  # The test is written to match documented No-SD Mode behavior and will pass once
  # jschon_tools is updated.
  @xfail
  Scenario: UC-ES-NOSBOM-1: Only Pipeline and Topology contexts generated
    Given the workspace is initialized with test data from "e2e/base"
    And the pipeline parameter "ENV_NAMES" is set to "test-cluster/test-env"
    And the pipeline parameter "ENV_BUILD" is set to "true"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the effective set contains only topology and pipeline contexts
