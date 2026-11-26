# How-to guide

How to write a how-to guide under `docs/how-to/`. A how-to lists the recipe for one task a reader came to
do. It is goal-oriented and procedural: the reader already knows the domain and wants the steps, not the
theory.

- [How-to guide](#how-to-guide)
  - [What a how-to guide is](#what-a-how-to-guide-is)
  - [Canonical shape](#canonical-shape)
  - [Heading variation across the real docs](#heading-variation-across-the-real-docs)
  - [Multi-approach how-to guides](#multi-approach-how-to-guides)
  - [Distinct from a tutorial](#distinct-from-a-tutorial)
  - [Distinct from a feature doc](#distinct-from-a-feature-doc)
  - [Target length](#target-length)

## What a how-to guide is

A how-to guide lives in `docs/how-to/` and sits in the Diataxis How-to quadrant. It is goal-oriented and
practical: it solves one specific problem with minimal theory and maximum action. Write terse recipes for a
reader who knows the domain - omit filler steps such as "open the file". If a tutorial already covers the
topic, do not re-teach it end to end - link to it and cross-link.

The reader arrives with one task and wants the steps to finish it. Background and rationale go in the
feature doc, which the how-to cross-links.

## Canonical shape

The common shape across the real how-to guides is: a `## Description` opener, a `## Prerequisites` list,
numbered steps, a results section, and a closing routing section. Mined from
[`generate-effective-set.md`](/docs/how-to/generate-effective-set.md), the skeleton reads:

```markdown
# How to Generate an Effective Set

## Description
## Prerequisites
## Steps
### 1. Verify the Inventory Is Configured
### 2. Prepare the Solution Descriptor
### 3. Trigger the Pipeline
## Results
## Other Common Scenarios
```

The `## Description` states what the guide does and names the one task. `## Prerequisites` is a short list
of what must exist before the reader starts. The steps are numbered and named for the action they perform.
`## Results` states what exists when the run succeeds (files written, structure produced). A closing
routing section - `## Related documentation`, or `## Other Common Scenarios` as `generate-effective-set.md`
names it - points out to the feature doc, the reference, and neighboring how-tos.

## Heading variation across the real docs

The step container and the closing section vary across the real guides. Match the variant to the task,
but keep the Description-Prerequisites-Steps-Results-Related spine.

- [`generate-effective-set.md`](/docs/how-to/generate-effective-set.md) nests the steps under one
  `## Steps` heading as `### 1. ...`, `### 2. ...`, and closes with `## Results` then
  `## Other Common Scenarios`.
- [`blue-green-deployment-configure.md`](/docs/how-to/blue-green-deployment-configure.md) promotes each step
  to a top-level `## Step 1: Plan the topology` through `## Step 7: Validate the result`, and closes with
  `## Related documentation`. Use this form when the steps are long enough that nesting would bury them.
- [`split-cloud-passport-for-business-and-infra.md`](/docs/how-to/split-cloud-passport-for-business-and-infra.md)
  opens with `## Overview` and adds a `## When to use this pattern` and a `## Layout` section before
  `## Steps`, then closes with `## Result` and `## Related documentation`. Use the extra framing sections
  when the task is a pattern the reader must first recognize applies to them.
- [`credential-encryption.md`](/docs/how-to/credential-encryption.md) runs two sibling procedures under one
  file (`## How to enable Credential encryption` and `## How to Migrate from Fernet to SOPS`), each with its
  own `### Step N:` sequence. Two procedures in one file is the exception, not the spine - prefer one job per
  document (see [One document, one job](/.apm/skills/writing-docs/references/doc-structure.md#one-document-one-job)).

`## Description` and `## Overview` are interchangeable openers, and `## Results` and `## Result` are the same
closing section. Pick one and use it consistently within the doc.

## Multi-approach how-to guides

A how-to that presents several valid approaches to the same task must help the reader choose, not just list
recipes. Apply this pattern only when a how-to genuinely covers multiple approaches - it is not a universal
requirement for every how-to.
[`configure-resource-profiles.md`](/docs/how-to/configure-resource-profiles.md) is the real exemplar: it
opens with a shared `## How profiles resolve` section, then runs `## Scenario 1` through `## Scenario 7`,
each named for the reader's intent and led by a one-line **When to use:**.

When a how-to covers more than one approach:

1. Name each approach by the reader's goal so the table of contents itself becomes the decision index.
   Well-named approaches plus the one-line "When to use" below usually let a reader jump straight to the
   right one. Add a separate decision table only when the names alone cannot disambiguate the approaches.
2. Give each approach a one-line "When to use" that states the condition under which it is the right
   choice, not an explanation of how it works.
3. Mark the recommended approach and add a short NOTE flagging the common wrong path (the anti-pattern)
   so readers do not take it by default.
4. Keep deep rationale and trade-offs out of the how-to. Put the "why" in the feature (explanation) doc
   and cross-link it. The how-to stays action-oriented.
5. Put full, copyable example files under `docs/samples/` and reference them rather than inlining every
   approach's complete files, so the how-to stays within the target length.

❌ **INCORRECT:**

- A how-to that lists several approaches with steps but provides no guidance on which to pick.
- A how-to that embeds paragraphs of trade-off rationale inline next to each approach.

✅ **CORRECT:**

- Approaches named by goal so the table of contents is the decision index, with a separate table added
  only when names cannot disambiguate.
- Each approach has a one-line "When to use" and a marked recommended path.
- Rationale and trade-offs are cross-linked to the feature (explanation) doc, not inlined.

**Scope:** Applies to new and modified content only.

**Why:** When a task has several valid approaches, the reader's hardest step is choosing. A bare list of
recipes without guidance on which to pick fails them at that step. Keeping the trigger to one line and
moving rationale to the feature doc preserves the Diataxis separation of how-to from explanation and
keeps the guide within its target length.

## Distinct from a tutorial

The border against a [tutorial](/.apm/skills/writing-docs/references/tutorial.md) is who the reader is
and what the document does. A how-to assumes competence: the reader knows the domain and wants the recipe
for one task, so the steps are imperative and terse and carry no teaching. A tutorial teaches a newcomer
on one fixed scenario and narrates the why as it goes - it explains while doing. If the steps stop to teach
a concept the reader is assumed not to know, the content is tutorial material. Move it to the tutorial and
cross-link.

## Distinct from a feature doc

The border against a [feature doc](/.apm/skills/writing-docs/references/feature.md) is procedure versus
explanation. A how-to tells the reader to do steps, in imperative mood, to finish one task. A feature doc
never tells the reader to do steps - it explains what the capability does, why it exists, and how it
behaves. Rationale and trade-offs that creep into a how-to belong in the feature doc, cross-linked. A
how-to that spends paragraphs explaining why the system behaves a certain way is absorbing explanation that
should be a feature doc.

## Target length

Mined from the real how-to guides, the range is roughly 200 to 330 lines of Markdown. A single-task recipe
runs about 200 to 240 lines:
[`split-cloud-passport-for-business-and-infra.md`](/docs/how-to/split-cloud-passport-for-business-and-infra.md)
is about 206 lines, [`blue-green-deployment-configure.md`](/docs/how-to/blue-green-deployment-configure.md)
about 219, and [`generate-effective-set.md`](/docs/how-to/generate-effective-set.md) about 236. A
multi-approach guide runs longer - [`configure-resource-profiles.md`](/docs/how-to/configure-resource-profiles.md)
is about 330 lines across seven scenarios. The Diataxis target is `~200-400` lines. A how-to that grows well
past this is usually fusing two jobs or absorbing a tutorial or feature doc that should be its own document
and cross-linked. See
[One document, one job](/.apm/skills/writing-docs/references/doc-structure.md#one-document-one-job).
