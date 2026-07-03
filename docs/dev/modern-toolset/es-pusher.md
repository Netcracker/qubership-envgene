# es-pusher

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

> Phase: phase1 - Change: modified - Repo: env-generator (extend)

## Purpose

Push the Effective Set and the appsets to the deploy target repository.

## Trigger

- `PIPELINE_TYPE == GITAB_DEPLOY`

## Inputs

| Source                   | Item                   | Notes                              |
|--------------------------|------------------------|------------------------------------|
| Local filesystem         | Effective Set          | Produced earlier in the pipeline   |
| Local filesystem         | appsets directory      | Pushed alongside the Effective Set |
| Effective Set parameters | Git connection details | Read from the Effective Set        |

## Outputs

| Target                   | Item            | Notes                                  |
|--------------------------|-----------------|----------------------------------------|
| Deploy target repository | Commit and push | Contains the Effective Set and appsets |

## Implementation

- Path: `env-generator` `python/es-pusher/src/espusher/main.py push`. Uses GitPython and SOPS.

## Backward compatibility

- Not run in the old flow.

## Open items

- [ ] phase1: move to GitHub.
