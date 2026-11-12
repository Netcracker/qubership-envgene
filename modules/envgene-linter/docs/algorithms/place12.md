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
   If any required input is unknown, record an incomplete check and withhold candidates for the whole group.

3. **Select participants for each scope.** Include every group environment with a nonempty binding list for
   the scope's target and category. An empty selected parameter bag still participates. For an application scope,
   a bound environment without that application bag still participates and prevents agreement on its keys.
   Environments without the target/category binding do not participate. Require at least two participants.
   Same-cluster participants remain eligible.

4. **Intersect leaf paths and compare values.** Every participant must supply the same leaf path.
   Missing keys, conflicting values, and unconfirmed comparisons block that path. A conflict within one cluster
   also blocks it; there is no majority vote. Other paths can still qualify.
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

Without `-t PATH` / `--template-repo PATH`, show the reconstructed values with the `<shared-paramset-name>` substitution slot.
Explain that the reader chooses an unused name and uses it for the ParameterSet file and reference.
Identify the named environment template and existing Cloud or Namespace association target.
Map the parameter category to its `template_override` ParameterSet list and show only the new item to append last.
Keep existing references and fields, and explain creation of missing override lists and Cloud string conversion.
Require publication and generation checks before removing only the shown duplicate entries.
Do not invent destination paths, list indices, or existing reference lists.
For unsupported Application end-to-end scope, retain its note and withhold attachment instructions.
With the option, inspect the explicit local repository root or `templates/` directory.
Prepend both absolute repository roots to complete, partial, and unresolved recommendations.
`environments/` source paths belong to the instance root. `templates/` paths belong to the template root.
For a `templates/` input, identify its parent as the template root without resolving linked sources.
CLI users can select the instance root with `-i` / `--instance-repo` instead of the positional argument.

First consider complete ParameterSet relocation with its existing name and Environment Inventory binding.
Require one environment-owned source per participant, equal complete payloads, and coverage of every source value
by the current eligible finding. Reject extra consumers or bindings, occupied destinations, unsupported fields,
and incomplete local context. Application parameters retain their container and scope.
Known primary, origin, and peer artifact consumers participate in the conflict check.
Physical-source aliases and existing template references block relocation.
Participants with unresolved role-specific destinations retain partial guidance.
Identical numeric versions are retained. Other versions are omitted with an explicit note about the deprecated field.
The report shows an absolute template destination with complete file YAML and lists absolute instance source paths.
It requires artifact publication and environment updates before source removal.
It shows each participant's complete reference list as an unchanged binding, rather than replacement YAML.
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
3. Reserve a readable filename such as `oss-common-deploy.yml`. Include `.json`, `.yml`, `.yaml`, and `.j2`
   ParameterSet inputs when checking occupied names. Avoid existing stems, instance references,
   selected template references, and other proposed names throughout this check. Use numeric suffixes for collisions.
4. Show the complete grouped ParameterSet and the selected descriptor entry as a merge fragment.
   Begin with `Template repository changes:` and show the absolute `Create file:` destination.
   Show `Edit file:` with the absolute descriptor path and loaded selected-entry line and column.
   Retain the exact selected entry path in `TemplateProposal.entry_path` and its source coordinates in `entry_position`.
   A Cloud entry uses `cloud`. A Namespace entry uses its actual zero-based list index, including indices after zero.
   Render the complete YAML path to the relevant override list.
   Require occurrence-specific coordinates at every selected path step.
   Anchored values or inherited keys without those coordinates retain the descriptor and entry selector as Review,
   with no create or edit action. This avoids directing an edit to a shared anchor definition or fallback position.
   Retain its path, selectors, and existing category override references. Append the new reference last.
   Name the existing Cloud or Namespace entry and the exact `template_override` list in the recommendation.
   Explain that the reader creates the override list if absent and appends the new reference after existing references.
   Keep unrelated descriptor entries and override fields. A Cloud path string becomes object form with the same path.
   An unresolved descriptor receives an absolute inspection path when known and no invented file action.
5. Keep source evidence distinct from effective defaults. Local checkout equivalence with the artifact,
   rendered Jinja values, external parents, and other consumers remain unverified.

For example, a local descriptor selects `oss.yml` for the `oss` association target.
A grouped deployment finding can propose `templates/parameters/oss-common-deploy.yml`:

```yaml
name: "oss-common-deploy"
parameters:
  APP_LOG_LEVEL: "info"
  LOG_FORMAT: "json"
```

Merge the following fragment into the selected Template Descriptor. Keep the other Namespace entries and fields:

```yaml
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/oss.yml"
    deploy_postfix: "oss"
    template_override:
      deployParameterSets:
        - "oss-common-deploy"
```

| Category   | Descriptor field                      | Filename suffix |
|------------|---------------------------------------|-----------------|
| Deployment | `deployParameterSets`                 | `deploy`        |
| End-to-end | `e2eParameterSets`                    | `pipeline`      |
| Technical  | `technicalConfigurationParameterSets` | `runtime`       |

Descriptor overrides merge before ParameterSet processing. Primitive references append without duplicates.
Instance-specific references are attached later. A distinct proposed name avoids repeating the instance reference.
Both reports explain that later ParameterSets take precedence and environment-specific ParameterSets keep priority.
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

The engine withholds PLACE-12 candidates whenever discovery reports selected ParameterSet, passport, or
instance-definition read failures that make merge inputs incomplete. Located `Check skipped:` entries remain
available in reports. Independent rules continue. See the
[input error algorithm](/modules/envgene-linter/docs/algorithms/input-errors.md).

Within a comparable group, missing, invalid, unavailable, or unrendered selected ParameterSets block the group.
Supported documents are untagged mappings with optional mapping `parameters` and optional list `applications`.
Each application must be an untagged mapping with a literal nonempty identity and an untagged parameter mapping.
Null or absent top-level bags follow the existing empty-bag interpretation.

A missing or ambiguous explicit passport reference, unreadable selected passport, or selected Jinja passport
also blocks the group. Record a located skip at the affected environment definition.
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
