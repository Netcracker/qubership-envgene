# set_defaults

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

> Phase: phase1 - Change: new - Repo: env-generator (extend)

## Purpose

Set default values for pipeline variables and parameters at the start of the `env_prepare` job, so later steps
read normalised inputs.

## Trigger

- Always.

## Inputs

| Source   | Item               | Notes                        |
|----------|--------------------|------------------------------|
| Pipeline | Pipeline variables | Raw values passed to the job |

## Outputs

| Target      | Item                         | Notes                                    |
|-------------|------------------------------|------------------------------------------|
| Later steps | Normalised default variables | Available to subsequent steps in the job |

## Actions

1. Read the incoming pipeline variables.
2. Apply default values where a variable is unset.
3. Expose the normalised variables to later steps.

## Implementation

- Path: to be created.

## Backward compatibility

- Old flow: no equivalent standalone step. This behaviour did not exist as a discrete step.
- New flow: helper for the consolidated single job.

## Open items

- [ ] phase1 create the step.
