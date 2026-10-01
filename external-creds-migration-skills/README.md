# External Credentials migration kit

| Piece | Role |
|-------|------|
| [migration-skills/](migration-skills/) | Skill entry (welcome: where are creds?) |
| [migration-skills/scripts/python/envgene_migrate/](migration-skills/scripts/python/envgene_migrate/) | YAML `plan` / `apply` |
| [migration-skills/scripts/cli/](migration-skills/scripts/cli/) | `migration-cli` collect / export / fill |
| [migration-skills/scripts/external-cred-provision/](migration-skills/scripts/external-cred-provision/) | `external-cred-provision` (Store writes) |
| [migration-skills/transfer-config.example.yml](migration-skills/transfer-config.example.yml) | Optional agent helper for transfer |

**Start here:** [migration-skills/commands.md](migration-skills/commands.md)
(commands + when to use apply-Store vs transfer).

Then invoke `/migration-skills` or attach [migration-skills/SKILL.md](migration-skills/SKILL.md)
(welcome, modes, hard constraints, [when the agent stops](migration-skills/SKILL.md#when-the-agent-stops)).

Modes: [template](migration-skills/references/mode-template.md) ·
[instance](migration-skills/references/mode-instance.md) ·
[transfer](migration-skills/references/mode-transfer.md) ·
[plan-review](migration-skills/references/plan-review.md).

Instance defaults: passport/system auto (`create: false`; system path `global` +
Store write on apply); everything else asked in `to_review`. Whole-repo plan unless
`--env CLUSTER/ENV`. Use `--verbose` for per-cred logs.
