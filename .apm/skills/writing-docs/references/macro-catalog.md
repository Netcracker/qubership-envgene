# Macro catalog

How to write a macro catalog under `docs/`. A macro catalog lists the template macros of EnvGene, one entry
per macro, each stating what it resolves to, where its value comes from, and how to use it. It is a lookup
register in the Diataxis Reference quadrant.

- [Macro catalog](#macro-catalog)
  - [What a macro catalog is](#what-a-macro-catalog-is)
  - [Canonical shape](#canonical-shape)
  - [The resolution-scope preamble](#the-resolution-scope-preamble)
  - [The per-entry template](#the-per-entry-template)
  - [Distinct from a parameter catalog and a feature doc](#distinct-from-a-parameter-catalog-and-a-feature-doc)

## What a macro catalog is

A macro catalog lives at the top level of `docs/` and sits in the Diataxis Reference quadrant. The real
exemplar is [`template-macros.md`](/docs/template-macros.md). It catalogs the two macro families EnvGene
resolves in templates and parameters - the Jinja macros rendered at generation, and the calculator
command-line macros rendered at Effective Set time - one entry per macro.

The reader has a macro name or a value they need to produce and needs the macro's contract - what it resolves
to, its source, its type, and a usage snippet. The catalog answers that lookup. The workflow built on the
macro goes to a how-to or feature doc, cross-linked.

## Canonical shape

Mined from [`template-macros.md`](/docs/template-macros.md), the skeleton is a `## Macro resolution scope`
preamble, then one `##` per macro family, each holding one `### <macro>` per entry:

```markdown
# Template Macros

## Macro resolution scope

## Jinja Macros
### `templates_dir`
### `current_env.name`
### `current_env.tenant`
...

## Calculator command-line tool macros
### `APPLICATION_NAME`
### `NAMESPACE`
### `CLOUDNAME`
...
```

Each entry heading is the macro in backticks. The two families are the top-level grouping axis - a macro
belongs to exactly one.

## The resolution-scope preamble

The distinguishing section of a macro catalog is `## Macro resolution scope` at the top. It states, once for
the whole document, when and against what each macro family resolves - the rule a field comment in a parameter
catalog has no equivalent of. Mined from [`template-macros.md`](/docs/template-macros.md), it states that a
calculator `${...}` macro resolves at Effective Set time against a binding set by the parameter's level
(tenant, cloud, namespace, application) and its context (deploy, pipeline, runtime), that a parameter may
reference a macro from its own level or above but never below, and that a Jinja `{{ ... }}` macro resolves
once at generation against the full `current_env` with no level or context split.

Carry this preamble because the resolution rules are shared across every entry - stating them once at the top
keeps each entry from repeating the level-and-context contract. Each entry then notes only its own level.

## The per-entry template

Every entry follows the same label template. Mined from the `templates_dir` and `APPLICATION_NAME` entries in
[`template-macros.md`](/docs/template-macros.md), the real labels, in order:

- `**Description:**` - what the macro resolves to and where the value is sourced from (for example "Value is
  get from `name` of the Application object"). A level-scoped macro states its level here ("Application-level
  macro, can not be used on Tenant, Cloud and Namespace objects").
- `**Type:**` - the resolved value's type (`string`, `String`).
- `**Default Value:**` - the default, or `None`.
- `**Basic usage:**` - a one-line snippet showing the macro in a real field (`name: "{{current_env.name }}-oss"`).
- `**Usage in sample:**` - a link to a sample file under `docs/samples/` that uses the macro, or `TBD` when
  none exists yet.

An entry is separated from its heading by a `---` rule before the `**Description:**`, matching the real docs.
Keep the labels and order identical across entries so the reader scans the same slots in every macro.

## Distinct from a parameter catalog and a feature doc

A macro catalog is keyed by a template macro and opens with a resolution scope - the rule stating when and
against what the macro resolves. A [parameter catalog](/.apm/skills/writing-docs/references/parameter-catalog.md)
is keyed by a launch or pipeline parameter the operator passes to a run, and has no resolution-scope section.
The entry templates differ - the macro catalog uses `**Type:**` / `**Basic usage:**` / `**Usage in sample:**`,
the parameter catalog uses `**Default Value**` / `**Mandatory**`. The user has decided these are two separate
types - do not fold one into the other.

Against a [feature doc](/.apm/skills/writing-docs/references/feature.md) the border is the "why". A macro
catalog states each macro's contract with no rationale narrative - it is a lookup register. When an entry
starts explaining why a capability resolves the way it does end to end, that explanation belongs in the
feature doc, cross-linked.
