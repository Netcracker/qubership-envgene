# Source: an existing design doc or PR

Parse an existing design artifact and generate the CR body. Use this when the input names a doc PR
(URL or number) or a path to a `docs/features/*.md` file. The pipeline (dry-run default, link rigor,
filing, AGENTS compliance) lives in `SKILL.md`. This file covers only the parse-and-generate
mechanics.

## 1. Resolve the source

Take one of two inputs. If the user provides neither, ask which.

- **`pr <number-or-url>`.** Call `mcp__github__pull_request_read` with `method: get` to confirm the
  PR exists and to capture `head.sha` for later permalinks. Then call `method: get_files` and filter
  the changed paths to `docs/features/*.md`. If several feature docs are touched, list them and ask
  which one to use. Run the flow once per chosen file if the user wants multiple issues.
- **`file <path>`.** Read the file. Verify it lives under `docs/features/`. If it does not, fail loud
  rather than parsing an arbitrary Markdown file as a feature doc.

Capture the SHA the body will pin to: `head.sha` for a PR, or `git log -1 --format=%H -- <path>` for
a committed local file. If a local file is uncommitted, follow the placeholder rule in the shared
link-rigor section.

## 2. Parse the feature doc into sections

Map the doc's structure onto the `creating-cr.md` sections best-effort, by heading text. Feature docs
vary, so match on any of these cues:

- **Issue title** - the H1. See title derivation below.
- **Context** - the first non-heading paragraph, or `## Description` / `## Overview` / `## Problem`.
  State the situation, not the action.
- **In scope changes** - `## Changes` / `## Components where behavior changes` / `## Requirements` /
  top-level numbered lists. Structure per the flat/grouped rule.
- **Acceptance** - `## Acceptance` / `## Acceptance criteria` / `## Results` / observable behavioral
  statements. Observable and testable.
- **Implementation notes** - mentions of "PoC", "for now", "out of scope", named libraries, `@user`
  contacts, "use the X pattern". Emit only if such hints exist.

Do not derive `Out of scope changes` - that boundary is an analyst decision. Leave it for the user.

When a structural element is missing, generate the section with a `<!-- TODO: ... -->` placeholder
and explain the gap in the dry-run output rather than inventing content.

## 3. Derive the title

Take the doc's H1, tighten it (optionally with a phrase from Context), and keep it under about 70
characters. Prefix it with the issue-type tag per `creating-cr.md` (`[Feat:]`, `[Bug:]`, `[Story:]`,
or `[Docs:]`).

## 4. Per-item anchor permalinks

Each `In scope changes` item needs an inline anchor permalink to the design section that motivates
it. Compute the anchor and pin the SHA per the shared link-rigor rules. The source-specific part is
how to find the right section:

1. Identify the motivating design section by heading match, structural correspondence, or keyword
   match in the design text.
2. Attach the link to the most relevant noun in the item - the modified component, file, or schema
   field.
3. If no section matches, emit the item, append `<!-- TODO: link to specific design section -->`,
   and warn the user that the item is either a derived change (link to the file-level permalink and
   drop the TODO) or needs an addressable section added to the design. Do not block the dry run.

## 5. Flat or grouped in-scope list

Mirror the design's own structure. Do not impose a shape it does not have.

- If the design clusters changes under thematic headings (for example a `## Validation` section with
  several sub-rules), emit a grouped list: a top-level umbrella with sub-items.
- If the design is flat (each change is its own top-level concern), emit a flat list.
- Never nest more than one level deep.
- If a group would have a single sub-item, flatten it to a top-level item - a one-child group carries
  no signal.
- Every item and sub-item carries its own anchor link.

## Failure modes (this source)

- **Doc PR contains no `docs/features/*.md`.** Refuse and explain: the CR convention applies to
  implementation handoffs derived from feature docs. Suggest an analysis or investigation issue
  instead. Do not generate a draft.
- **Multiple feature docs in one PR.** List them and ask which one (or set) to use. Run the flow once
  per chosen file.
- **Feature doc lacks an Acceptance-like section.** Generate `## Acceptance` with
  `<!-- TODO: extract from design -->` and tell the user the section needs manual work.
- **`file` path is outside `docs/features/`.** Fail loud - it is not a feature doc.
