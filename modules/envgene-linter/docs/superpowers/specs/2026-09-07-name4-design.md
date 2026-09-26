# envgene-linter: NAME-4 (bound ParameterSet stem)

> **Historical specification.** The body preserves the 2026-09-07 decisions, including the former file selection, examples and test expectations. File selection and the examples and expectations affected by it are superseded by the shared [connected-only contract](2026-09-11-connected-only-design.md). Grouping is now by selected physical file, not by a globally matching stem. Categories and cluster/environment names come only from actual uses of that file; the rule emits at most one finding per file. See the [current NAME-4 algorithm](../../algorithms/name4.md) for the current processing flow. Other decisions remain unless they conflict with the new scope.

Date: 2026-09-07  
Status at design time: approved in conversation; awaiting file review\

Standard: NAME-4 SHOULD — a bound ParameterSet stem is `<subject>-<category>`. The last token is the category and is determined by the `envSpecific*` array that lists the stem, using the mapping below. The subject identifies what the parameters concern and is chosen by the operator, for example `postgresql`. The stem must not bake in a cluster name, environment name, ticket, or release. This cycle **reports** a bad stem. It does **not** rename files or edit `env_definition`. Names are used in generation; renaming them requires a separate refactor. TYPE **Information**, ACTION **Review**.

## Terms and reading guide

- **ParameterSet:** a YAML parameter file.
- **RepoIndex:** the inventory of files, clusters and environments built by repository discovery.
- **Stem:** the filename without its data extension and optional `.j2` suffix: `cloud-deploy.yml.j2` → `cloud-deploy`.
- **Finding:** one reported rule result. TYPE is its classification and ACTION is the suggested response.
- **Effective Set:** the final parameter set after merging layers.
- **STV (Shared Template Variables):** variables shared by templates.

Integration sections, rule ordering and tests describe the development cycle dated above, not the complete current linter. `SHOULD` identifies a recommendation in the standard; the actual finding classifications are specified below.

## Goal

`check` reports NAME-4 when a ParameterSet stem that appears in at least one `envSpecific*` list is not `<subject>-<category>`, or bakes scope/ticket/release into the name.

## In plain terms

`bss.yml` listed under `envSpecificParamsets` → finding (needs `bss-deploy`).  
`bss-deploy.yml` in that array → silent.  
`postgresql-pipeline.yml` in `envSpecificE2EParamsets` → silent.  
`postgresql-deploy.yml` in the end-to-end array → finding (wrong tail).\
`qa01-bss-deploy.yml` when an environment directory is `qa01` → finding (env in the name).  
`extra.yml` in `parameters/` but not listed in any env → silent (unbound).

## Out of scope

- Autofix / renaming files or editing `env_definition`
- YAML keys and the `name` field (NAME-2)
- Unbound ParameterSets
- Credentials, STV, resource profiles, passports, named definitions
- Directory names (NAME-3)
- Effective Set (`compute`)
- NAME-5…NAME-9
- `--rules`, JSON report, `--strict`

## Algorithm

Input: `RepoIndex` only. Do not call `compute`.

### Who is bound

A stem is bound iff at least one environment lists it in any `envSpecificParamsets` / `envSpecificE2EParamsets` / `envSpecificTechnicalParamsets` target list (`env.bindings`).

Collect `categories(stem)`: the set of `Category` values (`deploy` / `e2e` / `technical`) that list that stem. If the set is empty, skip the stem.

Check each bound stem once, not once per layer file.

### Category tail (last token)

| Binding (`Category`) | Required last token |
| --- | --- |
| `deploy` (`envSpecificParamsets`) | `deploy` |
| `e2e` (`envSpecificE2EParamsets`) | `pipeline` |
| `technical` (`envSpecificTechnicalParamsets`) | `technical` |

Split the stem on `-`. There must be **at least two** tokens. The last token must be exactly the required token for **every** category in `categories(stem)`. If the stem is bound as both deploy and end-to-end, no single last token can satisfy both → finding.

`postgresql-deploy-ha` has last token `ha` → finding (tail must be the category, nothing after it).  
`deploy` has one token → finding (subject required).  
Jinja: use `paramset_stem` (`foo-deploy.yml.j2` → `foo-deploy`). Check it.

### Cluster / env / ticket / release

If the stem contains any of these, it is a finding even when the tail is correct:

- a cluster directory name from `index.clusters` (hyphen-bounded, case-insensitive): whole stem, `-name-` infix, `name-` prefix, or `-name` suffix
- an environment directory name from every `env.name` on the index (same match)
- ticket: regular expression `(?:^|-)(?:ticket|jira|issue)-\d+` (case-insensitive)
- release: regular expression `(?:^|-)(?:r\d+(?:-\d+)?|20\d{2}[.-]\d{1,2})`

Do not treat the words `env` / `cluster` / `site` as forbidden unless they are an actual directory name on the index.

Check this **before** the tail rule when both apply (one finding, scope/ticket message).

### Finding

One finding per failing bound stem.

`path`: the first ParameterSet file on the index with that stem, sorted by `path.as_posix()` (collect repository, cluster and environment files, then choose the lexicographically first path; collection order does not determine the result).\
`locations`: that one file at `1:1`.  
`related`: empty.

| Field | Value |
| --- | --- |
| `rule` | `NAME-4` |
| `severity` | `Severity.INFORMATION` (`information`) |
| `issue_type` | `Information` |
| `action` | `Review` |
| `line` / `column` | `1:1` |
| `key` | the stem |
| `scope` | bound category tokens, comma-separated, sorted: `deploy`, `pipeline`, `technical` (the **filename** tokens, not `e2e`) |
| `message` (scope/ticket) | `ParameterSet {stem!r} bakes a cluster, environment, ticket or release into the name.` |
| `message` (tail) | `ParameterSet {stem!r} must end with -{token} to match its env_definition binding ({scope}).` When more than one required token, `{token}` is the sorted slash-joined list (`deploy/pipeline`). |
| `hint` | `Review whether this stem can be <subject>-<category>. Do not rename it if env_definition or other logic still depends on the current spelling.` |

Do not call `str.capitalize()` on messages.

## Catalog, console, HTML

`rulemeta.py`:

- description: `Bound ParameterSet stem is <subject>-<category>`
- default TYPE `Information`, ACTION `Review`

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `NAME-1`, `NAME-2`, `NAME-3`, `NAME-4`. Empty block: `NAME-4\nNo findings`.

A typical fixture that binds `env-params` is **not** an empty NAME-4 block.

HTML heading: `NAME-4: Bound ParameterSet stem is <subject>-<category>`. Chips: Information / Review.

Console: `information`. NAME-4 findings alone do not make the exit code nonzero.

## Engine

`run_check` appends `check_name4(index)` after NAME-3. No extra Effective Set work.

## Algorithm doc

Write `docs/algorithms/name4.md` and `docs/algorithms/ru/name4.md` in the implementation cycle. Update NAME-1…NAME-3 algorithm `RULE_ORDER` prose to seven rules, NAME-4 last.

## Tests

- Bound `bss.yml` in deploy → one NAME-4 Information / Review; key `bss`; message requires `-deploy`
- Bound `bss-deploy.yml` in deploy → no NAME-4
- Bound `postgresql-pipeline.yml` in end-to-end → no NAME-4
- Bound `postgresql-deploy.yml` in end-to-end → finding (must end with `-pipeline`)
- Bound `postgresql-technical.yml` in technical → no NAME-4
- Bound `postgresql-deploy-ha.yml` in deploy → finding
- Bound `deploy.yml` in deploy → finding (subject required)
- Bound `qa01-bss-deploy.yml` while env directory is `qa01` → finding (bakes name)
- Bound `bss-ticket-12-deploy.yml` in deploy → finding
- Unbound `extra.yml` → no NAME-4
- Same stem at site and env, both bound → one finding (not two)
- Jinja `foo.yml.j2` bound as deploy → finding (must end with `-deploy`)
- Console: `NAME-4` after `NAME-3`; finding prints `information`
- HTML heading and chips Information / Review
- PLACE-* / NAME-1…NAME-3 tests that assumed an empty NAME-4 block on a live `check` with `env-params` must expect a NAME-4 finding (pure `render()` tests stay empty)

## Code changes

| File | Role |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | NAME-4 catalog |
| `src/envgene_linter/report.py` | `RULE_ORDER` |
| `src/envgene_linter/engine.py` | call NAME-4 |
| `src/envgene_linter/rules/name4.py` | create |
| `docs/algorithms/name4.md` | algorithm |
| `docs/algorithms/ru/name4.md` | Russian algorithm |
| `docs/algorithms/name1.md` … `name3.md` and `ru/` | `RULE_ORDER` prose |
| `tests/test_name4.py` | create |
| `tests/test_rulemeta.py`, `test_report.py`, `test_cli.py`, `test_lab.py` | catalog / empty blocks / live `check` |

Discovery, yamlio, and Effective Set stay as they are. Reuse the existing paramset lists and `env.bindings`.
