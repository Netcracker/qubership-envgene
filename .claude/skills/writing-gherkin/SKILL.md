---
name: writing-gherkin
description: >-
  Generate NEW acceptance criteria or Cucumber (Gherkin) scenarios for a qubership-envgene feature or
  change, before the tests exist. Use this whenever someone wants to enumerate the cases a behavior must
  satisfy: "draft gherkin for X", "write cucumber scenarios for this feature", "list the scenarios
  covering feature X", "acceptance criteria or conditions for a CR or issue #N", "turn this use case
  into test cases", or a request to cover the happy path plus each failure mode of some behavior,
  including a specific named failure like "cover the missing-at-root case" or "every way the merge can
  fail". The source can be a change request or issue, a subject area or topic, or a single feature or
  use-case doc. Produces both a collapsed acceptance-criteria list and full Given/When/Then scenarios.
  Do not trigger to grade or review scenarios that already exist (that is bdd-test-review), to file the
  CR issue itself (that is design-to-cr), to run or debug existing tests, or to write step definitions
  or other test code.
---

# writing-gherkin

Turn described behavior into checkable cases. The skill reads a source, enumerates the observable cases
the behavior must satisfy, grounds each case in an observable channel, and renders the cases as two
projections of one ladder: collapsed-Gherkin acceptance criteria and full Given/When/Then Cucumber
scenarios.

The skill produces the cases and their renderings. It does not judge scenarios that already exist, it
does not open the CR issue, and it does not write step definitions or golden files. Those are separate
jobs (see the boundary below).

## Why one ladder

A CR states acceptance criteria before code exists. A test suite needs full Cucumber scenarios after
code exists. When these are authored by two independent hands, they drift: the CR promises one set of
cases and the suite checks another. This skill enumerates the cases once, then renders the same case
list two ways, so the acceptance section of a CR and the scenarios in the suite stay the same behavior
described at two levels of detail.

## Boundary

| Skill                    | Its job                                             | Why not it                                            |
|--------------------------|-----------------------------------------------------|-------------------------------------------------------|
| `bdd-test-review`        | Validate and grade scenarios that already exist     | That reviews existing tests. This authors new cases.  |
| `design-to-cr`           | File the CR issue and write its body                | That publishes the issue. This only drafts the cases. |
| `writing-docs`           | Write the prose of docs, readmes, issues            | That is prose style. This is behavior enumeration.    |
| step definitions / code  | Implement the Gherkin steps in Python               | This authors scenarios, never their executable code.  |

## Trigger

Invoke explicitly, or when a consumer skill calls for case generation. Do not auto-fire on a request to
review existing tests, to file a CR, or to edit prose.

## Five phases

1. **Acquisition** - resolve the source into the material to read: the described behavior, its
   variations, and the observable channels it names. Read `references/acquisition.md` for the three
   input modes (CR, topic, doc file).
2. **Enumeration** - derive the case list: documented variations, the happy path per valid combination,
   and each independent failure mode. Read `references/enumeration.md`.
3. **Grounding** - attach each case to an observable channel and verify it, adapting to whether code
   exists yet. Cases with no channel are flagged, not rendered as fake tests. Read
   `references/grounding.md`.
4. **Rendering** - render the grounded case list as collapsed-Gherkin acceptance criteria and full
   Cucumber scenarios, reusing the suite's existing step vocabulary. Read `references/rendering.md`.
5. **Output** - present the case list, the two renderings, and the grounding report. Default to chat.
   On request, write a `.feature` draft under `cucumber_tests/features/` or a scratch draft under
   `stuff/`. Never commit or push without explicit confirmation.

## Input modes

| Mode      | Source                                                        | Status   |
|-----------|---------------------------------------------------------------|----------|
| CR        | A filed issue or a CR draft that carries a design reference   | live now |
| topic     | A subject area, resolved to the relevant docs and behavior    | live now |
| doc file  | A single `docs/features/*.md` or `docs/use-cases/*.md`        | live now |

The router in this file picks the mode. Phases 2 to 5 and the core reference files are input-agnostic.

## Reference files

| Phase or concern                          | File                            |
|-------------------------------------------|---------------------------------|
| Input handling per mode (phase 1)         | `references/acquisition.md`     |
| Case enumeration (phase 2)                | `references/enumeration.md`     |
| Observable-channel grounding (phase 3)    | `references/grounding.md`       |
| Ladder rendering to both forms (phase 4)  | `references/rendering.md`       |

## Output discipline

- Show the enumerated case list before rendering, so the boundaries are editable. A missed variation or
  an extra case changes every scenario downstream.
- Every rendered row traces to one enumerated case. No scenario appears without a case, and no grounded
  case is silently dropped.
- Flag ungroundable cases explicitly. A case with no observable channel cannot become an honest test.
- When running unattended - invoked by another skill or a batch run with no interactive user - list the
  corpus and the case list for the record and proceed, rather than blocking on a confirmation that will
  never come.
