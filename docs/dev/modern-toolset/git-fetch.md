# git_fetch

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

> Phase: phase1 - Change: as-is - Repo: env-generator (extend)

## Purpose

Fetch and check out the repository content that the job needs. This is job 3, step 3 in the pipeline.

## Trigger

- Always.

## Inputs

| Source     | Item             | Notes            |
|------------|------------------|------------------|
| Repository | Repository       | Source to fetch  |
| Repository | Branch reference | Ref to check out |

## Outputs

| Target | Item         | Notes                  |
|--------|--------------|------------------------|
| Job    | Working tree | Checked out in the job |

## Actions

1. Fetch the repository at the given branch reference.
2. Check out the working tree in the job.

## Implementation

- Path: pipeline checkout logic.

## Backward compatibility

- Old flow: unchanged.
- New flow: unchanged.

## Open items

- [ ] None.
