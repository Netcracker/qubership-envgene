---
name: envgene-design
description: EnvGene override of the component-design slot. Runs after the propose gate and before plan - agrees the approach for an approved change with the developer (2-3 approaches, one decision), covers every contract of the hand-off design.md, and writes openspec/changes/<id>/dev-design.md. Use when a change has its propose gate row and no dev design yet.
---

# EnvGene design (override of component-design)

Replaces `component-design` in this repository. It runs after the propose gate, so the owner has already approved
WHAT changes. This slot decides HOW, and plan and implement read its result.

## Entry check

- The ledger has the propose gate row (`gate: proposal approved by <owner> on MR !<n> @ <sha>`).
- `design.md` (hand-off), `specs/` and `tasks.md` exist in `openspec/changes/<id>/`.
- `dev-design.md` does not exist yet, or it is being revised in an open change.

## Steps

1. **Read.** `proposal.md`, the delta specs, the hand-off `design.md` and `tasks.md`. Note every contract id
   (`C-1`, `C-2`, ...) in `design.md`.
2. **Questions.** Ask the developer what the specs and contracts do not settle. Ask in one batch, not one by one.
3. **Approaches.** Propose 2-3 approaches with trade-offs and a recommendation. Stop until the developer chooses.
4. **Decision.** Record the chosen approach and who chose it:
   `| <time> | design | - | - | approach <x> chosen by <developer>, <chat or MR> |`.
5. **Write `dev-design.md`** from the template `envgene-component/templates/dev-design.md`:
   - Approaches, Decision, Out of Scope, Open Questions as in the template;
   - **Contracts:** one line per contract id from `design.md`: how the decision meets it, or why it cannot be met.
     A contract without a line blocks plan;
   - **Constraints:** one line per rule of sections 2 to 5 of `.claude/skills/envgene-code-review/SKILL.md`.
6. **Scope check.** If the decision changes the scope, the set of tasks or a contract, stop: the change returns to
   the propose gate. A change that only refines the implementation may update `tasks.md` without a new approval.
7. **Validate.** `openspec validate <id> --strict --no-interactive; echo "exit=$?"`, then the row:

   ```text
   | <time> | design | `openspec validate <id> --strict --no-interactive` | <exit> | valid @ <sha> |
   ```

8. **Gate.** Commit `dev-design.md` (with the developer's yes for commits), then append the gate row with the sha of
   that commit. The ledger rides along with the next commit.

   ```text
   | <time> | design | - | - | gate: approach <x> accepted by <developer> (dev-design.md @ <sha>) |
   ```

## Rules

- The developer accepts the decision. The agent proposes and records it; it does not accept it for the developer.
- Ask for the developer's yes before commit, push or merge request.
- Do not put tokens, passwords or usernames in the dev design or the ledger.
