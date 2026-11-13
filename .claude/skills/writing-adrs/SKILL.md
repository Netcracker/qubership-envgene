---
name: writing-adrs
description: Write an Architecture Decision Record (ADR) as a readable MADR-based design-carrier - a narrative Context and problem statement, considered options with per-option pros and cons, a decision outcome, and consequences - scaled by change class. Use whenever the user wants to record, capture, or file an architecture decision. Trigger on phrases like "write an ADR", "record this decision", "make an ADR for X", "document why we chose Y", "add a decision record", or "log this design decision". Also use when a settled design or trade-off from the conversation needs a durable decision log entry. Produces an ADR under docs/adr/, one to two pages for a hard call, that a reader without prior context can understand.
---

# Writing ADRs

An ADR records one decision and the reasoning behind it, so future contributors understand why, and do
not silently reverse or re-litigate it. Its value is that the decision is understood, not that it is
short. An ADR is a design-carrier: a reader who was not in the room must be able to follow what was
wrong, what options were weighed, what was chosen, and what it costs. Write it to be read, not skimmed.

## A readable design-carrier, not a terse draft

This skill follows the MADR form (Markdown Any Decision Records): a narrative context, explicit
considered options with per-option pros and cons, a decision outcome, and consequences. That is a
deliberate departure from the repo's terse-draft convention. The terse, fragment-and-scan style - short
lines, no narrative, detail pushed into YAML and inline comments - belongs to draft analysis under
`docs/analysis/`, where the audience is an expert skimming their own working notes. An ADR has a
different audience and a different job. It is the readable record a later contributor relies on, so it
carries prose that stands on its own.

Terse decision forms optimize for the expert skimmer who already holds the context. A one-sentence form
hurts readability for everyone else, which is why this skill does not use it. Readability beats
compression for a design-carrier.

## Scale the form to the change class

Two skeletons, picked by how much decision there is to carry.

- An architectural change uses the **full form** - every section, one to two pages. Reach for it when
  the decision shapes how the system is built, trades off real alternatives, or must be understood by
  someone outside the conversation.
- A bounded change uses the **minimal form** - the three core sections only, kept short. Reach for it
  when the decision is small and self-contained but still had a real choice behind it.
- A bounded change with no real decision has no ADR at all. That gate lives in the
  `envgene-analyst-authoring` flow, not here - this skill is only a pointer to it.

## Non-negotiables

- **One decision per file.** Two decisions mean two ADRs. If you are tempted to add a second decision,
  split the file.
- **Say why.** Each choice carries the reason that drove it. A bare assertion, like "the app chart uses
  the group repository", makes the next reader reverse-engineer the motive, which is exactly the recall
  an ADR exists to prevent.
- **State a downside.** Every real decision costs something. The Consequences must carry at least one
  Negative, and the chosen option's pros and cons must name what you accept. An ADR with only upsides is
  hiding the trade-off, and a reader cannot trust a record that reads as a sales pitch.
- **No code references, describe in domain and behavior terms.** Do not name files, functions, classes,
  or modules in the prose. A code reference goes stale and belongs in the specs or the dev-design, not in
  a durable decision record. Prefer naming the observable behavior or the documented object over the code
  that implements it, for example "the effective set resolves the profile by signal-gated side selection"
  over naming the resolver class and the method it calls. A design mechanism that is not a code symbol is
  still implementation: a flag, toggle, input, knob, or its default and on/off state describes how the
  decision is wired, so state the observable behavior it produces instead. Prefer "the cleanup context is
  generated for every namespace in No-CMDB v1 and not in No-CMDB v2" over "an input defaults to off, when
  on the generator produces the cleanup context, and the pipeline sets the input on for the legacy flow".
- **No Date field.** The commit history is the authoritative date.
- **No implementation-status prose.** An ADR records the decision, not whether the code exists yet. Do
  not write that the decision is "ahead of implementation", "not yet wired", "doc-ahead", or holds "until
  that lands". Lifecycle lives in the `Status` field (`Proposed` before agreement, `Accepted` after) and
  in the commit history. A prose status note goes stale the moment the code merges, and a durable record
  that contradicts reality is worse than none. If you need to point at the implementing change, link the
  PR or issue under More information instead of narrating its progress.
- **Capture the whole decided model.** When writing or revising, cross-check the decision against the
  source model and add any rule that is missing, including small normalization or edge-case rules (for
  example, how an empty value is treated). Do not drop a settled rule to save space. Do not assume the
  existing text is complete.
- **When revising, audit the whole document.** Apply every rule in this skill to the entire ADR, not
  only the lines you set out to change. This differs from the `writing-docs` scope, which limits style
  fixes to new and modified content only. Check all sections against these rules and against the source
  decision before you submit any revision.

## Full form (architectural change)

```markdown
# ADR-NNNN: <the decision in plain terms, as a title>

Status: Proposed

## Context and problem statement

<2-4 sentences, or a short illustrative story. What is wrong and why it is urgent now, in domain
vocabulary a reader without prior context can follow. Make them curious.>

## Decision drivers            (optional)

- <force 1 - what the decision must satisfy>
- <force 2>

## Considered options

- <Option A - the chosen one>
- <Option B>
- <Option C>

## Decision outcome

Chosen: <Option A>, because <one line - why it wins>.

<Optional worked example or before -> after showing the chosen option in action.>

## Pros and cons of the options

### <Option A> (chosen)

- Good, because <...>
- Neutral, because <...>
- Bad, because <... - the cost we accept>

### <Option B>

- Good, because <...>
- Bad, because <... - why it lost>

### <Option C>

- Bad, because <...>

## Consequences

- Positive: <what this makes true>
- Negative: <the accepted cost, or who must now do X>

## More information            (optional)

- Specs: <link to specs/ for the behavior detail>
- Proposal: <link>
```

## Minimal form (bounded change)

```markdown
# ADR-NNNN: <title>

Status: Proposed

## Context and problem statement

<2-3 sentences: what is wrong, why now.>

## Considered options

- <A (chosen)>, <B>, <C>

## Decision outcome

Chosen: <A>, because <reason>. Rejected <B> and <C> because <one clause each>.
```

## Writing each section

- **Title.** Name the decision in plain terms, not a topic. Good: "Adapt registry auth from e2e
  params". Weak: "Registry authentication".
- **Context and problem statement.** A narrative that conveys urgency and is understandable without
  prior context. The problem statement may be free form in two to three sentences, or in the form of a
  short illustrative story, and it should convey a sense of urgency and make the reader curious. State
  the forces in tension, not the project's chronology. An illustrative story is welcome when it carries
  the urgency. A history lecture is not - give the reader the forces, not the timeline.
- **Decision drivers.** The forces the decision must satisfy, as a bullet list. Optional - include them
  when they are not already obvious from the problem statement.
- **Considered options.** An explicit list of the chosen option and the real contenders. This is the
  line people cite years later to avoid redoing dead work, so name the genuine alternatives.
- **Decision outcome.** State the choice plainly in one line, with the reason it wins. It may carry one
  worked example or a before -> after illustration showing the chosen option in action.
- **Pros and cons of the options.** The chosen option and the real contenders each get their own pros
  and cons, labeled "Good, because", "Neutral, because", and "Bad, because". The chosen option must
  carry at least one "Bad, because" - the cost you accept. Each rejected option must carry the "Bad,
  because" that explains why it lost.
- **Consequences.** At least one Positive and at least one Negative. The Negative is required, not
  optional - it is the cost you accept or the party who must now do something new.
- **More information.** Links out for depth - the specs that carry the behavior detail, the proposal,
  the implementing issue. Push detail here and into the specs and dev-design rather than growing the ADR.

### State the reason in the same breath as the choice

Pair each choice with its reason, so the trail survives without the surrounding conversation.

Bare, hard to recall later:

```markdown
- The app chart always uses the group repository, regardless of the Maven channel.
- The app chart is required. Generation fails when the DD names no chart.
```

With the why, each line stands on its own:

```markdown
- The app chart uses the group repository regardless of the Maven channel, because the deploy side
  resolves it the same way and the SBOM must point at the identical chart.
- The app chart is required, so a missing chart fails fast with a readable error instead of a silently
  incomplete result downstream.
```

### Keep detail out of the ADR

The ADR carries the decision and its reasoning. The behavior detail lives in the specs, and the
implementation detail lives in the dev-design. One diagram per option is allowed inside the ADR, when a
picture carries an option better than prose. More than one diagram, or inline code, crosses the line
into a design doc squeezed into an ADR - push that detail out.

## Style

Readability comes from clear prose, not from padding. Tighten wording and move detail out, but never at
the cost of the downside, the alternatives, or a settled rule.

- Cut sales-pitch language. Check every adjective and adverb: is it needed, and is the claim behind it
  true? If not, delete it. "Clean, elegant, robust" earns nothing.
- Prefer plain declaratives over hedging. "We do X" beats "It is proposed that X may be".
- Follow the repo's `writing-docs` rules. In particular: plain hyphens, never em or en dashes. No
  semicolons, split into separate sentences. 120-character lines, sentence-case headings. An ADR is a
  repo doc like any other.
- When a section enumerates cases, options, warnings, or rules, present each one as a bullet, not as a
  run-on inline sentence. One item per bullet, and one distinct rule per bullet. Do not restate the same
  fact as both a mechanism bullet and its outcome. A sentence that lists several items separated by
  semicolons, or by repeated use of "and", is an enumeration and must be rewritten as a bulleted list.
  This applies when revising existing prose too, even if the surrounding text is unchanged.

  Anti-example: "We emit warnings for missing keys; null values; and unknown fields." becomes:

  ```markdown
  We emit warnings for:

  - Missing keys
  - Null values
  - Unknown fields
  ```

- State findings qualitatively, not with exact counts or measurements. "A corpus scan found no
  divergences" instead of "753 environment definitions, 2033 namespaces". Specific numbers age and
  belong in the analysis or ledger, not in the durable ADR.

## When generated from a session

When an ADR is generated from a design session, the session is already readable - it has a narrative and
a concrete example. Carry that readability into the ADR. Preserve the narrative and the concrete example
from the session rather than distilling it into headline fragments. The job is to turn readable
discussion into readable prose, not to compress it into a cryptogram. This is the skeleton the analyst
authoring flow fills, co-located with the craft because the ADR is not an OpenSpec artifact.

## Filing

- Path: `docs/adr/NNNN-kebab-title.md`, number zero-padded (`0001`, `0002`, ...). Next number is the
  highest existing plus one. If `docs/adr/` does not exist yet, start at `0001`.
- Status lifecycle: `Proposed`, then `Accepted` once agreed, then `Superseded by ADR-XXXX`. Never edit
  an accepted ADR's decision to reverse it. Write a new ADR that supersedes it and flip the old one's
  status. The trail is the point.
- Link out for depth: put the specs, proposal, issue, or flow.md references under More information so
  the ADR stays a design-carrier while the details live where they belong.

## Anti-patterns

Reject these. They are the failure modes that make an ADR untrustworthy or unread.

- **Fairy Tale.** An option or a Consequences section with only pros and no cons. Every real option
  costs something, and a record that hides the cost cannot be trusted. Name the "Bad, because" and the
  Negative.
- **Free Lunch Coupon.** Consequences omitted or buried, so the reader never learns what the decision
  makes true and what it costs. The Consequences section is required, and it must carry a Negative.
- **Tunnel Vision.** Context stated in isolation, with the operational and maintenance perspective
  missing. Ask who runs and maintains the result, and let their forces into the problem statement and
  the pros and cons.
- **Mega-ADR.** A whole design doc squeezed into one ADR - multiple diagrams, inline code, or exhaustive
  behavior detail. Push that detail to the specs and the dev-design. One diagram per option is the line.
```