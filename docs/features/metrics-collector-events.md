# Metrics Collector events

- [Metrics Collector events](#metrics-collector-events)
  - [Overview](#overview)
  - [Problem statement](#problem-statement)
  - [How it works](#how-it-works)
  - [Related documentation](#related-documentation)

## Overview

EnvGene reports pipeline activity to Metrics Collector Service. Each run emits a `start` event at
the beginning and a `stop` event at the end, so downstream observability can track deployment
sessions across orchestrated pipelines.

## Problem statement

Pipeline status is available in GitLab, but it is not enough for end-to-end deployment tracking
across several tools and pipelines.

Teams need a common format to collect deployment activity, understand when a deployment started and
finished, check the final result, and connect related pipeline executions.

Metrics Collector Service provides this common tracking layer by collecting pipeline events in
CloudEvents format.

## How it works

The first executed job sends `type: start` with `status: IN_PROGRESS`. The last executed job sends
`type: stop` with a terminal status (`SUCCESS`, `FAILED`, and others).

Events use `kind: pipeline` and share one `traceid` per run. EnvGene generates a new UUID v4 for
each event `id` before POST. A successful request returns `202 Accepted`. When Metrics Collector
Service is unavailable, EnvGene logs the error and continues without retries.

For field-level API contract, request examples, and `data` structure, see
[Metrics Collector events API](/docs/dev/metrics-collector-integration.md).

## Related documentation

- [Metrics Collector events API](/docs/dev/metrics-collector-integration.md) - event fields, `data`
  structure, and JSON examples
