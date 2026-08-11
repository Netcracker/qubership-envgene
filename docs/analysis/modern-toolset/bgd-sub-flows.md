# BGD sub-flows

This document projects the main pipeline described in [`flow.md`](./flow.md) onto the Blue-Green Deployment
(BGD) scenarios. Each sub-flow lists only the steps that actually fire for a given `OPERATION_TYPE`, plus the
launch parameters that produce it. The step triggers are the single source of truth and live in `flow.md` -
this document does not redefine them, it only resolves them per scenario.

- [BGD sub-flows](#bgd-sub-flows)
  - [Launch parameters](#launch-parameters)
  - [Sub-flow 1 - BGD state operations](#sub-flow-1---bgd-state-operations)
  - [Sub-flow 2 - BGD-WARMUP](#sub-flow-2---bgd-warmup)
  - [Sub-flow 3 - deploy to active or candidate](#sub-flow-3---deploy-to-active-or-candidate)

## Launch parameters

The parameters below select a sub-flow. See `flow.md` for the full definition of each variable.

| Parameter              | Values                                                                          | Role in BGD                          |
|------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| `PIPELINE_TYPE`        | `GITLAB_DEPLOY`, `LEGACY`                                                       | BGD requires `GITLAB_DEPLOY`         |
| `OPERATION_TYPE`       | `BGD-INIT`, `BGD-WARMUP`, `BGD-PROMOTE`, `BGD-ROLLBACK`, `BGD-COMMIT`, `DEPLOY` | selects the sub-flow                 |
| `BG_NS_TARGET`         | `ORIGIN`, `PEER`                                                                | physical side; `ACTIVE`/`CANDIDATE` intent resolved upstream via bg-controller API |
| `APPLICATION_VERSIONS` | SD or application versions                                                      | required only when a deploy happens  |

## Sub-flow 1 - BGD state operations

Applies to `BGD-INIT`, `BGD-PROMOTE`, `BGD-ROLLBACK`, and `BGD-COMMIT`. Pure state change with no new deploy.

Flow:

```text
1.1 preprocess -> 1.5 bg_manage -> 1.13 generate_effective_set -> 1.16 postprocess
              -> 1.17 git_commit -> 1.18 es_pusher
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: BGD-INIT        # or BGD-PROMOTE, BGD-ROLLBACK, BGD-COMMIT
# the transition is derived from OPERATION_TYPE + current state files
# APPLICATION_VERSIONS is not an input
```

Actions: `bg_manage` applies the state transition on the state files.

## Sub-flow 2 - BGD-WARMUP

`BGD-WARMUP` replicates the active namespace into the candidate.

Flow:

```text
1.1 preprocess -> 1.5 bg_manage -> 1.11 generate_deployment_plan -> 1.13 generate_effective_set
              -> 1.14 generate_argocd_repo -> 1.16 postprocess -> 1.17 git_commit -> 1.18 es_pusher
              -> [job 2] sync
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: BGD-WARMUP
```

Actions: `bg_manage` applies the state transition on the state files. `bg_manage` copies the active env instance
into the candidate. `generate_deployment_plan`, `generate_effective_set`, and `generate_argocd_repo` then run over
that candidate copy, and `sync` applies it. The candidate ends up as a replica of the active, with versions taken
from the copied instance rather than a new `APPLICATION_VERSIONS`.

`1.12 env_build` deliberately does not fire. The candidate already carries the built env instance copied by
`bg_manage`, so there is nothing to render. The effective set is generated over that copy rather than over a
fresh build.

## Sub-flow 3 - deploy to active or candidate

A regular deploy scoped to one BG namespace, selected by `BG_NS_TARGET` (`ORIGIN` or `PEER`). It covers deploy-sd
to the candidate side and a hotfix into the active side. The candidate/active intent is
resolved upstream (bg-controller API) to the physical `ORIGIN`/`PEER` side. It is not a `BGD-*` operation, it is
`OPERATION_TYPE: DEPLOY`.

Flow:

```text
1.1 preprocess -> (1.2/1.3 passport, 1.4 credential_rotation, 1.6 inventory - if requested)
              -> 1.8 process_env_template -> 1.9 app_reg_def_process -> 1.11 generate_deployment_plan
              -> 1.12 env_build -> 1.13 generate_effective_set -> 1.14 generate_argocd_repo
              -> 1.16 postprocess -> 1.17 git_commit -> 1.18 es_pusher -> [job 2] sync
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: DEPLOY
APPLICATION_VERSIONS: <SD or application versions>
BG_NS_TARGET: <ORIGIN|PEER>
```

Actions: this is the full deploy chain, including `env_build`. Unlike Sub-flow 2 it renders a fresh build
and deploys the versions from `APPLICATION_VERSIONS` rather than a copy of the active.
