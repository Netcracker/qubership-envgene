# Metrics Collector events

- [Metrics Collector events](#metrics-collector-events)
  - [Problem statement](#problem-statement)
  - [Approach](#approach)
    - [Event model](#event-model)
    - [Correlation across pipelines](#correlation-across-pipelines)
    - [Multiple environments](#multiple-environments)
    - [Optional integration](#optional-integration)
  - [Related documentation](#related-documentation)

EnvGene reports Instance pipeline activity to Metrics Collector Service so a deployment can be tracked
across tools, not only inside one GitLab job. Field-level mapping and request examples are in
[Metrics Collector activity](/docs/technical-design/metrics-collector-activity.md).

## Problem statement

Pipeline status in GitLab shows each job on its own. A deployment usually spans a parent orchestrator,
EnvGene, and other downstream jobs, so that per-job view is not enough to see when the deployment
started, how it finished, and which runs belong together.

Metrics Collector Service is the shared record for that view. EnvGene contributes the same kind of
pipeline activity events as other platform components.

## Approach

EnvGene sends CloudEvents 1.0 HTTP events to Metrics Collector Service at `POST /api/v1/activity`.
The events use `kind: pipeline`.

### Event model

A run sends three event types:

- `type: start` with `status: IN_PROGRESS` when the run begins.
- `type: running` while a job is in progress, and again when that job finishes. The finished event
   carries the job outcome and the Instance pipeline step results. An in-progress event carries step
   results only when they are already known.
- `type: stop` when the run finishes, with a terminal status such as `SUCCESS` or `FAILED`. It carries
   the EnvGene version, the pipeline inputs, and the step results for that job. It does not repeat
   step results from an earlier job in the same pipeline.

Each event has its own ID. Events in one run share one trace ID, and each event carries the time it
was sent, so a collector can measure the interval from `start` to `stop`.

If Metrics Collector Service is unavailable or rejects the event, EnvGene logs the failure and
continues the Instance pipeline run. EnvGene does not retry the request.

### Correlation across pipelines

A parent pipeline can connect EnvGene to the wider deployment by passing two pipeline parameters:

- `METRICS_COLLECTOR_TRACE_ID` links this run to the parent deployment session.
- `METRICS_COLLECTOR_PARENT_ID` references the parent activity event.

When the parent does not pass a trace ID, EnvGene creates one for the run. Every event in that run
uses it.

### Multiple environments

When `ENV_NAMES` lists more than one environment, each environment reports its own `running` activity.
The run still has one `start` event and one `stop` event. The `stop` event combines the environment
results, and every event in the run shares one trace ID.

### Optional integration

EnvGene sends events only when `METRICS_COLLECTOR_URL` is set. When the variable is empty or absent,
EnvGene sends nothing and the Instance pipeline run continues. That is the expected state where
Metrics Collector Service is not deployed.

TLS certificate checks stay on unless `METRICS_COLLECTOR_SSL_VERIFY` is `false`.

## Related documentation

- [Metrics Collector activity](/docs/technical-design/metrics-collector-activity.md) - event fields,
   `data` structure, and request examples
- [Instance pipeline flow](/docs/technical-design/instance-pipeline/flow.md) - Instance pipeline
   steps reported with the finished job
- [EnvGene repository variables](/docs/envgene-repository-variables.md#metrics_collector_url) -
   `METRICS_COLLECTOR_URL` and `METRICS_COLLECTOR_SSL_VERIFY`, set on the repository
- [Instance pipeline parameters](/docs/instance-pipeline-parameters.md#metrics_collector_trace_id) -
   `METRICS_COLLECTOR_TRACE_ID` and `METRICS_COLLECTOR_PARENT_ID`, passed when the pipeline starts
