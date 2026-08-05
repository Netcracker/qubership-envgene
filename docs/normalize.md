---
description: Normalize EnvGene parameters produced by the CMDB lift-and-shift migration tool. Runs a 5-phase procedure on Phase 1 migration output — discovery, inventory, classification, rule checks, and output generation. Rules sourced from configuration-standard.md.
---

# Skill: normalize

## What this skill does

Runs a 5-phase normalization procedure on the Phase 1 migration output for one or more
environments. Every change is traceable to a rule ID from `docs/configuration-standard.md`.

All output goes to `output-normalised/` — the Phase 1 `output/` directory is never modified.
The skill runs to completion without asking for input. All decisions are made automatically
using the rules below and recorded in the normalisation log and report.

**Rules applied by this skill:**

| Area | Rules included | Rules excluded |
|------|---------------|----------------|
| PLACE | 1, 2, 3, 4, 5, 6 | 7, 8 |
| SEC | 1, 2, 3, 4, 5 | — |
| INT | 1, 2, 3, 4, 5, 6 | — |
| NAME | 2, 5, 7 | 1, 3, 4, 6 |
| VAL | 1, 2, 3, 4, 5 | — |
| TPL | — | all |

---

## Phase 1 — Discovery

Read `config.yml` and build a mapping table:

| `<cluster>/<env>` | `cmdbTenantName` | `cmdbCloudName` | `cmdbNamespaceNames` |
|--------------------|------------------|-----------------|----------------------|

For each row confirm the following files exist before continuing:

**Phase 1 output (required):**
- `output/environments/<cluster>/cloud-passport/<cluster>.yml`
- `output/environments/<cluster>/cloud-passport/<cluster>-creds.yml`
- `output/environments/<cluster>/<env>/Inventory/env_definition.yml`
- `output/environments/<cluster>/<env>/Inventory/parameters/*.yml` (at least one)

If any required file is missing, report it as a blocker and stop. Do not proceed to Phase 2
until all files are confirmed present.

---

## Phase 2 — Parameter inventory

Build a complete inventory of every parameter across all input files. For each parameter record:

| Field | What to capture |
|-------|-----------------|
| `key` | The parameter key as found in the file |
| `value` | The raw value |
| `source_file` | Full path of the file |
| `param_type` | `deploy`, `e2e`, or `technical` (from which category section it sits under) |
| `scope` | `env`, `cluster`, `site`, or `template` (from file path) |
| `value_type` | `string`, `boolean`, `url`, `ip`, `credential_candidate`, `empty`, or `multiline` |

Read from:
- Cloud Passport YAML and its `-creds.yml`
- All YAML files under `parameters/`
- `env_definition.yml`
- All YAML files under `resource_profiles/`
- All YAML files under `credentials/`

Complete the full inventory before running any rule checks — PLACE-1 and PLACE-2 require
cross-file and cross-environment comparison.

---

## Phase 3 — Classification

Classify each parameter using this decision order:

1. **Connectivity + secret** → `cloud-passport/<cluster>-creds.yml`
2. **Connectivity + non-secret** → `cloud-passport/<cluster>.yml`
   - Connectivity keys: `CLOUD_API_HOST`, `CLOUD_API_PORT`, `CLOUD_PROTOCOL`,
     `CLOUD_PRIVATE_HOST`, `CLOUD_PUBLIC_HOST`, `CLOUD_DASHBOARD_URL`,
     `CLOUD_DEPLOY_TOKEN`, `PRODUCTION_MODE`
   - Connectivity values: contains `api.k8s`, `:6443`, `maas-service`,
     `dbaas-aggregator`, `consul-server`, or `vault`
3. **Secret (non-connectivity)** → `Inventory/credentials/<product>-<purpose>-cred.yml`
   - Secret keys (case-insensitive): contain `PASSWORD`, `PASSWD`, `TOKEN`, `SECRET`,
     `KEY`, `CREDENTIAL`, `CERT`, `PRIVATE`, or `API_KEY`
   - Secret values: base64 string >40 chars, JWT (`eyJ…`), or value inside a
     `credentials:` section
4. **STV candidate** → record in the report as a limitation; classify as environment-level
   ParameterSet and continue — cannot auto-promote without knowing which templates consume it
5. **Same value across ALL environments of this topology** → template repo ParameterSet
6. **Same value across ALL environments on this cluster** → cluster-level ParameterSet
7. **Everything else** → environment-level ParameterSet

---

## Phase 4 — Rule checks and auto-apply

Apply every rule below in sequence. All findings are applied automatically. Every decision is
written to the normalisation log with its rule ID, file, key, and the action taken. No input
is requested at any point.

---

### SEC-1 — No plaintext secrets

Detect any key or value matching the secret patterns from Phase 3 (step 3). For each hit:

1. Determine the correct layer:
   - Value identical across all environments on the cluster → cluster-level:
     `output-normalised/environments/<cluster>/Inventory/credentials/<product>-<purpose>-cred.yml`
   - Value identical across all clusters in scope → environment-level (conservative default;
     record in report that template-level placement may be possible when more clusters are in scope)
   - Otherwise → environment-level:
     `output-normalised/environments/<cluster>/<env>/Inventory/credentials/<product>-<purpose>-cred.yml`

2. Derive the credential ID automatically:
   - Extract `<product>` from the key prefix before the first `_` (e.g. `DB_PASSWORD` → `db`)
   - Extract `<purpose>` from the remainder (e.g. `DB_PASSWORD` → `password` → normalise to
     `admin` for `PASSWORD`/`PASSWD`, `token` for `TOKEN`, `secret` for `SECRET`/`KEY`/`API_KEY`)
   - ID format: `<product>-<purpose>-cred` (e.g. `db-admin-cred`)
   - If the key has no `_` separator, use the full key lowercased as `<product>` and `secret`
     as `<purpose>`

3. Write a Credential stub with `envgeneNullValue` placeholder at the determined path.
4. Replace the plaintext value in the ParameterSet with `${creds.get("<id>").<field>}`.

---

### SEC-2 — No mixed plaintext and encrypted secrets

Scan for SOPS-encrypted credential files (files containing `sops:` metadata). If any exist
alongside credential files that hold real plaintext secret values, flag the repository state
in the report. Write all new credential stubs as plaintext with `envgeneNullValue` — do not
introduce SOPS encryption; record in the report that the repository owner must resolve the
mixed state.

---

### SEC-3 — No secrets in runtime parameters

Scan all `technicalConfigurationParameters` sections for keys matching the secret patterns.
For each hit, move the key and its (already-replaced) credential reference to
`deployParameters` in the same file. Record the move in the log.

---

### SEC-4 — Credential shape matches the secret

For each Credential object, inspect the declared `type` against its data:
- `usernamePassword` type with only one meaningful data field → change `type` to `secret`
  and flatten the data to a single `secret:` field
- `secret` type holding separate username and password fields → change `type` to
  `usernamePassword` and restructure the data block

Apply the correction and record it in the log.

---

### SEC-5 — Repository-wide encryption

Check whether any SOPS configuration (`.sops.yaml`) exists in the repository. If none exists
and new credential stubs are being written, add a note to the report recommending SOPS setup.
No file changes are made for this rule — it is informational only.

---

### PLACE-1 — Highest correct layer

When multiple environments are in scope, compare each parameter's value across all environments
on the same cluster:
- Value identical across every environment on the cluster → move the key to the cluster-level
  ParameterSet at `output-normalised/environments/<cluster>/parameters/` and remove it from
  each environment-level file
- Value identical across all clusters in scope → record in the report as a template-promotion
  candidate; leave at cluster level (conservative default)

If only one environment is in scope, skip this check and record the limitation in the report.

---

### PLACE-2 — Override only the delta

After PLACE-1 has run, scan environment-level files for any key that also appears at the
cluster level with the same value. Remove the redundant environment-level entry and record
the removal in the log.

---

### PLACE-3 — Place by system tier

Flag any parameter whose key or value pattern indicates it describes a platform or cluster
resource (e.g. monitoring URLs, Consul addresses, platform hosts) but is currently at the
environment level. Move it to the cluster-level ParameterSet and record the move in the log.

Platform indicators — key contains: `MONITORING`, `CONSUL`, `VAULT`, `MAAS`, `PLATFORM`,
`CLUSTER`, `DBAAS`; or value contains: `consul`, `vault`, `maas-service`, `dbaas-aggregator`.

---

### PLACE-4 — Contract keys in the Cloud Passport

Scan all ParameterSet files for keys beginning with `CLOUD_`. For each found outside a Cloud
Passport file, move it to
`output-normalised/environments/<cluster>/cloud-passport/<cluster>.yml` and remove it from
the ParameterSet. Record the move in the log.

---

### PLACE-5 — Right parameter category

Scan for parameters placed in the wrong category using these patterns:

- Keys suggesting pipeline use (`E2E_`, `LOGIN_URL`, `TEST_`, pipeline base URLs) found under
  `deployParameters` or `technicalConfigurationParameters` → move to `e2eParameters`
- Keys suggesting runtime configuration (`CACHE_TTL`, `REPLICA_COUNT`, `LOG_LEVEL`,
  `THREAD_POOL`, `TIMEOUT`, `MAX_CONNECTIONS`) found under `deployParameters` → move to
  `technicalConfigurationParameters`

Apply the move within the same file and record it in the log.

---

### PLACE-6 — Pipeline parameters bind to the Cloud

Inspect `env_definition.yml` for any `envSpecificE2EParamsets` entries keyed by a namespace
deploy-postfix instead of the reserved key `cloud`. Re-key the entry to `cloud` and record
the change in the log.

---

### INT-1 — Schema-valid

Check the structural shape of every EnvGene object:
- `*ParameterSets` fields must be lists — if a map is found, convert it to a list of the
  map's values and record the conversion
- Category bodies (`deployParameters`, `e2eParameters`, `technicalConfigurationParameters`)
  must be maps — if a list is found, record it in the report as unresolvable and leave it
  unchanged

---

### INT-2 — Every reference resolves

For every `${creds.get("<id>")}` expression and every `$type: credRef`, confirm a credential
with that ID exists on the resolution path. For every ParameterSet name in `env_definition.yml`,
confirm the file exists. Record every dangling reference in the report with its file and key.
Do not remove dangling references — flag them so the repository owner can supply the missing
object.

---

### INT-3 — One resolvable Cloud Passport

For each environment, resolve the Cloud Passport:
- If `inventory.cloudPassport: <name>` is set, count matching files named `<name>.yml` on the
  path. Zero matches or more than one match → record in the report as a blocker; do not modify
  `env_definition.yml`.
- If no `cloudPassport` field is set, check for `cloud-passport/<cluster>.yml` then
  `cloud-passport/passport.yml`. If neither exists, record in the report as a blocker.

---

### INT-4 — No shadowed same-name overrides

Check whether any ParameterSet, Credential, Shared Template Variable, or Resource Profile name
appears at more than one scope. For each duplicate, rename the lower-scope file to
`<original-name>-<env>` (for environment scope) or `<original-name>-<cluster>` (for cluster
scope) to make the name unique, update all references in `env_definition.yml` accordingly,
and record the rename in the log.

---

### INT-5 — No unreferenced entities

For each ParameterSet file under `parameters/`, confirm it is named in at least one reference
array. Check `env_definition.yml`, `deployer.yml`, `registry.yml`, and the Cloud Passport as
reference sites. Any file named by nothing is moved to
`output-normalised/_unreferenced/<original-path>` (not deleted) and recorded in the report
so the repository owner can decide whether to restore the reference or discard the file.

---

### INT-6 — No dead parameters

Flag parameters with no evidence of consumption. A parameter is a dead candidate when:
- Its key does not appear in any `.j2` template in the template repo
- Its key does not appear in any Helm `values.yaml` or `values.schema.json` in scope
- It is not a Cloud Passport contract key

Move dead candidates to a `_dead:` comment block at the bottom of their source file (commented
out, not deleted) and record them in the report. This preserves the values for review while
removing them from the active configuration. If no template repo or Helm schemas are available,
record the limitation and skip this check.

---

### NAME-2 — Filename equals `name` field

For every ParameterSet, Application Definition, Registry Definition, and Artifact Definition,
compare the filename (without `.yml`) to the `name:` field value. On a mismatch, correct the
`name:` field to match the filename and record the correction in the log.

---

### NAME-5 — Resource Profile Override naming

For every Resource Profile Override file, check the filename follows
`<baseline>-<subsystem>-override` with an optional `-<flavor>` suffix. Also verify the
`baseline:` field value matches the leading token in the filename. Record violations in the
report — do not rename files, as renaming breaks existing references; the repository owner
must update both the filename and all references together.

---

### NAME-7 — Shared Template Variable naming

For every file listed in a `sharedTemplateVariables` array, check the filename does not
contain an environment name, customer name, release version, or generic `-template-variables`
suffix. Record violations in the report — do not rename files for the same reason as NAME-5.

---

### VAL-1 — YAML type matches consumer

Scan for common type mismatches:
- Boolean values written as quoted strings (`"true"`, `"false"`, `"yes"`, `"no"`) → remove
  the quotes and apply the fix
- Version strings or codes that YAML would coerce to a number (`1.20`, country codes like
  `NO`, leading-zero numbers) not quoted → add quotes and apply the fix

Record every correction in the log.

---

### VAL-2 — Reserved-value semantics

Scan all parameter values for `envgeneNullValue`. If the key context suggests it is being used
to mean "empty" or "off" rather than "a lower layer must supply this", replace it with an
empty string and record the correction in the log with a note explaining the change.

---

### VAL-3 — URLs have no trailing slash

Scan all parameter values for strings matching a URL pattern that end with `/`. Strip the
trailing slash and apply the fix. Record every correction in the log.

---

### VAL-4 — Complex values are native YAML

Scan all parameter values for:
- Strings containing literal `\n` escape sequences → convert to a YAML block scalar (`|`)
- Strings that appear to be a JSON object or array (starting with `{` or `[`) → parse and
  convert to native YAML structure

Apply the conversion and record it in the log.

---

### VAL-5 — Resource quantities use unit form

In Resource Profile Override files, scan memory and CPU values for raw byte or bare number
values without a Kubernetes unit suffix. Apply the conversion:
- Values ≥ 1073741824 → convert to `Gi`
- Values ≥ 1048576 → convert to `Mi`
- Values ≥ 1024 → convert to `Ki`
- CPU values without `m` suffix → add `m`

Record every correction in the log.

---

## Phase 5 — Output generation

Write all changes to `output-normalised/` only. Never modify `output/` or the raw CMDB export.

Files to produce:

1. **Modified ParameterSet files** — all rule changes applied at the equivalent path under
   `output-normalised/`
2. **Credential stubs** — one file per detected secret at the layer-determined path
3. **Updated `env_definition.yml`** — references updated to reflect any layer promotions,
   renames, or category moves
4. **Unreferenced entity archive** — `output-normalised/_unreferenced/` for INT-5 removals
5. **Normalisation report** — `output-normalised/normalisation-report.md`
6. **Normalisation log** — `output-normalised/normalisation-log.yml`

### Normalisation report format

```markdown
# Normalisation report — <cluster>/<env> — <date>

## Summary

| Rule | Description | Findings | Applied |
|------|-------------|----------|---------|

## Changes applied

### SEC-1 — No plaintext secrets
...

## Limitations

### Rules skipped due to missing data
...

## Items requiring follow-up

### Dangling references (INT-2)
...
```

### Normalisation log format

```yaml
- rule: SEC-1
  file: environments/cluster-01/env-1/Inventory/parameters/env-bss-deploy.yml
  key: DB_PASSWORD
  action: replaced with credential reference
  credential_id: bss-admin-cred
  credential_path: environments/cluster-01/Inventory/credentials/bss-admin-cred.yml
  layer: cluster
  timestamp: <ISO-8601>

- rule: PLACE-1
  file: environments/cluster-01/env-1/Inventory/parameters/env-bss-deploy.yml
  key: MONITORING_URL
  action: moved to cluster layer
  destination: environments/cluster-01/parameters/cluster-bss-deploy.yml
  timestamp: <ISO-8601>
```

---

## Decision boundaries (quick reference)

All decisions are made automatically. Nothing waits for input.

| Rule | Check | Default action |
|------|-------|----------------|
| SEC-1 | Plaintext secret detected | Write credential stub; replace with reference |
| SEC-1 | Credential ID ambiguous | Derive from key name using `<product>-<purpose>-cred` pattern |
| SEC-1 | Layer ambiguous (single env) | Use environment-level as conservative default |
| SEC-2 | Mixed plaintext + encrypted | Record in report; leave encryption decision to repo owner |
| SEC-3 | Secret in runtime params | Move reference to `deployParameters` |
| SEC-4 | Credential shape mismatch | Correct the `type` field and restructure data block |
| SEC-5 | No SOPS config found | Add recommendation to report; no file changes |
| PLACE-1 | Cluster-promotion candidate | Move to cluster layer |
| PLACE-1 | Template-promotion candidate | Leave at cluster level; note in report |
| PLACE-1 | Single env in scope | Skip; record limitation |
| PLACE-2 | Redundant env-level key | Remove from env-level file |
| PLACE-3 | Platform param at env level | Move to cluster layer |
| PLACE-4 | CLOUD_ key in ParameterSet | Move to Cloud Passport |
| PLACE-5 | Wrong category | Move key to correct category section |
| PLACE-6 | E2E paramset not bound to Cloud | Re-key to `cloud` |
| INT-1 | *ParameterSets is a map | Convert to list |
| INT-1 | Category body is a list | Record in report; leave unchanged |
| INT-2 | Dangling reference | Record in report; do not remove |
| INT-3 | Cloud Passport not resolvable | Record as blocker in report |
| INT-4 | Shadowed same-name at two scopes | Rename lower-scope file; update references |
| INT-5 | Unreferenced entity | Move to `_unreferenced/`; record in report |
| INT-6 | Dead parameter candidate | Comment out in source file; record in report |
| INT-6 | No template repo or Helm schemas | Skip; record limitation |
| NAME-2 | Filename ≠ name field | Correct `name:` field to match filename |
| NAME-5 | RPO naming violation | Record in report; do not rename |
| NAME-7 | STV naming violation | Record in report; do not rename |
| VAL-1 | Boolean as quoted string | Remove quotes |
| VAL-1 | YAML-coerced value not quoted | Add quotes |
| VAL-2 | `envgeneNullValue` misused | Replace with empty string |
| VAL-3 | Trailing slash on URL | Strip trailing slash |
| VAL-4 | Escaped `\n` in value | Convert to block scalar |
| VAL-4 | JSON string value | Convert to native YAML |
| VAL-5 | Resource quantity without unit | Convert to Kubernetes unit form |

---

## Known limitations

These are recorded in the report when encountered. No input is requested — the skill continues.

1. **Single-environment scope** — PLACE-1 layer promotion requires multiple environments.
   Conservative default: leave all parameters at environment level.
2. **No template variable list** — STV classification (Phase 3, step 4) cannot be completed.
   Default: classify as environment-level ParameterSet.
3. **No Helm schema or template repo** — INT-6 dead parameter detection is skipped.
   VAL-1 type checks are best-effort based on value patterns only.
