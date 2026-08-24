# Template Repository migration

Orchestrator skill: `migrate-template-repository`.

Migrates Environment Templates to External Credentials. By default every Template Descriptor
(or a user-named subset). Deterministic steps use `scripts/`. Structure / `create` / `remoteRefPath`
require user confirmation.

How-to: [Migrate Template Repository](/docs/how-to/migrate-template-repository-to-external-credentials.md)

## Layout

| Path | Role |
|------|------|
| [SKILL.md](SKILL.md) | Workflow, stop conditions, script commands |
| [references/](references/) | Structure rules, Credential Template, descriptor, transforms |
| [scripts/](scripts/) | Inventory, draft template, register descriptor, macros, validate |

## Start

```text
migrate-template-repository
```

## Script smoke tests

```bash
python scripts/tests/run_tests.py
```

Next folder: [../instance-repository/](../instance-repository/).
