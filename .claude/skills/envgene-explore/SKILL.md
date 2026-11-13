---
name: envgene-explore
description: >-
  Explicit trigger only - the first stage of the EnvGene analyst authoring flow, invoked deliberately by
  name when an analyst starts a new qubership-envgene change from a raw, unsettled idea. Interactive
  discovery: it takes a raw idea, task, or ticket and converges on a settled understanding of what to build
  and why, captured as one exploration brief the downstream crafts render from. It follows the brainstorming
  method for intent, researches how the system behaves today from code and docs, clarifies the ambiguities,
  and writes the brief that feeds the proposal, the specs, and the ADR, so those forms cannot drift. It
  produces only the brief - the proposal, specs, and ADR are authored downstream by
  `envgene-analyst-authoring`, the implementation design is envgene-design, and a docs-vs-code audit is
  discrepancy-audit.
---

# envgene-explore

The first stage of the analyst authoring flow for a qubership-envgene change. It takes a raw
idea, task, or ticket and converges on a settled understanding of what to build and why - just enough
for the downstream crafts to render the proposal, the specs, and the ADR, without any of them going back
to the analyst.

The output is one working document, the **exploration brief**. Everything downstream renders from it.
That is the whole point: when the proposal, the specs, and the ADR all trace to one settled brief,
they describe the same change at different levels of detail and cannot drift apart. This mirrors the
one-case-list-N-projections discipline the `writing-gherkin` skill uses for scenarios, applied one
level up to the change itself.

This skill is a thin orchestrator. It stands on two existing capabilities and owns only the glue between
them plus the brief:

- Intent discovery adapts the superpowers brainstorming method, inlined here (attributed at the end) so the
  skill carries no dependency on that plugin being installed.
- Current-behavior research invokes the built-in read-only `Explore` agent plus direct reading of code,
  docs, and schemas.
- This skill owns the clarify pass, the convergence, and the brief itself.

Adapt rather than reinvent, because the brainstorming method and the Explore agent are already good at their
jobs. The value this skill adds is the convergence and the single shared brief, not a second copy of
divergent questioning or codebase search.

## Interactive, not autonomous

Unlike the downstream crafts, which run near-autonomously once the brief is settled, explore asks the
analyst and plays findings back. Discovery is where the human knows things the code and the ticket do not,
so the conversation is the work, not an interruption to it.

## The five phases

Run these in order, but loop back when research or clarification reopens intent. The phases are
territory, not a rigid script.

### 1. Brainstorm - diverge to find intent

Diverge to find what the analyst actually wants and why, before any options. The method, adapted from the
superpowers brainstorming skill (attributed at the end of this file):

- Open questions before options. Ask what the change is for and who it serves before proposing shapes.
- One question at a time. Do not dump a list of questions. Prefer multiple choice when the analyst is
  unsure, and offer a concrete guess they can correct when they say "you decide".
- Play findings back in small chunks as you understand them, and cover goals, non-goals, and anti-goals
  (what would make this a failure even if it technically works), prior art, current state, and the
  how-it-gets-made choices the analyst wants to make versus hand to you.
- Write back your understanding and separate what the analyst said from what you assume, so the analyst can
  correct the assumptions. Only what the analyst said goes into the brief as theirs.

The method is inlined here on purpose, so explore does not depend on a brainstorming plugin. Do not invoke a
brainstorming skill as a live skill even if one is present, because it would load its own approval gate and
its own design-document output, which collide with explore's single brief and single gate. The `Explore`
agent in phase 2 is the opposite case: you do invoke it, because it is a built-in agent that runs in
isolation and returns data, so none of its own instructions leak back here.

Brainstorm diverges. The clarify pass (phase 3) is the opposite motion - do not try to close every
ambiguity here.

### 2. Research - ground how the system behaves today

Before converging on a change, understand the baseline it changes. Start from the stable anchors:
`AGENTS.md` for orientation, `docs/glossary.md` for the terms the change touches, the living specs
(`openspec list --specs`, then `openspec show <spec> --type spec` for the related ones) for the current
behavior contract, and the concrete object examples under `docs/examples/` and sample sets under
`docs/samples/` for the shapes. Then use the `Explore` agent for broad read-only codebase search when you
need to sweep many files or naming conventions, and read code, docs under `docs/`, and schemas under
`schemas/` directly when you know where to look.

Ground every claim about current behavior in something you read, and record where you read it. The
brief's Current-behavior section carries provenance - a file path, a doc, a schema - so the downstream
crafts and the reviewer can trust the baseline without re-deriving it. This is the same honesty the
downstream specs demand: say what is evidence and what is inference.

Do not use `discrepancy-audit` here. It is a report-only audit that reconciles docs against code for a
settled topic. Discovery is open-ended and interactive, so it is the wrong shape.

### 3. Clarify - converge to kill ambiguity

A thin questioning pass of this skill's own. After brainstorm has found the intent and research has
grounded the baseline, there will be underspecified areas and ambiguities that would force a
downstream craft to guess. Surface them to the analyst and resolve them now.

This is distinct from brainstorm on purpose. Brainstorm diverges to discover intent, clarify converges
to remove ambiguity before you write the brief. Keep it thin - a handful of pointed questions on the
things that are genuinely unsettled, not a re-run of the whole brainstorm. A good clarify question
names the specific fork and why it matters downstream, for example "does this apply to the No-CMDB v1
flow too, or only v2 - the specs will cover one case list or two depending on the answer". A term that is
not in the glossary or the docs is a question, not an assumption - surface it rather than guessing its
meaning, and note a genuinely new term as a glossary candidate for the hand-off.

### 4. Converge - write one exploration brief

Pull the brainstorm, the research, and the clarifications into the single brief, using the section
template below. Write each section for its downstream consumer. The brief is the one source every
downstream craft projects from, so a gap here becomes a gap in the proposal, the specs, and the ADR at
once - and, equally, a settled point here keeps all three consistent. Classify the change as you converge,
say the class out loud so the analyst can overrule it, and let research or clarify upgrade it if the change
turns out larger than it looked.

The brief is working material, not a durable repo doc, so keep it as a working note rather than a
committed file. It is not a change artifact - the change folder holds the proposal, the specs, and the
rest, which the authoring phase sets up later. Do not create an OpenSpec change folder or claim a change
id here. Discovery produces the brief and may conclude the change is not worth doing, so scaffolding a
change at this stage would be premature.

### 5. Human gate - confirm the brief is settled

Play the finished brief back and ask the analyst to confirm it is settled before it goes downstream.
This is the one hard checkpoint. The downstream crafts run near-autonomously and trust the brief as
settled, so an unconfirmed brief silently propagates its gaps into every artifact. Do not hand off
until the analyst agrees the brief captures what to build and why. Explore never self-certifies this
gate - it always needs the analyst and does not proceed past it unattended, even when it applied the
inlined brainstorming method along the way.

## The exploration brief

One document, these sections, in this order. Each maps to a downstream consumer so nothing is written
that no craft will use, and nothing a craft needs is missing. Keep each section to what it uniquely
contributes - the brief is working material, so favor tight prose and inline YAML over long narration.
The analyst passes the brief to each downstream craft as its source, rather than the craft discovering
it on its own.

- **Change class** (bounded or architectural) - bounded is a change to a flow that already exists here,
  such as a parameter, a small endpoint, or a one-module fix. Architectural is a new capability, an
  interface others depend on, or a change across modules. When in doubt take architectural. Complexity
  found later upgrades the class, and nothing downgrades it. State the class so the analyst can overrule
  it, because it scales how much the authoring phase does.
- **Problem / Why** - the problem this change solves and why it matters now. Feeds the proposal. This is
  the analyst voice - the user-visible problem, not a solution in disguise.
- **Current behavior** - how the system behaves today, the baseline the change moves. Every claim
  carries its provenance (file, doc, or schema path). Grounded in phase 2, it grounds the proposal and the
  specs, so the downstream crafts and the reviewer trust the starting point.
- **Intended behavior / cases** - the observable cases the changed behavior must satisfy: the happy
  path per valid combination and each independent failure mode. Feed the specs, so enumerate them
  observable, one case per distinct outcome.
- **Decision + rejected alternatives** - the approach chosen paired with the force that drove it, the cost
  or trade-off the chosen approach accepts, and the real alternatives rejected with a one-clause reason
  each. Feed the ADR. Capturing the accepted cost here is what lets the ADR carry a Negative consequence
  and the chosen option's downside that trace back to the brief rather than being invented at ADR time, and
  capturing the rejected options is what stops the team re-litigating dead ends later.
- **Entities / contracts** (optional) - when the change introduces a new object or data shape, its
  structure and invariants. These feed the specs as requirements (the structural contract stated as
  invariants), and the schema that encodes them is left to implement. Include this only when the change
  adds a new object worth pinning. Omit it when the proposal and specs carry the whole change.
- **Open questions / provenance** - what is still unresolved and must be settled downstream or by the
  analyst, plus a consolidated note of the sources the brief rests on. An honest open-questions list is
  not a failure of discovery - it is the brief telling the next stage exactly where it still needs a
  human.

## House style

The brief is prose this repository produces, so follow the `writing-docs` house style for it: plain
hyphen-minus dashes (never em or en dashes), no semicolons in prose, sentence-case headings, and lines
wrapped at about 120 characters. Use block-style YAML for any object examples, never inline flow maps.
Keep it lean - the brief earns its keep by being read and projected from, not by being exhaustive.

## Attribution

The brainstorm phase adapts the brainstorming method from obra/superpowers (MIT, Copyright (c) 2025 Jesse
Vincent).
