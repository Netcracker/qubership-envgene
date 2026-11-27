---
name: envgene-implementation
description: EnvGene override of the component-implementation slot. Implements an approved OpenSpec change step by step, test first, and adds the BDD steps of this repository - the Gherkin scenarios come from the delta specs, and the BDD tests are reviewed with bdd-test-review before the change goes to verification. Use when plan.md and tasks.md of an approved change are ready and code must be written.
---

# EnvGene implementation (override of component-implementation)

Replaces `component-implementation` in this repository. It keeps its gates and evidence rules: entry only
with an approved change, a reuse check before new code, a red run before every green run, both in the ledger.

## Entry check

- The propose, design and plan stages are closed (Gate rows of `envgene-orchestration/references/ledger.md`). On a bug
  fix the two rows may be the skip rows: `design: skipped, no contract change` and `plan: skipped, <n> tasks`.
- `tasks.md` exists in `openspec/changes/<id>/`, and so do `component-design.md` and `plan.md` unless their stage is on
  a skip row. With no `plan.md` the input is `tasks.md` and the failing test of the fix; with no `component-design.md`
  the constraints come from the specs.
- The edit belongs to an open task in `tasks.md`.

## Inputs

Implement reads `plan.md` and `component-design.md` (Decision and Constraints), where those files exist. The BDD scenarios
come from the delta specs under `specs/`, which the analysis phase already rendered with the writing-gherkin craft.

## Steps

1. **Worktree.** Work in a worktree on the change branch, never on the base branch. Read the Decision and the
   Constraints of `component-design.md` and the Global constraints of `plan.md` before the first step, where those
   files exist.
2. **Baseline.** Run the test commands from `AGENTS.md` (section Commands) on the untouched branch. One row per
   command: stage `implement`, the command, its exit, result `baseline: <counts> @ <sha>`. A failing baseline is reported to the developer, not fixed silently.
3. **BDD scenarios (BDD only).** Put the scenarios of the delta specs that this task covers into the feature file
   before the step definitions. Do not invent scenarios: a case the specs do not cover is a gap, and it goes back
   to the analysis side through `envgene-design` (step 7). For the layout of `cucumber_tests/`, the feature-file, test-data and step-definition conventions, read the
   `envgene-bdd-tests` skill (`.claude/skills/envgene-bdd-tests/SKILL.md`).
4. **For every task, red, green, refactor:**
   - **Reuse check** before any new function, module or helper: search the code first, and write in the step
     what is reused and why nothing existing fits.
   - **Red:** write the one test the step names. Run it. It must fail for the expected reason. Row: the command, exit 1,
     result `red: <what failed>`.
   - **Green:** minimal code. Run the module's tests. Row: the command, exit 0, result `green: <n> tests @ <sha>`.
   - **Refactor** while green. Run the tests again.
   - Tick `- [x] n.m` in `tasks.md` when every step of the task is green.
   - Commit the step with the ledger row, once the developer's yes for commits is recorded.
5. **BDD review (BDD only).** When a task adds or changes BDD scenarios or their test data, run the
   `bdd-test-review` skill (`.claude/skills/bdd-test-review/`) on them. Fix the findings or answer them in the
   ledger before the task is ticked.
6. **A failure you do not understand** goes to `component-debugging`. Do not stack fixes.
7. **A gap the design never settled, or a case the specs do not cover**: stop, and go back to `envgene-design` with that one question.
8. **Done** when every task in `tasks.md` is ticked and green, and the BDD review has no open findings.
   Hand over to verification.

## Rules

- The general rules of `envgene-orchestration` (section Rules) apply.
- Do not edit a test to make it pass without knowing why it failed.
