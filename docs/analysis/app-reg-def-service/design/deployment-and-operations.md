# Deployment and operations

> _Placeholder. How to deploy and run the service for an operator. The logical architecture is in
> architecture.md, this doc is the operational detail._

## Deploy profiles

> _Placeholder. Lite (one pod, in-process cache) and HA (read-service plus a write/sync singleton plus
> Redis), selected by config._

## Configuration reference

> _Placeholder. A table of config inputs: git URL, branch, credentials, webhook secret, backstop interval,
> cache backend, and the rest._

## Scaling and multi-cluster

> _Placeholder. One instance per cluster over the shared git, leader election for the singleton, and Redis
> HA._

## Bootstrap, health, and startup

> _Placeholder. Initial clone and cache warm, readiness gating, and liveness._

## Observability

> _Placeholder. Metrics (resolve latency, cache size, sync lag, webhook deliveries, write latency) and the
> SLO._

## Failure modes and recovery

> _Placeholder. Git unreachable, a missed webhook, a malformed def, and a pod or singleton restart._
