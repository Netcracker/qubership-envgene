# envgene-linter: PLACE-2

- [Current removal contract](#current-removal-contract)
  - [Requirements](#requirements)
  - [Design](#design)
  - [Acceptance tests](#acceptance-tests)
- [Original approved iteration](#original-approved-iteration)
- [Goal](#goal)
- [In plain terms](#in-plain-terms)
- [Out of scope (this cycle)](#out-of-scope-this-cycle)
- [Code changes](#code-changes)
- [Rule](#rule)
  - [Examples](#examples)
- [Report](#report)
- [Tests](#tests)
- [Algorithm document](#algorithm-document)

File eligibility is governed by the later shared [connected-only contract](2026-09-11-connected-only-design.md).

The current requirements below govern removal advice. The original approved iteration follows for historical
context. Its unconditional restatement warning and instruction to avoid Effective Set changes are superseded by
this contract. The complete processing flow is in the
[PLACE-2 algorithm](/modules/envgene-linter/docs/algorithms/place2.md).

The later [input error contract](/modules/envgene-linter/docs/superpowers/specs/2026-10-20-input-error-handling-design.md)
also applies. Unreadable environment definitions remain potential consumers when proving shared-source removals.

## Current removal contract

### Requirements

A repeated value qualifies for Fix only when its decoded YAML type matches the inherited value and removing
the exact source entry preserves the complete merged parameter bags of every known local selected consumer.
The proof covers all selecting environments, targets, categories, and application scopes, including uses where
that entry is not a restatement or the final winner. A definite change makes the override necessary and is silent.
Unconfirmed equality or preservation produces Information / Review without deletion advice or source values.

The source identity is the resolved physical file plus the full YAML source path.
Global and application parameter containers, nested paths, and literal keys containing dots remain distinct.
Repeated selections and physical aliases of the same source entry receive one result.
Each finding concerns an independent removal. Removing several findings together is not proven safe.
No source file or indexed YAML document is modified.

### Design

- [yaml_values.py](/modules/envgene-linter/src/envgene_linter/yaml_values.py) supplies typed, recursive,
   three-valued comparison shared with PLACE-1. Quote style does not affect string equality.
- [effective.py](/modules/envgene-linter/src/envgene_linter/effective.py) shares its accumulation path between
   leaf projections and complete parameter bags. Analysis can omit one source entry from a copy at every
   selection of its physical file, preserving parent mappings, file order, and filename shadowing.
- [removal_analysis.py](/modules/envgene-linter/src/envgene_linter/removal_analysis.py) records known consumers,
   checks their selected merge sources, and compares bags before and after each independent removal.
   It caches baseline bags per environment and results per source entry within a run.
- [rules/place2.py](/modules/envgene-linter/src/envgene_linter/rules/place2.py) retains projection-based
   candidate collection and deduplicates by the complete source identity before choosing Fix, Review, or silence.

Source completeness requires readable ordinary YAML with supported parameter/application shapes and literal
references and application identities. Missing, dynamic, invalid, or relevant unrendered sources prevent a proof.
Anchors, aliases, YAML merge keys, custom tags, unsupported values, and bounded-analysis failures also require Review.
The proof is limited to the known local binding graph. Remote consumers and complete template composition are excluded.

### Acceptance tests

- Distinct scalar types and nested type differences do not receive redundant-override advice.
- A sequence of values `2`, `5`, and `2` retains the last override, including nested and application parameters.
- Shared sources must preserve every selecting environment, target, and parameter category.
- Physical aliases are omitted together, and shadowed repository sources remain absent.
- Global/application entries and literal dotted/nested keys receive separate findings.
- Missing, Jinja, malformed, anchored, tagged, or otherwise unsupported source contexts receive Review.
- Unknown application identities and unknown scalar equality receive Review without parameter values.
- Repeated analysis leaves source bytes and indexed documents unchanged.

Tests live in [test_place2.py](/modules/envgene-linter/tests/test_place2.py),
[test_yaml_values.py](/modules/envgene-linter/tests/test_yaml_values.py), and
[test_effective.py](/modules/envgene-linter/tests/test_effective.py).

## Original approved iteration

Date: 2026-09-02  
Status at design time: approved\

## Goal

Terminology: **env** means environment; a **binding** is a reference from `env_definition.yml` to a ParameterSet; a **scope** is target × category, optionally separated by application. Effective Set is the merged parameter result; discovery catalogs files and reads bindings.

`envgene-linter check <repo>` prints PLACE-1 first, then PLACE-2.

PLACE-2 (SHOULD): if a more specific layer authors a key with the same value the less specific layers already supply, that override is a restatement. Remove the key from the more specific layer, or change the value if a real difference was intended.

## In plain terms

Same three layers as PLACE-1: repository (`environments/parameters/`) → cluster → env.

Only ParameterSets named in `env_definition` participate. Unbound files are invisible to the rule.

PLACE-1: “the same in every env — hoist it.”  
PLACE-2: “the environment or cluster copied an inherited value — delete the copy.”

A key does not get both rules: PLACE-1 already skips restatements.

## Out of scope (this cycle)

- Template, passport, Jinja
- `--rules`, JSON/HTML, baseline, `[EXCEPTION …]`, autofix
- Later rules (PLACE-3 onward)

## Code changes

Do not change discovery or Effective Set.

| File | Role |
| --- | --- |
| `rules/place2.py` | The rule |
| `engine.py` | Run PLACE-2 after PLACE-1 |
| `report.py` | PLACE-1 block, then PLACE-2 block |
| `tests/test_place2.py` | Synthetic cases |
| `testdata/place2/{ok,not-ok}/` | Lab trees |
| `docs/algorithms/place2.md` | Algorithm (English) |
| `docs/algorithms/ru/place2.md` | Same algorithm in Russian |

## Rule

Use the same Effective Set projections as PLACE-1: `full`, `lower` (no env), `site` (repository only).

For each key **authored** at the more specific layer (environment or cluster), compare the same scope and leaf path in the less specific projection:

1. The less specific projection has no such key → silent (new, not a restatement).
2. The less specific projection has a different value → silent (a real override).
3. The less specific projection has the same value → PLACE-2 warning.

Two comparisons:

- **Env over lower layers.** Env wrote `LOG_LEVEL: info`, cluster or repository already supplied `LOG_LEVEL: info` → finding.
- **Cluster over repository.** Cluster wrote the same value already in `environments/parameters/` → finding.

A cluster file is shared by many envs. Emit the cluster restatement **once**, not once per env.

### Examples

The environment binds both `shared` and `env-deploy` under `envSpecificParamsets.cloud`. The following are two separate ParameterSet files; the environment repeats a cluster value:

```yaml
# environments/cluster-01/parameters/shared.yml
name: shared
parameters:
  LOG_LEVEL: info
  REPLICA_COUNT: 2
```

```yaml
# environments/cluster-01/env-01/Inventory/parameters/env-deploy.yml
name: env-deploy
parameters:
  LOG_LEVEL: info      # restatement
  REPLICA_COUNT: 3     # genuine override
```

One finding: `LOG_LEVEL`. Hint: remove the key here, or change the value.

OK: env only has `REPLICA_COUNT: 3`. Silence.

The cluster-versus-repository comparison follows the same rule. Emit one finding per source file and leaf key, even if several environments or scopes see that restatement. Different repeated keys in one file produce separate findings.

## Report

Same shape as PLACE-1:

```text
PLACE-1
…

PLACE-2
<path>:<line>
warning
Key LOG_LEVEL at the environment layer repeats the value already supplied by the cluster layer
Remove LOG_LEVEL here, or change the value if a genuine difference was intended
```

No findings for a rule: that rule’s header and `No findings`. Always print both headers, even if one rule is silent.

Exit codes unchanged: 0 on warnings, 2 if there is no `environments/`.

## Tests

Write with the rule:

- env copies cluster → one finding
- different value → silence
- key absent below → silence
- cluster copies repository → one finding
- two envs see one cluster restatement → one finding, not two
- lab: `testdata/place2/ok` and `testdata/place2/not-ok`

## Algorithm document

After the code: `docs/algorithms/place2.md` and `docs/algorithms/ru/place2.md` — short, same examples, no Python dumps.
