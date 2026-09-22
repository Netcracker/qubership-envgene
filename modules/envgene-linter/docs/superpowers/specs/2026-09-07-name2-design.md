# envgene-linter: NAME-2 (filename stem equals name)

> **Historical specification.** The body preserves the 2026-09-07 decisions, including the former file selection, examples and test expectations. File selection and the examples and expectations affected by it are superseded by the shared [connected-only contract](2026-09-11-connected-only-design.md). Only selected physical ParameterSets and selected Artifact Definitions are checked; presence in a definition directory does not establish use. See the [current NAME-2 algorithm](../../algorithms/name2.md) for the current processing flow. Other decisions remain unless they conflict with the new scope.

Date: 2026-09-07  
Status at design time: approved in conversation; awaiting file review\
Russian copy (for the reader): [ru/2026-09-07-name2-design.md](ru/2026-09-07-name2-design.md)

Standard: NAME-2 SHOULD — the filename stem equals the object's `name` field. The stem is the reference key (`env_definition` lists `cloud-deploy`, not the YAML `name`). A mismatch can be determined by direct comparison. This cycle **reports** it and tells the reader to set `name` to the stem. It does **not** edit files.

## Terms and reading guide

- **ParameterSet:** a YAML parameter file.
- **RepoIndex:** the inventory of files, clusters and environments built by repository discovery.
- **Stem:** the filename without its data extension and optional `.j2` suffix: `cloud-deploy.yml.j2` → `cloud-deploy`.
- **Finding:** one reported rule result. TYPE is its classification and ACTION is the suggested response.
- **Effective Set:** the final parameter set after merging layers.
- **STV (Shared Template Variables):** variables shared by templates.

Integration sections, rule ordering and tests describe the development cycle dated above, not the complete current linter. `SHOULD` identifies a recommendation in the standard; the actual finding classifications are specified below.

## Goal

`check` reports NAME-2 when a ParameterSet or a named definition file has a `name` that does not equal its filename stem, or has no usable `name`. Mismatch is TYPE **Warning**, ACTION **Fix**. Missing / empty `name` is TYPE **Information**, ACTION **Review**.

## In plain terms

`cloud-deploy.yml` with `name: deploy-params` → one finding: set `name: cloud-deploy`. The same file with `name: cloud-deploy` is silent. No `name` (or `name: ""`) → a softer Information finding, same fix suggestion.

## Out of scope

- Autofix / rewriting YAML
- Renaming the file to match `name`
- Full schema validation of Application / Registry / Artifact definitions
- Scanning env_definition, Cloud Passport, credentials, resource profiles, STV, or other YAML
- Effective Set (`compute`)
- NAME-3…NAME-9
- `--rules`, JSON, `--strict`
- Running `check` without `environments/` (still exit 2)

## Algorithm

Input: `RepoIndex` only. Do not call `compute`.

### Files

**ParameterSets.** Every `ParamsetFile` on the index (repository, cluster, environment) that is not Jinja and has no load error. Unbound / orphan files **were included in this historical scope**; the connected-only contract above now excludes them.

**Named definitions.** Every YAML file under these instance-root directories (same table as the old linter). Deduplicate by resolved path if a file is reachable twice:

| Relative directory | Kind label |
| --- | --- |
| `appdefs` | Application definition |
| `configuration/appdefs` | Application definition |
| `regdefs` | Registry definition |
| `configuration/regdefs` | Registry definition |
| `configuration/artifact_definitions` | Artifact definition |

Skip a definition that fails to load. Skip Jinja (`.yml.j2` / `.yaml.j2`) the same way as paramsets.

Do not scan passport files, `env_definition`, or any other YAML.

### Stem and declared name

- Stem = existing `paramset_stem` (`cloud-deploy.yml` and `cloud-deploy.yml.j2` → `cloud-deploy`).
- Declared name = root-document `name`. If the key is absent or the value is `None` or `""`, the file has **no name**. Otherwise compare `str(name)` to the stem (so `name: 1` is `"1"`).

If `str(name) == stem` → no finding.

### Findings

One finding per file. At most one of the two shapes below.

**Mismatch** — a usable name that is not equal to the stem:

| Field | Value |
| --- | --- |
| `rule` | `NAME-2` |
| `severity` | `Severity.WARNING` (`warning`) |
| `issue_type` | `Warning` |
| `action` | `Fix` |
| `path` / `line` / `column` | the `name` key |
| `locations` | that one location |
| `key` | `name` |
| `scope` | stem |
| `related` | empty |
| `message` | `{kind} filename stem {stem!r} does not equal the name field {declared!r}.` |
| `hint` | `Set name: {stem} to match the filename, which is the reference key.` |

`kind` is `ParameterSet`, `Application definition`, `Registry definition`, or `Artifact definition`.

**No name** — key absent, `None`, or `""`:

| Field | Value |
| --- | --- |
| `rule` | `NAME-2` |
| `severity` | `Severity.INFORMATION` (`information`) |
| `issue_type` | `Information` |
| `action` | `Review` |
| `path` / `line` / `column` | the `name` key if present (including `""`); otherwise `1:1` |
| `locations` | that one location |
| `key` | `name` |
| `scope` | stem |
| `related` | empty |
| `message` | `{kind} {filename} has no name field; EnvGene requires it to equal the filename stem {stem!r}.` |
| `hint` | `Set name: {stem}` |

`{filename}` is `path.name` (for example `cloud-deploy.yml`).

The filename wins. Never hint to rename the file.

## Catalog, console, HTML

`rulemeta.py`:

- description: `Filename stem must equal the name field`
- default TYPE `Warning`, ACTION `Fix`

Missing-name findings override TYPE/ACTION to Information / Review. PLACE-* stay Warning / Fix. NAME-1 stays Information / Review.

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `NAME-1`, `NAME-2`. Empty console block: `NAME-2\nNo findings`.

HTML: same details/cards as other rules. Heading `NAME-2: Filename stem must equal the name field`. FILE lists `locations`. Chips follow the finding: Warning/Fix or Information/Review.

## Engine and discovery

`run_check` appends `check_name2(index)` after NAME-1. No extra Effective Set work.

Discovery grows a `NamedEntityFile` list on `RepoIndex` (path, stem, kind, loaded / error). Paramsets already on the index are enough; read `name` from `loaded.doc` at check time.

`check` still requires `environments/` (exit 2). Named definitions are scanned when that check runs and the directories exist.

## Algorithm doc

Write `docs/algorithms/name2.md` and `docs/algorithms/ru/name2.md` in the implementation cycle (same role as `name1.md`).

## Tests

- Paramset stem equals `name` → no NAME-2
- Paramset `name` differs → one Warning / Fix; message has both stem and declared; hint tells to set `name` to the stem
- Paramset missing `name` → Information / Review
- Paramset `name: ""` → Information / Review
- Orphan paramset with a mismatch → finding
- Jinja paramset skipped
- Load-error paramset skipped
- Artifact definition under `configuration/artifact_definitions` with a mismatch → finding (`Artifact definition`)
- Application or registry definition stem equals `name` → no finding
- Console: `NAME-2` after `NAME-1`; mismatch prints `warning`
- HTML heading `NAME-2: Filename stem must equal the name field`; mismatch chips Warning / Fix
- PLACE-* and NAME-1 tests still pass (empty NAME-2 console block — update exact strings)

## Code changes

| File | Role |
| --- | --- |
| `src/envgene_linter/model.py` | `NamedEntityFile`; list on `RepoIndex` |
| `src/envgene_linter/discovery.py` | walk the five definition directories |
| `src/envgene_linter/rulemeta.py` | NAME-2 catalog |
| `src/envgene_linter/report.py` | `RULE_ORDER` + NAME-2 |
| `src/envgene_linter/engine.py` | call NAME-2 |
| `src/envgene_linter/rules/name2.py` | create |
| `docs/algorithms/name2.md` | algorithm |
| `docs/algorithms/ru/name2.md` | Russian algorithm |
| `tests/test_name2.py` | create |
| `tests/test_report.py`, `test_cli.py`, `test_rulemeta.py` | empty NAME-2 block / catalog |

yamlio and Effective Set stay as they are. Reuse `paramset_stem` and `LoadedYaml.position`.
