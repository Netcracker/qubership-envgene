# Acquisition - the three input modes

Phase 1 resolves the source into three things the later phases need: the described behavior, its
variations, and the observable channels the behavior names. This file covers how each input mode gets
there. Phases 2 to 5 are the same regardless of mode.

Show the assembled material to the user before enumerating. A missed doc or an extra one changes which
cases come out, so the source boundary is worth confirming once.

## Mode: doc file

The source is a single `docs/features/*.md` or `docs/use-cases/*.md` path.

- A use-case doc is the richest source. Use cases are written as observable behavior that doubles as
  test-design input, so their steps already name outcomes and often the channel that carries them.
- A feature doc states the contract: the objects, the fields, the enum values, the behavior in each
  condition. Read the whole doc, not one section - a variation named in an early section often drives a
  failure mode described later.
- Collect the doc's cross-references. When the doc links a schema or another feature doc for a rule it
  relies on, that linked file is part of the material.

## Mode: topic

The source is a subject area, for example "external credentials" or "SBOM retention".

- Resolve the topic into a corpus the way `discrepancy-audit` does in its topic mode: fan out to gather
  the relevant feature docs, use-case docs, and schemas, then read them.
- A wide topic spans several docs. Gather candidates first, show the corpus, and let the user trim it
  before enumeration.
- The topic mode carries the most risk of missing a variation, because nothing scopes the behavior for
  you. Prefer a use-case doc as the spine when one exists, and treat the feature docs as the source of
  the variation axes.

## Mode: CR

The source is a filed issue or a CR draft that carries a design reference.

- A CR is pre-code by default: it describes behavior a developer has not built yet. This is the mode
  where grounding is truth-adaptive toward the design-named channel (see `references/grounding.md`).
- Read the CR body for the In scope items and any Covered cases, and read the linked design doc for the
  behavior and its channels. The CR's own Acceptance section, if present, is a starting case list to
  extend and ground, not a finished answer.
- A CR without a design reference is not ready for case generation. Say so and stop, the same way
  `design-to-cr` refuses a link-less CR. There is no addressable behavior to enumerate against.

## What phase 1 hands to phase 2

- The behavior statement: what the system does, in the source's own words.
- The variation axes: the dimensions the behavior varies along (action, place, mode, object shape).
- The named channels: every log line, error message, emitted request, or output file the source names
  as an observable effect. These seed grounding.
- Whether code exists yet: post-code (an implemented PR or a shipped feature) or pre-code (a CR for
  unbuilt behavior). This selects the grounding strategy.
