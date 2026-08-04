Feature: Artifact Downloading
  As an EnvGene pipeline
  I want to download SD, DD, and Environment Template artifacts from various registries
  So that the pipeline has the artifacts required for environment processing

  Background:
    Given the pipeline has ENV_BUILD set to "false"

  # ── SD/DD Artifact Download ───────────────────────────────────────────────────

  Scenario: UC-AD-SD-1: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v1)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_1"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "artifactory-maven-v1"
    And the artifact download log contains authentication attempt with credentials "artifactory-creds"

  Scenario: UC-AD-SD-2: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v1)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_2"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "artifactory-maven-anon-v1"
    And the artifact download proceeds without authentication headers

  Scenario: UC-AD-SD-3: Download SD from Nexus with User/Password (AppDef v1 + RegDef v1)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_3"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "nexus-maven-v1"
    And the artifact download log contains authentication attempt with credentials "nexus-creds"

  Scenario: UC-AD-SD-4: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v1)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_4"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "nexus-maven-anon-v1"
    And the artifact download proceeds without authentication headers

  Scenario: UC-AD-SD-5: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_5"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "artifactory-maven-v2"
    And the artifact download log contains authentication attempt with credentials "artifactory-creds-v2"

  Scenario: UC-AD-SD-6: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_6"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "artifactory-anon-v2"
    And the artifact download proceeds without authentication headers

  Scenario: UC-AD-SD-7: Download SD from Nexus with User/Password (AppDef v1 + RegDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_7"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "nexus-maven-v2"
    And the artifact download log contains authentication attempt with credentials "nexus-creds-v2"

  Scenario: UC-AD-SD-8: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_8"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "nexus-anon-v2"
    And the artifact download proceeds without authentication headers

  @xfail
  Scenario: UC-AD-SD-9: Download SD from AWS CodeArtifact with Secret (AppDef v1 + RegDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_9"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "aws-codeartifact"
    And the artifact download log contains AWS authentication attempt

  @xfail
  Scenario: UC-AD-SD-10: Download SD from GCP Artifact Registry with Service Account (AppDef v1 + RegDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_10"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "gcp-artifact-registry"
    And the artifact download log contains GCP authentication attempt

  Scenario: UC-AD-SD-11: Download Specific Version SD
    Given the workspace is initialized with test data from "e2e/uc_ad_sd_11"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log shows version "1.0.0" was requested

  # ── Environment Template Artifact Download ────────────────────────────────────

  Scenario: UC-AD-ENV-9: Download Template from Artifactory with GAV notation
    Given the workspace is initialized with test data from "e2e/uc_ad_env_9"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "artifactory-maven"
    And the artifact download log contains GAV coordinates "org.test:project-env-template:v1.2.3"

  Scenario: UC-AD-ENV-10: Download Template from Artifactory with GAV notation and Anonymous Access
    Given the workspace is initialized with test data from "e2e/uc_ad_env_10"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "artifactory-maven-anon"
    And the artifact download proceeds without authentication headers

  Scenario: UC-AD-ENV-11: Download Template from Nexus with GAV notation
    Given the workspace is initialized with test data from "e2e/uc_ad_env_11"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "nexus-maven"
    And the artifact download log contains GAV coordinates "org.test:project-env-template:v1.2.3"

  Scenario: UC-SC-NEX-1: Download template artifact from Nexus with custom CA certificate
    Given the workspace is initialized with test data from "e2e/uc_sc_nex_1"
    And the CA certificate file exists at "configuration/certs/internal-ca.pem"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "nexus-maven"
    And no TLS certificate verification errors appear in the logs

  Scenario: UC-AD-ENV-12: Download Template from Nexus with GAV notation and Anonymous Access
    Given the workspace is initialized with test data from "e2e/uc_ad_env_12"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains registry resolution for "nexus-maven-anon"
    And the artifact download proceeds without authentication headers

  Scenario: UC-AD-ENV-13: Download Template with app ver notation from Artifactory (ArtDef v1)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_13"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download log contains authentication attempt with credentials "artifactory-creds"

  Scenario: UC-AD-ENV-14: Download Template with app ver notation from Artifactory and Anonymous Access (ArtDef v1)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_14"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download proceeds without authentication headers

  Scenario: UC-AD-ENV-15: Download Template with app ver notation from Nexus (ArtDef v1)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_15"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download log contains authentication attempt with credentials "nexus-creds"

  Scenario: UC-AD-ENV-16: Download Template with app ver notation from Nexus and Anonymous Access (ArtDef v1)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_16"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download proceeds without authentication headers

  Scenario: UC-AD-ENV-17: Download Template from Artifactory with app ver notation (ArtDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_17"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download log contains authentication attempt with credentials "artifactory-creds-v2"

  Scenario: UC-AD-ENV-18: Download Template from Artifactory with app ver notation and Anonymous Access (ArtDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_18"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download proceeds without authentication headers

  Scenario: UC-AD-ENV-19: Download Template from Nexus with app ver notation (ArtDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_19"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download log contains authentication attempt with credentials "nexus-creds-v2"

  Scenario: UC-AD-ENV-20: Download Template from Nexus with app ver notation and Anonymous Access (ArtDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_20"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download proceeds without authentication headers

  @xfail
  Scenario: UC-AD-ENV-21: Download Template from AWS CodeArtifact with app ver notation (ArtDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_21"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download log contains AWS authentication attempt

  @xfail
  Scenario: UC-AD-ENV-22: Download Template from GCP Artifact Registry with app ver notation (ArtDef v2)
    Given the workspace is initialized with test data from "e2e/uc_ad_env_22"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log contains artifact definition resolution for "project-env-template"
    And the artifact download log contains GCP authentication attempt

  Scenario: UC-AD-ENV-23: Download SNAPSHOT Template Version
    Given the workspace is initialized with test data from "e2e/uc_ad_env_23"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log shows version "1.0.0-SNAPSHOT" was requested

  Scenario: UC-AD-ENV-24: Download Specific Template Version
    Given the workspace is initialized with test data from "e2e/uc_ad_env_24"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline completes with artifact download attempted
    And the artifact download log shows version "2.5.1" was requested

  # ── Error Handling ────────────────────────────────────────────────────────────

  Scenario: UC-AD-ERR-1: Handle Missing Application Definition
    Given the workspace is initialized with test data from "e2e/uc_ad_err_1"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "non-existent-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline logs contain a missing definition error for "non-existent-app"

  Scenario: UC-AD-ERR-2: Handle Missing Registry Definition
    Given the workspace is initialized with test data from "e2e/uc_ad_err_2"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline logs contain a missing definition error for "missing-registry"

  Scenario: UC-AD-ERR-3: Handle Authentication Failure
    Given the workspace is initialized with test data from "e2e/uc_ad_err_3"
    And the pipeline parameter "SD_SOURCE_TYPE" is set to "artifact"
    And the pipeline parameter "SD_VERSION" is set to "sd-app:1.0.0"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline logs contain an artifact download failure message

  Scenario: UC-AD-ERR-4: Handle Missing Artifact Definition
    Given the workspace is initialized with test data from "e2e/uc_ad_err_4"
    And the pipeline parameter "ENV_BUILDER" is set to "true"
    When the unified pipeline orchestrator runs
    Then the pipeline fails
    And the pipeline logs contain a missing definition error for "non-existent-template"
