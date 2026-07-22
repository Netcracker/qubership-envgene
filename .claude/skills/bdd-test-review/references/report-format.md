# Report format

Published title: "Test review: scenarios and test data". Five sections, in this order: Per-scenario
verdicts, Proposed scenarios, Test data per scenario, Notes, Related issues (context only). When the
draft becomes file-based (SKILL.md owns that mode switch), it lives in the scratch directory beside
the repository clone (`<repo-parent>/stuff/pr-<N>-test-review.md`, outside the repository, never
committed). The published comment is the draft's English translation.

House style everywhere: no semicolons in prose, hyphen-minus only (no em or en dashes), prose wrapped at
120 characters (tables and URLs exempt), all tables with vertically aligned pipes and dash-padded
separator rows (align programmatically, skip fenced code blocks). Plain language: allowed jargon is
limited to test-approach terms (golden, snapshot, negative, the verdict values, @xfail) and product
terminology as spelled in the docs. Everything else - paraphrase (no "oracle", "no-op", "advisory",
"camelCase" and similar in reasons). After issues are filed, reference them as bare #NNNN (GitHub
auto-links them). Before filing, use named placeholders plus a pointer in the Related issues
section, and replace them at filing.

## Per-scenario verdicts

Open with the legend, one plain sentence per value:

- `valid` - the scenario correctly verifies the claimed behavior
- `weak` - the scenario exists, but its checks cannot tell some wrong outcomes from the right one
- `invalid` - the scenario passes even when the behavior is broken: the checks do not serve their purpose
- `missing` - no such scenario, proposed to add (drafts are in "Proposed scenarios")
- `not needed` - the scenario exists, but per the taken decisions it is removed or moved out of this
  feature

Table columns: Scenario | Verdict | Reason.

- The Scenario column holds the UC ID ONLY. For existing scenarios spell it exactly as in the feature
  file. `missing` rows carry proposed IDs continuing the family numbering (UC-X-PS-4 after PS-1..3) and
  are interleaved into the table right next to their family, not appended at the bottom. No "(proposed)"
  markers - the `missing` verdict itself carries that meaning.
- Verdict values are English even in a Russian draft.
- Reasons are evidence, not restatements. For `valid` name what proves it ("pre-run content differs from
  the golden - full overwrite is proven"). For `weak` and `invalid` name the exact blindness and the
  cure. For `missing` keep identical wording for identical gaps ("place cluster/site are not covered").
  For `not needed` state the decision and its carrier ("removed together with the legacy X flow
  (#NNNN)").
- Verdict-driving analyses stay inside the cell (no footnotes), but trim resolution history to an issue
  reference. A reason must answer "why is this verdict earned", not only state a fact about the data -
  "the payload fails at the wrong point: at schema validation, before the first write - there is nothing
  to roll back" explains `invalid`, "the payload uses an invalid action value" does not.
- Suite-level limitations and observations about product code smuggled by the PR get NO rows.

## Proposed scenarios

One fenced gherkin block. For every `missing` row either a full draft or an explicit mention in a pattern
comment that names the UC ID, so searching any ID finds its draft. Rules:

- Reuse the existing step vocabulary of the suite verbatim - drafts must be paste-ready.
- Use Scenario Outline plus an Examples table for place or mode variants instead of copypaste.
- Every draft starts with a short `# why:` comment stating the gap it closes.
- Data that does not exist yet appears as "<new payload>"-style placeholders. Paths that already exist in
  the repository stay real.
- A draft expected to fail until an issue is fixed carries a comment: "@xfail(strict) with a link to
  #NNNN until the fix".
- No meta boilerplate around the block ("IDs are tentative", "payloads to be created") - substantive
  inline comments only.

## Test data per scenario

Open with the legend:

- `✓` - the data exists and does its job (where it matters, the cell says what it proves)
- `✗` - the data is required but absent - the cell says what the missing piece would catch
- `n/a by design` - this kind of data is not required for the scenario (a create scenario starts from a
  clean workspace). Do not reuse the verdict phrase "not needed" here - the collision with
  the verdict value confuses readers.
- `-` - not applicable: the scenario leaves the suite
- a `weak:` note - the data exists but has the described defect

Table columns: Scenario | Payload | Initial state | Golden. Rows are the existing scenarios of the
Per-scenario verdicts table (`missing` ones have no data yet). Cells are self-explanatory phrases
that name what differs from what and what that proves - never invented terms or bare tokens.
"✓ old values differ from the payload" and
"✓ differs from the pre-run state - proves the replacement", not "✓ discriminating" or "✓ old_param"
(both fail readers once the surrounding discussion is gone). Every ✗ cell states the cure ("a golden
of the remaining state would catch extra deletion"). If the data mapping stops being one-to-one per
scenario (shared goldens across many scenarios), point shared cells at one place instead of duplicating.

## Notes

PR-scoped action items ONLY - everything here is addressed to the author of the reviewed PR. Bullets:

- dead data and the dead steps that reference it (list the files, name what stays alive and why).
- dead or unused fixture fields.

Nothing tracked in a separate issue belongs here: mixing them made a reader take the filed tickets for
the review's requested scope once.

## Related issues (context only)

Product-side findings discovered during the review, tracked in their own issues. Open with the lead-in:
"Product-side findings discovered during the review. Tracked in their own issues - they are not part of
this PR's scope and do not block it." Bullets:

- one bullet per filed issue: bare #NNNN plus a one-line statement of FACT (what is broken or decided),
  not of action - the action lives in the issue, the review only points at it.
- the docs-alignment bullet: which docs PR fixes current truth (mergeable now, creates no gap) and which
  draft PRs carry target-state docs attached to which issues.

No references to reviewer-local files, patches or paths anywhere in the report - the published comment
must be self-contained for a GitHub reader. The numbered divergence list from Phase 5 is a working
artifact (a draft section or chat) and is stripped at publish: every "divergence #N" reference
collapses to the bare issue number or to self-contained wording.

## Worked example rows

| Scenario  | Verdict | Reason                                                                                                                           |
|-----------|---------|----------------------------------------------------------------------------------------------------------------------------------|
| UC-X-ED-2 | valid   | pre-run content differs from the golden - full file overwrite is proven                                                          |
| UC-X-CR-2 | invalid | the file existed before the run and exists after, the content is never compared - the test is green even if the code did nothing |
| UC-X-PS-4 | missing | place cluster/site are not covered                                                                                               |

A complete published instance:
<https://github.com/Netcracker/qubership-envgene/pull/1570#issuecomment-5028814660>
