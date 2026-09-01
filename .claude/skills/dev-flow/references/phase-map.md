# Phase map

The per-phase contract. Each phase lists its entry artifacts (what a fresh subagent reads), the child
skill it invokes, the exit artifact it writes, the model it runs on, and the dispatch prompt template.
Substitute the bracketed values from the ledger before dispatching.

A dispatch prompt never pastes prior-phase output or conversation history. It names file paths and the
child skill. The subagent reads the files itself and writes its full output to the exit artifact,
returning only a short status.

## design (interactive, not dispatched)

- **Entry:** the ticket or idea, plus the code the change touches for grounding.
- **Child skill:** `brainstorming`, then `writing-adrs` and `writing-docs`.
- **Exit:** an ADR under `docs/adr/`, the doc edits, and a doc PR.
- **Model:** interactive in the main loop. Brainstorming has a hard human-approval gate, so it is not
  handed to a subagent that cannot hold the dialogue.
- **Note:** the flow proper begins once the design is settled and addressable. Verify before leaving
  this phase that a fresh reader could open the ADR and doc PR and understand the change. Ground every
  named identifier against the code before it enters the docs - an ungrounded claim here costs a full
  rewrite cycle downstream.

## cr

- **Entry:** the ADR and doc PR permalink from `design`.
- **Child skill:** `design-to-cr`.
- **Exit:** a filed CR issue (Story or Feature), its number recorded in the ledger.
- **Model:** Sonnet. This is transcription of a settled design into the CR format, not fresh judgement.
- **Dispatch prompt:**
  > Read the design at [ADR path] and the doc PR [#NNNN]. Invoke the design-to-cr skill to draft and
  > file a CR for this change. The design is settled - do not redesign. Follow the skill's dry-run
  > discipline and house rules. Carry into Implementation notes the design-time seam hint from
  > [ledger ruling / design doc]: reuse the existing mechanism, and if it is not directly reusable,
  > extract a helper rather than adding a parallel path. Do not write any "docs are ahead of code" meta
  > line. When filed, return the issue number and the draft path only.

## plan

- **Entry:** the CR issue number and the design permalink.
- **Child skill:** `writing-plans`.
- **Exit:** a plan at `docs/superpowers/plans/YYYY-MM-DD-<slug>.md` with per-task briefs and Global
  Constraints.
- **Model:** Sonnet. Structured authoring from a settled design. Escalate to a strong model only if the
  design carries a load-bearing unknown that the plan must resolve with a spike.
- **Dispatch prompt:**
  > Read CR issue [#NNNN] and the design at [permalink]. Invoke the writing-plans skill to produce an
  > implementation plan. Annotate each task brief with a recommended model tier: transcription of
  > complete code is a cheap tier, integration across files is a standard tier. If a load-bearing
  > unknown exists, make Task 0 a spike that confirms it. Write the plan to the standard path and return
  > only that path.

## implement

- **Entry:** the plan file and, if resuming, the SDD ledger at `.superpowers/sdd/<plan-basename>/`.
- **Child skill:** `subagent-driven-development`.
- **Exit:** the code and tests committed on the work branch, and a code PR into the base branch.
- **Model:** Sonnet for the SDD controller. The controller coordinates - it does not need a top-tier
  model. Inside SDD, follow its own Model Selection section strictly:
  - implementers doing transcription from a complete task brief run on the cheapest tier,
  - implementers doing multi-file integration run on a standard tier,
  - task reviewers run on a standard tier scaled to the diff,
  - the final whole-branch review runs on the most capable model - the one expensive point,
  - fix-loop rounds 4 and 5 escalate one tier above the implementer that got stuck.
- **Controller checkpointing:** the SDD controller checkpoints itself to its ledger by task batch. It
  does not carry the whole session in one context. On resume, it reads the ledger and git, not the
  conversation.
- **Dispatch prompt:**
  > Read the plan at [plan path] and its ledger if present. Invoke the subagent-driven-development
  > skill to execute the plan task by task. Follow its Model Selection section exactly: cheap tier for
  > transcription implementers, standard for integration and reviewers, most capable for the final
  > whole-branch review, escalate on fix rounds 4 and 5. Commit per task, keep the ledger current, and
  > open a PR into [base branch] when the final review is clean. Return the PR number, the commit list,
  > and any parked findings only.

## review

- **Entry:** the diff `BASE..HEAD` for the code PR and the CR acceptance conditions.
- **Child skill:** `code-review`, and `writing-gherkin` when a BDD slice is warranted.
- **Exit:** a review report file and, when authored, a BDD slice added to the suite.
- **Model:** Sonnet. The two axes split by nature:
  - Standards axis is rule matching against repo standards and the smell baseline - Sonnet,
  - Spec axis is judgement against the CR acceptance - Sonnet, escalate to the most capable model when
    the diff is subtle or high risk.
- **Dispatch prompt:**
  > Read the diff for PR [#NNNN] against [BASE] and the acceptance conditions in CR [#NNNN]. Invoke the
  > code-review skill against that fixed point. Run the Standards axis on a standard tier and the Spec
  > axis on a standard tier, escalating the Spec axis to the most capable model if the diff is subtle.
  > If a coverage gap warrants a BDD slice, invoke writing-gherkin to enumerate the missing cases. Write
  > the report to [report path] and return the path plus the count of findings per axis.

## verify

- **Entry:** the code PR number.
- **Child skill:** none - poll CI check runs.
- **Exit:** the check-run outcomes recorded in the ledger.
- **Model:** Haiku or Sonnet. Pure mechanical polling. Run it out of the orchestrator's context - a
  background watcher or a cheap dispatched poll - so a long wait does not re-read the orchestrator
  context on every tick.
- **Note:** cover every terminal state, not only success. A green build gates on the head commit type
  where the CI requires it (for this repo, the Java Docker build needs a feat/fix/BREAKING head).

## acceptance (human)

- **Entry:** the CR acceptance conditions and the green checks from `verify`.
- **Child skill:** none.
- **Exit:** a human sign-off recorded in the ledger and on the issue.
- **Model:** human. The acceptance is executable - the CR acceptance conditions are projected into the
  BDD and unit tests - so the human signs off on green checks rather than running the pipeline by hand.
