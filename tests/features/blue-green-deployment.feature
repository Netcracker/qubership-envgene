Feature: Blue-Green Deployment State Management
  As an EnvGene orchestrator
  I want to transition state files between origin and peer namespaces
  So that blue-green deployment works correctly

  Scenario: UC-BG-1: Init Domain
    Given Blue-Green state files are not created
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Init Domain"
    Then the Blue-Green state files become ".origin-active" and ".peer-idle"

  Scenario: UC-BG-2: Warmup
    Given Blue-Green state files ".origin-active" and ".peer-idle" exist
    And Origin namespace "origin-ns" and peer namespace "peer-ns" exist with different contents
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Warmup"
    Then the Blue-Green state files become ".origin-active" and ".peer-candidate"
    And Origin namespace "origin-ns" and peer namespace "peer-ns" have the same content

  Scenario: UC-BG-3: Promote
    Given Blue-Green state files ".origin-active" and ".peer-candidate" exist
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Promote"
    Then the Blue-Green state files become ".origin-legacy" and ".peer-active"

  Scenario: UC-BG-4: Commit
    Given Blue-Green state files ".origin-legacy" and ".peer-active" exist
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Commit"
    Then the Blue-Green state files become ".origin-idle" and ".peer-active"

  Scenario: UC-BG-5: Rollback
    Given Blue-Green state files ".origin-legacy" and ".peer-active" exist
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Rollback"
    Then the Blue-Green state files become ".origin-idle" and ".peer-active"

  Scenario: UC-BG-6: Reverse Warmup
    Given Blue-Green state files ".origin-idle" and ".peer-active" exist
    And Origin namespace "origin-ns" and peer namespace "peer-ns" exist with different contents
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Reverse Warmup"
    Then the Blue-Green state files become ".origin-candidate" and ".peer-active"
    And Origin namespace "peer-ns" and peer namespace "origin-ns" have the same content

  Scenario: UC-BG-7: Reverse Promote
    Given Blue-Green state files ".origin-candidate" and ".peer-active" exist
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Reverse Promote"
    Then the Blue-Green state files become ".origin-active" and ".peer-legacy"

  Scenario: UC-BG-8: Reverse Commit
    Given Blue-Green state files ".origin-active" and ".peer-legacy" exist
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Reverse Commit"
    Then the Blue-Green state files become ".origin-active" and ".peer-idle"

  Scenario: UC-BG-9: Reverse Rollback
    Given Blue-Green state files ".origin-active" and ".peer-legacy" exist
    When the Instance pipeline is started with BG_MANAGE=true and BG_STATE for "Reverse Rollback"
    Then the Blue-Green state files become ".origin-active" and ".peer-idle"
