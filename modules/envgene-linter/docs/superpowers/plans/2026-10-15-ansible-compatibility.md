# Ansible compatibility implementation plan

**Goal:** Review legacy expressions that cannot be confirmed compatible with the applicable EnvGene renderer.

**Architecture:** A pure analyzer models compatibility processing and known filter contracts.
A separate collector determines source spans and rendering contracts. TPL-6 incorporates compatibility Reviews
without extending TPL-4 or changing the established statement checks.

**Tech stack:** Python 3.12, Jinja2 3.1.6, ruamel.yaml, and pytest. No additional runtime dependencies.

**Specification:** [Ansible compatibility](/modules/envgene-linter/docs/superpowers/specs/2026-10-15-ansible-compatibility-design.md).

- [Constraints and review focus](#constraints-and-review-focus)
- [Compatibility analysis](#compatibility-analysis)
- [Source collection and integration](#source-collection-and-integration)
- [Documentation and verification](#documentation-and-verification)

## Constraints and review focus

- Preserve uncommitted raw and filter-policy changes on `feature/envgene-linter-dev`.
- Never render, compile, execute lookups, or read their target files or environment values.
- Preserve positions, disabled-rule behavior, safe paths, and redaction.
- Keep external-consumer uncertainty distinct from a confirmed unsupported renderer contract.
- Keep raw literal changes, descriptor stage differences, dynamic arguments, physical aliases, and missing renderer
  evidence covered by regression tests.

## Compatibility analysis

Files: `src/envgene_linter/ansible_compat.py` and `tests/test_ansible_compat.py`.

Interface: `CompatibilitySource(path, text, rendering, offset=0, descriptor=False)` describes an analysis source.
`analyze_compatibility(source) -> dict[int, str]` returns original source lines and generic Review reasons.
Contracts are `envgene`, `custom_jinja`, `jinja`, and `unknown`.

- [x] Write and observe failing tests for supported replacements, unsupported lookup forms, filter availability,
  argument contracts, unknown stages, literal changes, source positions, and redaction.
- [x] Implement transformations on an analysis copy and static AST checks without template execution.
- [x] Run the focused tests and review unknown-source handling and lexical boundaries.

## Source collection and integration

Files: `src/envgene_linter/ansible_sources.py`, `rules/tpl6.py`, and `tests/test_ansible_sources.py`.

Interface: `compatibility_sources(index, sources) -> list[CompatibilitySource]` combines existing source records
with safely selected additional configuration. TPL-6 converts the analyzer's generic reasons into Information / Review.

- [x] Write and observe failing integration tests for descriptor contracts, additional instance/template sources,
  excluded root GSF metadata, aliases, unsafe paths, report output, and disabled TPL-6.
- [x] Implement conservative rendering-stage selection and additional marker-based collection.
- [x] Integrate compatibility findings while retaining ordinary TPL-6 statements and loops.
- [x] Reconcile existing filter tests with permitted syntax versus runtime availability, then run adjacent rule tests.

## Documentation and verification

- [x] Update the TPL-6 specification, algorithm, applicability matrix, readmes, functional changelog, and spec index.
- [x] Add synthetic runnable compatibility examples without private data.
- [x] Run the full pytest suite, Markdown lint, terminology lint, local link checks, and diff checks.
- [x] Review the final implementation and run the compatibility analysis read-only on the local corpus.
- [x] Report actual verification results and any pre-existing platform failures. Do not commit, push, or publish.

Verification on October 15, 2026: 352 adjacent tests passed. The full suite had 1,478 passes and three pre-existing
macOS failures involving case-insensitive `Credentials`/`credentials` paths. Independent review confirmed fixes for
namespace rendering stages, full-renderer YAML selection, and signed numeric filter arguments, with 121 focused passes.
Markdown lint, terminology lint, local file links, and diff checks passed.
Private corpus evidence remains outside the repository. Whole-object descriptor serialization remains outside static
compatibility coverage.
