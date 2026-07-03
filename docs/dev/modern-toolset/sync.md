# Sync

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

Drive the ArgoCD sync from `ARGO_DPG_CONTEXT.env`.

## Trigger

- The new flow, when `OPERATION_TYPE` is not `CLEAN`.

## Inputs

| Source                | Item                   | Notes                          |
|-----------------------|------------------------|--------------------------------|
| argocd_repo_generator | `ARGO_DPG_CONTEXT.env` | Context file produced upstream |

## Outputs

| Target | Item                | Notes |
|--------|---------------------|-------|
| ArgoCD | Applications synced |       |

## Actions

1. Read `ARGO_DPG_CONTEXT.env`.
2. Sync the ArgoCD applications from that context.

## Implementation

- Path: env-generator `argo-app-life`, run from the syncer image.

## Backward compatibility

- Old flow: not called.
- New flow: called when `OPERATION_TYPE` is not `CLEAN`.

## Open items

- [ ] phase2: move to GitHub.
- [ ] If `ARGO_DPG_CONTEXT.env` is encrypted by crypt, this job must decrypt it first. TBD (design).
