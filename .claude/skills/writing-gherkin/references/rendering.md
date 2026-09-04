# Rendering - the ladder into two forms

Phase 4 renders the grounded case list. The same list produces two projections at different levels of
detail: collapsed-Gherkin acceptance criteria for a CR, and full Cucumber scenarios for a `.feature`
file. Render whichever the caller asked for, or both when running standalone. Because both come from one
case list, a CR's acceptance section and the suite's scenarios describe the same behavior.

## Acceptance criteria (collapsed Gherkin)

One line per case: `Given <discriminating fixture and mode>, <observable outcome through its channel>.`
The Given states the prepared on-disk state and any run or placement mode. The rest collapses When and
Then into a single observable-outcome clause. This is the notation `design-to-cr` consumes, so honor its
Acceptance rules:

- Make every outcome externally observable through the channel grounding verified. Prefer "the job fails
  with an error naming the missing definition and both checked locations" over internal state.
- Keep each line self-contained. Inline the observable contract. Do not link to a use case or a design
  section from inside an acceptance line.
- Put a sibling's discriminating precondition in the Given, so the outcome cannot be read as applying to
  the sibling.
- One line per independently-failing case. Do not fold a missing folder and a missing file into one.

Example:

> - Given an AppDef committed only under `configuration/` and none at the instance root, the job fails
>   with an error naming the missing definition and both checked locations.

## Cucumber scenarios (full Gherkin)

Full `Scenario` blocks with Given, When, Then. Match the existing suite exactly so drafts are
paste-ready, because a scenario that invents its own step vocabulary cannot run.

- **Reuse the suite's step vocabulary verbatim.** Read the existing `.feature` files and step
  definitions first, and phrase steps the way they already read: "the workspace is initialized with test
  data from ...", "the pipeline parameter ... is set to ...", "the unified pipeline orchestrator runs",
  "the orchestrator completes successfully", "the pipeline log contains ...". A new step is a last
  resort, and when one is unavoidable, call it out so a step definition can be written.
- **Name each scenario with its case.** Use the family's UC ID scheme, continuing the numbering. When
  proposing additions to an existing family, continue from the last used ID.
- **The Then asserts the grounded channel.** Every Then checks the observable channel from phase 3 - a
  log line, an error, an emitted request, a file or directory assertion. A scenario whose Then only
  restates the When is empty.
- **Negatives assert the failure point.** Write the Then so the failure is observed at the stage the
  case recorded, not merely that something failed.
- **Use Scenario Outline with an Examples table only when the fixture structure is identical across
  variants and only a literal value changes** - a place or mode that renames a scope but keeps the same
  setup. When variants need different fixtures (for example a different secret-store type with its own
  test data and reference shape), write separate scenarios. An Examples table over structurally
  different fixtures is superficial and hides the real setup.
- **Start each draft with a `# why:` comment** stating the case it covers, so any case ID can be found
  by search.

## Handling data that does not exist yet

- Paths and fixtures that already exist in the repository stay real, so the draft is paste-ready.
- Data that must be created appears as a `<placeholder>` in the angle-bracket style the suite uses, so
  it is obviously not yet real.
- A scenario expected to fail until an issue is fixed carries a comment naming the state: `@xfail(strict)
  with a link to #NNNN until the fix`. This is the same convention `bdd-test-review` uses when a
  divergence is resolved code-side.

## When the feature has no test-suite integration yet

A subject area may have no way to reach it through the existing suite - a component that runs standalone
(a CLI invoked outside the pipeline) or a behavior with no pipeline entry point. Every step for it is a
new step. Do not hide this by rendering the scenarios as if they were paste-ready. Put them in a
separate Feature or scenario group, annotate each new step with `# NEW STEP NEEDED`, and open the group
with a comment that it is a stub pending step definitions. This tells the reader honestly that the cases
are designed but not yet runnable, which is more useful than a green-looking block that cannot execute.
Treat a file-absence or file-content assertion the same way when the suite has no step for it.

## Keep the two forms in step

The acceptance line and the full scenario for one case must assert the same channel. If rendering an
acceptance line reveals that the full scenario would check a different observable, the case was
under-specified - go back and fix the case, not one rendering. The value of the ladder is that the two
forms cannot drift, and that only holds if both trace to the same grounded case.
