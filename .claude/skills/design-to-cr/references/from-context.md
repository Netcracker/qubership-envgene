# Source: the working context

Synthesize the CR draft from the working context - the conversation, your code investigation, and
memory - as a local Markdown file the user edits by hand across turns, then file it. Use this when
there is no ready feature doc to parse. The pipeline (dry-run default, link rigor, filing, AGENTS
compliance) lives in `SKILL.md`. This file covers only the synthesize-and-draft mechanics.

## Phase 1 - draft the local Markdown

Gather the inputs, asking only for what is missing:

- The change in one or two sentences (Context - the situation and the problem, not the action).
- The design reference. Apply the shared link-rigor rules. If no design reference exists, the work is
  not ready for a CR - say so and stop.
- The in-scope changes, numbered, each naming what it changes in the design's own terms (a documented
  object, schema field, job, or parameter, not a private function or file path), each with its anchor
  permalink.
- Optional: covered cases (enumerable shapes as YAML), acceptance conditions, implementation notes,
  and out-of-scope items (only if the user states them - never infer the boundary).

Pick the draft path. Default to the user's scratch area beside the cloned repository,
`<repo-parent>/stuff/<slug>-ticket.md`, where the slug is the kebab-case feature name. This directory
is outside the repository and is never committed. Confirm the path if it is ambiguous.

Write the file:

- Start with `# [<Type>:] <Title>` as the H1 - the issue title with its type prefix per
  `creating-cr.md` (backticks allowed for code).
- Follow with the `creating-cr.md` sections in order. Omit optional sections that are empty rather
  than leaving hollow placeholders.
- Keep items terse and link-driven.
- Apply the `AGENTS.md` house rules from the start so the body is publish-ready.

Print the path. Tell the user to edit it by hand and to say `file it` when ready.

## Phase 2 - manual iteration

The local Markdown is the living source of truth, and the user edits it directly between turns.

- **Re-read the file at the start of every turn, before any edit.** It may have changed since the
  last write, and acting on a stale in-memory copy would silently discard the user's hand edits. Do
  not assume the last write is still current.
- Apply the requested edits, keep the file AGENTS-compliant, and re-lint on request.
- Do not file the issue until the user explicitly asks.

## Phase 3 - file the issue

Trigger words: `file it`, `create the ticket`, `publish`. Before filing:

- **Translate any non-English prose to English.** Chat may be Russian, but the ticket ships in
  English. Do this on the draft as the last editing step, so the filed body is fully English.
- Follow the shared filing procedure in `SKILL.md`: confirm once, resolve the type owner-only, create
  with the matched issue type, title = the H1 text (with its type prefix), body = the draft minus the
  H1 line. Return the issue URL.

## Failure modes (this source)

- **Ambiguous draft path.** Confirm the `stuff/` location before writing rather than guessing where
  the user keeps scratch files.
- **Non-English prose still present at filing.** Translate before the `issue_write` call, not after.
