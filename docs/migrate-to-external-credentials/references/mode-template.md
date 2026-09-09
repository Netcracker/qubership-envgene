# Mode: template

Orchestrate Template Repository YAML cutover. Prefer scripts under
[scripts/template/](../scripts/template/) for deterministic work.

Entry skill: [../SKILL.md](../SKILL.md). Overview: [overview.md](overview.md).

Obey entry skill **Hard constraints**. Mode-specific rules below.

## Hard constraints (template)

- Read [template/credential-policy.md](template/credential-policy.md) before draft or apply.
  Inventory may run without user decisions.
- Never apply ambiguous `create` / `remoteRefPath`. Exit `2` (`NEEDS_INPUT`) - stop and ask.
- Default path proposal: `{{ current_env.cloud }}/{{ current_env.name }}`.
- Credential Template path: `templates/external-credentials/<descriptor-stem>.yml.j2`.
- Never open Instance Credential `data` for secret values.
- Never migrate Template system credentials.
- Non-empty `technicalConfigurationParameterSets` is a **blocker only if** those ParameterSets
  still contain `creds.get` / `#creds`. If macros are gone, treat as warning and continue.
  Present blockers with [template/report-format.md](template/report-format.md) Critical callout; do not continue
  until the user chooses.
- **Compact reports:** do not paste full script JSON; full cred table only for ask/review rows;
  batch the rest. See report-format Global rules.

## Script contract

Exit `0` ok, `1` error, `2` `NEEDS_INPUT`. Always `--plan` before `--apply`.

Run scripts from [scripts/template/](../scripts/template/) with the Template Repository as
`--repo`.

## Workflow

Stay on this mode for Steps 1-7. Do not switch modes mid-cutover.

### Step 1. Preflight

```bash
python preflight.py --repo REPO
```

Read-only. Exit `0` to continue; exit `2` to fix blockers and re-run. Present output with
[template/report-format.md](template/report-format.md).

### Step 2. Inventory (collect credential IDs)

```bash
python inventory_credids.py --repo REPO
```

Returns structure evidence and policy proposals. No secret values. Read
[template/structure-from-refs.md](template/structure-from-refs.md).

### Step 3. Confirm decisions

Resolve every `needsReview` / ambiguous row. Confirmed records are required before draft.

### Step 4. Draft Credential Template

Read [template/credential-template.md](template/credential-template.md) and
[template/transforms.md](template/transforms.md).

```bash
python draft_credential_template.py --repo REPO --output PATH --credentials-json '...' --secret-store ID --plan
python draft_credential_template.py ... --apply
```

### Step 5. Register descriptor

Read [template/descriptor.md](template/descriptor.md). Credential Template file must already exist.

```bash
python register_descriptor.py --repo REPO --descriptor DESCRIPTOR_REL --template-path '{{ templates_dir }}/external-credentials/<stem>.yml.j2' --plan
python register_descriptor.py ... --apply
```

### Step 6. Replace macros

```bash
python replace_macros.py --repo REPO --files PATHS --plan
python replace_macros.py --repo REPO --files PATHS --apply
```

### Step 7. Validate and handoff

```bash
python validate_template.py --repo REPO --descriptor PATH --credential-template PATH --macro-files PATHS --schemas-dir SCHEMAS
```

User publishes a concrete Template version, then runs Instance migration. Agent does not publish.

## Analyze report rules

Follow [template/report-format.md](template/report-format.md). Paths only - no YAML dumps. One table row per
`credId`. Number decision questions with the recommended option first.
