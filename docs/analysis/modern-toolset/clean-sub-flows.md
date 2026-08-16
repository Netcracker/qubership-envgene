# CLEAN sub-flows

- [CLEAN sub-flows](#clean-sub-flows)
  - [Launch parameters](#launch-parameters)
  - [Sub-flow 1 - CLEAN](#sub-flow-1---clean)
  - [Sub-flow 2 - CLEAN a Blue-Green side](#sub-flow-2---clean-a-blue-green-side)

This document projects the main pipeline described in [`flow.md`](/docs/analysis/modern-toolset/flow.md) onto the `CLEAN` operation.
It lists only the steps that actually fire for `OPERATION_TYPE: CLEAN`, plus the launch parameters that
produce it. The step triggers are the single source of truth and live in `flow.md` - this document does
not redefine them, it only resolves them for the scenario.

## Launch parameters

The parameters below select the sub-flow. See `flow.md` for the full definition of each variable.

| Parameter         | Values                    | Role in CLEAN                                                  |
|-------------------|---------------------------|----------------------------------------------------------------|
| `PIPELINE_TYPE`   | `GITLAB_DEPLOY`, `LEGACY` | CLEAN requires `GITLAB_DEPLOY`                                 |
| `OPERATION_TYPE`  | `CLEAN`, `DEPLOY`         | `CLEAN` selects this sub-flow                                  |
| `NAMESPACE_NAMES` | namespace names, or empty | the namespaces to clean. Empty means all namespaces of the env |

## Sub-flow 1 - CLEAN

`CLEAN` marks the target namespaces as cleaned and emits a cleanup context in the effective set. EnvGene
does not perform the cluster-side undeployment itself, downstream tooling consumes the effective set and
undeploys. A subsequent `DEPLOY` restores the marked namespaces.

Flow:

```text
1.1 preprocess -> 1.13 generate_deployment_plan -> 1.14 env_build -> 1.15 generate_effective_set
              -> 1.16 git_commit -> 1.18 es_pusher -> 1.20 postprocess
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: CLEAN
NAMESPACE_NAMES: env-1-bss;env-1-oss   # empty means all namespaces of the env
# APPLICATION_VERSIONS is not an input
```

Actions:

- `reduce_deployment_plan` (in `generate_deployment_plan`) removes the cleaned namespaces from the
  repository `deploy-plan.yml` using the plan filter in exclude mode (each namespace as a `!<namespace>`
  token). It updates the repository plan only. `CLEAN` produces no delta.
- `set_cleaned_mark` (in `env_build`) sets `cleaned: true` on the `namespace.yml` of each namespace in
  `NAMESPACE_NAMES` (all namespaces when empty). No other env instance content is modified.
- `generate_effective_set` is invoked with no deployment plan. Because `CLEAN` produces no delta deployment plan, no
  plan is passed to the calculator. The env-level `topology/` and `pipeline/` contexts are generated as
  always. The rest is marker-driven: for each namespace with `cleaned: true`, `.cleaned` is written into
  `deployment/<ns>/` and `runtime/<ns>/` (no app content), and `cleanup/<ns>/` is emitted. The cleaned
  namespaces are removed from `deployment/mapping.yaml` and `runtime/mapping.yaml`, and
  `cleanup/mapping.yaml` lists the cleaned namespaces only.
- `es_pusher` pushes the effective set with `ESPUSHER_OVERWRITE: true`, so the deploy target repository
  reflects the reduced state.

`1.14 env_build` fires only `set_cleaned_mark`. The rendering functions (`generate_composite_structure`,
`compute_composite_topology`, `generate_solution_structure`, `run_build_environment`) are `DEPLOY` only,
so the env instance is left otherwise untouched. `generate_argocd_repo` and the `sync` job do not fire
for `CLEAN`.

## Sub-flow 2 - CLEAN a Blue-Green side

Cleans one physical Blue-Green namespace (origin or peer) of a BG domain. Same mechanics as Sub-flow 1,
scoped to a single BG-side namespace. It is not a Blue-Green operation (`OPERATION_TYPE: BGD`), it is
`OPERATION_TYPE: CLEAN` with `NAMESPACE_NAMES` set to the origin or peer namespace name.

Flow:

```text
1.1 preprocess -> 1.13 generate_deployment_plan -> 1.14 env_build -> 1.15 generate_effective_set
              -> 1.16 git_commit -> 1.18 es_pusher -> 1.20 postprocess
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: CLEAN
NAMESPACE_NAMES: env-1-bss-origin   # or env-1-bss-peer
# APPLICATION_VERSIONS is not an input
```

Actions: identical to Sub-flow 1, scoped to the BG-side namespace. `reduce_deployment_plan` removes the
entries whose `namespace` is the BG-side namespace. `set_cleaned_mark` marks that namespace. The other BG
side and the BG state files are not touched, `CLEAN` is not a state operation.
