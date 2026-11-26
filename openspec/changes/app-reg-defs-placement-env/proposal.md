# Proposal

## Why

`app_reg_def_process` always writes rendered Application and Registry Definitions to two places: the root-level
`appdefs/` and `regdefs/`, and a compatibility copy under `environments/<cluster>/<env>/AppDefs/` and `RegDefs/`.
The dual layout is a leftover of the move to root-level definitions. It doubles the committed surface of every
instance repository, and the two copies drift, because only the root pair is treated as canonical while consumers
still read the per-environment pair.

The repository has no way to choose one layout. A team that wants root-only definitions cannot stop the
per-environment copies from being rewritten, and a team whose consumers still read the per-environment layout has
no way to keep only that layout. The default is the worst middle ground: dual, which keeps both alive indefinitely.

## What Changes

- `app_reg_defs_placement` in `configuration/config.yml` gains a third value, `env`, and the default changes from
  `dual` to `root`. `env` writes the per-environment pair only, `root` writes the root pair only, `dual` keeps
  writing both and is retained for backward compatibility.
- The value is matched exactly and declared in `schemas/config.schema.json` with the `root` / `env` / `dual` enum and
  a `root` default, so an invalid value fails configuration validation before any definition folder is changed.
- Definition resolution becomes placement-aware. Today every consumer reads the root pair while the deployment plan
  generator reads the per-environment pair through `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH`, which is
  inconsistent and would break `env` at first use. Each consumer now reads the locations its placement mode selects:
  the root pair in `root`, the per-environment pair in `env`, and the root pair with a per-environment fallback in
  `dual`.
- `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH` follow the primary location of the mode, so an `env` placement points
  them at the per-environment directories instead of the root ones.
- A definition that no location of the selected mode provides fails the pipeline, and the error names every location
  it searched.
- The per-environment pair is removed under `root`, so a repository switching to the default is left clean rather than
  holding stale copies.

## Capabilities

### New Capabilities

- `app-reg-defs-placement`: where `app_reg_def_process` publishes rendered Application and Registry Definitions, and
  which of those locations the pipeline reads back, for each value of `app_reg_defs_placement`.

### Modified Capabilities

<!-- openspec/specs/ is empty, so no existing capability has a requirement that changes. -->

## Impact

- Configuration: `configuration/config.yml` gains `app_reg_defs_placement` semantics, declared in
  `schemas/config.schema.json`. The schema is also staged into `git_hooks/`, which `scripts/tests/test_schema_distribution.py`
  already covers.
- Pipeline step: `app_reg_def_process` write side in `scripts/build_env/appregdef_render.py`.
- Read side: `scripts/sd/process_sd.py`, `scripts/pipeline/resolve_env_names.py` with
  `scripts/pipeline/pipeline_parameters.py`, `scripts/regdefv2_adapter/regdefv2_adapter.py`, and the
  `LOCAL_APPDEFS_PATH` / `LOCAL_REGDEFS_PATH` values set for `scripts/effective_set/dd_downloading.py`.
- Existing behavior locked by a test: `test_committed_regdefs_dir_ignores_placement_mode` in
  `scripts/tests/regdefv2_adapter/test_regdefv2_adapter.py` asserts that resolution ignores the placement mode. That
  assertion is reversed by this change and the test is replaced.
- Breaking change: repositories that rely on the current `dual` default lose the per-environment copies after the
  upgrade unless they pin `app_reg_defs_placement: dual` explicitly.
- Tests: the BDD fixtures that carry per-environment definitions pin `dual`, 52 fixture `configuration/config.yml`
  files created and 7 amended.
- Docs: already updated in this change, `docs/envgene-configs.md`, `docs/features/app-reg-defs.md`,
  `docs/technical-design/instance-pipeline/steps/appregdef-render.md`, `docs/use-cases/app-reg-defs.md`, and
  `docs/use-cases/artifact-downloading.md`.
