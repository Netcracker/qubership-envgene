# envgene-linter: PLACE-3

File eligibility is governed by the later shared [connected-only contract](2026-09-11-connected-only-design.md).

This is the original three-check design. [PLACE-4](2026-09-07-place4-design.md) later replaced the ParameterSet-key checks; current PLACE-3 checks passport file placement only. The connected-only contract also excludes unselected passports from placement findings and from passport-derived catalogs. The original catalog and three-check sections below are historical; see the [current algorithm](../../algorithms/place3.md).

Date: 2026-09-04  
Status at design time: approved in conversation; awaiting file review\

## Goal

Terminology: **env** means environment; a **binding** is a reference from `env_definition.yml` to a ParameterSet; a **scope** is target × category, optionally separated by application. Effective Set is the merged parameter result; discovery indexes files and reads bindings.

`envgene-linter check <repo>` prints PLACE-1, then PLACE-2, then PLACE-3.

PLACE-3 (SHOULD): a Cloud Passport contract key lives at the **cluster** layer. An environment may override it with a different value. The passport **file** lives under that cluster's `cloud-passport/` (or `cloud-passports/`). Severity is warning. Exit codes stay as they are.

## In plain terms

Passport describes the platform and the physical cluster. That content is shared by every environment on the cluster. Copying it into each env, or into `environments/parameters/`, puts it on the wrong tier.

PLACE-1: “the same in every env — hoist it” (any key).  
PLACE-2: “the environment or cluster copied an inherited value — delete the copy.”\
PLACE-3: “this is a passport-tier key or file — it belongs on the cluster, unless this env genuinely changed the value.”

Bindings still come from `env_definition` (`envSpecific*` and `inventory.cloudPassport`). Unbound ParameterSets stay invisible to Effective Set, as today.

Passport values are **not** merged into the Effective Set this cycle.

## Out of scope (this cycle)

- Merging the passport into Effective Set projections
- PLACE-4 (“author the key in `passport.yml`, not in a ParameterSet”)
- Template layer, Jinja passport / Jinja ParameterSets (skip; stderr note)
- `--rules`, JSON/HTML, baseline, `[EXCEPTION …]`, autofix

## Code changes

Discovery must index passport files and read `inventory.cloudPassport`. Effective Set merge stays unchanged.

| File | Role |
| --- | --- |
| `discovery.py` | Index passport YAML; read `inventory.cloudPassport` on each env |
| `passport.py` (new) | Resolve one env's passport; build catalogs |
| `rules/place3.py` | The three checks |
| `rules/place1.py` | Do not hoist catalog keys |
| `engine.py` | Run PLACE-3 after PLACE-2 |
| `report.py` | Third block: `PLACE-3` |
| `tests/test_place3.py` | Synthetic cases |
| `testdata/place3/{ok,not-ok}/` | Lab trees |
| `docs/algorithms/place3.md` | Algorithm (English) |
| `docs/algorithms/ru/place3.md` | Same algorithm in Russian |

## Catalog (original design)

Two sources, unioned.

### EnvGene table (always on)

Closed list of Effective Set parameter names **and** the passport YAML keys that map to them, from `docs/features/cloud-passport-processing.md` on `feature/modern-toolset`. Include both sides when they differ (`MAAS_SERVICE_ADDRESS` and `MAAS_EXTERNAL_ROUTE`; `DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME` and `DBAAS_AGGREGATOR_USERNAME`; `VAULT_AUTH_ROLE_ID` and `VAULT_TOKEN`; `CLOUD_DEPLOY_TOKEN` even though it has no Effective Set parameter).

Include derived entries from the same table: `DBAAS_ENABLED`, `MAAS_ENABLED`, `VAULT_ENABLED`, `PUBLIC_VAULT_URL`.

Keep this list in one module constant (the table in code). Do not scrape the markdown at runtime.

### Keys from a resolved passport

Every map under a section other than `version`. Flatten one level: section name is not part of the ParameterSet key. `dbaas.DBAAS_AGGREGATOR_ADDRESS` contributes `DBAAS_AGGREGATOR_ADDRESS`. Nested maps inside a section are out of scope (passport sections are flat in the generator).

Unreadable or Jinja passport: skip that file, stderr note, do not add its keys.

### Which catalog applies where

- **Env catalog** = table ∪ keys from the passport resolved for that env. If resolve fails or there is no passport, env catalog = table only.
- **Cluster catalog** = table ∪ union of env catalogs in that cluster ∪ keys from passport files that sit under that cluster's `cloud-passport/` or `cloud-passports/` (so a cluster file still feeds the catalog even if no env resolved it).
- **Repo catalog** = table ∪ union of every cluster catalog.

A leaf's **top key** is the first path segment (`DBAAS_AGGREGATOR_ADDRESS`, not a dotted child). PLACE-3 and the PLACE-1 skip match on that top key.

## Passport resolution

The original list below did not specify whether explicit matches were counted across all search levels or separately at each level. For current behavior, use the [PLACE-9 specification](2026-09-11-place9-design.md): explicit lookup collects candidates across the listed roots; automatic lookup stops at the first nonempty name group. This note clarifies which document to follow without inventing a historical priority.

Match the generator (`find_cloud_passport_definition` / `find_passport_by_env_definition` in `business_helper.py`). The linter **does not** fail the check when the generator would raise.

For each environment, in order:

1. If `inventory.cloudPassport` is a non-empty string, search for `<name>.yml` or `<name>.yaml` (not a creds file) under `cloud-passport/` and `cloud-passports/`, recursively, at these levels:
   - `<env>/Inventory/`
   - `<cluster>/` (parent of the env)
   - the instance-repo `environments/` directory
   - Zero matches or more than one match: do not resolve. Stderr note. Env catalog = table only.
2. If the field is absent or empty, auto-associate **only** in the cluster directory, in this order:
   - `cloud-passport/<cluster-name>.yml|.yaml`
   - `cloud-passport/passport.yml|.yaml`
   - Auto uses the directory name `cloud-passport` only (not `cloud-passports`), same as the generator.
   - Zero matches: no passport. Env catalog = table only.
   - More than one match at the same step: do not resolve. Stderr note.

`*-creds.yml` / files under a `credentials/` or `Credentials/` subfolder are not passports.

## On the cluster (file placement)

A passport file is **on the cluster** when its path is under:

`environments/<cluster>/cloud-passport/` or `environments/<cluster>/cloud-passports/`

and `<cluster>` is a discovered cluster.

Every other passport YAML we index is a finding: repo-level `environments/cloud-passport/`, env `Inventory/cloud-passport/`, or any other folder. One finding per misplaced file. Hint: move it to `environments/<cluster>/cloud-passport/`. If the path identifies an owning cluster, name it in the hint; otherwise say “a cluster's `cloud-passport/`”.

Index candidate passport files by walking `cloud-passport/` and `cloud-passports/` under `environments/`, under each cluster, and under each env `Inventory/`. Do not treat those directories as clusters or environments (already true).

## The three checks (original design)

### 1. Misplaced passport file

Each indexed passport YAML that is not on the cluster → one PLACE-3 warning on that file (line 1 if we have no better position).

### 2. Contract key at the repository layer

In the **site** projection, a leaf authored at `repository` whose top key is in the **repo catalog** → one PLACE-3 warning. Dedup `(file, top key)` so two scopes sharing one file print once.

Hint: move the key to the cluster layer.

### 3. Contract key copied across environments

For each cluster, independently:

1. For each env, take leaves authored at `environment` in `full` whose top key is in that **env catalog**.
2. Drop a leaf that is a restatement versus `lower` (same key, same value already in repository+cluster ParameterSets). That case is PLACE-2 only.
3. Participants for a `(scope, path)` = envs whose remaining contribution contains that leaf.
4. Emit when at least **two** participants author the same path with the same value.

One env alone is an override (or the only writer) — silent. Differing values — silent.

Anchor the finding on the first participant after sorting env names (same as PLACE-1). Hint: move the key to the cluster; keep it at env only when the value is genuinely different. Mention the other participants in `related` (console may omit `related`, same as PLACE-2).

Dedup `(file, top key)` across scopes.

## PLACE-1 skip

PLACE-1 must not hoist a catalog key:

- Env → cluster: skip a leaf whose top key is in that env's catalog.
- Cluster → repository: skip a leaf whose top key is in that cluster's catalog.

PLACE-2 is unchanged.

## Report

Same four-line block as PLACE-1 / PLACE-2. Always print three headers, in order, each with findings or `No findings`.

```
PLACE-1
…

PLACE-2
…

PLACE-3
<path>:<line>
warning
<message>
<hint>
```

Messages (English in code, this meaning):

- File: passport `<stem>` is not at the cluster layer.
- Repository key: key `<key>` belongs to the Cloud Passport contract but is authored at the repository layer.
- Env agreement: key `<key>` belongs to the Cloud Passport contract and is repeated in environments of cluster `<cluster>`.

Exit: `0` on warnings, `2` if there is no `environments/` or on bad CLI usage.

## Tests

Write with the rule:

- Explicit `cloudPassport` resolves; auto `passport.yml` resolves; missing passport → table only.
- Duplicate explicit match → no resolve, stderr note, table only.
- Passport file under `environments/cloud-passport/` → file finding.
- Passport file under env `Inventory/cloud-passport/` → file finding.
- Passport under `environments/<cluster>/cloud-passport/` → no file finding.
- Table key in `environments/parameters/` → repository finding.
- Free-form key only in this cluster's passport, same key at repository → repository finding.
- Two envs, same catalog key, same value, absent from `lower` → one PLACE-3; PLACE-1 silent on that key.
- One env only → silence.
- Two envs, different values → silence.
- Env restates cluster ParameterSet (same value below) → PLACE-2 only.
- Lab: `testdata/place3/ok` and `testdata/place3/not-ok`.

## Algorithm document

After the code: `docs/algorithms/place3.md` and `docs/algorithms/ru/place3.md` — enough to reimplement without reading Python. Cite the generator functions and the mapping table. List the table keys explicitly.
