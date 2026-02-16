# Test Case ID: TC-TP-002 — Place Template  Build Template Artifact

**Description**

This test case verifies that a baseline test template can be copied into the EnvGene Template Repository and published to Artifactory.

**Preconditions**

- The Template Repository has been successfully initialized (EnvGene_Template_TC_01 completed).
- The baseline test template files are available in the repository under: /test-data/templates/baseline-template/
- The `Clean-up` procedure has been executed before starting the test.

**Steps**

1.  Run the pipeline executing `git-copy-files`
    1. Copy the baseline test template from: /test-data/templates/baseline-template/ into the target Template Repository
2. Run the `build-artifacts`

**Expected Results**

- The pipeline completes with status **SUCCESS**

