# Mode: instance

Orchestrate Instance Repository YAML cutover. Prefer scripts under
[scripts/instance/](../scripts/instance/) for deterministic work.

Entry skill: [../SKILL.md](../SKILL.md). Overview: [overview.md](overview.md).

Obey entry skill **Hard constraints**. Mode-specific rules below.

## Hard constraints (instance)

- Read [instance/credential-policy.md](instance/credential-policy.md) before convert or apply.
  Analyze may run without user decisions.
- Never apply ambiguous proposals (`needsReview`, `confidence: ambiguous`, unknown owner/path).
  Exit `2` - stop and ask.
- `writeToStore` is plan-only. Never write it into Credential YAML.
- Plan may show `create: false`; final YAML omits the field when false.
- Never call Secret Store APIs from this mode. Transfer is [mode-transfer.md](mode-transfer.md).

## Prerequisites

- Concrete Template version with `external_credential_template` published (or user acknowledges
  risk).
- Instance Repository uses No-CMDB for deployer creds (delete deployer creds - do not convert).
- One `default_store` in `configuration/secret-stores.yml`.

**Stop** if unmet.

If CMDB / Cloud Deployer config leftovers remain, ask early: remove them in this migration, or
leave them for a separate No-CMDB migration. Remember the answer. Apply removal on the cleanup
step, not before YAML cutover work starts.

## Script contract

Exit `0` ok, `1` error, `2` `NEEDS_INPUT`. Always `--plan` before `--apply`.

## Workflow

Steps 1-10 stay in this mode. Pipeline, verify, and deploy after Step 10 are the user only.

Load references only when needed:

| When | Reference |
|------|-----------|
| Before convert | [instance/credential-policy.md](instance/credential-policy.md) |
| Secret Store | [instance/secret-store.md](instance/secret-store.md) |
| Passport | [instance/cloud-passport.md](instance/cloud-passport.md) |
| Shared | [instance/shared-credentials.md](instance/shared-credentials.md) |
| System | [instance/system-credentials.md](instance/system-credentials.md) |
| Parameters / cleanup | [instance/remaining-credentials.md](instance/remaining-credentials.md) |
| YAML shapes | [instance/transforms.md](instance/transforms.md) |

### Step 1. Preflight

```bash
python preflight.py --repo REPO
```

Read-only graph from `env_definition.yml`. Present with [instance/report-format.md](instance/report-format.md).

### Step 2. Inventory

```bash
python inventory.py --repo REPO
```

### Step 3. Classify and confirm decisions

```bash
python classify_credentials.py --repo REPO
```

Ask the user for every ambiguous row. Record confirmed decisions in a decisions JSON file.

### Step 4. Secret Store

Configure `configuration/secret-stores.yml` if missing
([instance/secret-store.md](instance/secret-store.md)).

### Step 5. Convert Cloud Passport

```bash
python convert_credential_files.py --repo REPO --files PATHS --decisions-json DECISIONS.json --secret-store ID --plan
python convert_credential_files.py ... --apply
python replace_macros.py --repo REPO --files PASSPORT_MAIN --plan
python replace_macros.py ... --apply
```

### Step 6. Convert Shared Credentials

```bash
python convert_credential_files.py --repo REPO --files PATHS --decisions-json DECISIONS.json --secret-store ID --plan
python convert_credential_files.py ... --apply
python fix_shared_master_refs.py --repo REPO --plan
python fix_shared_master_refs.py --repo REPO --apply
```

### Step 7. Convert System Credentials

```bash
python convert_credential_files.py --repo REPO --files PATHS --decisions-json DECISIONS.json --secret-store ID --plan
python convert_credential_files.py ... --apply
python replace_macros.py --repo REPO --files CONFIG_PATHS --plan
python replace_macros.py ... --apply
```

### Step 8. Update parameters

```bash
python replace_macros.py --repo REPO --files PATHS --plan
python replace_macros.py ... --apply
```

### Step 9. Cleanup generated / deployer / orphans

```bash
python cleanup_generated.py --repo REPO --environments cluster/env ... --plan
python cleanup_generated.py ... --apply
```

Delete deployer-creds and confirmed orphan Shared files when required (plan first). Apply the
CMDB leftover decision from Prerequisites here if the user chose removal.

### Step 10. Validate

```bash
python validate_instance.py --repo REPO --schemas-dir SCHEMAS --macro-files PATHS
```

### After Step 10 (user)

User commits and runs the Instance pipeline. Agent does not run it. Secret Store transfer (if
needed) is [mode-transfer.md](mode-transfer.md).

## Analyze report rules

Follow [instance/report-format.md](instance/report-format.md). One row per `credId`. Number decision questions.
Recommended option first.
