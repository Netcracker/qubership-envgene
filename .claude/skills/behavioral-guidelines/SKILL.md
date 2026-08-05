---
name: behavioral-guidelines
description: Coding principles — think before acting, keep it simple, make surgical changes, verify with clear success criteria. Biases toward caution over speed.
when_to_use: Use when planning an implementation, reviewing code, refactoring, or writing new features in this repository.
disable-model-invocation: false
---

# Behavioral Guidelines

Behavioral guidelines to reduce common LLM coding mistakes.

**Trade-off:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface trade-offs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Test the Real Thing

**Never mock the system under test. Mocks are for external dependencies, not the subject.**

A test that replaces the component it claims to verify with a reimplementation is not a test — it is a
tautology. It can only catch bugs in the mock itself, not in the real code.

The rule in two lines:

- **Allowed to mock:** network calls, wall clock, randomness, services unavailable in the test
  environment (e.g. a remote registry, a live Kubernetes cluster).
- **Never mock:** the component named in the scenario title, any library or binary that the pipeline
  step under test directly invokes.

When the real component requires a build step before it can be invoked (e.g. a Java JAR built with
Maven, a compiled binary), **build it as part of test setup or as a prerequisite fixture**. Slow
is acceptable; vacuous is not.

Concretely for this repository:

- If a scenario is titled "Calculator CLI validates deployPostfix", the test must invoke the real
  `effective-set-generator-*-runner.jar`. A Python reimplementation of the same rules is a separate
  artefact, not a test of the CLI.
- If a scenario is titled "SBOM retention removes legacy flat files", the test must run the real
  `sboms_retention_policy()` Python function — which it does, because the full pipeline runs. That
  is the correct pattern.
- Mock stubs placed at `EFFECTIVE_SET_CLI_PATH` that always exit 0 are acceptable **only** for
  scenarios whose subject is NOT the Calculator CLI (e.g. SBOM retention scenarios that merely need
  the ES step to not crash). They are never acceptable for Calculator CLI scenarios themselves.

Diagnostic question before writing any mock: "If the real component had a bug that made it
produce wrong output, would this test catch it?" If the answer is no, remove the mock.

## 5. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
