# Spec Delta

## Purpose

This capability defines the effective-set generator's unconditional application-chart requirement - it
fails loud when a SBOM carries no app-chart component, it always writes per-service parameters under one
directory keyed by the normalized app-chart name, and it ignores the removed legacy validation toggle.

## ADDED Requirements

### Requirement: App-chart component is required for effective-set generation

The effective-set generator SHALL require a SBOM to carry an app-chart component and SHALL fail
effective-set generation loud with a readable error naming the application when the app-chart component is
absent, rather than silently writing per-service parameters under per-service-name directories.

#### Scenario: SBOM has no app-chart component

- **WHEN** effective-set generation reads a SBOM that has no app-chart component
- **THEN** generation fails with a readable error naming the application

### Requirement: Per-service parameters keyed by the normalized app-chart name

The effective-set generator SHALL always write per-service parameters under one directory keyed by the
app-chart name, normalized by the generator's existing Helm name normalization, one section per service,
with no per-service-name fallback layout.

#### Scenario: Per-service parameters under the app-chart directory

- **WHEN** effective-set generation reads a SBOM that carries an app-chart component with services
- **THEN** all per-service parameters are written under the single directory keyed by the normalized
  app-chart name, one section per service

### Requirement: Legacy app-chart validation toggle is ignored

The effective-set generator SHALL treat the application-chart requirement as unconditional, and SHALL
ignore an `app_chart_validation` entry that is still present in the effective-set configuration without
raising an unknown-option error.

#### Scenario: Configuration still carries the removed toggle

- **WHEN** the effective-set configuration still carries an `app_chart_validation` entry
- **THEN** generation ignores the entry, does not raise an unknown-option error, and still enforces the
  app-chart requirement unconditionally
