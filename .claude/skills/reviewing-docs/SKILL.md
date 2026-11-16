---
name: reviewing-docs
description: >-
  Review documentation changes in this repository - a how-to, feature, tutorial, reference doc, README, or a
  doc pull request - for fitness for purpose, not just rule compliance. Use whenever the user asks to review,
  critique, or sanity-check docs before a PR: "review this doc", "review my docs PR", "review PR #N" when it
  is a docs PR, "check these guides before I open the PR", "is this how-to any good", "go over the
  documentation changes", "review the docs on this PR before merge". For a mixed code-and-docs PR, use this
  skill for the documentation part only. It judges whether each document does one job for its
  reader, is named for that job, places each section in the right Diataxis quadrant and its canonical home,
  covers the domain surface, and reuses existing vocabulary - the things the linters and link checker pass
  over. Do NOT use this for code
  review (that is envgene-code-review), for reviewing a PR through its BDD tests (that is bdd-test-review),
  for the explicit-trigger doc-vs-code reconciliation audit (that is discrepancy-audit), or for writing or
  editing docs (that is writing-docs). The signal is judging documentation someone already wrote, against
  both the house style and its fitness for the reader.
---

# Reviewing docs

This skill reviews documentation someone has written. It is the discriminator counterpart to `writing-docs`
(the generator): `writing-docs` holds the rules for how text is written, and this skill applies them plus a
method that catches what rule-by-rule scanning misses.

Read the rules you review against from `writing-docs`
(`.claude/skills/writing-docs/references/`) - do not restate them here. This skill is the procedure.

## Why a method, not a checklist

A documentation review fails in a predictable way: the reviewer scans the text against a list of rules,
confirms the mechanical ones (heading case, link exists, index updated), sees green CI, and stops. That
catches surface compliance and misses the findings that matter most - a document that does not do one job,
a title that no longer matches its content, a section sitting in the wrong document, a guide that omits half
the domain. These are properties of the document as an instrument for a reader, not properties of a line.

Green linters are the floor, not the ceiling. They are an entry precondition for this review, never a
finding category and never evidence of quality. The substantive review begins after they pass.

The fix is to force the fitness-for-purpose questions with small artifacts you must produce per document, so
applying the rules is not optional. The method below is those artifacts plus the sweeps that ground them.

## Scope

Review the new and modified content. When a PR edits an existing doc, judge the lines it adds or rewrites,
and the document-level properties the edit changes (its title, its scope, its place in the index). Do not
restyle surrounding prose the PR did not touch.

Line-local scope applies to style, not to fitness for purpose. The purpose line, the fused-jobs check, and
the coverage diff are whole-document judgments even on a small edit: a section appended to an
already-fused document, or a pre-existing coverage gap the change now touches, is in scope. If you cannot
tell whether a fitness defect is the author's to fix in this change, raise it as an observation rather than
dropping it.

## Entry preconditions

1. Confirm CI is green (lint, link checker, title check). If red, that is the author's to fix first; note it
   and continue the substantive review - do not list passing linters as findings.
2. Get the real content: the rendered files at the PR head, with their real filenames. The filename is part
   of what you review - do not review a diff hunk in isolation.
3. List every changed file and classify each: new doc, reworked doc, small edit, sample, index.

## Per-document method

For each substantial document, produce these three artifacts and put them in the review (an appendix per
document is fine). They are not scratch notes you may skip. A verdict like "coverage is complete" or "one job
throughout" with no ledger or diff behind it is exactly the holistic scan this skill exists to replace, and
it is where real findings get rationalized away. Build the table; let the findings fall out of the rows.

Show the section ledger and the coverage diff as tables in the review, one per substantial document.
Compressing either to a sentence ("coverage complete", "no fused jobs") is the skip in disguise: the
enumerated coverage rows are what make a missing version or variant visible, and the per-section cadence
column is what makes a fused job visible. A prose "no gap" hides exactly the row you did not write.

### 1. Purpose line

Write one sentence: **this document's one job is ___, for ___ (the reader).** The Overview states a job;
treat that as a claim to test, not as the answer. Derive the real job from what the sections actually make
the reader do, then compare it to what the Overview and title claim.

Two findings fall straight out of this line:

- **Name mismatch.** Does the title and the filename name that job, in the reader's terms? A title naming one
  object the doc merely mentions, or a filename describing an older or narrower scope, is a finding. (See
  "Title names the job" in `writing-docs` `doc-structure.md`.)
- **Fused jobs.** Read the cadence column of the section ledger below. If it shows more than one cadence -
  connecting a store (once per repository), converting a template (once per template), adding one parameter
  (recurring) - the document fuses jobs, however single its Overview sounds. The opening step is the quickest
  tell: a "create X" guide that starts by *finding* existing X has borrowed a step from a different job. (See
  "One document, one job" in `writing-docs` `doc-structure.md`.)

### 2. Section ledger

Make a table, one row per section: **section | Diataxis type | cadence | canonical home | load-bearing fact.**

- **Diataxis type** - classify every section, including the ones that look fine. Trigger the finding on the
  type, not on quality: a subsection narrating how something works ("...authentication flow", "how X works")
  is explanation; a table enumerating allowed values, fields, or methods ("supported ... reference", a field
  reference) is reference. Both inside a how-to are misplacement findings even when accurate and well
  written - accuracy is not the test, placement is. Such a section belongs in the feature or reference doc,
  cross-linked.
- **Canonical home** - where does this content already live, or where should it live? Reverse-lookup it:
  grep `docs/`, `schemas/`, and the code for the section's key identifier (the object, macro, parameter, or
  concept it is about); the document whose H1 or Overview claims that identifier as its subject is its home.
  If the home is another document, the row is a duplication-or-misplacement finding - cross-link, do not
  re-host. If two documents both claim it, the duplication itself is the finding. Use the anchors you find to
  judge placement, not only to confirm a link resolves. Run the grep before you call a new section a welcome
  addition: a section that re-teaches a mechanism another document owns (for example, filling a templated
  definition, which the app-reg-defs feature doc and its how-tos own) is a finding even when it is accurate
  and helpful - the reader now has two homes to keep in sync. Ownership is the test, not usefulness.
- **Cadence** - how often the section's reader runs it: once per repository, once per template, once per
  cluster, per environment, or recurring. Fill it for every row. If the rows show more than one cadence, the
  document fuses jobs - record it against the purpose line's fused-jobs check rather than letting a clean
  prose verdict absorb it.
- **Load-bearing fact** - name the one unique fact the section carries. A row with no unique fact, or whose
  fact is a tautology, is a value finding. (See "Section value audit" in `writing-docs` `doc-structure.md`.)

### 3. Coverage diff

List the domain surface for the document's topic from an **enumerable source**, and mark each item covered or
omitted. Omissions the document claims to cover are findings. Bound this to real, listable sources so it does
not drift into speculation:

- the object's schema fields and enum values (`/schemas/`, `modules/*/schemas/`)
- the object's section in `/docs/envgene-objects.md`
- the documented parameter catalog (`/docs/instance-pipeline-parameters.md`, `/docs/e2e-parameters.md`)
- the sibling how-tos and the feature doc's table of contents

Match the source to the document type. A how-to or reference about an object uses its schema and its
object-reference section: for a how-to about object X, the surface is "the configurations of X a reader could
need" - if the schema has RegDef v1 and v2 and the guide covers only v2, that gap is a finding. A tutorial or
README has no schema surface; there the surface is the set of tasks or entry points a reader expects, taken
from the sibling docs and the index. If a document genuinely has no enumerable surface, say so and skip the
diff rather than inventing one.

Anchor the diff to the object's full surface, not to the version the document declares. A guide that says it
uses v2 does not get its coverage measured against the v2 schema alone: if the reader's task ("configure a
registry") can also be done with v1 or through parameters, those are part of the surface, and their omission
is the finding. Enumerate every version and variant from the object reference (`/docs/envgene-objects.md`,
all `/schemas/`), and the parameter-driven path from the parameter catalog (`/docs/e2e-parameters.md`,
`/docs/instance-pipeline-parameters.md`), before you conclude "no gap". Measuring coverage against the single
version the document happens to use is how a real gap passes the review.

## Cross-cutting sweeps

Run every sweep below across the whole change, and account for each one in the review - as a finding or as an
explicit "checked, none". A sweep you do not mention reads as skipped, and a skipped sweep is how a known
class slips through: a configuration guide filed under "Migrations", a term capitalized three ways, an
inlined sample. Do not drop a sweep because the change looks clean to you; run it and say it is clean.

- **Vocabulary.** Does the change coin new labels for concepts the product already names? Grep the docs,
  schemas, and code for the established term and flag coinages. (See "Use existing vocabulary" in
  `writing-docs`.) Also check one term, one capitalization across all touched files - a term written three
  ways across H1, index, and a sample README is a consistency finding.
- **Index and naming coherence.** Are new docs in both index readmes, under the correct section (a
  configuration guide filed under "Migrations" is a finding)? Do title, filename, and index entry agree?
- **Samples and inlining.** Does a doc inline large concrete file content that should be a `docs/samples/`
  set and a link? (See `writing-docs` examples-and-samples.)
- **Grounding.** Every identifier, path, anchor, and reserved value the change states is verified against the
  code, schema, or target doc. A value presented as reserved that is actually free-form, or an example that
  contradicts the feature doc, is a correctness finding - not a style nit.

## Adversarial gate

Before a finding goes in the report, challenge it: **is this defensible, or am I over-reading?** State the
load-bearing fact of the finding and the rule or evidence behind it. If the author could reasonably defend
the current text (a real exception applies, the restatement is a sanctioned first-mention, the "duplication"
is an operational copy the reader acts on), drop it or downgrade it. A review that survives its own
skepticism is worth more than a long list.

Separate "out of scope" from "explained away". A placement, coverage, or fused-job issue in content this
change adds or rewrites stays a finding even when it is accurate, useful, or matches the document's existing
structure - those make it well executed, not correctly placed. Drop a finding only for a named exception: a
sanctioned first-mention, an operational copy the reader acts on, or pre-existing content the change does not
touch. "It reads fine" and "it is already like that elsewhere" are not exceptions.

When a finding depends on a product fact you are not certain of, verify it before stating it, or mark it an
open question - never assert it.

## Output

Produce a review with:

1. **Overview** - what the change does, which documents, the audience, the main message, the Diataxis types,
   and the CI status (one line, as context, not as findings).
2. **Cross-cutting findings** - account for every sweep here (a finding or an explicit "checked, none"), then
   **per-file findings**, each with: what, where (heading or quote), why (the rule or evidence), and a
   concrete direction. Mark non-blocking or author's-call items as such.
3. **One verdict** - approve, approve after fixes, or request changes. Not a scatter of remarks.

Prioritize: correctness and fitness-for-purpose findings first, then placement and duplication, then style.

Draft the review to `stuff/<pr-or-doc>-review.md` for the user to check before anything is posted. Publish
only when the user approves - a documentation review is outward-facing. When publishing to a PR, post one
review (a single body grouped as above) unless the user asks for inline per-line comments.

## Relationship to other skills

- **writing-docs** - the rules this skill reviews against. Load it; do not duplicate its rules here.
- **envgene-code-review** - code, not docs.
- **bdd-test-review** - a PR judged through its BDD scenarios and test data.
- **discrepancy-audit** - the explicit-trigger, report-only doc-vs-code-vs-schema reconciliation. This skill
  reviews a change for fitness and style; `discrepancy-audit` reconciles existing docs against the system.
