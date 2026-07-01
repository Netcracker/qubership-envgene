# Report on XFAIL Tests

This document lists the integration test groups currently marked as `XFAIL` (Expected Failure) due to missing external dependencies or unimplemented functionality in the pipeline or test framework. For each case, a description of what is missing for its successful execution is provided.

## 1. Multiple Environments (UC-ME)
**Associated Files:** 
- `tests/step_defs/test_unified_pipeline_success.py`
- `tests/step_defs/test_environment_instance_generation.py`

**Test Cases:**
- `Scenario: UC-ME-1: Unified Pipeline Success with Multiple Environments`
- `Scenario: UC-EIG-ME-1: Parallel Environment Instance Generation for Multiple Environments`

**Problem Description:**
The integration tests check the ability to run a single pipeline for multiple environments simultaneously (e.g., `test-cluster/env1, test-cluster/env2`).
**Missing Requirements for Resolution:**
Currently, the orchestrator script (`orchestrator.py`) or the test framework does not support running multiple environments in a single invocation. Resolving this requires modifying `orchestrator.py` to process a list of environments in a loop, or updating the test framework (fixtures) to correctly generate a multi-environment directory structure before the invocation.

## 2. Template Inheritance Tests (UC-TI)
**Associated File:** `tests/step_defs/test_template_inheritance.py`

**Test Cases:**
- `Scenario: UC-TI-PT-1: Build child template using a single parent template`
- `Scenario: UC-TI-PT-2: Build child template composed from multiple parent templates`
- `Scenario: UC-TI-CS-1: Use explicit composite_structure from child Template Descriptor`
- `Scenario: UC-TI-OV-1: Override parent parameters for Cloud template`
- `Scenario: UC-TI-OV-2: Override parent parameters for Namespace template`

**Problem Description:**
Tests involving template inheritance verify that a child `Template Descriptor` correctly inherits parameters and overrides settings from parent templates.
**Missing Requirements for Resolution:**
The "Template Builder Pipeline" logic, which resolves and merges templates (e.g., `cloud.parent` inheritance), resides in an external tool not present in this repository. To fix these tests, a mock function (Python wrapper) must be implemented in `tests/framework/workspace.py` to simulate the external tool's behavior and generate the final `template.yml` before launching `envgene`.

## 3. GSF Repository Maintenance Tests (UC-GSF)
**Associated File:** `tests/step_defs/test_gsf_repository_maintenance.py`

**Test Cases:**
- `Scenario: UC-GSF-TMP-1: Initialize Template Repository via GSF`
- `Scenario: UC-GSF-TMP-2: Upgrade Template Repository via GSF`
- `Scenario: UC-GSF-TMP-2.1: Upgrade legacy Template Repository (versions before 2.85.0)`
- `Scenario: UC-GSF-TMP-3: Downgrade Template Repository via GSF`
- `Scenario: UC-GSF-INST-1: Initialize Instance Repository via GSF`
- `Scenario: UC-GSF-INST-2: Upgrade Instance Repository via GSF`
- `Scenario: UC-GSF-INST-3: Downgrade Instance Repository via GSF`

**Problem Description:**
The GSF (Git System Follower) test group verifies the migration, installation, and maintenance of repository instances.
**Missing Requirements for Resolution:**
Executing these steps requires the `git-system-follower` binary (or CLI script), which is absent in the current test Docker container (`devtools-cucumber`). To resolve these tests, either a lightweight/mock version of `git-system-follower` must be downloaded within the test environment Dockerfile, or a Python mock simulating GSF command outputs must be added to `tests/framework/workspace.py`.
