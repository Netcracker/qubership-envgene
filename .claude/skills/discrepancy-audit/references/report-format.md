# Report format

This file defines the structure phase 5 emits. Follow it exactly. Every rule here was established
to keep the report grounded and auditable.

## Header

The report opens with three items, each on its own line:

- **Topic** - the subject area as stated by the user.
- **Corpus** - the docs, code entry points, and schemas actually read. List every file by path.
  This transparency makes it visible what was NOT examined.
- **Scope note** - any boundary the user confirmed, adjusted, or excluded during phase 1.

## Discrepancy table

Columns: `#`, `Claim (doc quote)`, `Axis`, `Verdict`, `Evidence (doc file:line + code/schema file:line)`,
`Recommendation`.

Rows are grouped in descending severity order:

1. `contradiction`
2. `doc-vs-doc` (covers both `doc-vs-doc / code breaks tie` and `doc-vs-doc / code silent`)
3. `doc-ahead`
4. `unverifiable`

The table ends with a single summary line: `consistent: checked N` where N is the count of claims
that were verified and matched. Consistent items are not listed as rows.

## Legends

After the table, include a legend block covering only the verdict values that actually appear in
the table. Do not include legends for verdicts not used.

| Verdict                        | Meaning                                                          |
|--------------------------------|------------------------------------------------------------------|
| `contradiction`                | Code exists and behaves differently from the doc.                |
| `doc-ahead`                    | Behavior is documented but no code implements it yet.            |
| `doc-vs-doc / code breaks tie` | Two docs disagree. Code matches one of them; that doc is correct.|
| `doc-vs-doc / code silent`     | Two docs disagree. Code is silent. Resolution deferred.          |
| `unverifiable`                 | Claim is pure prose with no code or schema anchor to check.      |

## Self-checks before showing the report

Run these three checks before presenting the report to the user:

1. Every claim extracted in phase 2 is either a row in the table or carries the verdict `unverifiable`.
   No claim may be silently dropped.
2. Every row (other than `doc-ahead` and `unverifiable`) carries a complete evidence pair: a doc
   quote with its file and line number, and a code or schema reference with its file and line number.
3. The corpus stated in the header is complete: every file read during the audit appears in the
   corpus list, and no file not in the corpus was used to form a verdict.

## Publication

The default output is chat. On the user's explicit request, write the report to
`stuff/<topic>-discrepancy-audit.md` beside the repository clone (the scratch directory, not inside
the repository). When writing to a file, apply house style: English, prose wrapped at 120 characters,
no em dashes, no en dashes, no semicolons, `|---|` table separators with aligned pipes. Nothing is
pushed or committed without explicit confirmation from the user.
