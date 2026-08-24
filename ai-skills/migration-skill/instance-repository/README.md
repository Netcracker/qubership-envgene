# Instance Repository migration

Orchestrator skill: `migrate-instance-repository`.

Migrates an Instance Repository to External Credentials. File edits go through `scripts/` after
user confirmation. Heuristic choices (`create`, `remoteRefPath`, multi-store, System now/later)
are asked in the skill - never invented.

Prerequisite: Template Repository migrated and a concrete Template version published.

How-to: [Migrate Instance Repository](/docs/how-to/migrate-instance-repository-to-external-credentials.md)

## Layout

| Path | Role |
|------|------|
| [SKILL.md](SKILL.md) | Workflow, stop conditions, when to run scripts / read references |
| [references/](references/) | Cloud Passport, Shared, System, remaining, Secret Store, transforms |
| [scripts/](scripts/) | Deterministic inventory, convert, macros, cleanup, validate |

## Start

```text
migrate-instance-repository
```

## Script smoke tests

```bash
python scripts/tests/run_tests.py
```

Previous folder: [../template-repository/](../template-repository/).
