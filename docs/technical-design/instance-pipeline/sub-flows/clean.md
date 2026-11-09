# CLEAN sub-flows

- [CLEAN sub-flows](#clean-sub-flows)
  - [Launch parameters](#launch-parameters)
  - [CLEAN a whole environment](#clean-a-whole-environment)
  - [CLEAN selected namespaces](#clean-selected-namespaces)

This document projects the main pipeline described in
[`flow.md`](/docs/technical-design/instance-pipeline/flow.md) onto the `CLEAN` operation. It lists only the steps
that actually fire for `OPERATION_TYPE: CLEAN`, plus the launch parameters that produce it. The step triggers are
the single source of truth and live in `flow.md` - this document does not redefine them, it only resolves them
for the scenario.

`CLEAN` empties the target namespaces' deployment and runtime content in the effective set and writes a
`.cleaned` marker in their place. No cleanup context is produced. EnvGene does not perform the cluster-side
undeployment itself. Downstream tooling consumes the effective set and undeploys. A subsequent `DEPLOY` restores
the cleaned namespaces, where `argo-dpg generate structure` pushes the rebuilt effective set. The two sub-flows
differ only in scope, set by `NAMESPACE_NAMES`.

`CLEAN` runs on the [No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2) architecture
(`PIPELINE_TYPE: GITLAB_DEPLOY`).

For what cleanup is across both deployment architectures, and the output each one produces, see
[Cleanup](/docs/features/clean.md).

## Launch parameters

The parameters below select the sub-flow. See `flow.md` for the full definition of each variable.

| Parameter         | Values                    | Role in CLEAN                                                          |
| ----------------- | ------------------------- | ---------------------------------------------------------------------- |
| `PIPELINE_TYPE`   | `GITLAB_DEPLOY`, `LEGACY` | CLEAN requires `GITLAB_DEPLOY` (No-CMDB v2)                            |
| `OPERATION_TYPE`  | `CLEAN`, `DEPLOY`         | `CLEAN` selects this sub-flow                                          |
| `NAMESPACE_NAMES` | namespace names, or empty | empty cleans the whole environment; a list cleans the named namespaces |

## CLEAN a whole environment

`NAMESPACE_NAMES` is empty, so every namespace of the environment is cleaned.

Flow:

```text
1.1 preprocess -> 1.17 cleanup -> 1.18 git_commit -> 1.22 postprocess
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: CLEAN
NAMESPACE_NAMES: ""   # empty cleans the whole environment
# APPLICATION_VERSIONS is not an input
```

Actions:

- The `cleanup` step runs `reduce_deployment_plan`, which removes the cleaned namespaces' entries from the
  repository `deploy-plan.yml`.
- The `cleanup` step then runs `clean_effective_set`, performed by `argo-dpg cleanup structure`, which first
  cleans the effective-set content. Because `NAMESPACE_NAMES` is empty, it cleans every namespace of the
  environment, taken from the topology context read at its contractual location in the effective set. For each
  namespace it removes the `deployment` and `runtime` context content under
  `effective-set/<deployment|runtime>/<namespace>/<application-name>/`, keeps `<application-name>`, and writes
  `effective-set/<deployment|runtime>/<namespace>/.cleaned`. It warns if a namespace is absent from the effective
  set or already cleaned.
- The same clean then removes each cleaned application's ArgoCD Application CR manifest `argo-app.yaml` from its
  `deployment` application directory, where `argo-dpg generate structure` wrote it, so the cleaned namespaces are
  detached from ArgoCD.
- `argo-dpg` then pushes the effective set to the ES repository in overwrite mode, so the repository mirrors the
  emptied state and the removed content is deleted there as well.

## CLEAN selected namespaces

`NAMESPACE_NAMES` lists the namespaces to clean. A Blue-Green side namespace (origin or peer) is cleaned as any
other namespace; the other side and the BG state files are not touched, `CLEAN` is not a state operation. The
Blue-Green controller namespace, and any namespace that is neither an origin nor a peer side, is cleaned in
exactly the same way - `CLEAN` marks every target namespace regardless of its Blue-Green role, and
`reduce_deployment_plan` removes only the deploy plan entries that exist for it.

Flow:

```text
1.1 preprocess -> 1.17 cleanup -> 1.18 git_commit -> 1.22 postprocess
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: CLEAN
NAMESPACE_NAMES: env-1-bss;env-1-oss   # or a single BG side, e.g. env-1-bss-origin
# APPLICATION_VERSIONS is not an input
```

Actions:

- The `cleanup` step runs `reduce_deployment_plan`, which removes the cleaned namespaces' entries from the
  repository `deploy-plan.yml`.
- The `cleanup` step then runs `clean_effective_set`, performed by `argo-dpg cleanup structure`, which first
  cleans the effective-set content. It cleans the namespaces listed in `NAMESPACE_NAMES`, rather than every
  namespace from the topology context. For each namespace it removes the `deployment` and `runtime` context
  content under `effective-set/<deployment|runtime>/<namespace>/<application-name>/`, keeps `<application-name>`,
  and writes `effective-set/<deployment|runtime>/<namespace>/.cleaned`. It warns if a namespace is absent from
  the effective set or already cleaned.
- The same clean then removes each cleaned application's ArgoCD Application CR manifest `argo-app.yaml` from its
  `deployment` application directory, where `argo-dpg generate structure` wrote it, so the cleaned namespaces are
  detached from ArgoCD.
- `argo-dpg` then pushes the effective set to the ES repository in overwrite mode, so the repository mirrors the
  emptied state and the removed content is deleted there as well.
