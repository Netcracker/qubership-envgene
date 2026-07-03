# credential_rotation

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

> Phase: phase1 - Change: as-is - Repo: qubership-envgene (core)

## Purpose

Rotates credentials for the environment.

## Trigger

- `CRED_ROTATION_PAYLOAD` is not empty. Mutually exclusive with `GET_PASSPORT`.

## Inputs

| Source   | Item                    | Notes             |
|----------|-------------------------|-------------------|
| Pipeline | `CRED_ROTATION_PAYLOAD` | Rotation payload. |

## Outputs

| Target      | Item                     | Notes |
|-------------|--------------------------|-------|
| Environment | Rotated credential files |       |

## Actions

1. Read the `CRED_ROTATION_PAYLOAD` value.
2. Rotate the environment credentials and write the rotated credential files.

## Implementation

- Path: `qubership-envgene creds_rotation/scripts/creds_rotation_handler.py`

## Backward compatibility

- Old flow: runs as a separate job through `build_pipegene/scripts/credential_rotation_job.py`.
- New flow: runs as a step inside `env_prepare`.

## Open items

- [ ] phase2: check use-case readiness and test coverage.
