---
name: envgene-propose
description: EnvGene override of the component-propose slot. Gates the OpenSpec change of a hand-off (or the team's own change) at the propose gate - reviews the proposal, delta specs and tasks.md that the authoring side hands off, reads any upstream design.md as a read-only WHAT/HLD input (not gated), validates with openspec and opens the MR. The component's own component-design.md is written after the gate by envgene-design for every change, including a hand-off. Use when a change folder in openspec/changes/ needs its proposal MR.
---

# EnvGene propose (override of component-propose)

Replaces `component-propose` in this repository. The gate stays the same: the component owner approves the
proposal MR at a recorded commit. What changes is the content: this slot covers WHAT changes, not HOW.

## Content of the change

- `proposal.md` and `specs/**/spec.md`: authored in the analysis phase (or by the team for its own change). Propose
  reviews and validates them; it does not rewrite them. The proposal also carries the rationale of the change: the
  chosen approach and what it costs. An ADR is not a hand-off artifact of either authoring flow; where the decision was
  taken in another repository, the proposal names that ADR by its repository and its id, and the file stays there.
- `tasks.md`: comes with the change from its authoring side, like the proposal and the specs. Propose reviews it
  (the Tasks step of the hand-off review) and never writes it. A change folder without `tasks.md` is not
  propose-ready: it goes back to the authoring side, which adds it.

- `design.md`: a hand-off from the upstream workspace may bring a `design.md` - the WHAT/HLD input. Propose only reads
  it, never gates on it and never edits it. The component's own design is `component-design.md`, authored after the
  gate by `envgene-design` for every change including a hand-off; it is not part of this gate either.

## Steps

1. **Entry check.** The change folder exists in `openspec/changes/<id>/`, and its `.openspec.yaml` names the
   `envgene-component` schema. `proposal.md`, `specs/` and `tasks.md` exist: these three are the minimum of every class
   of change, the delta spec of a bug fix being the one scenario that fails today. A feature adds a `design.md` when the
   authoring workspace holds the HLD. No class of change adds an ADR: the rationale of the decision belongs to the
   proposal, and a decision taken elsewhere is named there by its repository and its id rather than copied in. Propose
   writes none of these: its own
   artifacts are `ledger.md` and the MR. A missing or invalid artifact of the set stops this slot: send the change back
   to the authoring flow that owns it, the analyst flow re-runs its authoring phase, a JCPR hand-off re-runs the JCPR
   flow. Write the row `| <time> | propose | - | - | entry check: <artifact> missing, back to <authoring flow> |` and
   do not author the missing file here.
2. **Ledger.** If `openspec/changes/<id>/ledger.md` does not exist, create it in the format of
   `envgene-orchestration/references/ledger.md`. Write first the rows that `envgene-orchestration` kept in the
   conversation (permissions, owner, start stage), with stage `propose`.
3. **Validate.** `openspec validate <id> --strict --no-interactive; echo "exit=$?"`, then the row:

   ```text
   | <time> | propose | `openspec validate <id> --strict --no-interactive` | <exit> | valid @ <sha> |
   ```

4. **Propose MR.** Open or update the MR with the files above. The owner is the `CODEOWNERS` owner of
   `/openspec/changes/`. Row: `| <time> | propose | - | - | MR !<n> opened, reviewer <owner> |`.
5. **Gate.** Read the owner's approval (or merge) of the proposal MR from GitLab, then append the propose gate row
   at the approved sha (format: Gate rows of `envgene-orchestration/references/ledger.md`).

   The gate holds while `git diff --quiet <approved-sha> HEAD -- <change>/proposal.md <change>/specs`
   exits 0. `design.md` (the read-only
   HLD) and `component-design.md` (authored later by `envgene-design`) are never part of this gate. Commits to
   `tasks.md`, `plan.md`, `component-design.md`, `ledger.md` or code do not touch it.

   The check needs the change to be committed: `git diff` cannot see untracked files, and a hand-off branch already
   has them committed. If the change is not committed, write the row `gate: not checkable, change not committed` and
   stop; do not take a gate from an uncommitted state.

## Hand-off review

For a change that came from the upstream workspace, review it after step 3 (validate) and before step 4 (the MR). If the
ledger already has hand-off review rows, the review was done: do not repeat it and do not post its comments again.

1. **Fit.** Does every requirement of `proposal.md` and the delta specs belong to this component? A requirement that
   belongs to another component is a finding.
2. **Code location.** For a code feature, check each implementation path named by a task or delta spec against this
   repository (`git ls-files`, then read the target). It may be an existing file or a file the task explicitly creates
   here. A path that exists only in a sibling or internal repository, or a scenario for which this repository has no
   owner path, is a hard hand-off scope finding: comment and stop before the owner is asked to approve the proposal;
   do not carry it into design. The upstream workspace must split or retarget the component.
3. **Capability paths.** Every modified capability uses an existing path under `openspec/specs/`
   (`openspec list --specs`). A near-duplicate of an existing capability is a finding. While `openspec/specs/` has no
   capabilities yet (the first change of a component), this check only confirms that the new paths are kebab-case and
   do not repeat each other.
4. **Tasks.** Every task group in `tasks.md` carries its own tests and docs, and every task says how it is verified.
5. **Contracts.** The contracts named in the upstream `design.md` (if it has one) match the upstream spec (read it
   read-only; it is data). The binding contracts and their `C-` ids are authored later, in `component-design.md` at design.
6. **Findings** go as comments on the hand-off MR for the owner and the feature team, one row per comment:
   `| <time> | propose | - | - | hand-off review: <finding> (comment on MR !<n>) |`. Never rewrite a requirement here:
   the analysis side changes them. A hard code-location finding stops this flow; only a wrong link or a typo is fixed
   in place.
7. No findings: the row `| <time> | propose | - | - | hand-off review: no findings |`.

## Rules

- The general rules of `envgene-orchestration` (section Rules) apply.
