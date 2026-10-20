# Rule coverage and repository support

- [Purpose and snapshot](#purpose-and-snapshot)
- [Repository support](#repository-support)
- [Implemented rules](#implemented-rules)
  - [Placement](#placement)
  - [Secrets](#secrets)
  - [Integrity](#integrity)
  - [Naming](#naming)
  - [Values](#values)
  - [Templating](#templating)
- [Report labels](#report-labels)
- [Approved policy decisions](#approved-policy-decisions)
- [Known limitations and open decisions](#known-limitations-and-open-decisions)
- [Rules without an implementation](#rules-without-an-implementation)
- [Proposed applicability model](#proposed-applicability-model)
- [Maintenance](#maintenance)

## Purpose and snapshot

Use this matrix to answer three questions about the EnvGene Linter command-line interface (CLI):
which rules exist, where they run, and which inputs they check.
Rule IDs refer to the [configuration standard](/docs/configuration-standard.md).
Each implemented rule links to its detailed algorithm.

The tables describe the source checkout assessed on October 16, 2026.
Installed packages can have different coverage. Check the package version against the
[changelog](/modules/envgene-linter/CHANGELOG.md).

The standard contains **55 active rules**. The CLI implements **25**, with **22 enabled by default** and three disabled.
The remaining **30 have no implementation**. Retired NAME-5 is excluded from these counts.
An implemented check covers the inputs listed below. Registration alone does not establish full standard coverage.

## Repository support

Repository terms follow the [Instance Repository](/docs/glossary.md#instance-repository) and
[Environment Template](/docs/glossary.md#environment-template) definitions.
The directory names below describe how the CLI selects its execution path.

| Root          | Directories                      | Execution                                                                                        |
|---------------|----------------------------------|--------------------------------------------------------------------------------------------------|
| Instance-only | `environments/`, no `templates/` | Enabled instance checks, TPL-1, and TPL-6 compatibility checks. TPL-4 has no template sources.   |
| Template-only | `templates/`, no `environments/` | TPL-1, TPL-4, and TPL-6. Other enabled rules receive the report label `Not applicable`.          |
| Mixed         | Both directories                 | Enabled instance checks plus the three template checks, each within its documented source scope. |

A template repository without `environments/` is valid. Missing optional directories do not create violations.
A root containing only `configuration/` does not meet the CLI's repository check.

For example, VAL-4 does not inspect `templates/parameters/example.yml` in a template-only repository.
The engine reports that rule as `Not applicable`.
Template ParameterSets are still relevant to the standard's requirement.
Adding an `environments/` directory does not make instance checks inspect every file under `templates/`.

Most instance rules inspect **connected sources**: files selected by supported references or generator associations.
The [connection algorithm](/modules/envgene-linter/docs/algorithms/connections.md) defines selection and precedence.
INT-4 also catalogs recognized unconnected candidates. TPL-1, TPL-4, and TPL-6 select sources without instance bindings.
The [object reference](/docs/envgene-objects.md) defines the object types named in the tables.

Connected ParameterSet selection includes `.yml`, `.yaml`, and `.json` files recursively under the supported
repository, cluster, and Inventory `parameters/` directories. INT-2, content rules, and Effective Set merging
share that selection. INT-4 uses the same enumeration for its separate authored analysis.

## Implemented rules

`On` and `Off` describe the build-time defaults in
[rule_config.py](/modules/envgene-linter/src/envgene_linter/rule_config.py).
Changing a flag requires rebuilding or reinstalling from the modified source.
The CLI has no per-run rule-selection flag.
Placement, secret, integrity, naming, and VAL-4 checks below use instance inputs.
The templating section describes the additional file scopes.

### Placement

| Rule                   | Default   | Implemented check                                                                         |
|------------------------|-----------|-------------------------------------------------------------------------------------------|
| [PLACE-1][place-1]     | On        | Compare selected ParameterSet values across environments and clusters.                    |
| [PLACE-2][place-2]     | On        | Confirm that removing a repeated value preserves all known local selected consumers.      |
| [PLACE-3][place-3]     | On        | Check selected Cloud Passport file placement.                                             |
| [PLACE-4][place-4]     | On        | Find Cloud Passport contract keys in selected ParameterSets.                              |
| [PLACE-6][place-6]     | On        | Check that resolved pipeline ParameterSet bindings target the Cloud.                      |
| [PLACE-7][place-7]     | On        | Find a selected ParameterSet reference used in multiple categories in one environment.    |
| [PLACE-8][place-8]     | On        | Review connected empty ParameterSets, Resource Profile Overrides, and Credential files.   |
| [PLACE-9][place-9]     | On        | Check used passport roles, ambiguity, cluster ownership, layout, and companions.          |
| [PLACE-10][place-10]   | On        | Check directories of five connected entity types.                                         |

PLACE-10 covers ParameterSets, Resource Profile Overrides, Shared Template Variables, shared Credentials,
and Cloud Passports.

PLACE-1 and PLACE-2 compare decoded YAML and JSON values with their scalar types intact.
PLACE-2 reports Fix only after confirming one independent source-entry removal.
Necessary overrides are silent. Missing, unrendered, or unsupported merge context receives Review.
The proof covers known local selected bindings, including shared and application-specific uses.
PLACE-1 does not simulate its proposed promotion or prove preservation for all consumers.

### Secrets

| Rule           | Default | Implemented check                                                                                    |
|----------------|---------|------------------------------------------------------------------------------------------------------|
| [SEC-1][sec-1] | On      | Find literal secret candidates by parameter name in selected ParameterSets and Cloud/Namespace bags. |
| [SEC-3][sec-3] | On      | Find Credential references in selected runtime parameter bags.                                       |
| [SEC-4][sec-4] | On      | Review different Credential IDs in recognized username/password parameter pairs.                     |
| [SEC-5][sec-5] | On      | Inspect protection of selected secret material and supported Credential sources.                     |

SEC-5 does not make SOPS configuration mandatory.

### Integrity

| Rule           | Default | Implemented check                                                                           |
|----------------|---------|---------------------------------------------------------------------------------------------|
| [INT-2][int-2] | On      | Resolve supported connected references using local sources and available catalogs.          |
| [INT-3][int-3] | On      | Find used shared Credential, profile, or Shared Template Variable names at multiple scopes. |
| [INT-4][int-4] | On      | Review authored candidates with no references found in available sources.                   |

### Naming

| Rule             | Default | Implemented check                                                                              |
|------------------|---------|------------------------------------------------------------------------------------------------|
| [NAME-1][name-1] | Off     | Review equal string values under different keys in connected ParameterSets.                    |
| [NAME-2][name-2] | On      | Compare filename stems with declared names in selected ParameterSets and Artifact Definitions. |
| [NAME-3][name-3] | Off     | Review kebab-case naming of selected instance files, directories, and namespaces.              |
| [NAME-4][name-4] | Off     | Review the subject/category naming pattern of bound instance ParameterSets.                    |
| [NAME-8][name-8] | On      | Check selected default passport and companion names in single-passport cluster contexts.       |

### Values

| Rule           | Default | Implemented check                                                                                 |
|----------------|---------|---------------------------------------------------------------------------------------------------|
| [VAL-4][val-4] | On      | Review JSON collections and YAML block collections encoded as strings in connected ParameterSets. |

### Templating

| Rule           | Default | Implemented check                                                                             |
|----------------|---------|-----------------------------------------------------------------------------------------------|
| [TPL-1][tpl-1] | On      | Check Jinja in YAML under templates/, environments/, and configuration/.                      |
| [TPL-4][tpl-4] | On      | Review potentially optional Jinja references without recognized presence protection.          |
| [TPL-6][tpl-6] | On      | Check Jinja statements, loop sources, and compatibility with the applicable EnvGene renderer. |

TPL-1 ignores YAML comments and accepts `.j2` files regardless of their directory.
Ordinary YAML environment template descriptors under `templates/env_templates/` select inputs for generation.
Their [supported fields](/modules/envgene-linter/docs/algorithms/tpl1.md#descriptor-fields) allow active Jinja.
TPL-4 and TPL-6 statement checks inspect `.j2` sources under `templates/` and values in those supported fields.
TPL-4 accounts for supported lookup rewrites and fields that the generator guarantees at the relevant rendering stage.

TPL-6 also checks potential legacy expressions in configuration YAML, including instance inputs.
Its [compatibility algorithm](/modules/envgene-linter/docs/algorithms/ansible-compatibility.md) distinguishes rendering stages.
Root `description_template*.yml` and `description_template*.yaml` files are excluded as build metadata.
The linter does not render templates, execute filters or lookups, or read external repositories.

## Report labels

Execution coverage and recommended action answer different questions.
`Fix` asks for a configuration change. `Review` asks for human assessment of the reported uncertainty.
Neither action performs automatic edits or states how much of the repository was inspected.

| Label or condition | Meaning in the CLI                                                                            |
|--------------------|-----------------------------------------------------------------------------------------------|
| Disabled           | The build-time flag is off. The rule and its findings are omitted from reports.               |
| Not applicable     | For a template-only root, the engine uses this label for unsupported enabled instance checks. |
| No findings        | No findings were produced within the checked scope. Unchecked sources can still exist.        |
| Incomplete checks  | HTML lists recorded skip notes. The console prints them to stderr.                            |

Structured YAML, JSON, and Jinja read or parser skips become located JSON Review entries beginning with `Check skipped:`.
Console and HTML display `Not applicable`.
JSON exports findings and structured skips, without execution-status records.
Some enumeration and unsupported-source notes have no structured JSON representation.
Recoverable source failures retain independent checks and fresh reports.
Incomplete merge inputs cannot confirm PLACE-1 promotion or PLACE-2 removal.
An empty JSON array therefore does not establish that every source was checked.
See the [report contract](/modules/envgene-linter/docs/algorithms/reports.md).

## Approved policy decisions

These decisions define CLI behavior where the standard's shorter wording differs or needs a narrower interpretation.

- INT-3 permits same-named ParameterSet fragments across scopes because generation can merge them.
   Its duplicate-name checks retain the three entity types listed in the matrix.
- PLACE-10 reports Shared Template Variable placement mismatches as Review with generator lookup guidance.
   Supported legacy lookup paths prevent treating every mismatch as a safe move.
- SEC-4 keeps different user/password Credential IDs as Review, allowing intentional separation.
- SEC-5 reports literal `data.username` in a `usernamePassword` Credential as Fix.
   Exact `envgeneNullValue` data values are ignored. Unknown expressions and Fernet values remain Review.
- NAME-8 suppresses naming findings when the consuming cluster context contains multiple ordinary YAML passports.
   Physical aliases count once. The exact `passport-infra` role is excluded.
   Companion lookup uses `.yml` paths, even though the standard also permits `.yaml`.
- TPL-1 permits generator-supported descriptor expressions and excludes YAML comments and `.j2` placement checks.
- TPL-6 permits built-in and custom filter syntax and all syntactically valid raw blocks.
   Unsupported or unconfirmed renderer compatibility receives Review.
   Compatibility processing that changes literal raw content also receives Review.

## Known limitations and open decisions

The matrix records supported scope. It does not certify every authored file or every standard requirement.
The following limits affect how you interpret a run:

- An incomplete ParameterSet directory scan or file/directory collision prevents connected source selection
   for the affected environments.
   INT-2 reports Review. Unavailable files retain their staged slots and cannot restore shadowed lower inputs.
   Reserved `from_template`, `from_origin_template`, and `from_peer_template` paths require template context
   and make the affected reference uncertain.
- Template composition, remote consumers, and inherited template inputs are not resolved as a complete dependency graph.
   An unknown consumer cannot establish that a source is unused. INT-4 retains Review without deletion advice.
- TPL-4 recognizes confirmed descriptor context guarantees. Full `.j2` sources have different generation stages.
   The remaining guaranteed-field contract needs clarification before extending exemptions.
- Existing source parsing has failure cases that abort a run instead of producing incomplete-check diagnostics.
   Coverage claims require a completed run and inspection of the available diagnostics.
- Inline `[EXCEPTION RULE-ID]` comments from the standard do not suppress findings.
   The CLI has no shared exception-handling mechanism.

The following standard requirements also need broader implementation or a policy decision:

| Rule     | Remaining requirement or decision                                                                                  |
|----------|--------------------------------------------------------------------------------------------------------------------|
| PLACE-3  | System-tier placement of parameters. The implementation checks passport file placement.                            |
| PLACE-8  | One concern per entity. The implementation reviews definite structural emptiness.                                  |
| PLACE-10 | Misplaced files whose location prevents discovery, plus template object locations.                                 |
| SEC-4    | Credential shape compared with the consumer contract, beyond the current pair-ID heuristic.                        |
| SEC-5    | Optional repository-wide encryption and backend policy, beyond selected-source protection checks.                  |
| NAME-2   | Application and Registry Definition coverage after establishing their local usage.                                 |
| NAME-3   | Exceptions for fixed generator inputs and externally dictated identities.                                          |
| NAME-4   | The standard permits runtime and an optional topology suffix. The code uses technical and rejects that suffix.     |
| TPL-1    | Ordinary Registry Definition Jinja policy and the supported versions of legacy resourceProfiles descriptor fields. |
| TPL-6    | Criteria for set and other uncertain statements. These retain Review.                                              |

## Rules without an implementation

Every rule below is absent from the CLI registry in both repository modes.
No configuration switch enables these checks. The requirement text summarizes the standard, not promised CLI behavior.
Future support depends on the object's role and available inputs, rather than repository type alone.

| Rule     | Check not implemented                                                              |
|----------|------------------------------------------------------------------------------------|
| PLACE-5  | Select the right parameter category from its consumer contract.                    |
| PLACE-11 | Assign resource profiles to namespaces rather than the Cloud.                      |
| SEC-2    | Detect mixed plaintext and encrypted secret material.                              |
| INT-1    | Validate typed objects against their schemas, accounting for unrendered templates. |
| INT-5    | Detect dead parameters using available application and pipeline consumers.         |
| NAME-6   | Check Credential ID names against their purpose.                                   |
| NAME-7   | Check Shared Template Variable names against their purpose.                        |
| NAME-9   | Check infra passport and companion names and explicit references.                  |
| VAL-1    | Check a value's YAML type against its consumer.                                    |
| VAL-2    | Validate reserved markers and mandatory-value semantics.                           |
| VAL-3    | Check trailing slashes in URLs and consumer exceptions.                            |
| VAL-5    | Check Kubernetes CPU and memory quantity forms.                                    |
| VAL-6    | Reject empty strings in the documented Resource Profile fields.                    |
| VAL-7    | Require a baseline when a Resource Profile Override contains custom values.        |
| VAL-8    | Require replace mode for baseline changes using template and instance inputs.      |
| VAL-9    | Check one Resource Profile Override string per instance binding key.               |
| TPL-2    | Detect Jinja plumbing that should use layer overrides.                             |
| TPL-3    | Distinguish legitimate template branching from defaults that belong on a layer.    |
| TPL-5    | Detect per-level presence guards on nested paths.                                  |
| TPL-7    | Check URL construction against Cloud Passport host facts.                          |
| TPL-8    | Require protection for Helm passthrough.                                           |
| TPL-9    | Check YAML validity across template branches and explicit render scenarios.        |
| TPL-10   | Detect secret candidates in template literals and comments.                        |
| TPL-11   | Detect hardcoded values already derivable from generation context.                 |
| TPL-12   | Check current-namespace references against supported macros.                       |
| TPL-13   | Check that application presence controls the relevant branches.                    |
| TPL-14   | Check namespace resolution by deploy-postfix and supported lookup mechanisms.      |
| TPL-15   | Detect Jinja expressions with an equivalent supported macro.                       |
| TPL-16   | Detect deploy-scope macros in pipeline or runtime parameters.                      |
| TPL-17   | Detect edits to generated output using source provenance.                          |

## Proposed applicability model

This section is a design proposal. The CLI does not expose these coverage statuses as a shared per-rule model.

| Proposed status | Meaning                                                                                   |
|-----------------|-------------------------------------------------------------------------------------------|
| Checked         | The declared input scope was evaluated. Findings can still exist.                         |
| Partial         | Some eligible inputs were checked. Identified dependencies or sources remain unavailable. |
| Not applicable  | No objects with the required role exist in the assessed scope.                            |
| Not implemented | Relevant objects exist, but the rule or repository mode is unsupported.                   |
| Disabled        | Configuration explicitly disables the rule.                                               |

For example, a template-only root containing ordinary ParameterSets would need NAME-2 coverage reported as
`Not implemented`, rather than the engine's `Not applicable` label.
A repository with no Cloud Passport objects has no passport naming inputs.
A single rule could be `Checked` for local objects and `Partial` for objects with unavailable dependencies.

## Maintenance

Update this matrix when a rule, default flag, repository execution path, or supported source scope changes.
Keep approved decisions separate from proposals and unresolved limits.
Validate rule counts against the [registry](/modules/envgene-linter/src/envgene_linter/rulemeta.py), defaults against
the build-time flags, and execution against the [engine](/modules/envgene-linter/src/envgene_linter/engine.py).
Use the linked algorithms for detailed behavior and the
[specification catalog](/modules/envgene-linter/docs/superpowers/specs/README.md) for requirements and design history.

[place-1]: /modules/envgene-linter/docs/algorithms/place1.md
[place-2]: /modules/envgene-linter/docs/algorithms/place2.md
[place-3]: /modules/envgene-linter/docs/algorithms/place3.md
[place-4]: /modules/envgene-linter/docs/algorithms/place4.md
[place-6]: /modules/envgene-linter/docs/algorithms/place6.md
[place-7]: /modules/envgene-linter/docs/algorithms/place7.md
[place-8]: /modules/envgene-linter/docs/algorithms/place8.md
[place-9]: /modules/envgene-linter/docs/algorithms/place9.md
[place-10]: /modules/envgene-linter/docs/algorithms/place10.md
[sec-1]: /modules/envgene-linter/docs/algorithms/sec1.md
[sec-3]: /modules/envgene-linter/docs/algorithms/sec3.md
[sec-4]: /modules/envgene-linter/docs/algorithms/sec4.md
[sec-5]: /modules/envgene-linter/docs/algorithms/sec5.md
[int-2]: /modules/envgene-linter/docs/algorithms/int2.md
[int-3]: /modules/envgene-linter/docs/algorithms/int3.md
[int-4]: /modules/envgene-linter/docs/algorithms/int4.md
[name-1]: /modules/envgene-linter/docs/algorithms/name1.md
[name-2]: /modules/envgene-linter/docs/algorithms/name2.md
[name-3]: /modules/envgene-linter/docs/algorithms/name3.md
[name-4]: /modules/envgene-linter/docs/algorithms/name4.md
[name-8]: /modules/envgene-linter/docs/algorithms/name8.md
[val-4]: /modules/envgene-linter/docs/algorithms/val4.md
[tpl-1]: /modules/envgene-linter/docs/algorithms/tpl1.md
[tpl-4]: /modules/envgene-linter/docs/algorithms/tpl4.md
[tpl-6]: /modules/envgene-linter/docs/algorithms/tpl6.md
