# PLACE-8: review referenced or used empty entities

File eligibility is governed by the later shared [connected-only contract](2026-09-11-connected-only-design.md).

The connected-only contract reuses the resolution below without changing PLACE-8 results. Architecture and report counts describe this iteration; see the [current algorithm](../../algorithms/place8.md).

Date: 2026-09-11

Status at design time: approved and implemented.

Russian copy: [ru/2026-09-11-place8-design.md](ru/2026-09-11-place8-design.md).

## Scope

This increment of PLACE-8 reviews empty ParameterSets, Resource Profile Overrides,
and credentials files selected by visible bindings or known generator usage.
It does not determine whether an empty entity is intentional: the finding is
Information / Review. It does not infer unrelated concerns from file size,
application count, service names, or key prefixes.

The agreed behavior for all three types is:

- Empty with a visible binding or known generator usage of that physical file: one Information / Review finding per file.
- Without a visible binding or known usage: skip the file.
- Nonempty: no PLACE-8 finding.

The recommendation is to review whether the empty entity is intentional. Template
bindings are outside this implementation; files used only through such bindings
are skipped until that usage can be established.

Source of resolution behavior: local `qubership-envgene`, `feature/modern-toolset`:
`scripts/build_env/resource_profiles.py:get_env_specific_resource_profiles`,
`scripts/build_env/create_credentials.py:findSharedCredentials`, and
`modules/envgene/envgenehelper/yaml_helper.py:find_yaml_file`.
ParameterSet staging uses the linter's existing `effective.resolve_reference`.

## Discovery and data model

Extend `RepoIndex` and discovery rather than introducing another repository walk
inside the rule. Keep existing fields and constructor behavior compatible by
giving new fields empty defaults. Reuse `NamedEntityFile` as a loaded-file record
in separate `RepoIndex.resource_profiles` and `RepoIndex.credential_files` lists;
do not add these records to `named_entities`, which NAME-2 already checks.

Add `EnvModel.resource_profile_bindings: dict[str, str]` and
`EnvModel.shared_credential_bindings: list[str]`. Read them from `envTemplate`:

| Entity | Binding |
| --- | --- |
| ParameterSet | existing deploy, e2e, technical `envSpecific*Paramsets` maps |
| Resource Profile Override | `envSpecificResourceProfiles`: target to reference name |
| Shared credentials file | `sharedMasterCredentialFiles`: reference-name list |

Keep valid string reference names exactly, without case folding or removing
extensions. Ignore malformed new binding containers and non-string entries.
Existing ParameterSet discovery semantics remain unchanged.

For the repository level, existing clusters, and discovered environments, examine
these bases: `environments/`, `environments/<cluster>/`, and
`environments/<cluster>/<env>/Inventory/`. Within them:

- Profiles: `resource_profiles`, `rp_override`, `Profiles`; also `parameters`
  as the generator's legacy lookup fallback.
- Credentials: `credentials`, `Credentials`, `shared-credentials`.

Search profile/credential directories recursively for `.yml` and `.yaml` files.
Record `.yml.j2` and `.yaml.j2` as skipped templates, without rendering them.
Exclude `.git` directories and generated environment output outside Inventory,
including `<env>/Profiles` and `<env>/Credentials`.
ParameterSet candidate discovery retains its current locations and depth.
Deduplicate file identity using resolved paths; do not follow files outside the
instance repository root through symlinks.

New read errors must not put YAML source snippets or values into skip messages.
Use a path and generic reason such as `cannot parse YAML; PLACE-8 skipped`.
Never include credential IDs, credential values, or file contents in findings.


Known implicit usage: each discovered environment uses the exact file
`Inventory/credentials/inventory_generation_creds.yml`, read by EnvGene
`envgenehelper/env_helper.py:Environment` through `INV_GEN_CREDS_PATH`, even without
a shared-file binding. If it exists and is empty, report Information / Review.
The generator permits the file to be absent (`allow_default=True`); missing files
produce no finding. Same-named repository/cluster files are not implicitly used.
Other implicit usage mechanisms and template bindings are not inferred.

## Resolving visible bindings

Collect a set of bound physical paths across all discovered environments.
A reference in an unrelated cluster must not select a same-named file elsewhere.
An entity shared by multiple environments is checked if any visible binding
selects it.

For ParameterSets, use `resolve_reference(index, env, reference)` for every
existing category and target. Retain every surviving staged file, including
environment overrides. Repository files replaced by an identically named cluster
file do not become bound merely because their stem matches.

For profiles and credentials, search one environment in this order:

1. Its `Inventory` base.
2. Its cluster base.
3. The `environments` base.

At each base, use the directory order listed above (including the profile
`parameters` fallback). Match the exact filename stem, recursively, and stop at
the first directory with a match (a **bucket** is one alias directory at one base, including its descendants). A malformed matching YAML file still
occupies that slot; do not fall through to lower-priority files.

The generator's recursive helper uses filesystem traversal order for multiple
matches within a bucket. That order is not a stable tie-breaker. If a bucket has
multiple matches, treat all its candidates as potentially referenced and check them; do
not invent a deterministic winner. Lower-priority buckets are still shadowed.

The bound-path set is shared across entity kinds: a file selected as a legacy
profile inside `parameters/` must not also receive an empty-ParameterSet finding.

## Entity kind in legacy parameters directories

Classification determines how to inspect a candidate; it does not establish usage. An unselected, unused candidate remains outside findings even when its kind is recognizable.

Files in dedicated profile/credential directories have the corresponding kind.
In a `parameters` directory:

- A path selected by a profile binding is a profile candidate.
- A YAML mapping with `applications` entries containing `services` is also a
  profile candidate, even without a binding.
- Other existing ParameterSet candidates retain their ParameterSet kind.

Use profile emptiness for recognizable profile candidates; skip mixed or
unrecognized payload structures rather than treating them as empty.
An empty, unreferenced mapping in `parameters/` without a recognizable profile
shape is classified by its directory as a ParameterSet. Emit at most one finding
per resolved physical path regardless of overlapping candidate lists.
These classifications are local to PLACE-8 and must not change existing rules.

## Empty, nonempty, or unknown

Inspect structure, not the truthiness of individual values. Root empty mappings,
blank/comment-only YAML, and a root null document are empty. A non-mapping root
other than null is unknown and skipped; an empty YAML list is not a valid entity
mapping and must not be reported as an empty entity.

**ParameterSet:** no entries in top-level `parameters`, and no entries in any
`applications[].parameters`. Missing containers count as absent. Empty application
entries with names alone contribute no parameters. An existing parameter key
counts as content even when its value is null, `""`, false, 0, an empty mapping,
or an empty list. Metadata such as `name` and `version` is not payload.
Wrong container types or malformed application entries make emptiness unknown.

**Resource Profile Override:** no parameter entries in any
`applications[].services[].parameters` list. Missing or empty containers
contribute no entries. Application/service names and metadata are not payload.
Any parameter entry prevents an empty finding even if its value is not populated.
Wrong container types or malformed application/service entries are unknown.

For these structural checks, an application/service entry must be a mapping;
checking its required name or other schema requirements is not part of PLACE-8.
Explicit null containers have the wrong type and are unknown, unlike an absent
container. A root mapping can be classified empty only when its keys are limited
to `name`, `version`, `description`, `parameters`, `applications` for ParameterSets,
or `name`, `version`, `description`, `baseline`, `applications` for profiles.
Other root keys make an otherwise empty candidate unknown. This avoids treating
an unfamiliar or encrypted document as empty metadata.

**Credentials file:** an empty root mapping or empty document. Any top-level
entry prevents an empty finding, even if its credential fields are incomplete.
Do not decrypt, validate secret values, or classify an encrypted mapping as empty.

Unreadable YAML, Jinja files, and unknown structures are skipped, never reported
as empty. This is not schema validation.

## Rule and reporting

Create `rules/place8.py:check(index: RepoIndex) -> list[Finding]`. Build visible
bound paths, classify and deduplicate candidate files, then report only known
empty files that are in the bound/used set. No Effective Set computation is needed.

| Field | Value |
| --- | --- |
| `rule` | `PLACE-8` |
| `severity` | `Severity.INFORMATION` |
| `issue_type` | `IssueType.INFORMATION` |
| `action` | `Action.REVIEW` |
| `path` | empty entity file |
| `line`, `column` | `1`, `1` (whole-file issue) |
| `locations` | this one location |
| `key` | filename stem |
| `scope` | `repository`, cluster directory name, or `<cluster>/<env>` |
| `related` | empty |
| `message` | `{kind} {filename!r} is empty but is referenced or used by the generator.` |
| `hint` | `Review whether this empty file is intentional. If not, populate it or remove its reference or usage.` |

`{filename!r}` means the filename formatted with Python `repr`, including quotes.
`kind` is `ParameterSet`, `Resource Profile Override`, or `Credentials file`.
Catalog description: `Referenced or used entities are empty`.
Sort by `(path.as_posix(), key, line)`.

Register PLACE-8 after PLACE-7 and before NAME-1 in engine, catalog, and report
order. All eleven console headers are printed; empty block:
`PLACE-8\nNo findings`. HTML uses Information / Review chips and the existing
renderer. Findings retain exit code 0. No autofix or new CLI options.

## Validation

Test all three kinds: known empty without binding, bound empty, and nonempty.
Cover main/application parameter content, metadata-only objects, root empty
documents, false/null/zero/empty-string values, malformed structures, Jinja,
encrypted mappings, and sanitized parse-error messages.

Resolve tests cover each level, directory aliases, nested files, exact names,
unrelated clusters, same-name shadowing, multiple environments, ambiguous matches,
unreadable winners, and legacy profiles in `parameters/` without duplicate findings.
Verify exclusion of generated output and outside-root symlinks.

Integration tests pin exact finding fields/copy, sorting, eleven-rule console
order, HTML metadata, and exit code. Run the existing full suite to protect
discovery and all existing rules. Add synthetic ok/not-ok fixtures and English
and Russian algorithm documents.

Real repositories under `/home/andy-/test_data` may be checked read-only locally.
Do not upload them, run generation against them, copy real files into tests or
committed documentation, or expose secret material in output. Use synthetic
examples for tests and documentation.
