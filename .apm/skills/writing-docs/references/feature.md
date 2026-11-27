# Feature doc

How to write a feature doc under `docs/features/`. A feature doc explains one distinct functional
capability of EnvGene to someone who uses it: what the feature does, why it exists, and how it
behaves, in implementation-independent terms.

- [Feature doc](#feature-doc)
  - [What a feature doc is](#what-a-feature-doc-is)
  - [Canonical shape](#canonical-shape)
  - [Legacy shape, not the canon](#legacy-shape-not-the-canon)
  - [Validation rule sections](#validation-rule-sections)
  - [Observable behavior over implementation detail](#observable-behavior-over-implementation-detail)
  - [Distinct from a technical-design doc](#distinct-from-a-technical-design-doc)
  - [Target length](#target-length)

## What a feature doc is

A feature doc lives in `docs/features/` and sits in the Diataxis Explanation quadrant. The repository's
own house rules for the directory are in [`docs/features/README.md`](/docs/features/README.md): each
document describes a distinct functional capability - a complete, self-contained functionality that can
be understood on its own - covering what the feature does and why it exists, and how it works. For
step-by-step execution the reader goes to a how-to or a use case, which the feature doc cross-links.

The reader is someone who uses EnvGene. The feature doc tells them how the capability behaves so they can
rely on it, not how it is wired inside.

## Canonical shape

The canonical form is the newer prose form. Open with a `## Description` (or `## Overview`) section that
states what the feature is and why it exists in plain declarative language, carry the behavior in topic
sections named for what they explain, and close with a `## See also` or `## Related documentation`
section that routes to the how-to, the reference, and the deeper design.

Mined from [`blue-green-deployment.md`](/docs/features/blue-green-deployment.md), the skeleton reads:

```markdown
# Blue-Green Deployment

## Description
## Why EnvGene supports Blue-Green
## What a BG environment looks like
## Two kinds of work on a BG environment
## Lifecycle in plain terms
## What state files tell you
## Where to read next
```

[`resource-profile.md`](/docs/features/resource-profile.md) is the same form with an `## Overview`
opener and a `## Related documentation` close:

```markdown
# Resource profiles

## Overview
## Three-level hierarchy
## Environment generation: combining overrides
## Effective Set calculation: resolving the profile
## Resolving dot notation
## Related documentation
```

The behavior sections are declarative - they describe the system as it is, named for the thing they
explain ("What state files tell you", "Baseline resolution within the active side"), not for a document
mechanic. The closing routing section is a table ("Where to read next" in `blue-green-deployment.md`) or
a list ("Related documentation" in `resource-profile.md`) that points out to doing, lookup, and design.

## Legacy shape, not the canon

An older feature-doc shape runs `## Problem Statement` -> `## Proposed Approach` -> `## Use Cases`, seen
in [`sbom.md`](/docs/features/sbom.md). Do not use it for new feature docs. It reads like a design or
proposal doc - it argues for a decision rather than describing a capability - and "It is proposed to..."
breaks the declarative-tone rule (see
[Declarative tone](/.apm/skills/writing-docs/references/doc-structure.md#declarative-tone)). A new or
reworked feature doc uses the prose form above: state what the feature is, not what was once proposed.

## Validation rule sections

When a feature doc documents semantic validation rules the system applies on top of schema validation,
group them by phase, state invariants declaratively, and factor out shared failure behavior into a single
note. The pattern:

1. **Open with a note that establishes shared context** - what schema validation already covers, the
   default failure behavior (fail vs warn), and the error-message contract. Do not repeat these in
   each rule.
2. **Group rules by phase** - each phase (a generation stage, an import operation, a runtime check)
   gets its own subsection.
3. **State invariants, not actions** - write what must be true. The reader infers the negative case.
4. **Name each rule** with a short bold noun-phrase followed by a period, then the explanation.
5. **Mark exceptions inline** - non-failure cases (warnings, deferred checks) are noted in the rule
   name itself.
6. **Cross-link, do not restate** - reference the canonical object definitions and field semantics
   rather than duplicating them.

❌ **INCORRECT:**

- Describing the validator's actions ("The validator iterates over...", "The check runs after...")
  instead of the invariant.
- Repeating "If this fails, generation stops with an error" in every rule.
- Listing field constraints already documented in the object schema.
- Mixing rules across phases in one undifferentiated list.

✅ **CORRECT:**

- "Every X of type Y has a Z field referencing a known W." (invariant form)
- A single note block at the top of the section describing the default failure behavior and the
  error-message contract.
- Cross-link to the object definition for field semantics.
- Subsections per phase ("During X generation", "During Y import").

**Scope:** Applies to new and modified content only.

**Why:** Declarative invariants are easier to scan and harder to misinterpret than procedural
descriptions of validator behavior. Phase grouping helps readers locate rules relevant to the operation
they care about. Shared failure semantics factored out reduces noise and prevents inconsistencies between
rules.

## Observable behavior over implementation detail

A feature doc foregrounds observable behavior - what users, downstream tools, or consuming systems can
rely on. Internal mechanism - phases, ordering of components, runtime fallback paths - is worth including
when it is part of what readers depend on. Otherwise the observable outcome often communicates more
clearly.

A useful self-check: would a reasonable alternative implementation that produces the same outcome
invalidate this paragraph? If yes, the mechanism is load-bearing - keep it. If no, the observable outcome
alone may carry the message.

❌ **INCORRECT** (when mechanism is not load-bearing):

- Describing the sequence of internal components (step 1: X reads file. Step 2: Y exports value).
- Naming runtime phases that have no user-visible meaning.

✅ **CORRECT:**

- Stating the observable outcome (the value is available to downstream consumer Y).
- Documenting mechanism only when it is part of the commitment (timing, atomicity, ordering).

**Scope:** Applies to new and modified content only.

**Why:** Implementation choices evolve faster than the observables they deliver. Documenting mechanism
that is not load-bearing forces stale doc updates with every implementation change.

## Distinct from a technical-design doc

The border between a feature doc and a
[technical-design doc](/.apm/skills/writing-docs/references/technical-design.md) is a deterministic
test. A feature doc describes observable behavior and why, for someone who uses EnvGene, and is
implementation-independent: a different internal implementation with the same observable outcome would
not force a rewrite. If a different implementation would force a rewrite, the content is a technical-design
doc, and it belongs under `docs/technical-design/`, cross-linked.

A feature doc must not carry a step I/O contract. Naming the inputs a pipeline step reads, the stage it
runs in, and the exact files it emits ties the doc to one implementation - change the wiring and the doc
is wrong, which is the technical-design test failing. The fused docs are the anti-pattern:
[`effective-set-generation.md`](/docs/features/effective-set-generation.md) carries `## Inputs` and
`## Pipeline Stage`, and [`clean.md`](/docs/features/clean.md) carries `## Emitted output`. That contract
belongs in a technical-design step doc (for example the
[`generate_effective_set` step](/docs/technical-design/instance-pipeline/steps/generate-effective-set.md)),
with the feature doc cross-linking to it and keeping only the observable, implementation-independent
behavior.

## Target length

Mined from the real feature docs, the range is roughly 100 to 340 lines of Markdown:
[`sbom.md`](/docs/features/sbom.md) is about 110 lines,
[`effective-set-generation.md`](/docs/features/effective-set-generation.md) about 165,
[`blue-green-deployment.md`](/docs/features/blue-green-deployment.md) about 280, and
[`resource-profile.md`](/docs/features/resource-profile.md) about 340. A feature doc that grows well past
this is usually fusing two jobs or absorbing a how-to, reference, or step contract that should be its own
document and cross-linked. See
[One document, one job](/.apm/skills/writing-docs/references/doc-structure.md#one-document-one-job).
