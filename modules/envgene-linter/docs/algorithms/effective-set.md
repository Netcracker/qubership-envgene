# Effective Set

- [1. Purpose](#1-purpose)
- [2. Scope](#2-scope)
- [3. Staging](#3-staging)
- [4. Apply order](#4-apply-order)
- [5. `dict_merge(a, b)`](#5-dict_mergea-b)
- [6. Provenance](#6-provenance)
- [7. Three projections per environment](#7-three-projections-per-environment)
  - [Complete bags for removal analysis](#complete-bags-for-removal-analysis)
- [8. Citations (source of truth)](#8-citations-source-of-truth)
- [9. Limitations this cycle](#9-limitations-this-cycle)
- [10. Worked example (the golden)](#10-worked-example-the-golden)

Prerequisite for: [`docs/algorithms/place1.md`](./place1.md).

## 1. Purpose

An **Effective Set leaf** is the answer to "what value does this environment actually
see for this parameter key, and which file put it there?" — one
`(scope, key path) -> (value, provenance)` pair. EnvGene does not compare files to each
other directly; it stages several ParameterSet files for the same reference name and
merges them, later files overriding earlier ones key by key. The Effective Set is that
merge result, computed once per environment, kept per scope, with the source file
recorded for every leaf so later checks can say *where* a value came from.

This document describes how to compute it for one instance repository and one
environment, without a template layer and without Cloud Passport (see §9).

## 2. Scope

A **scope** is `target × category`, plus an optional `application` name:

- **category** is one of `deploy`, `e2e`, `technical`. Each corresponds to one array in
  `env_definition.yml` under `envTemplate`: `envSpecificParamsets` (deploy),
  `envSpecificE2EParamsets` (end-to-end), `envSpecificTechnicalParamsets` (technical).
- **target** is a key of one of those arrays: the literal string `cloud` for the Cloud
  object, or a namespace name for anything else. Each target maps to a list of
  **reference names**.
- A **reference name** is a ParameterSet filename stem: strip a trailing `.j2`
  if present, then strip a trailing `.yml`, `.yaml`, or `.json`.
- An environment that has no entry for a given `target × category` in its
  `env_definition.yml` **does not resolve** that scope. It never contributes to that
  scope's Effective Set and is not a participant in any check over that scope.
- Without a template repository, `envSpecific*` bindings are the only bindings that
  exist. Do not invent a binding from a template array that isn't present. A
  ParameterSet that discovery indexed but that no `envSpecific*` entry names is not in
  any scope, even though the file exists on disk.
- Cluster and environment identity are the **directory names** under `environments/`,
  never `inventory.cloudName` / `inventory.environmentName` inside `env_definition.yml`.
- **Application scope**: when a ParameterSet file that a scope resolves also has an
  `applications:` list, and one of its entries has an application name (`appName`, or
  `name` if `appName` is absent/empty) together with its own `parameters:` mapping,
  that entry defines one more scope: the same `target × category`, plus that
  application name. Its leaves come **only** from that entry's `parameters:` mapping —
  never from the file's top-level `parameters:` — and merge independently of the plain
  scope, through the same rules as §3–§6.

## 3. Staging

For one reference name and one environment, the generator physically copies files into
a working tree before merging; this document models that copy step logically, without
writing anything to disk:

1. Recursively enumerate `.yml`, `.yaml`, `.json`, and unrendered `.j2` sources under each supported
   `parameters/` directory. Retain paths relative to that directory.
2. Copy repository sources into the staged tree at their relative paths.
3. Copy cluster sources into the same tree. An identical relative path replaces the repository file completely
   (`copy2` semantics). Different directories or extensions remain distinct fragments.
4. Copy Inventory sources under `from_instance/`, preserving their relative paths. Use the same staged tree:
   Inventory `shared.yml` replaces repository or cluster `from_instance/shared.yml`.
5. Select surviving records by filename stem and sort them as described in section 4.
   Apply projection layer filters only after selecting the actual winners.

Unavailable files retain replacement slots but contribute no values. An incomplete directory scan suppresses
connected selection for the environment rather than choosing uncertain lower-layer files.
File/directory collisions also prevent complete staging, including collisions with unsupported ancestor files.
Paths containing `from_template`, `from_origin_template`, or `from_peer_template` make the affected reference uncertain.
INT-2 reports Review for these cases.
Jinja contents are not evaluated. YAML Jinja names retain the conservative alias described in section 2.

## 4. Apply order

Once staged, sort every file that will apply for the reference by `(tier, staged
path)`, ascending, and apply them in that order. Later entries overwrite earlier ones
per §5. Tiers:

| Tier | Staged path test                                             |
|------|--------------------------------------------------------------|
| 0    | Recognized by the generator's template-directory pattern.    |
| 1    | Neither template-directory nor `from_instance` test matches. |
| 2    | Contains `from_instance` anywhere in the path.               |

The `from_instance` test takes precedence over the template-directory test.
Within a tier, use lexicographic staged-path order. The full relative path participates in that order:
`a/shared.yml` sorts before `z/shared.yml`, even when the latter belongs to a lower source layer.
A repository or cluster path containing `from_instance` also sorts in tier 2.
Template dependency discovery and role-specific template selection remain outside this model.

## 5. `dict_merge(a, b)`

`a` is the value accumulated so far for one key (or nested key); `b` is the next
file's value for that same key, applied in the order from §4. The rule is the same at
every depth, including a bare top-level scalar key — there is no special case for
"top level":

1. **If `a` is not a mapping, or `b` is not a mapping** (this covers scalars, lists,
   `null`, and a mapping being replaced by something that isn't a mapping, or vice
   versa):
   - if `b` is `null`, the result is `a`, unchanged — a later file's explicit `null`
     never erases whatever was already accumulated;
   - otherwise the result is `b` — `b` **replaces `a` wholesale**. Scalars and lists
     never merge item-by-item; a list of 3 items is fully replaced by a list of 1 item,
     never concatenated or zipped.
2. **If both `a` and `b` are mappings**, the result is a mapping whose keys are the
   union of `a`'s and `b`'s keys. For every key in that union, recurse: apply rule 1/2
   to `a`'s value and `b`'s value for that key (a key missing on one side counts as
   `null` on that side, so a key that only `a` has is kept, and a key that only `b` has
   is added).

Worked micro-example — a cluster file sets `FOO: 5`; a later environment file restates
`FOO:` with no value (YAML `null`):

```text
a = 5, b = null
```

`a` is not a mapping, so by rule 1: `b` is `null`, so the result is `a` — `FOO` stays
`5`. This holds however deep `FOO` sits inside a nested mapping; only an explicit
**non-null** value at a given path can change that path.

Corollary: if a later file replaces a mapping with a scalar (or a scalar with a
mapping) at some key, every leaf that used to live *underneath* that key in the old
mapping disappears from the merged result — there is no partial mapping left to merge
into. The new scalar (or the new mapping's own leaves) get provenance from that later
file, per §6.

## 6. Provenance

Provenance answers "which file, applied last in order, actually changed this leaf?"
Process files in the §4 order; for each file, for every leaf path inside the key this
file sets (its own contribution, not the running merged value):

- if that leaf's value **in this file** is not `null`, this file becomes (or stays) the
  leaf's provenance;
- if that leaf's value **in this file** is `null` **and** an earlier file already has
  provenance for that exact path, provenance is left untouched — the earlier file keeps
  the credit, matching §5's "keep `a`" rule;
- if that leaf's value in this file is `null` and no earlier file has ever touched that
  path, this file still becomes its provenance — there is nothing earlier to protect,
  so the leaf's merged value is `null` and stays attributed to the file that first
  mentioned it.

After each file is applied, drop provenance for any path that no longer appears in the
merged value's leaves (the case in §5's corollary — a mapping collapsed into a scalar,
or vice versa, so the old nested path is gone).

The **line number** reported for a leaf is the source line of its key inside its
provenance file: start at the document root, descend through the container path
(`parameters`, or `applications[i].parameters` for an application leaf), then
descend the leaf path.

## 7. Three projections per environment

Resolve the environment's actual full-layer input files first. Compute three
projections by filtering these selected files to the requested layers before merging.
A shadowed repository file is not restored in a projection; see
[connected entities](connections.md).

| Projection | Layers included | Role |
| --- | --- | --- |
| `full` | repository + cluster + environment | What the environment actually sees; which leaves the environment itself authored |
| `lower` | repository + cluster only | What the environment would see without its own overrides; detects environment-layer restatements; which leaves the cluster authored |
| `site` | repository only | Selected repository inputs only; detects cluster-layer restatements without resurrecting shadowed files |

"Authored at layer L" means: in the relevant projection, the leaf's provenance
(§6) has that layer.

### Complete bags for removal analysis

`compute()` returns leaves and provenance for the three projections.
`compute_values()` returns the complete merged parameter bag per scope, including empty mappings,
using the same selected inputs and merge implementation.

PLACE-2 can pass one source occurrence to `compute_values()` for an analysis replay.
An occurrence is the resolved physical file path plus its complete YAML path, including the global or
application parameter container. Replay omits only that entry from an analysis copy at every selection
of the physical file. The file remains selected, its parent mappings remain present, and shadowed inputs
remain absent. Original files and indexed YAML or JSON documents are unchanged.

The [PLACE-2 algorithm](/modules/envgene-linter/docs/algorithms/place2.md) defines source completeness,
consumer coverage, and typed comparison of the bags before and after removal.

## 8. Citations (source of truth)

Canonical generator code, `feature/modern-toolset` branch of `qubership-envgene`:

- Staging (§3): `scripts/build_env/main.py` → `prepare_folders_for_rendering`
- Apply order (§4): `scripts/build_env/build_env.py` → `sort_paramsets_with_same_name`
- Bindings (§2): same file, the `envSpecificParamsets` / `envSpecificE2EParamsets` /
  `envSpecificTechnicalParamsets` lookup
- Merge (§5–§6): `modules/envgene/envgenehelper/collections_helper.py` → `dict_merge`

If generator code and `docs/configuration-standard.md` disagree, the generator code
wins.

## 9. Limitations this cycle

- **No template dependency graph.** Only local instance ParameterSets are selected.
  Reserved template paths require role context and remain uncertain. External template files are not discovered.
  Target filtering against a generated `Namespaces/` tree does not
  happen. Every key named by an `envSpecific*` array is treated as a scope.
- **Cloud Passports are not merged.** Passport values are not part of the Effective
  Set, but the static contract keys plus keys from selected passports form catalogs
  that suppress those keys in PLACE-1. This avoids false hoist findings without
  treating passport values as ParameterSet contributions.
- **Jinja ParameterSets are skipped, not evaluated.** A `.j2` file is indexed with a skip note and contributes
  no leaf. Its unavailable content cannot establish reference validity or a removal proof.
  YAML Jinja filename aliases remain conservative rather than modeling rendered output names.
- **Unreadable YAML and JSON ParameterSets contribute no values.** They retain their staged replacement slots
  and produce generic skip notes. An unavailable replacement does not restore lower-layer values.
  INT-2 reports Review at supported references whose selected source is unreadable.
- **Incomplete staging does not establish source completeness.** Unscanned directories and file/directory
  collisions suppress connected selection. Shared-source removal proofs still account for affected known bindings.
- **JSON decoding follows the generator.** The JSON decoder determines values and scalar types.
  A duplicate object key uses its last value and source location. Position lookup handles nested maps,
  list entries, and application parameters without YAML string normalization.

## 10. Worked example (the golden)

Fixture: `testdata/golden/instance/`, one cluster `c01`, one environment `e01`,
one reference `shared`, scope `cloud/deploy` (`env_definition.yml` binds
`envSpecificParamsets: {cloud: [shared]}`).

Files:

| Layer | File | `parameters:` |
| --- | --- | --- |
| repository | `environments/parameters/shared.yml` | `KEEP_SITE: site`, `WIN: site` |
| cluster | `environments/c01/parameters/shared.yml` | `WIN: cluster`, `FROM_CLUSTER: 1` |
| environment | `environments/c01/e01/Inventory/parameters/shared.yml` | `FROM_ENV: 2` |

Step by step:

1. **Staging (§3).** Both the repository and cluster files are named `shared.yml`, so
   the cluster file **replaces** the repository file in the flat directory outright.
   `KEEP_SITE` is gone; it never reaches the merge. The environment file goes into
   `from_instance/shared.yml` and survives (different directory, no name collision).
2. **Apply order (§4).** Tier 1: the cluster's `shared.yml` (`WIN: cluster`,
   `FROM_CLUSTER: 1`). Tier 2: `from_instance/shared.yml` (`FROM_ENV: 2`).
3. **Merge (§5).** Start from nothing. Apply tier 1: result is
   `{WIN: cluster, FROM_CLUSTER: 1}`. Apply tier 2: `FROM_ENV` is a new key, so it is
   added: `{WIN: cluster, FROM_CLUSTER: 1, FROM_ENV: 2}`.
4. **Provenance (§6).** `WIN` and `FROM_CLUSTER` were last (and only) set by the
   cluster file → provenance layer `cluster`. `FROM_ENV` was set by the environment
   file → provenance layer `environment`. `KEEP_SITE` never entered the merge, so it
   has no leaf and no provenance.

Effective Set for scope `cloud/deploy`, projection `full`:

| Key | Value | Provenance layer |
| --- | --- | --- |
| `WIN` | `cluster` | `cluster` |
| `FROM_CLUSTER` | `1` | `cluster` |
| `FROM_ENV` | `2` | `environment` |

This matches `testdata/golden/expected-leaves.yml`, and `KEEP_SITE` is absent from it.
