# Effective Set

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
  `envSpecificE2EParamsets` (e2e), `envSpecificTechnicalParamsets` (technical).
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

1. Every repository-layer file `environments/parameters/<name>` whose stem is the
   reference goes into one flat staging directory.
2. Every cluster-layer file `environments/<cluster>/parameters/<name>` whose stem is
   the reference also goes into that **same** flat directory. If its filename is
   identical to a file already placed there by step 1, it **replaces that file
   outright** (`copy2` semantics) — the site file's content is gone, not merged with
   the cluster file. Two names differ if their extensions differ: `shared.yml` and
   `shared.yaml` are different names, and both may end up in the flat directory side
   by side.
3. Every environment-layer file
   `environments/<cluster>/<env>/Inventory/parameters/<name>` whose stem is the
   reference goes into a `from_instance/` subdirectory, never into the flat directory.
   Because it never collides with a same-named file there, an environment-layer file
   always survives even when the site and/or cluster already have a file with the same
   name.

Jinja ParameterSets (`*.yml.j2`, `*.yaml.j2`) are skipped this cycle (§9) and never
reach staging, so in practice the staged filename is just the real filename. An
unreadable YAML ParameterSet is not Jinja: it still occupies its staged filename
(§9).

## 4. Apply order

Once staged, sort every file that will apply for the reference by `(tier, staged
path)`, ascending, and apply them in that order — later entries overwrite earlier ones
per §5. Tiers:

| Tier | Location |
| --- | --- |
| 0 | a template directory (`from_template`, `from_peer_template`, `from_origin_template`) — unused this cycle, no template layer exists |
| 1 | the flat staging directory (site and cluster files, after the same-name replacement in §3.2) |
| 2 | `from_instance/` (environment files) |

Within a tier, ties break alphabetically by staged path (so `shared.yaml` sorts before
`shared.yml`... concretely: plain lexicographic string order of the staged filename).
Consequence: tier 1 always applies before tier 2, so an environment-layer file always
has the last word for any key it sets, regardless of alphabetical order.

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

```
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

- **No template layer.** There is no `from_template` staging, no tier-0 files, and
  target filtering against a generated `Namespaces/` tree does not happen — every key
  named by an `envSpecific*` array is treated as a scope.
- **Cloud Passports are not merged.** Passport values are not part of the Effective
  Set, but the static contract keys plus keys from selected passports form catalogs
  that suppress those keys in PLACE-1. This avoids false hoist findings without
  treating passport values as ParameterSet contributions.
- **Jinja ParameterSets are skipped, not evaluated.** A `*.yml.j2` / `*.yaml.j2` file is
  recorded as skipped (a note on the skipped-note list, printed on stderr) and never
  contributes a leaf, even if its rendered-and-evaluated content would. It also never
  occupies a staged filename, so it cannot replace a readable site or cluster file.
- **Unreadable YAML ParameterSets are skipped from merge and provenance.** A ParameterSet
  that fails to parse is recorded on the same skipped-note list as Jinja and never
  contributes a leaf or provenance. Staging still keys the file by staged filename
  (`resolve_reference`): an unreadable cluster file with the same name as a site file
  replaces that site file in the flat directory (§3.2) and then contributes zero
  leaves. The site values for that stem are gone. There is no extra diagnostic beyond
  the skip note.

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
