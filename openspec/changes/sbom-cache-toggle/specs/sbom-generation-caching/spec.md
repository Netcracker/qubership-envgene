# Spec Delta

## Purpose

This capability defines whether SBOM generation stores its output as the `/sboms/` cache in the Instance
Repository, governed by the instance-global `sbom_cache.enabled` configuration, so a repository that spans
several zones can turn caching off and avoid reusing one zone's registry addresses in another.

## ADDED Requirements

### Requirement: SBOM caching is enabled by default

SBOM generation SHALL cache its output when `sbom_cache.enabled` is `true` or absent from `config.yml`:
it regenerates an application's SBOM only when the cached file is absent, and it stores the `/sboms/`
cache in the Instance Repository.

#### Scenario: Caching key absent

- **WHEN** SBOM generation runs and `config.yml` has no `sbom_cache.enabled` key
- **THEN** an application whose SBOM file is already present is not regenerated, and the `/sboms/` cache is
  stored in the Instance Repository

#### Scenario: Caching enabled explicitly

- **WHEN** SBOM generation runs with `sbom_cache.enabled: true`
- **THEN** an application whose SBOM file is already present is not regenerated, and the `/sboms/` cache is
  stored in the Instance Repository

### Requirement: Disabling SBOM caching regenerates every run and persists nothing

When `sbom_cache.enabled` is `false`, SBOM generation SHALL regenerate the SBOM for every application in
the deploy plan on every run regardless of whether a cached file is present, SHALL use the regenerated
SBOMs for Effective Set generation in that run, and SHALL NOT store them in the Instance Repository, so the
entire `/sboms/` directory is removed from the Instance Repository on every run, leaving no residual cache
from an earlier run.

#### Scenario: Caching disabled with applications to generate

- **WHEN** SBOM generation runs with `sbom_cache.enabled: false` and the deploy plan lists applications
- **THEN** every listed application's SBOM is regenerated, the regenerated SBOMs are available to Effective
  Set generation for that run, and the Instance Repository contains no `/sboms/` directory afterwards

#### Scenario: Environment in a second zone does not reuse another zone's SBOM

- **WHEN** an environment in one zone and an environment in another zone of the same Instance Repository
  each run SBOM generation with `sbom_cache.enabled: false`
- **THEN** each environment's SBOM carries the registry addresses of its own zone, because neither reuses
  the other's SBOM

#### Scenario: Caching disabled with nothing to generate

- **WHEN** SBOM generation runs with `sbom_cache.enabled: false` and there is nothing to generate, because
  the deploy plan is empty or no Solution Descriptor is present
- **THEN** the entire `/sboms/` directory is removed from the Instance Repository anyway

#### Scenario: Caching disabled across a multi-environment run

- **WHEN** several environments of the same Instance Repository run SBOM generation in one
  multi-environment run with `sbom_cache.enabled: false`
- **THEN** each environment removes the entire `/sboms/` directory, and the committed result is the absence
  of the `/sboms/` directory for every environment

### Requirement: SBOM retention has no effect when caching is disabled

When `sbom_cache.enabled` is `false`, SBOM retention SHALL have no effect, because SBOM generation persists
nothing for retention to clean.

#### Scenario: Retention enabled together with caching disabled

- **WHEN** SBOM generation runs with `sbom_cache.enabled: false` and `sbom_retention.enabled: true`
- **THEN** no `/sboms/` cache is persisted and retention changes nothing

### Requirement: The configuration schema validates the SBOM cache key

The `config.yml` schema SHALL accept a `sbom_cache` object with a boolean `enabled` property and SHALL
reject an invalid `enabled` value, consistent with the existing `sbom_retention` and `cache` keys.

#### Scenario: Invalid caching value

- **WHEN** `config.yml` sets `sbom_cache.enabled` to a value that is not a boolean
- **THEN** configuration validation rejects it with a schema error
