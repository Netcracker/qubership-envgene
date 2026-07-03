# argocd_repo_generator

> Phase: phase1 - Change: modified - Repo: env-generator (extend)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Generate the ArgoCD GitOps repository structure from the Effective Set and the deploy plan. Previously named
argocd-dpg (job 3, step 20).

## Trigger

- PIPELINE_TYPE == GITAB_DEPLOY

## Inputs

| Source   | Item                         | Notes                         |
|----------|------------------------------|-------------------------------|
| Pipeline | APPLICATION_VERSIONS         | Application version set       |
| Pipeline | environment_id               | Target environment identifier |
| Upstream | Effective Set                | Resolved parameter set        |
| Upstream | Local deployment descriptors | Per-application descriptors   |
| Upstream | Deploy plan                  | Ordered deployment plan       |

## Outputs

| Target      | Item                        | Notes                              |
|-------------|-----------------------------|------------------------------------|
| GitOps repo | ApplicationSet manifest     | Single manifest                    |
| GitOps repo | ArgoCD Application manifests | One per application                |
| GitOps repo | appsets directory           | Holds the generated manifests      |
| Pipeline    | ARGO_DPG_CONTEXT.env        | Context handed to downstream steps |

## Actions

1. Read APPLICATION_VERSIONS, environment_id, the Effective Set, the local deployment descriptors, and the deploy plan.
2. Generate the ApplicationSet manifest and the per-application ArgoCD Application manifests.
3. Write the manifests into the appsets directory.
4. Emit ARGO_DPG_CONTEXT.env for downstream steps.

## Implementation

- Path: env-generator python/argocd-dpg/src/dpg/main.py generate
- Depends on dobp-common-library and qubership-pipelines-common-library.

## Backward compatibility

- Old flow: not run.
- New flow: runs on PIPELINE_TYPE == GITAB_DEPLOY to produce the GitOps repository structure.

## Open items

- [ ] Remove its own deploy plan generation and consume the output of generate_dp. Owner Artem.
- [ ] Add local deployment descriptors. Owner Artem.
- [ ] Encrypt ARGO_DPG_CONTEXT.env, or let crypt do it. Owner Artem.
- [ ] Move to GitHub. phase2.
- [ ] Consider merging build.env.
