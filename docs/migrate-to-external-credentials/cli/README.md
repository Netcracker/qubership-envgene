# migration-cli

Local helper for EnvGene External Credentials migration.

Commands:

1. `collect` - read actual passwords and tokens from local Credentials in an Instance Repository and write one tiered values file for the whole repository.
2. `export-credentials` - fetch passwords and tokens from Jenkins CM API + Script Console into YAML for `fill`.
3. `fill` - match values (Instance-scoped file or local Jenkins export) into an External Credential Context for `external-cred-provision`.
   Only Context entries with `strategy: fail_if_absent` are filled and written.
   Entries with `create_if_absent` are skipped (EnvGene / provision generates them).

`collect` and `fill` do not call Jenkins or Secret Store. `export-credentials` calls Jenkins only.
System credentials under `configuration/credentials/` are out of scope.

## Install

```bash
cd docs/migrate-to-external-credentials/cli
pip install -e .
pip install -e ".[decrypt]"   # Fernet field-level decryption
```

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

## Collect

```bash
migration-cli collect \
  --instance-root /path/to/instance-repo \
  --out /tmp/cred-values.yaml
```

With Fernet encryption:

```bash
export SECRET_KEY='your-fernet-key'
migration-cli collect --instance-root /path/to/instance-repo --out /tmp/cred-values.yaml
```

Optional environment filter:

```bash
migration-cli collect \
  --instance-root /path/to/instance-repo \
  --out /tmp/cred-values.yaml \
  --env-filter acme-cluster/env-dev,acme-cluster/env-qa
```

## Fill entire repository (flat output for provision)

Scan all `external-credentials.yaml` files under `environments/` and write **one** YAML file with a top-level
`credentials` map. Keys are `{cluster}/{env}/{credId}` so the same credId in different environments stays unique.
The format matches [external-cred-provision](/docs/features/external-creds-provisioning-cli.md) input.

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

Each entry keeps `vals` from the Effective Set Context for that environment. Actual passwords and tokens
come from collect or Jenkins lookup. Provision writes to the path in `vals`, not the map key.

From collect output:

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values /tmp/cred-values.yaml \
  --values-format instance_scoped \
  --out /tmp/filled-all-environments.yaml
```

From a directory of Jenkins exports (multiple tenant files):

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values-dir /path/to/jenkins-exports \
  --values-format jenkins_export \
  --out /tmp/filled-all-environments.yaml \
  --continue-on-error
```

With `--values-dir`, `--tenant` and `--cloud` are optional. The CLI falls back to suffix match on `*-{credId}` across all export files.

Optional filters:

```bash
  --env-filter acme-cluster/env-b,acme-cluster-b/env-qa
  --continue-on-error
  --partial
  --report /tmp/unmatched.yaml
```

`--partial` writes every matched `fail_if_absent` credential even when some ids miss.
Unmatched ids go to `--report` (default `<out>-unmatched.yaml`). Exit code stays non-zero so
provision is not treated as complete.

## Fill one environment (flat output)

## Fill from Jenkins export file on disk

Jenkins match order for each `fail_if_absent` credId:

1. `{tenant}-{cloud}-{env}-{credId}` (env folder from Context path)
2. `{tenant}-{cloud}-{cluster}-{credId}` (cluster folder fallback)
3. any `{tenant}-{cloud}-*-{credId}` in the export (CMDB/env segment unknown)

The CLI logs which level matched (`env-level`, `cluster-level`, or `suffix-level`).

```bash
migration-cli fill \
  --context /path/to/environments/cluster/env/effective-set/external-credential/external-credentials.yaml \
  --values /path/to/jenkins-export.yml \
  --values-format jenkins_export \
  --tenant demo \
  --cloud cloud \
  --out /tmp/filled-context.yaml
```

## Fill from collect output

For `instance_scoped`, lookup order is: environment -> shared -> cloud -> repository.shared -> cross-cluster shared.

Then:

```bash
external-cred-provision /tmp/filled-all-environments.yaml
```
