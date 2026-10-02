# Commands — External Credentials migration

Canonical command reference for this kit. Mode files are checklists only — they
link here instead of repeating install blocks.

## Prerequisites

- **Python 3.12.x** for kit CLIs (`migration-cli`, `external-cred-provision`).
  Check with `python --version` before install. Other majors (3.11 / 3.13 / 3.14…)
  are unsupported — use a 3.12 venv if needed. The skill does **not** install or
  upgrade Python for you; fix the environment, then continue.
- Kit Python on `PYTHONPATH` (YAML migrate)
- Optional: `pip install -e <qubership-envgene>/modules/envgene` (crypt / YAML helpers)
- `external-cred-provision` on PATH — install from this skill (see Set up)
- SOPS repos: `SOPS_AGE_KEY` (never commit)
- Fernet collect: `SECRET_KEY` + `pip install -e <kit>/scripts/cli"[decrypt]"`
- Do not pass `--manual` on `envgene_migrate`. That flag is for a person running
  the CLI without this skill. It hides Questions and Reply. The skill uses the
  default output.

## Set up

```powershell
# must print 3.12.x — stop and use a 3.12 interpreter/venv if not
python --version
$KIT = "<path-to>/external-creds-migration-skills/migration-skills"
$env:PYTHONPATH = "$KIT\scripts\python"
cd "$KIT\scripts\cli"; pip install -e .; pip install -e ".[decrypt]"
cd "$KIT\scripts\external-cred-provision"; pip install -e .
```

```bash
# must print 3.12.x — stop and use a 3.12 interpreter/venv if not
python --version
export PYTHONPATH="<path-to>/external-creds-migration-skills/migration-skills/scripts/python"
cd "$KIT/scripts/cli" && pip install -e . && pip install -e ".[decrypt]"   # transfer CLI
cd "$KIT/scripts/external-cred-provision" && pip install -e .             # Store writes
```

Write `migration-plan.yaml` under `--root` (the Template or Instance repository
root). Plan, apply, and strip-technical-macros all read and write that same path.

## System credentials first (before Instance YAML apply)

Reads `configuration/credentials/`, builds a provision context under path `global`
from `default_store`. **No fill step.**

**Skill must ask** the operator for `--out`: an absolute path where to write the
context file. Prefer outside the instance Git checkout. Do not invent the path.

```bash
migration-cli collect-system \
  --instance-root /path/to/instance-repo \
  --out /path/outside-repo/system-provision-context.yml
# optional: --strategy create_if_absent  (default: overwrite)

external-cred-provision /path/outside-repo/system-provision-context.yml
```

Do not commit the `--out` file. Then continue with Template / Instance
`envgene_migrate` (system entries keep `writeToStore: false` in the plan).

## When to write the Secret Store (pick one path)

| Situation | Use | Do not also |
|-----------|-----|-------------|
| **System** creds at start of migration | `migration-cli collect-system` → `external-cred-provision` | Do not use fill; do not rely on Instance apply Store write for system |
| Values in Git (default happy path after Welcome) | I0 collect-system → provision; then `migration-cli collect` (values file outside repo) → Instance apply **Git only** (`writeToStore: false` for non-system) → ES/env-gen with `EXTERNAL_CREDENTIAL_PROVISIONING=skip` → `fill` → `external-cred-provision` | Do not ask writeToStore before I4; do not re-collect from Git after I4 as the default |
| Values still in Instance Git; operator **explicitly** wants Store filled **during** YAML cutover (non-system) | `envgene_migrate apply --repo=instance` (`writeToStore: true`) | Skip transfer fill/provision for the same creds |
| Values only in Jenkins | ES/env-gen with `EXTERNAL_CREDENTIAL_PROVISIONING=skip` → `export-credentials` → `fill` → `external-cred-provision`; later pipeline may use `apply` (default) | Skip `collect`; do not also `writeToStore: true` for the same creds |
| Template phase | Never write Store | — |

Default happy path when values are in **Git**:  
**System (I0) → Template YAML → Instance plan/review → collect → I4 Git-only → Transfer skip/fill/provision → Template version check → I5–I7.**

**CI/CD vs local auth:** CI/CD variables on the Instance repo → reply **`done`**.  
Store auth on **this machine** before local I0 provision → reply **`ready`**.  
Same env var names; two places. See mode-instance Local auth.

## Store auth env vars (Instance apply or provision)

| Store type | Required env vars |
|------------|-------------------|
| Vault / OpenBao | `VAULT_ADDR`, `VAULT_TOKEN` |
| GCP | `GOOGLE_APPLICATION_CREDENTIALS` |
| AWS | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |
| Azure | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |

One `default_store` in `configuration/secret-stores.yml` only.

**TLS / certificates (Vault, OpenBao, and other HTTPS stores):** private or
corporate CA can cause certificate verify errors on Store calls. Fix trust
(`SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` when applicable); public CA usually needs
nothing extra. Do not skip TLS verification unless your security team explicitly
allows it. Do not invent cert paths or disable verify silently.

Ask the operator only for fields EnvGene uses (plus auth **env vars**, never
tokens in Git):

| type | YAML fields | Connection / auth (env) |
|------|-------------|-------------------------|
| vault / OpenBao | `mountPath` | `VAULT_ADDR`, `VAULT_TOKEN` |
| gcp | `projectId` | `GOOGLE_APPLICATION_CREDENTIALS` |
| aws | `region` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |
| azure | `vaultName` | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |

Do **not** ask for Store `url` as the server address. `url` in YAML is optional
and unused for Vault/GCP VALS and connection (Vault host is `VAULT_ADDR`).

Create the file via Python (skill collects type + fields above — no tokens in Git):

```bash
PYTHONPATH=external-creds-migration-skills/migration-skills/scripts/python python -c "
from pathlib import Path
import json, sys
from envgene_migrate.secret_store import write_secret_stores
spec = json.loads(sys.stdin.read())
print(json.dumps(write_secret_stores(Path('/path/to/instance-repo'), spec)))
"
```

Example stdin (Vault): `{\"type\":\"vault\",\"mountPath\":\"secret\"}`  
Example stdin (GCP): `{\"type\":\"gcp\",\"projectId\":\"my-gcp-project\"}`

## Template phase

```bash
python -m envgene_migrate plan  --repo=template --root /path/to/template-repo
python -m envgene_migrate apply --repo=template --root /path/to/template-repo
```

If GATE STOP on `runtime_credential_macros` and the operator chooses **B**:

```bash
# optional: --dry-run first
python -m envgene_migrate strip-technical-macros \
  --repo=template --root /path/to/template-repo
# then re-plan
python -m envgene_migrate plan --repo=template --root /path/to/template-repo
```

`strip-technical-macros` is **Template-only** (reads hits from `migration-plan.yaml`).
It removes credential macros under `technicalConfigurationParameters` / technical
paramsets; it does **not** rewrite them to credRef. Do not use on Instance.

Then publish a template version from the migration branch. Do not merge until
Instance succeeds.

## Check Template version (before Instance I5)

```bash
python -m envgene_migrate check-template-version \
  --repo=instance --root /path/to/instance-repo \
  --expect <published-template-artifact>
```

Compares `envTemplate.artifact` in every `environments/**/Inventory/env_definition.yml`
to `--expect`. Exit 0 on match; otherwise lists mismatches. Operator edits files;
agent does not.

## Instance phase

```bash
# Whole repository (default)
python -m envgene_migrate plan  --repo=instance --root /path/to/instance-repo
# One env only (debug) — only when the operator explicitly asks:
# python -m envgene_migrate plan --repo=instance --root /path/to/instance-repo --env CLUSTER/ENV

# edit migration-plan.yaml to_review (commit of plan file is optional)
python -m envgene_migrate apply --repo=instance --root /path/to/instance-repo
# optional: --dry-run (Store dry-run; no Git writes)
# optional: --verbose (per-cred stderr; default is summary only)
```

Apply aborts on dirty tracked Git files (exit 3), Cyrillic credential paths,
or mixed local+external types in one source file (exit 2).

System credentials: `create: false`, `remoteRefPath: global`, and
`writeToStore: false` after I0 (`collect-system`). Set `writeToStore: true` only
if system was not provisioned yet.

Then: env-gen (I5), deploy (I6), merge Template then Instance (I7).  
Ensure Store (including system) is populated **before** Effective Set / env-gen.

Instance apply with `writeToStore: true` builds the same provision context shape as
`collect-system` (`vals` / `strategy` / `data`) and runs
`external-cred-provision <temp-file>` (product CLI).

## Transfer (optional)

Jenkins / Context fill: operator runs env-gen/ES with
`EXTERNAL_CREDENTIAL_PROVISIONING=skip` first (Context only). Then
export or collect → fill → provision. Next normal run: `apply` (default).
If the pipeline parameter is missing, stop — see
[mode-transfer.md](references/mode-transfer.md).

```bash
migration-cli collect --instance-root /path/to/instance-repo --out values.yml
migration-cli export-credentials ...    # Jenkins — see scripts/cli/README.md
migration-cli fill ...                  # see scripts/cli/README.md
# then external-cred-provision — confirm before running
```

Full flags and examples: [scripts/cli/README.md](scripts/cli/README.md).  
Agent checklist: [references/mode-transfer.md](references/mode-transfer.md).

Do not commit collect / export / fill outputs.

## Artifacts

| Artifact | Writer |
|----------|--------|
| `migration-plan.yaml` | `envgene_migrate plan` (editable) |
| plan/migration reports | stdout from plan/apply |
| collect / export / fill YAML | `migration-cli` (local only) |

## Rollback

Git restore to pre-migration. No separate rollback CLI.
