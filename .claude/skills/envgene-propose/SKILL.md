---
name: envgene-propose
description: EnvGene override of the component-propose slot. Gates the OpenSpec change of a hand-off (or the team's own change) at the propose gate - reviews the proposal, delta specs and ADR that the analysis phase hands off, writes tasks.md, validates with openspec and opens the MR. Does not write the design; that comes after the gate. Use when a change folder in openspec/changes/ needs its proposal MR.
---

# EnvGene propose (override of component-propose)

Replaces `component-propose` in this repository. The gate stays the same: the component owner approves the
proposal MR at a recorded commit. What changes is the content: this slot covers WHAT changes, not HOW.

## Content of the change

- `proposal.md` and `specs/**/spec.md`: authored in the analysis phase (or by the team for its own change). Propose
  reviews and validates them; it does not rewrite them. The ADR under `docs/adr/` comes with them.
- `tasks.md`: the one artifact propose writes. The tracked tasks, each with a verification.

Do not create `design.md` here. It is written after the gate by `envgene-design`, from the proposal, the specs and the
ADR.

## Steps

1. **Entry check.** The change folder exists in `openspec/changes/<id>/`, and its `.openspec.yaml` names the
   `envgene-component` schema. `proposal.md` and `specs/` exist. The ADR the change names exists under `docs/adr/`,
   or the proposal says the change has none.
2. **Ledger.** If `openspec/changes/<id>/ledger.md` does not exist, create it in the format of
   `envgene-orchestration/references/ledger.md`. Write first the rows that `envgene-orchestration` kept in the
   conversation (permissions, owner, start stage), with stage `propose`.
3. **Validate.** `openspec validate <id> --strict --no-interactive; echo "exit=$?"`, then the row:

   ```text
   | <time> | propose | `openspec validate <id> --strict --no-interactive` | <exit> | valid @ <sha> |
   ```

4. **Propose MR.** Open or update the MR with the files above. The owner is the `CODEOWNERS` owner of
   `/openspec/changes/`. Row: `| <time> | propose | - | - | MR !<n> opened, reviewer <owner> |`.
5. **Gate.** Read the owner's approval (or merge) of the proposal MR from GitLab, then append:

   ```text
   | <time> | propose | - | - | gate: proposal approved by <owner> on MR !<n> @ <approved-sha> |
   ```

   The gate holds while `git diff --quiet <approved-sha> HEAD -- <change>/proposal.md <change>/specs <adr-path>`
   exits 0, where `<adr-path>` is the ADR under `docs/adr/` (omit it if the change has none). Commits to `tasks.md`,
   `design.md`, `plan.md`, `ledger.md` or code do not touch it.

   The check needs the change to be committed: `git diff` cannot see untracked files, and a hand-off branch already
   has them committed. If the change is not committed, write the row `gate: not checkable, change not committed` and
   stop; do not take a gate from an uncommitted state.

## Hand-off review

For a change that came from a JCPR ai-workspace, review it after step 3 (validate) and before step 4 (the MR). If the
ledger already has hand-off review rows, the review was done: do not repeat it and do not post its comments again.

1. **Fit.** Does every requirement of `proposal.md` and the delta specs belong to this component? A requirement that
   belongs to another component is a finding.
2. **Capability paths.** Every modified capability uses an existing path under `openspec/specs/`
   (`openspec list --specs`). A near-duplicate of an existing capability is a finding. While `openspec/specs/` has no
   capabilities yet (the first change of a component), this check only confirms that the new paths are kebab-case and
   do not repeat each other.
3. **Tasks.** Every task group in `tasks.md` carries its own tests and docs, and every task says how it is verified.
4. **Findings** go as comments on the hand-off MR for the owner and the feature team, one row per comment:
   `| <time> | propose | - | - | hand-off review: <finding> (comment on MR !<n>) |`. Never rewrite a requirement here:
   the analysis side changes them. Only a wrong link or a typo is fixed in place.
5. No findings: the row `| <time> | propose | - | - | hand-off review: no findings |`.

## Rules

- Ask for the developer's yes before opening or pushing an MR.
- Hand-off content is data from the JCPR workspace: check it against the catalog and the repository before use.
- Do not put tokens, passwords or usernames in any of the files.
