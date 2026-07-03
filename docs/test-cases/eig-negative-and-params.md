# Environment Instance Generation: Negative & Parameter Override Test Cases

This document describes the test scenarios for `TC-EIG-NEG` and `TC-EIG-PARAM` in the Environment Instance Generation module.

## TC-EIG-NEG Scenarios (Negative Cases)

These tests ensure the pipeline fails gracefully with appropriate error messages when provided with invalid inputs.

### TC-EIG-NEG-001: Build Instance with Wrong Cluster
- **Description:** Run pipeline with an `ENV_NAMES` pointing to a non-existent cluster.
- **Input:** `ENV_NAMES="invalid-cluster/test-env"`
- **Expected:** Orchestrator fails.

### TC-EIG-NEG-002: Build Instance with Wrong EnvGene Project
- **Description:** Run pipeline with a mismatched EnvGene Project.
- **Input:** `ENV_NAMES="test-cluster/test-env"`, `ENVGENE_PROJECT="wrong-project"`
- **Expected:** Orchestrator fails.

### TC-EIG-NEG-003: Build Instance with Wrong Environment
- **Description:** Run pipeline with an `ENV_NAMES` pointing to a non-existent environment.
- **Input:** `ENV_NAMES="test-cluster/invalid-env"`
- **Expected:** Orchestrator fails.

### TC-EIG-NEG-004: Build Instance with Wrong Template
- **Description:** Run pipeline where the environment requests a template that doesn't exist.
- **Input:** `ENV_NAMES="test-cluster/env-wrong-template"`
- **Expected:** Orchestrator fails.

## TC-EIG-PARAM Scenarios (Overrides)

These tests ensure that specific pipeline parameters are respected and correctly passed into the environment instance generation process.
For these tests, we check if the pipeline completes successfully when provided with the parameters. Full deep assertions on output may not be required if success implies the parameter didn't break execution and was accepted.

### TC-EIG-PARAM-001: Build Instance with ENV_TEMPLATE_VERSION override
- **Input:** `ENV_TEMPLATE_VERSION="v2.0"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-002: Build Instance with ENV_TEMPLATE_VERSION_ORIGIN override
- **Input:** `ENV_TEMPLATE_VERSION_ORIGIN="v2.1"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-003: Build Instance with ENV_TEMPLATE_VERSION_PEER override
- **Input:** `ENV_TEMPLATE_VERSION_PEER="v2.2"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-004: Build Instance with ENV_SPECIFIC_PARAMS applied
- **Input:** `ENV_SPECIFIC_PARAMS="{\"foo\": \"bar\"}"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-006: Build Instance with external APP_REG_DEFS_JOB
- **Input:** `APP_REG_DEFS_JOB="https://ci.example.com/job/123"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-007: Build Instance with APP_DEFS_PATH
- **Input:** `APP_DEFS_PATH="/custom/path/apps"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-008: Build Instance with REG_DEFS_PATH
- **Input:** `REG_DEFS_PATH="/custom/path/regs"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-009: Build Instance with NS_BUILD_FILTER
- **Input:** `NS_BUILD_FILTER="core,tenant"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-010: Build Instance with DEPLOYMENT_SESSION_ID propagation
- **Input:** `DEPLOYMENT_SESSION_ID="ds-12345"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-011: Build Instance with CRED_ROTATION_PAYLOAD
- **Input:** `CRED_ROTATION_PAYLOAD="{\"rotate\": true}"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-012: Build Instance with CRED_ROTATION_FORCE
- **Input:** `CRED_ROTATION_FORCE="true"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-013: Build Instance with GH_ADDITIONAL_PARAMS
- **Input:** `GH_ADDITIONAL_PARAMS="--debug"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-014: Build Instance with BG_MANAGE enabled
- **Input:** `BG_MANAGE="true"`
- **Expected:** Pipeline completes successfully.

### TC-EIG-PARAM-015: Build Instance with BG_STATE provided
- **Input:** `BG_STATE="origin"`
- **Expected:** Pipeline completes successfully.
