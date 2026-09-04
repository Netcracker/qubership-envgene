---
name: migrate-instance-repository
description: >-
  Migrates an EnvGene Instance Repository from local Credentials to External Credentials:
  inventory, classify with creation-owner policy, confirm create/remoteRefPath, plan/apply via
  scripts, validate. Use for instance external-creds YAML cutover.
---

# Migrate Instance Repository

Orchestrate Instance Repository YAML cutover. Prefer scripts for deterministic work.

Pack root: [../../README.md](../../README.md).

## Hard constraints

- Read [references/credential-policy.md](references/credential-policy.md) before convert or apply.
  Analyze may run without user decisions.
- Never apply ambiguous proposals (`needsReview`, `confidence: ambiguous`, unknown owner/path).
  Exit `2` - stop and ask.
- Never invent `create` or `remoteRefPath`. Never print `data` values.
- `writeToStore` is plan-only. Never write it into Credential YAML.
- Plan may show `create: false`; final YAML omits the field when false.
- Always set `secretStore` on external entries (usually `default_store`).
- Never run pipeline, deploy, commit, push, or merge.
- Never call Secret Store APIs or `migration-cli` from this skill.

## Prerequisites

- Concrete Template version with `external_credential_template` published (or user acknowledges risk).
- Instance Repository uses No-CMDB for deployer creds (delete deployer creds - do not convert).
- One `default_store` in `configuration/secret-stores.yml`.

**Stop** if unmet.

## Script contract

Exit `0` ok, `1` error, `2` `NEEDS_INPUT`. Always `--plan` before `--apply`.

## Workflow

### 1. Preflight

```bash
python preflight.py --repo REPO
```

Read-only graph from `env_definition.yml`. Present with
[../shared/analyze-report-format.md](../shared/analyze-report-format.md).

### 2. Analyze

```bash
python inventory.py --repo REPO
python classify_credentials.py --repo REPO
```

Classify returns decision records without secret values.

### 3. Resolve NEEDS_INPUT

Ask the user for every ambiguous row. Record confirmed decisions in a decisions JSON file.

Source notes (load only when needed):

| When | Reference |
|------|-----------|
| Before convert | [credential-policy.md](references/credential-policy.md) |
| Secret Store | [secret-store.md](references/secret-store.md) |
| Passport | [cloud-passport.md](references/cloud-passport.md) |
| Shared | [shared-credentials.md](references/shared-credentials.md) |
| System | [system-credentials.md](references/system-credentials.md) |
| Parameters / cleanup | [remaining-credentials.md](references/remaining-credentials.md) |
| YAML shapes | [transforms.md](references/transforms.md) |

### 4. Secret Store

Configure `configuration/secret-stores.yml` if missing ([secret-store.md](references/secret-store.md)).

### 5. Plan and apply

Order: Passport → Shared → System → parameter macros → cleanup generated / deployer / confirmed orphans.

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

### 6. Validate

```bash
python validate_instance.py --repo REPO --schemas-dir SCHEMAS --macro-files PATHS
```

### 7. Handoff

User commits and runs the Instance pipeline on a non-prod environment. Agent does not run it.
Secret Store transfer (if needed) is outside this skill. See
[transfer-secrets-to-store](../../how-to/transfer-secrets-to-store.md).

## Analyze report rules

Follow [../shared/analyze-report-format.md](../shared/analyze-report-format.md). One row per
`credId`. Number decision questions. Recommended option first.
