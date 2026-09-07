# Migrate to External Credentials (pack)

P2 self-contained skill pack: one entry skill, three modes, scripts, and migration CLI inside
this folder. Skill name: `migrate-to-external-credentials`.

- [Discovery](#discovery)
- [Reading order](#reading-order)
- [Layout](#layout)
- [Install CLI](#install-cli)
- [Out of scope](#out-of-scope)

## Discovery

Canonical in-repo path: `docs/migrate-to-external-credentials/` (this folder). Scripts and
CLI stay here so the pack remains self-contained.

For Cursor / Claude skill discovery, install or junction this folder under a skills root (do not
fork a second copy of the scripts):

| Client | Skills root |
|--------|-------------|
| Cursor project | `.cursor/skills/migrate-to-external-credentials/` |
| Cursor personal | `~/.cursor/skills/migrate-to-external-credentials/` |
| Claude Code personal | `~/.claude/skills/migrate-to-external-credentials/` |

Prefer a directory junction or symlink to this docs path. If you must copy, sync from this folder
after changes. Entry file: [SKILL.md](SKILL.md) (`disable-model-invocation: true` - attach or
invoke explicitly).

## Reading order

| Step | Mode | Reference |
|------|------|-----------|
| 0 | - | [references/overview.md](references/overview.md) |
| 1 | `template` | [references/mode-template.md](references/mode-template.md) |
| 2 | `transfer` (`collect`) | [references/mode-transfer.md](references/mode-transfer.md) - if values are still in Instance Git |
| 3 | `instance` | [references/mode-instance.md](references/mode-instance.md) |
| 4 | `transfer` (`fill` / export) | [references/mode-transfer.md](references/mode-transfer.md) - after Effective Set `skip` |

Invoke the skill once: [SKILL.md](SKILL.md). The agent picks a mode and stays on it until that
mode ends.

## Layout

```text
docs/migrate-to-external-credentials/
  SKILL.md                 # only skill entry
  README.md
  references/
    overview.md
    mode-template.md
    mode-instance.md
    mode-transfer.md
    template/              # Template policy, report format, transforms
    instance/              # Instance policy, report format, transforms
  scripts/
    template/
    instance/
    shared/extcreds_mig/
  cli/                     # migration-cli (runtime only)
```

Dev tests for `migration-cli` live outside the skill pack, at repo-root
`scripts/tests/migration_cli/` - alongside the tests for the repo's other `scripts/` modules
(`creds_rotation/`, etc.). They are not part of what gets junctioned into a skills root.

## Install CLI

```bash
cd docs/migrate-to-external-credentials/cli
pip install -e .
pip install -e ".[decrypt]"   # Fernet field-level decryption
```

## Out of scope

- Pipeline orchestration inside the skill (clone, branch, commit, pipeline) - later P2
- Blue-Green and template composition
- Template Repository system credentials (local-only by design)
- Putting actual passwords or tokens in Git, MRs, or migration notes
- Mixing No-CMDB migration into this pack (ask only; do not run that migration here)
