# ADR-0007: Decompose custom params into the per-service deployment structure

Status: Proposed

## Context

The `CUSTOM_PARAMS` pipeline parameter carries deployment overrides. Today it sits flat at the root of the
deployment context, while `deployment-parameters.yaml` is already decomposed into a root layer, a `global`
layer, and a per-service layer derived from the application's SBOM. A flat custom override therefore does
not reach inside a service, so it cannot target one service's deployment parameters the way the rest of the
deployment context can.

## Decision

We decompose `custom_params` in the deployment context into the same root plus `global` plus per-service
structure that `deployment-parameters.yaml` uses, generated from the application's SBOM, so a custom
override applies inside each service instead of only at the root.

- The decomposition is scoped to the deployment context only. The runtime and cleanup contexts keep their
  current flat custom params.
- Custom params override deployment and runtime parameters. They do not override image or artifact
  metadata. `docker_tag`, `docker_registry`, and `image` come from the read-only SBOM-derived
  deployDescriptor.

Rejected:

- Author-controlled structured targeting written into the deployDescriptor, because the deployDescriptor is
  read-only SBOM-derived provenance and must not become an override surface.
- Generating a deployDescriptor block from custom_params, because that would let overrides rewrite image and
  artifact metadata, which stays SBOM-owned.

## Consequences

- A custom override can target one service's deployment parameters, matching how the rest of the deployment
  context is already decomposed.
- Runtime and cleanup stay flat, so the decomposition is inconsistent across contexts and a reader must know
  that only the deployment context is per-service.
- The structure is bounded to the SBOM's services, so a custom override for a name absent from the SBOM has
  no per-service slot to land in.
- Custom params cannot override image or artifact metadata, so an override that needs a different tag,
  registry, or image has no path through this mechanism.

See ticket JCPR-3049 for the tracked implementation.
