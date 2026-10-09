---
name: dev-design
description: Write a dev design for a code change in this repository as a brainstorm with the developer - questions one at a time, approaches with trade-offs, sectioned design, approval gate. The dev design says how the change is built in code, before the implementation plan and before any code.
when_to_use: Use before any code is written for a new feature, bug fix, or refactoring in this repository - "dev design", "дев дизайн", "how do we implement this", "design the change". Not for the solution design (ADR and docs) and not for the task-by-task implementation plan.
disable-model-invocation: false
---

# Dev design

A dev design says how a change is built in code: which steps, modules, and objects change, where the
data lives, and how the result is verified. It comes after the solution design (ADR and docs) and
before the implementation plan.

You write it as a brainstorm with the developer, not alone. When the `brainstorming` skill is
installed, take only its dialogue rules. This skill replaces its output steps: do not write a spec
under `docs/superpowers/specs/` and do not commit anything on your own. The dev design file from
section 4 is the only design document.

**Trade-off:** This skill biases toward caution over speed. For a trivial change, a short design in
chat is enough.

## 1. Brainstorm steps

Do the steps in order. One question per message.

1. **Read the context.** Read the CR or the request, the code the change touches, and the docs for it.
2. **Write back your understanding.** State the goal, the constraints, and the success criteria in a
   short note. Separate what the developer said from your assumptions. Wait for corrections.
3. **Ask clarifying questions.** One at a time, only the ones that change the design. Prefer a choice
   between options.
4. **Propose 2-3 approaches.** Give the trade-offs and your recommendation. Put the recommended
   approach first.
5. **Present the design in sections.** Ask after each section whether it is right.
6. **Write the dev design file.** See section 4.
7. **Ask the developer to review the file.** Change it until the developer approves it.

8. **Ask how the change is implemented.** When separate agents write the code, invoke the
   `writing-plans` skill with the dev design as its spec. When the developer implements it in the same
   session, go to the code without a plan.

**Gate:** no code, no implementation plan, and no scaffolding before the developer approves the dev
design. An approval covers the stage that was presented, not the next one.

## 2. Think Before Coding

**Don't assume. Don't hide confusion. Surface trade-offs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 3. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 4. Dev design file

Write the approved design to `docs/dev/designs/<slug>.md`. The file goes into git so that the team and
the reviewers of the code PR read it. Commit it only when the developer asks.

- Follow the `writing-docs` skill. The file is under `docs/` and the doc linters check it.
- Start with the problem and its root cause. The solution follows.
- Lead with a small concrete example of the mechanism: before and after.
- Keep EnvGene terms as they are: AppDef, RegDef, Namespace, ParameterSet, step names.
- Leave out language internals. Describe steps, objects, and files.
- Use few words. One decision per line, each with its reason.
- Cover: what changes in which step and module, where the data lives, what is validated and where,
  what the developer sees differently, how the change is verified, and what stays out of scope.
- List the open questions separately. Do not hide them inside the text.
- End with a "Constraints" section. Copy into it the rules from sections 2 to 5 of the
  `envgene-code-review` skill, one line each. The `writing-plans` skill copies this section into the
  Global Constraints of the plan, and every implementer and reviewer agent gets it from there. Without
  this section the agents never see the team rules.

## 5. Design code that passes review

**The dev design follows the rules that the review checks.**

Before you present the design, read the `envgene-code-review` skill
(`.claude/skills/envgene-code-review/SKILL.md`) and check the design against its "Simplicity First" and
"Code rules" sections. A design that breaks them produces code that fails the review.

---

**This skill is working if:** clarifying questions come before implementation rather than after mistakes.
