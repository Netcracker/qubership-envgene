# envgene-linter: PLACE-1 first implementation

File eligibility is governed by the later shared [connected-only contract](2026-09-11-connected-only-design.md).

The original iteration is preserved below, including its report format and exclusions. For current behavior, see [PLACE-1](../../algorithms/place1.md) and [Effective Set](../../algorithms/effective-set.md). In particular, projections now filter inputs selected with all layers present; removing a layer must not restore a shadowed file.

Date: 2026-09-01  
Status at design time: approved\

## Goal

Rebuild the EnvGene instance-repository linter from scratch, rule by rule. This cycle ships one thing a user can run: `envgene-linter check <repo>` reports PLACE-1 findings on stdout.

PLACE-1 (SHOULD): define a value at the highest layer where it holds; override lower only for a genuine difference. In this cycle the layers are **repository**, **cluster**, and **environment**. Template is out.

## Why this shape

PLACE-1 is not a file-to-file comparison. EnvGene merges ParameterSets. A finding is valid only if we know which value an environment actually sees, which layer authored it, and which environments resolve that scope. The first cycle therefore implements the complete path from file discovery to a usable report: discovery → Effective Set → PLACE-1 → console report.

Source of truth when documents and code disagree: **generator code on `feature/modern-toolset`**, then `docs/configuration-standard.md`. The previous `envgene-lint` tree is a draft, not a contract. `docs/envgene-objects.md` “first match found” applies to credentials and resource-profile files, not to ParameterSet merge.

Canonical generator files (local checkout `/home/andy-/Work_Folder/Qubership/qubership-envgene` on `feature/modern-toolset`):

- Staging: `scripts/build_env/main.py` → `prepare_folders_for_rendering`
- Apply order: `scripts/build_env/build_env.py` → `sort_paramsets_with_same_name`
- Binding: same file, `envSpecificParamsets` / `envSpecificE2EParamsets` / `envSpecificTechnicalParamsets`
- Merge: `modules/envgene/envgenehelper/collections_helper.py` → `dict_merge`

## Out of scope (this cycle)

- Template layer (`from_template`, `--templates`)
- Cloud Passport in the Effective Set (PLACE-4 later). A passport key restated in a ParameterSet may appear as PLACE-1 until then
- `*.yml.j2` / `*.yaml.j2` evaluation (skip the file, record a note)
- PLACE-2…PLACE-10, NAME, SEC, INT, VAL, TPL
- JSON/HTML reports, baseline, `--strict`, `--min-envs`, `[EXCEPTION …]` comments, autofix
- Live EnvGene generator in CI

## Architecture

Python package `envgene_linter`. Six units, each with one job:

| Unit | Does | Does not |
| --- | --- | --- |
| `discovery` | Walk `environments/`, build an index (clusters, envs, ParameterSet files, `env_definition` bindings) | Merge values |
| `yamlio` | Load YAML and remember key positions | Know EnvGene types |
| `effective` | For one env, compute Effective Set leaves with provenance | Know PLACE-1 |
| `rules/place1` | Hoist env→cluster and cluster→repository | Print |
| `report` | Format findings for the console | Compute findings |
| `cli` | `envgene-linter check <repo>` wires the path above | Embed rule logic |

Data flow: repo path → `Index` → per-env Effective Set (three projections) → `Finding[]` → text.

## Discovery

An instance repository is a directory that contains `environments/`. If that directory is missing, discovery fails (exit 2).

Layout we care about:

- Repository layer: `environments/parameters/*.yml|yaml`
- Cluster layer: `environments/<cluster>/parameters/*.yml|yaml`
- Environment layer: `environments/<cluster>/<env>/Inventory/parameters/*.yml|yaml`
- Recipe: `environments/<cluster>/<env>/Inventory/env_definition.yml`

A ParameterSet’s reference name is the filename stem (strip `.yml` / `.yaml` / `.json`, and a trailing `.j2` if present). Discovery indexes files even when they are not bound; Effective Set only applies files that a binding names.

`env_definition.yml` bindings (under `envTemplate`):

| Array | Category |
| --- | --- |
| `envSpecificParamsets` | deploy |
| `envSpecificE2EParamsets` | e2e |
| `envSpecificTechnicalParamsets` | technical |

Each binding field maps a target name to a list of reference stems. Target `cloud` is the Cloud object. Any other key is a namespace target. This cycle does not filter targets against a generated `Namespaces/` tree: every key in those maps is a scope.

Cluster and environment identities are directory names under `environments/`, not `inventory.environmentName` / `inventory.cloudName`.

Without a template repository, only `envSpecific*` bindings apply. A ParameterSet that a template array would name, and that no `envSpecific*` entry names, is not part of any scope (uncovered). Do not invent template bindings.

Directories that are not clusters (do not treat as cluster names): `parameters`, `resource_profiles`, `rp_override`, `Profiles`, `credentials`, `Credentials`, `shared-credentials`, `configuration`, `configurations`, `shared_template_variables`, `shared-template-variables`, `cloud-passport`, `cloud-passports`. Under a cluster, the same set plus `app-deployer` and `cloud-deployer` are not environments.

Jinja ParameterSets (`*.yml.j2`, `*.yaml.j2`) are indexed as skipped, not evaluated.

## Effective Set

Terminology: a **leaf** is an individual parameter value at a key path; **provenance** records its source file, layer, and YAML position. **Site** means the repository layer. A **projection** is the merged result restricted to a specified set of layers.

Input: repo index + one environment.  
Output: for each **scope**, a map of leaf path → `{value, provenance}`.

**Scope** = target (`cloud` or namespace name) × category (`deploy` / `e2e` / `technical`). An optional application name is a separate scope when the ParameterSet carries `applications[].parameters` (matching the generator’s handling of those parameter maps). An environment that does not bind a given target+category does not resolve that scope and is not a PLACE-1 participant for it.

### Staging (no template)

For a reference stem the generator copies:

1. Site files `environments/parameters/` into one flat staging directory
2. Cluster files `environments/<cluster>/parameters/` into the **same** directory — identical staged filename **replaces** the site file entirely (`copy_path` / `copy2`)
3. Environment files `Inventory/parameters/` into `from_instance/`, so a second file with the same name survives

Staged filename is the real filename. `.yml` and `.yaml` are different names; both can apply.

### Apply order

`sort_paramsets_with_same_name`: sort key is `(tier, filePath)`.

- tier 0: path contains a template directory (`from_template`, `from_peer_template`, `from_origin_template`) — unused this cycle
- tier 2: path contains `from_instance`
- tier 1: everything else (the flat site+cluster directory)

Later entries override earlier ones.

### `dict_merge(a, b)`

- If either side is not a dict: return `a` if `b is None`, else `b` (scalars and lists replace wholesale)
- If both are dicts: union of keys; each common key merges recursively (`None` in `b` means “absent”, keep `a`)

Provenance of a leaf is the last file that supplied that leaf during merging, including an explicit repetition of the same value. A nested `None` ignored by `dict_merge` does not change provenance.

### Three projections per environment

PLACE-1 needs more than the fully merged set:

| Projection | Layers included | Role |
| --- | --- | --- |
| `full` | repository + cluster + environment | What the env sees; which leaves environment authored |
| `lower` | repository + cluster | Detect environment restatements; cluster-authored leaves |
| `site` | repository only | Detect cluster restatements |

“Authored at layer L” means: in the relevant projection, the leaf’s provenance layer is L.

## PLACE-1

Severity: warning (SHOULD). Agreement threshold: **2**, hardcoded (no `--min-envs`).

A leaf is a **restatement** when a more specific layer supplies the same value as the less specific layers at the same scope and path: compare environment against `lower`, or cluster against `site`. Restatements are silent this cycle (PLACE-2’s subject).

### Environment → cluster

For each cluster, independently:

1. For each environment, contribution = leaves authored at environment in `full` that are not restatements versus `lower`.
2. Participants for a scope = environments with at least one remaining contribution in that scope. Resolving the scope alone does not make an environment a participant.
3. Emit a finding when there are at least two participants and they all author the same path with the same value.

An environment with no remaining contribution in the scope is not a participant. For example, two environments contributing `LOG_LEVEL` can agree even if a third contributes nothing. If the third contributes another key in that scope but lacks `LOG_LEVEL`, it participates and blocks agreement on `LOG_LEVEL`. Moving a value to a cluster ParameterSet reaches only objects that reference that ParameterSet.

One environment alone never produces a finding. Differing values are a genuine difference, not a finding.

If every environment that resolves the scope overrides a stale cluster value with the same new value, that is PLACE-1 (the cluster value no longer holds).

### Cluster → repository

1. Skip a cluster that has no environments (nothing resolves its ParameterSets).
2. Cluster contribution = leaves authored at cluster in `lower` that are not restatements versus `site`. If the collected cluster-authored contributions disagree on a path’s value across environments, drop that path.
3. Participants for a scope = clusters whose contribution contains that scope.
4. Emit a finding when at least two such clusters author the same path with the same value.

### Finding

Anchor on the first participant after sorting names:

- `rule`: `PLACE-1`
- `path` + `line` of the anchored leaf
- `severity`: warning
- `key`, `scope` (cluster + scope for env→cluster; `repository` + scope for cluster→repository)
- `message`: what is wrong (who agrees, which value, why the higher layer is where it holds)
- `hint`: move the key to `environments/<cluster>/parameters/` or `environments/parameters/` and drop the copies
- `related`: the other participants’ locations

## Console report

One header per rule, then one block per finding:

```
PLACE-1
<path>:<line>
warning
<message>
<hint, including related paths>

```

Blank line between findings. Zero findings:

```
PLACE-1
No findings
```

Skipped Jinja / unreadable YAML files: notes on stderr after the report, not mixed into PLACE-1 blocks.

## Errors and exit codes

| Situation | Exit | Output |
| --- | --- | --- |
| Findings (warnings only) | 0 | Report on stdout |
| No findings | 0 | `PLACE-1` / `No findings` |
| Missing `environments/` or bad CLI usage | 2 | Error on stderr |
| One YAML file unreadable | 0 if the rest ran | Skip that file; stderr note |

Warnings do not fail CI in this cycle (no `--strict`).

## Testing

Write tests with the algorithm, not after the whole slice.

1. **`dict_merge` and staging** — nested maps, list replace, `None` keeps prior, same staged filename cluster replaces site, environment file survives under `from_instance`, `.yml` vs `.yaml` both apply, sort order `(tier, path)`.
2. **PLACE-1 units** (synthetic repos): identical env values → one finding; different values → none; single env → none; unbound third env does not block; restatement vs lower → none; stale cluster overridden identically → finding; identical cluster values across two clusters → repository finding; disagreeing clusters → none.
3. **Lab trees** `testdata/place1/ok` and `testdata/place1/not-ok` — ordinary instance repos, not mocks.
4. **One Effective Set golden** — vendor a small generated snippet into `testdata/golden/` (copied from `qubership-envgene` on `feature/modern-toolset`, with traceability comments). The test always runs against that fixture. Do not invoke the generator.

## Algorithm documents

After the code works, write the check algorithms as standalone docs (not only module docstrings):

- `docs/algorithms/effective-set.md` — staging, apply order, `dict_merge`, scopes, three projections
- `docs/algorithms/place1.md` — restatement, env→cluster, cluster→repository, participants, threshold, finding shape

Each file must be enough to reimplement the check without reading the Python. Cite the modern-toolset functions above.

## Process constraints

- Design and document each algorithm (this spec, then the files under `docs/algorithms/`) before treating the cycle as done.
- Ask when generator code and the standard still leave a fork; do not silently copy `envgene-lint`.
- Next cycle starts only after PLACE-1 `check` works, the tests above pass, and the algorithm files exist. Candidate: PLACE-2 (delta / restatement), which reuses Effective Set.
