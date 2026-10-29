# Reports and incomplete checks

- [Inputs and rendering](#inputs-and-rendering)
- [Skipped checks](#skipped-checks)
- [Output contract](#output-contract)

## Inputs and rendering

The engine returns findings, enabled and inapplicable rules, skip notes, and structured source skip records.
The CLI always writes `envgene-linter-report.html` and `envgene-linter-report.json` after a successful check.
Report rendering uses these records without rereading configuration files.

HTML groups ordinary findings by rule and shows the repository folder name in the header.
JSON serializes each finding with its related locations, preserving the shared rule order.
The [JSON field reference](/modules/envgene-linter/README.md#json-reports) defines the six fields.

Generated files are outside finding and incomplete-check locations under the [authored configuration scope](/modules/envgene-linter/docs/algorithms/source-scope.md).
Context-dependent reference uncertainty remains at the authored consumer.

## Skipped checks

1. When a source reader cannot read or parse YAML, JSON, or Jinja, record a generic note and one structured record
   for each affected enabled rule. Associate discovery failures with selected inputs and actual rule reads.
   A TPL-4 analysis recursion failure records only that rule.
2. Retain file, line, and column without copying source expressions or exception text. Parser errors use their
   original line. Descriptor errors use the selected scalar opening line. Read errors use `1:1`.
3. Deduplicate identical records while preserving distinct invalid scalar locations in one file.
4. Pass ordinary skip notes to HTML and stderr. Discovery errors omit raw YAML exception text.
   HTML hides explicitly disabled-rule notes, escapes visible notes, and displays `Incomplete checks`.
5. Convert structured records to JSON `Review` entries with an issue beginning `Check skipped:`.
   Use the same field names and rule filter as ordinary findings. Keep diagnostics out of engine finding counts.

Some existing skip notes have no structured JSON representation. Unsupported sources do not automatically create
skip entries. A JSON consumer must treat `Check skipped:` as an incomplete check rather than a confirmed violation.

## Output contract

A skip-only HTML report says `No findings in the checked sources` and retains the incomplete-check section.
A run with structured skips produces a nonempty JSON array. When there are no findings or structured skips, JSON is `[]`.
Disabled and inapplicable rules have no JSON entries. Neither report includes a finding `type` field.

The CLI keeps separate `HTML report saved here:` and `JSON report saved here:` notices and its current exit codes.
Skip diagnostics remain nonfatal. The report filenames are added to `.gitignore` without changing existing entries.
Recoverable input failures still replace both reports and retain independent findings.
The [input error algorithm](/modules/envgene-linter/docs/algorithms/input-errors.md) defines parser boundaries,
rule association, and merge uncertainty.

See the [design](/modules/envgene-linter/docs/superpowers/specs/2026-10-12-skipped-checks-design.md) and
[tests](/modules/envgene-linter/tests/test_skipped_reports.py).
