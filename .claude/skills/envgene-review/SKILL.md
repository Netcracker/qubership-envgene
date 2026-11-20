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
4. **Ledger row:** the review gate row with the verdict and the counts per severity (format: Gate rows of
   `envgene-orchestration/references/ledger.md`).

## Receive

1. Read all the feedback before changing anything. Check each item against the code and the rules.
2. Push back with reasons when an item is wrong or adds something nobody uses.
3. Fix in order: critical, important, minor. Test first for behaviour changes.
4. Answer every comment: `Fixed in <sha>: <what changed>` or the technical reason why not.
5. A new commit makes the verification stale: run `envgene-verification` again.

## Rules

- The general rules of `envgene-orchestration` (section Rules) apply.
