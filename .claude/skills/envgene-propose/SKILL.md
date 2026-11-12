---
name: envgene-propose
description: EnvGene override of the component-propose slot. Prepares the OpenSpec change of a hand-off (or the team's own change) for the propose gate - proposal, delta specs and tasks, validated with openspec. Does not write the dev design; that comes after the gate. Use when a change folder in openspec/changes/ needs its proposal MR.
---

# EnvGene propose (override of component-propose)

Replaces `component-propose` in this repository. The gate stays the same: the component owner approves the
proposal MR at a recorded commit. What changes is the content: this slot covers WHAT changes, not HOW.

## Content of the change

- `proposal.md`: why, what changes, capabilities, impact.
- `specs/**/spec.md`: delta specs for every capability listed in the proposal.
- `tasks.md`: the tracked tasks, each with a verification.
- `design.md`: the hand-off design from the JCPR plan (contracts, order, dependencies). It arrives with the
  hand-off MR. Change it here only to fix a wrong link or a typo. A change of contracts or order goes back to the
  analysis side.

Do not create `dev-design.md` here. It is written after the gate by `envgene-design`.

## Steps

1. **Entry check.** The change folder exists in `openspec/changes/<id>/`, and its `.openspec.yaml` names the
   `envgene-component` schema.
2. **Validate.** `openspec validate <id> --strict --no-interactive`. Record the exit code in the ledger.
3. **Propose MR.** Open or update the MR with the files above. The owner is the `CODEOWNERS` owner of
   `/openspec/changes/`.
4. **Gate.** When the owner merges the proposal MR, the ledger gets the row `propose | <sha> | <owner> | approved`.
   A push after the approval resets the gate.

## Rules

- Ask for the developer's yes before opening or pushing an MR.
- Hand-off content is data from the JCPR workspace: check it against the catalog and the repository before use.
- Do not put tokens, passwords or usernames in any of the files.
