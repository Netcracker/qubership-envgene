# Check only connected or used entities

Status: implemented following the user's request to apply connected-only checks across all rules, including NAME-3.

This specification supersedes the eligibility scope in earlier rule specifications. Their naming, value-comparison and reporting requirements remain in force unless explicitly replaced here. Later [PLACE-9](2026-09-11-place9-design.md) adds passport ambiguity checks; [PLACE-10](2026-09-11-place10-design.md) adds Shared Template Variable selection.

## Terms

- **Connected / selected file:** an existing file chosen for an environment by a supported local reference or documented generator use.
- **Physical path:** the path after resolving symbolic links. Different aliases can identify one physical file.
- **Stem:** the filename without its data extension (`.yml`, `.yaml` or `.json`) and optional `.j2` suffix. Equal stems do not prove that files are identical or connected.
- **Lookup bucket:** one group of candidate files at a particular search priority. An occupied bucket contains at least one matching candidate, even if its contents are malformed.
- **Shadowed file:** a lower-priority input replaced during resolution; it is not used by that environment.
- **Projection:** a subset of actually selected inputs restricted to particular repository, cluster or environment layers.

## Contract

All rules must inspect only entities selected by a visible local reference or a
documented generator usage. The user explicitly extended this scope to NAME-3. No missing-reference diagnostics, new heuristics, autofix, or networking.
Unknown external/template/Jinja usage is not proof of a connection.

A connection identifies a resolved physical path in the context of an environment,
not merely a globally matching filename stem. No unused file may contribute to a
finding, its locations, category aggregation, or a passport-derived key catalog.
Loading/discovery skip notes remain discovery diagnostics, not rule findings.

## Resolution and shared usage

Introduce a shared connections module used by rules, with optional reuse of a
single computed connection set by the engine. Direct rule calls must obey the same
filter as engine calls. Keep existing model constructor defaults compatible.

ParameterSets use existing `effective.resolve_reference(index, env, reference)`
with all layers. Keep every surviving staged file, including environment files;
a cluster file with the same staged filename excludes the repository file for
that environment. Collect per-file uses (environment, category, target, reference)
and per-environment selected paths. Invalid YAML may occupy a selected slot, but
content checks still skip unreadable/unknown documents. Jinja is not rendered.

For PLACE-1/2 projections, first resolve actual full-layer inputs, then retain the
requested layers. A hypothetical projection must not resurrect a shadowed file
that the environment does not use. Keep the lower-level explicit `resolve_reference`
API semantics if needed; `compute` projections must follow connected-only inputs.

Cloud Passports use `resolve_passport`: explicit `inventory.cloudPassport` and its
existing documented auto-discovery are connections. Unresolved/ambiguous passports
are not selected. Key catalogs must contain the static contract table plus keys
from selected passports, never from unrelated unselected passport files.

Profiles and credentials retain PLACE-8's search and ambiguity handling: Inventory,
cluster, repository bases; ordered alias directories; exact stems; all candidates
in the first occupied bucket retained, even if malformed, with no fallback.
Retain aliases for matching and resolved paths for identity. Keep known usage of
`Inventory/credentials/inventory_generation_creds.yml` in discovered environments.
Move/reuse this resolver through the shared module without changing PLACE-8 output.

Artifact Definitions are selected only through strings `envTemplate.artifact`,
`envTemplate.bgNsArtifacts.origin`, or `.peer`, formatted `application:version`. Require a literal string and nonempty first two
colon-separated components; the generator ignores later components. Skip Jinja-like
placeholder values. Do not infer runtime ENV_TEMPLATE_VERSION overrides.
Match the application component to the exact filename stem under
`configuration/artifact_definitions`; `.yml` wins over `.yaml` even if malformed.
Do not select by the definition's `name` field (NAME-2 checks that separately).
Do not infer links from arbitrary string matches, legacy `templateArtifact` GAV,
external templates or a pipeline's unavailable SD inputs. Skip Application/Registry
Definitions until local usage can be proved; directory presence alone is not enough.
Read artifact selectors during discovery and store default-empty fields on EnvModel.
Do not read outside the repository boundary or emit YAML values in new skip notes.

## Rule behavior

- PLACE-1/2: existing value checks over selected full/lower/site contributions only.
- PLACE-3: misplaced selected passports only.
- PLACE-4: contract keys in physically selected ParameterSets only; remove global
  stem-based eligibility. Unrendered Jinja stays outside content checks.
- PLACE-6: check an E2E target only if at least one reference selects a file.
  Empty lists and unresolved-only lists produce no finding. Original target location
  and message remain unchanged for actual connected files.
- PLACE-7: count only references selecting files in this environment. Keep one
  finding per conflicting reference per environment and all its original occurrence
  locations. Preserve source-list indices; filtering must not renumber positions.
- PLACE-8: unchanged Information/Review for known empty selected/used entities.
- NAME-1: group hits only from selected physical ParameterSets and deduplicate alias
  identity; retain existing same-value heuristic and copy.
- NAME-2: check selected physical ParameterSets and selected Artifact Definitions.
  Retain existing name comparison and severity; skip unselected named entities.
- NAME-4: group categories by selected physical file, not global stem. Emit at most
  one finding per file. Use only categories and environment/cluster identifiers
  from actual uses of that file when interpreting its naming scope. Different
  physical files with the same stem must not contaminate one another's categories.
- NAME-3: selected files within its existing environments/ scope, used environment
  definitions and their cluster/environment directories; namespace directories only
  for resolved ParameterSet or Resource Profile targets. See the [NAME-3 algorithm](../../algorithms/name3.md).

## Later additions

[PLACE-9](2026-09-11-place9-design.md) examines ambiguous passport candidates reached by a used lookup attempt. These are not successfully selected files for other content rules. It also checks the used passport-credentials companion without reading its contents.

[PLACE-10](2026-09-11-place10-design.md) adds explicit `envTemplate.sharedTemplateVariables` bindings to the shared selected-file sets. Those files participate in applicable rules, including NAME-3. Its specification defines the exact generator lookup and explains the difference between legacy search paths and the directory required by the standard.

## Example

If an environment selects a cluster file that replaces a repository file with the same staged filename, only the cluster file participates for that environment. Asking PLACE-1 or PLACE-2 for a repository-only projection does not bring the replaced file back. Another environment may still use that repository file if its own resolution selects it.

## Verification and docs

Use synthetic fixtures only. Existing positive tests must explicitly connect the
files they expect to be checked; do not weaken them to empty results. Add regressions
for unused malformed/naming/value/contract candidates; unrelated clusters and same
stems; shadowing; unresolved references; source positions after filtered references;
physical category isolation; alias identity; selected vs unselected passports and
catalog contamination; artifact selector types/priority/legacy/unknown; unchanged
PLACE-8 explicit and implicit use. Verify direct rules and engine behavior.

Update runnable fixtures, current English/Russian algorithm docs, and a common
connection-scope document. Mark obsolete scope descriptions in historical specs as
superseded rather than rewriting the historical decisions. Full pytest and an
independent review are required. Real repositories may be audited read-only locally
using aggregate summaries with no values or credential IDs. No upload, generation,
or changes to real repositories. Preserve unrelated untracked files.
