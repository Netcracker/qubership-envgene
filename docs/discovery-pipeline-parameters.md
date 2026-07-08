
# Discovery Pipeline Parameters

- [Discovery Pipeline Parameters](#discovery-pipeline-parameters)
  - [Parameters](#parameters)
    - [`ENV_NAME`](#env_name)

The following are the launch parameters for the Discovery repository pipeline.

The Discovery pipeline performs Cloud Passport generation for a target cluster. It is triggered automatically from the [Instance pipeline](/docs/envgene-pipelines.md) when [`GET_PASSPORT: true`](/docs/instance-pipeline-parameters.md#get_passport), or can be triggered manually via the GitLab UI.

All parameters are of the string data type.

> [!IMPORTANT]
> The Discovery pipeline recognises and processes **only the parameter listed on this page**. Passing any variable not documented here has no effect on pipeline behaviour and will be silently ignored.

## Parameters

### `ENV_NAME`

**Description**: Specifies the target environment for which Cloud Passport generation will be triggered. Uses the `<cluster-name>/<env-name>` notation.

Unlike the Instance pipeline's [`ENV_NAMES`](/docs/instance-pipeline-parameters.md#env_names), the Discovery pipeline processes **one environment per run**.

When triggered automatically from the Instance pipeline, `ENV_NAME` is set by EnvGene to match the environment being processed.

**Default Value**: None

**Mandatory**: Yes

**Example**:

- `ocp-01/platform`
- `k8s-01/env-1`
