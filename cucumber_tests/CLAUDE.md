# cucumber_tests — BDD Test Infrastructure Reference

## Mandatory steps when adding a new BDD test

Every new BDD test must go through these steps before the work is considered done:

**1. Add to GitHub Actions workflow** (`.github/workflows/perform_e2e_tests.yml`):
```yaml
- name: Run <Feature Name> BDD tests
  run: |
    docker compose -f devtools/docker-compose.yml exec -T cucumber bash -c \
      "export PYTHONPATH=/workspace && \
       cd /workspace && \
       pytest cucumber_tests/step_defs/test_<module>.py \
         -v -s \
         --junitxml=reports/<module>.xml \
         | tee -a /workspace/e2e_tests.log"
```
Insert the step before "Publish Test Report" in the same order as the use-case docs.

**2. Run the full test suite in Docker** to confirm no regressions:
```bash
# Start the container (if not already running)
docker build -t local-envgene-main -f build_envgene/build/Dockerfile .
docker compose -f devtools/docker-compose.yml up -d --build cucumber
docker compose -f devtools/docker-compose.yml exec -T cucumber \
  bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"

# Run all tests
docker compose -f devtools/docker-compose.yml exec -T cucumber bash -c \
  "export PYTHONPATH=/workspace && cd /workspace && \
   pytest cucumber_tests/ -v -s \
   --html=cucumber_tests/reports/report.html --self-contained-html"
```
All previously passing tests must still pass. The new test must pass.



Tests use **pytest-bdd**. Entry points in `step_defs/test_*.py` import steps and call `scenarios(...)`. Step implementations live in `shared_steps/` only — `step_defs/` contains only `test_*.py` entry points.

## Workspace defaults

`EnvGeneWorkspace(tmp_path)` — fixture in `conftest.py`:

- `cluster_name = "test-cluster"`, `env_name = "test-env"`
- `run_pipeline()` runs `scripts.pipeline.orchestrator` via subprocess with env vars:
  - `ENV_NAMES`, `CLUSTER_NAME`, `ENVIRONMENT_NAME`, `FULL_ENV_NAME` set from workspace fields
  - `IS_LOCAL_DEV_TEST_ENVGENE = "true"`
  - `EFFECTIVE_SET_CLI_PATH` → stub that exits 0 (does NOT invoke the real Java CLI)
  - `SECRET_KEY` = fixed Fernet key `c2VjcmV0LWtleS1tdXN0LWJlLTMyLWJ5dGVzLWxvbmc=`
- `extra_env` dict on workspace overrides/extends the above before `run_pipeline()`

## Mock Nexus (session fixture, port 8000)

Serves these artifacts — use exactly these IDs in `env_definition.yml`:

| Artifact ID | Templates provided |
|-------------|--------------------|
| `test-artifact:v1` | `Namespace.yml.j2` (`name: dummy-namespace`), `BgDomain.yml.j2`, `env_templates/test.yml` (2 namespaces: `deploy_postfix: core` and `deploy_postfix: bss`), `env_templates/composite-prod.yml` (0 namespaces), `Tenant.yml.j2`, `Cloud.yml.j2`, `appdefs/app1.yml.j2`, `appdefs/app3.yml.j2`, `regdefs/registry1.yml.j2`, `regdefs/off-site-registry-X.yml.j2` |
| `foo:1.0` | same template structure as `test-artifact:v1` |
| `project-env-template:v1.2.3` | same template structure as `test-artifact:v1` |
| `test_app_artifact:1.0.0` | SD JSON: `test_app:1.0.0 / deployPostfix: dp1` |
| `test_app_2_artifact:2.0.0` | SD JSON: `test_app_2:2.0.0 / deployPostfix: dp2` |

Registry config is pre-wired: `test-registry` → `http://localhost:8000/release`.

**Important**: `bgNsArtifacts.origin/peer` require a separately registered artifact in mock Nexus. The mock only registers the five IDs above — do not reference other artifact IDs in test data.

## Orchestrator step names (for `pipeline log contains "START: <name>"`)

`get_passport` · `credential_rotation` · `bg_manage` · `env_inventory_generation` · `set_template_version` · `appregdef_render` · `deploy_postfix_namespace_map` · `migrate_sd_to_deploy_plan` · `process_sd` · `generate_deployment_plan` · `env_build` · `generate_effective_set` · `git_commit`

`process_sd` runs when `SD_DATA` or `SD_VERSION` is set AND `OPERATION_TYPE == DEPLOY` (default) AND NOT `GITLAB_DEPLOY`.

## Namespace folder naming algorithm

```
base   = deploy_postfix  OR  template_filename_without_extension
                              (e.g. "Namespace.yml.j2" → "Namespace")
suffix = ""           # non-BG or controller
       | "-origin"    # origin namespace in BG Domain
       | "-peer"      # peer namespace in BG Domain
folder = base + suffix
```

Role is determined by matching the rendered `namespace.yml` `name` field against `bg_domain.yml` `originNamespace.name` / `peerNamespace.name`. Controller gets no suffix.

## Test data conventions

Minimal `env_definition.yml` for env_builder tests:

```yaml
inventory:
  environmentName: test-env
  cloudName: test-cluster
envTemplate:
  name: <template-name>          # must match a yml file in artifact's env_templates/
  artifact: "test-artifact:v1"
  templateRepository: maven-repo
  registry: test-registry
  namespaces:                    # omit to use template's own namespace list
    - template_path: "{{ templates_dirs.common }}/Namespace.yml.j2"
      deploy_postfix: "core"     # optional; without it folder = "Namespace"
      template_override:         # optional; controls rendered namespace name
        name: "origin-ns"
```

For BG tests add `bg_domain.yml` next to `Inventory/`:

```yaml
controllerNamespace:
  name: controller-ns
originNamespace:
  name: origin-ns
peerNamespace:
  name: peer-ns
```

**Credential rotation tests always require `configuration/config.yml` with `crypt: false`** (Windows path normalization requires `Path` joins; the orchestrator uses string concat `f"{work_dir}/environments/..."` which creates mixed-slash paths on Windows).

For SBOM retention tests add `configuration/config.yml`:

```yaml
sbom_retention:
  enabled: true
  keep_versions_per_app: 10
```

Test data root layout: `e2e/<uc_id>/environments/<cluster>/<env>/Inventory/env_definition.yml`  
Optional siblings at `e2e/<uc_id>/`: `sboms/`, `configuration/`, `bg_domain.yml` (at env level).

## Step vocabulary (all available steps)

**Given**
- `the workspace is initialized with test data from "<e2e/path>"`
- `the pipeline parameter "<PARAM>" is set to "<value>"`  ← use `\\n` for newlines
- `the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "<einv/...json>"`
- `the pipeline has <PARAM> set to "<value>"`
- `the repository has an initial state for rollback testing`
- `the bg_domain.yml is configured with origin namespace "<ns>" and peer namespace "<ns>"`
- `the SBOM files are inflated to exceed the size limit`
- `the config parameter "<param>" is set to <value>`

**When**
- `the unified pipeline orchestrator runs`

**Then**
- `the orchestrator completes successfully`
- `the orchestrator fails`
- `the pipeline log contains "<text>"`  (also: `pipeline log shows`, `pipeline logs contain`)
- `the pipeline log does not contain "<text>"`
- `the pipeline fails`
- `the environment instance "<cluster>/<env>" matches the reference "<golden-dir>"`
- `the workspace matches the reference "<golden-dir>"`
- `the namespace folder "<name>" exists in the environment instance`
- `the namespace folder "<name>" exists in environment "<cluster>/<env>"`
- `the "<filename>" file is created / updated / deleted`
- `the environment directory is deleted`
- `its parent directory is not deleted`
- `the <entity> file "<name>" is created / updated / deleted at "<scope>" scope`  (entity: paramset, credentials, resource_profile, shared_template_variable)
- `the decrypted credentials file "<name>" at "<scope>" scope matches the reference "<ref>"`
- `the generated env_definition contains minimal required fields`
- `the repository state is identical to the initial state`
- `the Blue-Green state files are "<f1>" and "<f2>"`
- `the namespace "<ns1>" and namespace "<ns2>" have the same content`
- `no SBOM files were removed`
- `<N> SBOM files were removed in total`
- `the SBOM directory "<app>" contains <N> files`
- `only the single most recent SBOM file remains in each application directory`
- `no flat SBOM files remain directly under the sboms directory`
- `the "<filename>" file exists at the workspace root`
- `the "<filename>" file does not exist at the workspace root`
- `no credential files were modified by the rotation`
- `the credential "<cred_id>" field "<field>" equals "<value>" in the env credentials file`
