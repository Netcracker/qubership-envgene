---
name: envgene-design
description: EnvGene override of the component-design slot. Runs after the propose gate and before plan, for every change - including one the upstream workspace handed off. Agrees the approach with the developer (2-3 approaches, one decision), defines the contracts the change exposes or consumes, and writes openspec/changes/<id>/component-design.md, the component's own design (HOW + Contracts + Constraints). A design.md the upstream workspace hands off is a read-only WHAT/HLD input, never the component design; this stage always writes component-design.md. Use when a change has its propose gate row.
---

# EnvGene design (override of component-design)

Replaces `component-design` in this repository. It runs after the propose gate, so the owner has already approved
WHAT changes. This slot decides HOW, and writes the component's own design artifact: `component-design.md`
(Approaches, Decision, Contracts, Constraints). Plan and implement read its result.

It runs for every change, including one the upstream workspace handed off. The upstream `design.md` is a read-only
WHAT/HLD input (context) - a separate file the component flow never edits; changes to it go back to the upstream
workspace. This stage always writes `component-design.md` from that input: it does not re-argue the WHAT or the ADR
options the upstream design settled - it settles HOW and defines the Contracts. For the team's own change there is no
upstream `design.md`; the stage writes `component-design.md` from `proposal.md`, the specs and the ADR.

## Entry check

- The ledger has the propose gate row (`gate: proposal approved by <owner> on MR !<n> @ <sha>`).
- `proposal.md`, `specs/` and `tasks.md` exist in `openspec/changes/<id>/`, and the ADR the change names exists under
  `docs/adr/` (or the proposal says the change has none).
- `openspec/changes/<id>/component-design.md` does not exist yet, or it is being revised in an open change. This
  stage always runs and writes `component-design.md`: for a hand-off it reads the upstream `design.md` as the read-only
  WHAT/HLD input, for the team's own change it starts from `proposal.md`, the specs and the ADR. It does not re-argue
  the WHAT or the ADR options already settled - it settles HOW and defines the Contracts. A hand-off runs design here;
  it does not skip to plan. The stage never edits the upstream `design.md`.

## Steps

1. **Read.** `proposal.md` (the HLD), the delta specs (the behavior contract, and the BDD scenarios) and the ADR under
   `docs/adr/` that the change names. The ADR holds the system-level options and their consequences; do not re-argue
   them without new facts. Then `tasks.md`. For a hand-off, read its `design.md` as the WHAT/HLD input (its
   approaches, decisions, contracts and open questions): build on it, do not re-argue its WHAT. Whatever it left to
   the component owner is a question to ask in step 3.
2. **Brainstorm.** Map the work-map of `proposal.md` to the components and code paths it touches, and find the path
   that handles each spec scenario. Read the code, do not guess. Turn each ADR consequence into a constraint. What the
   code does not settle is a question, not an assumption.
3. **Questions.** Ask the developer what the specs, the ADR and the code do not settle. Ask in one batch, not one by one.
4. **Approaches.** Propose 2-3 component-level approaches with trade-offs and a recommendation. Stop until the
   developer chooses.
5. **Decision.** Record the chosen approach and who chose it:
   `| <time> | design | - | - | approach <x> chosen by <developer>, <chat or MR> |`.
6. **Write `component-design.md`** from the design template `envgene-component/templates/design.md`:
   - Approaches, Decision, Out of Scope, Open Questions as in the template;
   - **Contracts:** one line per interface the change exposes or consumes, with an id (`C-1`, `C-2`, ...), and how the
     decision meets it. A contract without a line blocks plan;
   - **Constraints:** one line per rule of sections 2 to 5 of `.claude/skills/envgene-code-review/SKILL.md`.
7. **Scope check.** If the decision changes the scope, the set of tasks or a spec, stop: the change returns to the
   propose gate. A change that only refines the implementation may update `tasks.md` without a new approval.
8. **Validate.** `openspec validate <id> --strict --no-interactive; echo "exit=$?"`, then the row:

   ```text
   | <time> | design | `openspec validate <id> --strict --no-interactive` | <exit> | valid @ <sha> |
   ```

9. **Gate.** Commit `component-design.md` (with the developer's yes for commits), then append the gate row with the
   sha of that commit. The ledger rides along with the next commit.

   ```text
   | <time> | design | - | - | gate: approach <x> accepted by <developer> (component-design.md @ <sha>) |
   ```

## Rules

- The developer accepts the decision. The agent proposes and records it; it does not accept it for the developer.
- Ask for the developer's yes before commit, push or merge request.
- Do not put tokens, passwords or usernames in the design or the ledger.
</content>
