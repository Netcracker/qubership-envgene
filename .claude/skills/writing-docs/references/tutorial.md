# Tutorial

How to write a tutorial under `docs/tutorials/`. A tutorial teaches a newcomer one capability end to end on
one fixed scenario. It is learning-oriented: a complete worked example, narrated in a second-person
teaching voice that explains while it does.

- [Tutorial](#tutorial)
  - [What a tutorial is](#what-a-tutorial-is)
  - [Canonical shape](#canonical-shape)
  - [A divergent shape, not the canon](#a-divergent-shape-not-the-canon)
  - [Distinct from a how-to](#distinct-from-a-how-to)
  - [Target length](#target-length)

## What a tutorial is

A tutorial guide lives in `docs/tutorials/` and sits in the Diataxis Tutorial quadrant. It is
learning-oriented: a step-by-step, complete working example for a reader who is new to the capability. The
voice is second-person teaching ("By the end of this tutorial you will know how to...") and it explains
each move while making it, so the reader finishes with understanding, not just a finished task.

The reader is a beginner working one fixed scenario from start to end. They have not come for a specific
task of their own - they have come to learn how the capability works by doing one worked example.

## Canonical shape

The canonical form opens by naming what the reader will learn, states the prerequisites, fixes one concrete
scenario, walks numbered steps that build on each other with expected output shown inline, and closes with a
summary. Mined from [`effective-set.md`](/docs/tutorials/effective-set.md), the skeleton reads:

```markdown
# Tutorial: Understanding the Effective Set

## What You Will Learn
## Prerequisites
## Scenario
## Step 1: Understand What the Effective Set Is
## Step 2: Generate the Effective Set
...
## Step 8: Understand What Triggers a Regeneration
## Summary
```

[`resource-profiles.md`](/docs/tutorials/resource-profiles.md) is the same form with sub-steps: its steps
carry `### N.1`, `### N.2` subsections (for example `### 2.1 Create the override file`,
`### 2.2 Reference the profile in a Namespace template`) when one step has several parts.

The sections carry the teaching, not a contract:

- `## What You Will Learn` - a bullet list of the concrete skills the reader will hold at the end, each a
  verb phrase ("Generate the Effective Set with traceability enabled").
- `## Prerequisites` - what must exist and what the reader should already know before starting.
- `## Scenario` - one concrete, fixed example the whole tutorial works ("You manage a solution called BSS
  deployed to `prod-cluster/prod-01`..."). Every step uses this scenario, so values stay consistent.
- `## Step N: ...` - numbered steps that build on each other, named for what the reader does or learns.
  Show the expected output inline after the step so the reader confirms they are on track. Split a long
  step into `### N.1` sub-steps.
- `## Summary` - recaps what the reader traced, then a **Related documentation** list routing to the
  feature doc, the matching how-to, and the reference.

## A divergent shape, not the canon

[`envgene-null-value.md`](/docs/tutorials/envgene-null-value.md) keeps `## What you will learn`,
`## Prerequisites`, and `## Summary` but diverges in the middle: it runs `## Overview`,
`## Where validation happens`, and topic sections (`## Mandatory parameters in templates`,
`## Credentials placeholder`) with a `## Before / after example`, rather than one fixed scenario walked
through numbered steps. This reads closer to an explanation than a worked example. For a new tutorial use
the canonical numbered-step-on-one-scenario form from `effective-set.md` and `resource-profiles.md` - the
divergent shape is not the canon.

## Distinct from a how-to

The border against a [how-to guide](/.claude/skills/writing-docs/references/how-to.md) is the inverse of the
how-to's. A tutorial teaches understanding on one fixed scenario and narrates the why as it goes - it
explains while doing, for a reader who is new to the capability. A how-to assumes you already know the
domain and just lists the steps for one task you came to do, with no teaching. If the document stops
explaining and becomes a terse recipe for a competent reader, it is a how-to. If it teaches concepts on a
fixed example, it is a tutorial. The two often pair: a tutorial links to the how-to that performs the same
task tersely, and the how-to links back to the tutorial for the reader who needs to learn it first.

## Target length

Mined from the real tutorials, the range is roughly 260 to 470 lines of Markdown - these are the longest
coherent docs in the repository, because a worked example narrates every step. The divergent
[`envgene-null-value.md`](/docs/tutorials/envgene-null-value.md) is about 263 lines, while the canonical
[`resource-profiles.md`](/docs/tutorials/resource-profiles.md) is about 465 lines and
[`effective-set.md`](/docs/tutorials/effective-set.md) about 469. A tutorial longer than this is usually
teaching two capabilities and should split, each with its own scenario. See
[One document, one job](/.claude/skills/writing-docs/references/doc-structure.md#one-document-one-job).
