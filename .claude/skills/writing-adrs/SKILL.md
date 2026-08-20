---
name: writing-adrs
description: Write an Architecture Decision Record (ADR) in a terse, one-page house style. Use whenever the user wants to record, capture, or file an architecture decision. Trigger on phrases like "write an ADR", "record this decision", "make an ADR for X", "document why we chose Y", "add a decision record", or "log this design decision". Also use when a settled design or trade-off from the conversation needs a durable decision log entry. Produces a short Nygard-format ADR under docs/adr/. Keep it to one page and never let it grow into a design doc.
---

# Writing ADRs

An ADR records one decision and the reasoning behind it, so future contributors understand why, and
do not silently reverse or re-litigate it. Its value is the rationale, not the length. A bloated ADR
is a failed ADR: nobody rereads a wall of text, so the decision trail is lost anyway. Default to
short.

## Non-negotiables

- **One decision per file.** Two decisions mean two ADRs. If you are tempted to add a second
  `## Decision`, split the file.
- **One page.** A slide's worth of prose for an easy call, a page for a hard one. If it runs longer,
  the analysis belongs in a linked design doc, not here.
- **State a downside.** Every real decision costs something. An ADR with only upsides is hiding the
  trade-off. Name at least one negative consequence you accept.
- **No diagrams, no code, no deep dives.** Link them. The ADR carries the choice and the why, nothing
  that needs scrolling.

## Format

Use the five Nygard sections. Nothing more.

```markdown
# ADR-NNNN: <short imperative title, for example "Adapt registry auth from e2e params">

Status: Proposed | Accepted | Superseded by ADR-XXXX
Date: YYYY-MM-DD

## Context

<2-3 sentences. The forces that make a decision necessary: the problem, the constraint, what is in
tension. Not a history lesson.>

## Decision

<What we do, present tense, 1-3 sentences: "We do X.">

Rejected:

- <option A>, because <one clause>.
- <option B>, because <one clause>.

## Consequences

- <what gets easier or what this unlocks>
- <the cost we accept, required, not optional>
```

- **Title**: a short present-tense imperative, the decision itself, not a topic. Good: "Adapt registry
  auth from e2e params". Weak: "Registry authentication".
- **Rejected alternatives**: option titles plus a single `because` clause each, as a bullet list. This
  is the line people cite years later to avoid redoing dead work, so name the real contenders, but
  resist per-option pros and cons prose. One clause conveys enough. With one or two contenders you may
  fold them into the Decision sentence instead.
  Rejected holds decision-level alternatives, other ways to solve this problem that a reviewer might
  propose. Litmus: would someone offer this instead of the whole decision? If yes, it belongs here. If
  it is a knob within the chosen design (how it persists, what it is gated on), it states how the
  decision works and belongs in Decision, not here.
- If the whole decision fits one sentence, a Y-statement replaces the prose: *"In the context of \<use
  case\>, facing \<concern\>, we chose \<option\> to achieve \<quality\>, accepting \<downside\>."*

## Style

Terseness comes from tighter wording and moving detail out, not from dropping the downside or the
alternatives.

- Cut sales-pitch language. Check every adjective and adverb: is it needed, and is the claim behind it
  true? If not, delete it. "Clean, elegant, robust" earns nothing.
- Prefer plain declaratives over hedging. "We do X" beats "It is proposed that X may be".
- Follow the repo's `writing-docs` rules. In particular: plain hyphens, never em or en dashes. No
  semicolons, split into separate sentences. 120-character lines, sentence-case headings. An ADR is a
  repo doc like any other.

## Filing

- Path: `docs/adr/NNNN-kebab-title.md`, number zero-padded (`0001`, `0002`, ...). Next number is the
  highest existing plus one. If `docs/adr/` does not exist yet, start at `0001`.
- Status lifecycle: `Proposed`, then `Accepted` once agreed, then `Superseded by ADR-XXXX`. Never edit
  an accepted ADR's decision to reverse it. Write a new ADR that supersedes it and flip the old one's
  status. The trail is the point.
- Link out for depth: put "see design doc, issue, or flow.md" references at the bottom so the ADR stays
  one page while the details live where they belong.

## Anti-examples

Reject these. They are the failure modes that make ADRs unread.

- A Context that recounts the project's history for three paragraphs. Cut to 2-3 sentences of forces.
- Considered options with a good, bad, and neutral table per option. Use titles plus one `because`.
- A Consequences section listing only benefits. Include the cost.
- Architecture diagrams or code pasted inline. Link a design doc.
