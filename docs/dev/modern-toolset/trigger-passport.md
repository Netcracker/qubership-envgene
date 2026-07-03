# trigger_passport

> Phase: phase1 - Change: as-is - Repo: qubership-envgene (core) and env-generator (extend)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Trigger the external Cloud Passport discovery pipeline for the cluster.

## Trigger

- `GET_PASSPORT` is true and the passport job has not yet been added for this cluster.

## Inputs

| Source   | Item            | Notes                           |
|----------|-----------------|---------------------------------|
| Pipeline | `FULL_ENV_NAME` | Identifies the target cluster.  |
| Pipeline | `GET_PASSPORT`  | Gates whether the job is added. |

## Outputs

| Target              | Item                         | Notes                           |
|---------------------|------------------------------|---------------------------------|
| Downstream pipeline | Cloud Passport discovery run | External discovery for cluster. |

## Actions

1. Check that `GET_PASSPORT` is true.
2. Check that the passport job has not yet been added for this cluster.
3. Prepare and add the job that triggers the Cloud Passport discovery pipeline.

## Implementation

- Path: `qubership-envgene` `build_pipegene/scripts/passport_jobs.py`, entrypoint `prepare_trigger_passport_job`.

## Backward compatibility

- Old flow: unchanged.
- New flow: unchanged.

## Open items

- [ ] phase1: test manually.
- [ ] phase2: prepare a use case and cover with tests.
