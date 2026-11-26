# Design

## Work map

| Behavior | Spec scenario | File or function in this repository | Status | Evidence |
| ----------- | ----------- | ----------------------------------- | ----------- | ----------------------------------------- |
| Placement mode selects the output locations | attribute absent and the default applies; root placement; env placement; dual placement writes both locations | `scripts/build_env/appregdef_render.py::write_app_reg_defs` | tracked | `appregdef_render.py:7-27` takes `placement_mode`, branches on `dual` at lines 19-20 and 26-27, and `run_appregdef_render` reads the value with a `dual` default at line 78 |
| Definition overrides land in the mode-selected locations | root placement; env placement | `scripts/build_env/appregdef_render.py::override_app_reg_defs` | tracked | `appregdef_render.py:41-65` copies every override to the root pair at line 61 and to the per-environment pair only under `dual` at lines 63-64 |
| Placement value is validated against the allowed set | unknown value is rejected before any folder change; value is matched case-sensitively | `schemas/config.schema.json` | tracked | `config.schema.json` is the schema `get_envgene_config_yaml` validates `configuration/config.yml` against (`modules/envgene-shared/envgene_shared/utils/business_utils.py:46`); it does not declare `app_reg_defs_placement` today and allows unknown properties |
| Unknown value is rejected before any folder change | unknown value is rejected before any folder change | `scripts/build_env/appregdef_render.py::write_app_reg_defs` guard | tracked | `appregdef_render.py:8-9` raises `ValueError` for a value outside `root` / `dual`, locked by `scripts/tests/app_reg_defs/test_appregdef_write.py:54` |
| Value is matched case-sensitively | value is matched case-sensitively | `scripts/build_env/appregdef_render.py::run_appregdef_render` | tracked | `appregdef_render.py:78` lower-cases the configured value, which the exact-match scenario removes |
| Root placement removes the per-environment directories | legacy per-environment directories are removed under root placement | `scripts/build_env/appregdef_render.py::write_app_reg_defs` | tracked | `appregdef_render.py:17-18` removes `AppDefs/` and `RegDefs/` from the environment directory in every mode today; under `root` neither directory is recreated |
| Files no definition produces are removed from the rebuilt pair | files no definition produces are removed from the rebuilt pair | `scripts/tests/app_reg_defs/test_appregdef_write.py` | tracked | `test_appregdef_write.py:88-96` asserts the per-environment pair is rebuilt, so an orphan disappears under `env` and `dual` |
| Root files are not cleaned | root files are not cleaned | `scripts/build_env/appregdef_render.py::write_app_reg_defs` | tracked | `appregdef_render.py:16` only creates the root pair and never removes it, in any mode |
| Resolution reads the root location | root placement reads the root location only | `scripts/sd/process_sd.py` | tracked | `process_sd.py:224-225` resolves AppDefs from `ctx.committed_regdefs_dir.parent` and RegDefs from `ctx.committed_regdefs_dir`, both root-level |
| Resolution reads the per-environment location | env placement reads the per-environment location only | `scripts/regdefv2_adapter/regdefv2_adapter.py` | tracked | `regdefv2_adapter.py:192` reads `ctx.committed_regdefs_dir`, whose default is the root `regdefs/` (`scripts/pipeline/pipeline_parameters.py:45-46`) |
| Dual placement prefers the root location | dual placement prefers the root location | `scripts/utils/app_reg_defs_placement.py` lookup order | new-in-repo | No module computes a definition search order; each consumer above hard-codes one location |
| A definition missing from every selected location fails the run | a definition missing from every selected location fails the run | `scripts/regdefv2_adapter/regdefv2_adapter.py` and `scripts/sd/process_sd.py` error paths | tracked | `regdefv2_adapter.py:192` and `process_sd.py:224-225` each look in one directory, so their not-found errors name one location |
| Local definition path variables point at the primary location | env placement exports the per-environment paths; root placement exports the root paths | `scripts/pipeline/resolve_env_names.py::build_resolved_variables` | tracked | `resolve_env_names.py:50-51` exports `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH` as `<env_dir>/AppDefs` and `<env_dir>/RegDefs` unconditionally; the names are exported to `envgene-vars.env` through `JOB_ENV_EXPORTS` (`pipeline_parameters.py:25`) and consumed by `scripts/effective_set/dd_downloading.py` and the post-orchestrator CI steps |
| Dual placement is retained for existing consumers | pinning dual preserves the legacy layout across the default change | `schemas/config.schema.json` enum plus `cucumber_tests/test_data/e2e/*/configuration/config.yml` | tracked | The 7 fixture `config.yml` files under `cucumber_tests/test_data/e2e/` are tracked (`git ls-files`, `uc-sbom-2` to `uc-sbom-7` and `uc-sbom-mig-1`); the remaining fixtures carrying per-environment definitions hold no `configuration/config.yml` yet and are tracked when added |
| Every mode above is proven end to end | every scenario of the capability | `cucumber_tests/features/` | tracked | The directory holds 14 feature files (for example `sbom-storage-migration.feature`) wired through `cucumber_tests/shared_steps/unified_pipeline_steps.py` |

Every row is `tracked` or `new-in-repo`. No `not-in-repo` row, so the design is not blocked.

## Approaches

- **A. One shared placement resolver (recommended).** Add `scripts/utils/app_reg_defs_placement.py` exposing the
  effective mode, the write targets and the definition lookup order. `write_app_reg_defs`, `override_app_reg_defs`,
  `build_resolved_variables`, the `committed_regdefs_dir` default and the SD definition paths each call it. One place
  owns the default, the enum and the root-then-per-environment order, and a consumer cannot disagree with the write
  side. Cost: one new module and a call at five sites.
- **B. Resolve in `PipelineParametersHandler` only.** Add `appdefs_dir` and `regdefs_dir` fields derived from the
  configuration and let consumers read them off the context. Trade-off: it covers the in-pipeline consumers, but
  `regdefv2_adapter` resolves paths through a field default factory, and `argocd-dpg` and `es-pusher` run after the
  orchestrator from `envgene-vars.env`, so both still need the rule outside the handler. Two ways to compute one path
  is the failure mode this change is meant to remove. Rejected.
- **C. Inline branch per consumer.** Each of the five sites reads `app_reg_defs_placement` itself with its own
  `root` default. Trade-off: the default and the fallback order are duplicated five times, a future mode means five
  edits, and each copy needs its own test. Rejected.
- Shapes the design conversation dropped: keep the write side dual and teach only the readers (rejected, it cannot
  express `env` at all); move the mode into a pipeline parameter instead of `configuration/config.yml` (rejected, the
  placement is a property of the committed repository layout, not of one run); have the consumers glob both layouts
  without consulting the mode (rejected, it hides a missing definition in a stale copy).

## Decision

Approach A, accepted by toma0422 in chat at the design gate. The write side, the readers and the exported `LOCAL_*`
paths all take their locations from the resolver, so no consumer computes a definition path on its own. The behavior
the specs settle is not reopened here: `root` is the default, the value is matched exactly, and `dual` keeps the
root-first order with a per-environment fallback.

The design stage rows are in `ledger.md`. The gate row carries the commit sha once `component-design.md` is committed.

## Contracts

- C-1 | provides | the effective placement mode | `resolve_placement_mode(config) -> str` in
  `scripts/utils/app_reg_defs_placement.py`. Returns `root` when `app_reg_defs_placement` is absent, the configured
  value when it is one of `root`, `env`, `dual`. No case folding.
- C-2 | provides | the write targets of one run | `definition_write_dirs(base_dir, env_dir, mode) -> list[Path]`,
  ordered. `[<base>/appdefs, <base>/regdefs]` for `root`, the environment `AppDefs` and `RegDefs` pair for `env`, the
  root pair followed by the environment pair for `dual`. `write_app_reg_defs` and `override_app_reg_defs` write to
  every entry, first entry last for cleanup purposes.
- C-3 | provides | the lookup order for a named definition | `definition_search_dirs(base_dir, env_dir, mode) -> list[Path]`.
  Root pair only for `root`, environment pair only for `env`, root pair then environment pair for `dual`. Consumers
  return the first hit and report every directory searched when there is none.
- C-4 | provides | the exported file-system contract | `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH` carry the first
  entry of C-2 for the mode: the root directories under `root` and `dual`, the environment pair under `env`. The
  variable names, `JOB_ENV_EXPORTS` membership and the `envgene-vars.env` write are unchanged.
- C-5 | consumes | `configuration/config.yml` schema validation | `get_envgene_config_yaml` validates against
  `schemas/config.schema.json`, so the enum and the `root` default are declared there and an invalid value fails
  before `app_reg_def_process` runs. The same schema file is staged into `git_hooks/`, a distribution already covered
  by `scripts/tests/test_schema_distribution.py`, which needs no change.
- C-6 | changes | `committed_regdefs_dir` in `PipelineParametersHandler` | resolves through C-3 instead of the fixed
  `<CI_PROJECT_DIR>/regdefs` default, so `scripts/regdefv2_adapter/regdefv2_adapter.py:192` reads the mode-selected
  directory. This reverses `test_committed_regdefs_dir_ignores_placement_mode`, which is replaced, not kept.
- C-7 | preserves | the cleanup asymmetry | the root pair is created and overwritten but never removed, in every
  mode. The environment pair is removed and rebuilt under `env` and `dual`, and removed and not recreated under
  `root`.
- C-8 | preserves | the pipeline parameter surface | no new pipeline parameter, no new exported variable, no change
  to `ENV_NAMES`, `FULL_ENV_NAME`, `CLUSTER_NAME` or `ENVIRONMENT_NAME` handling.
- C-9 | provides | the failure message | a definition that no C-3 directory provides fails with the definition name
  and every directory searched, in the order searched.

## Order and Dependencies

Single component. The documentation half is committed at a19c8c58 on this branch and describes the behavior this
design adds, so the implementation commit must ride in the same merge request: the documentation is not to be merged
to `main` alone, or `main` briefly documents an `env` mode that does not exist. The BDD fixture pins and the placement
feature file depend on the resolver and the write side landing first, and the sibling test ticket is a sibling of the
implementation ticket, not a follow-up, because the plan stage is test-first.

## Constraints

- The production default is `root` in code and in `schemas/config.schema.json`. The string `dual` stays out of every
  production default and appears only in BDD fixture `configuration/config.yml` files.
- Exact match: drop the `.lower()` at `appregdef_render.py:78` and the case-insensitive path it implies, so the code
  and the schema enum agree.
- The out-of-enum guard in `write_app_reg_defs` is updated to name all three allowed values rather than only
  `root` or `dual`.
- Schema enum is `["root", "env", "dual"]` with `"default": "root"`. `dual` is documented as retained for backward
  compatibility, not deprecated in the schema, since the schema has no deprecation marker in use here.
- `test_committed_regdefs_dir_ignores_placement_mode` (`scripts/tests/regdefv2_adapter/test_regdefv2_adapter.py:369`)
  is an approved reversal: replace it with a test that the directory follows the mode. Do not leave the old assertion
  behind as a skipped test.
- Tests that pin the current `dual` default or the unconditional per-environment `LOCAL_*` paths are re-anchored, not
  widened: `scripts/tests/pipeline/test_resolve_env_names.py:104-112`, `scripts/tests/pipeline/test_dispatch.py:104-105`
  and `:139`, and `scripts/tests/app_reg_defs/test_appregdef_write.py`.
- BDD fixtures follow decision F1: pin `app_reg_defs_placement: dual` in the 59 fixtures that carry per-environment
  definitions, 7 amended and 52 created. Excluded: `uc_cr_common`, `uc_cr_common_sops`, `uc_cr_lch_3`,
  `uc_cr_lch_4`, and `uc_ec_d_8_mixed_at_es`, which already holds definitions at the root level. A
  `configuration/config.yml` carrying only the placement key is behavior-neutral, because `get_crypt()` reads
  `config.get('crypt', True)`.
- BDD scenarios reuse the existing steps (`the generated definitions match the reference "<x>"`,
  `the environment instance "<cluster>/<env>" matches the reference "<x>"`, `the pipeline fails`, and the
  configuration-parameter step in `cucumber_tests/shared_steps/unified_pipeline_steps.py:31-40`) rather than adding
  placement-specific steps.
- The commit is `feat!` with a `BREAKING CHANGE` footer naming the default flip and the pin, so the post-merge build
  workflow rebuilds the images.

## Out of Scope

- Removing `dual` and the per-environment directories. This change makes `root` the default; the removal is a later
  change once no consumer reads the legacy layout.
- Cleaning `appdefs/` and `regdefs/` at the repository root. Files that no definition produces keep persisting there.
- The CMDB export of definitions and the `sboms/` layout, both unchanged by placement.
- The mechanism that stages `config.schema.json` into `git_hooks/`, and the schema-validation call site in
  `envgene_shared`.
- Any change to `configuration/appregdef_config.yaml`, which selects which definitions render, not where they are
  written.

## Open Questions

- Where the out-of-enum guard lives once the schema rejects bad values: kept in `write_app_reg_defs` as defense in
  depth for callers that pass a mode directly, or dropped in favor of the schema alone. Either answer satisfies the
  specs and changes no task, so the implementation step can settle it with the resolver's own test.
