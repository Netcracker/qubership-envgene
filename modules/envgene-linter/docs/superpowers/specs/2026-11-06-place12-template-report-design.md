# PLACE-12 template report design

- [Intent and approach](#intent-and-approach)
- [Report contract](#report-contract)
- [Local template context](#local-template-context)
- [Verification](#verification)

## Intent and approach

PLACE-12 recommendations help a maintainer review repeated instance values as possible template defaults.
One finding groups common values from the same selected ParameterSet sources, template identity, and parameter scope.
The scope includes the association target, category, and application.
The [artifact grouping design](/modules/envgene-linter/docs/superpowers/specs/2026-11-09-place12-artifact-name-design.md)
defines comparison by template name and artifact name, ignoring artifact versions.

The user approved grouped recommendations based on the local template repository conventions.
The implementation uses an explicit `--template-repo PATH` option for local source inspection.
Automatic filesystem discovery would make the selected source unclear.
Rendering Jinja or downloading an artifact would exceed the static review contract.

## Report contract

- Keep all PLACE-12 eligibility, source ownership, completeness, and sensitive-value guards.
- Group by the ordered participant and effective ParameterSet reference identities.
- Preserve every qualifying source position in JSON and expandable HTML details.
- Keep one YAML example per group, actual values, scalar types, literal dotted keys, and nested mappings.
- Keep Information / Review and the six existing JSON fields. Do not restore `type`.
- Show the environment count in issue messages without the cluster count.
- Show a short explanation when the template destination cannot be established.
- Propose readable, globally unused ParameterSet names. Reserve names across the entire check.
- Keep application-scoped end-to-end findings as observations without an unsupported descriptor attachment.
- Never edit source configurations, render templates, access the network, or publish customer data.

## Local template context

The optional input accepts a repository root containing `templates/` or that directory itself.
Resolve descriptor extensions in generator order: `.yml.j2`, `.yaml.j2`, `.yml`, and `.yaml`.
Reject path traversal and symbolic links. Parse ordinary YAML with the existing bounded parser.
Read only the unconditional YAML prefix before the first Jinja statement when inspecting source definitions.
Such prefix definitions are evidence of source content, not a claim about the rendered result.

Resolve literal `{{ templates_dir }}` paths without evaluating Jinja.
Match Namespace targets by literal `deploy_postfix`, then the renderer filename rule.
The renderer removes `.yml.j2` and `.yaml.j2`. Other suffixes remain in the fallback association target.
Reserve local ParameterSet names from `.json`, `.yml`, `.yaml`, and `.j2` inputs, including standalone Jinja files.
For inherited entries without a local path, report the `overrides-parent` location and unresolved parent context.
Do not invent the parent's effective ParameterSet list.

Recommendations create a distinct ParameterSet and attach it through the selected descriptor entry.
Preserve `template_path`, selectors, existing override fields, and reference order.
Show only the relevant Cloud or Namespace entry. Explain how to merge the displayed fragment.
Name the existing descriptor entry and the exact `template_override` ParameterSet list to update.
Tell the reader to append the proposed reference last and create the override list if absent.
Explain that later ParameterSets take precedence and environment-specific ParameterSets are applied afterwards.
The instance ParameterSet reference remains unchanged, so the new template reference has a different name.

For each shared key, list matching local ParameterSet or object definitions
with source positions and comparison status.
Separate source definitions from effective defaults. Dynamic selection, Jinja, external parents,
and artifact equivalence
remain unverified. A local checkout does not prove that a published artifact, including a SNAPSHOT, has identical bytes.
Malformed, unavailable, ambiguous, or dynamic context keeps the grouped observation and a concrete uncertainty reason.

## Verification

Use synthetic fixtures for grouping, provenance, nested values, source selection, duplicate stems, traversal,
symbolic links, inherited entries, Jinja prefixes, malformed input, and optional CLI behavior.
Retain HTML escaping and the six-field JSON contract.
Verify placement instructions for Cloud and Namespace entries across all three parameter categories.
Keep the append instructions and existing reference order in both reports.
Build and inspect the package, then run the installed CLI on the selected local instance repository with explicit
template context. Customer examples and reports remain outside Git and the distribution.
