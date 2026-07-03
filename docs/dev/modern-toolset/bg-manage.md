# bg_manage

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

> Phase: phase1 - Change: as-is - Repo: qubership-envgene (core)

## Purpose

Create or update Blue-Green state files and perform warmup.

## Trigger

- `BG_MANAGE` is set.

## Inputs

| Source   | Item        | Notes                     |
|----------|-------------|---------------------------|
| Variable | `BG_MANAGE` | Enables the step when set |

## Outputs

| Target     | Item                   | Notes              |
|------------|------------------------|--------------------|
| Repository | Blue-Green state files | Created or updated |

## Implementation

- Path: `qubership-envgene` `scripts/bg_manage/bg_manage.py`.

## Backward compatibility

- Old flow: runs as a separate job through `build_pipegene/scripts/bg_manage_job.py`.
- New flow: runs as a step embedded into the single job. It is not part of the deploy flow.

## Open items

- [ ] phase2: check use-case readiness and test coverage.
