# Verdict model

The skill states the relationship between a doc claim and what code or schema does - never who is at
fault and never what the intent was. Verdicts are fact-oriented. When two sources conflict, the skill
records both sides and leaves the fix direction to the human.

## Verdicts

| Verdict                          | Condition                                             | Report carries                                                        |
|----------------------------------|-------------------------------------------------------|-----------------------------------------------------------------------|
| `contradiction`                  | Code exists and behaves differently from the doc      | Doc quote + code `file:line`. Fix direction is the human's call.      |
| `doc-ahead`                      | Code absent for documented behavior                   | Doc quote. Separate category, not a defect.                           |
| `doc-vs-doc / code breaks tie`   | Two docs disagree, code resolves it                   | Both quotes + code `file:line`. Names the doc that diverges from code.|
| `doc-vs-doc / code silent`       | Two docs disagree, code is silent                     | Both quotes. Verdict deferred.                                        |
| `unverifiable`                   | No code or schema anchor (pure prose)                 | Doc quote. Surfaced but flagged.                                      |
| `consistent`                     | Checked, matches                                      | Not listed (or a "checked N" summary line at the table bottom).       |

## Evidence-pair rule (hard gate)

Every row in the verdict table must carry an evidence pair: a doc quote AND a code or schema
`file:line`. A row that lacks either half of the pair is dropped from the report - not softened,
not marked `unverifiable`, dropped. The purpose of this rule is to keep the report grounded in
verifiable facts rather than in recalled or inferred claims.

The only exception is `doc-ahead`, where the code half of the pair is "absent" by definition.
For `doc-ahead` rows, the doc quote alone is sufficient, and the evidence cell records "no code
found at HEAD."

For `unverifiable`, no code anchor exists by definition either. The evidence cell records the
doc quote and notes "pure prose - no code or schema to check."
