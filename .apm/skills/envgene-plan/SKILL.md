---
name: envgene-plan
description: EnvGene override of the component-plan slot. Turns tasks.md of an approved change into a step plan with a failing test first for every step, using the decision of component-design.md and checking that every contract of component-design.md is covered. Saves openspec/changes/<id>/plan.md. Use after the design gate, before implement.
---

# EnvGene plan (override of component-plan)

Replaces `component-plan` in this repository. The plan reads the approach, the constraints and the contracts from
`component-design.md`, the component's own design artifact of the change (the upstream `design.md`, if present, is the
read-only HLD context).

The gates and evidence rules of the package stay: a failing test first for every step, every scenario mapped to a
test, the plan saved in the change folder and noted in the ledger.

## Entry check

1. The propose gate is passed (Gate rows of `envgene-orchestration/references/ledger.md`).
2. The design stage is closed: the `gate: approach … accepted by …` row, or, for a bug fix, the
   `design: skipped, no contract change @ <sha>` row that `envgene-design` writes.
3. `component-design.md` exists in `openspec/changes/<id>/`. On the skip row it does not exist, and the plan is written
   from `tasks.md` and the failing test of the fix.
4. **Work map.** Where `component-design.md` exists, its Work map has no `not-in-repo` rows. For every contract and task
   path, `git ls-files` shows the file exists, or the design says it is `new-in-repo`. A path outside this repository
   stops the plan: go back to design.

If any check fails, stop and say which one.

**Skip.** A bug fix of one to three tasks writes no `plan.md`: the failing test is the plan, and implement works from
`tasks.md`. The stage closes with `| <time> | plan | - | - | plan: skipped, <n> tasks, the failing test is the plan |`,
named by the developer. Above three tasks, or any task that moves a contract, the plan is written.

## Steps

1. **Read.** `proposal.md`, the delta specs, `tasks.md`, `component-design.md` (Decision, Contracts, Constraints, Out of scope),
   `AGENTS.md` (Commands, conventions, task routing) and the code the tasks touch. On the skip row there is no
   `component-design.md`: the specs, `tasks.md` and the failing test of the fix are the whole input.
2. **Map the files.** Which files are created or modified and the one responsibility of each. Follow the repository's
   patterns; do not restructure what the change does not need.
3. **Copy the constraints.** Values the specs fix and the Constraints of `component-design.md` (names, limits, formats,
   versions) go verbatim into **Global constraints** of the plan. Contract shapes from `component-design.md` go there too.
   With no `component-design.md`, the constraints come from the specs and from what the reproduction of the bug shows.
4. **Name the review focus.** Up to five inputs or conditions the specs are silent on, each with the behaviour a
   reasonable user expects. Each one gets a test step.
5. **Write the steps**, task by task:
   - every `n.m` of `tasks.md` has its steps; every spec scenario has a test step; every contract id that a task
     touches has a step that checks it;
   - each step: write the failing test, run it (command and expected failure), the minimal code, run it (expected
     pass), commit;
   - the test commands come from `AGENTS.md` Commands: one test and all tests of the affected module.
6. **Save and self-review.** Write `openspec/changes/<id>/plan.md` in the format below, then check it: every
   scenario mapped to a test; no step without a check; no placeholders such as "add error handling"; names and
   signatures the same in every step that uses them; the plan does not contradict the specs or the design Decision.
    **Contract coverage:** every contract id listed in the Contracts section of `component-design.md` (`C-1`, `C-2`, ...) is
    covered by a step. Check with a command, not by reading: for each id, `grep -n "<id>"` on `plan.md`. A missing id
    needs a step; a contract that `component-design.md` does not settle goes back to `envgene-design` with that id.
    With no `component-design.md` there is no contract to cover: the gate row says `no contract, plan from tasks.md`.
7. **Gate.** Append the plan gate row (format: Gate rows of `envgene-orchestration/references/ledger.md`).
8. **Show the plan** to the developer and adjust it to their comments. It is committed with the next commit of the
   change, after the developer's yes for commits.

Gate: the plan gate row of step 7. Implement starts from this plan. A change to the plan during implement is an edit
to `plan.md`, recorded in the ledger.

## Format of plan.md

```markdown
# Plan: <id>

**Goal:** one sentence.
**Approach:** two or three sentences from the Decision of component-design.md. If the upstream `design.md` (the read-only HLD) names order or dependencies, use them here.
**Change:** openspec/changes/<id>/ (proposal, specs, design, tasks)
**Commands:** one test: `<from AGENTS.md>`; all tests: `<from AGENTS.md>`; lint: `<from AGENTS.md, or "not defined">`

## Global constraints

- <value copied verbatim from the specs or design Constraints, one per line>

## Contracts

- C-1: <shape from component-design.md>; covered in step <n.m>

## Review focus

- <input or condition> -> <expected behaviour>; test in step <n.m.x>

## Task 1.1: <task text from tasks.md>

**Files:** create `path/to/new_file`; modify `path/to/existing:120-145`; test `path/to/test`
**Interfaces:** `<signature>` (used by 1.2)
**Scenario:** specs/<capability>/spec.md, "<scenario name>"

- [ ] 1. Write the failing test `<name>`: <what it expects>.
- [ ] 2. Run `<one-test command>`; expect FAIL: <reason>.
- [ ] 3. Minimal code: <what>.
- [ ] 4. Run `<one-test command>`; expect PASS; run `<all-tests command>`; no new failures.
- [ ] 5. Tick `1.1` in tasks.md; commit `<type>: <description>`.
```

Use real test names, file paths and signatures. Show code only where the decision is not obvious.

## Rules

- The general rules of `envgene-orchestration` (section Rules) apply.
