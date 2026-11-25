Feature: EnvPrepareReport job artifact
  As an upstream orchestration pipeline
  I want a machine-readable report from the env_prepare job
  So that I can aggregate operation status without parsing logs

  Scenario: A single-environment run publishes the report when artifacts are otherwise disabled
    Given the pipeline parameter "SAVE_ARTIFACTS_STRATEGY" is set to "NEVER"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the env_prepare report is published
    And the env_prepare report has kind "EnvPrepareReport" and apiVersion "v1"
    And the env_prepare report contains a skipped step named "env_build" without a time

  Scenario: A completed step reports its duration in the report
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the env_prepare report contains a step named "copy_env_artifact" with a time in "H:MM:SS" format

  Scenario: A failed step still publishes failed and skipped results
    Given the pipeline parameter "ENV_TEMPLATE_VERSION" is set to "broken-version"
    When the unified pipeline orchestrator runs
    Then the orchestrator fails
    And the env_prepare report is published
    And the env_prepare report contains a failed step named "set_template_version"
    And the env_prepare report contains a skipped step named "env_build" without a time

  Scenario: The report survives artifact size-limit trimming
    Given the pipeline parameter "ARTIFACT_SIZE_LIMIT_MB" is set to "0"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the env_prepare report is published
    And the published artifacts were trimmed

  Scenario: The report steps match the Metrics Collector activity record
    Given Metrics Collector is configured
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the env_prepare report steps match the Metrics Collector activity record

  Scenario: A report write error does not change the pipeline outcome
    Given the env_prepare report path is occupied by a directory
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the pipeline log contains "Failed to write EnvPrepareReport artifact"

  Scenario: A multi-environment fan-out does not publish a single-environment report
    Given the pipeline uses multiple environment names
    When the unified pipeline orchestrator runs
    Then the env_prepare report is not published
