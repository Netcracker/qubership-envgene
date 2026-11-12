# PLACE-12 conservative template-default review design

- [Intent](#intent)
- [Approaches](#approaches)
- [Inputs and eligibility](#inputs-and-eligibility)
- [Candidate selection](#candidate-selection)
- [Findings and incomplete checks](#findings-and-incomplete-checks)
- [Template guidance](#template-guidance)
- [Integration](#integration)
- [Acceptance criteria](#acceptance-criteria)

> [!NOTE]
> The [template report design](/modules/envgene-linter/docs/superpowers/specs/2026-11-06-place12-template-report-design.md)
> replaces the per-key finding layout and filename guidance below. Candidate eligibility remains applicable.

## Intent

Implement the candidate-review part of
[PLACE-12](/docs/configuration-standard.md#place-12---shared-defaults-belong-in-the-template-should).
Repeated values from at least two environments are candidates, including environments inside one cluster.
The rule reports Information / Review because repetition does not establish a template-wide default.
It does not prove that moving a value preserves consumers.

The user requested same-cluster support on November 5, 2026, replacing the initial two-cluster threshold.
The remaining conservative eligibility checks continue to apply.

## Approaches

- **Local environment evidence, selected:** reuse connected instance inputs and their Effective Sets.
   This works in the existing single-repository CLI without downloading template artifacts.
   It supplies candidates for human review rather than confirmed template defaults.
- **Evaluate the exact template artifact:** inspect template defaults and render each consumer context.
   This provides more evidence but requires artifact resolution and template evaluation beyond this iteration.

A frequency percentage is not a confidence score. Aliases of one physical source do not add evidence.
Separate copied files can still qualify; physical separation does not prove independent design decisions.
The check considers only the repository supplied to the CLI. It does not combine unrelated roots automatically.

## Inputs and eligibility

Add `EnvModel.template_identity: tuple[str, str] | None = None`.
Discovery derives it from `envTemplate.name` and `envTemplate.artifact` during the existing definition read.
Both values must be nonempty strings. Preserve the exact decoded strings, including the artifact version.
Missing values, invalid shapes, Jinja, and `${...}` expressions do not establish a comparable identity.
Do not derive this pair from `artifact_selectors`, which also contains other artifact roles.

The check consumes `RepoIndex`, complete `EnvEffective` values, and the existing Cloud Passport `Catalogs`.
It uses resolved connected ParameterSets, with the existing staging, merge, and generated-output policy.
Cloud, Namespace, Credential, and other generated objects do not supply parameter values to this check.

Implementation choices for the first version:

- Consider deployment, technical, and end-to-end categories, preserving target and application scope.
- Require complete selected ParameterSet inputs for every environment in a template group.
   A missing reference, unavailable source, parser failure, or unrendered selected Jinja prevents a candidate.
   Preserve raw binding completeness alongside normalized references. Dynamic targets or malformed reference lists
   make group membership unknown and block the group. Absent fields and empty mappings or lists remain valid.
- A target/category participant is every group environment with a nonempty binding list for that target/category.
   An empty parameter bag still participates. An absent application bag cannot establish agreement.
- One cluster is sufficient. Require distinct physical source entries. Aliases of one entry do not add support.
- Exclude repository-authored leaves, including aliases whose resolved source lies under `environments/parameters/`.
   A source must physically belong to its consuming cluster directory to supply an instance-authored contribution.
   The logical `ParamsetFile.layer` alone cannot establish physical origin.
   Repository-owned consumers still participate in missing-value and conflict checks, then prevent a candidate.

Resolve each participant's Cloud Passport explicitly using the existing resolver.
A missing or ambiguous explicit selection, or an unreadable or unrendered selected passport, blocks the template group.
When no passport is selected and resolution reports no error, the standard key table remains sufficient.
The `Catalogs` object supplies excluded keys but does not prove that passport resolution completed.

## Candidate selection

Group environments by the exact template name and artifact name before the first colon, ignoring the version.
Retain complete artifact references in discovery and related source evidence.
Then compare each target/category/application scope. See the
[artifact grouping design](/modules/envgene-linter/docs/superpowers/specs/2026-11-09-place12-artifact-name-design.md).
At least two applicable environments must contribute. They may belong to one or several clusters.
For a given leaf path, every applicable environment must have a value and all comparisons must return
`True` from the existing typed YAML equality function. A missing key or unconfirmed comparison blocks that path.
A conflicting value blocks that path, including a conflict inside one cluster.
Other independent paths can still qualify.

Require at least two distinct physical source entries, identified by resolved file path and source YAML path.
Filenames do not need to match. Repeated references or aliases of one entry do not increase the count.
Compare dictionaries by leaf paths and lists as whole ordered values, following the Effective Set contract.
Only string leaf-path components are supported; typed mapping-key identity is not inferred.

Exclude a candidate when any participant identifies its top-level key as a Cloud Passport contract key.
Reuse the SEC-1 secret-name predicate through a shared public helper in `security_values.py`.
Secret-like parameter names do not become template-default recommendations.
Reject values that are null, contain unresolved expressions, or use unsupported YAML tag semantics.
Inspect strings and keys inside lists and mappings too, with bounded traversal and cycle rejection.
Parameter leaf-path components must also be literal.
Inspect raw provenance values and their ancestors for custom tags, because Effective Set normalization
can remove tags from containers. Apply the secret-name predicate to mapping keys inside list values too.

Also exclude a scalar string exactly equal to a participating cluster name, environment name, or full environment name.
This is a narrow identifier check, not a claim to understand the meaning of every parameter.
Other cluster dependencies can remain unrecognized, which is one reason all candidates remain Review.

Release and `SNAPSHOT` versions do not split groups with the same template and artifact names.
The check does not establish that separate builds of a mutable reference contained identical template bytes.

## Findings and incomplete checks

Emit one finding per template identity, scope, and parameter leaf path:

- `rule`: `PLACE-12`.
- `severity`: `Severity.INFORMATION`.
- `issue_type`: `IssueType.INFORMATION`.
- `action`: `Action.REVIEW`.
- Title: `Repeated values may be shared template defaults`.
- Message: identify the key, template name, artifact name without its version, and environment count.
   Do not include the parameter value.
- Hint: show a proposed Template ParameterSet and descriptor attachment with the actual common value.
   Preserve its YAML types, nested path, target/category, and optional application scope.
   Retain Review and require confirmation of existing defaults and template consumers before removal.
- Locations: every contributing source entry, deduplicated and sorted.
- Related evidence: contributing environment identities and source provenance.

Zero candidates means no PLACE-12 finding. One environment or one shared source entry is insufficient.
Two environments in one cluster can qualify when they have distinct authored entries and meet every other check.
Existing PLACE-1 and PLACE-2 results retain their current meaning and behavior.

Add PLACE-12 to the existing selected-ParameterSet and Cloud Passport read-diagnostic associations.
The engine withholds PLACE-12 candidates when discovery reports incomplete merge inputs, as it does for PLACE-1.
For other unresolved selected inputs, record a located skipped check for the affected template group.
Disabled PLACE-12 produces neither candidates nor its own skipped checks.

## Template guidance

The user requested concrete YAML guidance and explicitly allowed actual values in local reports on November 5, 2026.
Issue messages and related provenance still omit values. Only the recommendation includes the candidate value.
Existing secret-name, expression, passport, and unsupported-input exclusions continue to apply.

Use the template schema and generator's descriptor override mechanism as the portable approach.
A new `template_default_guidance.py` builds a proposed, safe relative filename under `templates/parameters/`.
Include a digest of the exact template name, artifact, target, category, and application identity in the basename.
Distinct scopes must remain separate after normalization or component joining. Parameter paths and values do not
enter the digest, so entries for one template scope share a proposed file. Bound the basename length.
It creates an ordinary ParameterSet with `name` and either `parameters` or `applications`.
Preserve the complete nested parameter path; a literal dotted key remains distinct from nested keys.
Quote string values so values such as `"true"` remain strings after copying.

Show a second YAML fragment with `template_override` for the existing Cloud or Namespace descriptor entry.
Map deployment to `deployParameterSets`, end-to-end to `e2eParameterSets`, and technical to
`technicalConfigurationParameterSets`. Suggested filename suffixes are `deploy`, `pipeline`, and `runtime`.
For a Cloud path string, explain conversion to object form while retaining its path as `cloud.template_path`.
Merge with existing overrides and preserve other descriptor entries and references.
The generator appends primitive ParameterSet references before applying instance-specific references.

Do not invent an existing descriptor filename or Namespace template path from an instance association target.
The check has no template artifact contents. Identify the descriptor by its known template name, and label the
ParameterSet filename as proposed. This avoids changing a common Cloud or Namespace source shared by other templates.
An alternative requiring a local template repository would resolve real files and current defaults, but adds
input resolution beyond this change. No new flag, network request, or template rendering is introduced.

Use `build_template_default_hint(template_name, artifact, scope, path, value) -> str` to build the recommendation.
HTML preserves multiline recommendation indentation in an escaped, wrapping code block.
JSON retains its six-field contract and stores the same text in `fix_suggestion`.
Real repository values appear only in local generated reports, never in source examples or distribution content.
The default Application structure has no `e2eParameters` field. For an application-scoped end-to-end finding,
show the observed ParameterSet value and explain that renderer support needs review. Do not propose an attachment.
Candidate eligibility and Information / Review remain unchanged.

## Integration

Register PLACE-12 in `rulemeta.py`, `rule_config.py`, and `engine.py`. Enable it by default.
Template-only roots retain the existing Not applicable behavior for instance checks.
Reports keep their existing schema and JSON fields, including the absence of a Type field.
No new CLI flags, runtime dependencies, network calls, automatic changes, or release version bump are required.

Add a standalone algorithm, runnable synthetic examples, an entry in the specification index,
and coverage notes in the applicability matrix and readmes. Add one functional Unreleased changelog entry.
Real repository data and trial reports remain outside Git and distribution archives.

## Acceptance criteria

- Equal values in two environments with the same literal template identity produce one Review per qualifying leaf,
   whether the environments belong to one cluster or several clusters.
- One environment or two consumers of one physical source entry produce none.
- Different template names, artifact names, categories, targets, or application names never establish agreement.
- Different literal versions of one artifact can establish agreement. Every bound consumer across those versions
   participates.
- Missing keys, empty participating bags, known conflicts, incomplete selected sources, and uncertain equality
   do not produce candidates.
- Unbound files, repository-only values, generated outputs, shared physical sources, Cloud Passport keys,
   secret-like keys, expressions, and exact local identifiers do not create template-default recommendations.
- Nested values, YAML scalar types, ordered lists, source positions, and deterministic output are covered by tests.
- Disabled and template-only execution, input-error reporting, public examples, HTML/JSON reporting,
   and the distribution allowlist remain covered by integration checks.
- A read-only trial on the local corpus records candidates and exclusions without publishing customer data.
