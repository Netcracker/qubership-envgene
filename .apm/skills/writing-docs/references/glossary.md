# Glossary

How to write the glossary under `docs/`. The glossary defines the repository's cross-document terms in one
place, one term per heading, each definition a sentence or two closing with a cross-link to the canonical doc.
It is the smallest, most mechanical reference type, in the Diataxis Reference quadrant.

- [Glossary](#glossary)
  - [What the glossary is](#what-the-glossary-is)
  - [Canonical shape](#canonical-shape)
  - [The per-term entry](#the-per-term-entry)
  - [Relationship to the define-every-term rule](#relationship-to-the-define-every-term-rule)
  - [Distinct from an object-model reference and a feature doc](#distinct-from-an-object-model-reference-and-a-feature-doc)

## What the glossary is

The glossary is the single file [`docs/glossary.md`](/docs/glossary.md), in the Diataxis Reference quadrant.
It holds the definitions of the terms that recur across EnvGene's documentation - one short definition per
term, each pointing to the doc that owns the full treatment.

The reader has met a term in another doc and needs its one-line meaning. The glossary gives it and routes them
to the canonical doc for more. It is a dispatch table of terms, not a place that teaches any one of them in
depth.

## Canonical shape

Mined from [`docs/glossary.md`](/docs/glossary.md), the skeleton is a one-line intro sentence then one `##`
per term:

```markdown
# Glossary

## Custom Params
## Deploy Postfix
## Environment
## Environment Inventory
## Environment Template
## Effective Set
## Namespace
## Environment Template Artifact
```

One term per heading, title-cased as the term is used in the docs. There is one definition per heading - a
term is defined once, not split across entries.

## The per-term entry

Each entry is one to three sentences and ends in a cross-link to the doc that owns the term. The definition
states what the term is in the reader's vocabulary, not how it is implemented. Mined verbatim from
[`docs/glossary.md`](/docs/glossary.md):

```markdown
## Deploy Postfix

A short identifier for a [Namespace](/docs/envgene-objects.md#namespace) role. Used in the Solution Descriptor. Typically matches the namespace folder name or template name.

## Effective Set

The complete set of parameters generated for a specific Environment, used by consumers (e.g., ArgoCD). See [Effective Set Structure](/docs/features/calculator-cli.md#version-20-effective-set-structure).
```

The cross-link is load-bearing, not decorative - it is the only route from the one-line meaning to the full
definition, and it is where every term that another doc defines points. Link the first mention of any other
glossary term or object inside a definition, so the glossary is navigable term to term. Keep the entry short -
if a definition needs a paragraph of explanation, that explanation lives in the canonical doc and the glossary
entry links to it.

## Relationship to the define-every-term rule

The `writing-style` integrity rule "define every term" requires each term to be defined on first use. The
glossary is where terms that cross documents are defined once and linked to, so a doc using a shared term can
link to the glossary rather than redefine it. A term local to one document is defined in that document. A term
that recurs across documents earns a glossary entry. When you add a cross-document term, add it here and point
the using docs at it rather than repeating the definition in each.

## Distinct from an object-model reference and a feature doc

The glossary defines a term in one or two sentences and dispatches to the canonical doc. An
[object-model reference](/.apm/skills/writing-docs/references/object-model-reference.md) defines an object's
fields in full with an annotated-YAML dictionary - the glossary entry for that object is a one-line gloss that
links to the reference, not a second copy of the field list. Against a
[feature doc](/.apm/skills/writing-docs/references/feature.md) the border is depth and the "why": the
glossary never explains why a thing exists or how it behaves - it names it and links out. Any explanation that
creeps into a glossary entry belongs in the canonical doc the entry points to.
