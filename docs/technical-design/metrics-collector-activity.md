# `metrics_collector_activity`

- [`metrics_collector_activity`](#metrics_collector_activity)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Request body mapping](#request-body-mapping)
    - [Event fields](#event-fields)
    - [`data` fields](#data-fields)
    - [`data.steps` item fields](#datasteps-item-fields)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

The `metrics_collector_activity` integration sends one `start` and one `stop` CloudEvents 1.0 HTTP
event to Metrics Collector Service at `POST /api/v1/activity` per Instance pipeline run.

## Input parameters

| Parameter               | Source | Required | Default | Values / format | Effect |
| ----------------------- | ------ | -------- | ------- | --------------- | ------ |
| `METRICS_COLLECTOR_URL` | CI/CD  | No       | None    | Base URL        | When empty or absent, the Instance pipeline skips all Metrics Collector POSTs. Otherwise events POST to `{METRICS_COLLECTOR_URL}/api/v1/activity`. |

## Request body mapping

### Event fields

| Field           | Required | Source | Example |
| --------------- | -------- | ------ | ------- |
| `specversion`   | Yes      | `"1.0"` | `"1.0"` |
| `id`            | Yes      | EnvGene (UUID v4) | `"123e4567-e89b-12d3-a456-426614174000"` |
| `source`        | Yes      | `CI_PROJECT_URL` | `"https://gitlab.example.com/platform/env-instance-repo"` |
| `type`          | Yes      | `"start"` or `"stop"` | `"start"` |
| `kind`          | Yes      | `"pipeline"` | `"pipeline"` |
| `kindversion`   | Yes      | `"1.0"` | `"1.0"` |
| `traceid`       | Yes      | Environment variable `METRICS_COLLECTOR_TRACE_ID` from parent pipeline, or EnvGene (UUID v4) | `"4bf92f3577b34da6a3ce929d0e0e4736"` |
| `parentid`      | No       | Environment variable `METRICS_COLLECTOR_PARENT_ID` from parent pipeline, or `""` | `"d72800f6-29c7-42b5-a9ab-519f026bcad5"` |
| `technicalname` | Yes      | `CI_JOB_NAME` | `"instance_pipeline"` |
| `displayname`   | No       | Pipeline context | `"EnvGene Instance Pipeline"` |
| `jobid`         | Yes      | `CI_JOB_ID` | `"5550001"` |
| `pipelineid`    | Yes      | `CI_PIPELINE_ID` | `"987654"` |
| `projectid`     | Yes      | `CI_PROJECT_ID` | `"12345"` |
| `status`        | No       | `IN_PROGRESS` on `start`; run outcome on `stop` | `"SUCCESS"` |
| `time`          | Yes      | Current UTC time | `"2026-06-12T14:00:00Z"` |
| `data`          | Yes      | See [`data` fields](#data-fields) | *(object)* |

Terminal `status` on `stop`: `SUCCESS`, `FAILED`, `CANCELLED`, `SKIPPED`, `UNKNOWN`.

### `data` fields

| Field             | Required | `start` | `stop` | Source |
| ----------------- | -------- | ------- | ------ | ------ |
| `envgeneVersion`  | Yes      | Yes     | Yes    | EnvGene build version |
| `inputParameters` | Yes      | Yes     | Yes    | Selected pipeline environment variables; at minimum `PIPELINE_TYPE` when set |
| `steps`           | Yes      | No      | Yes    | Instance pipeline step results from the orchestrator |

### `data.steps` item fields

| Field        | Required | Source |
| ------------ | -------- | ------ |
| `name`       | Yes      | Step name |
| `status`     | Yes      | `SUCCESS`, `FAILED`, or `SKIPPED` |
| `durationMs` | No       | Step duration in milliseconds; omitted when the step was skipped |

## Processing flow

1. **Decide whether to run**

   1. The Instance pipeline reads CI/CD variable `METRICS_COLLECTOR_URL`.

   2. The Instance pipeline skips Metrics Collector activity when `METRICS_COLLECTOR_URL` is empty or
      absent.

2. **Resolve correlation identifiers**

   1. EnvGene generates event field `id` as a new UUID v4 before each POST.

   2. EnvGene sets `traceid` from environment variable `METRICS_COLLECTOR_TRACE_ID` when the parent
      pipeline passes it. Otherwise EnvGene generates a new UUID v4 for the run.

   3. EnvGene sets `parentid` from environment variable `METRICS_COLLECTOR_PARENT_ID` when the parent
      pipeline passes it. Otherwise EnvGene sends `""`.

   4. When `ENV_NAMES` lists multiple environments, each child process inherits
      `METRICS_COLLECTOR_TRACE_ID` from the job environment and sends its own `start` and `stop`
      events.

3. **Build event payload**

   1. EnvGene sets `data.envgeneVersion` to the EnvGene build version.

   2. EnvGene sets `data.inputParameters` from selected pipeline environment variables. At minimum,
      `PIPELINE_TYPE` is included when set.

   3. EnvGene sets the remaining event fields from [Event fields](#event-fields).

4. **Send `start` event**

   1. The Instance pipeline sends `type: start` with `status: IN_PROGRESS` when the Instance pipeline
      run begins, before the first step executes.

   2. EnvGene sets event field `time` to the current UTC timestamp.

   3. EnvGene POSTs the event to `/api/v1/activity`.

   4. The `start` event does not include `data.steps`.

5. **Collect step results**

   1. The Instance pipeline records one result per registered step in fixed run order: `get_passport`,
      `credential_rotation`, `change_bg_state`, `warmup`, `env_inventory_generation`,
      `set_template_version`, `appregdef_render`, `deploy_postfix_namespace_map`, `process_sd`,
      `migrate_sd_to_deploy_plan`, `process_deployment_plan`, `env_build`, `generate_effective_set`,
      `git_commit`.

   2. For each step, the Instance pipeline records `name`, `status` (`SUCCESS`, `FAILED`, or
      `SKIPPED`), and `durationMs` when the step ran.

6. **Send `stop` event**

   1. The Instance pipeline sends `type: stop` when the run finishes, including on step failure.

   2. EnvGene sets terminal `status` to `SUCCESS`, `FAILED`, `CANCELLED`, `SKIPPED`, or `UNKNOWN`.

   3. EnvGene sets `data.steps` from the orchestrator step results.

   4. EnvGene sets event field `time` to the current UTC timestamp and reuses the same `traceid` and
      `parentid` as the matching `start` event.

   5. EnvGene POSTs the event to `/api/v1/activity`.

## Result

1. Metrics Collector Service receives one `start` event per Instance pipeline run when
   `METRICS_COLLECTOR_URL` is set.

2. Metrics Collector Service receives one `stop` event when the run finishes, with
   `data.envgeneVersion`, `data.inputParameters`, and step results in `data.steps`.

## Error handling

**1a.** The Instance pipeline skips Metrics Collector activity when CI/CD variable
`METRICS_COLLECTOR_URL` is empty or absent. The Instance pipeline run continues.

**6a.** EnvGene logs the failure and continues the Instance pipeline run when Metrics Collector
Service returns an error or is unavailable. EnvGene does not retry the POST.

**6b.** EnvGene logs the failure and continues the Instance pipeline run when the serialized event
body exceeds 1 MiB.

## Example

`start` event:

```json
{
  "specversion": "1.0",
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "start",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "instance_pipeline",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:00:00Z",
  "data": {
    "envgeneVersion": "1.2.3",
    "inputParameters": {
      "PIPELINE_TYPE": "GITLAB_DEPLOY"
    }
  }
}
```

`stop` event:

```json
{
  "specversion": "1.0",
  "id": "223e4567-e89b-12d3-a456-426614174001",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "stop",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "instance_pipeline",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:30:00Z",
  "data": {
    "envgeneVersion": "1.2.3",
    "inputParameters": {
      "PIPELINE_TYPE": "GITLAB_DEPLOY"
    },
    "steps": [
      { "name": "get_passport", "status": "SKIPPED" },
      { "name": "env_build", "status": "SUCCESS", "durationMs": 120000 },
      { "name": "git_commit", "status": "SUCCESS", "durationMs": 15000 }
    ]
  }
}
```

## Related documentation

- [Metrics Collector events](/docs/features/metrics-collector-events.md)
- [Instance pipeline flow](/docs/technical-design/instance-pipeline/flow.md)
