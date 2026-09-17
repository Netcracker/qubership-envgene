# qubership-cred-migration

Migrates EnvGene template and instance repositories from local credentials to external
credentials backed by a Secret Store. Two console commands are installed.

## Install

```bash
pip install -e .
```

## Commands

### `envgene-migrate`

```bash
envgene-migrate plan --repo=<instance|template>
envgene-migrate apply --repo=<instance|template> [--dry-run]
```

Run from the repository root. `plan` writes `migration-plan.yaml`. Operator reviews / edits.
`apply` invokes `external-cred-provision` for Store writes and rewrites Git.

### `envgene-external-context-generator`

```bash
# From the repo root (defaults: --plan=migration-plan.yaml --repo=.):
envgene-external-context-generator [--out <path>]

# Or with explicit paths:
envgene-external-context-generator --plan <migration-plan.yaml> --repo <repo-root> [--out <path>]
```

Reads the migration plan + repository and emits the CLI-context YAML that `external-cred-provision`
consumes. `envgene-migrate apply` invokes this internally; the standalone form is available for
debug / one-off runs.

Expected repository state: `envgene-migrate plan` already run (`migration-plan.yaml` present),
Secret Store configured (`configuration/secret-stores.yml` present), source cred files still
contain `data` (apply's Git rewrites not yet applied - so anywhere between `plan` and `apply`).

The emitted YAML contains **one entry per unique cred-id across the entire plan**, batched into
a single file (external-cred-provision consumes one context per invocation). Skipped creds
(envgeneNullValue placeholders) are warned on stderr; missing or malformed inputs exit with
code 2.

## Design

See `docs/analysis/cred-migration-flow.md` in the qubership-envgene repository.

## Development

```bash
pip install -e ".[dev]"
pytest
```
