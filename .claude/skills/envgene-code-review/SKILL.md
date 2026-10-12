---
name: envgene-code-review
description: Team code review for this repository - review procedure and the code rules a diff is checked against (simplicity, surgical changes, real tests, naming and other team rules).
when_to_use: Use for any code review in this repository - "review", "ревью", "check my changes", "review this branch or commit" - and when writing or refactoring code, so that the code passes the review.
disable-model-invocation: false
---

# EnvGene code review

Team rules that a code change is checked against, and the procedure for the check.

## 1. Reviewing code

**Check the diff against sections 2 to 5. Report first, fix only on request.**

- Review the diff of the current branch against its base, including untracked files.
- For each finding give `file:line`, the rule it breaks, and the fix in one line.
- After a rename, search the whole repository for the old name. Untracked tests break silently.
- Report correctness bugs even when no rule in this document covers them.
- When the reviewer names a new kind of problem, propose a new rule for section 5.
- When a separate reviewer agent does the review, for example through the `requesting-code-review`
  skill, add to its prompt: read `.claude/skills/envgene-code-review/SKILL.md` and check the diff
  against sections 2 to 5. The reviewer agent starts without this skill.

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

## 5. Code rules

**Team rules for Python code. Each rule comes from a real review comment.**

- **Name things by what they are.** A name says what the thing is without a look at its type.
  `namespace_paths`, not `items`.
- **No comments in new code.** No comments, no docstrings, and no `# noqa` or other pragmas. Tests
  included.
- **No wrapper that only composes.** Do not add a function that only calls an existing function. Put
  the expression at the call sites.
- **No extra enum members.** Do not add `_missing_` or a sentinel member when a plain `==` against one
  value already gives the right default.
- **No assertions on log text.** A test checks that a warning fired. It never checks the message text.

---

**These rules are working if:** fewer unnecessary changes in diffs and fewer rewrites due to overcomplication.
