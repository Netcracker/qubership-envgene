---
name: design-to-cr
description: >-
  This skill should be used when the user wants to turn a settled design into a change request (CR)
  issue in Netcracker/qubership-envgene. One pipeline - draft, validate, publish - runs the same no
  matter where the draft's material comes from. The source only seeds the first draft. Sources: an
  existing design doc or doc PR (parse it), or the working context - the conversation, code
  investigation, and memory (synthesize it). Trigger on "file a CR from this PR", "turn this feature
  doc into an issue", "doc PR to issue", "draft a ticket", "make a CR ticket in stuff/", "create the
  ticket then publish", or "file a Feature issue" for a settled design. Trigger this whenever the user
  is heading toward a qubership-envgene implementation CR, even if they do not name the format or say
  "CR" - filing an implementation issue from a design, a doc PR, or notes shaped from the working
  context all belong here.
---

# design-to-cr

Turn a settled design into a change request (CR) issue in `Netcracker/qubership-envgene`. A CR hands
a finished design to a developer for implementation: it cuts the implementation slice and states how
the work is verified. This skill produces the issue only. It never pushes branches or opens PRs -
shipping the design docs is a separate flow, and the CR just links to where that design lives.

The body format is the six-section convention in `docs/dev/creating-cr.md`, which is the single
source of truth for section order, meaning, and good/bad examples. Do not restate those sections
here or invent variants - open that file when writing the body. Two sections are optional and only
appear when the material genuinely exists - see `Optional sections` below.

Target repository is hardcoded `Netcracker/qubership-envgene`. Fail loud on any other repository.

A CR-ready draft is bounded and link-driven: it states the situation and problem in a few sentences,
points at a settled design with a durable link, cuts a numbered implementation slice where each item
names what it touches, and gives observable acceptance conditions. If the design is not settled or has
no addressable reference, the work is not ready for a CR - route the user to an analysis issue rather
than forcing a body.

## Pick the source

One pipeline - draft, validate, publish - runs the same regardless of source. The source only decides
how the first draft is seeded. Everything downstream - link rigor, iteration, filing, house rules - is
shared. Two sources:

- **An existing design doc or doc PR.** The input names a design artifact: a doc PR (URL or number) or
  a path to a `docs/features/*.md` file. Parse it into the draft. Read `references/from-doc-or-pr.md`
  for the parse-and-generate mechanics.
- **The working context.** There is no ready doc, so synthesize the draft from what the session already
  holds: the conversation, your code investigation, and memory. Read `references/from-context.md` for
  the synthesize-and-draft mechanics.

The source seeds the draft. It does not change the requirement for a `Design reference`: every CR links
a committed design doc or PR, even when the draft was synthesized from context rather than parsed from
that doc. When the source is ambiguous (a design doc exists but the user has not said whether to parse
it or synthesize), ask before doing work.

## Shared workflow

### Draft as a dry run by default

Creating an issue is outward-facing and hard to reverse, so never file on the first turn. Produce the
draft first as a local Markdown file in the user's scratch dir, and treat it as provisional until the
user gives an explicit go-ahead. The draft always carries an H1 title line plus the
`creating-cr.md` sections. Omit optional sections that are empty rather than filling them with noise.

### Optional sections

Two sections are optional and must never be padded to look complete. Add each only when its material
genuinely exists, and omit it entirely otherwise - an absent section reads better than an invented one.

- **Out of scope changes.** Include this only when there are real exclusions to name: work a reader
  might expect that this CR deliberately leaves out. Do not infer or invent exclusions - the boundary
  is an analyst decision, not something derivable from the design. When nothing is genuinely excluded,
  drop the section rather than writing "none" or padding it.
- **Covered cases.** Add this, right after `In scope changes`, only when the change enumerates
  discrete shapes or scenarios worth pinning as YAML, for example topology cases or credential shapes.
  When the change has no such enumerable cases, omit it.

### Analyst voice - name only the documented surface

A CR is read by a developer, but it is written by an analyst: it states the behavior contract and how
to verify it, and leaves the code mapping to the implementer. Keep the whole body - Context, In scope,
Acceptance, Implementation notes - in the design's own vocabulary, not the code's. Two habits carry
most of the weight:

- Name only the documented surface. Every object, job, field, parameter, or macro you mention should
  be findable in the product docs (feature docs, `envgene-objects.md`, `envgene-configs.md`,
  `template-macros.md`). If a name lives only in the code or is generated internally - a private
  function, a file path, an intermediate field the tool writes for itself - the reader cannot look it
  up, so describe the observable outcome instead. For example, prefer "the `current_env.cloud` macro
  resolves to the cluster name" over naming the resolver function and the internal field it writes.
- Verify before you name. Confirm each macro, field, or behavior against the docs or the code before
  stating it - do not infer which macro carries a value or which engine resolves it. A confident wrong
  claim costs the reader more than describing the effect and letting the implementer bind the mechanism.

State only settled behavior. If the design has not decided something (an extra warning, a side effect),
leave it out or raise it as an open question - do not write it into In scope or Acceptance as fact.
For Acceptance, when a condition has a sibling case (a mode set versus absent, a file present versus
missing), put the discriminating precondition in the Given so the outcome cannot be read as applying to
the sibling.

### Acceptance notation

Write each acceptance condition in collapsed Gherkin: `Given <fixture>, <observable outcome>.` The Given
states the prepared on-disk state, committed fixtures, and any run or placement mode. The rest collapses
Gherkin's When and Then into one observable-outcome clause. This complements, and does not replace, the
Acceptance principles in `docs/dev/creating-cr.md`, so honor those rather than restating them here.

- Make every outcome externally observable through an existing channel: a job log, a mock registry, an
  emitted request, or an error message. Prefer "the artifact is requested from registry X" or "the job
  fails with an error naming the missing definition and both checked locations" over internal state like
  "resolution uses the root-level copy". Give fixtures distinguishing traits so the outcome is checkable,
  for example a distinct registry name per copy so the request target reveals which copy won.
- Keep each bullet self-contained by inlining the observable contract. Do not link to use cases or design
  sections from inside an acceptance bullet.
- Enumerate every case that can fail independently, covering the happy path and each failure mode. A
  condition is redundant only when it cannot fail independently of the others, not when it is logically
  derivable. Do not fold distinct failures such as a missing folder versus a missing file into one bullet.
- When a placement or run mode appears in a Given, treat it as on-disk setup only. The rule "do not
  branch the implementation on the mode" is implementer guidance for Implementation notes, not an
  acceptance bullet.

Example:

> - Given an AppDef committed only under `configuration/` and none at the instance root, the job fails
>   with an error naming the missing definition and both checked locations.

### Design reference link rigor

The design-reference link, and each in-scope item's link, must survive the design PR's merge and the
deletion of its source branch. This rule holds for every source.

- In the `Design reference` section, use a PR reference like `#1198` (GitHub auto-links it and it
  stays after merge) and/or a commit-SHA permalink to the design doc, for example
  `https://github.com/Netcracker/qubership-envgene/blob/<sha>/docs/<path>.md`. Get the SHA from the
  PR head (`mcp__github__pull_request_read` method `get`, field `head.sha`), the merge commit, or
  `git log -1 --format=%H -- <path>` for a committed local file.
- Give each `In scope changes` item an inline anchor permalink to the specific design section that
  motivates it, on the most relevant noun (the modified file, schema field, job, or parameter):
  `https://github.com/Netcracker/qubership-envgene/blob/<sha>/docs/<path>.md#<anchor>`. Compute the
  anchor by lowercasing the heading text, replacing spaces with `-`, and stripping every non
  alphanumeric character except `-`.
- Never emit branch-pinned URLs (`.../blob/<branch-name>/...`) - they break on branch deletion.
- If the design doc is not yet committed, do not invent a SHA. Emit `<add permalink after
  committing>` as a placeholder and warn the user. Repo-relative links like `/docs/...#anchor` are
  acceptable only for docs guaranteed to land on the default branch.
- If an in-scope item has no matching design section (a derived change such as a test or refactor),
  append `<!-- TODO: link to specific design section -->`, link to the file-level permalink, and warn
  rather than blocking. The user decides whether to add an addressable section or accept the placeholder.

### Iterate to confirmation

Apply the user's edits and re-present the draft until they explicitly signal to file. The draft lives
in a local file, and the user may edit it by hand between turns, so re-read the file before every edit
rather than trusting the last write. Do not file until the user says so with words like `create`,
`file it`, or `publish`, and confirm once more before the write.

### Issue type and title

Match the GitHub issue type to the change's nature and prefix the draft's H1 accordingly, per the
`Issue type and title` section of `creating-cr.md`: Feature (`[Feat:]`), Bug (`[Bug:]`), or Story
(`[Story:]`, or `[Docs:]` for a documentation ticket). The H1 carries the prefix, so the filed issue
title carries it too.

### House-rule compliance

Keep the body publish-ready under the repository house rules in the `writing-docs` skill, even though the draft file
lives outside the repository: plain hyphen-minus for dashes (no em or en dash), no semicolons in
prose, wrap prose at 120 characters, vertically aligned table pipes, sentence-case headings, and
GitHub native callouts. Chat may be Russian, but the artifact ships in English. Run the pre-file gate
below before the `issue_write` call.

### Pre-file gate

Right before the `issue_write` call, re-read the final body and check it mechanically. Each item below
is a miss that has actually shipped in a filed CR, so treat them as blocking rather than advisory:

- Code references: no source file paths or modules (`python/...`, `scripts/...`, `src/...`, `*.py`,
  `*.java`, `*.ts`) and no private function or method names (`snake_case(`, `CamelCase(`). Documented
  product locations are fine (`cloud-passport/`, `configuration/credentials/`) - the test is whether a
  reader can look the name up in the docs, not whether it contains a slash.
- Undocumented identifiers: for every backticked object, field, or macro, confirm it appears in the
  docs. If it does not, replace it with the observable outcome.
- Links: no repo-relative `/docs/...` links in the issue body - GitHub renders them as dead paths.
  Use commit-SHA permalinks, pinned to the doc PR head commit when the doc has not merged yet.
- House rules (as stated under House-rule compliance): no em or en dashes, no semicolons in prose,
  prose wrapped at 120.

### File the issue

On the go-ahead, re-present the final draft, ask one confirmation question, and on `yes`:

1. Resolve the issue type with `mcp__github__list_issue_types` using **owner only**
   (`owner: Netcracker`, no `repo`). The repository-level call returns 404 for this org. Match the
   type to the change's nature (Feature, Bug, or Story; a docs ticket is a Story), and default to
   `Feature` if unclear.
2. Call `mcp__github__issue_write` with `method: create`, `owner: Netcracker`,
   `repo: qubership-envgene`, `type` = the matched type, `title` = the draft H1 (with its `[Feat:]` /
   `[Bug:]` / `[Story:]` / `[Docs:]` prefix), and `body` = the draft **without** the H1 line, so the
   body starts at `## Context`. Do not set labels.
3. Return the resulting issue URL.

## Guardrails

- Confirm once before creating the issue. Never create without an explicit go-ahead.
- Issue types for this org are org-level. Always query `list_issue_types` with owner only.
- Use the GitHub MCP tools, not the `gh` CLI, for reads and writes.

## Failure modes

- **No design reference.** The work is not ready for a CR. Say so and stop - a link-less CR cannot be
  scoped or reviewed.
- **Repository other than `Netcracker/qubership-envgene`.** Fail loud. The skill is hardcoded for this
  repository.
- Source-specific failure modes (a doc PR with no feature doc, multiple feature docs, a missing
  Acceptance section, an ambiguous draft path) live in the source references.

## Non-goals

- Do not push branches or open PRs. Doc shipping is a separate flow. The CR only links to it.
- Do not work cross-repo. Fork or adapt the skill for other repos.
- Do not auto-edit `docs/dev/creating-cr.md` or this `SKILL.md` from learnings. Learnings are
  advisory. The user applies them.

## Reference files

- Read `references/from-doc-or-pr.md` when the source is an existing design doc or PR (a doc PR or a
  `docs/features/*.md` path) - source resolution, the heading-to-section mapping, title derivation,
  per-item anchor matching, the flat/grouped list rule, and its failure modes.
- Read `references/from-context.md` when the source is the working context and no ready doc exists -
  input gathering, the `stuff/` draft path, section assembly, the re-read-every-turn rule, and the
  translate-to-English-before-filing rule.
