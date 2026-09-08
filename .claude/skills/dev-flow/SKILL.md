---
name: dev-flow
description: >-
  Orchestrate the design-to-code-PR delivery flow for a qubership-envgene change as a sequence of
  isolated phase subagents, each on an explicit model, handing work over through files rather than
  conversation history. Use this to run or resume the full flow - "run the dev flow for this change",
  "orchestrate design to PR", "drive this CR through plan, implement, review", "resume the flow", "what
  phase are we on" - or to run a single named phase (cr, plan, implement, review, verify) against a
  settled design. Each phase reads its entry artifact, invokes the right child skill, writes its exit
  artifact, updates the flow ledger, and returns only a short status. Keeps the orchestrator context
  small and routes cheap models to mechanical work. Do not use this to author a design from scratch
  (that is brainstorming), to write docs (writing-docs), or to file a CR directly (design-to-cr) - this
  wraps those, it does not replace them.
---

# dev-flow

Run the delivery flow - design, CR, plan, implement, review, verify - as a chain of **isolated phase
subagents**. Each phase is a fresh context that reads a file artifact, does its work through a child
skill, writes a file artifact, and returns a short status. The orchestrator stays thin, and each phase
runs on the cheapest model that fits.

## Why this exists

Running the whole flow in one growing conversation is expensive: the context is re-read on every turn,
at the session model's rate, for thousands of turns. Two levers fix it, and this skill encodes both:

- **Phase isolation (context stays small).** A subagent runs in its own context, transcript, and
  cache. Only a short result summary returns to the orchestrator, so the orchestrator does not grow as
  phases complete. Handing work over as files, not chat, is what makes a phase restartable from
  nothing.
- **Model routing (rate stays low).** Model tier is a function of a turn's judgement depth, not its
  importance. Mechanical and reversible work runs cheap, load-bearing judgement runs on a strong
  model. Because each phase is a separate dispatch, the model is chosen per phase.

## The invariant

If a phase cannot be run from scratch by reading only its entry artifacts, the hand-over artifact is
incomplete. That is the quality gate - not "it is convenient to continue in this chat". State lives in
git, the CR issue, and the ledger. A phase never reads "what we discussed".

## Phases at a glance

Read `references/phase-map.md` for the full per-phase contract (entry and exit artifacts, the child
skill, the dispatch prompt, and the model). Summary:

| Phase       | Child skill                     | Model (default)          | Exit artifact              |
|-------------|---------------------------------|--------------------------|----------------------------|
| design      | brainstorming + adrs + docs     | interactive, main loop   | ADR + doc edits + doc PR   |
| cr          | design-to-cr                    | Sonnet                   | CR issue (Story or Feature)|
| plan        | writing-plans                   | Sonnet                   | plan file + task briefs    |
| implement   | subagent-driven-development     | Sonnet controller        | code + tests + code PR     |
| review      | code-review (+ writing-gherkin) | Sonnet, Spec escalates   | review report + BDD slice  |
| verify      | none (CI poll)                  | Haiku or Sonnet, async   | green checks recorded      |
| acceptance  | none (human sign-off)           | human                    | sign-off recorded          |

`design` and `acceptance` are interactive and human-gated - the orchestrator prepares their inputs and
waits, it does not dispatch a subagent to hold a human dialogue. Everything from `cr` through `verify`
is dispatched.

## How to run

1. **Locate or create the ledger.** The ledger is `.superpowers/flow/<slug>.md`, git-ignored scratch.
   Its format and the resume protocol are in `references/ledger.md`. If a ledger for this change
   exists, read it and resume at the first unchecked phase. If not, create one from the template.
2. **Confirm the entry point.** A flow starts from a settled design - an ADR and a doc PR that a fresh
   reader can open. If the design is not settled, stop and run `brainstorming` first. This skill wraps
   the mechanical phases, it does not invent the design.
3. **Run one phase at a time.** For the current phase, dispatch exactly as `references/phase-map.md`
   specifies: the entry-artifact paths, the child skill to invoke, the exit-artifact path, and the
   model. Pass the model explicitly on every dispatch - an omitted model inherits the orchestrator's,
   which defeats routing.
4. **Gate between phases.** By default, after a phase completes, summarize its result in one or two
   lines and ask the user before starting the next phase. Run straight through only when the user asked
   for `auto`.
5. **Update the ledger, then continue.** Mark the phase complete with its exit artifact, append any
   ruling, and move on. The ledger - not this conversation - is the recovery map.

## Dispatch discipline

The whole cost argument rests on keeping the orchestrator thin. Hold to these:

- **Hand over files, never pasted context.** A dispatch prompt names the entry-artifact paths and the
  exit-artifact path. It does not paste prior-phase output or conversation history into the prompt. The
  subagent reads the files itself.
- **Return status, not content.** Each phase subagent writes its full output to the exit artifact and
  returns only: status, the artifact path, the identifiers it created (issue number, PR number,
  commits), and any concern. Do not ask it to echo the artifact back.
- **One phase, one dispatch.** Do not fan out phases in parallel - they depend on each other's exit
  artifacts. Within a phase, the child skill may fan out (implement dispatches implementers) - that is
  the child skill's job, up to the 3-layer spawn depth.
- **Explicit model always.** Every dispatch carries its model from `references/phase-map.md`. When a
  phase escalates a cheap turn to a stronger model, record why in the ledger.

## Model routing rules

The per-phase defaults are in `references/phase-map.md`. On top of them:

- **Sonnet is the floor for anything with a reasoning loop.** Haiku is for pure transcription and CI
  polling only. A weak model on branching work takes more turns and costs more overall - the false
  economy the routing exists to avoid.
- **Escalate to a strong model** when the entry artifact does not settle a fork, when an adversarial
  verification must genuinely refute a claim, or after a repeated failure in a fix loop.
- **The one expensive point inside implement** is the final whole-branch review - dispatch it on the
  most capable model. Implementers doing transcription from a complete plan run cheap.

## Reference files

- `references/phase-map.md` - the per-phase contract: entry and exit artifacts, child skill, dispatch
  prompt template, and model, for every phase.
- `references/ledger.md` - the flow-ledger format, the resume protocol, and the ruling log.
