---
name: discrepancy-audit
description: >-
  Explicit trigger only: /discrepancy-audit. Runs a topic-scoped, report-only audit that
  reconciles EnvGene docs against code and schema and against other docs, emitting a
  fact-oriented verdict table. Does not author or edit documentation (that is writing-docs),
  does not review a PR through its BDD tests (that is bdd-test-review), and does not compare
  code against coding standards or an issue spec (that is code-review). Do not auto-fire on
  a general PR review ask, a doc editing request, or a single identifier factual question.
---

# discrepancy-audit

Systematic subject-area reconciliation of docs-vs-code-vs-docs with a verdict table, no test
intermediary, and no doc authoring. The skill takes a topic, gathers the relevant docs, code, and
schemas, and produces a verdict report of discrepancies. Resolution - filing a CR, opening a docs PR -
is handed off to `design-to-cr` or `writing-docs`. The skill never guesses intent. It reports the
fact of a discrepancy plus what code or schema says, and leaves the fix direction to the human.

## Neighbor boundary

| Skill                              | Its job                                              | Why not it                                                  |
|------------------------------------|------------------------------------------------------|-------------------------------------------------------------|
| `writing-docs` (content-integrity) | Verify one identifier while writing a doc            | Not a systematic audit, no doc-vs-doc, no verdict report    |
| `bdd-test-review`                  | Discrepancies seen through BDD tests on a PR         | Intermediary is tests. Here there is none.                  |
| `code-review` (mattpocock)         | Code vs coding standards or issue spec               | Truth is code standards, not documentation                  |
| `design-to-cr`                     | Turn a settled decision into a CR                    | Downstream. Consumes the verdict report from this skill.    |

## Trigger

Explicit only: `/discrepancy-audit`. Do not auto-fire. Do not fire on a general doc review request,
a doc editing task, a single factual question about an identifier, or a PR review not explicitly
directed at this skill.

## Five phases

1. **Scope resolution** - turn the topic into a concrete corpus: docs, code entry points, and schemas.
   Show the corpus to the user before auditing. Boundaries are editable before phase 2 starts.
2. **Claim extraction** - from corpus docs, pull checkable claims: identifiers, defaults, enum values,
   contract parameters, behavior, and artifact producer/consumer pairs. Pure conceptual prose becomes
   `unverifiable`.
3. **Truth location** - for each claim, find the code or schema anchor. Apply the verify-before-claim
   rules from `references/verify-before-claim.md`.
4. **Verdict and evidence** - assign a verdict from `references/verdict-model.md`. Drop any row that
   lacks its evidence pair.
5. **Report** - emit the verdict table using the format in `references/report-format.md`.

## Execution model

Phases 1 and 2 may fan out to subagents to cover a wide corpus: `Explore` agents in phase 1 to gather
candidate files, and one worker per corpus slice in phases 2 and 3 to extract claims and locate their
code or schema anchors in parallel. A slice is a coherent sub-area (one CLI, one data-model group, one
generation stage). Never fan out phase 4.

Findings returned by a subagent are candidates, not verdicts. Before any finding enters the report, the
controller re-verifies its evidence pair in the main context: open the cited doc line and the cited
code or schema line and confirm both say what the finding claims. This keeps the grounded discipline of
`references/verify-before-claim.md` even when reading was delegated. A candidate whose evidence does not
survive re-verification is dropped or downgraded, never passed through on the subagent's word.

For a narrow corpus, run all phases inline in the main context - the fan-out earns its cost only when
the corpus is too large to hold at once.

## Mode table

| Mode        | Phase 1 (acquisition)                              | Status   |
|-------------|----------------------------------------------------|----------|
| topic       | Topic -> corpus (Explore agents or inline grep)    | live now |
| PR/diff     | Worktree on PR head -> changed docs + their truth  | not yet  |
| single-file | One .md -> its claims + cross-referenced docs      | not yet  |

Adding mode 2 or 3 requires one new reference file and one new router row. Phases 2-5 and all core
reference files stay untouched.

## Reference files

| Phase or concern                        | File                                   |
|-----------------------------------------|----------------------------------------|
| Verdict scale and evidence-pair gate    | `references/verdict-model.md`          |
| Truth-location rules (phase 3)          | `references/verify-before-claim.md`    |
| Topic-mode acquisition (phases 1 and 2) | `references/acquisition-topic.md`      |
| Report structure (phase 5)              | `references/report-format.md`          |
