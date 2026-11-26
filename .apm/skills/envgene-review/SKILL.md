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
4. **Ledger row** `| <time> | review | - | - | review <verdict> by envgene-reviewer @ <sha>, <n> critical, <n> important, <n> minor |`.
   An open critical or important finding: go to Receive. None: go to Human check.

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
confirm as closed goes back to step 1. When this re-review leaves no open critical or important finding, go to
Human check.

## Human check

The agent review does not close the stage. A person does.

1. **Ask** the developer to review the MR (and the GitHub PR, if there is one): the diff, the reviewer's findings and
   the answers to them. Ask for one of two answers: "ok", or what to change. Wait for it; silence is not an "ok".
2. **"ok"**: append the review gate row at that HEAD (format: Gate rows of
   `envgene-orchestration/references/ledger.md`).
3. **Not ok**: hold a dialogue. The person says what to change, one point at a time. For each point:
   - a question or "this is unclear" is answered, not acted on; change code only when the person asks for a change;
   - an unclear request: ask what they mean before changing anything;
   - mechanical: fix it;
   - design: give the options with the risk of each and a recommendation; the person decides;
   - test first for a behaviour change, one point in one commit, then answer `Fixed in <sha>: <what changed>`;
   - ledger row `| <time> | review | - | - | <person>: <point> -> <sha or answer> |`.
4. **When the person has no more points**: run `envgene-verification` again for the new HEAD, then go back to step 1.
   The "ok" must be for the HEAD the gate row names.

## Rules

- The general rules of `envgene-orchestration` (section Rules) apply.
