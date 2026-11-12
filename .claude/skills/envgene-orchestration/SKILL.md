---
name: envgene-orchestration
description: EnvGene override of the component-orchestration slot. Sets the stage order of a change in this repository (hand-off, propose gate, dev design, plan, implement, verify, review, docs, finish, archive) and routes each stage to its skill, the envgene override where one exists. Use when a change in openspec/changes/ moves to its next stage.
---

# EnvGene orchestration (override of component-orchestration)

Replaces `component-orchestration` in this repository. It picks the next stage from the ledger and calls the
skill for that stage.

## Stage order

| # | Stage | Skill | Gate (ledger row) |
|---|-------|-------|-------------------|
| 1 | Hand-off MR | (from the JCPR workspace, or the team) | - |
| 2 | Propose | `envgene-propose` | `propose \| <sha> \| <owner> \| approved` |
| 3 | Dev design | `envgene-design` | `design \| <sha> \| <developer> \| <approach>` |
| 4 | Plan | `component-plan` (no override yet) | plan entry: every contract id of `design.md` covered in `dev-design.md` |
| 5 | Implement | `envgene-implementation` | - |
| 6 | Verify | `envgene-verification` (not in the repository yet) | verification row for HEAD |
| 7 | Review | `envgene-review` | review row |
| 8 | Docs | `envgene-documentation` | docs row |
| 9 | Finish | `component-finish` | person merges |
| 10 | Archive | `openspec-archive-change` | change archived into `openspec/specs/` |

## Rules

- Stage 3 does not start without the row of stage 2. Stage 5 does not start without the rows of stages 2 and 3.
- A dev design change that alters scope or tasks sends the change back to stage 2.
- Stages 4 and 6 have no envgene override in the repository yet. Until they exist, the orchestrator uses the
  package slot and records that in the ledger.
- The ledger format is not defined yet; rows are written as in the table above.
