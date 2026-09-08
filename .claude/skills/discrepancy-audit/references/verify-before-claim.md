# Verify before claim

These are the truth-location rules for phase 3 of the audit harness. They apply in every mode
(topic, PR/diff, single-file). Each rule exists because breaking it once produced a false claim
in a real audit pass.

EnvGene runs all pipeline jobs as one consolidated job, dispatched by `scripts/pipeline/orchestrator.py::dispatch`.
The orchestrator fans out to parallel child processes via `multi_env_runner.fan_out()` for multi-environment
runs. This architecture matters for rule 3: a step that looks absent from the primary flow may be
invoked as a separate orchestrator phase, not inlined.

## The four rules

1. **Verify on the current HEAD.** Directories move between branches. The `python/` directory was
   renamed to `modules/` in this branch, which made earlier greps silently blind and produced a
   false "not implemented" claim. Always confirm the path exists before quoting it. A grep that
   returns nothing may be pointing at a path that no longer exists.

2. **For an artifact claim, locate both the writer and the reader.** A claim about a file or
   parameter that the code produces requires finding where it is written AND where it is consumed.
   A writer whose output no reader consumes is a different finding from a name mismatch between
   writer and reader - and it is the worse finding. Do not stop the search at the writer.

3. **Before declaring something unimplemented, search `dispatch` for a separate step.** The
   orchestrator calls steps that are not inline in the main flow function. A behavior that appears
   absent from one step may be implemented in a distinct phase invoked by `dispatch`. Exhausting
   the orchestrator search is required before the `doc-ahead` verdict is used.

4. **Verify where a payload actually fails and where data actually differs.** Names and comments
   lie. A function named `validate_credentials` may exit without calling the schema validator in
   certain branches. Always trace the actual execution path to the point of failure or divergence,
   not the path implied by the symbol name.

5. **A delegated finding is a candidate until re-verified in the main context.** When phases 2 and 3
   are fanned out to subagents (see the execution model in `SKILL.md`), the findings they return are
   candidates, not verdicts. Before a finding enters the report, open its cited doc line and its cited
   code or schema line yourself and confirm both say what the finding claims. Rules 1 to 4 apply to
   that re-verification. A candidate whose evidence does not survive is dropped or downgraded, never
   passed through on the subagent's word.
