---
name: migrate-to-external-credentials
description: >-
  Migrates EnvGene Template and Instance repositories from local Credentials to External
  Credentials. Routes to template YAML cutover, instance YAML cutover, or secret transfer
  (collect / export / fill). Use when starting external-creds migration or when the user asks
  which migration mode to run.
disable-model-invocation: true
---

# Migrate to External Credentials

One pack entry for External Credentials migration. Prefer scripts and `migration-cli` for
deterministic work. Do not invent paths or secret values.

Canonical pack path in this repository: `docs/migrate-to-external-credentials/`.

- [Modes](#modes)
- [Hard constraints (all modes)](#hard-constraints-all-modes)
- [Script and CLI layout](#script-and-cli-layout)
- [Reports](#reports)
- [Examples](#examples)
- [After the mode ends](#after-the-mode-ends)

Pack root: [README.md](README.md). Human flow: [references/overview.md](references/overview.md).

Policy (load when drafting or converting):

- Template: [references/template/credential-policy.md](references/template/credential-policy.md)
- Instance: [references/instance/credential-policy.md](references/instance/credential-policy.md)

## Modes

Pick **one** mode per run. If unclear, ask the user. Then load that mode file and follow it.

| Mode | When | Load next |
|------|------|-----------|
| `template` | Template Repository YAML cutover | [references/mode-template.md](references/mode-template.md) |
| `instance` | Instance Repository YAML cutover | [references/mode-instance.md](references/mode-instance.md) |
| `transfer` | Move passwords and tokens into the Secret Store | [references/mode-transfer.md](references/mode-transfer.md) |

Suggested order for a full cutover:

1. `template` - user publishes a Template version after the agent finishes.
2. `transfer` with `collect` - only if values still live in Instance Git (before instance cutover).
3. `instance`.
4. User runs Effective Set with `EXTERNAL_CREDENTIAL_PROVISIONING=skip`.
5. `transfer` with `export-credentials` (Jenkins) and/or `fill`, then `external-cred-provision`.
6. User runs Effective Set with `apply` (default), then test deploy.

Stay in the chosen mode until that mode finishes. Do not switch mid-cutover.

## Hard constraints (all modes)

- Never invent `create` or `remoteRefPath`. Stop and ask (`NEEDS_INPUT`).
- Never print Credential `data` values, passwords, or tokens.
- Never commit collect / export / fill outputs to Git.
- Always `--plan` before `--apply` for YAML scripts.
- Script exit codes: `0` ok, `1` error, `2` `NEEDS_INPUT`.
- Always set `secretStore` on external Credential entries (usually `default_store`).
- Do not append `credId` to `remoteRefPath` in YAML. EnvGene appends the normalised id.
- Never run commit, push, merge, publish, or pipeline (automation is a later P2 step).
- Never call Secret Store write APIs from YAML cutover modes. Store write is
  `external-cred-provision` after `fill`.
- Template mode: never migrate Template system credentials. Never use
  `{{ current_env.namespace }}` in Credential Template paths.
- Instance mode: stop if No-CMDB deployer prerequisites are unmet. Delete deployer creds. Do
  not convert them. If CMDB / Cloud Deployer leftovers remain, ask the user whether to remove
  them or leave them for a separate No-CMDB migration.
- Transfer mode: use CLI under [cli/](cli/). Install with `pip install -e ./cli` (add
  `[decrypt]` for Fernet).

## Script and CLI layout

| Piece | Path |
|-------|------|
| Template scripts | [scripts/template/](scripts/template/) |
| Instance scripts | [scripts/instance/](scripts/instance/) |
| Shared helpers | [scripts/shared/extcreds_mig/](scripts/shared/extcreds_mig/) |
| Migration CLI | [cli/](cli/) |

Run Template / Instance scripts with `--repo` pointing at the user repository. Run CLI from this
pack so the tool stays inside the package. Qualify scripts as `scripts/template/...` or
`scripts/instance/...` - never a bare `scripts/<name>.py`.

## Reports

Follow the report format for your mode: [references/template/report-format.md](references/template/report-format.md) or [references/instance/report-format.md](references/instance/report-format.md).

- Paths only. No YAML dumps of secrets. No full script JSON in chat.
- Compact inventory: batch default proposals; full table only for ask/review rows.
- Number decision questions. Put the recommended option first.

## Examples

**Template cutover:** user says "migrate template demo-b2b to external creds" → mode `template` →
preflight → inventory → confirm decisions → draft → register descriptor → replace macros →
validate. Hand back publish step.

**Instance cutover:** user says "migrate instance test env cluster/env-a" → mode `instance` →
preflight → inventory → classify/confirm → secret-store if needed → convert passport/shared/system
→ parameters → cleanup → validate. Hand back pipeline step.

**Transfer (Git values):** user says "collect secrets before instance cutover" → mode `transfer` →
`migration-cli collect` to a temp path. Never commit the output. Later `fill` +
`external-cred-provision` after Effective Set `skip`.

## After the mode ends

Hand back to the user with the next overview step. Do not start the next mode unless they ask.
