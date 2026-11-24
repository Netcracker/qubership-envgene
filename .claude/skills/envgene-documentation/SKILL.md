---
name: envgene-documentation
description: EnvGene override of the component-documentation slot. Updates docs/ in the same change - the feature docs, use cases, glossary terms - using the writing-docs and reviewing-docs skills, and checks the result against the code with discrepancy-audit. Use when a change alters behaviour, configuration, parameters or terms.
---

# EnvGene documentation (override of component-documentation)

Replaces `component-documentation` in this repository. It keeps its gate: the docs are updated in the
same change, and the review of the docs passes before the change is merged.

## Steps

1. **Find what the change touches**: behaviour, configuration, parameters, terms, steps of the pipeline. Read
   `proposal.md`, the delta specs and the Contracts of `component-design.md`. Do not read the Approaches and the
   Decision of `component-design.md`: the docs describe the approved behaviour, not the implementer's choice.
2. **Write** the docs with the `writing-docs` skill (`.claude/skills/writing-docs/`). Every `.md` file,
   doc, issue, CR and PR text follows it. Ground every named identifier in the code before it goes into the docs.
3. **Glossary.** `docs/glossary.md` is a link index, not a place for definitions. Define a new term in the doc
   that owns it, then add the term to the glossary as a link to that doc. A term with several meanings gets its list
   of senses, as described in the glossary's How to use section.
4. **Review** the docs with the `reviewing-docs` skill (`.claude/skills/reviewing-docs/`) for fitness for purpose.
5. **Audit (optional, after implement).** Run the `discrepancy-audit` skill when the diff changes a
   documented behaviour, configuration or schema: it reconciles the docs with the code and schema and reports
   a verdict per statement. Skip it when the diff touches no documented area, and say so in the ledger.
6. **Settle each contradiction with the person.** The audit only reports; it never edits a doc and never picks the
   side. For every statement it marks as contradicting the code or the schema, stop and ask which side moves, and
   record the answer as a decision row:
   - the docs move: rewrite them here with `writing-docs`, then re-run the gate of this stage;
   - the code moves: `envgene-implementation` fixes it, then `envgene-verification`, then this stage again - the docs
     stage reports a code defect, it does not fix code;
   - the specs or the proposal move: `envgene-propose`, back to the owner who approves the WHAT;
   - nobody has decided yet: this stage does not go on, and the ledger keeps the question open.
7. **Ledger row:** `| <time> | docs | - | - | <n> files updated; reviewing-docs: pass or findings; discrepancy-audit: <verdict> @ <sha> |`.
8. **Gate.** All of `docs/` is public in this repository, so the docs gate holds for HEAD when:
   - `reviewing-docs` has no open findings;
   - `discrepancy-audit` reports no statement that contradicts the code or schema, or the ledger says why it was
     skipped (the diff touches no documented area), and every contradiction the audit did report is settled by a
     decision row and fixed on the side the person chose;
   - the lint row of `envgene-verification` at HEAD (super-linter: textlint, codespell, gitleaks on `docs/`) is exit 0.

   Then append the docs gate row (format: Gate rows of `envgene-orchestration/references/ledger.md`).

   A docs change after this row makes it stale; run the gate again.

## Rules

- The general rules of `envgene-orchestration` (section Rules) apply.
