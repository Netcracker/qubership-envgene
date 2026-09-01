# ADR-0005: Decompose custom_params deployment overrides into global and per-service

Status: Proposed
Date: 2026-08-31

## Context

`custom_params` (the `CUSTOM_PARAMS` pipeline parameter) is the highest-priority, session-scoped override, applied
last in the deployer's values merge. Its deployment overrides are written flat into `custom-params.yaml`, so an
override sits only at the root level. A deployment parameter, by contrast, is laid out at the root, under the `global`
block, and under each per-service key generated from the application's SBOM, so it is reachable inside each service. A
flat custom override is absent from `global` and from the per-service keys, so it does not apply where a deployment
parameter applies, which defeats the purpose of an incident-override tool.

## Decision

We decompose `custom_params` deployment overrides into the same root, `global`, and per-service structure that
`deployment-parameters.yaml` uses, generated from the application's SBOM, written to `custom-params.yaml`, reusing the
existing decomposition. The override then keeps its highest priority and applies wherever a deployment parameter
applies. The scope is the deployment context only. The runtime and cleanup contexts are flat, so they are unchanged.
`custom_params` overrides deployment and runtime parameters, not image or artifact metadata. `docker_tag`,
`docker_registry` and `image` live in the read-only, SBOM-derived `deployDescriptor` block and stay non-overridable
through `custom_params`.

Rejected:

- Author-controlled structured targeting, where the author writes the full path into `deployDescriptor`, because no
  confirmed case needs overriding image metadata and it leaks the internal Effective Set structure to authors.
- Generating a `deployDescriptor` block from `custom_params`, because `deployDescriptor` is read-only provenance
  derived from the SBOM and user input has no mapping to it.
- Extending the change to the runtime or cleanup context, because runtime is flat (Config Server injection) and
  cleanup receives no Custom Params. The pipeline context is not a Custom Params target.

## Consequences

- A `custom_params` deployment override is present at the root, in `global`, and per-service, matching a deployment
  parameter, and wins the merge, closing the silent no-op.
- An override now applies at every per-service scope instead of at the root alone. This parity with deployment
  parameters is intended, and the accepted cost is the wider scope compared with the former flat behavior.
- A custom key equal to a service name reuses the existing collision handling. A custom key equal to `global`,
  `deployDescriptor`, or a service name, carrying a scalar value, replaces a structural map and breaks the deploy. A
  map value deep-merges safely. This is documented, not guarded.
- The schema and `calculator-cli.md` currently imply `custom_params` applies to the cleanup context. This is
  inaccurate against the behavior and is corrected to state deployment and runtime only.
- This is a decision ahead of implementation. The decomposition is not yet wired, so `custom_params` keeps its flat
  behavior until that lands.

See [`CUSTOM_PARAMS`](/docs/instance-pipeline-parameters.md#custom_params) and the Effective Set deployment context
in [Calculator CLI](/docs/features/calculator-cli.md).
