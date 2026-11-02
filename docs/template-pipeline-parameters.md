
# Template Pipeline Parameters

- [Template Pipeline Parameters](#template-pipeline-parameters)
  - [Parameters](#parameters)
    - [`INCLUDE_BUILDS`](#include_builds)
    - [`PROMOTE_MODE`](#promote_mode)

The following are the launch parameters for the Template repository pipeline. These parameters control the build and promotion steps of the pipeline.

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
