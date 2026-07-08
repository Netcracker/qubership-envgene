# EnvGene end-to-end flows

- [EnvGene end-to-end flows](#envgene-end-to-end-flows)
  - [TC-001: Baseline flow (template to Effective Set)](#tc-001-baseline-flow-template-to-effective-set)
  - [TC-002: Full flow with CMDB import](#tc-002-full-flow-with-cmdb-import)
  - [TC-003: Full flow with SD processing and Effective Set generation](#tc-003-full-flow-with-sd-processing-and-effective-set-generation)


## TC-001: Baseline flow (template to Effective Set)

**Description:**

Verifies the minimal end-to-end EnvGene flow.

**Preconditions:**

- Template repository exists and is accessible.
- Instance repository exists and is accessible.
- Baseline template files exist in the repository under the agreed path (e.g. `/test-data/templates/baseline-template/`).
- `git-clean-repository` procedure has been executed for both repositories before starting the test.

**Steps:**

1. Run the orchestration pipeline with the required inputs to identify:

   - target Template repository (project + branch)
   - target Instance repository / environment ID (`<cluster-name>/<env-name>`)
   - baseline template location
   - required EnvGene/GSF artifacts (if applicable)

2. The orchestration pipeline triggers component test cases sequentially:

   - `git-clean-repository`
   - `TC-TP-001 — Init Template Repository via GSF`
   - `TC-TP-002 — Place Template into Template Repo`
   - `git-clean-repository`
   - `TC-INS-001 — Init Instance Repository via GSF`
   - `TC-INS-002 — Generate Inventory with ENV_INVENTORY_CONTENT`
   - `TC-INS-003 — Generate Environment Instance`
   - `TC-SD-001 — Process SD`
   - `TC-ES-001 — Generate Effective Set`

3. Orchestration pipeline waits for completion of each triggered pipeline/job before starting the next step.
4. Orchestration pipeline collects final statuses and artifacts references (if required).
5. Send Webex notification as a final reporting stage of the orchestration pipeline:

   - if the final status is SUCCESS, send a success notification
   - if the final status is FAILURE, send a failure notification
   - use the Common Library command `send-webex-message` to deliver the notification
   - notification delivery must not affect the pipeline result (informational only)

**Expected Results:**

- The orchestration pipeline completes with status SUCCESS.

---

## TC-002: Full flow with CMDB import

**Description:**

Verifies the instance pipeline flow with App Reg Def rendering, environment build, Git commit, and CMDB import.

**Preconditions:**

- Instance repository exists and is accessible.
- Environment exists under `/environments/<cluster-name>/<env-name>/`.
- AppDef/RegDef templates exist in the template repository.
- CMDB endpoint is configured and accessible.

**Steps:**

1. Run the instance pipeline with the required inputs:

   - target Instance repository / environment ID (`<cluster-name>/<env-name>`)
   - pipeline parameters (`ENV_TEMPLATE_VERSION` — substitute the target template version from test data):

     ```yaml
     ENV_NAMES: <cluster-name>/<env-name>
     ENV_BUILD: True
     ENV_TEMPLATE_VERSION: <env-template-version>
     DEPLOYMENT_SESSION_ID: b8278696-82ba-4893-97d7-7ac3a9fe1a18
     CMDB_IMPORT: True
     ```

2. The instance pipeline runs the following jobs sequentially:

   - `app_reg_def_render`
   - `env_builder`
   - `git_commit`
   - `cmdb_import`

3. Orchestration pipeline waits for completion of each triggered pipeline/job before starting the next step.
4. Orchestration pipeline collects final statuses and artifacts references (if required).

**Expected Results:**

- The orchestration pipeline completes with status SUCCESS.
- Instance pipeline jobs complete with status SUCCESS: `app_reg_def_render`, `env_builder`, `git_commit`, `cmdb_import`.

---

## TC-003: Full flow with SD processing and Effective Set generation

**Description:**

Verifies the instance pipeline flow with App Reg Def rendering, SD processing, environment build, Effective Set generation, and Git commit.

**Preconditions:**

- Instance repository exists and is accessible.
- Environment exists under `/environments/<cluster-name>/<env-name>/`.
- AppDef/RegDef templates exist in the template repository.

**Steps:**

1. Run the instance pipeline with the required inputs:

   - target Instance repository / environment ID from test data (`<cluster-name>/<env-name>`)
   - input parameters (`ENV_NAMES` and `SD_DATA` — substitute values from test data):

     ```yaml
     ENV_NAMES: <cluster-name>/<env-name>
     ENV_BUILD: True
     GENERATE_EFFECTIVE_SET: True
     SD_SOURCE_TYPE: json
     SD_DATA: <sd-data-json>
     SD_REPO_MERGE_MODE: basic-merge
     DEPLOYMENT_SESSION_ID: 5e9409de-4327-4646-a55b-38162e91248f
     ENVGENE_LOG_LEVEL: INFO
     EFFECTIVE_SET_CONFIG: '{"version":"v2.0","effective_set_expiry":"1 week","contexts":{"operational":{"consumers":[{"name":"dobp","version":"v2.0"}]}}}'
     ENV_TEMPLATE_VERSION_UPDATE_MODE: PERSISTENT
     ```

2. The instance pipeline runs the following jobs sequentially:

   - `app_reg_def_render`
   - `process_sd`
   - `env_builder`
   - `generate_effective_set`
   - `git_commit`

3. Orchestration pipeline waits for completion of each triggered pipeline/job before starting the next step.
4. Orchestration pipeline collects final statuses and artifacts references (if required).

**Expected Results:**

- The orchestration pipeline completes with status SUCCESS.
- Instance pipeline jobs complete with status SUCCESS: `app_reg_def_render`, `process_sd`, `env_builder`,
  `generate_effective_set`, `git_commit`.
- Effective Set is generated.
