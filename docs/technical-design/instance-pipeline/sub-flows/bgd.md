# BGD sub-flows

- [BGD sub-flows](#bgd-sub-flows)
  - [Launch parameters](#launch-parameters)
  - [BGD state operations](#bgd-state-operations)
  - [BGD warmup](#bgd-warmup)

This document projects the main pipeline described in
[`flow.md`](/docs/technical-design/instance-pipeline/flow.md) onto the Blue-Green Deployment (BGD) operations:
the state operations and warmup. Each sub-flow lists only the steps that actually fire for a given
`BGD_OPERATION`, plus the launch parameters that produce it. The step triggers are the single source of truth and
live in `flow.md` - this document does not redefine them, it only resolves them per scenario.

BGD runs on the [No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2) architecture
(`PIPELINE_TYPE: GITLAB_DEPLOY`).

Deploying application versions to a Blue-Green side is a deploy, not a BGD operation. See
[Deploy to a Blue-Green side](/docs/technical-design/instance-pipeline/sub-flows/deploy.md#deploy-to-a-blue-green-side).

## Launch parameters

The parameters below select a sub-flow. See `flow.md` for the full definition of each variable.

| Parameter        | Values                                                   | Role in BGD                               |
| ---------------- | -------------------------------------------------------- | ----------------------------------------- |
| `PIPELINE_TYPE`  | `GITLAB_DEPLOY`, `LEGACY`                                | BGD requires `GITLAB_DEPLOY` (No-CMDB v2) |
| `OPERATION_TYPE` | `BGD`, `DEPLOY`                                          | `BGD` selects a BGD sub-flow              |
| `BGD_OPERATION`  | `warmup`, `commit`, `promote`, `rollback`, `init-domain` | the Blue-Green operation                  |

## BGD state operations

Applies to `BGD_OPERATION` `init-domain`, `promote`, `rollback`, and `commit`. Pure state change with no new
deploy.

Flow:

```text
1.1 preprocess -> 1.4 change_bg_state -> 1.16 git_commit -> 1.18 es_pusher -> 1.20 postprocess
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: BGD
BGD_OPERATION: init-domain      # or promote, rollback, commit
# the transition is derived from BGD_OPERATION + current state files
# APPLICATION_VERSIONS is not an input
```

Actions: `change_bg_state` applies the state transition on the state files. The effective set calculator is not
invoked: a state operation only flips BG state, it does not recompute the effective set.

## BGD warmup

Warmup (`BGD_OPERATION: warmup`) replicates the active namespace into the candidate.

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

Actions: `change_bg_state` applies the state transition on the state files. `warmup` copies the active namespace
into the candidate (rename). `generate_deployment_plan` synthesizes the delta from the `deploy-plan` (filter the
active side, rebind the namespace to the candidate). `generate_effective_set` and `generate_argocd_repo` then run
over the copied candidate namespace with that delta, and `sync` applies it. The candidate ends up as a replica of
the active, with versions taken from the full plan rather than a new `APPLICATION_VERSIONS`.

`1.14 env_build` deliberately does not fire. The candidate already carries the built env instance copied by
`warmup`, so there is nothing to render. The effective set is generated over that copy rather than over a fresh
build.
