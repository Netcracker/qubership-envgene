# Metrics Collector events

- [Metrics Collector events](#metrics-collector-events)
  - [Overview](#overview)
  - [Problem statement](#problem-statement)
  - [How it works](#how-it-works)
    - [Event model](#event-model)
    - [Correlation across pipelines](#correlation-across-pipelines)
    - [Multiple environments in one job](#multiple-environments-in-one-job)
    - [Optional integration](#optional-integration)
  - [Related documentation](#related-documentation)

## Overview

EnvGene reports Instance pipeline activity to Metrics Collector Service. Each run emits one `start`
event when the Instance pipeline begins and one `stop` event when the run finishes.

The events use CloudEvents 1.0 and `kind: pipeline`. They let platform observability track deployment
activity across orchestrated pipelines, not only inside a single GitLab job.

## Problem statement

Pipeline status is available in GitLab, but it is not enough for end-to-end deployment tracking
across several tools and pipelines.

A deployment often spans a parent orchestrator, EnvGene, and other downstream jobs. GitLab shows each
job in isolation. Teams need a shared format to record when a deployment started and finished, what
the final result was, and how related pipeline runs connect to each other.

Metrics Collector Service provides this common tracking layer. EnvGene contributes pipeline activity
events in the same format as other platform components.

## How it works

EnvGene sends CloudEvents 1.0 HTTP events to Metrics Collector Service at `POST /api/v1/activity`.

### Event model

At the beginning of an Instance pipeline run, EnvGene sends `type: start` with `status: IN_PROGRESS`.
When the run finishes, EnvGene sends `type: stop` with a terminal status such as `SUCCESS` or `FAILED`.

The `stop` event carries run details in `data`: the EnvGene build version (`envgeneVersion`), selected
pipeline input parameters (`inputParameters`), and a summary of Instance pipeline step results
(`steps`).

EnvGene generates a new UUID v4 for each event `id`. Metrics Collector Service uses the `time`
difference between the matching `start` and `stop` events to calculate pipeline duration.

When Metrics Collector Service is unavailable or returns an error, EnvGene logs the failure and
continues the Instance pipeline run. EnvGene does not retry failed POSTs.

### Correlation across pipelines

EnvGene participates in a larger orchestration chain. A parent pipeline, such as an orchestration
broker job, can pass environment variables to EnvGene:

- `METRICS_COLLECTOR_TRACE_ID` - links EnvGene activity to the parent deployment session
- `METRICS_COLLECTOR_PARENT_ID` - references the parent pipeline activity event `id`

When the parent does not pass `METRICS_COLLECTOR_TRACE_ID`, EnvGene generates a new `traceid` for
the run. All events in the same run share one `traceid`.

### Multiple environments in one job

When pipeline parameter `ENV_NAMES` lists more than one environment, EnvGene fans out to one Instance
pipeline run per environment. Each child run inherits `METRICS_COLLECTOR_TRACE_ID` from the job
environment and sends its own `start` and `stop` events.

For N environments, Metrics Collector Service receives 2 × N events: one `start` and one `stop` per
environment, all sharing the same `traceid` when the parent passed it.

### Optional integration

EnvGene sends activity events only when CI/CD variable `METRICS_COLLECTOR_URL` is set. When the
variable is empty or absent, EnvGene skips all Metrics Collector POSTs and the Instance pipeline run
continues normally.

This is the expected state for on-prem deployments where Metrics Collector Service is not deployed.
No extra configuration is required to disable the integration.

For orchestration flow, field-level mapping, and JSON examples, see
[Metrics Collector activity](/docs/technical-design/metrics-collector-activity.md).

## Related documentation

- [Metrics Collector activity](/docs/technical-design/metrics-collector-activity.md) - orchestration
  flow, event field mapping, `data` structure, and request examples
- [Instance pipeline flow](/docs/technical-design/instance-pipeline/flow.md) - Instance pipeline
  steps reported in `data.steps`
