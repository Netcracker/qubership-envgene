# EnvGene Automated Testing Process (HLD)

## Purpose
This document describes the high-level design of implementing component-level automated testing for EnvGene,
 using **OOB (out-of-box) pipelines** and a centralized orchestration approach.

## Scope

The solution covers:
- A standardized repository structure for test scenarios.
- Execution of positive/negative test cases per feature.
- A top-level orchestration pipeline that runs selected scenarios step-by-step.
- Integration with EnvGene via OOB commands (Common Library).

## Key Principles

- **One YAML file = one test case** (atomic, reproducible).
- Tests are grouped by **feature/domain** (inventory, SD processing, effective set and etc.).
- Execution is performed via **OOB pipelines** (Common Library commands).
- A single **orchestrator pipeline** coordinates end-to-end execution and reporting.


## 



## Repository Structure Template

```plaintext

.../envgene/
  config/
    *-config-global.yaml                     # global integration config (systems, registry, gitlab, envgene, etc.)
    *-tests-gitlab-executor-config.yaml      # executor config
    *-tests-global-config.yaml               # optional global test config (if used)

  orchestrators/
    envgene-pos-orchestration.yaml           # orchestration of positive scenarios
    envgene-neg-orchestration.yaml           # orchestration of negative scenarios
    envgene-e2e-orchestration.yaml           # optional: end-to-end orchestration

  <feature-1>/
    pos-run-*.yaml                           # positive test cases (1 file = 1 test case)
    neg-run-*.yaml                           # negative test cases (1 file = 1 test case)

  <feature-2>/
    pos-run-*.yaml
    neg-run-*.yaml

  docs/
    test-cases/                              # test case descriptions in Markdown
      <feature-1>/
        TC-XXX_*.md
      <feature-2>/
        TC-XXX_*.md

  test-data/                                 # test inputs and expected results
    <feature-1>/
      input/                                 # source test files (yaml/json/values/etc.)
        ...
      expected/                              # golden/etalon results for validation
        ...
    <feature-2>/
      input/
        ...
      expected/
        ...

```

### Example

```plaintext
  config/
    envgene-config-global.yaml
    envgene-tests-gitlab-executor-config.yaml
    envgene-tests-global-config.yaml

  orchestrators/
    envgene-pos-orchestration.yaml
    envgene-neg-orchestration.yaml
    envgene-e2e-orchestration.yaml

  template/
    pos-run-tc-tp-001-init-template-repo-via-gsf.yaml
    pos-run-tc-tp-002-place-template-into-template-repo.yaml

  instance/
    pos-run-tc-ins-001-init-instance-repo-via-gsf.yaml
    pos-run-tc-ins-002-generate-inventory-with-env-inventory-content.yaml
    pos-run-tc-ins-003-generate-environment-instance.yaml
    pos-run-tc-sd-001-process-sd.yaml
    pos-run-tc-es-001-generate-effective-set.yaml

  e2e/
    pos-run-tc-e2e-001-envgene-end-to-end-template-to-es.yaml

  docs/
    test-cases/
      template/
        TC-TP-001_Init_Template_Repository_via_GSF.md
        TC-TP-002_Place_Template_into_Template_Repo.md
      instance/
        TC-INS-001_Init_Instance_Repository_via_GSF.md
        TC-INS-002_Generate_Inventory_with_ENV_INVENTORY_CONTENT.md
        TC-INS-003_Generate_Environment_Instance.md
        TC-SD-001_Process_SD.md
        TC-ES-001_Generate_Effective_Set.md
      e2e/
        TC-E2E-001_EnvGene_End-to-End_Template_to_Effective_Set.md

  test-data/
    template/
      input/
        templates/
          env_templates/
            test-template/
              simple/
              billing.yml.j2
              cloud.yml.j2
              tenant.yml.j2
      expected/
        template-repo/
          expected-paths.txt                 # e.g. list of files expected in TemplateRepo after copy ???

    instance/
      input/
        env_inventory_content/
          inventory-content-create.yaml
        sd/
          sd-data-valid.json
      expected/
        inventory/
          expected-inventory.yaml 
        
```

### Notes

<feature-X>/ — folder per feature/command/domain (e.g., inventory, sd-processing, effective-set, cred-rotation, blue-green) добавить про джобы 

pos-run-*.yaml — positive test cases for the feature

neg-run-*.yaml — negative test cases for the feature

orchestrators/*.yaml — top-level orchestrators that select and execute test cases via an executor

## Execution Flow Overview

1. Orchestrator pipeline is triggered (manual or scheduled).
2. Selected test cases are resolved from repository structure.
3. For each test case:
   - Required input data is loaded from test-data/
   - OOB commands (Common Library) are executed
   - Output artifacts are generated
   - Results are validated against expected data
4. Final status aggregation is performed.
5. Webex notification is sent.

## Execution Architecture

### 1. Test Component (Dedicated Test Module)

To implement automated testing, a dedicated component must be created to store:

- Test scenarios (`pos-run-*`, `neg-run-*`)
- Orchestrator definitions
- Executor configuration
- Common/global configs required to run tests

## 2. Add new test cases

- Each YAML file represents one test case
- Follow naming conventions
- Include required parameters and expected results

## 3. Connect scenarios to the orchestrator

- Include them in:
  - `envgene-pos-orchestration.yaml`
  - `envgene-neg-orchestration.yaml`

- Optionally create a dedicated orchestrator for the feature if isolation or separate execution control is required.


## Notification

The final status of automated tests execution (SUCCESS / FAILURE) must be reflected via a `Webex` notification implemented at the orchestration pipeline level, as the single aggregation point for all component pipeline results.

To send the notification, the orchestration pipeline must use the Common Library command `send-webex-message` , which is designed to deliver a Webex message based on the Atlas pipeline execution report generated by the `build-report` command.

## Repository Cleanup Strategy

To make each test run clean and reproducible:

  clean the TemplateRepo before the run
  reset/clean the InstanceRepo, or delete and recreate it

use CLI commands for cleanup:

git-clean-repository

git-delete-branch (if a branch must be removed)