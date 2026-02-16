# Test Case ID: TC-E2E-001 — EnvGene End-to-End Flow (Template to Effective Set)

**Description**

This test case verifies the minimal end-to-end EnvGene flow.

**Preconditions**

- Template repository exists and is accessible.
- Instance repository exists and is accessible.
- Baseline template files exist in the repo under the agreed path (e.g. `/test-data/templates/baseline-template/`).
- `git-clean-repository` procedure has been executed for both repositories before starting the test

**Steps**


1. Run the orchestration pipeline with the required inputs to identify:
   - target Template repository (project + branch)
   - target Instance repository / environment id (`<cluster-name>/<env-name>`)
   - baseline template location
   - required EnvGene/GSF artifacts (if applicable)

2. The orchestration pipeline triggers component test cases sequentially:

`git-clean-repository`
   - `TC-TP-001 — Init Template Repository via GSF`
   - `TC-TP-002 — Place Template into Template Repo`
`git-clean-repository`
   - `TC-INS-001 — Init Instance Repository via GSF`
   - `TC-INS-002 — Generate Inventory with ENV_INVENTORY_CONTENT`
   - `TC-INS-003 — Generate Environment Instance`
   - `TC-SD-001 — Process SD` 
   - `TC-ES-001 — Generate Effective Set`

3. Orchestration pipeline waits for completion of each triggered pipeline/job before starting the next step.
4. Orchestration pipeline collects final statuses and artifacts references (if required).

6. Send Webex notification as a final reporting stage of the orchestration pipeline:
   - if the final status is SUCCESS, send a success notification
   - if the final status is FAILURE, send a failure notification
   - use the Common Library command send-webex-message to deliver the notification
   - notification delivery must not affect the pipeline result (informational only)

**Expected Results**

- The orchestration pipeline completes with status **SUCCESS**