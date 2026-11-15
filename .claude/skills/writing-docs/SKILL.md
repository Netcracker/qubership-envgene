---
name: writing-docs
description: >-
  The document-authoring layer for this repository: how to structure and shape a documentation
  deliverable - a how-to, tutorial, feature doc, reference doc, technical-design doc, or README - on top of the
  `writing-style` house voice. Use this skill whenever you author or rework a document under `docs/` or a
  README: structuring it with Diataxis, placing each section in the right quadrant and its canonical home,
  adding a table of contents, callouts, or heading numbering, producing a validated object example, or
  building a copyable sample set under `docs/samples/`. For the voice of the prose itself - dashes,
  semicolons, line length, sentence-case headings, vocabulary, verified identifiers - read `writing-style`
  first. This skill builds on it for the document-level layer. Do not trigger for the body of an issue, CR,
  PR, ADR, proposal, or spec (that is prose, handled by `writing-style`), nor for pure code, config-value
  edits, debugging, or linter setup. The signal is authoring or reworking a document deliverable, not
  generic prose.
---

# writing-docs

This skill builds on `writing-style`. It is the catalog of standalone narrative and reference documents
under `docs/` - how to structure and shape each document type, on top of the house voice. It covers
Diataxis structure, document mechanics (tables of contents, callouts, heading numbering), validated object
examples, and copyable sample sets, plus a per-type reference for each document type in the catalog. The
rules live in reference files, each carrying the full rule with its rationale and examples. This file
routes you to the right one - open it before you write, do not work from memory.

Read `writing-style` first for the voice of any prose - dashes, semicolons, line length, sentence-case
headings, tables, link text, block-style YAML, vocabulary, and verified identifiers. Then read this skill
for the document-level layer when you are authoring a doc deliverable. The voice rules are not restated
here.

This skill is not everything written in the repository. It does not cover:

- The house voice itself - that is `writing-style`, the base layer this skill builds on.
- The flow-craft artifacts - an ADR is `writing-adrs`, a delta spec and its Gherkin are `writing-gherkin`,
  a change-request body is `design-to-cr`. They are a different category and are not in this catalog.
- Use cases - a deprecated document type, no longer authored. The catalog does not cover them.
- Test cases, analysis notes, and the configuration standard - out of scope for the catalog.

## Authoring flow

This flow is for standalone documentation work - a new doc or an edit made outside a change. Within a
change, documentation is the developer flow's documentation stage (`envgene-documentation`), which applies
this same catalog.

1. Frame it - name what prompts the doc (a gap, an edit, a capability that shipped) and who the reader is.
2. Pick the type - choose the document type from the catalog below and read its reference.
3. Gather and verify the facts - the factual source of truth is the code, the schemas, and the pipeline,
   not memory. Read them and confirm every identifier (parameter, field, macro, path) before you state it.
   The context (existing docs, the glossary, the change that prompted it) frames which doc to write and
   supplies the vocabulary. This is the `writing-style` "verify, don't fabricate" and "use existing
   vocabulary" rules applied as a step.
4. Draft to the shape in the voice - write to the chosen type's reference shape, in the `writing-style`
   house voice.
5. Finish checks - confirm the identifiers, run the pre-flight linters (`references/content-integrity.md`),
   cross-link, and update the index readmes.
6. Review - dispatch a subagent that applies `reviewing-docs` against the draft in a fresh context, the way
   a code change is reviewed by a reviewer subagent. Reuse `reviewing-docs` as the review craft - do not
   restate its rules here.

The factual input in step 3 is concrete per type family:

| Document type                                                        | Factual input                                                                        |
|----------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Object-model reference, parameter catalog, macro catalog, glossary   | the code and schemas - the fields, parameters, macros, and terms read from source    |
| Feature, technical-design                                            | the design decision and the observable behavior - the ADR or design plus how it acts |
| How-to, tutorial                                                     | a procedure or worked scenario run against the system                                |
| Policy/architecture note                                             | the standing policy or the architecture as it is                                     |

The voice is `writing-style`, the shape is this catalog, and the review is `reviewing-docs` - this section
is only the sequence that connects them for standalone work.

## Document-type catalog

Each standalone document under `docs/` is one of these nine types. Find the type, read its reference, and
write to that shape.

| Type                     | Job of the document                                               | Read                                 |
|--------------------------|-------------------------------------------------------------------|--------------------------------------|
| Feature                  | Explain one capability and why, for someone who uses EnvGene       | `references/feature.md`              |
| How-to                   | Walk a reader through one task they came to do                     | `references/how-to.md`               |
| Tutorial                 | Teach a beginner one capability end to end with a worked example   | `references/tutorial.md`             |
| Technical-design         | Specify the internal wiring - jobs, steps, I/O - for a developer   | `references/technical-design.md`     |
| Object-model reference   | Define an EnvGene object or config file: its fields and semantics  | `references/object-model-reference.md` |
| Parameter catalog        | List pipeline or config parameters with values and effect          | `references/parameter-catalog.md`    |
| Macro catalog            | List template macros with their inputs and output                  | `references/macro-catalog.md`        |
| Policy/architecture note | State a standing policy or classify a small architecture domain    | `references/policy-architecture-note.md` |
| Glossary                 | Define the repository's cross-document terms in one place          | `references/glossary.md`             |

## How to use this skill

Match the task to a reference file and read that file before writing. For any prose, read `writing-style`
first. Pick the document type from the catalog above and read its reference. Then add the cross-type files
below that fit the document-level job.

| Task                                                                       | Read                                 |
|----------------------------------------------------------------------------|--------------------------------------|
| Structure a document or shape its sections - Diataxis type, section value  | `references/doc-structure.md`        |
| Write a feature doc under `docs/features/`                                  | `references/feature.md`              |
| Write a how-to guide under `docs/how-to/`                                   | `references/how-to.md`               |
| Write a tutorial under `docs/tutorials/`                                    | `references/tutorial.md`             |
| Write a technical-design doc under `docs/technical-design/`                 | `references/technical-design.md`     |
| Define EnvGene objects or config files as an annotated-field register       | `references/object-model-reference.md` |
| List pipeline or repository parameters with values and effect               | `references/parameter-catalog.md`    |
| List template macros with their resolution scope and usage                  | `references/macro-catalog.md`        |
| State a standing policy or classify a small architecture domain             | `references/policy-architecture-note.md` |
| Define the repository's cross-document terms in one place                   | `references/glossary.md`             |
| Add document mechanics - table of contents, callouts, heading numbering    | `references/markdown.md`             |
| Keep docs truthful - internal-analysis wording, pre-flight linters, checks | `references/content-integrity.md`    |
| Write a YAML or JSON object example, or build a `docs/samples/` set         | `references/examples-and-samples.md` |

For a substantial new or reworked document you touch several of these. A typical feature doc needs the
`writing-style` voice, the feature-doc reference, document structure, document mechanics, content
integrity, and validated examples. Read each file whose column matches what you are about to write rather
than guessing the rule.

## Scope

Almost every rule applies to new and modified content only. When you edit an existing document, apply
the rules to the lines you add or rewrite. Do not reflow or restyle surrounding prose that you are not
otherwise changing - that produces large, noisy diffs unrelated to the task. Each reference file marks
the few rules that differ from this default.

## Reference files

- `references/doc-structure.md` - the Diataxis document types, the cross-type voice and structure rules
  that keep each section carrying only what it uniquely contributes, and keeping the index readmes current.
- `references/feature.md` - the feature-doc type under `docs/features/`: its canonical prose shape,
  validation-rule and observable-behavior rules, and the border against a technical-design doc.
- `references/how-to.md` - the how-to type under `docs/how-to/`: its canonical step shape, the heading
  variants, the multi-approach pattern, and the borders against a tutorial and a feature doc.
- `references/tutorial.md` - the tutorial type under `docs/tutorials/`: its canonical worked-example shape
  and the border against a how-to.
- `references/technical-design.md` - the technical-design type under `docs/technical-design/`: the step,
  flow, and sub-flow sub-shapes, and the border against a feature doc.
- `references/object-model-reference.md` - the object-model reference type (`envgene-objects.md`,
  `envgene-configs.md`): the annotated-YAML field dictionary, the mandatory/optional/deprecated markers, and
  the prose rule subsections.
- `references/parameter-catalog.md` - the parameter-catalog type (`instance-pipeline-parameters.md`,
  `envgene-repository-variables.md`): the recognised-parameters callout, the per-entry template, deprecated
  parameters, and the group-by-repository variant.
- `references/macro-catalog.md` - the macro-catalog type (`template-macros.md`): the resolution-scope
  preamble, the two macro families, and the per-entry template.
- `references/policy-architecture-note.md` - the lightest reference type (`credential-value-policy.md`,
  `deployment-architecture.md`): a standing policy or a small-domain classification with a decision table.
- `references/glossary.md` - the glossary (`docs/glossary.md`): one cross-linked definition per term and the
  tie to the define-every-term rule.
- `references/markdown.md` - document mechanics: tables of contents, callouts, heading numbering, heading
  renames and cross-links, and documentation file naming.
- `references/content-integrity.md` - keep internal-analysis wording out of user-facing docs, and run the
  pre-flight linters and final checks before a doc change is done.
- `references/examples-and-samples.md` - validated object examples inside docs, and copyable sample
  file sets under `docs/samples/`.
