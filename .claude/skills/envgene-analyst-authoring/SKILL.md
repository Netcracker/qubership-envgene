---
name: envgene-analyst-authoring
description: >-
  Run the analyst authoring phase for a qubership-envgene change: a thin orchestrator that sequences the
  authoring crafts over one settled exploration brief into a propose-ready hand-off - a committed change
  folder plus a hand-off pull request. Invoke it deliberately, by name, when an analyst is ready to author
  a whole change from a settled brief and carry it to the hand-off. It is a process entry point with real
  side effects - it drives sub-skills and ends in a commit and pull request behind a human gate - not a
  reactive helper, so it is not meant to auto-fire from ambient phrasing, and auto-firing it would
  double-trigger against the very crafts it applies. For a single artifact, work from its contract directly:
  the proposal and the specs follow the envgene-component schema's per-artifact instruction, served by
  `openspec instructions`. For the discovery that produces the brief, use
  envgene-explore. Never use it for
  developer-side work after the hand-off - the design, plan, implementation, verification, review,
  docs, or finish, which are envgene-design and the sibling dev-flow skills.
---

# envgene-analyst-authoring

The authoring phase of the analyst flow for a qubership-envgene change. It drives one change from a
settled exploration brief to a propose-ready hand-off - a committed change folder plus a hand-off pull
request - by running the discovery stage and then applying each authoring craft in turn. It owns the
sequencing and the gates. It does not do the craft work itself. Each craft lives in its own skill, and
this orchestrator points at it rather than restating it.

The whole phase rests on one discipline: every authoring craft renders its artifact from the single
exploration brief. The proposal and the delta specs are two projections of one source, so
they describe the same change at different levels of detail and cannot drift apart. This mirrors the
one-case-list-N-projections discipline used for scenarios, lifted one level up to the change itself. State
that source discipline to yourself as the spine of everything below - when
in doubt about what an artifact should say, go back to the brief, not to another artifact.

## Why this is a thin orchestrator

The contract and the crafts are already good at their jobs. The `envgene-component` schema's instructions,
served by openspec, frame the proposal and the specs and point to the crafts. Re-teaching any of that here
would be a second copy that drifts out of step with the
real source. The value this orchestrator adds is the sequencing, the single shared brief, and the two
human gates - not a restatement of the contract or the crafts.

## Build-alongside boundary

The analyst phase and the developer flow share one schema - `envgene-component` - because a change carries
one schema across its whole lifecycle. Under the agreed consolidation with the component owner, the analyst
authors the proposal and the specs, and their per-artifact instructions in `envgene-component` are the
shared authoring contract this phase renders from. Editing those two instruction fields was a coordinated
change, so no separate analyst schema exists any more.

What this phase must not touch: the developer-side artifacts of `envgene-component` - the `design` artifact and its
instruction - and the developer-side skills (`envgene-propose`,
`envgene-design`, `envgene-plan`, `envgene-implementation`, `envgene-verification`, `envgene-review`,
`envgene-documentation`, `envgene-finish`, `envgene-orchestration`). `envgene-propose` is now
gate-and-review only - it no longer authors the proposal or the specs, the analyst does, agreed with the
component owner. This phase produces a change folder plus a hand-off pull request that the developer-side
propose stage later gates and reviews - propose already has an entry for the team's own change. Name
propose only by its role at the boundary, and do not reach into how it works.

## Invoke versus apply

This phase works across two layers, and treats each deliberately.

- Read the contract from the schema through the tool. For the OpenSpec artifacts - the proposal and the
  specs - run `openspec instructions <artifact> --change <id>` to get the enriched instruction, after
  scaffolding with `openspec new change <id>` (the schema comes from `openspec/config.yaml`, which is
  `envgene-component`). The schema is where the proposal and spec contracts live, including the pointer to
  the voice and grounding crafts, so this phase does not restate those crafts.
- Invoke `envgene-explore` for stage 1. Its own brief-settled gate is the one this phase wants, so
  re-implementing it would duplicate a gate that already exists.

## The single source - the exploration brief

`envgene-explore` produces one exploration brief, and every stage below renders from it. The brief
carries these sections, and each one feeds a specific downstream stage:

- Problem / Why - feeds the proposal in stage 2.
- Current behavior (with provenance) - grounds the proposal and the specs.
- Intended behavior / cases - feeds the delta specs in stage 3.
- Decision + rejected alternatives - feeds the rationale the proposal carries in stage 2, and the design that
  the developer phase reads after the gate. No stage of this phase waits on a written decision record.
- Entities / contracts (optional) - a new object's structure feeds the delta specs as requirements in
  stage 3, and its schema encoding is an implement-time concern. It does not feed a hand-off design here.
- Open questions / provenance - the honest list of what is still unsettled and the sources the brief
  rests on.

A gap in the brief becomes a gap in every artifact at once, and a settled point in the brief keeps all
of them consistent. That is why stage 1 does not proceed until the brief is settled.

## Stages

Run these in order. The first and last are hard human gates. Everything between is rendering from the
brief.

Scale the work to the brief's Change class. An architectural change gets the full set of stages. A bounded
change keeps the proposal and the specs tight, with the short rationale of its decision inside the proposal.
The two human gates hold for every class.

### 1. Explore - settle the brief

Invoke `envgene-explore`. It runs its full interactive discovery and its own brief-settled gate, which is
the gate this stage wants. The output is the one exploration brief. If a settled brief already exists from
an earlier session - envgene-explore ran before - confirm it with the analyst and proceed, rather than
re-running discovery. Do not proceed to any authoring stage until the analyst has confirmed the brief is
settled - every stage below trusts it as settled, so an unconfirmed brief silently propagates its gaps.

The change id and the capability names are set here, not inherited. This phase claims the change id and
scaffolds the change by running `openspec new change <id>`, which creates `openspec/changes/<id>/` under the
schema named in `openspec/config.yaml` (envgene-component) - each artifact's template arrives with its
instruction in stages 2 and 3 - and the brief's Intended-behavior cases name the capabilities the delta
specs live under in stage 3. The authoring stages below use `<id>`
and `<capability>` as givens. The brief itself stays a working note, not a committed file - it feeds these
stages but is not part of the change folder.

### 2. Proposal - run openspec instructions and author per the result

Get the proposal contract by running `openspec instructions proposal --change <id>`, which returns the
enriched instruction - the schema's proposal instruction composed with the config rules and the template.
Author `openspec/changes/<id>/proposal.md` per that instruction, feeding the brief's Problem / Why and the
scope. The instruction already carries the work-map, the Capabilities, the sibling-link rule (references
point to the change's own siblings, the delta specs under `specs/`, not to an
external design doc), the voice, and the rule that acceptance lives in the specs, not here - so do not
restate them here.

### 3. Specs - run openspec instructions and author per the result

Get the spec contract by running `openspec instructions specs --change <id>`, which returns the enriched
instruction. Author each capability's `openspec/changes/<id>/specs/<capability>/spec.md` per that
instruction, feeding the brief's Intended-behavior cases. The instruction carries the delta-spec format and
the grounding - every outcome observable, each independent failure its own scenario, the discriminating
precondition in the WHEN - so do not restate them here. The result is a requirement and scenario pair per
case that `openspec validate --strict` can check and that can later become one test.

### 4. Decision record - optional, and not a hand-off artifact

The chosen approach, the force that drove it and the alternatives rejected are already carried by the proposal, and the
developer phase reads them from there. Nothing in this phase waits on a written decision record and no gate checks for
one. When the analyst wants a durable record of one single decision outside the change folder, apply `writing-adrs`: it
fills that craft's MADR skeleton and writes the result under `docs/adr/`, one decision per file, with its reason, its
rejected alternatives and the cost it accepts. The craft is a practice of its own, not a stage of the flow - a change
with no such file is complete, and do not manufacture a record for a change that had no alternatives.

### 5. Assemble and check

Place the artifacts and confirm the folder is propose-ready - the file-completeness checklist below,
resting on the brief the analyst settled at stage 1. The checklist:

- `openspec/changes/<id>/proposal.md` present.
- `openspec/changes/<id>/specs/<capability>/spec.md` present for every capability the proposal names.
- `tasks.md` present, every task naming its verification.

This is a completeness check, not a second review. The crafts already own the quality of each artifact.

### 6. Commit and hand-off pull request - on an explicit go-ahead only

Do nothing in this stage without the analyst saying so. The standing repo rule holds: never commit, push,
or open a pull request unless the person asks. On the explicit human go-ahead, run the hand-off against
GitHub:

- Create a feature branch off `main` - never commit to `main`.
- Commit the change folder. The paths are docs-only (`openspec/changes/<id>/`), so use a `docs:`-type
  message. A decision record written under `docs/adr/` rides in the same commit when the analyst wrote one.
- Open the pull request into `main` with `gh pr create` (the repo uses the `gh` CLI). The PR body states
  the problem and the decision, and links the delta specs.

This is the boundary where the analyst phase ends and the developer flow begins - the hand-off is what the
developer-side propose stage gates and reviews.

## Output to the developer flow

The hand-off is a change folder plus a pull request, and each artifact answers a specific developer-side
concern. Make each one legible on its own:

- `proposal.md` - what the component owner gates and approves at propose.
- the delta specs - the behavior contract the design must cover and that later becomes tests.
- the decision and its rejected alternatives - stated in the proposal's rationale, which is where the developer reads
  them; an optional record under `docs/adr/` is a separate practice, not something the hand-off promises.
- the capability paths - written the way `openspec list --specs` shows them.
- new terms the change introduces - added to `docs/glossary.md`, so the vocabulary lands where the
  developer and the reviewer look for it.

## Human gates are real

Two stages are hard checkpoints, and the rendering in between trusts both. The brief-settled gate at
stage 1 and the commit-and-pull-request gate at stage 6 are the only two places this phase waits for a
person. Never self-certify either. An unconfirmed brief feeds gaps into every artifact, and an
un-asked-for commit or pull request breaks the standing repo rule.

## Coming back from the developer flow

After the hand-off, the developer flow may find a gap the brief and the specs never settled - a parameter,
an error path, a mode. It returns to this phase with that one question. Decide it with the analyst, update
the affected artifact from the brief, and re-hand-off. Never let a downstream stage pick the plausible
answer on its own, because a silent answer leaks the brief's authority into code no one agreed to.

## Open seams

The consolidation settled two seams that used to live here, agreed with the component owner: the analyst
and the developer share the one `envgene-component` schema, and proposal and spec authoring has moved out
of `envgene-propose` into this phase - propose is now gate-and-review only. The remaining seams:

- The decision record is not an artifact of the flow: `writing-adrs` and `docs/adr/` stay a documentation practice of
  their own, and no hand-off is expected to carry one. A change whose decision was taken in another repository names
  that ADR in `proposal.md` by its repository and its id.
- `tasks.md` is authored here, from the schema's tasks template and `openspec instructions tasks`: the tracked tasks,
  each naming its verification. `envgene-propose` reviews it and never writes it, so a hand-off without `tasks.md` is
  not a hand-off. The set this phase hands off scales with the class of the change: `proposal.md`, `specs/` and
  `tasks.md` always, `design.md` with a feature whose HLD lives in this workspace.
- `component-design.md` is not produced here. The design phase writes it after the propose gate, from the proposal, the
  specs and the upstream `design.md`, and it defines the cross-component contracts itself. Whether a cross-component change needs
  anything from above before the design phase is an open seam. The parent-and-child decomposition case is out of
  scope for this phase.

## House style

The artifacts this phase produces are prose and specs this repository ships, so follow the `writing-style`
house voice. Each craft also carries its own house-style rules - honor those where they are stricter, and
this phase does not override them.

## Red flags

| Thought                                                    | Reality                                                                                                   |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| "The brief looks done, I'll author and commit in one pass" | The commit gate is separate from the brief gate. Author, show the result, then ask before committing.     |
| "They liked the brief, so the hand-off is approved"        | Approval covers what was shown. The commit and the PR need their own explicit yes.                        |
| "It is a tiny change, skip the brief"                      | A bounded change needs a settled brief too - a lighter one, never none.                                   |
| "A downstream gap is obvious, I will just answer it"       | Return it to the analyst with one question. A silent answer leaks the brief's authority.                  |
