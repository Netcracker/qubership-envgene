# Proposal

## Why

The four `current_env.cluster.*` connection macros (`cloud_api_protocol`, `cloud_api_url`, `cloud_api_port`,
`cloud_public_url`) take their values only from the Environment Inventory's `clusterUrl`. When an environment is
generated with a Cloud Passport and `clusterUrl` is not set, the macros resolve to empty strings, so a template that
builds a host from `cloud_public_url` produces a hostname with no domain, which the deployment target rejects. The
template-macros documentation already states these values come from the Cloud Passport, so template authors rely on a
behavior the generator does not provide. The condition follows from an absent `clusterUrl` with passport-sourced
cluster facts, independent of the environment architecture.

## What Changes

- The four `current_env.cluster.*` connection macros fall back to the Cloud Passport's cluster values (public host,
  API host, API port, protocol) when `clusterUrl` is not set in the Environment Inventory.
- Precedence is fallback, not override: when `clusterUrl` is set it stays the source and the Cloud Passport is not
  consulted. The Cloud Passport fills only the otherwise-empty case. When neither source provides a value the macro
  stays an empty string, as today.
- The template-macros documentation is corrected for the four macros: each description changes from "overwritten from
  Cloud Passport file" to a fallback statement that names the Cloud Passport value used when `clusterUrl` is not set.

## Capabilities

### New Capabilities

- `cluster-connection-macros`: how the four `current_env.cluster.*` connection macros resolve their values from the
  Environment Inventory and, as a fallback, the Cloud Passport.

### Modified Capabilities

<!-- No existing spec under openspec/specs/ governs these macros, so there is no modified capability. -->

## Impact

- Objects: Environment Inventory (`clusterUrl`), Cloud Passport (cluster public host, API host, API port, protocol),
  and the generated environment configuration context (`current_env.cluster`).
- Macros: `current_env.cluster.cloud_api_protocol`, `current_env.cluster.cloud_api_url`,
  `current_env.cluster.cloud_api_port`, `current_env.cluster.cloud_public_url`.
- Pipeline step: environment build, where the environment configuration context is generated.
- Docs: `docs/template-macros.md`.
