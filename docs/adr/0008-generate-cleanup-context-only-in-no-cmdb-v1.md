# ADR-0008: Generate the cleanup context only in No-CMDB v1

Status: Proposed

## Context

The cleanup context is the per-namespace data that pipeline-driven cleanup reads to undeploy a
namespace. In No-CMDB v1 it is not produced during deploy, so that cleanup has nothing to read, and
because generation was scoped to the namespaces named by the solution descriptor, a namespace with no
deployed applications was absent from the cleanup mapping and environment decommission failed. In
No-CMDB v2 the cleanup context is still produced, yet the cleaner there resolves everything from the
topology and never reads it.

## Decision

The cleanup context is generated for every namespace of the environment in No-CMDB v1, and is not
generated in No-CMDB v2.

- No-CMDB v1 generates the cleanup context for every namespace of the environment, including a namespace
  with no deployed applications and a run with no solution descriptor.
- No-CMDB v2 generates no cleanup context, at deploy or at clean. Its clean operation marks the target
  namespaces' deployment and runtime for removal without a cleanup context.
- Removing an application from the solution does not drop a namespace's cleanup context, because the
  namespace still exists.
- The cleanup context composition is unchanged. It stays the tenant, cloud, and namespace parameters.
- The behavior follows the deployment architecture, which the pipeline already knows. No new user-facing
  parameter is introduced.

Rejected:

- Restore the solution-descriptor-scoped generation, because it omits namespaces with no deployed applications.
- Introduce a new user-facing parameter, because the deployment architecture already separates the flows.
- Generate the cleanup context in No-CMDB v2 as well, because it ships credential-bearing output that the
  No-CMDB v2 cleaner never reads.

## Consequences

- No-CMDB v1 cleanup and environment decommission work again, covering namespaces with no deployed applications.
- No-CMDB v2 ships no cleanup context, so its cleaner relies on the topology alone.
- The two architectures diverge on cleanup output, one more behavior difference to track.
- A pipeline-driven cleanup consumer paired with No-CMDB v2 finds no cleanup context, so that pairing is unsupported.
- Stale cleanup context from an earlier version is not removed by this decision. The cleaner side owns that
  housekeeping.
