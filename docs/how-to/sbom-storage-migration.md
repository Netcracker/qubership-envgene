# Migrate SBOM Storage to Per-Application Layout

This guide describes how migration to the per-application SBOM layout works when you run EnvGene with a version that uses the new storage structure.

- [Migrate SBOM Storage to Per-Application Layout](#migrate-sbom-storage-to-per-application-layout)
  - [When to use this guide](#when-to-use-this-guide)
  - [How migration works](#how-migration-works)
  - [What to expect](#what-to-expect)

## When to use this guide

Use this guide when:

- Your Instance Repository currently has SBOM files stored directly under `/sboms/` (flat layout)
- You are upgrading EnvGene (Instance pipeline) to a version that uses the new per-application SBOM layout

After the first run with the new version, [SBOM Retention](/docs/features/sbom-retention.md) and Effective Set generation will use the new paths. See [SBOM directory layout](/docs/features/sbom.md#sbom-directory-layout) for the target structure.

## How migration works

Migration is **automatic** when you run the Instance pipeline with an EnvGene version that implements the new SBOM storage structure:

1. **Old SBOMs are removed** - SBOM files in the previous flat location (`/sboms/*.sbom.json`) are deleted by EnvGene.
2. **New SBOMs are generated** - SBOMs are generated and written to the new layout: `/sboms/<application-name>/<application-name>-<application-version>.sbom.json`.

You do **not** need to move or copy files manually. The first pipeline run that includes the `generate_effective_set` job (e.g. with `GENERATE_EFFECTIVE_SET: true`) and uses the new EnvGene version will clear the old flat SBOMs and produce SBOMs in the per-application directories. Because SBOM generation can be expensive, that run may take longer than usual while SBOMs are recreated.

Example:

- **Before:** `/sboms/Cloud-BSS-1.2.3.sbom.json`, `/sboms/cloud-oss-2.0.1.sbom.json`
- **After:** `/sboms/Cloud-BSS/Cloud-BSS-1.2.3.sbom.json`, `/sboms/cloud-oss/cloud-oss-2.0.1.sbom.json`

For the formal scenario (pre-requisites, trigger, steps, results), see [SBOM Storage Migration Use Case](/docs/use-cases/sbom-storage-migration.md).

## What to expect

- **First run with new EnvGene version:** Flat SBOMs under `/sboms/` are removed; SBOMs are generated into `/sboms/<application-name>/`. The job may take longer while SBOMs are regenerated.
- **Later runs:** Only the new layout is used; no migration step runs again.
- **Rollback:** If you revert to an older EnvGene version that expects the flat layout, you would need to run that version again; it may regenerate SBOMs in the old flat structure (behavior depends on that version).
