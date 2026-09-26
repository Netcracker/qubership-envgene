# Connected-only Rule Checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Track steps with checkboxes.

**Goal:** Make all in-scope rules inspect only entities whose local connection or generator usage is established.

**Architecture:** A shared physical-path connection index centralizes ParameterSet, passport, profile, credentials, and artifact usage. Rules consume that selection before grouping or inspecting content; Effective Set projections retain only actual selected files.

**Tech Stack:** Python 3.12, ruamel.yaml, pytest, existing Click CLI.

**Spec:** `docs/superpowers/specs/2026-09-11-connected-only-design.md`.

## Global Constraints

- User authorizes connected-only checks; NAME-3 remains unchanged pending explicit clarification because the user excluded it earlier.
- Physical path + environment context determines usage. No arbitrary stem/name/string matches, external resolution, Jinja rendering, or missing-reference findings.
- Preserve all existing rule messages except where an existing scope statement needs correction; keep eleven rule headers, severity/action, exit0 for findings.
- No network or real repository modifications, no real payloads in fixtures or output. Preserve unrelated untracked files; controller handles Git mutations.

### Task 1: Shared connections, rule integration, and regression tests

**Files:** create `src/envgene_linter/connections.py`, `tests/test_connections.py`; modify `model.py`, `discovery.py`, `effective.py`, `passport.py`, `engine.py`, rules `place1.py`, `place2.py`, `place3.py`, `place4.py`, `place6.py`, `place7.py`, `place8.py`, `name1.py`, `name2.py`, `name4.py` as necessary. Update corresponding tests and `tests/test_cli.py`, `tests/test_lab.py`, existing synthetic `testdata/` fixtures. Do not edit NAME-3 source/tests or documentation (controller owns docs).

**Interfaces:** preserve `check(index, ...)` usability; optionally add defaulted connections arguments for reuse. Produce a connections object with selected physical paths, per-file ParameterSet uses and per-environment selections. Add default-empty artifact selector state on EnvModel. Reuse current record types and resolver semantics from the spec.

- [x] Write regressions proving unused files are ignored and physically selected files remain checked. A minimal direct-rule red case:

```python
def test_name2_ignores_unreferenced_parameter_set(repo):
    from envgene_linter.discovery import build_index
    from envgene_linter.rules.name2 import check
    repo.env("c", "e")
    path = repo.root / "environments/parameters/unused.yml"
    path.parent.mkdir(parents=True)
    path.write_text("name: wrong\nparameters: {}\n", encoding="utf-8")
    assert check(build_index(repo.root)) == []
```

- [x] Run `.venv/bin/python -m pytest tests/test_connections.py -q` and record expected RED failures.
- [x] Implement actual ParameterSet selection using `resolve_reference(index, env, reference)` before any layer projection; reuse selected paths/categories for all relevant rules. For the projection loop the operative order is `for entry in resolve_reference(index, env, reference):` followed by `if entry.file.layer not in layers: continue`. Keep per-reference binding positions unchanged in PLACE-7.
- [x] Add selected passport discovery and key catalogs, preserving automatic passport selection. Move existing PLACE-8 shared binding machinery to the common module or reuse without circular imports; preserve known fixed-path credentials use and first-bucket ambiguity behavior.
- [x] Read the three artifact selectors from envTemplate; accept well-formed application:version strings only. Select configuration/artifact_definitions/application.yml before .yaml, respecting physical boundaries. Unselected AppDefs/RegDefs remain skipped because current local inputs cannot prove their use.
- [x] Gate PLACE-3/4/6/7 and NAME-1/2/4 before inspecting/grouping. NAME-4 emits per physical file using only actual-use categories and owners. Ensure NAME-1 unused files cannot affect a selected file's group or locations.
- [x] Update positive tests with explicit real synthetic bindings/files instead of weakening expectations. Add all regressions listed in spec, including direct-rule checks and engine consistency, parameter projection shadowing, passport catalog contamination, malformed artifact winner, exact reference format and original YAML positions after filtered names.
- [x] Run focused affected tests, then `.venv/bin/python -m pytest -q`. Write a self-review report with exact red/green commands, output/counts, changed files, deviations and unresolved concerns. Do not commit or spawn agents.

### Task 2: Document the shared scope and verify examples

**Files:** create `docs/algorithms/connections.md`, `docs/algorithms/ru/connections.md`; update current in-scope algorithm documents and supersession notes on old specs. Controller owns this task concurrently with task1 implementation.

**Interfaces:** consume shared rule scope and exact current findings from task1; historical plan bodies remain unchanged.

- [x] Document the eligibility table: physical selected ParameterSets, resolved/auto passports, selected profiles/credentials, fixed Inventory credentials, artifact selectors, unknown AppDefs/RegDefs usage, NAME-3 exception.
- [x] Remove current claims that orphans are checked, globally equal stems establish usage, missing references still trigger PLACE-6/7, or projections resurrect unused files. Preserve field copy and other behavior.
- [x] Verify synthetic ok/not-ok examples through `run_check`, compare intended rule findings, and check documentation links. Do not regenerate or modify real repositories.
- [x] Obtain task-scoped and final review, fix concrete findings, record final full-suite evidence, and save local commits.
