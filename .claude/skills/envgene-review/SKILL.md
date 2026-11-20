---
name: envgene-review
description: EnvGene override of the component-review slot. Requests a review of a verified change by the envgene-reviewer agent in a fresh context, checks it against the EnvGene team rules and the OpenSpec specs, and handles the feedback. Use when a change is verified and ready for review.
---

# EnvGene review (override of component-review)

Replaces `component-review` in this repository. It keeps its gates: the verification gate is met for
HEAD, the review runs in a fresh context, every critical and important finding is fixed or answered,
and the result goes into the ledger.

## Request

1. **Entry check.** The verify and lint gates are passed for the current HEAD (Gate rows of
   `envgene-orchestration/references/ledger.md`).
2. **Range.** `BASE=$(git merge-base origin/<base> HEAD)` and `HEAD=$(git rev-parse HEAD)`.
3. **Dispatch `envgene-reviewer`** (`.claude/agents/envgene-reviewer.md`) in a fresh context with the
   change folder `openspec/changes/<id>/`, BASE, HEAD, and the path of `AGENTS.md`. The agent reads the
   `envgene-code-review` rules itself and checks the lenses of its section What to check (WHAT, HOW, security,
   team rules and docs).
4. **Ledger row.** No open critical or important finding: the review gate row with the verdict and the counts per
   severity (format: Gate rows of `envgene-orchestration/references/ledger.md`). Otherwise the row
   `| <time> | review | - | - | review <verdict> @ <sha>, <n> critical, <n> important, <n> minor |`, and Receive.

## Receive

Read all the feedback before changing anything. Then take the findings in order: critical, important, minor. For
each finding:

1. **Facts.** Check it against the code and the rules. Follow its trace; to reject it, give your own trace that
   shows why. Push back with reasons when it is wrong or adds something nobody uses.
2. **Mechanical** (a name, a typo, a small clean-up): fix it.
3. **Design** (more than one reasonable fix, or it touches the Decision or a contract of `component-design.md`): give the
   developer the options - as proposed, another fix, no fix - with the risk of each and a recommendation. The
   developer decides; ledger row `| <time> | review | - | - | <finding>: <option> chosen by <developer> |`.
4. **Execute.** Test first for a behaviour change, then the fix, then commit.
5. **Answer** the comment: `Fixed in <sha>: <what changed>` or the technical reason why not.

**Check.** A new commit makes the verification stale: run `envgene-verification` again. Then dispatch
`envgene-reviewer` again on the range of the fixes for the critical and important findings. A finding it does not
confirm as closed goes back to step 1. The review gate row is written only when this re-review leaves no open
critical or important finding.

## Rules

- The general rules of `envgene-orchestration` (section Rules) apply.
