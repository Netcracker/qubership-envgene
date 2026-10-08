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

EnvGene reports pipeline activity for an Instance pipeline run:

1. `type: start` when the run begins.
2. `type: running` while a job is in progress and when that job finishes.
3. `type: stop` when the run finishes.

## Input parameters

| Parameter                      | Source | Required | Default   | Values / format   | Effect                                     |
|--------------------------------|--------|----------|-----------|-------------------|--------------------------------------------|
| `METRICS_COLLECTOR_URL`        | CI/CD    | No       | empty     | Base URL          | POST `{url}/api/v1/activity`, or skip      |
| `METRICS_COLLECTOR_TRACE_ID`   | Pipeline | No       | generated | 32 hex characters | Event field `traceid`                      |
| `METRICS_COLLECTOR_PARENT_ID`  | Pipeline | No       | omitted   | Parent event `id` | Sets `parentid`, or omits the field        |
| `METRICS_COLLECTOR_SSL_VERIFY` | CI/CD    | No       | `true`    | `true` or `false` | `false` skips TLS certificate verification |

## Request body mapping

### Event fields

| Field           | Required | Source                                               | Example                                                   |
|-----------------|----------|------------------------------------------------------|-----------------------------------------------------------|
| `specversion`   | Yes      | `"1.0"`                                              | `"1.0"`                                                   |
| `id`            | Yes      | EnvGene (UUID v4)                                    | `"123e4567-e89b-12d3-a456-426614174000"`                  |
| `source`        | Yes      | `CI_PROJECT_URL`                                     | `"https://gitlab.example.com/platform/env-instance-repo"` |
| `type`          | Yes      | `"start"`, `"running"`, or `"stop"`                  | `"start"`                                                 |
| `subject`       | Yes      | `CI_JOB_ID` of the job that sends the event          | `"5550001"`                                               |
| `kind`          | Yes      | `"pipeline"`                                         | `"pipeline"`                                              |
| `kindversion`   | Yes      | `"1.0"`                                              | `"1.0"`                                                   |
| `traceid`       | Yes      | `METRICS_COLLECTOR_TRACE_ID`, or generated           | `"4bf92f3577b34da6a3ce929d0e0e4736"`                      |
| `parentid`      | No       | `METRICS_COLLECTOR_PARENT_ID` when set. Omit when empty | `"d72800f6-29c7-42b5-a9ab-519f026bcad5"`               |
| `technicalname`    | Yes      | `<DD name>:<CI_JOB_NAME>`: instance repository Deployment Descriptor name without the version, `:`, and the name of the job that sends the event | `"envgene-instance-pipeline:env_prepare"`                 |
| `technicalversion` | Yes      | Instance repository Deployment Descriptor version                   | `"v3.9.1-cloud_dd-20261007.065010-1-RELEASE"`            |
| `displayname`      | No       | Constant `EnvGene Instance Pipeline`                 | `"EnvGene Instance Pipeline"`                             |
| `datacontenttype`  | Yes      | `"application/json"`                                 | `"application/json"`                                      |
| `jobid`         | Yes      | `CI_JOB_ID`                                          | `"5550001"`                                               |
| `pipelineid`    | Yes      | `CI_PIPELINE_ID`                                     | `"987654"`                                                |
| `projectid`     | Yes      | `CI_PROJECT_ID`                                      | `"12345"`                                                 |
| `status`        | No       | `IN_PROGRESS`, `SUCCESS`, `FAILED`, or other         | `"SUCCESS"`                                               |
| `time`          | Yes      | Current UTC time                                     | `"2026-06-12T14:00:00Z"`                                  |
| `data`          | Yes      | See [`data` fields](#data-fields)                    | *(object)*                                                |

Terminal `status` values: `SUCCESS`, `FAILED`, `CANCELLED`, `SKIPPED`, `UNKNOWN`.

### `data` fields

| Field             | Required | `start` | `running` (in progress) | `running` (finished) | `stop`      | Source          |
|-------------------|----------|---------|-------------------------|----------------------|-------------|-----------------|
| `inputParameters` | Yes      | Yes     | Yes                     | Yes                  | Yes         | Pipeline inputs |
| `steps`           | No       | No      | When recorded           | Yes                  | Current job | Step results    |

### `data.steps` item fields

| Field         | Required | Source                                               |
|---------------|----------|------------------------------------------------------|
| `name`        | Yes      | Step name                                            |
| `status`      | Yes      | `SUCCESS`, `FAILED`, or `SKIPPED`                    |
| `durationMs`  | No       | Milliseconds. Omitted when the step was skipped      |
| `environment` | No       | Recorded `ENV_NAMES`, when environments are combined |

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
      pipeline passes a non-empty value. Otherwise EnvGene omits `parentid`.

   4. When `ENV_NAMES` lists multiple environments, each child process inherits
      `METRICS_COLLECTOR_TRACE_ID` and sends its own `running` events. Child processes do not send
      `start` or `stop`. The run sends one `start` event and one `stop` event, and those events use
      the same `traceid`. The `stop` event reads the child completion files. It uses `inputParameters`
      from the first file in name order, then sets `ENV_NAMES` to the recorded environment names
      joined by commas. When more than one completion belongs to the current `CI_JOB_ID`, each
      `steps` item includes `environment`.

3. **Build event payload**

   1. EnvGene sets `data.inputParameters` from non-empty pipeline parameters. It omits
      `CRED_ROTATION_PAYLOAD` and `ENV_INVENTORY_CONTENT`. The `start`, `running`, and `stop` hook
      commands, before they apply a recorded completion, include only `PIPELINE_TYPE` and `ENV_NAMES`
      when those variables are set.

   2. EnvGene sets the remaining event fields from [Event fields](#event-fields).

4. **Send `start` event**

   1. EnvGene sends `type: start` with `status: IN_PROGRESS` when the run begins.

   2. EnvGene sets `jobid` from `CI_JOB_ID` and `technicalname` to `<DD name>:<CI_JOB_NAME>`.

   3. EnvGene sets event field `time` to the current UTC timestamp.

   4. EnvGene POSTs the event to `/api/v1/activity`.

   5. The `start` event does not include `data.steps`.

5. **Send `running` event while a job runs**

   1. The orchestrator sends `type: running` with `status: IN_PROGRESS` when the job script starts,
      before any step result exists. That event omits `data.steps`.

   2. EnvGene sets `jobid` from `CI_JOB_ID`.

   3. A later `running` event includes `data.steps` when completion records for the current
      `CI_JOB_ID` already exist. Its `status` stays `IN_PROGRESS` unless an explicit status is passed.

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
      `set_template_version`, `appregdef_render`, `regdefv2_adapter`,
      `deploy_postfix_namespace_map`, `process_sd`, `migrate_sd_to_deploy_plan`,
      `process_deployment_plan`, `env_build`, `generate_effective_set`, `git_commit`, `CMDB_import`.
      It then records `copy_env_artifact`. For each step, the Instance pipeline records `name`,
      `status` (`SUCCESS`, `FAILED`, or `SKIPPED`), and `durationMs` when the step ran.

   5. EnvGene sets event field `time` to the current UTC timestamp and reuses the same `traceid` and
      `parentid` as the matching `start` event.

   6. EnvGene POSTs the event to `/api/v1/activity`.

7. **Send `stop` event**

   1. EnvGene sends `type: stop` when the run finishes.

   2. EnvGene sets terminal `status` from `CI_JOB_STATUS` when no completion was recorded:
      `success` to `SUCCESS`, `failed` to `FAILED`, `canceled` to `CANCELLED`, `skipped` to
      `SKIPPED`, and any other value to `UNKNOWN`. When completion records exist and `--status` is
      not passed, EnvGene chooses `FAILED` if any recorded status or the job status is `FAILED`,
      otherwise `CANCELLED` on the same rule, otherwise `UNKNOWN` if any recorded status is
      `UNKNOWN`, otherwise `SKIPPED` if every recorded status is `SKIPPED`, otherwise `SUCCESS`.
      An explicit `--status` keeps that value. After a successful `stop`, another `stop` for the
      same `CI_JOB_ID` is not sent.

   3. EnvGene sets event field `time` to the current UTC timestamp and reuses the same `traceid` and
      `parentid` as the matching `start` event.

   4. EnvGene POSTs the event to `/api/v1/activity`.

## Result

1. Metrics Collector Service receives one `start` event when the run begins and
   `METRICS_COLLECTOR_URL` is set.

2. Metrics Collector Service receives `running` events during job activity for each job that runs,
   including `env_prepare` and `sync` when present. The finished-job `running` event for
   `env_prepare` includes `data.steps` and the job outcome in `status`.

3. Metrics Collector Service receives one `stop` event when the run finishes.

## Error handling

**1a.** The Instance pipeline skips Metrics Collector activity when CI/CD variable
`METRICS_COLLECTOR_URL` is empty or absent. The Instance pipeline run continues.

**7a.** EnvGene logs the failure and continues the Instance pipeline run when Metrics Collector
Service returns an error or is unavailable. EnvGene does not retry the POST.

**7b.** EnvGene logs the failure and continues the Instance pipeline run when the serialized event
body exceeds 1 MiB.

## Examples

JSON examples shorten `data.steps` and `inputParameters`. A real event lists every registered step, then
`copy_env_artifact`. An orchestrator event, and any later event that reads a recorded completion, puts
every non-empty pipeline parameter into `inputParameters` except `CRED_ROTATION_PAYLOAD` and
`ENV_INVENTORY_CONTENT`. The examples below keep only `PIPELINE_TYPE`.

### Pipeline with one job `env_prepare`

Sequence:

1. `type: start`
2. orchestrator → `type: running` (job in progress)
3. orchestrator → `type: running` (job finished, with `data.steps` and job outcome in `status`)
4. `type: stop`

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
  "subject": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:env_prepare",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:00:00Z",
  "data": {
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
  "subject": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:env_prepare",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:00:05Z",
  "data": {
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
  "subject": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:env_prepare",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:25:00Z",
  "data": {
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
  "subject": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:env_prepare",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:30:00Z",
  "data": {
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

1. `type: start`
2. orchestrator → `type: running` (`env_prepare` in progress)
3. orchestrator → `type: running` (`env_prepare` finished, with `data.steps` and job outcome in `status`)
4. `type: running` (`sync` in progress, no `data.steps`)
5. `type: stop`

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
  "subject": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:env_prepare",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:00:00Z",
  "data": {
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
  "subject": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:env_prepare",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:00:05Z",
  "data": {
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
  "subject": "5550001",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:env_prepare",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:25:00Z",
  "data": {
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
  "subject": "5550002",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "IN_PROGRESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:sync",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:30:00Z",
  "data": {
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
  "jobid": "5550002",
  "subject": "5550002",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "envgene-instance-pipeline:sync",
  "technicalversion": "v3.9.1-cloud_dd-20261007.065010-1-RELEASE",
  "displayname": "EnvGene Instance Pipeline",
  "datacontenttype": "application/json",
  "time": "2026-06-12T14:35:00Z",
  "data": {
    "inputParameters": {
      "PIPELINE_TYPE": "GITLAB_DEPLOY"
    }
  }
}
```

## Related documentation

- [Metrics Collector events](/docs/features/metrics-collector-events.md)
- [Instance pipeline flow](/docs/technical-design/instance-pipeline/flow.md)
- [EnvGene repository variables](/docs/envgene-repository-variables.md#metrics_collector_url)
- [Instance pipeline parameters](/docs/instance-pipeline-parameters.md#metrics_collector_trace_id)
