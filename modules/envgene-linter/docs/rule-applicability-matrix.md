# Rule applicability and coverage matrix

- [Scope and notation](#scope-and-notation)
- [Implemented rules](#implemented-rules)
  - [Placement](#placement)
  - [Secrets](#secrets)
  - [Integrity](#integrity)
  - [Naming](#naming)
  - [Values and templating](#values-and-templating)
- [Rules without an implementation](#rules-without-an-implementation)
- [Differences and open questions](#differences-and-open-questions)
- [Proposed applicability model](#proposed-applicability-model)
- [Recommended implementation order](#recommended-implementation-order)

## Scope and notation

Applicability follows the object's role and available context. A repository type alone does not determine which rules
apply. A template repository without `environments/` is valid.

This development assessment uses the local [configuration standard](/docs/configuration-standard.md) and working tree
on September 29, 2026. It includes the TPL-4 and TPL-6 implementations beyond released version 0.0.5.
The standard has 55 active rules. The linter registers 25 rules, including three disabled by default.
The remaining 30 rules have no registered implementation. NAME-5 is retired and excluded from both counts.
Registration does not imply complete coverage of a standard rule.

The instance column concerns authored inputs in an
[Instance Repository](/docs/glossary.md#instance-repository).
The template column concerns reusable [Environment Template](/docs/glossary.md#environment-template) sources and
their supporting objects. Object roles follow [EnvGene objects](/docs/envgene-objects.md).
A mixed repository contains both sets of objects, so both columns apply to their respective inputs.

| Applicability | Meaning                                                                                                                    |
|---------------|----------------------------------------------------------------------------------------------------------------------------|
| Local         | Relevant objects can be inspected within that repository. Dynamic values or missing dependencies can still limit coverage. |
| Context       | A useful conclusion needs consumers, composition, another layer, or an external contract.                                  |
| No            | The rule targets a role absent from ordinary authored inputs of this repository type.                                      |

These columns describe intended applicability, not implemented support. For example, a template repository with
instance fixtures also contains instance roles. Conversely, the absence of an optional object is not a violation.

In the assessed [engine](/modules/envgene-linter/src/envgene_linter/engine.py),
a template-only root runs **TPL-1, TPL-4, and TPL-6**.
Other enabled rules are reported as `Not applicable`. This is an implementation limitation, not a conclusion about
their applicability under the standard. In mixed roots, other rules retain their instance selection boundaries.
They do not automatically check every file under `templates/`.

The coverage column below describes that implementation. Rule links open the detailed algorithms.
Unless stated otherwise, instance checks use
[connected entities](/modules/envgene-linter/docs/algorithms/connections.md).
No findings therefore does not establish that every authored object was checked.

## Implemented rules

### Placement

| Rule                                                           | Instance | Template | Objects and required context                                                        | Implemented coverage and limits                                                                                                                                    |
|----------------------------------------------------------------|----------|----------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [PLACE-1](/modules/envgene-linter/docs/algorithms/place1.md)   | Context  | Context  | Values, their consumers, and shared authoring layers                                | Compares selected ParameterSet values across instance environments and clusters. No template layer or general Credential placement analysis.                       |
| [PLACE-2](/modules/envgene-linter/docs/algorithms/place2.md)   | Context  | Context  | Overrides and the values inherited through the applicable merge process             | Compares selected instance ParameterSets across repository, cluster, and environment. No comparison with template inputs.                                          |
| [PLACE-3](/modules/envgene-linter/docs/algorithms/place3.md)   | Context  | Context  | Parameters and whether they configure an application, platform, or physical cluster | Checks selected passport file placement only. Does not classify parameter consumers by system tier.                                                                |
| [PLACE-4](/modules/envgene-linter/docs/algorithms/place4.md)   | Local    | Local    | Parameter-bearing objects and the Cloud Passport contract                           | Checks contract keys in selected ParameterSets. Does not cover every other EnvGene object or template source.                                                      |
| [PLACE-6](/modules/envgene-linter/docs/algorithms/place6.md)   | Local    | Local    | Pipeline category and Cloud/Namespace association                                   | Checks resolved instance pipeline bindings against the `cloud` target. Template category arrays are not inspected.                                                 |
| [PLACE-7](/modules/envgene-linter/docs/algorithms/place7.md)   | Context  | Context  | ParameterSet references and the categories assigned by consumers                    | Checks selected instance references within each environment. No template composition or template category-array analysis.                                          |
| [PLACE-8](/modules/envgene-linter/docs/algorithms/place8.md)   | Local    | Local    | ParameterSets, Resource Profile Overrides, and Credential catalogs                  | Reviews connected empty entities only. Does not infer unrelated concerns from file size, names, or application count.                                              |
| [PLACE-9](/modules/envgene-linter/docs/algorithms/place9.md)   | Context  | No       | Cluster ownership, passport roles, lookup paths, and companions                     | Checks used passports, ambiguity, cardinality by role, and layout. Unused passports are outside selection.                                                         |
| [PLACE-10](/modules/envgene-linter/docs/algorithms/place10.md) | Local    | Local    | Authored entity type and its supported location                                     | Checks five connected entity types. Files whose misplaced location prevents discovery can remain unchecked. Template locations need their own object-role mapping. |

For PLACE-1 and PLACE-2, template composition and instance layer overrides are distinct processes.
Comparisons need the relevant process and provenance. Treating every parent template as an instance layer would
produce incorrect conclusions.

### Secrets

| Rule                                                     | Instance | Template | Objects and required context                                                     | Implemented coverage and limits                                                                                                                |
|----------------------------------------------------------|----------|----------|----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| [SEC-1](/modules/envgene-linter/docs/algorithms/sec1.md) | Local    | Local    | Parameter values and evidence that a value is a secret                           | Uses secret-name suffixes in connected ParameterSets and supported Cloud/Namespace objects. It is a heuristic, not general secret detection.   |
| [SEC-3](/modules/envgene-linter/docs/algorithms/sec3.md) | Local    | Local    | Runtime parameter bags and Credential references                                 | Detects supported Credential references in runtime inputs. Literal secret detection remains with SEC-1. Template runtime bags are not covered. |
| [SEC-4](/modules/envgene-linter/docs/algorithms/sec4.md) | Context  | Context  | Credential shape and the secret required by its consumer                         | Compares Credential IDs in recognized user/password parameter pairs. Does not validate Credential shape against the secret.                    |
| [SEC-5](/modules/envgene-linter/docs/algorithms/sec5.md) | Local    | Local    | Local Credential material, external references, and repository encryption policy | Reviews protection of selected secret candidates and supported sources. Does not establish repository-wide encryption or backend consistency.  |

SEC-5 is a `MAY` rule. Missing SOPS configuration alone must not become a violation.
An external-store-only repository, or one without local secret material, does not need repository-wide encryption.
Unknown secret semantics require review rather than a guessed shape or an automatic conversion.

### Integrity

| Rule                                                     | Instance | Template | Objects and required context                                           | Implemented coverage and limits                                                                                                                               |
|----------------------------------------------------------|----------|----------|------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [INT-2](/modules/envgene-linter/docs/algorithms/int2.md) | Context  | Context  | Typed references, lookup precedence, and available dependency catalogs | Checks supported connected references. Missing template context and dynamic references produce Review. It does not load a complete template dependency graph. |
| [INT-3](/modules/envgene-linter/docs/algorithms/int3.md) | Context  | No       | Used names across environment, cluster, and repository lookup scopes   | Reports supported names defined at multiple instance scopes. Template composition is not this override chain.                                                 |
| [INT-4](/modules/envgene-linter/docs/algorithms/int4.md) | Context  | Context  | Authored candidates and every available local or external consumer     | Reviews candidates with no reference found in available local sources, with uncertainty. Template-only catalogs are not scanned. No automatic deletion.       |

An unavailable external consumer is not evidence that a template entity is dead.
A dynamic reference is also not evidence that its target is missing.

### Naming

| Rule                                                       | Instance | Template | Objects and required context                                            | Implemented coverage and limits                                                                                                                                      |
|------------------------------------------------------------|----------|----------|-------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [NAME-1](/modules/envgene-linter/docs/algorithms/name1.md) | Context  | Context  | Parameter keys and the concepts their consumers assign to them          | Disabled by default. Reviews equal string values under different keys in connected ParameterSets. Equality does not establish an alias.                              |
| [NAME-2](/modules/envgene-linter/docs/algorithms/name2.md) | Local    | Local    | Filename and declared `name` of a named object                          | Checks selected ParameterSets and Artifact Definitions. Application and Registry Definitions are outside this implementation. Dynamic names need additional context. |
| [NAME-3](/modules/envgene-linter/docs/algorithms/name3.md) | Local    | Local    | Authored names, fixed layout names, and externally dictated identities  | Disabled by default. Reviews selected instance names using kebab-case matching. Fixed input filenames and identity exceptions need reconciliation with the standard. |
| [NAME-4](/modules/envgene-linter/docs/algorithms/name4.md) | Context  | Context  | ParameterSet subject, category, optional topology, and actual consumers | Disabled by default. Checks bound instance stems. Uses `technical` instead of `runtime` and rejects a suffix after the category.                                     |
| [NAME-8](/modules/envgene-linter/docs/algorithms/name8.md) | Local    | No       | Default Cloud Passport and its selected companion                       | Checks selected passport and companion stems. Excludes the exact infra role. Companion selection follows the generator's `.yml` lookup.                              |

### Values and templating

| Rule                                                     | Instance | Template | Objects and required context                                      | Implemented coverage and limits                                                                                                                                                     |
|----------------------------------------------------------|----------|----------|-------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [VAL-4](/modules/envgene-linter/docs/algorithms/val4.md) | Local    | Local    | Parameter values and any consumer requirement for encoded strings | Reviews JSON collections and YAML block collections encoded as strings in connected ParameterSets. Skips dynamic content. No template or general inline parameter-bag coverage.     |
| [TPL-1](/modules/envgene-linter/docs/algorithms/tpl1.md) | Local    | Local    | File role, Jinja delimiters, and supported descriptor fields      | Scans YAML and `.j2` under `templates/`, `environments/`, and `configuration/` without requiring connections. Allows documented descriptor fields and reviews ambiguous delimiters. |
| [TPL-4](/modules/envgene-linter/docs/algorithms/tpl4.md) | No       | Context  | Template references and presence guards                           | Reviews unprotected candidates locally without proving input availability.                                                                                                          |
| [TPL-6](/modules/envgene-linter/docs/algorithms/tpl6.md) | No       | Local    | Template statements, filters, and raw blocks                      | Checks local template sources and allows recognizable Helm passthrough.                                                                                                             |

TPL-1 accepts `.j2` regardless of directory and excludes YAML comments.
Its descriptor-field exceptions are an approved compatibility decision
for generator-supported syntax, including the documented namespace selector syntax.
They do not permit arbitrary Jinja in every descriptor field.
The descriptor exceptions refine the standard's shorter wording and need to remain explicit.

## Rules without an implementation

Every row in this section is unimplemented in both repository modes. Applicability is an assessment for future design,
not a claim that enabling an existing switch activates these checks.

| Rule     | Instance | Template | Objects and required context                                                                                        |
|----------|----------|----------|---------------------------------------------------------------------------------------------------------------------|
| PLACE-5  | Context  | Context  | Consumer contract and parameter category. A key prefix alone cannot establish the correct category.                 |
| PLACE-11 | Local    | Local    | Cloud and Namespace profile assignments, including whether a namespace is an appropriate target.                    |
| SEC-2    | Local    | Local    | All live Credential material and encryption markers. Distinguish secret values from placeholders.                   |
| INT-1    | Local    | Local    | Object type and schema. Unrendered Jinja needs source-aware validation or explicit render contexts.                 |
| INT-5    | Context  | Context  | Application and pipeline consumers. Absence from local configuration does not establish a dead parameter.           |
| NAME-6   | Context  | Context  | Credential purpose, role, and externally dictated IDs.                                                              |
| NAME-7   | Context  | Context  | Shared Template Variable files, purpose, and supported reference sites.                                             |
| NAME-9   | Local    | No       | Infra passport role, filename, companion, and explicit environment references.                                      |
| VAL-1    | Context  | Context  | Consumer type contracts, including application Helm `values.schema.json` where applicable.                          |
| VAL-2    | Context  | Context  | Reserved markers, mandatory-value contracts, and values supplied by later layers.                                   |
| VAL-3    | Local    | Local    | Literal URLs or analyzable URL expressions and documented consumer exceptions.                                      |
| VAL-5    | Local    | Local    | Resource Profile Override fields identified as Kubernetes CPU or memory quantities.                                 |
| VAL-6    | Local    | Local    | Profile `name` and `baseline` fields, with authored-source provenance for generated objects.                        |
| VAL-7    | Local    | Local    | Resource Profile Overrides with custom values and a declared baseline.                                              |
| VAL-8    | Context  | Context  | Instance merge mode, template override values, and both selected baselines. Template inputs alone are insufficient. |
| VAL-9    | Local    | No       | Instance `envSpecificResourceProfiles` entries and their required string shape.                                     |
| TPL-2    | Context  | Context  | Jinja pass-through expressions and the layer inputs that supply them.                                               |
| TPL-3    | Context  | Context  | Template defaults, genuine branching, and the applicable inheritance chain.                                         |
| TPL-5    | No       | Local    | Jinja presence guards on nested paths.                                                                              |
| TPL-7    | Context  | Context  | URL construction, passport host facts, and the originating template.                                                |
| TPL-8    | No       | Local    | Helm passthrough inside generator-rendered template sources.                                                        |
| TPL-9    | No       | Context  | Jinja branches, target YAML shape, and explicit render scenarios. Sample renders cannot prove all branches valid.   |
| TPL-10   | No       | Local    | Template literals and comments containing secret candidates.                                                        |
| TPL-11   | Context  | Context  | Derived values and generation context that already exposes them.                                                    |
| TPL-12   | Context  | Context  | Namespace identity, consumer context, and available macros.                                                         |
| TPL-13   | No       | Context  | Template conditions and application presence in resolved solution composition.                                      |
| TPL-14   | Context  | Context  | Namespace lookup, deploy-postfix, render order, and supported lookup mechanisms.                                    |
| TPL-15   | Context  | Context  | Expression semantics and equivalent macros available in the consumer context.                                       |
| TPL-16   | Local    | Local    | Macro scope and the parameter's deploy, pipeline, or runtime category.                                              |
| TPL-17   | Context  | Context  | Generated-file provenance and evidence of authored edits. Presence of generated files alone is insufficient.        |

## Differences and open questions

The following issues need explicit decisions before broader enforcement. This matrix does not change the standard or
the implementations.

| Item                | Difference or limitation                                                                                                                       | Required decision                                                                                          |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| Template execution  | The engine labels unsupported template checks `Not applicable`.                                                                                | Separate actual inapplicability from missing implementation.                                               |
| PLACE-3             | The standard concerns parameter placement by system tier. Code checks passport file placement.                                                 | Specify the semantic check and its evidence, and clarify overlap with PLACE-9.                             |
| PLACE-8             | Empty entities are only one part of the standard's single-concern requirement.                                                                 | Keep emptiness coverage explicit. Define review evidence for unrelated concerns without file-size guesses. |
| SEC-4               | Matching user/password reference IDs does not establish the required Credential shape.                                                         | Specify shape checks and consumer evidence. Decide where the existing pair-ID heuristic belongs.           |
| SEC-5               | Selected-source protection review differs from optional repository-wide encryption with one backend.                                           | Define policy-aware coverage without making optional SOPS use mandatory.                                   |
| NAME-3              | The standard exempts externally dictated names and protects exact reference identities. The heuristic still flags some fixed generator inputs. | Identify protected names and preserve reference identity before recommending renames.                      |
| NAME-4              | The standard permits `runtime` and an optional topology suffix. Code requires `technical` and a final category token.                          | Align the algorithm, specification, tests, and catalog before extending template coverage.                 |
| INT-3               | The standard describes first-match behavior for all listed entities. The linter documents ParameterSet merging.                                | Reconcile the explanation with generator behavior while retaining the agreed duplicate-name check.         |
| PLACE-10 and NAME-7 | PLACE-10 names `shared-template-variables/`, while NAME-7 describes legacy `configuration/variables/` locations.                               | Clarify canonical locations and supported legacy lookup by scope.                                          |
| NAME-8              | The standard permits `.yaml`, but companion lookup selects `.yml` only.                                                                        | Keep lookup compatibility explicit. Do not infer that an adjacent `.yaml` companion is selected.           |
| TPL-1               | Generator-supported descriptor expressions are accepted. YAML comments and `.j2` file placement are outside the rule's scope.                  | Preserve these approved refinements in the specification and standard alignment work.                      |
| TPL-6 and TPL-8     | TPL-6 forbids `raw`, while TPL-8 requires it for Helm passthrough.                                                                             | Approved: allow recognizable Helm passthrough and review other raw blocks. Preserve this refinement.       |
| TPL-14              | The target late-resolving macro is not yet available.                                                                                          | Check supported interim lookup behavior. Do not require the illustrative future macro syntax.              |
| Inline exceptions   | The standard defines `[EXCEPTION RULE-ID]` comments. The linter has no shared exception-handling mechanism.                                    | Specify how declared exceptions affect findings and coverage.                                              |

## Proposed applicability model

Evaluate every rule against discovered object roles. Repository detection supplies available inputs, while rule
prerequisites determine whether a check can run. This is a proposal, not an implemented API.

The shared context needs an object's type, authored or generated role, source location, category, references, and
available dependencies. Preserve source locations through template composition and instance merging separately.
Unknown dynamic values remain unknown. Do not invent rendering inputs to obtain a definitive result.

Report execution coverage separately from finding severity and action:

| Proposed status | Meaning                                                                                               |
|-----------------|-------------------------------------------------------------------------------------------------------|
| Checked         | The declared scope was evaluated with sufficient inputs. Findings can still exist.                    |
| Partial         | Some eligible inputs were evaluated, but identified dependencies or dynamic values remain unresolved. |
| Not applicable  | No objects with the rule's required role exist in the assessed scope.                                 |
| Not implemented | Eligible objects exist, but this rule or repository mode is unsupported.                              |
| Disabled        | Configuration explicitly disables the rule.                                                           |

Record the reason and affected scope for incomplete coverage. One rule can be checked for local static objects and
partial for other objects in the same repository. An empty findings list must not hide that distinction.
Unreadable inputs must remain visible as diagnostics rather than being counted as successfully checked.

For example, a template repository containing ordinary YAML ParameterSets has applicable NAME-2 and VAL-4 inputs.
Those checks are unimplemented for template-only roots in the assessed engine, not inapplicable.
The same repository without cluster passports has no inputs for NAME-8.
INT-4 can offer local reference evidence but cannot prove non-use by unavailable instance repositories.

## Recommended implementation order

1. Resolve the listed semantic differences and coverage terminology before reusing existing checks more broadly.
2. Introduce shared discovery of typed authored objects for instance, template, and mixed repositories.
   Keep generated objects distinguishable and retain their source provenance where available.
3. Extend local static checks first, including NAME-2, PLACE-4, PLACE-10, SEC-1, SEC-3, and VAL-4.
   Document each rule's exact object coverage instead of treating every YAML mapping as a ParameterSet.
4. Add template reference and composition context for PLACE-6, PLACE-7, INT-2, and INT-4.
   Preserve Information / Review for uncertain unreferenced candidates, with no automatic deletion.
5. Add cross-layer comparisons and checks that need consumer contracts or controlled render scenarios.

Each implementation change needs an English specification, design, algorithm, and tests for its supported roles.
Cover instance-only, template-only, and mixed roots, missing optional directories, unavailable dependencies,
dynamic inputs, and generated files. Missing `environments/` must remain valid for a template repository.
