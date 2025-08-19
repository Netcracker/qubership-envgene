# Cluster Endpoint Information in Topology Context Test Cases

- [Cluster Endpoint Information in Topology Context Test Cases](#cluster-endpoint-information-in-topology-context-test-cases)
  - [TC-CETC-001: Cluster Endpoint Information with Cloud Passport](#tc-cetc-001-cluster-endpoint-information-with-cloud-passport)
  - [TC-CETC-002: Cluster Endpoint Information without Cloud Passport](#tc-cetc-002-cluster-endpoint-information-without-cloud-passport)
  - [TC-CETC-003: Cluster Endpoint Information with Non-Standard Port](#tc-cetc-003-cluster-endpoint-information-with-non-standard-port)
  - [TC-CETC-004: Cluster Endpoint Information with HTTP Protocol](#tc-cetc-004-cluster-endpoint-information-with-http-protocol)
  - [TC-CETC-005: Cluster Endpoint Information with Non-Standard Hostname](#tc-cetc-005-cluster-endpoint-information-with-non-standard-hostname)
  - [TC-CETC-006: Cluster Endpoint Information with Cloud Passport Overriding clusterUrl](#tc-cetc-006-cluster-endpoint-information-with-cloud-passport-overriding-clusterurl)
  - [TC-CETC-007: Missing Cluster Information](#tc-cetc-007-missing-cluster-information)

Test Cases for Cluster Endpoint Information in Topology Context feature

## TC-CETC-001: Cluster Endpoint Information with Cloud Passport

**Status:** New

**Test Data:**

- test_data/test_environments/cluster01/env-with-passport/Inventory/env_definition.yml
- test_data/test_environments/cluster01/env-with-passport/Inventory/cloud-passport/cloud-passport.yml

**Pre-requisites:**

- Environment with Cloud Passport configured
- Cloud Passport contains cluster endpoint information
- Calculator CLI available

**Steps:**

- `ENV_NAMES`: `cluster01/env-with-passport`
- `CALCULATOR_CLI`: `true`

**Expected Results:**

- The topology context in `parameters.yaml` contains a `cluster` object with values from Cloud Passport:
  - `API_url`: Value from Cloud Passport
  - `API_port`: Value from Cloud Passport
  - `public_url`: Value from Cloud Passport
  - `protocol`: Value from Cloud Passport

## TC-CETC-002: Cluster Endpoint Information without Cloud Passport

**Status:** New

**Test Data:**

- test_data/test_environments/cluster01/env-without-passport/Inventory/env_definition.yml

**Pre-requisites:**

- Environment without Cloud Passport configured
- Environment has `inventory.clusterUrl` set to `https://API.cl-03.managed.qubership.cloud:6443`
- Calculator CLI available

**Steps:**

- `ENV_NAMES`: `cluster01/env-without-passport`
- `CALCULATOR_CLI`: `true`

**Expected Results:**

- The topology context in `parameters.yaml` contains a `cluster` object with values derived from `inventory.clusterUrl`:
  - `API_url`: `API.cl-03.managed.qubership.cloud`
  - `API_port`: `6443`
  - `public_url`: `apps.cl-03.managed.qubership.cloud` (derived by removing 'API.' prefix)
  - `protocol`: `https`

## TC-CETC-003: Cluster Endpoint Information with Non-Standard Port

**Status:** New

**Test Data:**

- test_data/test_environments/cluster01/env-nonstandard-port/Inventory/env_definition.yml

**Pre-requisites:**

- Environment without Cloud Passport configured
- Environment has `inventory.clusterUrl` set to `https://API.cl-03.managed.qubership.cloud:8443`
- Calculator CLI available

**Steps:**

- `ENV_NAMES`: `cluster01/env-nonstandard-port`
- `CALCULATOR_CLI`: `true`

**Expected Results:**

- The topology context in `parameters.yaml` contains a `cluster` object with values derived from `inventory.clusterUrl`:
  - `API_url`: `API.cl-03.managed.qubership.cloud`
  - `API_port`: `8443`
  - `public_url`: `apps.cl-03.managed.qubership.cloud` (derived by removing 'API.' prefix)
  - `protocol`: `https`

## TC-CETC-004: Cluster Endpoint Information with HTTP Protocol

**Status:** New

**Test Data:**

- test_data/test_environments/cluster01/env-http-protocol/Inventory/env_definition.yml

**Pre-requisites:**

- Environment without Cloud Passport configured
- Environment has `inventory.clusterUrl` set to `http://API.cl-03.managed.qubership.cloud:6443`
- Calculator CLI available

**Steps:**

- `ENV_NAMES`: `cluster01/env-http-protocol`
- `CALCULATOR_CLI`: `true`

**Expected Results:**

- The topology context in `parameters.yaml` contains a `cluster` object with values derived from `inventory.clusterUrl`:
  - `API_url`: `API.cl-03.managed.qubership.cloud`
  - `API_port`: `6443`
  - `public_url`: `apps.cl-03.managed.qubership.cloud` (derived by removing 'API.' prefix)
  - `protocol`: `http`

## TC-CETC-005: Cluster Endpoint Information with Non-Standard Hostname

**Status:** New

**Test Data:**

- test_data/test_environments/cluster01/env-nonstandard-hostname/Inventory/env_definition.yml

**Pre-requisites:**

- Environment without Cloud Passport configured
- Environment has `inventory.clusterUrl` set to `https://cluster.cl-03.managed.qubership.cloud:6443`
- Calculator CLI available

**Steps:**

- `ENV_NAMES`: `cluster01/env-nonstandard-hostname`
- `CALCULATOR_CLI`: `true`

**Expected Results:**

- The topology context in `parameters.yaml` contains a `cluster` object with values derived from `inventory.clusterUrl`:
  - `API_url`: `cluster.cl-03.managed.qubership.cloud`
  - `API_port`: `6443`
  - `public_url`: `cluster.cl-03.managed.qubership.cloud` (unchanged since it doesn't start with 'API.')
  - `protocol`: `https`

## TC-CETC-006: Cluster Endpoint Information with Cloud Passport Overriding clusterUrl

**Status:** New

**Test Data:**

- test_data/test_environments/cluster01/env-passport-override/Inventory/env_definition.yml
- test_data/test_environments/cluster01/env-passport-override/Inventory/cloud-passport/cloud-passport.yml

**Pre-requisites:**

- Environment with both Cloud Passport and `inventory.clusterUrl` configured
- Cloud Passport contains cluster endpoint information
- Environment has `inventory.clusterUrl` set to `https://API.cl-03.managed.qubership.cloud:6443`
- Calculator CLI available

**Steps:**

- `ENV_NAMES`: `cluster01/env-passport-override`
- `CALCULATOR_CLI`: `true`

**Expected Results:**

- The topology context in `parameters.yaml` contains a `cluster` object with values from Cloud Passport, not from `inventory.clusterUrl`

## TC-CETC-007: Missing Cluster Information

**Status:** New

**Test Data:**

- test_data/test_environments/cluster01/env-missing-cluster-info/Inventory/env_definition.yml

**Pre-requisites:**

- Environment without Cloud Passport configured
- Environment does not have `inventory.clusterUrl` specified
- Calculator CLI available

**Steps:**

- `ENV_NAMES`: `cluster01/env-missing-cluster-info`
- `CALCULATOR_CLI`: `true`

**Expected Results:**

- The topology context in `parameters.yaml` contains a `cluster` object with empty values:
  - `API_url`: ``
  - `API_port`: ``
  - `public_url`: ``
  - `protocol`: ``
