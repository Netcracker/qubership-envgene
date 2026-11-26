# PLACE-12

- [Description](#description)
- [Inputs](#inputs)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Template guidance](#template-guidance)
- [Incomplete inputs](#incomplete-inputs)
- [Examples](#examples)
- [Limits](#limits)
- [Related documentation](#related-documentation)

## Description

PLACE-12 identifies repeated instance parameter values for review as possible template defaults.
It requires agreement from at least two applicable environments within one checked repository.
The environments may belong to one cluster or several clusters.
The rule never confirms a move or recommends unconditional removal of instance overrides.

## Inputs

| Input           | Source                | Purpose                                                         |
|-----------------|-----------------------|-----------------------------------------------------------------|
| `index`         | Repository discovery  | Environment template identities, bindings, and source ownership |
| `full`          | Effective Set         | Final selected values, scopes, and source provenance            |
| `catalogs`      | Cloud Passport lookup | Passport contract keys excluded from candidates                 |
| Minimum support | Rule constant         | Two environments and two distinct physical source entries       |

Discovery stores `EnvModel.template_identity` as the exact decoded pair of `envTemplate.name` and
`envTemplate.artifact`. Both must be nonempty strings without Jinja or `${...}` expressions.
Tagged definition containers and tagged identity values cannot establish a comparable identity.
PLACE-12 derives its group key from the exact template name and the artifact name before the first colon.
For example, `example-env-templates:1.0.0` and `example-env-templates:2.0.0` share an artifact name.
Without a colon, the complete string is the artifact name. An empty or whitespace-only artifact name is invalid.
Case and whitespace in the name remain significant. Versions do not split groups.
Discovery retains the original complete references. Other artifact roles do not supply this pair.

A scope is a target and parameter category, optionally with an application name.
The rule reuses ordinary connected ParameterSet selection and the full Effective Set merge.
Unbound files and generated Cloud, Namespace, and Credential values do not supply candidates.

## Processing flow

1. **Group environments by template and artifact names.** Process environments in full-name order and groups
   in key order. Ignore environments without a comparable identity or nonempty artifact name.
   Require at least two environments, including environments using different versions of the artifact.

2. **Check group completeness.** Resolve every selected ParameterSet reference for every environment in
   the group, including unavailable staged entries. Require ordinary loaded YAML or JSON mappings with supported
   parameter bags. Discovery retains `parameter_bindings_complete` alongside normalized bindings.
   A present binding field must be an untagged target mapping with literal string targets and untagged lists
   of literal string references. Unknown target or list membership blocks the group; absent fields and empty
   mappings or lists remain valid. Resolve the selected Cloud Passport separately.
   Its key catalog alone cannot prove completeness.
   A named passport file that is absent does not block the group. The standard contract-key table is enough,
   because the review asks whether repeated values can move into a template ParameterSet.
   If any other required input is unknown, record an incomplete check and withhold candidates for the whole group.

3. **Select participants for each scope.** Include every group environment with a nonempty binding list for
   the scope's target and category. An empty selected parameter bag still participates. For an application scope,
   a bound environment without that application bag still participates. A missing bag counts as an exception on its keys.
   Environments without the target/category binding do not participate. Require at least two participants.
   Same-cluster participants remain eligible.

4. **Compare leaf values with a bounded number of exceptions.** Consider every leaf path present for any participant.
   A path is shared when at least `N - floor(N/4)` participants have the same literal value. `N` is the participant
   count for that scope. Two or three participants must all agree. Four participants need three. Eight need six.
   Name each other participant in the recommendation and leave its instance value in place. A missing key is such
   an exception. An even split, or any larger dissent, leaves the path silent. Other paths can still qualify.
   Use typed YAML equality: `true`, `1`, `1.0`, and `"1"` differ. Lists compare in order, while mapping order inside
   lists does not matter. Dictionaries outside lists use Effective Set leaf paths. Accept only string path components.

5. **Exclude unsuitable values.** Reject a path if any participant classifies its top-level key as a Cloud
   Passport key, or any path component matches the shared secret-name predicate. Reject nulls, expressions,
   recognized encrypted or Credential markers, custom tags, cyclic collections, and unsupported comparisons.
   Traverse nested lists and mappings too, including their keys and secret-like mapping keys inside lists.
   Parameter path components must also be literal.
   Inspect the raw provenance value and its ancestors for tags that Effective Set normalization can remove.
   Exclude scalar strings exactly matching a participating cluster name, environment name, or full environment name.
   Dynamic target or application names cannot establish a candidate.

6. **Check physical source ownership.** Every contributing leaf must be authored at a cluster or environment
   layer and physically belong to its consuming cluster directory. Exclude repository inputs and aliases pointing
   to repository sources, including sources under `environments/parameters/`. Repository-origin consumers still
   participate in agreement checks, then prevent a candidate. Require at least two distinct source entries,
   identified by resolved file path and full YAML source path. Repeated references do not add evidence.

7. **Group compatible qualifying paths.** Group by template identity, scope, and the ordered participant,
   effective reference, and physical source-file identities. Include parameter count, source names,
   the artifact name without its version, environment count, and every contributing source location.
   Deduplicate locations by physical file, line, and column. Sort them by displayed path and position.
   Keep environment identities, complete artifact references, and provenance in related evidence. Keep values out of
   the issue message and provenance text. The recommendation includes
   all common values in one YAML fragment. Optional local template context supplies a scoped attachment.

Value traversal and equality checks are bounded at 20,000 visited items. Uncertainty excludes a candidate.
Groups, scopes, paths, and locations have deterministic ordering.

## Result

Every candidate receives Information / Review with the title `Repeated values may be shared template defaults`.
Without local template context, the recommendation gives a portable recipe with actual YAML and logical attachment steps.
Explicit local context adds exact destinations while retaining confirmation of template consumers and intentional overrides.
No candidate receives Fix, and the rule changes no files.

Console, HTML, and JSON use the existing finding contract. JSON retains its six fields and has no Type field.
Findings leave the CLI exit code at `0`. No qualifying paths produce an empty PLACE-12 findings list.
A disabled rule produces neither findings nor its own incomplete checks.
Template-only roots retain the instance-rule label `Not applicable`.

## Template guidance

One finding contains the eligible values contributed by the same selected ParameterSet sources and scope.
The recommendation reconstructs nested mappings from original leaf paths. Literal dotted keys remain literal.
YAML serialization preserves scalar types and list ordering. String values remain quoted.
Application values use `applications` entries with `appName` and `parameters`.

Without `-t PATH` / `--template-repo PATH`, show a review recipe that creates one new ParameterSet.
The name is `{template}-{subject}-shared`. A subject is the shared reference when every environment
selects the same ParameterSet, prefixed by the association target, plus the application name when the
scope has one. When each environment bakes its own name as `{cluster}-{environment}-{subject}`, the
subject is that shared tail. Groups that would otherwise share a name add the first parameter key,
lowercased, with underscores written as hyphens. The recipe names the template, the override list to
append, the artifact to release, the instance keys to delete, and any environments that keep a
different value. Keys whose names contain a site address, account, or credential marker are listed
for a second look. Do not invent destination paths, list indices, or existing reference lists.
For unsupported Application end-to-end scope, retain its note and withhold attachment instructions.
With `-t` / `--template-repo`, use the same short recipe.
The first two lines are the absolute instance root and the absolute template root.
Step 1 names the template file.
Add the keys to an existing ParameterSet, reuse a file that already has them, or create
`templates/parameters/<name>.yml`.
A whole-file transfer keeps the current reference and writes that file under `templates/parameters/`.
When the descriptor can be resolved, step 2 names that file in one line and names any resolved
dynamic references there.
Do not paste descriptor YAML, existing reference lists, or per-key cleanup coordinates.
If another consumer or an anchor blocks a deletion, add one Cleanup Review line for that file.
An identical numeric version stays in the relocated ParameterSet.
A differing or non-numeric version is omitted, and the recipe says so in one sentence.
`environments/` source paths belong to the instance root. `templates/` paths belong to the template root.
For a `templates/` input, identify its parent as the template root without resolving linked sources.
CLI users can select the instance root with `-i` / `--instance-repo` instead of the positional argument.

With explicit local context, first look for an existing ParameterSet by the common original reference name,
then by the standard proposed common name. Different original names do not provide one original destination.
Require a unique ordinary YAML or valid JSON file with a consistent name and resolvable association.
Ambiguity, Jinja, custom tags, anchors, dynamic membership, and unsupported containers block merging and cleanup.

Resolve supported dynamic reference names before choosing an attachment or existing destination.
Data-only Jinja attribute paths and literal string-key paths can read each participant's selected Cloud Passport,
name, and environmentName. Ordinary nonempty strings and finite numeric values can form safe ParameterSet names.
Calls, filters, protected paths, unavailable values, tagged ancestors, booleans, and unsupported syntax remain unresolved.
Each resolved dynamic name must identify exactly one readable local ParameterSet file.
Never borrow one participant's values for another. Compare source definitions using the actual selected names.

Later Jinja does not block a list already closed by an unconditional root key when bounded syntax analysis excludes
membership changes. Statements must occupy separate lines without whitespace controls, and later output must stay
inside the unrelated root value. Conditional lists, root-key output, includes, and unconfirmed output remain Review.
A blocked report explicitly states that no relocation proposal was generated and gives the offending source locations.
Successful source-comparison recipes name the resolved references on the attachment step.
Mixed existing-reference membership cannot justify a shared append and retains Review.
No Jinja rendering, Python evaluation, environment lookup, network access, or configuration edits are performed.

Plan absent keys as additions and typed-equal values as reuse. Keep conflicting keys in instance and show their paths.
Lists inside values compare as ordered wholes and are not concatenated.
Render only added fields, preserving unrelated source data without exporting it into the recommendation.
JSON destinations receive JSON fragments. Values that cannot preserve their YAML types in JSON remain conflicts.
Application parameters merge by application identity, retaining other Application entries.
Coordinate claims to one physical file across findings before rendering recommendations.
Conflicting values or parent/child claims invalidate the affected paths and their cleanup in every involved finding.
Existing Inventory references keep their order. Other existing template references remain in place.
Only absent references append last to the selected category list.
A blocked or conflict-only target does not fall back to a new file that would bypass the conflict.

After existing-target resolution, consider complete ParameterSet relocation with its existing name and Inventory binding.
Require one environment-owned source per participant, equal complete payloads, and coverage of every source value
by the current eligible finding. Reject extra consumers or bindings, occupied destinations, unsupported fields,
and incomplete local context. Application parameters retain their container and scope.
Known primary, origin, and peer artifact consumers participate in the conflict check.
Physical-source aliases and existing template references block relocation.
Participants with unresolved role-specific destinations retain partial guidance.
Identical numeric versions are retained in the relocated ParameterSet YAML.
Other versions are omitted, and the recipe says so in one sentence.
The recipe does not list relative instance paths or each participant's reference list.
It says to keep the existing Environment Inventory bindings and reference order.
Files spanning several finding scopes remain partial recommendations.
See the [relocation design](/modules/envgene-linter/docs/superpowers/specs/2026-11-11-place12-paramset-relocation-design.md).

For partial matches or blocked relocation, prepare descriptor guidance:

1. Resolve the named descriptor in generator extension order: `.yml.j2`, `.yaml.j2`, `.yml`, and `.yaml`.
   Require a unique static Cloud or Namespace entry. Namespace targets use literal `deploy_postfix`, then the
   renderer filename rule: remove `.yml.j2` or `.yaml.j2`, retaining other suffixes.
   Resolve only literal paths and the `{{ templates_dir }}` prefix.
2. Inspect ordinary YAML or the unconditional prefix before the first Jinja statement.
   Compare matching source definitions in object bags, descriptor overrides, and selected ParameterSets.
   Dynamic reference matches and duplicate stems remain explicitly uncertain. Preserve source positions.
3. Choose the displayed ParameterSet name with the `{template}-{subject}-shared` rule above.
   Include `.json`, `.yml`, `.yaml`, and `.j2` ParameterSet inputs when checking occupied names.
   Avoid existing stems, instance references, selected template references, and other proposed names.
   A repeated base adds the first parameter key. A further collision uses `-2`, `-3`, and so on before `-shared`.
4. Show that name in the short review recipe.
   Step 1 is `Create file:` with the absolute `templates/parameters/<name>.yml` path, `Merge into file:` for an
   existing ParameterSet, or `Reuse file:` when the keys are already present.
   A blocked target says that no relocation proposal was generated, gives the reason, and does not name a new file.
   When the descriptor resolves, step 2 names that absolute file in one line
   and names resolved dynamic references there.
   Do not paste descriptor YAML, list indices, or existing reference lists.
   Anchored values or inherited keys stay Review, with no create or edit action.
   Append a missing reference last. Keep existing references in place.
   An unresolved descriptor receives the reason and no invented file action.
5. Keep source evidence distinct from effective defaults. Local checkout equivalence with the artifact,
   rendered Jinja values, external parents, and other consumers remain unverified.

For example, environments that share template `business`, target `oss`, and reference `logging-deploy`
can propose `templates/parameters/business-oss-logging-deploy-shared.yml`:

```yaml
name: "business-oss-logging-deploy-shared"
parameters:
  APP_LOG_LEVEL: "info"
  LOG_FORMAT: "json"
```

Step 2 names the descriptor file and the override list. It does not paste the descriptor.

| Category   | Descriptor field                      | Filename token |
|------------|---------------------------------------|----------------|
| Deployment | `deployParameterSets`                 | `deploy`       |
| End-to-end | `e2eParameterSets`                    | `pipeline`     |
| Technical  | `technicalConfigurationParameterSets` | `runtime`      |

Descriptor overrides merge before ParameterSet processing. Primitive references append without duplicates.
Instance-specific references are attached later. The shared name does not repeat an environment-specific prefix.
The recipe then says to release the artifact, delete the same keys from the instance files already listed,
and rerun the check. Exact line and column positions stay in the finding locations.
Keep literal dotted keys distinct from nested paths.
Withhold a delete instruction for anchored occurrences and for a physical source selected outside the proposal.
A blocked deletion adds one Cleanup Review line for that file.
Whole-file relocation is proposed only when every participant agrees.
A named exception stays under `Keep as they are:`.
Unresolved template associations and unsupported Application end-to-end scope stop before the release and delete steps.
See [Template Override](/docs/features/template-override.md) and
[ParameterSet processing](/scripts/build_env/build_env.py).

Unresolved, conditional, malformed, linked, or external context retains the grouped observation and an explanation.
Inherited `overrides-parent` entries require the parent context before a safe attachment can be proposed.
Optional template context does not alter candidate eligibility or suppress independent checks.
The default Application structure has no `e2eParameters` field. Application-scoped end-to-end observations
show the grouped values without a descriptor attachment.

HTML shows unique source files with expandable exact positions for grouped findings.
JSON retains every source position and stores the recommendation in `fix_suggestion` with its existing six fields.
Relocation proposals also use this field. Other checks retain their instance-only source resolution,
so INT-2 can report Review for a binding whose file exists only in a template artifact.

## Incomplete inputs

A failed read of a selected ParameterSet, Cloud Passport, or environment definition is recorded as a
located `Check skipped:` entry. PLACE-12 still compares environments whose selected inputs were read.
Independent rules continue. See the
[input error algorithm](/modules/envgene-linter/docs/algorithms/input-errors.md).

Within a comparable group, missing, invalid, unavailable, or unrendered selected ParameterSets block the group.
The located skip names every selected ParameterSet reference that failed that read.
Supported documents are untagged mappings with optional mapping `parameters` and optional list `applications`.
Each application must be an untagged mapping with a literal nonempty identity and an untagged parameter mapping.
Null or absent top-level bags follow the existing empty-bag interpretation.

An explicit passport reference that matches no file does not block the group. PLACE-12 still compares that
environment and excludes only the standard contract keys.
An ambiguous explicit passport reference, unreadable selected passport, or selected Jinja passport
blocks the group. Record a located skip at the affected environment definition.
When no passport is selected and resolution reports no error, the standard passport key table remains sufficient.
An absent optional passport is not an error.

An incomplete template identity simply excludes that environment from grouping.
Normal exclusions, insufficient support, missing keys, and disagreements are not incomplete-check diagnostics.

## Examples

Two environments in one cluster use this literal identity and bind `logging-deploy` to the Cloud:

```yaml
envTemplate:
  name: "business"
  artifact: "example-env-templates:1.0.0"
  envSpecificParamsets:
    cloud:
      - "logging-deploy"
```

Each environment owns an `Inventory/parameters/logging-deploy.yml` file:

```yaml
name: "logging-deploy"
parameters:
  APP_LOG_LEVEL: "info"
```

PLACE-12 reports `APP_LOG_LEVEL` as Review with both locations and a count of two environments.
The author must decide whether it is a template default or an intentional instance choice.
Environments in different clusters can qualify too. PLACE-1 can also identify duplication within the cluster;
its recommendation concerns the cluster layer, while PLACE-12 asks for review against template consumers.

If a third bound environment uses `APP_LOG_LEVEL: "debug"`, or its selected bag is empty, this path is silent.
Three participants still require all three to agree. With four participants, three may share `info` while one
differs or lacks the key. The message then says 3 of 4 environments, and the recommendation names the exception.
An environment using another version of the same artifact joins the group. Its selected inputs and values
participate in the same completeness and agreement checks.
Different filenames can contribute when their selected scopes and parameter paths agree.

## Limits

The check inspects one instance repository and its available selected inputs. Optional local template context
compares source definitions. The check does not download or render the template, prove effective defaults,
discover remote consumers, or combine instance repositories.
Equal artifact names do not prove identical template contents or default compatibility across versions and builds.
Distinct source entries establish repeated authorship. Copied configurations can still qualify.
Same-cluster agreement can reflect a shared cluster dependency; even cross-cluster agreement does not prove
independent design decisions or a universal default.

The exact-identifier exclusion does not recognize every cluster dependency, address, business meaning, or secret.
The shared secret-name heuristic also has limits. Review every candidate before changing configuration.
PLACE-1 and PLACE-2 retain their separate layer-placement and removal meanings.

## Related documentation

- [Standard](/docs/configuration-standard.md#place-12---shared-defaults-belong-in-the-template-should)
- [Specification and design](/modules/envgene-linter/docs/superpowers/specs/2026-11-05-place12-design.md)
- [Effective Set](/modules/envgene-linter/docs/algorithms/effective-set.md)
- [Authored source scope](/modules/envgene-linter/docs/algorithms/source-scope.md)
- [Implementation](/modules/envgene-linter/src/envgene_linter/rules/place12.py)
- [Tests](/modules/envgene-linter/tests/test_place12.py)
- [Guidance implementation](/modules/envgene-linter/src/envgene_linter/template_default_guidance.py)
- [Local context design](/modules/envgene-linter/docs/superpowers/specs/2026-11-06-place12-template-report-design.md)
- [Local context implementation](/modules/envgene-linter/src/envgene_linter/template_context.py)
- [Local context tests](/modules/envgene-linter/tests/test_template_context.py)
- [Artifact grouping design](/modules/envgene-linter/docs/superpowers/specs/2026-11-09-place12-artifact-name-design.md)
- [Guidance tests](/modules/envgene-linter/tests/test_template_default_guidance.py)
- [Runnable examples](/modules/envgene-linter/testdata/rules/place12)

- [Merge and cleanup design](/modules/envgene-linter/docs/superpowers/specs/2026-11-13-place12-merge-cleanup-design.md)

- [Reference resolution design](/modules/envgene-linter/docs/superpowers/specs/2026-11-13-place12-reference-resolution-design.md)
