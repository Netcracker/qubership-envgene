# Object-model reference

How to write an object-model reference under `docs/`. An object-model reference defines the EnvGene objects
and configuration files: the fields of each, which are mandatory, and what each one means. It is a lookup
register in the Diataxis Reference quadrant - a reader looks up a field, not a procedure.

- [Object-model reference](#object-model-reference)
  - [What an object-model reference is](#what-an-object-model-reference-is)
  - [Canonical shape](#canonical-shape)
  - [The annotated-YAML field dictionary](#the-annotated-yaml-field-dictionary)
  - [The marker vocabulary](#the-marker-vocabulary)
  - [Prose subsections that add rules](#prose-subsections-that-add-rules)
  - [Distinct from a feature doc](#distinct-from-a-feature-doc)
  - [Target length](#target-length)

## What an object-model reference is

An object-model reference lives at the top level of `docs/` and sits in the Diataxis Reference quadrant. The
two real exemplars are [`envgene-objects.md`](/docs/envgene-objects.md), which defines every EnvGene object,
and [`envgene-configs.md`](/docs/envgene-configs.md), which defines the configuration files. Each presents a
catalog of objects, one per heading, with the fields of the object as an annotated YAML block.

The reader has an object or a file in hand and needs to know its fields - which exist, which are required,
and what each does. The reference answers that lookup. It does not walk the reader through doing anything -
that goes to a how-to, which the object entry cross-links.

## Canonical shape

The document is a two-level taxonomy carried as nested headings: a repository-or-grouping level as `##`, an
object-category level as `###`, and one object per `####`. Mined from
[`envgene-objects.md`](/docs/envgene-objects.md), the real heading tree reads:

```markdown
# EnvGene Objects

## Template Repository Objects
### Environment Template Objects
#### Template Descriptor
#### Tenant Template
#### Cloud Template
#### Namespace Template
#### Template ParameterSet
...
## Instance Repository Objects
### Environment Instance Objects
#### Tenant
#### Cloud
#### Namespace
...
## Discovery Repository Objects
```

[`envgene-configs.md`](/docs/envgene-configs.md) is the same form keyed by file rather than object - one `##`
per configuration file (`## env_definition.yml`, `## config.yml`), with the field dictionary directly under
it:

```markdown
# EnvGene Configuration

## `env_definition.yml`
### File resolution for shared entities
## `config.yml`
## Deprecated
### `registry.yml`
```

The grouping headings (`## Template Repository Objects`, `### Environment Template Objects`) carry a short
orienting paragraph naming what the group is. The object headings carry the field dictionary.

## The annotated-YAML field dictionary

The core convention is the annotated YAML block: the object's fields are written as a YAML skeleton where
every field carries, on the lines directly above it, a marker comment and a one-line description of what the
field is. Mined verbatim from the Template ParameterSet entry in
[`envgene-objects.md`](/docs/envgene-objects.md):

```yaml
# Optional
# Deprecated
version: string
# Mandatory
# The name of the Parameter Set
# Used to reference the Parameter Set in templates
# Must match the Parameter Set filename
name: string
# Mandatory
# Key-value pairs of parameters
# The actual parameters that will be set when this Parameter Set is referenced
parameters: hashmap
```

The value slot holds the type (`string`, `hashmap`, a nested structure), not a sample value. A separate
`**Example:**` block below the dictionary shows a real filled-in instance, and the entry closes with a
cross-link to the JSON schema (`[ParameterSet JSON schema](/schemas/paramset.schema.json)`) and to any
sibling object that shares the schema. Keep the field dictionary and the worked example as two blocks - the
dictionary defines the fields, the example shows them in use.

`envgene-configs.md` applies the same annotation to a live config file rather than a type skeleton - the
`## config.yml` block carries real keys with `# Optional. Default value - ...` comments describing each.

## The marker vocabulary

Each field is marked with exactly one requirement word on its own comment line above the field. The vocabulary
the real docs use:

- `# Mandatory` - the field must be present.
- `# Optional` - the field may be omitted. Where a default applies, the config exemplar writes
  `# Optional. Default value - true` on the same line.
- `# Deprecated` - the field is retained for compatibility and should not be used in new objects. It stacks
  with the requirement marker (a deprecated-but-still-optional field carries both `# Optional` and
  `# Deprecated`).

State the marker on every field. A field with no marker is a gap - the reader cannot tell whether it is
required. Do not invent new marker words. Use the three above, matched to how the sibling entries mark their
fields.

## Prose subsections that add rules

An object entry stays a field dictionary, but where a rule governs more than one field or more than one
object, it is lifted into a prose subsection next to the dictionary rather than crammed into a field comment.
[`envgene-configs.md`](/docs/envgene-configs.md) does this with
[`### File resolution for shared entities`](/docs/envgene-configs.md#file-resolution-for-shared-entities): a
short paragraph states the priority-ordered search rule, then one small table per entity type lists the
search paths with a Priority and Status column. Use a prose subsection when the rule is a resolution order, a
cross-field invariant, or a shared-entity lookup that no single field comment can hold. Keep it declarative -
it states the rule, it does not narrate how the resolver walks the paths.

## Distinct from a feature doc

An object-model reference states what an object's fields are. A [feature doc](/.apm/skills/writing-docs/references/feature.md)
explains what a capability does and why. The border is the "why": a reference carries no rationale narrative -
it is a lookup register. When an entry starts explaining why the object exists or how a capability built on it
behaves, that explanation belongs in the feature doc, cross-linked, and the reference keeps only the field
definitions. The sibling confusion is with the [parameter catalog](/.apm/skills/writing-docs/references/parameter-catalog.md)
and the [macro catalog](/.apm/skills/writing-docs/references/macro-catalog.md): those are keyed by a
launch parameter or a template macro and use a flat per-entry label template, while an object-model reference
is keyed by an object or file and uses the annotated-YAML field dictionary.

## Target length

These are among the largest docs in the repository, because they catalog the whole object model:
[`envgene-objects.md`](/docs/envgene-objects.md) is about 3000 lines and
[`envgene-configs.md`](/docs/envgene-configs.md) about 610. Length here comes from breadth of coverage, one
entry per object, not from any single entry running long. A single entry that grows well past its siblings is
usually absorbing a how-to or a feature explanation that should be its own document and cross-linked. See
[One document, one job](/.apm/skills/writing-docs/references/doc-structure.md#one-document-one-job).
