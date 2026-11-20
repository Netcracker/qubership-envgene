---
name: envgene-verification
description: EnvGene override of the component-verification slot. Runs the test suites of this repository (per-module pytest, scripts pytest, Maven generator, cucumber BDD) on the untouched baseline and on the change, records exit codes and counts in the ledger as a verification row for the current HEAD. Use when every task in tasks.md is ticked and green, before review.
---

# EnvGene verification (override of component-verification)

Replaces `component-verification` in this repository. The gate is the same: evidence before "done", real
commands with exit codes, compared with a baseline. What this slot adds are the exact commands of this repository.

## When it runs

After implement: every task in `tasks.md` is ticked and green. It runs again after any new commit, because the
`verify` rows are tied to HEAD. Review does not start without the `verify` rows for the current HEAD.

## Commands

Run every command of `AGENTS.md`, section Commands (Tests, BDD End-to-End Tests, Lint), as written there.

- Run the BDD suite only when the change touches the pipeline, scripts or the step definitions, and only where
  Docker or the local Python environment for it is available. If it cannot run here, record `not run: <reason>`.
- A textlint error in `AGENTS.md` or in `docs/` fails the pipeline, so fix it in the same change (for example
  `ID`, not `id`, in a terminology list).

## Steps

1. **Baseline.** Use the `baseline:` rows that `envgene-implementation` wrote before the first change; do not take
   a new baseline. Only a command that has no baseline row (for example BDD or the Maven suite, when implement did
   not run it) is run once on the base branch in a separate worktree, with the row
   `| <time> | verify | <command> | <exit> | baseline: <counts> @ <base-sha> |`.
2. **Change.** Run the same commands on HEAD. One `verify` row per command (format: Gate rows of
   `envgene-orchestration/references/ledger.md`).
3. **Compare.** Every suite that passed on the baseline must pass on HEAD. A new failure is a finding, not a
   "known issue": send it to `component-debugging` before review.
4. **Gate.** For HEAD, every command has a `verify` row with exit 0 or no new failure against its baseline row
   (or `not run: <reason>`).

## Rules

- Never edit a test to make it pass without knowing why it failed.
- The general rules of `envgene-orchestration` (section Rules) apply.
