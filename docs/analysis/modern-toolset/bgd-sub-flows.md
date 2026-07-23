# BGD sub-flows

This document projects the main pipeline described in [`flow.md`](./flow.md) onto the Blue-Green Deployment
(BGD) scenarios. Each sub-flow lists only the steps that actually fire for a given `OPERATION_TYPE`, plus the
launch parameters that produce it. The step triggers are the single source of truth and live in `flow.md` -
this document does not redefine them, it only resolves them per scenario.

- [BGD sub-flows](#bgd-sub-flows)
  - [Launch parameters](#launch-parameters)
  - [Sub-flow 1 - BGD state operations](#sub-flow-1---bgd-state-operations)
  - [Sub-flow 2 - BGD-WARMUP (replicate active into candidate)](#sub-flow-2---bgd-warmup-replicate-active-into-candidate)
  - [Sub-flow 3 - deploy to active or candidate](#sub-flow-3---deploy-to-active-or-candidate)
  - [Design notes](#design-notes)

## Launch parameters

The parameters below select a sub-flow. See `flow.md` for the full definition of each variable.

| Parameter              | Values                                                                          | Role in BGD                          |
|------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| `PIPELINE_TYPE`        | `GITLAB_DEPLOY`, `LEGACY`                                                       | BGD requires `GITLAB_DEPLOY`         |
| `OPERATION_TYPE`       | `BGD-INIT`, `BGD-WARMUP`, `BGD-PROMOTE`, `BGD-ROLLBACK`, `BGD-COMMIT`, `DEPLOY` | selects the sub-flow                 |
| `BG_NS_TARGET`         | `ACTIVE`, `CANDIDATE`                                                           | selects `deployPostfix -> namespace` |
| `TARGET_BG_STATE`      | object (origin/peer namespace + state, controller namespace)                    | target pair for the transition       |
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
TARGET_BG_STATE: <target origin/peer pair for the transition>
# APPLICATION_VERSIONS is not an input
```

Actions: `bg_manage` applies the state transition on the state files. During `generate_effective_set`, envgene
writes the `active`/`candidate` status into the `topology/bg_domain` block of the effective set, so the effective
set changes. Then `git_commit` and `es_pusher` persist and push it. No deployment plan, no ArgoCD structure, no
`sync`.

Notes:

- `BGD-PROMOTE` (candidate becomes active, traffic switch) deliberately does not run `generate_argocd_repo` or
  `sync`. The traffic switch is the BG operator's responsibility and is intentionally outside this pipeline.
- `BGD-COMMIT` (legacy becomes idle) does not clean the legacy namespace by design. The bg-controller performs
  the scale down, not a clean, so this flow only saves the state.

## Sub-flow 2 - BGD-WARMUP (replicate active into candidate)

`BGD-WARMUP` replicates the active namespace into the candidate. It does not deploy a new version - it copies the
active env instance into the candidate and deploys that copy, so the candidate becomes a replica of the active.

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
TARGET_BG_STATE: <target pair, candidate namespace populated>
# the candidate is implied by BGD-WARMUP, no BG_NS_TARGET is needed
# APPLICATION_VERSIONS is not a new input, the versions come from the copied active instance
```

Actions: `bg_manage` copies the active env instance into the candidate. `generate_deployment_plan`,
`generate_effective_set`, and `generate_argocd_repo` then run over that candidate copy, and `sync` applies it.
The candidate ends up as a replica of the active, with versions taken from the copied instance rather than a new
`APPLICATION_VERSIONS`.

`1.12 env_build` deliberately does not fire. The candidate already carries the built env instance copied by
`bg_manage`, so there is nothing to render. The effective set is generated over that copy rather than over a
fresh build.

## Sub-flow 3 - deploy to active or candidate

A regular deploy scoped to one BG namespace, selected by `BG_NS_TARGET`. It covers deploy-sd to the candidate
(`BG_NS_TARGET: CANDIDATE`, the main BGD deploy case) and a hotfix into the active (`BG_NS_TARGET: ACTIVE`). It
is not a `BGD-*` operation, it is `OPERATION_TYPE: DEPLOY`.

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
BG_NS_TARGET: CANDIDATE        # or ACTIVE for a hotfix into the active namespace
# filters (DEPLOY_POSTFIXES / NAMESPACE_NAMES / ...) narrow the scope further
```

Actions: this is the full deploy chain, including `env_build`, scoped to one BG namespace through
`BG_NS_TARGET`. `CANDIDATE` deploys the SD to the candidate (the JCPR-2861 selected case, always candidate for
deploy-sd), `ACTIVE` deploys a hotfix to the active. Unlike Sub-flow 2 it renders a fresh build and deploys the
versions from `APPLICATION_VERSIONS` rather than a copy of the active.

## Design notes

1. Warmup replicates the active into the candidate. `bg_manage` copies the active env instance into the
   candidate and that copy is deployed. It does not deploy a new version, and `env_build` is intentionally not
   run.
2. `BGD-PROMOTE` does not run `generate_argocd_repo` or `sync`. The traffic switch is the BG operator's
   responsibility, outside this pipeline.
3. Deploy to active or candidate is `OPERATION_TYPE: DEPLOY` with `BG_NS_TARGET: ACTIVE` or `CANDIDATE`, a
   scope selector rather than a separate `BGD-*` operation. Deploy-sd always targets the candidate, a hotfix
   targets the active.
4. `BG_NS_TARGET` (`ACTIVE` or `CANDIDATE`) is the selector that resolves `deployPostfix -> namespace` in
   Sub-flow 3. Warmup does not use it, its target is fixed to the candidate. The selector data source and
   authority are tracked in `flow.md`.
5. The `OPERATION_TYPE` gives the transition type, `TARGET_BG_STATE` gives the authoritative namespace-to-role
   mapping from the bg-controller. EnvGene uses it to write the `active`/`candidate` status into the effective
   set and to validate its own state files against the bg-controller. The role part of `TARGET_BG_STATE`
   partially duplicates the state files, its non-redundant purpose is that cross-check against the authority.
   The structure of `TARGET_BG_STATE` is not final, see the `AI[phase2-bgd]` note in `flow.md`.
