# Deployment and operations

> _Placeholder. How to deploy and run the service for an operator. The logical architecture is in
> architecture.md, this doc is the operational detail._

## Deployment

> _Placeholder. Two or more identical stateless replicas with an in-memory cache, across more than one
> cluster for high availability. See the Topology in architecture.md._

## Configuration reference

> _Placeholder. A table of config inputs: git URL, branch, credentials, and the periodic resync interval._

## Bootstrap, health, and startup

> _Placeholder. Initial clone and cache warm, readiness gating, and liveness._

## Observability

> _Placeholder. Metrics (resolve latency, cache size, sync lag, webhook deliveries, write latency) and the
> SLO._

## Failure modes and recovery

> _Placeholder. Git unreachable, a missed webhook, a malformed def, and a pod restart._
