# Flow ledger

The ledger is the recovery map. It lives at `.superpowers/flow/<slug>.md`, git-ignored scratch, one
file per change. The orchestrator reads it to know the current phase and resumes from it after any
interruption. It records state, not narration - the commits, issues, and PRs it names exist in git and
GitHub even when no conversation remembers creating them.

The `<slug>` is a short kebab-case name for the change, matching the work branch where practical, for
example `custom-params-decomposition`.

## Template

```markdown
# dev-flow ledger - <slug>

Design reference: <ADR path> / doc PR #<NNNN>
CR issue: #<NNNN>
Base branch: feature/modern-toolset
Work branch: <branch>
Mode: gate | auto

## Phases

- [ ] design      - <ADR + doc PR, or "settled elsewhere">
- [ ] cr          - <issue #, when filed>
- [ ] plan        - <plan path, when written>
- [ ] implement   - <PR #, when opened>
- [ ] review      - <report path, when done>
- [ ] verify      - <checks outcome, when green>
- [ ] acceptance  - <sign-off, when signed>

## Log

<append-only. one line per dispatch, ruling, or escalation, newest last.>
```

## Resume protocol

1. Read the ledger. The first phase whose checkbox is unchecked is the current phase. Every checked
   phase is done - do not re-run it. Its exit artifact exists in git or GitHub.
2. If the current phase is `implement` and an SDD ledger exists under
   `.superpowers/sdd/<plan-basename>/`, that ledger governs the task loop. Resume the task loop from
   it, not from this flow ledger. This flow ledger only records that `implement` is in progress.
3. Verify the previous phase's exit artifact is real before starting the current phase - the issue
   exists, the plan file is on disk, the PR is open. A ledger checkbox is a claim, git is the truth. If
   they disagree, trust git and correct the ledger.
4. Dispatch the current phase per `phase-map.md`, on its model, with its entry-artifact paths.

## Recording rules

- **Mark complete only on a real exit artifact.** `cr` is complete when the issue is filed and its
  number is in the ledger, not when a draft is written. `implement` is complete when the PR is open.
- **Append rulings, never rewrite them.** When the entry artifact does not settle a fork and the phase
  decides it, append `Ruling: <decision> - <why> - <cost if wrong>` to the log. This is how a decision
  survives a fresh session.
- **Record model escalations.** When a phase runs a turn on a stronger model than its default, append
  one line saying which turn and why. This keeps the routing auditable.
- **One ledger per change.** A ledger whose first line names a different change is not yours. Leave it
  and create your own.

## Git-ignore

The `.superpowers/` tree is scratch and must be git-ignored. If the repository does not already ignore
it, add `.superpowers/` to `.gitignore`. The ledger is never committed - it is a local recovery aid,
and its durable facts (issues, PRs, commits) live in git and GitHub already.
