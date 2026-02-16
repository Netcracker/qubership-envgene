# Test Case ID: TC-ES-004 — Generate Effective Set

**Description**

This test case verifies that the Effective Set generation job is executedwith the feature flag `GENERATE_EFFECTIVE_SET = true`.

**Preconditions**

- The Instance Repository exists and is accessible.
- Environment Instance and SD have already been generated.
- All required inputs for Effective Set generation are available.

**Steps**

1. Configure the command `envgene-build-instance` with the following parameters:

   - `params.envgene_environment_id`: `<cluster-name>/<env-name>`
   - `params.generate_effective_set`: `true`

2. Run the command `envgene-build-instance`.

**Expected Results**

- The pipeline completes with status **SUCCESS**