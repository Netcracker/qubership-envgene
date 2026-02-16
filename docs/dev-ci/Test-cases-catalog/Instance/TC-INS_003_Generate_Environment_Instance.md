# Test Case ID: EnvGene_Instance_TC_04_Generate_Environment_Instance

**Description**

This test case verifies that an Environment Instance is successfully generated with the feature flag `ENV_BUILDER = true`.

**Preconditions**

- The Instance Repository exists and is accessible.
- `env_definition.yml` has been successfully created:
  - `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`
- The referenced Template artifact exists and is accessible.


**Input Parameters**

Configure command `envgene-build-instance` with the following parameters:

- `params.envgene_environment_id`: `<cluster-name>/<env-name>`
- `params.build_instance`: `true`

**Steps**

1. Configure the parameters listed above for the command `envgene-build-instance`.
2. Run the command `envgene-build-instance`.

**Expected Results**

- The pipeline finishes with status **SUCCESS**.
