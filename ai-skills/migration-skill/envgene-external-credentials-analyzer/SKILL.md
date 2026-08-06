---
name: envgene-external-credentials-analyzer
description: Quickly analyse an EnvGene Instance Repository before External Credentials migration: find all Environment Instances, suggest non-prod candidates, identify Cloud Passport and Shared bindings, and show related Environment Instances. Change nothing.
---

# EnvGene External Credentials Analyzer

Perform a short read-only analysis. Do not change the repository.

## Constraints

- Work only with the local repository.
- Do not use the web, GitHub, or remote documentation.
- Do not create Python, PowerShell, shell, or other helper scripts.
- Do not open Credential files.
- Do not analyse System Credentials unless explicitly requested.

## First run

1. Find all `environments/<cluster>/<env>/Inventory/env_definition.yml` files.
2. For each Environment Instance, determine:
   - `<cluster>/<env>`;
   - `envTemplate.name` and `envTemplate.artifact`;
   - `inventory.cloudPassport`;
   - `envTemplate.sharedMasterCredentialFiles`.
3. From name and path, state only an assumption: `likely non-prod`, `likely prod`, or `unknown`.
4. Do not assert the environment type without user confirmation.
5. Suggest up to three suitable non-prod candidates.
6. Ask the user to select the first Environment Instance.

## After Environment Instance selection

1. Find all Environment Instances using the same Cloud Passport.
2. Find all Environment Instances using the same Shared Credentials.
3. Show which sources are used only by the selected Environment Instance and which are shared.
4. For a shared source, suggest:
   - migrating all consumers together;
   - splitting the shared source first.
5. Record:

```text
Template migration status: NOT_VERIFIED
```

You cannot determine from the Instance Repository whether the Environment Template has been updated.

## Unbound resources

Check only on command:

```text
Check unbound Shared Credentials and Cloud Passports.
```

Compare resource names with bindings without opening Credential files.

For each found resource, ask the user to choose:

1. include - the user specifies Environment Instances, then binding is added in a separate change;
2. do not include;
3. check later.

Do not include a resource automatically.

## Report

Create or update `external-credentials-migration-report.md`:

```markdown
# External Credentials Migration

## Environment Instances
| Environment | Assumed type | Template | Cloud Passport | Shared Credentials |
|---|---|---|---|---|

## Recommended start
...

## Selected group
- Environment:
- Type:
- Template:
- Template migration status: NOT_VERIFIED
- Cloud Passport:
- Shared Credentials:

## Related Environment Instances
| Source | Consumers |
|---|---|

## Next action
Select the first non-prod Environment Instance.
```

Show a short table, recommendation, and one question. Do not add a full Credential inventory, Credential values, or long status blocks.
