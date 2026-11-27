# Skipped check reporting specification and design

- [Requirements](#requirements)
- [Representation](#representation)
- [Verification](#verification)

> [!NOTE]
> This document preserves the initial Jinja reporting design from October 12, 2026.
> The later [input error contract](/modules/envgene-linter/docs/superpowers/specs/2026-10-20-input-error-handling-design.md)
> extends structured JSON skips to affected YAML and JSON checks.
> Follow the [report algorithm](/modules/envgene-linter/docs/algorithms/reports.md) for current behavior.

## Requirements

Reports expose incomplete checks when a source cannot be read, parsed, or analyzed.
HTML displays existing skip diagnostics in a visible `Incomplete checks` section with escaped text.
When skipped sources exist without findings, it says `No findings in the checked sources` instead of `No findings`.

Skipped Jinja checks also appear in JSON. Each affected enabled rule receives a `Review` entry whose issue starts
with `Check skipped:`. The entry identifies the source location and a generic reason without copying expressions,
values, or parser exception text. An empty array does not imply coverage of unsupported inputs or rules.
Legacy non-Jinja skip diagnostics remain available in HTML and stderr. YAML discovery errors use generic messages
without parser exception text. HTML hides explicitly rule-scoped skip notes when their rule is disabled.

Keep the JSON array and its six existing fields. Do not add a `type` field or change finding exit codes.
Ordinary findings remain separate from diagnostics within the engine, so skip entries do not inflate finding counts.
Disabled rules produce no Jinja skip entries.

## Representation

The shared Jinja reader records a structured skip for each affected rule, file, location, and reason,
alongside the existing console note. Parser errors use the reported source line. Decoded YAML descriptor errors
point to the scalar's opening line. Read failures use line 1, column 1. Distinct invalid descriptor scalars remain
distinct diagnostics. A TPL-4 analysis recursion failure records only a TPL-4 skip.

The engine carries these records to the CLI. HTML receives the existing skip notes. The JSON renderer converts
structured Jinja skips into report entries at serialization time, using the existing rule ordering and disabled-rule
filter. Skip entries recommend resolving the source problem and rerunning the check. No source rendering occurs.

See the [report algorithm](/modules/envgene-linter/docs/algorithms/reports.md) for current processing details.

## Verification

[Report regressions](/modules/envgene-linter/tests/test_skipped_reports.py) cover syntax errors alongside findings,
skip-only runs, separate descriptor locations, invalid UTF-8, disabled rules, escaped HTML, unchanged JSON fields,
source redaction, legacy YAML errors, and disabled-rule discovery notes.
Existing CLI, HTML, and JSON tests verify compatibility with successful checks.
