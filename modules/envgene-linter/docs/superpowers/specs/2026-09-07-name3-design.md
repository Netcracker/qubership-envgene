# envgene-linter: NAME-3 (kebab-case names)

> **Historical specification.** The body preserves the 2026-09-07 decisions, including the former file selection, examples and test expectations. File selection and the examples and expectations affected by it are superseded by the shared [connected-only contract](2026-09-11-connected-only-design.md). The former recursive file walk and checks of every namespace directory are superseded. Only selected files, used environment definitions and their cluster/environment directories, and namespaces targeted by resolved ParameterSet or Resource Profile bindings are checked. See the [current NAME-3 algorithm](../../algorithms/name3.md) for the current processing flow. Other decisions remain unless they conflict with the new scope.

Date: 2026-09-07  
Status at design time: amended in conversation (Information / Review; all YAML under `environments/`); awaiting file review\

Standard: NAME-3 SHOULD — filenames, directory names, and namespace names use kebab-case. YAML field names and enum values follow the object's own convention (this rule does **not** check them).

This cycle **reports** a non-kebab name. It does **not** rename files or directories. Some names are used in generation logic; renaming them requires a separate refactor. Therefore TYPE is **Information** and ACTION is **Review** for every finding.

## Terms and reading guide

- **ParameterSet:** a YAML parameter file.
- **RepoIndex:** the inventory of files, clusters and environments built by repository discovery.
- **Stem:** the filename without its data extension and optional `.j2` suffix: `cloud-deploy.yml.j2` → `cloud-deploy`.
- **Finding:** one reported rule result. TYPE is its classification and ACTION is the suggested response.
- **Effective Set:** the final parameter set after merging layers.
- **STV (Shared Template Variables):** variables shared by templates.

Integration sections, rule ordering and tests describe the development cycle dated above, not the complete current linter. `SHOULD` identifies a recommendation in the standard; the actual finding classifications are specified below.

## Goal

`check` reports NAME-3 when (1) a cluster, environment, or namespace directory name is not kebab-case, or (2) a YAML / JSON / Jinja file under `environments/` has a stem that is not kebab-case. TYPE **Information**, ACTION **Review**.

## In plain terms

`environments/Cluster_01/` → one finding (cluster directory). `cloud-deploy.yml` is silent. `Cloud_Deploy.yml` is a finding. `env_definition.yml` is a finding (`env_definition` is not kebab-case). The `Inventory/` directory name is not a finding (it is not a cluster / env / namespace). Files inside `Inventory/` are checked.

## Out of scope

- Autofix / renaming files or directories
- YAML keys and enum values
- Files outside `environments/` (including `appdefs/` / `regdefs/` / `artifact_definitions` at repository root)
- Files with unsupported extensions under `environments/` (`.md`, `.png`, `.txt`, …)
- Directory names other than cluster, environment, and namespace (`Inventory/`, `parameters/`, `cloud-passport/`, …)
- Effective Set (`compute`)
- NAME-4…NAME-9
- `--rules`, JSON report, `--strict`

## Algorithm

Input: `RepoIndex` (for `root`, clusters, and environments). Do not call `compute`. Walk `environments/` on disk for files. Do not change discovery.

### Kebab-case

A name is kebab-case iff it matches `^[a-z0-9]+(?:-[a-z0-9]+)*$` (full match). Examples that pass: `env`, `cluster-01`, `cloud-deploy`, `credentials` (one lowercase token). Examples that fail: `Cluster_01`, `Cloud_Deploy`, `env_definition`, empty string.

### No skip-list

Do not skip EnvGene-mandated names. `env_definition` is a finding. `Inventory` as a **directory** is still out of scope (see above); an `Inventory.yml` **file** under `environments/` would be a finding.

### File filter

Under `environments/`, consider a path iff it is a file and its name ends with `.yml`, `.yaml`, `.json`, `.yml.j2`, `.yaml.j2`, or `.json.j2`. Include hidden files (name starts with `.`).

Do not descend into a directory named `.git`.

### Stem

Reuse `paramset_stem`: strip a trailing `.j2` if present, then strip `.yml` / `.yaml` / `.json`. The kebab check uses that stem, not the filename with extension.

### What to check

One finding per failing path. Skip if `is_kebab(name)`.

| Source | Name | Kind | Path |
| --- | --- | --- | --- |
| each cluster on the index | `cluster.name` | `Cluster directory` | `cluster.path` |
| each environment on the index | `env.name` | `Environment directory` | `env.path` |
| each child directory of `env.path / "Namespaces"` (including hidden; do not recurse) | directory name | `Namespace` | that directory |
| each matching file under `environments/` (walk, not the paramset/passport/entity index) | `paramset_stem(path)` | `File` | that file |

Do not also iterate `ParamsetFile` / `NamedEntityFile` / `PassportFile` lists — that would duplicate paths already found by the walk, and would miss credentials / STV / other YAML that discovery does not index.

Hidden cluster / environment directories stay on the index if discovery indexed them; report them. Do not skip names that start with `.`.

### Finding

| Field | Value |
| --- | --- |
| `rule` | `NAME-3` |
| `severity` | `Severity.INFORMATION` (`information`) |
| `issue_type` | `Information` |
| `action` | `Review` |
| `path` / `line` / `column` | the directory or file; `1:1` |
| `locations` | that one location |
| `key` | the failing name |
| `scope` | the kind string |
| `related` | empty |
| `message` | `{kind} {name!r} is not kebab-case.` |
| `hint` | `Review whether this name can be kebab-case. Do not rename it if generation or other logic still depends on the current spelling.` |

Do not apply `str.capitalize()` to `kind`. Write `kind` as in the table.

## Catalog, console, HTML

`rulemeta.py`:

- description: `Filenames, directories, and namespaces use kebab-case` (unchanged)
- default TYPE `Information`, ACTION `Review`

`RULE_ORDER` unchanged: `PLACE-1`, `PLACE-2`, `PLACE-3`, `NAME-1`, `NAME-2`, `NAME-3`. Empty console block: `NAME-3\nNo findings`.

A typical fixture with `env_definition.yml` is **not** an empty NAME-3 block: it has a `File` finding for `env_definition`.

HTML heading: `NAME-3: Filenames, directories, and namespaces use kebab-case`. Chips: Information / Review.

Console: findings print `information`. NAME-3 findings alone do not make the exit code nonzero; other findings or command errors can still do so.

## Engine

`run_check` still appends `check_name3(index)` after NAME-2. No extra Effective Set work.

## Algorithm doc

Update `docs/algorithms/name3.md` and `docs/algorithms/ru/name3.md` in the implementation cycle.

## Tests

- Cluster `Cluster_01` → one NAME-3 Information / Review with kind `Cluster directory`; message has `Cluster_01`; hint is the review sentence (the same repository also has `env_definition` as a `File` finding)
- Kebab cluster and env (`cluster-01`, `env-01`) → no finding for those directory names; still a `File` finding for `env_definition`
- Env `Env_01` → finding `Environment directory`
- Namespace directory `Foo` under `Namespaces/` → finding `Namespace`
- Paramset file `Cloud_Deploy.yml` → finding `File` (not `ParameterSet`)
- `env_definition.yml` → finding `File` `'env_definition'`
- Directory name `Inventory` is not a NAME-3 finding
- Matching kebab file stem (`cloud-deploy.yml`) → no finding from that file
- Console: `NAME-3` after `NAME-2`; finding prints `information`
- HTML heading unchanged; chips Information / Review
- PLACE-* / NAME-1 / NAME-2 tests that assumed an empty NAME-3 block on a real `check` of a repository with `env_definition.yml` must expect the `env_definition` finding (pure `render()` unit tests with no NAME-3 findings stay empty)

## Code changes

| File | Role |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | NAME-3 defaults → Information / Review |
| `src/envgene_linter/rules/name3.py` | walk `environments/`; drop skip-list; Information; new hint |
| `docs/algorithms/name3.md` | algorithm |
| `docs/algorithms/ru/name3.md` | Russian algorithm |
| `tests/test_name3.py` | new expectations |
| `tests/test_cli.py`, `tests/test_rulemeta.py` | console / HTML / catalog |
| `tests/test_report.py` | only if empty-block assumptions break |

Discovery, yamlio, and Effective Set stay as they are. Reuse `paramset_stem`.
