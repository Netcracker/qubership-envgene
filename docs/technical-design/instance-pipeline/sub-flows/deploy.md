# Deploy sub-flows

- [Deploy sub-flows](#deploy-sub-flows)
  - [Launch parameters](#launch-parameters)
  - [No-CMDB v2](#no-cmdb-v2)
    - [Deploy](#deploy)
    - [Deploy to a Blue-Green side](#deploy-to-a-blue-green-side)
  - [No-CMDB v1](#no-cmdb-v1)
  - [CMDB](#cmdb)

This document projects the main pipeline described in
[`flow.md`](/docs/technical-design/instance-pipeline/flow.md) onto the deploy scenarios across the
[No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2),
[No-CMDB v1](/docs/deployment-architecture.md#no-cmdb-v1), and
[CMDB](/docs/deployment-architecture.md#cmdb) architectures. It lists only the steps that actually fire for each,
plus the launch parameters that produce it. The step triggers are the single source of truth and live in
`flow.md` - this document does not redefine them, it only resolves them per scenario.

## Launch parameters

The parameters below select a scenario. See `flow.md` for the full definition of each variable.

| Parameter                | Values                    | Role in deploy                                                   |
| ------------------------ | ------------------------- | ---------------------------------------------------------------- |
| `PIPELINE_TYPE`          | `GITLAB_DEPLOY`, `LEGACY` | `GITLAB_DEPLOY` for No-CMDB v2; `LEGACY` for No-CMDB v1 and CMDB |
| `OPERATION_TYPE`         | `DEPLOY`, `CLEAN`, `BGD`  | `DEPLOY` selects a deploy scenario                               |
| `APPLICATION_VERSIONS`   | SD or DD                  | the applications to deploy                                       |
| `BG_NS_TARGET`           | `ORIGIN`, `PEER`          | physical Blue-Green side; only for a Blue-Green side deploy      |
| `ENV_BUILDER`            | `true`, `false`           | builds the env instance under No-CMDB v1 and CMDB                |
| `CMDB_IMPORT`            | `true`, `false`           | imports into the CMDB (CMDB architecture)                        |
| `GENERATE_EFFECTIVE_SET` | `true`, `false`           | generates the effective set (No-CMDB v1 architecture)            |

## No-CMDB v2

The [No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2) architecture is the modern composite deploy under
`PIPELINE_TYPE: GITLAB_DEPLOY`.

### Deploy

Build the env instance, compute the deploy plan from `APPLICATION_VERSIONS`, generate the effective set, and hand
it to Argo. The standalone
[management operations](/docs/technical-design/instance-pipeline/sub-flows/management-operations.md) run first
when their parameters are set.

Flow:

```text
1.1 preprocess -> (1.2 get_passport, 1.3 credential_rotation, 1.6 env_inventory_generation, 1.8 set_template_version - if requested)
              -> 1.9 process_env_template -> 1.10 appregdef_render -> 1.11 deploy_postfix_namespace_map
              -> 1.13 generate_deployment_plan -> 1.14 env_build -> 1.15 generate_effective_set
              -> 1.16 git_commit -> 1.17 generate_argocd_repo -> 1.18 es_pusher -> 1.20 postprocess
              -> [job 2] sync
```

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: DEPLOY
APPLICATION_VERSIONS: <SD or application versions>
```

Actions: `generate_deployment_plan` builds the delta from `APPLICATION_VERSIONS` and merges it onto the
repository full plan. `env_build` renders the env instance. `generate_effective_set` produces all contexts.
`generate_argocd_repo` and `es_pusher` publish the result to the deploy target repository, and the `sync` job
applies it.

### Deploy to a Blue-Green side

A deploy scoped to one Blue-Green namespace, selected by `BG_NS_TARGET` (`ORIGIN` or `PEER`). It covers a deploy
to the candidate side and a hotfix into the active side. The active/candidate intent is resolved upstream
(bg-controller API) to the physical `ORIGIN`/`PEER` side. It is a deploy (`OPERATION_TYPE: DEPLOY`), not a
Blue-Green operation (`OPERATION_TYPE: BGD`).

Flow: same as Deploy.

Launch parameters:

```yaml
PIPELINE_TYPE: GITLAB_DEPLOY
OPERATION_TYPE: DEPLOY
APPLICATION_VERSIONS: <SD or application versions>
BG_NS_TARGET: <ORIGIN|PEER>
```

Actions: identical to Deploy, except `generate_deployment_plan` binds each bare Blue-Green `deployPostfix` to the
`BG_NS_TARGET` side.

## No-CMDB v1

The [No-CMDB v1](/docs/deployment-architecture.md#no-cmdb-v1) architecture runs under `PIPELINE_TYPE: LEGACY` as
an à-la-carte set of steps. Build the env instance and generate the effective set in EnvGene from a Solution
Descriptor. The effective set is committed to the instance repository.

Flow:

```text
1.1 preprocess -> 1.9 process_env_template -> 1.10 appregdef_render -> 1.11 deploy_postfix_namespace_map
              -> 1.12 process_sd -> 1.14 env_build -> 1.15 generate_effective_set
              -> 1.16 git_commit -> 1.20 postprocess
```

Launch parameters:

```yaml
ENV_BUILDER: true
GENERATE_EFFECTIVE_SET: true
SD_VERSION: <sd version>   # or SD_DATA
# PIPELINE_TYPE defaults to LEGACY
```

Actions: `process_sd` merges the Solution Descriptor and adapts it to the deploy plan through `namespace-map.yml`
(produced by `deploy_postfix_namespace_map`). `env_build` renders the env instance, `generate_effective_set`
produces the effective set, and `git_commit` commits both to the instance repository.

## CMDB

The [CMDB](/docs/deployment-architecture.md#cmdb) architecture runs under `PIPELINE_TYPE: LEGACY` as an à-la-carte
set of steps. Build the env instance and import it into the CMDB. EnvGene does not generate the effective set;
the CMDB computes it.

Flow:

```text
1.1 preprocess -> 1.9 process_env_template -> 1.10 appregdef_render -> 1.14 env_build
              -> 1.16 git_commit -> 1.19 cmdb_import -> 1.20 postprocess
```

Launch parameters:

```yaml
ENV_BUILDER: true
CMDB_IMPORT: true
# PIPELINE_TYPE defaults to LEGACY
```

Actions: `env_build` renders the env instance, `git_commit` commits it, and `cmdb_import` imports it into the
CMDB.
