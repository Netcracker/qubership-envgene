# EnvGene External Credentials migration skills

Two orchestrator skills. Deterministic work runs via `scripts/`. Heuristic decisions stay in the
skill and require user confirmation.

| Folder | Skill name | How-to |
|--------|------------|--------|
| [template-repository/](template-repository/) | `migrate-template-repository` | [Template how-to](/docs/how-to/migrate-template-repository-to-external-credentials.md) |
| [instance-repository/](instance-repository/) | `migrate-instance-repository` | [Instance how-to](/docs/how-to/migrate-instance-repository-to-external-credentials.md) |

Order: finish Template (publish concrete version) → then Instance.

## Rules

- Edit source YAML only after a script `--plan` the user confirmed.
- Never run pipeline, deploy, commit, push, or merge.
- Never print or copy values from `data`.
- Never invent `create`, `remoteRefPath`, or `properties` from the `credId` name.
- Script exit code `2` means ask the user; do not guess.
