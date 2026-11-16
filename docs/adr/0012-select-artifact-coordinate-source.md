# ADR-0012: Select the source of truth for application artifact coordinates

Status: Proposed

## Context

One Deployment Descriptor carries a single baked-in registry, but the same descriptor deploys to several
environments whose registries differ, each described by its own Registry Definition. The embedded registry
is correct for at most one environment, so for the others the Helm chart URL and the container image URL must
be reconstructed from the Registry Definition. Today both SBOM generation and the deploy side
trust the embedded coordinates whenever they are present, reconstructing from the Registry Definition only
when the descriptor was obfuscated at delivery, and nothing lets an operator force reconstruction when the
embedded coordinates are wrong for the target environment.

## Decision

We add an instance-repository configuration key that selects where application artifact coordinates come
from, because the multi-registry deployment is a durable structural choice that an operator must be able to
state once for the whole repository.

- The key is `artifact_coordinate_source`, an enum of `auto` and `regdef` that defaults to `auto`, so the
  existing behavior holds until an operator opts in.
- `auto` uses the embedded in DD chart and image coordinates when present and reconstructs from the
  Registry Definition only when the descriptor was obfuscated at delivery, because that preserves today's
  resolution for the single-registry case.
- `regdef` always reconstructs the chart and image coordinates from the Registry Definition and
  ignores the embedded in DD coordinates even when present, because in the multi-registry case the embedded ones
  are wrong for every environment but one. Helm base rewriting still applies to the reconstructed base as it
  does today.
- The key lives in the durable instance configuration alongside the other resolution-mode keys, because it
  states a lasting resolution policy rather than a per-environment registry topology, and reading it needs no
  environment render.
- The key is per instance repository, set once at the configuration root, because it declares the
  repository-wide deployment stance of multi-registry versus single-registry.
- Both SBOM generation and the deploy side use the key, so the Effective Set reflects the same chart that
  the deployment uses and the two never disagree.
- Instance-repository components read the configuration directly. The deploy side keeps its parameters-dict
  contract and the pipeline orchestrator injects the selected value into those parameters, because the deploy
  side is not taught a new configuration-reading path.

Rejected:

- Place the key in the per-environment Cloud end-to-end or pipeline parameters, because reading them needs a
  full Cloud render and they carry registry topology, while this is a repository-wide durable policy.
- Use the key only in SBOM generation and not on the deploy side, because the Effective Set would then
  resolve a different chart than the one the deployment pulls.

## Consequences

- An operator can force Registry-Definition reconstruction for a repository that targets several registries,
  so the generated coordinates match each target environment instead of the one the descriptor was built for.
- The default is unchanged, so existing repositories keep resolving coordinates exactly as before until they
  opt in.
- Cost we accept: the deploy side gains a reconstruction path it does not have today. Because it does not
  reconstruct the container image today, `regdef` for the image requires building the image URL from the
  Registry Definition on the deploy side.
- A per-environment difference is not a feature of this key. It is only available through the generic
  env-level configuration override that applies to every configuration key.

References: the decision to download the app chart for SBOM generation, and the `app_reg_def_mode`
resolution-mode key documented in [envgene-configs.md](/docs/envgene-configs.md).
