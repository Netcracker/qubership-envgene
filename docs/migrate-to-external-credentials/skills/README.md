# Migration skills

Agent skills for YAML cutover. See the pack [README](../README.md) for how-tos and CLI.

| Folder | Skill |
|--------|-------|
| [template-repository/](template-repository/) | `migrate-template-repository` |
| [instance-repository/](instance-repository/) | `migrate-instance-repository` |

Shared helpers: [shared/extcreds_mig/](shared/extcreds_mig/).
Report format: [shared/analyze-report-format.md](shared/analyze-report-format.md).

Script exit codes: `0` ok, `1` error, `2` `NEEDS_INPUT`. Always `--plan` before `--apply`.

Skills do not run pipeline, handle actual passwords and tokens, or write the Secret Store. Use
[transfer-secrets-to-store how-to](../how-to/transfer-secrets-to-store.md) and
[migration-cli](../cli/) for Store transfer.
