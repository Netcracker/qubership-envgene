# BGD sub-flows

This document projects the main pipeline described in [`flow.md`](./flow.md) onto the Blue-Green Deployment
(BGD) scenarios. Each sub-flow lists only the steps that actually fire for a given `OPERATION_TYPE` and
`BGD_OPERATION`, plus the launch parameters that produce it. The step triggers are the single source of truth and live in `flow.md` -
this document does not redefine them, it only resolves them per scenario.

- [BGD sub-flows](#bgd-sub-flows)
  - [Launch parameters](#launch-parameters)
  - [Sub-flow 1 - BGD state operations](#sub-flow-1---bgd-state-operations)
  - [Sub-flow 2 - BGD warmup](#sub-flow-2---bgd-warmup)
  - [Sub-flow 3 - deploy to active or candidate](#sub-flow-3---deploy-to-active-or-candidate)

## Launch parameters

The parameters below select a sub-flow. See `flow.md` for the full definition of each variable.

| Parameter              | Values                                                                          | Role in BGD                          |
|------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| `PIPELINE_TYPE`        | `GITLAB_DEPLOY`, `LEGACY`                                                       | BGD requires `GITLAB_DEPLOY`         |
| `OPERATION_TYPE`       | `BGD`, `DEPLOY`                                                                 | `BGD` for any Blue-Green operation   |
| `BGD_OPERATION`        | `warmup`, `commit`, `promote`, `rollback`, `init-domain`                        | the Blue-Green operation, only when `OPERATION_TYPE: BGD` |
| `BG_NS_TARGET`         | `ORIGIN`, `PEER`                                                                | physical side; `ACTIVE`/`CANDIDATE` intent resolved upstream via bg-controller API |
| `APPLICATION_VERSIONS` | SD or application versions                                                      | required only when a deploy happens  |

## Sub-flow 1 - BGD state operations

Applies to `BGD_OPERATION` `init-domain`, `promote`, `rollback`, and `commit` (all with `OPERATION_TYPE: BGD`).
Pure state change with no new deploy.

Flow:

```text
1.1 preprocess -> 1.4 change_bg_state -> 1.15 generate_effective_set -> 1.16 git_commit
              -> 1.18 es_pusher -> 1.20 postprocess
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: BGD
BGD_OPERATION: init-domain      # or promote, rollback, commit
# the transition is derived from BGD_OPERATION + current state files
# APPLICATION_VERSIONS is not an input
```

Actions: `change_bg_state` applies the state transition on the state files.

## Sub-flow 2 - BGD warmup

Warmup (`OPERATION_TYPE: BGD`, `BGD_OPERATION: warmup`) replicates the active namespace into the candidate.

Flow:

```text
1.1 preprocess -> 1.4 change_bg_state -> 1.5 warmup -> 1.13 generate_deployment_plan -> 1.15 generate_effective_set
              -> 1.16 git_commit -> 1.17 generate_argocd_repo -> 1.18 es_pusher -> 1.20 postprocess
              -> [job 2] sync
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: BGD
BGD_OPERATION: warmup
```

Actions: `change_bg_state` applies the state transition on the state files. `warmup` copies the active env instance
into the candidate. `generate_deployment_plan`, `generate_effective_set`, and `generate_argocd_repo` then run over
that candidate copy, and `sync` applies it. The candidate ends up as a replica of the active, with versions taken
from the copied instance rather than a new `APPLICATION_VERSIONS`.

`1.14 env_build` deliberately does not fire. The candidate already carries the built env instance copied by
`warmup`, so there is nothing to render. The effective set is generated over that copy rather than over a
fresh build.

## Sub-flow 3 - deploy to active or candidate

A regular deploy scoped to one BG namespace, selected by `BG_NS_TARGET` (`ORIGIN` or `PEER`). It covers deploy-sd
to the candidate side and a hotfix into the active side. The candidate/active intent is
resolved upstream (bg-controller API) to the physical `ORIGIN`/`PEER` side. It is not a Blue-Green operation
(`OPERATION_TYPE: BGD`), it is `OPERATION_TYPE: DEPLOY`.

Flow:

```text
1.1 preprocess -> (1.2 get_passport, 1.3 credential_rotation, 1.6 inventory, 1.8 set_template_version - if requested)
              -> 1.9 process_env_template -> 1.10 appregdef_render -> 1.11 deploy_postfix_namespace_map
              -> 1.13 generate_deployment_plan -> 1.14 env_build -> 1.15 generate_effective_set
              -> 1.16 git_commit -> 1.17 generate_argocd_repo -> 1.18 es_pusher -> 1.20 postprocess -> [job 2] sync
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
