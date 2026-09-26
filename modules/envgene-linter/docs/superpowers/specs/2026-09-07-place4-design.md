# envgene-linter: PLACE-4 (passport keys stay out of ParameterSets)

File eligibility is governed by the later shared [connected-only contract](2026-09-11-connected-only-design.md).

The original global stem-based selection and Jinja retry below are historical. The connected-only contract now requires a physical ParameterSet selected for an environment and excludes unrendered Jinja from content checks. Other decisions and the report order below describe this iteration; see the [current algorithm](../../algorithms/place4.md).

Date: 2026-09-07  
Status at design time: approved in conversation; awaiting file review\

Standard: PLACE-4 SHOULD — a Cloud Passport **contract** key does not live in a ParameterSet. Override it in that environment's cloud-passport, not in a paramset. This cycle **reports** the key and tells the reader to move it. It does **not** edit files.

## Goal

Terminology: **env** means environment; **stem** means filename without its extension; discovery catalogs files and reads bindings. TYPE is the issue classification; ACTION is the recommended action. `Fix` requests a correction but does not apply it automatically.

A **top-level key** here is a direct child of the ParameterSet `parameters` map, not a document metadata key such as `name`. `TABLE` is the static set of Cloud Passport contract names in `passport.py`.

`check` reports PLACE-4 when a bound ParameterSet contains a top-level key from the EnvGene passport table. TYPE **Warning**, ACTION **Fix**.

PLACE-3 keeps only **misplaced passport files**. Its ParameterSet-key checks (`_repository_keys`, `_env_agreement`) move here — including a contract key authored on the **cluster** layer.

## In plain terms

`CLOUD_API_HOST` in `Inventory/parameters/cloud-deploy.yml` → finding: put it in `cloud-passport/passport.yml` (cluster), or in this env's cloud-passport if the value is an override.  
The same key only in `environments/cluster-01/cloud-passport/passport.yml` → no PLACE-4.  
`MY_CUSTOM_HOST` from a passport YAML, not in the table → no PLACE-4.  
`extra.yml` not listed in any `envSpecific*` → no PLACE-4.

## Out of scope

- Autofix / rewriting YAML
- Merging the passport into Effective Set
- Custom keys that appear only in a passport file (not in `TABLE`)
- Unbound ParameterSets
- Credentials / STV / resource profiles as files
- `--rules`, JSON report, `--strict`

## Algorithm

Input: `RepoIndex` only. Do not call `compute`. Use `TABLE` from `passport.py` (do not union flattened passport-file keys).

### Bound files (original selection, later superseded)

A ParameterSet file is in scope iff its `stem` appears in at least one environment's `envSpecific*` lists (`env.bindings`). Site, cluster, and environment layers all count. Deduplicate by path.

### Jinja (original retry, later superseded)

If `file.is_jinja` or `file.loaded` is missing, try `load(file.path)`. Success → scan that doc. `YamlReadError` → skip (no finding). Do not change discovery.

### What to scan

`leaves(file.parameters)` (or `leaves` of the loaded `parameters` map after a jinja retry). A leaf's **top key** is `path[0]`. If that string is in `TABLE`, one finding for that file + top key. Nested children of the same top key do not add a second finding.

Error / unloadable non-jinja files: skip.

### Finding

| Field | Value |
| --- | --- |
| `rule` | `PLACE-4` |
| `severity` | `Severity.WARNING` (`warning`) |
| `issue_type` | `Warning` |
| `action` | `Fix` |
| `path` / `line` / `column` | the ParameterSet file; position of the top key |
| `locations` | that one location |
| `key` | the table key |
| `scope` | `"repository"` / `"<cluster>"` / `"<cluster>/<env>"` from the file's layer |
| `related` | empty |
| `message` | `{key} is a Cloud Passport contract key; do not store it in a ParameterSet.` |
| `hint` | `Move {key} to the cluster cloud-passport, or to this environment's cloud-passport if the value is an override.` |

Sort findings by `(path.as_posix(), key, line)`.

## PLACE-3 this cycle

`place3.py` keeps `_misplaced_files` only. Delete `_repository_keys` and `_env_agreement`. PLACE-3 tests that expected a key finding become PLACE-4 tests (or assert the finding's `rule == "PLACE-4"`). Lab `place3/not-ok` that only had a DBAAS key in a paramset is a PLACE-4 finding, not PLACE-3.

PLACE-1 still skips catalog keys using the existing `Catalogs` (table ∪ flattened passport keys). Do not change that skip.

## Catalog, console, HTML

`rulemeta.py`:

- description: `Cloud Passport keys do not belong in ParameterSets`
- default TYPE `Warning`, ACTION `Fix`

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `PLACE-4`, `NAME-1`, `NAME-2`, `NAME-3`, `NAME-4`.

Empty block: `PLACE-4\nNo findings`.

HTML heading: `PLACE-4: Cloud Passport keys do not belong in ParameterSets`. Chips: Warning / Fix.

Console: `warning`. Exit 0.

A fixture that binds `env-params` with no table keys is still an empty PLACE-4 block.

## Engine

`run_check` calls `check_place4(index)` after PLACE-3 and before NAME-1. No extra Effective Set work.

## Algorithm doc

Write `docs/algorithms/place4.md` and `docs/algorithms/ru/place4.md`. Update PLACE-1…PLACE-3 and NAME-*`RULE_ORDER` prose: PLACE-4 after PLACE-3, then NAME-*. Update `place3.md` so ParameterSet-key checks are PLACE-4.

## Tests

- Bound `cloud-deploy.yml` with `CLOUD_API_HOST` → one PLACE-4 Warning / Fix; exact message and hint
- Same key only in cluster `passport.yml` → no PLACE-4
- Bound file with `MY_CUSTOM_HOST` only → no PLACE-4
- Unbound `extra.yml` with `CLOUD_API_HOST` → no PLACE-4
- Cluster-layer paramset with `DBAAS_AGGREGATOR_ADDRESS` → PLACE-4 (not PLACE-3)
- Site-layer paramset with a table key → PLACE-4 (old PLACE-3 repository-key case)
- Two table keys in one file → two findings
- Jinja that is valid YAML and contains a table key → PLACE-4
- Jinja that does not parse → no PLACE-4
- Console: `PLACE-4` after `PLACE-3`; finding prints `warning`
- HTML heading and chips Warning / Fix
- PLACE-3 file-misplacement tests still pass; PLACE-3 key tests retargeted
- `render()` empty strings gain a PLACE-4 block

## Code changes

| File | Role |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | PLACE-4 catalog |
| `src/envgene_linter/report.py` | `RULE_ORDER` |
| `src/envgene_linter/engine.py` | call PLACE-4 |
| `src/envgene_linter/rules/place3.py` | drop key checks |
| `src/envgene_linter/rules/place4.py` | create |
| `docs/algorithms/place4.md` | algorithm |
| `docs/algorithms/ru/place4.md` | Russian algorithm |
| `docs/algorithms/place3.md` and `ru/` | key checks → PLACE-4 |
| other algorithm `RULE_ORDER` prose | eight rules |
| `tests/test_place4.py` | create |
| `tests/test_place3.py` | key cases → PLACE-4 or drop |
| `tests/test_lab.py`, `test_cli.py`, `test_report.py`, `test_rulemeta.py` | order / empty blocks |

Discovery, yamlio, Effective Set, and `TABLE` stay as they are. Reuse `leaves` and `load`.
