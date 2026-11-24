---
name: envgene-design
description: EnvGene override of the component-design slot. Runs after the propose gate and before plan, for every change - including one the upstream workspace handed off. Brainstorms HOW with the developer, then agrees the approach (2-3 approaches, one decision), defines the contracts the change exposes or consumes, and writes openspec/changes/<id>/component-design.md, the component's own design (HOW + Contracts + Constraints). A design.md the upstream workspace hands off is a read-only WHAT/HLD input, never the component design; this stage always writes component-design.md. Use when a change has its propose gate row.
---

# EnvGene design (override of component-design)

Replaces `component-design` in this repository. It runs after the propose gate, so the owner has already approved
WHAT changes. This slot decides HOW, and writes the component's own design artifact: `component-design.md`
(Approaches, Decision, Contracts, Constraints). Plan and implement read its result.

It runs for every change, including one the upstream workspace handed off. The upstream `design.md` is a read-only
WHAT/HLD input (context) - a separate file the component flow never edits; changes to it go back to the upstream
workspace. This stage always writes `component-design.md` from that input: it does not re-argue the WHAT or the
options the upstream design settled - it settles HOW and defines the Contracts. For the team's own change there is no
upstream `design.md`; the stage writes `component-design.md` from `proposal.md` and the specs.

## Entry check

- The propose gate is passed (Gate rows of `envgene-orchestration/references/ledger.md`).
- `proposal.md`, `specs/` and `tasks.md` exist in `openspec/changes/<id>/`. The rationale of the change - the chosen
  approach, what it costs and what was rejected - is read from `proposal.md`; where the decision was taken in another
  repository, the proposal names its record by repository and id, and that record is read there, not copied here.
- `openspec/changes/<id>/component-design.md` does not exist yet, or it is being revised in an open change. This
  stage runs for every change whose work touches a contract or adds one: for a hand-off it reads the upstream
  `design.md` as the read-only WHAT/HLD input, for the team's own change it starts from `proposal.md` and the
  specs. It does not re-argue the WHAT or the options already settled - it settles HOW and defines the Contracts. A
  hand-off runs design here unless its class is the skip below; it never skips straight to plan. The stage never edits
  the upstream `design.md`.
- **Skip.** A bug fix whose work changes no contract and exposes no new interface to the component writes no
  `component-design.md`. Its gate is the row
  `| <time> | design | - | - | design: skipped, no contract change @ <sha> |`, and plan works from `tasks.md` and the
  failing test alone. A change that names a contract, a module boundary or a configuration key is not a skip: write the
  design. The one who decides the skip is the developer, and the row names them.

## Steps

1. **Read.** `proposal.md` (the WHY, the scope and the rationale of the decision), the delta specs (the behavior
   contract, and the BDD scenarios) and, when the proposal names a decision record of another repository, that record
   read there. They hold the system-level options and their consequences; do not re-argue
   them without new facts. Then `tasks.md`. For a hand-off, read its `design.md` as the WHAT/HLD input (its
   approaches, decisions, contracts and open questions): build on it, do not re-argue its WHAT. Whatever it left to
   the component owner is open for step 3; what it decided is a constraint there.
2. **Work map.** Before proposing an approach, write the Work map from the design template: one row
   per requirement or spec scenario, with its file or function in this repository, its status (`tracked`,
   `new-in-repo` or `not-in-repo`) and evidence from the repository. Verify `tracked` rows with `git ls-files` at the
   current commit; do not guess. If a named target is absent and belongs to a sibling repository, mark
   `not-in-repo`, stop design, and return the finding to propose/upstream as a wrong-target or component-split problem.
   Do not turn it into an approach. Once every row is `tracked` or `new-in-repo`, map the code paths that handle each
   spec scenario and turn each accepted cost and consequence, from the proposal or the upstream design, into a
   constraint. What the code does not settle is a question, not an
   assumption.
3. **Brainstorm - diverge on HOW.** With the developer, over what the inputs leave open: everything the proposal,
   the specs and an upstream `design.md` decided is a constraint, not an option. The method is adapted from
   the superpowers brainstorming skill (see Attribution):
   - Open questions before options: what the developer already has in mind, which code they want reused or left
     alone, and the anti-goals - what would make the implementation a failure even if every scenario passes
     (coupling, a migration, performance, a second way to do the same thing).
   - One question at a time. Prefer multiple choice when the developer is unsure; offer a concrete guess they can
     correct when they say "you decide".
   - Widen before narrowing: list every shape that could meet the specs and the contracts, including "change less",
     "reuse what exists" and "no new code". Do not judge them yet.
   - Play your understanding back in small chunks, and separate what the developer said from what you assume.
   - A behaviour question is not a HOW option: a parameter, an error path or a mode the specs do not settle, or a
     scenario the code shows is wrong (with the trace). Stop design and take it back to whoever wrote the specs - the
     analysis phase, the upstream workspace, or the team for its own change. A spec change re-opens the propose gate.

   Do not invoke a brainstorming skill as a live skill even if one is present: it brings its own approval gate and
   design document, which collide with the design gate and `component-design.md`.
4. **Converge.** Ask in one batch what is still unsettled. Then pick 2-3 component-level approaches from the
   brainstorm list, with trade-offs and a recommendation. Stop until the developer chooses.
5. **Decision.** Record the chosen approach and who chose it:
   `| <time> | design | - | - | approach <x> chosen by <developer>, <chat or MR> |`.
6. **Write `component-design.md`** from the design template `envgene-component/templates/design.md`:
   - Work map, Approaches, Decision, Out of Scope, Open Questions as in the template;
   - **Approaches** also lists each shape the brainstorm dropped, one line with the reason;
   - **Contracts:** one line per interface the change exposes or consumes, with an id (`C-1`, `C-2`, ...), and how the
     decision meets it. A contract without a line blocks plan;
   - **Constraints:** one line per constraint specific to this change (limits, formats, compatibility, values the
     code must keep). The team rules of `envgene-code-review` apply to every change and are not copied here.
7. **Scope check.** If the decision changes the scope, the set of tasks or a spec, stop: the change returns to the
   propose gate. A change that only refines the implementation may update `tasks.md` without a new approval.
8. **Validate.** `openspec validate <id> --strict --no-interactive; echo "exit=$?"`, then the row:

   ```text
   | <time> | design | `openspec validate <id> --strict --no-interactive` | <exit> | valid @ <sha> |
   ```

9. **Gate.** Commit `component-design.md` (with the developer's yes for commits), then append the design gate row
   with the sha of that commit (format: Gate rows of `envgene-orchestration/references/ledger.md`). The ledger rides
   along with the next commit.

## Rules

- The developer accepts the decision. The agent proposes and records it; it does not accept it for the developer.
- The general rules of `envgene-orchestration` (section Rules) apply.

## Attribution

The brainstorm step adapts the brainstorming method from obra/superpowers (MIT, Copyright (c) 2025 Jesse Vincent).
