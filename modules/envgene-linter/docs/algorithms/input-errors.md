# Source read and parser failures

- [Parser boundaries](#parser-boundaries)
- [Read collection](#read-collection)
- [Rule diagnostics](#rule-diagnostics)
- [Merge uncertainty](#merge-uncertainty)
- [Reports and exit codes](#reports-and-exit-codes)

## Parser boundaries

`parsing.py` wraps YAML construction and composition, JSON decoding, and Jinja parsing.
Expected library syntax, value-conversion, and recursion failures become `ParseFailure` records.
Records contain a generic reason and a source location. They omit exception excerpts and source values.
Parser marks supply locations when available. Other failures use `1:1`.
Known malformed YAML scalar conversions, including invalid explicit tags and YAML 1.1 numeric overflow,
are normalized at the constructor call even when the library raises Python conversion exceptions.

An iterative graph walk rejects cycles and container depth greater than 256 before recursive consumers run.
Shared YAML aliases remain valid. YAML composition is checked before construction because the constructor can
replace a recursive mapping alias with `null`. JSON position-map construction remains outside the decoder catch.
Unexpected implementation exceptions propagate.

`yamlio.load()` converts read and parser failures to `YamlReadError`, preserving its path and cause interface.
Its additional `line` and `column` fields identify the failure without including source content.
UTF-8 decoding and operating-system read failures use a generic read reason.

## Read collection

1. `collect_read_errors()` creates a context-local list and restores the previous collector on every exit.
2. Discovery runs inside its own collector and stores its failures on `RepoIndex.read_problems`.
3. The engine resolves Connections before associating discovery failures with rule IDs.
4. Each enabled rule runs with an offset into the engine collector. New read failures become skips for that rule,
   including failures caught inside shared readers.

Unavailable ParameterSets retain their logical replacement slots. A failed read never restores a shadowed source.
Unbound and shadowed discovery inputs do not acquire connected-rule diagnostics.
INT-4 can report separate skips for its actual authored-source reads.

## Rule diagnostics

`diagnostics.skip_check()` deduplicates records by rule, path, reason, line, and column.
Selected physical inputs use their selected logical alias when available.
Only enabled applicable rules receive records.

| Failed selected input          | Affected content checks                                                               |
|--------------------------------|---------------------------------------------------------------------------------------|
| ParameterSet                   | PLACE-1, PLACE-2, PLACE-4, PLACE-8, SEC-1, SEC-3, SEC-4, SEC-5, NAME-1, NAME-2, VAL-4 |
| Cloud Passport                 | PLACE-1, PLACE-4, PLACE-9, NAME-2                                                     |
| Resource Profile or Credential | PLACE-8                                                                               |
| Artifact Definition            | NAME-2, SEC-5                                                                         |
| Environment definition         | Enabled instance checks whose local bindings cannot be established                    |

Jinja failures create skips for the affected template rules.
Descriptor composition failures also withhold TPL-1 findings that depend on knowing supported descriptor fields.
TPL-1 retains lexical checking for other malformed ordinary YAML.
TPL-6 records unavailable YAML compatibility context while retaining source-level analysis when that analysis completes.
Its compatibility parser reports failures through a callback supplied by the rule.
Rewrite findings established before a later parser failure remain available alongside the skip.

Generated files are outside finding and incomplete-check locations under the [authored configuration scope](/modules/envgene-linter/docs/algorithms/source-scope.md).
Context-dependent reference uncertainty remains at the authored consumer.

## Merge uncertainty

PLACE-1 withholds promotion findings when selected ParameterSet, passport, or environment-definition content
is unavailable. This conservative boundary prevents partial participants from proving that a value belongs higher.
Other independent checks continue.

PLACE-2 retains every unreadable environment definition as a potential consumer of sources in its applicable layers.
The definition's unknown bindings cannot prove that a shared value is safe to remove.
Its existing per-consumer removal analysis produces Review when preservation cannot be confirmed.

## Reports and exit codes

The CLI writes fresh HTML and JSON reports after recoverable input failures.
HTML shows the existing `Incomplete checks` section. JSON uses the existing six-field schema and exports
located Review entries beginning with `Check skipped:`. No `type` field is added.
Some directory-enumeration and unsupported-source notes remain HTML/stderr-only diagnostics.
An empty JSON array therefore does not prove that every repository source was checked.

Recoverable incomplete checks retain exit code `0`.
Invalid command configuration and report-write failures retain exit code `2`.
See the [report contract](/modules/envgene-linter/docs/algorithms/reports.md),
[design](/modules/envgene-linter/docs/superpowers/specs/2026-10-20-input-error-handling-design.md), and
[regression tests](/modules/envgene-linter/tests/test_input_errors.py).
