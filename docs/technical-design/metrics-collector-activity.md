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
  - [Examples](#examples)
    - [Pipeline with one job `env_prepare`](#pipeline-with-one-job-env_prepare)
    - [Pipeline with jobs `env_prepare` and `sync`](#pipeline-with-jobs-env_prepare-and-sync)
  - [Related documentation](#related-documentation)

## Description

The `metrics_collector_activity` integration sends CloudEvents 1.0 HTTP events to Metrics Collector
Service at `POST /api/v1/activity` for an Instance pipeline run.

EnvGene reports pipeline activity from `before_script`, during job activity, and from `after_script`:

1. `type: start` from `before_script` when the pipeline begins.
2. `type: running` during job activity for each job that runs (`env_prepare`, and `sync` when
   present).
3. `type: stop` from `after_script` when the pipeline finishes.

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
| `type`          | Yes      | `"start"`, `"running"`, or `"stop"` | `"start"` |
| `kind`          | Yes      | `"pipeline"` | `"pipeline"` |
| `kindversion`   | Yes      | `"1.0"` | `"1.0"` |
| `traceid`       | Yes      | Environment variable `METRICS_COLLECTOR_TRACE_ID` from parent pipeline, or EnvGene (UUID v4) | `"4bf92f3577b34da6a3ce929d0e0e4736"` |
| `parentid`      | No       | Environment variable `METRICS_COLLECTOR_PARENT_ID` from parent pipeline, or `""` | `"d72800f6-29c7-42b5-a9ab-519f026bcad5"` |
| `technicalname` | Yes      | `CI_JOB_NAME` | `"env_prepare"` |
| `displayname`   | No       | Pipeline context | `"EnvGene Instance Pipeline"` |
| `jobid`         | Yes      | `CI_JOB_ID` | `"5550001"` |
| `pipelineid`    | Yes      | `CI_PIPELINE_ID` | `"987654"` |
| `projectid`     | Yes      | `CI_PROJECT_ID` | `"12345"` |
| `status`        | No       | Example: `IN_PROGRESS`, `SUCCESS`, `FAILED` | `"SUCCESS"` |
| `time`          | Yes      | Current UTC time | `"2026-06-12T14:00:00Z"` |
| `data`          | Yes      | See [`data` fields](#data-fields) | *(object)* |

Terminal `status` values: `SUCCESS`, `FAILED`, `CANCELLED`, `SKIPPED`, `UNKNOWN`.

### `data` fields

| Field             | Required | `start` | `running` (job in progress) | `running` (job finished) | `stop` | Source |
| ----------------- | -------- | ------- | --------------------------- | ------------------------ | ------ | ------ |
| `envgeneVersion`  | Yes      | Yes     | Yes                         | Yes                      | Yes    | EnvGene build version |
| `inputParameters` | Yes      | Yes     | Yes                         | Yes                      | Yes    | Selected pipeline environment variables; at minimum `PIPELINE_TYPE` when set |
| `steps`           | No       | No      | Yes                         | Yes                      | No     | Instance pipeline step results from the orchestrator |

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
      `METRICS_COLLECTOR_TRACE_ID` from the job environment and sends its own `running` events. The
      pipeline-level `start` and `stop` events still use one shared `traceid` for the GitLab pipeline
      run.

3. **Build event payload**

   1. EnvGene sets `data.envgeneVersion` to the EnvGene build version.

   2. EnvGene sets `data.inputParameters` from selected pipeline environment variables. At minimum,
      `PIPELINE_TYPE` is included when set.

   3. EnvGene sets the remaining event fields from [Event fields](#event-fields).

4. **Send `start` event (`before_script`)**

   1. When the first job starts, GitLab runs `before_script` first. The `before_script` sends
      `type: start` with `status: IN_PROGRESS`.

   2. EnvGene sets `jobid` from `CI_JOB_ID` and `technicalname` from `CI_JOB_NAME`.

   3. EnvGene sets event field `time` to the current UTC timestamp.

   4. EnvGene POSTs the event to `/api/v1/activity`.

   5. The `start` event does not include `data.steps`.

5. **Send `running` event while a job runs**

   1. After `before_script`, the job script runs. The orchestrator sends `type: running` with
      `status: IN_PROGRESS` while the job is in progress and before it finishes.

   2. EnvGene sets `jobid` from `CI_JOB_ID`.

   3. EnvGene may include `data.steps` when step results are already available at the time of the
      call.

   4. EnvGene sets event field `time` to the current UTC timestamp and reuses the same `traceid` and
      `parentid` as the matching `start` event.

   5. EnvGene POSTs the event to `/api/v1/activity`.

   6. When the pipeline runs the `sync` job after `env_prepare`, EnvGene also sends `type: running`
      with `status: IN_PROGRESS` for the `sync` job.

6. **Send `running` event when a job finishes**

   1. The orchestrator sends `type: running` when the job finishes, including on step failure.

   2. EnvGene sets `status` from the job outcome, for example `SUCCESS` or `FAILED`.

   3. EnvGene sets `jobid` from `CI_JOB_ID`.

   4. For the `env_prepare` job, EnvGene sets `data.steps` from the orchestrator step results. The
      Instance pipeline records one result per registered step in fixed run order: `get_passport`,
      `credential_rotation`, `change_bg_state`, `warmup`, `env_inventory_generation`,
      `set_template_version`, `appregdef_render`, `deploy_postfix_namespace_map`, `process_sd`,
      `migrate_sd_to_deploy_plan`, `process_deployment_plan`, `env_build`, `generate_effective_set`,
      `git_commit`. For each step, the Instance pipeline records `name`, `status` (`SUCCESS`,
      `FAILED`, or `SKIPPED`), and `durationMs` when the step ran.

   5. EnvGene sets event field `time` to the current UTC timestamp and reuses the same `traceid` and
      `parentid` as the matching `start` event.

   6. EnvGene POSTs the event to `/api/v1/activity`.

7. **Send `stop` event (`after_script`)**

   1. After the last job script finishes, GitLab runs `after_script`. The `after_script` sends
      `type: stop` when the GitLab pipeline finishes.

   2. EnvGene sets terminal `status` to `SUCCESS`, `FAILED`, `CANCELLED`, `SKIPPED`, or `UNKNOWN`.

   3. EnvGene sets event field `time` to the current UTC timestamp and reuses the same `traceid` and
      `parentid` as the matching `start` event.

   4. EnvGene POSTs the event to `/api/v1/activity`.

## Result

1. Metrics Collector Service receives one `start` event from `before_script` when
   `METRICS_COLLECTOR_URL` is set.

2. Metrics Collector Service receives `running` events during job activity for each job that runs,
   including `env_prepare` and `sync` when present. The finished-job `running` event for
   `env_prepare` includes `data.steps` and the job outcome in `status`.

3. Metrics Collector Service receives one `stop` event from `after_script` when the pipeline
   finishes.

## Error handling

**1a.** The Instance pipeline skips Metrics Collector activity when CI/CD variable
`METRICS_COLLECTOR_URL` is empty or absent. The Instance pipeline run continues.

**7a.** EnvGene logs the failure and continues the Instance pipeline run when Metrics Collector
Service returns an error or is unavailable. EnvGene does not retry the POST.

**7b.** EnvGene logs the failure and continues the Instance pipeline run when the serialized event
body exceeds 1 MiB.

## Examples

### Pipeline with one job `env_prepare`

Sequence:

1. `before_script` → `type: start`
2. orchestrator → `type: running` (job in progress)
3. orchestrator → `type: running` (job finished, with `data.steps` and job outcome in `status`)
4. `after_script` → `type: stop`

`start` event (`before_script`):

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
  "technicalname": "env_prepare",
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

`running` event while `env_prepare` runs:

```json
{
  "specversion": "1.0",
  "id": "123e4567-e89b-12d3-a456-426614174010",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "running",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "env_prepare",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:00:05Z",
  "data": {
    "envgeneVersion": "1.2.3",
    "inputParameters": {
      "PIPELINE_TYPE": "GITLAB_DEPLOY"
    }
  }
}
```

`running` event when `env_prepare` finishes:

```json
{
  "specversion": "1.0",
  "id": "123e4567-e89b-12d3-a456-426614174011",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "running",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "env_prepare",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:25:00Z",
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

`stop` event (`after_script`):

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

### Pipeline with jobs `env_prepare` and `sync`

Sequence:

1. `before_script` → `type: start`
2. orchestrator → `type: running` (`env_prepare` in progress)
3. orchestrator → `type: running` (`env_prepare` finished, with `data.steps` and job outcome in `status`)
4. orchestrator → `type: running` (`sync` in progress)
5. orchestrator → `type: running` (`sync` finished)
6. `after_script` → `type: stop`

`start` event (`before_script`):

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
  "technicalname": "env_prepare",
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

`running` event while `env_prepare` runs:

```json
{
  "specversion": "1.0",
  "id": "123e4567-e89b-12d3-a456-426614174010",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "running",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "env_prepare",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:00:05Z",
  "data": {
    "envgeneVersion": "1.2.3",
    "inputParameters": {
      "PIPELINE_TYPE": "GITLAB_DEPLOY"
    }
  }
}
```

`running` event when `env_prepare` finishes:

```json
{
  "specversion": "1.0",
  "id": "123e4567-e89b-12d3-a456-426614174011",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "running",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "env_prepare",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:25:00Z",
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

`running` event while `sync` runs:

```json
{
  "specversion": "1.0",
  "id": "123e4567-e89b-12d3-a456-426614174012",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "running",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550002",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "sync",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:30:00Z",
  "data": {
    "envgeneVersion": "1.2.3",
    "inputParameters": {
      "PIPELINE_TYPE": "GITLAB_DEPLOY"
    }
  }
}
```

`running` event when `sync` finishes:

```json
{
  "specversion": "1.0",
  "id": "123e4567-e89b-12d3-a456-426614174013",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "running",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550002",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "sync",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:34:00Z",
  "data": {
    "envgeneVersion": "1.2.3",
    "inputParameters": {
      "PIPELINE_TYPE": "GITLAB_DEPLOY"
    }
  }
}
```

`stop` event (`after_script`):

```json
{
  "specversion": "1.0",
  "id": "223e4567-e89b-12d3-a456-426614174001",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "stop",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550002",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "instance_pipeline",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:35:00Z",
  "data": {
    "envgeneVersion": "1.2.3",
    "inputParameters": {
      "PIPELINE_TYPE": "GITLAB_DEPLOY"
    }
  }
}
```

## Related documentation

- [Metrics Collector events](/docs/features/metrics-collector-events.md)
- [Instance pipeline flow](/docs/technical-design/instance-pipeline/flow.md)
