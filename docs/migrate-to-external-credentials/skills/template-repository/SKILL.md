---
name: migrate-template-repository
description: >-
  Migrates EnvGene Template Repository credentials to External Credentials: inventory evidence,
  confirm create/remoteRefPath per credential-policy, draft Credential Template, register
  descriptor, replace macros, validate. Use for template external-creds YAML cutover.
---

# Migrate Template Repository

Orchestrate Template Repository YAML cutover. Prefer scripts for deterministic work.

Pack root: [../../README.md](../../README.md).

## Hard constraints

- Read [references/credential-policy.md](references/credential-policy.md) before draft or apply.
  Inventory may run without user decisions.
- Never apply ambiguous `create` / `remoteRefPath`. Exit `2` (`NEEDS_INPUT`) - stop and ask.
- Show evidence and proposals. Never invent `create` or `remoteRefPath`.
- Never use `{{ current_env.namespace }}` in Credential Template paths.
- Default path proposal: `{{ current_env.cloud }}/{{ current_env.name }}`.
- Credential Template path: `templates/external-credentials/<descriptor-stem>.yml.j2`.
- Always set `secretStore` on Credential Template entries (`default_store` unless confirmed).
- Never open Instance Credential `data` for secret values.
- Never migrate Template system credentials.
- Never run build, publish, commit, push, merge, or pipeline.

## Script contract

Exit `0` ok, `1` error, `2` `NEEDS_INPUT`. Always `--plan` before `--apply`.

Run scripts from `scripts/` with the Template Repository as `--repo`.

## Workflow

### 1. Preflight

```bash
python preflight.py --repo REPO
```

Read-only. Exit `0` to continue; exit `2` to fix blockers and re-run. Present output with
[../shared/analyze-report-format.md](../shared/analyze-report-format.md).

### 2. Inventory

```bash
python inventory_credids.py --repo REPO
```

Returns structure evidence and policy proposals. No secret values. Read
[references/structure-from-refs.md](references/structure-from-refs.md).

### 3. Confirm decisions

Resolve every `needsReview` / ambiguous row. Confirmed records are required before draft.

### 4. Draft Credential Template

Read [references/credential-template.md](references/credential-template.md) and
[references/transforms.md](references/transforms.md).

```bash
python draft_credential_template.py --repo REPO --output PATH --credentials-json '...' --secret-store ID --plan
python draft_credential_template.py ... --apply
```

### 5. Register descriptor

[references/descriptor.md](references/descriptor.md) → `register_descriptor.py`.

### 6. Replace macros

`replace_macros.py --plan` then `--apply`.

### 7. Validate

```bash
python validate_template.py --repo REPO --descriptor PATH --credential-template PATH --macro-files PATHS --schemas-dir SCHEMAS
```

### 8. Handoff

User publishes a concrete Template version, then runs Instance migration. Agent does not publish.

## Analyze report rules

Follow [../shared/analyze-report-format.md](../shared/analyze-report-format.md). Paths only - no
YAML dumps. One table row per `credId`. Number decision questions with the recommended option first.
