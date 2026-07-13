
# Template Pipeline Parameters

- [Template Pipeline Parameters](#template-pipeline-parameters)
  - [Parameters](#parameters)
    - [`INCLUDE_BUILDS`](#include_builds)
    - [`PROMOTE_MODE`](#promote_mode)
    - [`ENV_TEMPLATE_TEST`](#env_template_test)
    - [`ENV_NAMES`](#env_names)
    - [`ENV_BUILDER`](#env_builder)

The following are the launch parameters for the Template repository pipeline. These parameters control the build, promotion, and optional template-testing steps of the pipeline.

The Template pipeline is triggered automatically on every push or merge-request event in the Template repository. The parameters below can be set in the GitLab CI/CD pipeline variables UI before triggering a manual run, or pre-configured in the repository's `gitlab-ci/pipeline_vars.yaml`.

All parameters are of the string data type.

> [!IMPORTANT]
> The Template pipeline recognises and processes **only the parameters listed on this page**. Passing any variable not documented here has no effect on pipeline behaviour and will be silently ignored.

## Parameters

### `INCLUDE_BUILDS`

**Description**: Controls whether the build jobs run in the pipeline. Set to `false` to skip template packaging and artifact creation without aborting the rest of the pipeline.

**Default Value**: `true`

**Mandatory**: No

**Example**: `false`

### `PROMOTE_MODE`

**Description**: Controls when the template artifact promotion job runs.

**Allowed values**:

- `semver` — promote only for Git tags that match semantic versioning (e.g., `v1.2.3`). Use for official releases.
- `always` — promote on every pipeline run regardless of whether a tag was pushed. Use for continuous delivery or testing pipelines.
- `manual` — the promotion job is created as a manual action (a play button in the GitLab UI). Use when human approval is required before publishing.

**Default Value**: `always`

**Mandatory**: No

**Example**: `semver`

### `ENV_TEMPLATE_TEST`

**Description**: Activates template-testing mode. When set to `true`, the pipeline triggers an Instance pipeline run against the template under development before publishing the artifact. This validates that the template renders correctly against real environments.

When `ENV_TEMPLATE_TEST` is `true`, the parameters [`ENV_NAMES`](#env_names), [`ENV_BUILDER`](#env_builder) become active and are forwarded to the triggered Instance pipeline.

When `ENV_TEMPLATE_TEST` is `true`, the `git_commit` job in the triggered Instance pipeline is skipped — generated output is not written back to the Instance repository.

**Default Value**: `false`

**Mandatory**: No

**Example**: `true`

### `ENV_NAMES`

**Description**: Specifies the target environments for the template test run. Forwarded to the Instance pipeline as [`ENV_NAMES`](instance-pipeline-parameters.md#env_names).

Only active when [`ENV_TEMPLATE_TEST`](#env_template_test) is `true`.

**Default Value**: `env_template_test`

**Mandatory**: Conditional — required when `ENV_TEMPLATE_TEST=true`

**Example**:

- Single environment: `ocp-01/platform`
- Multiple environments (use Shift+Enter in the GitLab UI for newline separation): `k8s-01/env-1\nk8s-01/env-2`

### `ENV_BUILDER`

**Description**: Feature flag forwarded to the Instance pipeline. When `true`, the Environment Instance generation job runs as part of the template test. See [`ENV_BUILDER`](instance-pipeline-parameters.md#env_builder).

Only active when [`ENV_TEMPLATE_TEST`](#env_template_test) is `true`.

**Default Value**: `true`

**Mandatory**: No

**Example**: `true`
