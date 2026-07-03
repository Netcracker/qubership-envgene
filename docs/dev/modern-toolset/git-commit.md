# git_commit

> Phase: phase1 - Change: modified - Repo: qubership-envgene (core)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Commit the generated environment instance, Effective Set, and deploy plan to the EnvGene repository.

## Trigger

- There is a change to commit.

## Inputs

| Source   | Item                    | Notes                                                |
|----------|-------------------------|------------------------------------------------------|
| Pipeline | Generated files         | Environment instance, Effective Set, and deploy plan |
| Pipeline | PIPELINE_TYPE           | Decides what to commit                               |
| Pipeline | SAVE_ARTIFACTS_STRATEGY | Governs artifact save or skip (phase2)               |

## Outputs

| Target             | Item     | Notes                                  |
|--------------------|----------|----------------------------------------|
| EnvGene repository | A commit | Contains the committed generated files |

## Actions

1. Detect whether there is a change to commit.
2. Determine which files to commit based on PIPELINE_TYPE.
3. Commit the selected files to the EnvGene repository.

## Implementation

- Path: qubership-envgene build_envgene/scripts/git_commit.sh

## Backward compatibility

- Old flow: commits the environment instance and Effective Set.
- New flow: decides what to commit based on PIPELINE_TYPE.

## Open items

- [ ] phase1 commit or skip env_instance, Effective Set, and sd.yaml based on PIPELINE_TYPE.
- [ ] phase2 save or skip the same files as artifacts based on SAVE_ARTIFACTS_STRATEGY.
- [ ] phase2 consider merging with es-pusher.
