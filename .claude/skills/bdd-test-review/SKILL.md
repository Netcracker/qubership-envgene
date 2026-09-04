---
name: bdd-test-review
description: >
  Review a qubership-envgene PR that adds or changes BDD (pytest-bdd / Gherkin) scenarios and their test
  data. Invoke explicitly via /bdd-test-review only - do not auto-trigger on loosely matching requests
  such as a general PR review ask. Validates scenario completeness and validity plus
  test-data completeness and validity against both docs and code, drives doc-vs-code divergence resolution
  with the user, and produces the canonical verdict report published as a PR comment.
---

# bdd-test-review

Review AI-generated (or human-written) BDD scenarios and their test data as the domain expert's proxy.
The core threat model: a generated test can be plausible and green while verifying nothing - the review
exists to catch empty oracles, self-blessing and non-discriminating data before humans start trusting the
suite. The four axes below and the report format are settled defaults - do not re-ask for them,
re-open only if the user explicitly signals a different scope.

## Scope contract

The review validates exactly four axes - nothing else:

1. Scenario completeness - against docs AND code (doc-vs-code mismatches go to the divergence list, never
   auto-counted as coverage gaps).
2. Scenario validity - four questions per scenario (Phase 3).
3. Test-data completeness - every referenced datum exists and is reachable.
4. Test-data validity - schema-valid AND discriminating.

Explicitly out of scope (do not report, do not propose cases for):

- Framework and runner quality, CI wiring, lint, PR hygiene - other reviews own these.
- Product code brought in by the test PR itself. Its fate is the code reviewer's call. Never treat
  smuggled code as a coverage target. Exception: test-data findings stay in scope even when product code
  was bent around them (a schema loosened to admit a defective fixture - report the fixture).
- Suite-level limitations ("a hermetic run cannot verify the commit step"). They get no verdict rows.
  Where testable, absorb into a proposed scenario, otherwise drop.

## Phase 1 - fix the references

Work on the CURRENT PR head in a worktree (`git fetch origin pull/<N>/head:<branch>`, then
`git worktree add`). Identify and read:

- the feature file(s), step definitions, test data and goldens.
- the doc pair: use-case doc (`docs/use-cases/`) and feature doc (`docs/features/`).
- the JSON schemas the payloads are validated against.
- the implementation entry points the scenarios exercise.

Build the self-blessing map: diff the PR against ITS OWN base branch (not main) and list every product
file, schema and doc the PR itself changed. A scenario verifying behavior introduced by the same PR is
flagged under oracle independence.

Verification rules - each of these cost a wrong claim once:

- Re-verify every fact on the current head. Directories move mid-branch (a python/ to modules/ move made
  earlier greps silently blind and produced a false "not implemented" claim).
- Before declaring behavior unimplemented, search the orchestrator for a SEPARATE step implementing it.
- A claim about a written artifact needs BOTH its writer and its reader located. A writer whose output no
  reader consumes is a different and worse finding than a naming mismatch.
- Verify where a payload actually fails and where data actually differs - never trust names and comments.

## Phase 2 - completeness matrix

Enumerate the documented variations (use case x action x place x mode ...) and map them to scenarios.
Uncovered documented variations become `missing` rows. Code branches absent from the docs go to the
divergence list for maintainer triage - they are not automatically test gaps. Cross-check where the
uncovered zone overlaps the doc-vs-code disagreement zone: that overlap is the highest-value gap, because
a new test there forces the divergence to be resolved.

## Phase 3 - scenario validity, four questions each

1. Doc conformance - Given/When/Then does not contradict the documented behavior.
2. Oracle strength - what state transition does the assertion distinguish? Ask: would the test pass if the
   code did nothing? If it produced a wrong result? Existence-only asserts on a file that existed before
   the run are void, and comparing output against the very payload that produced it is an echo, not an
   oracle. This is informal mutation testing: imagine the smallest realistic break and check the test
   would catch it.
3. Oracle independence - the scenario must not be confirmed by the product code changed in the same PR
   (self-blessing). Goldens produced by UPDATE_GOLDEN-style runs are code-blessed: verify their content is
   independently derivable from the documented contract. Carry the result inside the verdict reason cell
   ("strict golden"), never as a standalone published note - standalone notes of that kind were rejected
   in review.

   **Real-code check (part of oracle independence):** A mock that re-implements the system under test
   is structurally self-blessing — it confirms the mock, not the code. For every scenario, ask: "Does
   the test invoke the real component the scenario title names?"
   - If the scenario is about the Calculator CLI, the test must execute the real JAR (via
     `EFFECTIVE_SET_CLI_PATH` pointing to the built `effective-set-generator-*-runner.jar`), not a
     Python reimplementation of the same rules.
   - If the scenario is about a Python pipeline step (SBOM retention, inventory generation, etc.),
     the test must run the real function through the full pipeline — which it does. Acceptable.
   - A no-op stub (exit 0) at `EFFECTIVE_SET_CLI_PATH` is acceptable ONLY for scenarios whose
     subject is NOT the Calculator CLI (e.g. SBOM retention needs the ES step to not crash, but is
     not testing what the CLI does with its inputs).
   When this check fails, mark the verdict `invalid` and add a finding: "Mock replaces SUT — test
   cannot catch regressions in the real [component]. Rebuild against the real binary."
4. Determinism - no network, wall clock, ordering or environment dependence. Encryption with random IVs
   makes byte-goldens impossible - a fixed test key enables decrypt-then-compare instead.

Negative scenarios get one extra check - the failure POINT: the payload must reach the failure stage the
title claims. A "rollback on mid-processing failure" test whose payload dies at upfront schema validation
proves nothing about rollback and silently duplicates the plain schema negative. Check WHERE it fails, not
just THAT it fails.

## Phase 4 - test data, per scenario

Judge payload, initial state and golden separately for each scenario:

- liveness - reachable from a live step. Data referenced only by dead steps is dead data: list it in
  Notes for deletion, together with the dead steps.
- schema validity - passes the product schemas. Placeholder stubs (`name: test / value: placeholder`) are
  findings.
- discriminating power - initial state, payload and golden must differ wherever the semantics require.
  If two scenarios would pass on identical data, or a replace test cannot be told from a no-op, that is
  the finding. Deletion tests need a surviving sibling file to make over-deletion observable.
- realism notes (plain-text credentials where real repositories store encrypted ones) - minor, recorded.

Goldens additionally: the comparison must be strict in both directions (missing AND extra files), and the
golden content must be verifiable against the docs without running the code.

## Phase 5 - divergence resolution

Every doc-vs-code contradiction goes to a numbered divergence list and is resolved WITH the user, never
silently. Present each one as: what the doc says (quote), what the code does (file:line), how it
manifests, recommendation. Verdict options: doc wrong / code wrong / both wrong / behavior OK but
undocumented / defer to the product owner.

Actions per verdict:

- code wrong - CR issue (use the design-to-cr skill when available, body format: `docs/dev/creating-cr.md`).
- doc wrong, mechanical fix (names, paths, copypaste) - direct docs PR.
- doc wrong, semantic (contract rewrite, removal of a promised feature) - issue first.
- defer - issue carrying the question.

All resulting issues and PRs are proposed to the user as one batch. Nothing is filed, committed or
pushed without explicit confirmation - a verdict on a divergence authorizes drafting, not publishing.
Keep the numbered divergence list in the draft report or chat while iterating - it is a working
artifact and does not survive into the published report (see the reference).

Two binding patterns:

- Current-truth doc fixes may merge immediately (they create no gap). Target-state doc changes ship as
  DRAFT PRs attached to their CRs ("merge together with the implementation, not before"), so the default
  branch never documents unimplemented behavior. The CR's in-scope item reads "Merge the prepared
  documentation PR #N together with the code change".
- Resolutions feed BACK into verdicts: "code wrong" flips the affected scenarios to doc-side expectations
  with @xfail(strict) plus the issue link until the fix lands. Record every resolution (issue links in the
  report, a resolved-mark per divergence while iterating).

## Scenario fate rules

The fate of a test follows the fate of the behavior:

- behavior removed - existing scenario becomes `not needed` (the row is the action item for the author),
  a proposed one vanishes from the report entirely.
- behavior fixed by an issue - the test stays, marked @xfail(strict) with the issue link until the fix.
- behavior owned by another module - the scenario moves out of this suite (`not needed`), proposed ones
  vanish.
- optional nice to have negatives (schema pattern guards already covered by a generic schema negative) are
  not proposed. When the schema itself is lax, fix the schema (issue + PR) instead of pinning the laxness
  with a test.

## Report and publication

The report format - sections, verdict scale, legends, table rules, worked example - lives in
`references/report-format.md`. Follow it exactly: every rule there was hard-won in review iterations.

Self-checks before showing the report:

- the rows for existing scenarios (every verdict except `missing`) must equal the scenario count in the
  feature file, one to one by UC ID (a row was silently lost once - counting the whole table would mask
  exactly that loss whenever missing rows are present).
- bidirectional check: every `missing` row has a Gherkin draft or is named in a pattern comment, and every
  draft has a row.
- every legend covers every value actually used in its table.

Publication, only on the user's explicit command:

1. Translate to English (chat iterations may be Russian, the published artifact ships in English).
2. Critic-author loop: a FRESH-context agent checks translation fidelity against the source, internal
   consistency, 3-4 repository spot-facts, and house style (no semicolons, no em or en dashes, aligned table
   pipes, prose at 120 chars). Fix and re-run until a clean round. If the user capped the iterations and
   complaints remain at the cap, stop and surface them instead of publishing.
3. Post as a PR comment. Never publish, commit or push anything without an explicit go-ahead.

## Iteration discipline

The report is a living artifact the user challenges row by row. While it is chat-borne, re-emit the FULL
report after every accepted change. Once the user asks to keep it as a file (default location:
`<repo-parent>/stuff/pr-<N>-test-review.md` - the scratch directory beside the repository clone,
outside the repository and never committed), update the
file after every accepted change and report the delta in chat. Debate challenges rather than
auto-accepting - recommend, then wait. When a challenge changes the format itself, propose an edit to
this skill's files (SKILL.md or the reference) and apply it on the user's approval - the skill does
not silently self-edit.
