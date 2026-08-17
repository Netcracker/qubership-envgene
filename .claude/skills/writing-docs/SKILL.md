---
name: writing-docs
description: >-
  House style guide for writing or editing any text this repository ships - documentation, README
  files, and the prose of issues, change requests, and pull requests. Use this skill whenever you
  write, draft, review, or clean up a `.md` file, a README, a doc under `docs/` (how-to, tutorial,
  feature doc, use case), or an issue, CR, or PR body - even when the user only says "write docs",
  "review my doc before the PR", "update the readme", or "fix this doc", without naming a style guide.
  Trigger it for tasks like fixing callouts, tables, lists, or headings, enforcing line length or
  sentence-case headings, removing em dashes, checking prose against the style rules, structuring a
  document with Diataxis, verifying identifiers, or producing a validated object example or sample
  file. Do not trigger for pure code, config-value edits, debugging, linter or CI setup, or
  answering a factual question about an identifier, even when docs are nearby. The signal is authoring
  or polishing prose and Markdown, not code.
---

# writing-docs

House rules for how text is written in this repository. They apply to documentation under `docs/`, the
README files, and any prose the repository produces for issues, change requests, and pull requests. The
rules live in reference files, each carrying the full rule with its rationale and examples. This file
routes you to the right one - open it before you write, do not work from memory.

The rules are the source of truth for prose and Markdown style. The repository `AGENTS.md` keeps only
the git and pull-request process rules that sit outside the text itself: commit messages, commit
granularity, and pull-request scope. When those processes need a style decision, they defer here.

## How to use this skill

Match the task to a reference file and read that file before writing. Most doc work touches prose, so
`references/prose-style.md` is the common default - read it for almost any writing or editing task, then
add the file that fits the specific job.

| Task                                                                         | Read                                 |
|------------------------------------------------------------------------------|--------------------------------------|
| Write or edit any prose - a doc, README, issue, CR, or PR description        | `references/prose-style.md`          |
| Format Markdown - lists, tables, ToC, callouts, links, line length, headings | `references/markdown.md`             |
| Structure a document or shape its sections - Diataxis type, section value    | `references/doc-structure.md`        |
| State an identifier, define a term, or link between in-repo files            | `references/content-integrity.md`    |
| Write a YAML or JSON object example, or build a `docs/samples/` set          | `references/examples-and-samples.md` |
| Write a use case under `docs/use-cases/`                                     | `references/use-cases.md`            |

For a substantial new or reworked document you touch several of these. A typical feature doc needs
prose style, Markdown formatting, document structure, content integrity, and validated examples. Read
each file whose column matches what you are about to write rather than guessing the rule.

## Scope

Almost every rule applies to new and modified content only. When you edit an existing document, apply
the rules to the lines you add or rewrite. Do not reflow or restyle surrounding prose that you are not
otherwise changing - that produces large, noisy diffs unrelated to the task. Each reference file marks
the few rules that differ from this default.

## Reference files

- `references/prose-style.md` - dialect, dashes, semicolons, Oxford comma, heading case, compound
  modifiers, vocabulary, sentence craft, pronouns and modifiers, voice and tense, hedging, AI tells.
  The general style layer, reusable for any text including issue and CR bodies.
- `references/markdown.md` - lists, table of contents, line length, callouts, heading numbering,
  tables, link text, heading renames and cross-links, file naming.
- `references/doc-structure.md` - the Diataxis document types, the voice and structure rules that keep
  each section carrying only what it uniquely contributes, and keeping the index readmes current.
- `references/content-integrity.md` - verify identifiers before stating them, use existing vocabulary,
  define every term once, do not re-gloss, link in-repo with repo-root paths, and run the pre-flight
  linters and final checks before a doc is done.
- `references/examples-and-samples.md` - validated object examples inside docs, and copyable sample
  file sets under `docs/samples/`.
- `references/use-cases.md` - use cases under `docs/use-cases/` as observable behavior that doubles as
  test-design input.
