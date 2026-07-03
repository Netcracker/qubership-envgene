# app_reg_def_process

> Phase: phase1 - Change: as-is - Repo: qubership-envgene (core)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Render AppDef and RegDef files and place them in the environment.

## Trigger

- Always.

## Inputs

| Source                  | Item                  | Notes                                      |
|-------------------------|-----------------------|--------------------------------------------|
| Environment template    | Template files        | Source for rendering                       |
| Environment instance    | Instance files        | Checked for already-present definitions    |
| Environment build input | `APPREG_DEF_STRATEGY` | `create_if_not_exist` (default), `replace` |

## Outputs

| Target      | Item          | Notes                     |
|-------------|---------------|---------------------------|
| Environment | AppDef files  | Rendered definitions      |
| Environment | RegDef files  | Rendered definitions      |

## Actions

1. Render the AppDef and RegDef files.
2. When `APPREG_DEF_STRATEGY` is `create_if_not_exist`, skip files already present in the environment instance.
3. When `APPREG_DEF_STRATEGY` is `replace`, render without skipping.

## Implementation

- Path: `qubership-envgene` `scripts/build_env/appregdef_render.py`.
- Currently renders all definitions.
- Supports `placement_mode` of `root` or `dual`.
- Records the resolved template version through `update_generated_versions`.

## Backward compatibility

- Old flow: phase1 unchanged. Definitions render in two passes, a required subset in this job (job 3, step 11) and
   the rest inside `env_build`.
- New flow: phase2 renders only the required appregdefs and implements the `create_if_not_exist` and `replace`
   strategies.

## Open items

- [ ] phase2: render only the required appregdefs.
- [ ] phase2: implement the `create_if_not_exist` and `replace` strategies.
