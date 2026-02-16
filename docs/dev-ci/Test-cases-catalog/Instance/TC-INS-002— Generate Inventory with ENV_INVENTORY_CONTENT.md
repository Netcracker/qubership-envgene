# Test Case ID: TC-INS-002— Generate Inventory with ENV_INVENTORY_CONTENT

**Description**

This test case verifies that `env_definition.yml` is created in the Instance Repository  with `ENV_INVENTORY_CONTENT`  and the target file does not exist.

**Preconditions**

- The Instance Repository exists and is accessible.
- The Environment Inventory file does not exist before the run:
  - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
- `Clean-up` procedure has been executed before starting the test.

**Steps**

1. Configure the command `envgene-build-instance` with the following parameters:
   - `ENV_NAMES`: `<cluster-name>/<env-name>`
   - `ENV_INVENTORY_CONTENT`: *(see payload in **Input Data**)*
   - `ENV_TEMPLATE_VERSION`: `<template-artifact>` 
   - `params.envgene_environment_id`: `<cluster-name>/<env-name>` 
2. Run the command `envgene-build-instance`.

**Expected Results**

- The pipeline completes with status **SUCCESS**


**Input Data**

Use the following payload value for `ENV_INVENTORY_CONTENT` (only `envDefinition` is included):

```json
"{\"envDefinition\":{\"action\":\"create_or_replace\",\"content\":{\"inventory\":{\"environmentName\":\"env-1\",\"tenantName\":\"Applications\",\"cloudName\":\"cluster-1\",\"description\":\"Full sample\",\"owners\":\"Qubership team\"},\"envTemplate\":{\"name\":\"composite-prod\",\"artifact\":\"project-env-template:master_20231024-080204\"}}}}"
