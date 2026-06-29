# Metrics Collector events

- [Metrics Collector events](#metrics-collector-events)
  - [Overview](#overview)
  - [Problem statement](#problem-statement)
  - [How it works](#how-it-works)
  - [Processing order](#processing-order)
  - [Configuration](#configuration)
  - [Event attributes](#event-attributes)
    - [Activity status](#activity-status)
    - [`start` event](#start-event)
    - [`stop` event](#stop-event)
  - [Error handling](#error-handling)

## Overview

EnvGene sends activity events to Metrics Collector Service for observability. A failed API call
does not fail the CI job.

## Problem statement

EnvGene must send activity events to Metrics Collector Service when a run starts and when it
ends. GitLab alone does not provide that signal in the format Metrics Collector Service expects.

## How it works

EnvGene sends events with `kind: pipeline` and a shared `traceid`. The first executed job sends
`type: start`; the last executed job sends `type: stop`.

If the HTTP call fails, EnvGene logs the failure and the CI job continues. A successful request
returns `202 Accepted`.

## Processing order

1. Resolve `traceid` from the parent pipeline when present; otherwise generate a value for this run.
2. When triggered by a parent pipeline, set `parentid` to the `id` of the parent activity event
   previously submitted to Metrics Collector Service.
3. **First executed job** sends `type: start` with `status: IN_PROGRESS`.
4. **Last executed job** sends `type: stop` with a terminal status.
5. On API error, log and continue. No retry.
6. On GitLab job retry, do not send duplicate events.

## Configuration

| Attribute               | Type   | Default | Description |
|-------------------------|--------|---------|-------------|
| `METRICS_COLLECTOR_URL` | string | —       | Base URL of Metrics Collector Service. Events POST to `{METRICS_COLLECTOR_URL}/api/v1/activity`. |

## Event attributes

The tables below list event fields. Each subsection includes a JSON example of a request body sent
to Metrics Collector Service at `POST /api/v1/activity`.

### Activity status

If `status` is absent or empty, Metrics Collector Service treats it as `UNKNOWN`. EnvGene always
sends an explicit value.

Allowed values: `NOT_STARTED`, `SKIPPED`, `IN_PROGRESS`, `SUCCESS`, `FAILED`, `CANCELLED`, `UNKNOWN`.

| Status        | When EnvGene sends it |
|---------------|-----------------------|
| `IN_PROGRESS` | `start` event at the beginning of the run |
| `SUCCESS`     | `stop` when the run completes successfully |
| `FAILED`      | `stop` when a job fails |
| `CANCELLED`   | `stop` when the run is cancelled |
| `SKIPPED`     | `stop` when the pipeline or the terminating job was skipped |
| `UNKNOWN`     | `stop` in cases not covered above |
| `NOT_STARTED` | Never |

### `start` event

| Attribute       | Required | Source            | Example                                  | Description |
|-----------------|----------|-------------------|------------------------------------------|-------------|
| `specversion`   | yes      | `"1.0"`           | `"1.0"`                                  | Event specification version. Must be `1.0`. |
| `id`            | yes      | UUID v4           | `"123e4567-e89b-12d3-a456-426614174000"` | Event UUID. The `source` + `id` pair must be unique. |
| `source`        | yes      | `$CI_PROJECT_URL` | `"https://gitlab.example.com/..."`       | Absolute `https://` URI identifying the activity source. |
| `type`          | yes      | `"start"`         | `"start"`                                | Activity start. |
| `kind`          | yes      | `"pipeline"`      | `"pipeline"`                             | GitLab CI pipeline activity. |
| `kindversion`   | yes      | `"1.0"`           | `"1.0"`                                  | Must be `1.0`. |
| `traceid`       | yes      | Parent or local   | `"4bf92f3577b34da6a3ce929d0e0e4736"`     | Correlation identifier from the parent pipeline or generated for this run. |
| `parentid`      | no       | Parent event      | `"d72800f6-29c7-42b5-a9ab-519f026bcad5"` | Parent activity event `id` when triggered by a parent pipeline. |
| `technicalname` | yes      | `$CI_JOB_NAME`    | `"env_inventory_generation"`             | Machine-readable entity name (non-empty string). |
| `displayname`   | no       | Pipeline context  | *(set at runtime)*                       | Human-readable name derived from the pipeline context. Not a fixed string. |
| `jobid`         | yes      | `$CI_JOB_ID`      | `"5550001"`                              | Job identifier. |
| `pipelineid`    | yes      | `$CI_PIPELINE_ID` | `"987654"`                               | Pipeline identifier. |
| `projectid`     | yes      | `$CI_PROJECT_ID`  | `"12345"`                                | Project identifier. |
| `status`        | no       | —                 | `"IN_PROGRESS"`                          | Always `IN_PROGRESS`. |
| `time`          | yes      | Current UTC time  | `"2026-06-12T14:00:00Z"`                 | RFC 3339 activity timestamp. |

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
  "technicalname": "env_inventory_generation",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:00:00Z"
}
```

### `stop` event

| Attribute       | Required | Source            | Example                                  | Description |
|-----------------|----------|-------------------|------------------------------------------|-------------|
| `specversion`   | yes      | `"1.0"`           | `"1.0"`                                  | Event specification version. Must be `1.0`. |
| `id`            | yes      | UUID v4           | `"223e4567-e89b-12d3-a456-426614174001"` | Event UUID. The `source` + `id` pair must be unique. |
| `source`        | yes      | `$CI_PROJECT_URL` | `"https://gitlab.example.com/..."`       | Absolute `https://` URI identifying the activity source. |
| `type`          | yes      | `"stop"`          | `"stop"`                                 | Activity end. |
| `kind`          | yes      | `"pipeline"`      | `"pipeline"`                             | GitLab CI pipeline activity. |
| `kindversion`   | yes      | `"1.0"`           | `"1.0"`                                  | Must be `1.0`. |
| `traceid`       | yes      | Parent or local   | `"4bf92f3577b34da6a3ce929d0e0e4736"`     | Same value as the matching `start` event. |
| `parentid`      | no       | Parent event      | `"d72800f6-29c7-42b5-a9ab-519f026bcad5"` | Same `parentid` as the matching `start` event. |
| `technicalname` | yes      | `$CI_JOB_NAME`    | `"cmdb_import"`                          | Machine-readable entity name (non-empty string). |
| `displayname`   | no       | Pipeline context  | *(set at runtime)*                       | Human-readable name derived from the pipeline context. Not a fixed string. |
| `jobid`         | yes      | `$CI_JOB_ID`      | `"5550099"`                              | Job identifier. |
| `pipelineid`    | yes      | `$CI_PIPELINE_ID` | `"987654"`                               | Pipeline identifier. |
| `projectid`     | yes      | `$CI_PROJECT_ID`  | `"12345"`                                | Project identifier. |
| `status`        | no       | `$CI_JOB_STATUS`  | `"SUCCESS"`                              | Terminal status. See [Activity status](#activity-status). |
| `time`          | yes      | Current UTC time  | `"2026-06-12T14:30:00Z"`                 | RFC 3339 activity timestamp. |

```json
{
  "specversion": "1.0",
  "id": "223e4567-e89b-12d3-a456-426614174001",
  "source": "https://gitlab.example.com/platform/env-instance-repo",
  "type": "stop",
  "kind": "pipeline",
  "kindversion": "1.0",
  "jobid": "5550099",
  "pipelineid": "987654",
  "projectid": "12345",
  "status": "SUCCESS",
  "parentid": "d72800f6-29c7-42b5-a9ab-519f026bcad5",
  "traceid": "4bf92f3577b34da6a3ce929d0e0e4736",
  "technicalname": "cmdb_import",
  "displayname": "EnvGene Instance Pipeline",
  "time": "2026-06-12T14:30:00Z"
}
```

## Error handling

Send failures do not fail the CI job. EnvGene does not retry failed requests.

| Situation                          | Behaviour          |
|------------------------------------|--------------------|
| Service unavailable                | Log; job continues |
| **400**, **405**, **415**, **500** | Log error; job continues |
