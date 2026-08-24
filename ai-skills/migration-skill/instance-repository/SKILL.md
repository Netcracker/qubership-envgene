---
name: migrate-instance-repository
description: >-
  Migrates an EnvGene Instance Repository from local Credentials to External Credentials:
  inventory, classify with creation-owner policy, confirm create/remoteRefPath, plan/apply via
  scripts, validate. Use when cutting over instance credentials or triaging external-creds migration.
---

# Migrate Instance Repository

Orchestrate Instance Repository cutover. Prefer scripts for deterministic work.

How-to: [/docs/how-to/migrate-instance-repository-to-external-credentials.md](/docs/how-to/migrate-instance-repository-to-external-credentials.md)

## Hard constraints

- Read [references/credential-policy.md](references/credential-policy.md) **before** Prepare / convert /
  apply. Analyze may run without user decisions.
- Never apply an ambiguous proposal (`needsReview: true`, `confidence: ambiguous`, unknown owner,
  or missing required path). Status `NEEDS_INPUT` (exit `2`) - stop and ask.
- Show evidence and proposed values in the report. Never invent `create` or `remoteRefPath`.
- Never print or copy values from `data`. Never run pipeline, deploy, commit, push, or merge.
- `writeToStore` is plan-only; never write it into Credential YAML.
- Plan may show `create: false`; final YAML omits the field.

## Prerequisites

- Concrete Template version with `external_credential_template` published.
- Secrets that must be kept are in the Store (or generation explicitly allowed).
- Instance Repository uses No-CMDB.

**Stop** if unmet.

## Script contract

| Exit | JSON `status` | Meaning |
|------|---------------|---------|
| `0` | `ok` | proceed |
| `1` | `error` | fix and retry |
| `2` | `NEEDS_INPUT` / `ambiguous` | ask user; do not apply |

Always `--plan` before `--apply`. Confirm decisions first.

## Workflow

### 1. Analyze (no user decisions required)

```bash
python inventory.py --repo REPO
python classify_credentials.py --repo REPO
```

Classify returns decision records: `tier`, `creationOwner`, `evidence`, `confidence`,
`proposedCreate`, `proposedRemoteRefPath`, `needsReview`. No secret values.

### 2. Resolve NEEDS_INPUT

For each `needsReview` / ambiguous / unknown owner or path: ask the user. Record confirmed
decisions (`confidence: confirmed`, `needsReview: false`) in a decisions JSON file for convert.

Read source-specific notes only when needed:

| When | Reference |
|------|-----------|
| Before any convert | [credential-policy.md](references/credential-policy.md) |
| Secret Store setup | [secret-store.md](references/secret-store.md) |
| Passport | [cloud-passport.md](references/cloud-passport.md) |
| Shared | [shared-credentials.md](references/shared-credentials.md) |
| System | [system-credentials.md](references/system-credentials.md) |
| Parameters / cleanup | [remaining-credentials.md](references/remaining-credentials.md) |
| YAML shapes | [transforms.md](references/transforms.md) |

### 3. Secret Store

Configure `configuration/secret-stores.yml` if needed ([secret-store.md](references/secret-store.md)).

### 4. Plan and apply (confirmed decisions only)

```bash
python convert_credential_files.py --repo REPO --files PATHS --decisions-json DECISIONS.json --secret-store ID --plan
python convert_credential_files.py ... --apply
python replace_macros.py --repo REPO --files PATHS --plan
python replace_macros.py ... --apply
python fix_shared_master_refs.py --repo REPO --plan
python fix_shared_master_refs.py --repo REPO --apply
python cleanup_generated.py --repo REPO --environments cluster/env ... --plan
python cleanup_generated.py ... --apply
```

Order: Passport → Shared → System (optional) → parameter macros → cleanup generated.

### 5. Validate

```bash
python validate_instance.py --repo REPO --schemas-dir SCHEMAS --macro-files PATHS
```

### 6. Handoff

User commits and runs Instance pipeline on non-prod (`CMDB_IMPORT=false`). Agent does not run it.

## Progressive disclosure

Do not paste the full policy into replies. Link and run scripts; use JSON output.
