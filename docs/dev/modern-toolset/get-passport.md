# get_passport

> Phase: phase1 - Change: as-is - Repo: qubership-envgene (core) and env-generator (extend)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Fetch the generated Cloud Passport into the environment repo.

## Trigger

- `GET_PASSPORT` is true.

## Inputs

| Source | Item |
|---|---|
| Discovery pipeline | Cloud Passport artifacts |

## Outputs

| Target | Item |
|---|---|
| Environment directory | Cloud-passport files |

## Implementation

- Path: `qubership-envgene` `build_pipegene/scripts/passport_jobs.py` `prepare_passport_job` and
  `scripts/cloud_passport`.

## Backward compatibility

- Old flow: unchanged.
- New flow: unchanged.

## Open items

- [ ] phase1: test manually.
- [ ] phase2: prepare a use case and cover with tests.
