# Input error handling

- [Contract](#contract)
- [Parser boundaries](#parser-boundaries)
- [Diagnostics and source scope](#diagnostics-and-source-scope)
- [Incomplete merge context](#incomplete-merge-context)
- [Verification](#verification)

## Contract

Expected source read, syntax, value-conversion, and recursion failures make the affected analysis incomplete.
Available independent sources remain checked. The CLI writes fresh HTML and JSON reports after a recoverable
source failure and keeps its existing exit codes. Invalid command configuration and report write failures
remain execution errors. Unexpected implementation exceptions propagate.

This implements the error-handling behavior approved in conversation on October 20, 2026.
It covers local YAML, JSON, and Jinja readers without rendering templates, changing parser limits in Python,
adding dependencies, introducing rule IDs, or changing the six-field JSON report schema.
Work remains in the current feature branch. Commit, push, issue comments, and release are separate requests.

## Parser boundaries

`parsing.py` normalizes expected third-party parser failures into a safe `ParseFailure` with reason and location.
YAML construction and composition, JSON decoding, and Jinja parsing use this boundary.
Known malformed YAML scalar conversions include invalid explicit tags, empty numeric scalars, and YAML 1.1
sexagesimal overflow. These failures are normalized only around the library constructor call.
Lexer fallback paths retain their source-level analysis when it completes successfully.

`yamlio.load()` keeps the `YamlReadError` API and records safe read problems in a context-local collector.
The collector is active only within discovery or one engine run and resets on every exit, including exceptions.
Read errors omit parser excerpts, source values, expressions, and secret identifiers.
Locations use parser marks when available and `1:1` otherwise.

Decoded YAML and JSON container graphs are validated before consumers receive them.
The implementation uses a maximum container depth of 256, selected by the implementer to leave room for existing
recursive consumers. Cyclic container graphs are unavailable. Ordinary shared aliases remain supported.
JSON values, duplicate-key semantics, and source positions retain the shared ParameterSet contract.
Position-map construction remains outside the third-party decoder exception boundary.

Jinja syntax, numeric-conversion, and recursion failures produce located skips for affected enabled template rules.
Malformed descriptors cannot silently remove TPL-4/TPL-6 source fragments.
When descriptor composition fails, TPL-1 also records a skip and withholds findings that depend on descriptor
exemptions. Its lexical fallback for other malformed ordinary YAML remains supported.
TPL-6 compatibility parsing records incomplete checks when used by the rule. Its standalone API can retain a
conservative Review result for callers that do not supply a diagnostic callback.
Compatibility rewrite findings established before a later parse failure remain available alongside the skip.

## Diagnostics and source scope

`read_errors.py` owns safe read-problem records and context-local collection without importing repository models.
`diagnostics.py` owns deduplicated `SkippedCheck` records and association with applicable enabled rules.
`jinja_analysis.skip_check` remains an import-compatible alias.

Discovery retains read problems on `RepoIndex`. Once Connections selects actual inputs, only surviving selected
sources supply connected-rule skip diagnostics. Unbound and shadowed sources do not gain connected checks.
INT-4 retains its separate authored-source scope.
Failures during an enabled rule's actual reads also become skips for that rule, including reads in shared helpers.

ParameterSet content diagnostics cover PLACE-1, PLACE-2, PLACE-4, PLACE-8, SEC-1, SEC-3, SEC-4, SEC-5,
NAME-1, NAME-2, and VAL-4. Selected passport content affects PLACE-1, PLACE-4, PLACE-9, and NAME-2.
Selected profile and Credential emptiness checks affect PLACE-8. Selected Artifact Definition content affects NAME-2
and SEC-5. Unreadable environment definitions make enabled instance checks incomplete because their local bindings
cannot be established. Path-only findings from readable independent evidence remain available.

The existing HTML incomplete-check section and JSON `Check skipped:` Review entries carry these diagnostics.
Disabled and inapplicable rules remain excluded. No `type` field is added.

## Incomplete merge context

Unavailable files retain staged replacement slots and cannot restore shadowed lower inputs.
PLACE-1 promotion checks are withheld when selected ParameterSet, passport, or environment-definition content
is unavailable. Other independent content checks continue.
PLACE-2 retains its existing per-consumer proof and treats unreadable environment definitions as unknown potential
consumers of sources in their applicable layers. Such definitions cannot justify excluding shared consumers.
No input failure is converted into an empty document as proof of successful checking.

## Verification

Tests use synthetic repositories and real parsers. Cases cover oversized integer literals in all three formats,
deep decoded structures, syntax and encoding failures, descriptor and compatibility paths, and fresh reports.
A valid source with a known finding must still contribute that finding alongside a broken source.
Additional cases cover source redaction, positions, disabled rules, alias and shadowing scope, sequential-run
collector isolation, shared-source removal uncertainty, and propagation of unexpected implementation errors.
The three existing macOS Credential casing failures remain outside this change and must be reported separately.
