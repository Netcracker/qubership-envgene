# Tasks

Test steps are listed here because the plan stage is test-first. Their execution and coverage review is owned by the
sibling test ticket; the implementation ticket does not decide placement behavior through them.

## 1. Placement resolver

- [ ] 1.1 Write failing unit tests for the resolver in `scripts/utils/app_reg_defs_placement.py` covering the effective
  mode for an absent attribute and for each of `root`, `env`, `dual`, and the rejection of an upper-case or otherwise
  unknown value. Verify: the tests fail with the module missing, and every case of C-1 is named.
- [ ] 1.2 Add the resolver module: the effective mode per C-1, the write targets per C-2, and the lookup order per
  C-3, with no case folding. Verify against the scenarios "root placement", "env placement", "dual placement writes
  both locations", "root placement reads the root location only", "env placement reads the per-environment location
  only" and "dual placement prefers the root location".
- [ ] 1.3 Add a resolver test for the failure case: a definition absent from every selected directory reports the
  definition name and every directory searched, in the order searched. Verify against the scenario "a definition
  missing from every selected location fails the run" (C-9).

## 2. Configuration schema and default

- [ ] 2.1 Add a failing schema test asserting `configuration/config.yml` with `app_reg_defs_placement: root`, `env`
  and `dual` validates, and that `ROOT` and an unknown value fail validation through `get_envgene_config_yaml`.
  Verify: the tests fail against the current schema, which does not declare the property.
- [ ] 2.2 Declare `app_reg_defs_placement` in `schemas/config.schema.json` as an enum of `root`, `env`, `dual` with a
  `root` default. Verify against the scenarios "unknown value is rejected before any folder change" and "value is
  matched case-sensitively" (C-5).
- [ ] 2.3 Confirm `scripts/tests/test_schema_distribution.py` still passes unchanged, since it stages the whole
  `config.schema.json` into `git_hooks/`. Verify: no new entry is needed for the property.

## 3. Write side

- [ ] 3.1 Write failing tests in `scripts/tests/app_reg_defs/test_appregdef_write.py` for the three modes: `root`
  writes the root pair only and removes the environment pair, `env` writes and rebuilds the environment pair and
  leaves the root pair as committed, `dual` writes both. Verify against the scenarios "attribute is absent and the
  default applies", "root placement", "env placement", "dual placement writes both locations" and "legacy
  per-environment directories are removed under root placement".
- [ ] 3.2 Drive `write_app_reg_defs` from the resolver write targets (C-2) and keep the cleanup asymmetry of C-7:
  create and overwrite the root pair without removing it, rebuild the environment pair under `env` and `dual`, remove
  it under `root`. Update the out-of-enum guard message to name all three values.
- [ ] 3.3 Read the mode through the resolver in `run_appregdef_render` with the `root` default, and drop the
  `.lower()` call. Verify against the scenario "a repeated run is idempotent in every mode" and "files no definition
  produces are removed from the rebuilt pair".
- [ ] 3.4 Apply the definition overrides to every write target of the mode in `override_app_reg_defs`. Verify against
  the root and env placement scenarios, where the overrides must reach the same directories as the rendered
  definitions.
- [ ] 3.5 Re-anchor `scripts/tests/app_reg_defs/test_appregdef_write.py:88-96` and the out-of-enum test at line 54 to
  the three-mode behavior and the `root` default. Verify: the orphan-removal assertion holds for the rebuilt pair only,
  and root files persist in every mode (C-7).

## 4. Read side

- [ ] 4.1 Write a failing test that the regdef v2 adapter reads the mode-selected directory, and replace
  `test_committed_regdefs_dir_ignores_placement_mode` (`scripts/tests/regdefv2_adapter/test_regdefv2_adapter.py:369`)
  with the placement-aware assertion. Verify against the "env placement reads the per-environment location only"
  scenario (C-6). This is an approved reversal, not a regression.
- [ ] 4.2 Resolve `committed_regdefs_dir` in `scripts/pipeline/pipeline_parameters.py` through the lookup order (C-3)
  instead of the fixed root default. Verify: `scripts/regdefv2_adapter/regdefv2_adapter.py` reads the environment pair
  under `env` without further change.
- [ ] 4.3 Resolve the AppDefs and RegDefs paths in `scripts/sd/process_sd.py:224-225` through the same lookup order.
  Verify against the "root placement reads the root location only" and "dual placement prefers the root location"
  scenarios.
- [ ] 4.4 Add a not-found test for a definition absent from every selected directory in both consumers, asserting the
  message names the definition and every directory searched. Verify against the failure scenario (C-9).

## 5. Pipeline exports

- [ ] 5.1 Write a failing test that `build_resolved_variables` exports `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH`
  at the root directories by default and at the environment pair under `env`. Verify against the "env placement
  exports the per-environment paths" and "root placement exports the root paths" scenarios (C-4).
- [ ] 5.2 Drive `scripts/pipeline/resolve_env_names.py:50-51` from the resolver write targets, keeping the variable
  names, `JOB_ENV_EXPORTS` membership and the `envgene-vars.env` write unchanged (C-8).
- [ ] 5.3 Re-anchor `scripts/tests/pipeline/test_resolve_env_names.py:104-112` and
  `scripts/tests/pipeline/test_dispatch.py:104-105` and `:139` to the mode-selected default. Verify: the assertions
  state the mode they exercise rather than assuming the old unconditional value.

## 6. BDD coverage and fixtures

- [ ] 6.1 Add the placement feature file under `cucumber_tests/features/` with one scenario per spec scenario, reusing
  the existing definition-match, instance-match, pipeline-failure and configuration-parameter steps. Verify: the
  feature covers all three modes, the default, the invalid value and the dual fallback.
- [ ] 6.2 Pin `app_reg_defs_placement: dual` in the 7 existing fixture `configuration/config.yml` files under
  `cucumber_tests/test_data/e2e/` (`uc-sbom-2` to `uc-sbom-7` and `uc-sbom-mig-1`). Verify: each file keeps its
  existing keys, and the placement key is the only addition.
- [ ] 6.3 Create `configuration/config.yml` with the `dual` pin in the 52 fixtures that carry per-environment
  definitions and hold no config file. Verify the count against the exclusion list: `uc_cr_common`,
  `uc_cr_common_sops`, `uc_cr_lch_3`, `uc_cr_lch_4` and `uc_ec_d_8_mixed_at_es` are not in the set.
- [ ] 6.4 Run the BDD suite on the untouched baseline and on the change and record both results. Verify: the baseline
  fixtures that gained a `dual` pin produce the same instances as before the change.

## 7. Verification and hand-off

- [ ] 7.1 Run the scripts suite, `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/`, on the baseline and on the
  change, and record the counts and exit codes in the ledger verification row.
- [ ] 7.2 Check the five documents already updated in this change against the implemented behavior, with the
  discrepancy audit, and correct whichever side is wrong. Files: `docs/envgene-configs.md`,
  `docs/features/app-reg-defs.md`, `docs/technical-design/instance-pipeline/steps/appregdef-render.md`,
  `docs/use-cases/app-reg-defs.md`, `docs/use-cases/artifact-downloading.md`.
- [ ] 7.3 Commit the implementation as `feat!` with a `BREAKING CHANGE` footer that names the default flip and the
  `app_reg_defs_placement: dual` pin, and state the merge order relative to the documentation commit in the merge
  request description.
