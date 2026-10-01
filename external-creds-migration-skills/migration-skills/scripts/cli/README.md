# migration-cli

Local helper for EnvGene External Credentials migration.

Commands:

1. `collect` - read actual passwords and tokens from local Credentials in an Instance Repository and write one tiered values file for the whole repository (passport / shared / env — **not** system).
2. `collect-system` - read `configuration/credentials/`, write an **external-cred-provision** context under `global` (no fill).
3. `export-credentials` - fetch passwords and tokens from Jenkins CM API + Script Console into YAML for `fill`.
4. `fill` - match values (Instance-scoped file or local Jenkins export) into an External Credential Context for `external-cred-provision`.
   Only Context entries with `strategy: fail_if_absent` are filled and written.
   Entries with `create_if_absent` are skipped (EnvGene / provision generates them).
   Not used after `collect-system`.

`collect`, `collect-system`, and `fill` do not call Jenkins. `collect-system` does not call the Secret Store; run `external-cred-provision` on its output. `export-credentials` calls Jenkins only.

`collect` and `fill` do not call Jenkins or Secret Store. `export-credentials` calls Jenkins only.
System credentials under `configuration/credentials/` are out of scope.

## Install

```bash
cd external-creds-migration-skills/cli
pip install -e .
pip install -e ".[decrypt]"   # Fernet field-level decryption
```

## Tests

Not shipped in this kit. Use the CLI against a real Instance repo when validating.

## Collect output shape

One YAML file for the whole Instance Repository. Cluster and shared credentials are stored once, not duplicated per environment:

```yaml
clusters:
  acme-cluster:
    cloud:
      credentials:
        passport-creds: {type: usernamePassword, username: "...", password: "..."}
    shared:
      credentials:
        shared-client-token: {type: secret, secret: "..."}
    environments:
      env-dev:
        credentials:
          ID_ENV_ONLY: {type: usernamePassword, username: "...", password: "..."}
```

Discovery follows `env_definition.yml` bindings (`inventory.cloudPassport`, `envTemplate.sharedMasterCredentialFiles`) plus files under `Inventory/credentials/` for each environment.

## Encrypted credentials

Credentials may be encrypted in the Instance Repository in two ways:

| Encryption | How to detect | What you need |
|------------|---------------|---------------|
| Fernet (field-level) | Values start with `[encrypted:AES256_Fernet]` | `SECRET_KEY` env var or `--secret-key` |
| SOPS (whole file) | File ends with a `sops:` block | `sops` CLI on PATH and `SOPS_AGE_KEY` or `ENVGENE_AGE_PRIVATE_KEY` |

`collect` decrypts in memory only. It does not write decrypted passwords or tokens back into the Instance Repository.

If encrypted content is found but no key is available, `collect` exits with an error naming the file and the required variable.

## Export credentials from Jenkins

Port of the GitLab CMDB export pipeline. Two steps:

1. CM API — list credential ids and types for a tenant.
2. Jenkins Script Console — fetch password/token values per id.

Output matches the Jenkins export format expected by `fill --values-format jenkins_export`.

### Single tenant

Default Jenkins URL (`https://jenkins.example.com`) uses `CLOUD_USERNAME` and `CLOUD_TOKEN`
from the environment. Pass `--jenkins-url` for your real Jenkins host.

```bash
export CLOUD_USERNAME='your-user'
export CLOUD_TOKEN='your-token'

migration-cli export-credentials \
  --tenant DEMO \
  --out-dir ./cmdb-export-credentials
```

A non-default Jenkins URL uses `JENKINS_USERNAME` and `JENKINS_TOKEN` (or `--username` /
`--token`):

```bash
migration-cli export-credentials \
  --tenant DEMO \
  --jenkins-url https://jenkins.my-company.example \
  --username my-user \
  --token "$JENKINS_TOKEN" \
  --insecure \
  --out-dir ./cmdb-export-credentials \
  --out-file shared-credentials.yml
```

### Multiple tenants (CLI)

Repeat `--tenant` or comma-separate in one flag. Each tenant writes `{tenant}-shared-credentials.yml` into `--out-dir`:

```bash
migration-cli export-credentials \
  --tenant DEMO \
  --tenant ACME \
  --out-dir ./cmdb-export-credentials
```

```bash
migration-cli export-credentials \
  --tenant DEMO,ACME,OTHER \
  --out-dir ./cmdb-export-credentials
```

Do not pass `--out-file` with multiple tenants. Use `--config` when tenants need different Jenkins URLs or credentials.

### Multi-tenant config

```yaml
# export-config.yml
exports:
  - tenant: DEMO
    out_file: DEMO-shared-credentials.yml
  - tenant: ACME
    jenkins_url: https://jenkins.acme.example
    out_file: ACME-shared-credentials.yml
    username: acme-user
    token_env: JENKINS_TOKEN_ACME
```

```bash
migration-cli export-credentials \
  --config export-config.yml \
  --out-dir ./cmdb-export-credentials
```

### Debug flags

```bash
  --dry-run    # list ids from CM API only
  --limit 10   # fetch at most 10 credentials
  --log-level DEBUG export-credentials ...
```

Then pass the export directory to `fill`:

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values-dir ./cmdb-export-credentials \
  --values-format jenkins_export \
  --out /tmp/filled-all-environments.yaml
```

## Collect system (provision context, no fill)

First step for Instance migration when system tokens must exist in the Store before ES.

```bash
migration-cli collect-system \
  --instance-root /path/to/instance-repo \
  --out /tmp/system-provision-context.yml

external-cred-provision /tmp/system-provision-context.yml
```

Requires `configuration/secret-stores.yml` (`default_store`) and `configuration/credentials/`.
Default strategy in the context is `overwrite`. Do not commit the output file.

## Collect

`collect` walks every environment bound in `env_definition.yml` unless you pass `--env-filter`.
Filtered runs still include cloud passport and shared files referenced by those environments.

### Whole repository

```bash
migration-cli collect \
  --instance-root /path/to/instance-repo \
  --out /tmp/cred-values.yaml
```

### Selected environments

```bash
migration-cli collect \
  --instance-root /path/to/instance-repo \
  --out /tmp/cred-values-pilot.yaml \
  --env-filter acme-cluster/env-dev,acme-cluster/env-qa
```

Keys are `cluster/env` (same shape as `FULL_ENV_NAME`). Comma-separated, no spaces required.

### Fernet-encrypted fields

```bash
export SECRET_KEY='your-fernet-key'
migration-cli collect \
  --instance-root /path/to/instance-repo \
  --out /tmp/cred-values.yaml
```

Or pass `--secret-key` instead of the env var. SOPS whole-file encryption needs `sops` on PATH plus
`SOPS_AGE_KEY` or `ENVGENE_AGE_PRIVATE_KEY`.

## Fill

`fill` only seeds Context entries with `strategy: fail_if_absent`. Entries already
`create_if_absent` are skipped (EnvGene / provision generates them).

On match, `fill` writes `data` and rewrites `strategy` to `--seed-strategy` (default
`create_if_absent`) so the file is ready for `external-cred-provision`.

Use either:

- `--repo-root` - scan every Context under `environments/*/.../external-credential/`
- `--context` - one environment's Context file

Do not pass both. Provide `--values` or `--values-dir` (not both).

### Output shape (flat provision input)

`--repo-root` writes **one** YAML file with a top-level `credentials` map. Keys are
`{cluster}/{env}/{credId}`. The format matches
[external-cred-provision](/docs/features/external-creds-provisioning-cli.md) input:

```yaml
credentials:
  acme-cluster/env-dev/app-api-secret:
    vals: ref+gcpsecrets://example-gcp-project/acme-cluster--env-dev--app-api-secret
    strategy: create_if_absent
    data:
      value: example-secret-value
  acme-cluster/env-b/cloud-deploy-sa-token:
    vals: ref+gcpsecrets://project/acme-cluster--cloud-deploy-sa-token
    strategy: create_if_absent
    data:
      value: "..."
```

Each entry keeps `vals` from the Effective Set Context. Provision writes to the path in `vals`,
not the map key.

### Whole repository from collect

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values /tmp/cred-values.yaml \
  --values-format instance_scoped \
  --out /tmp/filled-all-environments.yaml
```

`instance_scoped` lookup order: environment -> shared -> cloud -> repository.shared ->
cross-cluster shared.

### Selected environments from collect

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values /tmp/cred-values.yaml \
  --values-format instance_scoped \
  --env-filter acme-cluster/env-dev,acme-cluster/env-qa \
  --out /tmp/filled-pilot.yaml
```

### Whole repository from Jenkins export directory

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values-dir ./cmdb-export-credentials \
  --values-format jenkins_export \
  --out /tmp/filled-all-environments.yaml \
  --continue-on-error
```

With `--values-dir`, `--tenant` and `--cloud` are optional. The CLI falls back to suffix match on
`*-{credId}` across all export files.

### Selected environments from Jenkins exports

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values-dir ./cmdb-export-credentials \
  --values-format jenkins_export \
  --env-filter acme-cluster/env-dev \
  --out /tmp/filled-pilot.yaml \
  --continue-on-error
```

### One environment (`--context`) from collect

```bash
migration-cli fill \
  --context /path/to/environments/acme-cluster/env-dev/effective-set/external-credential/external-credentials.yaml \
  --values /tmp/cred-values.yaml \
  --values-format instance_scoped \
  --out /tmp/filled-env-dev.yaml
```

### One environment (`--context`) from a single Jenkins export file

Jenkins match order for each `fail_if_absent` credId:

1. `{tenant}-{cloud}-{env}-{credId}` (env folder from Context path)
2. `{tenant}-{cloud}-{cluster}-{credId}` (cluster folder fallback)
3. any `{tenant}-{cloud}-*-{credId}` in the export (CMDB/env segment unknown)

The CLI logs which level matched (`env-level`, `cluster-level`, or `suffix-level`).

```bash
migration-cli fill \
  --context /path/to/environments/acme-cluster/env-dev/effective-set/external-credential/external-credentials.yaml \
  --values /path/to/jenkins-export.yml \
  --values-format jenkins_export \
  --tenant demo \
  --cloud cloud \
  --out /tmp/filled-env-dev.yaml
```

### Partial fill (some ids unmatched)

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values /tmp/cred-values.yaml \
  --values-format instance_scoped \
  --out /tmp/filled-partial.yaml \
  --partial \
  --report /tmp/unmatched.yaml
```

`--partial` writes every matched `fail_if_absent` credential even when some ids miss. Unmatched
ids go to `--report` (default `<out>-unmatched.yaml`). Exit code stays non-zero so provision is
not treated as complete.

### Overwrite strategy in the filled file

Default `--seed-strategy create_if_absent` does not clobber an existing Store secret on provision.
Use `overwrite` only when you intend to replace Store values:

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values /tmp/cred-values.yaml \
  --values-format instance_scoped \
  --seed-strategy overwrite \
  --out /tmp/filled-overwrite.yaml
```

## Provision

```bash
external-cred-provision /tmp/filled-all-environments.yaml
```
