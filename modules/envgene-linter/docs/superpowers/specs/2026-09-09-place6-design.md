# envgene-linter: PLACE-6 (pipeline ParameterSets bind to the Cloud)

File eligibility is governed by the later shared [connected-only contract](2026-09-11-connected-only-design.md).

The original binding-only check below is historical. Under the connected-only contract, a target is checked only if at least one reference in its list selects a file for that environment. Empty and unresolved-only lists produce no finding. See the [current algorithm](../../algorithms/place6.md); report counts below describe this iteration.

Date: 2026-09-09  
Status at design time: approved in conversation; awaiting file review\

Standard: PLACE-6 MUST — a pipeline ParameterSet (`e2eParameters` / `envSpecificE2EParamsets`) associates to the Cloud only. The file may sit at repository, cluster, or environment. Only the **binding target** is fixed to `cloud`. This cycle **reports** a non-Cloud target. It does **not** edit `env_definition`.

## Goal

Terminology: **env** means environment; **stem** means filename without its extension; discovery catalogs files and reads bindings. TYPE is the issue classification; ACTION is the recommended action. `Fix` requests a correction but does not apply it automatically.

`check` reports PLACE-6 when an environment's `envSpecificE2EParamsets` has a map key other than `cloud` (case-insensitive). TYPE **Warning**, ACTION **Fix**. One finding per environment + bad target.

## In plain terms

```yaml
envSpecificE2EParamsets:
  bss:
    - env-1-pipeline
```

→ finding: `bss` is not the Cloud; bind the list under `cloud`.

```yaml
envSpecificE2EParamsets:
  cloud:
    - env-1-pipeline
```

→ no PLACE-6. `Cloud:` / `CLOUD:` also silent. Missing end-to-end block, or empty, → silent.

`cloud` plus `bss` in the same map → one finding, for `bss` only. Two bad targets → two findings.

The ParameterSet YAML and its layer are irrelevant. PLACE-6 does not look at keys inside the file.

## Out of scope

- Autofix / rewriting `env_definition`
- PLACE-5 (which keys belong in end-to-end) and PLACE-7 (one category per set)
- Checking `envSpecificParamsets` / `envSpecificTechnicalParamsets` targets
- Matching targets against a generated `Namespaces/` tree
- Unbound ParameterSet files
- `--rules`, JSON report, `--strict`
- Merging the passport into Effective Set

## Algorithm (original binding-only check)

Input: `RepoIndex` only. Do not call `compute`. Do not change discovery.

For each environment, take `env.bound_targets(Category.E2E)` (already parsed from `envTemplate.envSpecificE2EParamsets`). For each target name in that map, if `target.lower() != "cloud"`, emit one finding.

Dedup is natural: one map key per env. Sort findings by `(path.as_posix(), key, line)`.

### Position

Path: `{env.path}/Inventory/env_definition.yml` (same filename discovery already uses).

Load that file for the key position (`envTemplate` / `envSpecificE2EParamsets` / the target as written). `YamlReadError` → skip the environment (no finding). Unloadable env definitions never produced bindings, so this guards against a later reload failure.

### Finding

| Field | Value |
| --- | --- |
| `rule` | `PLACE-6` |
| `severity` | `Severity.WARNING` (`warning`) |
| `issue_type` | `Warning` |
| `action` | `Fix` |
| `path` / `line` / `column` | that env's `env_definition.yml`; position of the target key |
| `locations` | that one location |
| `key` | the target as written (`bss`, not lowercased) |
| `scope` | `"<cluster>/<env>"` |
| `related` | empty |
| `message` | `{target} is not the Cloud; pipeline ParameterSets must bind under envSpecificE2EParamsets.cloud.` |
| `hint` | `Move the envSpecificE2EParamsets.{target} list to cloud.` |

## Catalog, console, HTML

`rulemeta.py`:

- description: `Pipeline ParameterSets bind to the Cloud`
- default TYPE `Warning`, ACTION `Fix`

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `PLACE-4`, `PLACE-6`, `NAME-1`, `NAME-2`, `NAME-3`, `NAME-4`.

Empty block: `PLACE-6\nNo findings`.

HTML heading: `PLACE-6: Pipeline ParameterSets bind to the Cloud`. Chips: Warning / Fix.

Console: `warning`. Exit 0.

A fixture that binds only `envSpecificParamsets.cloud` (no end-to-end block) is an empty PLACE-6 block. `env-params` / `cloud-deploy` fixtures stay empty for PLACE-6.

## Engine

`run_check` calls `check_place6(index)` after PLACE-4 and before NAME-1. No extra Effective Set work.

## Algorithm doc

Write `docs/algorithms/place6.md` and `docs/algorithms/ru/place6.md`. Update other algorithm `RULE_ORDER` prose: nine headers, PLACE-6 after PLACE-4, then NAME-*. PLACE-5 is not in the catalog.

## Tests

In the shorthand below, `e2e` stands for `envTemplate.envSpecificE2EParamsets`; it is not a literal configuration key.

- `e2e: {bss: [env-1-pipeline]}` → one PLACE-6 Warning / Fix; `key == "bss"`; exact message and hint; path is `env_definition.yml`
- `e2e: {cloud: [env-1-pipeline]}` → no PLACE-6
- `e2e: {Cloud: [env-1-pipeline]}` → no PLACE-6
- no end-to-end block, only deploy → no PLACE-6
- `e2e: {bss: [a, b]}` → still one finding (per target, not per stem)
- `e2e: {bss: […], oss: […]}` → two findings
- `e2e: {cloud: […], bss: […]}` → one finding, key `bss`
- two environments each with `bss` → two findings
- Console: `PLACE-6` after `PLACE-4`; finding prints `warning`
- HTML heading and chips Warning / Fix
- `render()` empty strings gain a PLACE-6 block

## Code changes

| File | Role |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | PLACE-6 catalog |
| `src/envgene_linter/report.py` | `RULE_ORDER` nine-tuple with PLACE-6 after PLACE-4 |
| `src/envgene_linter/engine.py` | call PLACE-6 |
| `src/envgene_linter/rules/place6.py` | create |
| `docs/algorithms/place6.md` | algorithm |
| `docs/algorithms/ru/place6.md` | Russian algorithm |
| other algorithm `RULE_ORDER` prose | nine rules, PLACE-6 after PLACE-4 |
| `tests/test_place6.py` | create |
| `tests/test_lab.py`, `test_cli.py`, `test_report.py`, `test_rulemeta.py` | order / empty blocks |

Discovery, yamlio, Effective Set, PLACE-1…PLACE-4, and NAME-* stay as they are. Reuse `load` for positions. Bindings already on `EnvModel`.
