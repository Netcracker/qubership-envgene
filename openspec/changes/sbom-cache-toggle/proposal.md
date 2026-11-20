# Proposal

## Why

A generated SBOM carries the container-image registry addresses of its components, and those addresses
differ per zone. The SBOM cache lives in the shared root `/sboms/` of the Instance Repository, keyed by
application name, and the generator regenerates an SBOM only when its file is absent. When one Instance
Repository spans several zones, the first environment commits an SBOM carrying its own zone's addresses,
and an environment in another zone finds the file present, skips regeneration, and inherits the wrong
addresses. Storing SBOMs per environment would fix this but grows Git history and repository size, and a
registry-aware regeneration criterion would make the cache regenerate on every run and erase its benefit.
For such a repository the operator needs a way to turn SBOM caching off.

## What Changes

- SBOM generation gains an instance-global configuration key `sbom_cache.enabled` in `config.yml`,
  default `true`. When `true` or absent, SBOM generation behaves as today: it regenerates an SBOM only
  when the cached file is absent, and the `/sboms/` cache is stored in the Instance Repository.
- When `sbom_cache.enabled` is `false`, SBOM generation does not cache. On every run it regenerates the
  SBOM for every application in the deploy plan and does not store the result in the Instance Repository,
  so the entire `/sboms/` directory is removed from the Instance Repository on each run, folder and all,
  leaving no residual cache from an earlier run. The regenerated SBOMs are still used for Effective Set
  generation within that run.
- With `sbom_cache.enabled` set to `false`, SBOM retention has no effect, because nothing is persisted for
  it to clean.
- The `config.yml` schema accepts the `sbom_cache` object and rejects an invalid `enabled` value,
  consistent with the existing `sbom_retention` and `cache` keys.

## Capabilities

### New Capabilities

- `sbom-generation-caching`: whether SBOM generation stores its output as the `/sboms/` cache in the
  Instance Repository, governed by the `sbom_cache.enabled` configuration. Covers the default caching
  behavior, the no-cache behavior (regenerate every run, no persistence, remove the committed cache
  including when there is nothing to generate), the no-effect interaction with SBOM retention, and the
  multi-environment case.

### Modified Capabilities

<!-- No existing specs under openspec/specs/ cover SBOM generation caching. -->

## Impact

- Objects and parameters: the new `sbom_cache.enabled` configuration key in `config.yml`, with its schema.
- Pipeline steps: SBOM generation within Effective Set generation.
- Docs: the SBOM feature doc and the EnvGene configuration reference.
- Decision record: [ADR-0013](../../../docs/adr/0013-toggle-sbom-generation-caching.md).
- Behavior detail: the delta spec under [specs/](specs/sbom-generation-caching/spec.md).
