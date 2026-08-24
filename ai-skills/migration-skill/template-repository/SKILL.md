---
name: migrate-template-repository
description: >-
  Migrates EnvGene Template Repository credentials to External Credentials: inventory evidence,
  confirm create/remoteRefPath per credential-policy, draft Credential Template, register
  descriptor, replace macros, validate. Use for template external-creds migration.
---

# Migrate Template Repository

How-to: [/docs/how-to/migrate-template-repository-to-external-credentials.md](/docs/how-to/migrate-template-repository-to-external-credentials.md)

After publish → `migrate-instance-repository`.

## Hard constraints

- Read [references/credential-policy.md](references/credential-policy.md) **before** draft / Prepare.
  Inventory (Analyze) may run without user decisions.
- Never apply ambiguous create/path. Status `NEEDS_INPUT` (exit `2`) - stop and ask.
- Show evidence and proposed values. Never invent `create` or `remoteRefPath`.
- Never use `{{ current_env.namespace }}` without proof it exists in this Jinja context.
- Default Template path proposal: `{{ current_env.cloud }}/{{ current_env.name }}`.
- Never open Instance Credential files for secret values. Never migrate Template System Credentials.
- Never run build, publish, commit, push, or merge.

## Script contract

Exit `0` ok, `1` error, `2` `NEEDS_INPUT`. Always `--plan` before `--apply`.

## Workflow

### 1. Inventory (Analyze)

```bash
python inventory_credids.py --repo REPO
```

Returns structure evidence + policy proposals. No secret values.

Read [structure-from-refs.md](references/structure-from-refs.md).

### 2. Confirm decisions

Resolve `NEEDS_INPUT`. Confirmed records required before draft.

### 3. Draft Credential Template

Read [credential-template.md](references/credential-template.md) and
[transforms.md](references/transforms.md).

```bash
python draft_credential_template.py --repo REPO --output PATH --credentials-json '...' --secret-store ID --plan
python draft_credential_template.py ... --apply
```

`--credentials-json` items must include confirmed `structure`, `creationOwner`, `proposedCreate`,
`proposedRemoteRefPath` (or rely on defaults only when confidence is confirmed).

### 4. Register descriptor

[descriptor.md](references/descriptor.md) → `register_descriptor.py`.

### 5. Replace macros

`replace_macros.py --plan` / `--apply`.

### 6. Validate

```bash
python validate_template.py --repo REPO --descriptor PATH --credential-template PATH --macro-files PATHS --schemas-dir SCHEMAS
```

### 7. Handoff

User publishes concrete version, then Instance migration.
