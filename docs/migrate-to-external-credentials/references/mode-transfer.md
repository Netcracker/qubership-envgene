# Mode: transfer

Move actual passwords and tokens into the Secret Store during migration. Use
[migration-cli](../cli/README.md) in this pack and `external-cred-provision`. YAML cutover stays
in [mode-template.md](mode-template.md) and [mode-instance.md](mode-instance.md).

Entry skill: [../SKILL.md](../SKILL.md). Overview: [overview.md](overview.md).

Obey entry skill **Hard constraints**. Do not commit collect / export / fill outputs. Never print
secret values.

## Checkpoints and resuming

Each command below is a single file write to an explicit `--out` (or `--out-dir`) path. Nothing is
committed and nothing chains automatically - the agent runs one command, reports the result, and
waits before moving to the next.

- **Safe to re-run.** `collect`, `export-credentials`, and `fill` overwrite their own output path;
  re-running the same command after an interruption just regenerates it. `fill --seed-strategy
  create_if_absent` (the default) will not clobber values a previous `fill` run already wrote.
- **Resuming a stopped session.** If a transfer session stops partway (error, closed chat,
  `NEEDS_INPUT`), resume by re-running the last command with the same `--out` path - there is no
  separate state file to restore.
- **Where the agent stops on its own:** after any command that fails, exits `NEEDS_INPUT` (`--partial`
  with unmatched entries), or would otherwise have to print a secret value.
- **Where the agent asks first:** before `external-cred-provision`. `collect` / `export-credentials`
  / `fill` only produce local files; provisioning writes real secret values into the Secret Store, so
  the agent shows the command and confirms before running it.

## When to run which command

| Source of passwords and tokens | Command | When |
|--------------------------------|---------|------|
| Still in Instance Credential files (encrypted or plain) | `collect` | Before Instance YAML cutover |
| In Jenkins CMDB / Cloud Deployer | `export-credentials` | After Context exists (`skip` ES run) |
| Match into Context for provision | `fill` | After Context + values file/dir exist |

Follow [overview Flow](overview.md#flow):

- **Values in the Instance Repository:** run `collect` **before** Instance YAML cutover, then after
  Effective Set with `EXTERNAL_CREDENTIAL_PROVISIONING=skip`, run `fill` and
  `external-cred-provision`.
- **Values in Jenkins:** skip `collect`. After Effective Set with `skip`, run
  `export-credentials`, then `fill` and `external-cred-provision`.

`fill` writes those values into Context entries with `strategy: fail_if_absent`.
`create_if_absent` entries are skipped by `fill` - EnvGene / provision generates them.

Do not commit collect / export / fill outputs to Git. Never print secret values in chat.

## Install

```bash
cd docs/migrate-to-external-credentials/cli
pip install -e .
pip install -e ".[decrypt]"   # Fernet field-level decryption
```

Full command reference: [cli/README.md](../cli/README.md).

## Fast-start config

Optional - skip this if you're comfortable passing `--instance-root`, `--tenant`, etc. by hand.

Copy [`transfer-config.example.yml`](../transfer-config.example.yml) to `transfer-config.yml` and
fill in the paths for this migration. **The agent reads this file, not `migration-cli`** - `collect`
and `fill` take flags only and have no `--config` option. `export-credentials` has its own `--config`
for multi-tenant Jenkins export jobs (see [cli/README.md](../cli/README.md)); that is a different
file with a different shape, not this one.

Point the agent at `transfer-config.yml` and it builds the right command - `collect`,
`export-credentials`, or `fill` - from the fields below and shows the exact command before running
it. Do not commit `transfer-config.yml`: it names where secrets live, even though it holds no secret
values itself.

```yaml
instance_repo_path: /path/to/instance-repo
values_source: instance   # or: jenkins
env_filter: cluster/env1,cluster/env2
```

## Collect from the Instance Repository

```bash
export SECRET_KEY='...'   # if Fernet-encrypted fields
migration-cli collect \
  --instance-root /path/to/instance-repo \
  --out /tmp/cred-values.yaml
```

Optional: `--env-filter cluster/env1,cluster/env2`.

`collect` ignores `type: external` entries. Run it while Credentials are still local.

## Export from Jenkins

```bash
export CLOUD_USERNAME='...'
export CLOUD_TOKEN='...'
migration-cli export-credentials \
  --tenant TENANT \
  --out-dir ./cmdb-export-credentials
```

## Fill External Credential Context

From collect output (whole repo Context scan):

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values /tmp/cred-values.yaml \
  --values-format instance_scoped \
  --out /tmp/filled-all-environments.yaml
```

From Jenkins exports:

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values-dir ./cmdb-export-credentials \
  --values-format jenkins_export \
  --out /tmp/filled-all-environments.yaml \
  --continue-on-error
```

## Provision into the Secret Store

```bash
external-cred-provision /tmp/filled-all-environments.yaml
```

Configure store auth env vars as in the
[provisioning CLI](/docs/features/external-creds-provisioning-cli.md#environment-variables).

Then the user re-runs the Instance pipeline with `EXTERNAL_CREDENTIAL_PROVISIONING=apply`
(default). Agent does not run the pipeline.
