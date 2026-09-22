# envgene-linter: NAME-1 (one name per concept)

> **Historical specification.** The body preserves the 2026-09-05 decisions, including the former file selection, examples and test expectations. File selection and the examples and expectations affected by it are superseded by the shared [connected-only contract](2026-09-11-connected-only-design.md). Only selected physical ParameterSets contribute values or locations; orphan and shadowed files are excluded. See the [current NAME-1 algorithm](../../algorithms/name1.md) for the current processing flow. Other decisions remain unless they conflict with the new scope.

Date: 2026-09-05  
Status at design time: approved in conversation; awaiting file review\

Standard: NAME-1 SHOULD — collapse true aliases to one canonical key. Equal values are not proof of an alias. This cycle reports **Information / Review only**, without automatic fixes or instructions for an AI to change keys.

## Terms and reading guide

- **ParameterSet:** a YAML parameter file.
- **RepoIndex:** the inventory of files, clusters and environments built by repository discovery.
- **Finding:** one reported rule result. TYPE is its classification and ACTION is the suggested response.
- **Effective Set:** the final parameter set after merging layers.

Integration sections, rule ordering and tests describe the development cycle dated above, not the complete current linter. `SHOULD` identifies a recommendation in the standard; the actual finding classifications are specified below.

## Goal

`check` reports NAME-1 when **different key names** in the instance repo share the same non-empty string value. The page shows TYPE **Information**, ACTION **Review**. The operator (or a later AI rule) looks and leaves the keys alone unless they truly mean one concept for one consumer.

## In plain terms

Three Kafka keys, one broker address → one finding, all files and all keys listed. The same key name in ten files is not NAME-1 (that is the same name). A username and password that happen to share a placeholder are not aliases.

## Out of scope

- Autofix / collapsing keys
- Length minimums
- Scanning env_definition, Cloud Passport, or non-paramset YAML
- Effective Set (NAME-1 does not merge layers)
- NAME-2…NAME-9
- `--rules`, JSON, `--strict`

## Algorithm

Input: `RepoIndex` only. Do not call `compute`.

### Files

Every `ParamsetFile` on the index (repository, cluster, environment) that is not Jinja and has no load error. Unbound / orphan files **were included in this historical scope**; the connected-only contract above now excludes them. Skip passport files and `env_definition`.

### Leaves

From each file:

- `parameters` — `yamlio.leaves`, keep only non-empty strings
- each `applications[i].parameters` — the same; the reported key is `{appName}.{dotted}`

Do not walk lists (a list item has no key name). Nested maps: any depth. Numbers, bools, null, and `""` are ignored.

Key identity is the full dotted path (`NESTED.KAFKA_URL` ≠ `KAFKA_URL`).

### Groups

Group leaves by exact string value.

In a group, **distinct key names** matter, not file count. One name in many files → no finding.

Then drop credential pairs that share this value. Two names form a pair when their final dotted segments share the same prefix before partner suffixes:

| suffix | partner |
| --- | --- |
| `_USER` | `_PASSWORD` or, if using `_PASS`, `_PASS` |
| `_USERNAME` | `_PASSWORD` / `_PASS` |
| `_PASSWORD` / `_PASS` | `_USER` / `_USERNAME` |

Match on the **last segment** of the dotted path, case-insensitive (same table as the old linter: `_USER`/`_PASSWORD`, `_USERNAME`/`_PASSWORD`, `_USER`/`_PASS`, `_USERNAME`/`_PASS`). Dotted parents need not match: `db.POSTGRES_USER` and `app.POSTGRES_PASSWORD` form a pair, but `POSTGRES_USER` and `REDIS_PASSWORD` do not. Remove both sides of every matching pair simultaneously, then require at least two distinct names again.

### Finding

One finding per remaining value-group.

| Field | Value |
| --- | --- |
| `rule` | `NAME-1` |
| `severity` | `Severity.INFORMATION` (`information`) |
| `issue_type` | `Information` |
| `action` | `Review` |
| `path` / `line` / `column` | first occurrence (sort by relative path, then key name) |
| `locations` | every occurrence in the group |
| `key` | first key name |
| `scope` | `repository` |
| `related` | sorted unique key names |
| `message` | `Keys {k1}, {k2}, … share the value {value!r}.` |
| `hint` | `Review whether they mean the same concept for the same consumer. Do not collapse them unless that is intended.` |

Key names in `message` / `related` are sorted.

## Catalog, console, HTML

`rulemeta.py`:

- description: `Different keys may name the same concept`
- default TYPE `Information`, ACTION `Review`

`Severity` gains `INFORMATION = "information"`. PLACE-* stay `WARNING`. Console prints `information` for NAME-1.

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `NAME-1`. Empty console block: `NAME-1\nNo findings`.

HTML: same details/cards as other rules. FILE lists every `locations` entry. Chips: Information, Review.

## Engine

`run_check` appends `check_name1(index)` after PLACE-*. No extra Effective Set work.

## Algorithm doc

Write `docs/algorithms/name1.md` and `docs/algorithms/ru/name1.md` in the implementation cycle (same role as `place1.md`).

## Tests

- Three Kafka-style keys, same string, one file → one finding; `related` has all three names; TYPE Information, ACTION Review; `locations` length 3
- Nested map: `outer.KAFKA_URL` and `BOOTSTRAP_SERVERS` same string → finding (two names)
- Same key name in two files, same value → no NAME-1
- `POSTGRES_DBA_USER` / `POSTGRES_DBA_PASSWORD` same string → no finding
- Empty string / int / bool only → no finding
- Unbound paramset with two alias keys → finding
- Jinja paramset skipped
- `applications[].parameters` uses `{appName}.{key}`
- Console contains a `NAME-1` block; with a finding, `information` and both paths if two files
- HTML heading `NAME-1: Different keys may name the same concept`; chips Information / Review
- PLACE-* tests still pass (empty NAME-1 console block — update `test_report.py` / CLI no-findings exact strings)

## Code changes

| File | Role |
| --- | --- |
| `src/envgene_linter/model.py` | `Severity.INFORMATION` |
| `src/envgene_linter/rulemeta.py` | NAME-1 catalog |
| `src/envgene_linter/report.py` | `RULE_ORDER` + NAME-1 |
| `src/envgene_linter/engine.py` | call NAME-1 |
| `src/envgene_linter/rules/name1.py` | create |
| `docs/algorithms/name1.md` | algorithm |
| `tests/test_name1.py` | create |
| `tests/test_report.py`, `test_cli.py`, `test_rulemeta.py` | empty NAME-1 block / catalog |

Discovery, yamlio, and Effective Set stay as they are except using existing `leaves` / `ParamsetFile`.
