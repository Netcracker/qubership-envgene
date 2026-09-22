# SEC-4 pair-reference correction

> Execute with the receiving-code-review and test-driven-development skills. The user confirmed that two complete but different Credential blocks still violate the pair requirement.

**Goal:** Replace the old single-observed-field heuristic with existence, completeness and same-block checks for referenced username/password pairs.

**Architecture:** Reuse the connected security-source selector and strict reference parser. Walk consumer mappings independently, identify sibling username/password keys (including matching snake/camel/dotted prefixes), and resolve references within each consumer's catalog. When no generated runtime catalog exists, inspect unique selected shared/passport input definitions, treating unresolved or ambiguous inputs as unknown rather than guessing merge precedence. No secret values appear in findings.

**Scope:** Keep Information / Review. Local pairs require usernamePassword with both data fields; external pairs require both named properties. SOPS-encrypted type is inspected structurally without decryption. A single reference to username/password still requires a complete target pair but does not require both fields to be used. A literal counterpart adds no new SEC-4 prohibition. Unused definitions and unrelated pairs are not compared.

- [x] Replace obsolete SEC-4 tests with failing tests for same-ID complete pairs, different IDs, missing/partial definitions, local/external forms, nested/application/context separation, connected-only scope, unresolved inputs and redacted diagnostics.
- [x] Implement the consumer-pair algorithm in `src/envgene_linter/rules/sec4.py` and update its catalog description.
- [x] Update EN/RU SEC-4 specs/algorithms and README, explicitly removing the earlier one-field heuristic.
- [x] Run focused suites, full pytest, documentation link/format checks and independent review. Fix actionable findings with regression tests.
- [x] Keep all work local; preserve unrelated modifications and do not upload or commit them.

Validation commands:
```bash
.venv/bin/python -m pytest tests/test_sec4.py -q
.venv/bin/python -m pytest -q
git diff --check
```

## Verification record

- Initial corrected SEC-4 tests against the old implementation: 26 failed, 10 passed, demonstrating missed split pairs and obsolete single-field findings.
- Three additional reference-boundary regressions failed before their fixes: dynamic single-field references and a missing selected property in an otherwise complete pair.
- Four independent-review regressions failed before their fixes: ambiguous shared binding, missing/ambiguous passport, unsupported encrypted type classification.
- Final SEC-4 suite: 43 passed. Final full suite: 561 passed in 3.57s.
- Independent scoped re-review: all three reported findings addressed, generated-catalog precedence preserved.
- Compilation and diff whitespace checks passed. No network requests, decryption, real-repository writes, commits or uploads.
