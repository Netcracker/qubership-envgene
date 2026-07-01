Feature: Cluster Endpoint Information in Topology Context Test Cases
  As an EnvGene developer
  I want to ensure cluster endpoint information is correctly populated in the topology context
  So that deployments have the correct cluster API and public URLs

  Scenario: TC-CETC-001: Cluster Endpoint Information with Cloud Passport
    Given the workspace is initialized with test data from "test_environments"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-with-passport"
    And the pipeline parameter "CALCULATOR_CLI" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the topology context in "parameters.yaml" contains a cluster object with values:
      | API_url                             | API_port | public_url                          | protocol |
      | API.cl-01.managed.qubership.cloud   | 6443     | apps.cl-01.managed.qubership.cloud  | https    |

  Scenario: TC-CETC-002: Cluster Endpoint Information without Cloud Passport
    Given the workspace is initialized with test data from "test_environments"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-without-passport"
    And the pipeline parameter "CALCULATOR_CLI" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the topology context in "parameters.yaml" contains a cluster object with values:
      | API_url                             | API_port | public_url                          | protocol |
      | API.cl-03.managed.qubership.cloud   | 6443     | apps.cl-03.managed.qubership.cloud  | https    |

  Scenario: TC-CETC-003: Cluster Endpoint Information with Non-Standard Port
    Given the workspace is initialized with test data from "test_environments"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-nonstandard-port"
    And the pipeline parameter "CALCULATOR_CLI" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the topology context in "parameters.yaml" contains a cluster object with values:
      | API_url                             | API_port | public_url                          | protocol |
      | API.cl-03.managed.qubership.cloud   | 8443     | apps.cl-03.managed.qubership.cloud  | https    |

  Scenario: TC-CETC-004: Cluster Endpoint Information with HTTP Protocol
    Given the workspace is initialized with test data from "test_environments"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-http-protocol"
    And the pipeline parameter "CALCULATOR_CLI" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the topology context in "parameters.yaml" contains a cluster object with values:
      | API_url                             | API_port | public_url                          | protocol |
      | API.cl-03.managed.qubership.cloud   | 6443     | apps.cl-03.managed.qubership.cloud  | http     |

  Scenario: TC-CETC-005: Cluster Endpoint Information with Non-Standard Hostname
    Given the workspace is initialized with test data from "test_environments"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-nonstandard-hostname"
    And the pipeline parameter "CALCULATOR_CLI" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the topology context in "parameters.yaml" contains a cluster object with values:
      | API_url                             | API_port | public_url                          | protocol |
      | cluster.cl-03.managed.qubership.cloud | 6443     | cluster.cl-03.managed.qubership.cloud | https    |

  Scenario: TC-CETC-006: Cluster Endpoint Information with Cloud Passport Overriding clusterUrl
    Given the workspace is initialized with test data from "test_environments"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-passport-override"
    And the pipeline parameter "CALCULATOR_CLI" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the topology context in "parameters.yaml" contains a cluster object with values:
      | API_url                             | API_port | public_url                          | protocol |
      | API.cl-01.managed.qubership.cloud   | 443      | apps.cl-01.managed.qubership.cloud  | https    |

  Scenario: TC-CETC-007: Missing Cluster Information
    Given the workspace is initialized with test data from "test_environments"
    And the pipeline parameter "ENV_NAMES" is set to "cluster01/env-missing-cluster-info"
    And the pipeline parameter "CALCULATOR_CLI" is set to "true"
    When the unified pipeline orchestrator runs
    Then the orchestrator completes successfully
    And the topology context in "parameters.yaml" contains a cluster object with values:
      | API_url | API_port | public_url | protocol |
      |         |          |            |          |
