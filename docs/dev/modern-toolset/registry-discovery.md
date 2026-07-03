# registry_discovery

> Phase: phase1 - Change: new - Repo: env-generator (extend)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Generate the base artifact definition from CMDB or from a central appregdef storage. The job is optional and currently
disabled.

## Trigger

- Always, when enabled.

## Inputs

| Source   | Item           |
|----------|----------------|
| Pipeline | system config  |
| Pipeline | env_definition |

## Outputs

| Target        | Item                     |
|---------------|--------------------------|
| env-generator | base artifact definition |

## Actions

1. Generate the artdef base from CMDB or the central appregdef storage.

## Implementation

- Path: env-generator.
- The related plugin `get_sboms` writes `configuration/registry.yml`.
- In the current static pipeline the job is present but commented out.

## Backward compatibility

- Old flow: not present.
- New flow: not active by default.

## Open items

- [ ] phase1: keep the job disabled.
- [ ] phase2: consider enabling the job.
- [ ] phase3: add integration with the central appregdef storage.
- [ ] Decide whether to remove the job or extend it.
