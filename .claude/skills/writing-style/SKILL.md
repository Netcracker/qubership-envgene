---
name: writing-style
description: >-
  House voice for any text this repository ships - the prose style, formatting, accuracy, and vocabulary
  rules every text obeys, whether it is documentation, a README, or the body of an issue, change request,
  pull request, ADR, proposal, or spec. Use this skill whenever you write, draft, review, or clean up any
  prose or Markdown for this repository, even when the user only says "write this up", "clean up this
  text", "fix the wording", or "make this publish-ready", without naming a style guide. Trigger it for
  removing em dashes, splitting semicolons, enforcing line length or sentence-case headings, aligning
  tables, naming a concept with the product's existing term, verifying an identifier, or linking between
  in-repo files. It is the base voice layer other writing skills build on: `writing-docs` adds the
  document-authoring layer (Diataxis structure, callouts, validated examples, sample sets) on top of this
  voice. Do not trigger for pure code, config-value edits, debugging, or linter or CI setup. The signal is
  authoring or polishing the wording of any text, not code.
---

# writing-style

The house voice for any text this repository ships - documentation, readme files, and the prose of
issues, change requests, pull requests, ADRs, proposals, and specs. These rules govern how the words read,
how the Markdown and YAML are formatted, and how identifiers and terms are kept accurate. The rules live in
reference files, each carrying the full rule with its rationale and examples. This file routes you to the
right one - open it before you write, do not work from memory.

This is the base layer. Any writing skill builds on it: `writing-docs` adds the document-authoring layer
(Diataxis document types, document mechanics, validated object examples, sample sets) on top of this voice.
Read `writing-style` first for the voice of any prose, then the document-authoring skill for the
document-level layer when you are authoring a doc deliverable.

The repository `AGENTS.md` keeps only the Git and pull-request process rules that sit outside the text
itself: commit messages, commit granularity, and pull-request scope. When those processes need a style
decision, they defer here.

## How to use this skill

Match the task to a reference file and read that file before writing. Most text work touches prose, so
`references/prose-style.md` is the common default - read it for almost any writing or editing task, then
add the file that fits the specific job.

| Task                                                                        | Read                        |
|-----------------------------------------------------------------------------|-----------------------------|
| Write or edit any prose - a doc, readme, issue, CR, PR, ADR, proposal, spec | `references/prose-style.md`  |
| Format Markdown or YAML - line length, lists, tables, link text, block YAML | `references/formatting.md`   |
| State an identifier, name a concept, define a term, or link in-repo files   | `references/integrity.md`    |

## Scope

Almost every rule applies to new and modified content only. When you edit an existing document, apply
the rules to the lines you add or rewrite. Do not reflow or restyle surrounding prose that you are not
otherwise changing - that produces large, noisy diffs unrelated to the task. Each reference file marks
the few rules that differ from this default.

## Reference files

- `references/prose-style.md` - dialect, dashes, semicolons, Oxford comma, heading case, compound
  modifiers, vocabulary, sentence craft, pronouns and modifiers, voice and tense, hedging, AI tells. The
  general voice layer for any text, including issue, CR, PR, ADR, proposal, and spec bodies.
- `references/formatting.md` - line length, lists (empty lines around), link text, tables (alignment and
  delimiter row style), and block-style YAML in examples. The universal Markdown and YAML layout rules.
- `references/integrity.md` - verify identifiers before stating them, use existing vocabulary, define
  every term once, do not re-gloss, and link in-repo with repo-root paths.
