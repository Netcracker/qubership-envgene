# Rendering - the ladder into its forms

Phase 4 renders the grounded case list. The same list produces projections at different levels of
detail: collapsed-Gherkin acceptance criteria for a CR, full Cucumber scenarios for a `.feature` file,
and - when the caller is authoring an OpenSpec change - an OpenSpec delta spec. Render whichever the
caller asked for; standalone renders the CR acceptance and the Cucumber scenarios, and adds the OpenSpec
delta spec only when the caller asks for it. Because every form comes from one case list, a CR's
acceptance, the suite's scenarios, and the OpenSpec scenarios describe the same behavior and cannot drift.

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
- **The Given carries the complete triggering input set.** List every input the behavior is gated on -
  the flow selector, the toggles, the operation, and the discriminating fixture - so the scenario
  actually reaches the code path under test (see the trigger requirement in grounding). This is the
  minimal complete set, not a full environment dump: an input that changes neither reachability nor
  outcome stays implicit. A missing gating input makes the scenario pass vacuously, so treat it as a
  rendering defect, not a stylistic gap. When a flow needs a multi-step preamble - the modern-toolset
  deploy Given sets a pipeline type, an operation, application versions, and resolves the AppDefs and
  RegDefs - copy that preamble verbatim from the existing suite scenario that already runs that flow,
  rather than reconstructing it from memory; a partial preamble fails to reach the behavior exactly as
  a missing toggle does.
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

## OpenSpec delta spec (Requirement + WHEN/THEN)

Rendered when the caller is authoring an OpenSpec change (for example the envgene-analyst-authoring phase): the
grounded case list becomes delta specs in `openspec/changes/<id>/specs/<capability>/spec.md`. This is the
same behavior the collapsed-Gherkin acceptance states, projected into OpenSpec's requirement-and-scenario
shape so `openspec validate --strict` can check it and each scenario can become one test. Honor the same
grounding every other form does - every outcome observable, each independent failure its own scenario,
the discriminating precondition in the WHEN.

- Group the cases under `### Requirement: <behaviour name>` carrying a single SHALL statement that names
  the one behavior (keep it under about 500 characters). One requirement per behavior; several
  requirements when the change covers several behaviors.
- Under each requirement, write one `#### Scenario: <case name>` per independently-failing case, each
  with a `- **WHEN** <trigger and discriminating fixture>` line and a `- **THEN** <observable outcome>`
  line. The collapsed-Gherkin `Given <fixture>, <outcome>.` maps directly: the fixture and run mode
  become the WHEN, the observable outcome becomes the THEN. Keep every THEN on the grounded channel, as
  the acceptance and Cucumber forms do.
- Group the requirements under a delta header by how they change the capability's living spec:
  `## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements` (and `## RENAMED
  Requirements` when a name changes). A new capability's file opens with `## Purpose` - one or two
  sentences; a delta to an existing capability has no Purpose section.
- The capability name, the file path, and the New-versus-Modified decision are the caller's (for example
  a config rule such as "one capability per feature area"). This rendering fills the requirements and
  scenarios inside the file the caller names; it does not invent the capability taxonomy.

Example (the same case as the collapsed-Gherkin example above):

> ## ADDED Requirements
>
> ### Requirement: AppDef resolution checks both locations
>
> The pipeline SHALL resolve an AppDef from the instance root or from `configuration/`, and SHALL fail
> with an error naming the missing definition and both checked locations when neither holds it.
>
> #### Scenario: AppDef only under configuration
>
> - **WHEN** an AppDef is committed only under `configuration/` and none at the instance root
> - **THEN** the job fails with an error naming the missing definition and both checked locations

## Handling data that does not exist yet

- Paths and fixtures that already exist in the repository stay real, so the draft is paste-ready.
- Data that must be created appears as a `<placeholder>` in the angle-bracket style the suite uses, so
  it is obviously not yet real.
- A scenario expected to fail until an issue is fixed carries a comment naming the state: `@xfail(strict)
  with a link to #NNNN until the fix`. This is the same convention `bdd-test-review` uses when a
  divergence is resolved code-side.

## Annotating a correction to an existing family

When the render fixes or extends scenarios a reader already has - a filed CR, an existing family - show
the full corrected Given, not only the new lines, and mark each input you added or changed with a
trailing comment naming the step it triggers:

> ```gherkin
>   And the pipeline parameter "ENV_BUILDER" is set to "true"   # added: env build is skipped without
>                                                                # it under LEGACY, so the validation
>                                                                # under test never runs
> ```

The reader gets a paste-ready complete set and can see, line by line, what was missing and why. A bare
replacement that silently carries the fix hides the very gap the correction exists to close.

## When the feature has no test-suite integration yet

A subject area may have no way to reach it through the existing suite - a component that runs standalone
(a CLI invoked outside the pipeline) or a behavior with no pipeline entry point. Every step for it is a
new step. Do not hide this by rendering the scenarios as if they were paste-ready. Put them in a
separate Feature or scenario group, annotate each new step with `# NEW STEP NEEDED`, and open the group
with a comment that it is a stub pending step definitions. This tells the reader honestly that the cases
are designed but not yet runnable, which is more useful than a green-looking block that cannot execute.
Treat a file-absence or file-content assertion the same way when the suite has no step for it.

## Keep the forms in step

The acceptance line, the full scenario, and the OpenSpec scenario for one case must assert the same
channel. If rendering one form reveals that another would check a different observable, the case was
under-specified - go back and fix the case, not one rendering. The value of the ladder is that the
forms cannot drift, and that only holds if every form traces to the same grounded case.
