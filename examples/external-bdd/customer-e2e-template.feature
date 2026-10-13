Feature: Customer E2E Test Scenarios
  As an implementation engineer
  I want to run automated tests on my project configurations
  So that I can catch errors before deploying to production

  # ----------------------------------------------------------------------
  # Example 1: Successful Pipeline Execution
  # This scenario tests a happy path where all inputs are correct,
  # the pipeline succeeds, and the output matches our "golden" reference.
  # ----------------------------------------------------------------------
  Scenario: UC-PROJ-001: Successful Environment Generation
    # 1. Initialize the workspace by copying the contents of "test_data/e2e/base_proj"
    Given the workspace is initialized with test data from "e2e/base_proj"
    
    # 2. Set the environment variables exactly as the CI runner would
    And the pipeline parameter "ENV_NAMES" is set to "prod-cluster/backend-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    
    # 3. Trigger the EnvGene pipeline orchestrator
    When the unified pipeline orchestrator runs
    
    # 4. Assert the result
    Then the orchestrator completes successfully
    # Recursively compare the generated environment instance against the golden reference
    And the environment instance "prod-cluster/backend-env" matches the reference "golden/ref-proj-001"

  # ----------------------------------------------------------------------
  # Example 2: Expected Pipeline Failure
  # This scenario verifies that the pipeline correctly catches invalid
  # configurations (e.g., missing required variables) and fails safely.
  # ----------------------------------------------------------------------
  Scenario: UC-PROJ-002: Validation Failure on Missing Configuration
    Given the workspace is initialized with test data from "e2e/invalid_config"
    And the pipeline parameter "ENV_NAMES" is set to "prod-cluster/broken-env"
    And the pipeline parameter "GENERATE_EFFECTIVE_SET" is set to "true"
    When the unified pipeline orchestrator runs
    # We expect the pipeline to fail with a non-zero exit code
    Then the orchestrator fails

  # ----------------------------------------------------------------------
  # Example 3: Custom Project-Specific Checks
  # This scenario uses the built-in steps for execution, but uses a
  # CUSTOM step definition (written by you in Python) for the assertion.
  # ----------------------------------------------------------------------
  Scenario: UC-PROJ-003: Custom Assertion for Project Specific File
    Given the workspace is initialized with test data from "e2e/base_proj"
    And the pipeline parameter "ENV_NAMES" is set to "dev-cluster/frontend-env"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    # This step is NOT built-in. It must be defined in your steps_template.py!
    And a project-specific audit file is created at "dev-cluster/frontend-env"
