# SBOM Storage Migration Use Case

- [SBOM Storage Migration Use Case](#sbom-storage-migration-use-case)
  - [Overview](#overview)
  - [UC-SBOM-MIG-1: First run after upgrade](#uc-sbom-mig-1-first-run-after-upgrade)

## Overview

This document describes the use case for **automatic migration** from the flat SBOM layout to the per-application layout when upgrading EnvGene. For the procedural guide (when to use it, what to expect), see [Migrate SBOM Storage to Per-Application Layout](/docs/how-to/sbom-storage-migration.md). Target layout: [SBOM directory layout](/docs/features/sbom.md#sbom-directory-layout).

## UC-SBOM-MIG-1: First run after upgrade

**Pre-requisites:**

1. Instance Repository has SBOM files in the flat layout: `/sboms/<application-name>-<application-version>.sbom.json`
2. EnvGene (Instance pipeline) is upgraded to a version that uses the per-application SBOM layout

**Trigger:**

Instance pipeline is run with parameters that trigger effective set generation (e.g. `ENV_NAMES: <env>`, `GENERATE_EFFECTIVE_SET: true`).

**Steps:**

1. The pipeline runs with the new EnvGene version.
2. The `generate_effective_set` job (or equivalent) detects the old flat SBOM layout.
3. EnvGene removes all SBOM files from `/sboms/` (flat location).
4. For each application version required by the Solution Descriptor, EnvGene generates the SBOM and writes it to `/sboms/<application-name>/<application-name>-<application-version>.sbom.json`.
5. Effective set generation completes using the new SBOM paths.

**Results:**

1. No SBOM files remain directly under `/sboms/`; all SBOMs are under `/sboms/<application>/`.
2. Effective set is generated successfully.
3. Repository contains the new layout; subsequent runs do not perform migration again.
4. The run may take longer than usual due to SBOM regeneration.
