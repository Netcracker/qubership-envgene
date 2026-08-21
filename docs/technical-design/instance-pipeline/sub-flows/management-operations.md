# Management operations

- [Management operations](#management-operations)
  - [Launch parameters](#launch-parameters)
  - [Passport fetch](#passport-fetch)
  - [Credential rotation](#credential-rotation)
  - [Inventory generation](#inventory-generation)
  - [Template version bump](#template-version-bump)

This document projects the main pipeline described in
[`flow.md`](/docs/technical-design/instance-pipeline/flow.md) onto the standalone management operations: passport
fetch, credential rotation, inventory generation, and template version bump. Each modifies the instance
repository without a deploy. The step triggers are the single source of truth and live in `flow.md` - this
document does not redefine them, it only resolves them per operation.

Each operation is selected by its own parameter, independent of `PIPELINE_TYPE` and `OPERATION_TYPE`. They
run on all architectures ([No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2),
[No-CMDB v1](/docs/deployment-architecture.md#no-cmdb-v1), and [CMDB](/docs/deployment-architecture.md#cmdb)). The
operations are combinable in a single run and can also precede a [deploy](/docs/technical-design/instance-pipeline/sub-flows/deploy.md).
Passport fetch and credential rotation cannot be combined with each other.

## Launch parameters

Each operation runs when its parameter is set. See `flow.md` for the full definition of each variable.

| Operation             | Parameter                                        |
| --------------------- | ------------------------------------------------ |
| Passport fetch        | `GET_PASSPORT: true`                             |
| Credential rotation   | `CRED_ROTATION_PAYLOAD`                          |
| Inventory generation  | `ENV_INVENTORY_CONTENT` or `ENV_SPECIFIC_PARAMS` |
| Template version bump | `ENV_TEMPLATE_VERSION`                           |

## Passport fetch

Fetch the Cloud Passport for the environment's cluster.

Flow:

```text
1.1 preprocess -> 1.2 get_passport -> 1.16 git_commit -> 1.20 postprocess
```

Launch parameters:

```yaml
GET_PASSPORT: true
```

Actions: `get_passport` triggers the discovery repository pipeline and downloads the resulting Cloud Passport into
the environment.

## Credential rotation

Rotate the environment's credentials from the supplied payload.

Flow:

```text
1.1 preprocess -> 1.3 credential_rotation -> 1.16 git_commit -> 1.20 postprocess
```

Launch parameters:

```yaml
CRED_ROTATION_PAYLOAD: <payload>
```

Actions: `credential_rotation` rotates the environment's credentials from `CRED_ROTATION_PAYLOAD`.

## Inventory generation

Generate or update the Environment Inventory.

Flow:

```text
1.1 preprocess -> 1.6 env_inventory_generation -> 1.16 git_commit -> 1.20 postprocess
```

Launch parameters:

```yaml
ENV_INVENTORY_CONTENT: <inventory content>   # or ENV_SPECIFIC_PARAMS
```

Actions: `env_inventory_generation` writes `Inventory/env_definition.yml` and its objects from
`ENV_INVENTORY_CONTENT` (or `ENV_SPECIFIC_PARAMS`).

## Template version bump

Set the Environment Template version.

Flow:

```text
1.1 preprocess -> 1.8 set_template_version -> 1.16 git_commit -> 1.20 postprocess
```

Launch parameters:

```yaml
ENV_TEMPLATE_VERSION: <template artifact:version>
```

Actions: `set_template_version` sets the template version in `env_definition.yml` from `ENV_TEMPLATE_VERSION`.
