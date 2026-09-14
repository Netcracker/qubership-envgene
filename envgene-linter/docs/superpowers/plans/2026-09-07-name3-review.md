# NAME-3 Information/Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** NAME-3 still flags non-kebab cluster/env/namespace directories and every YAML/JSON/Jinja stem under `environments/`, but every finding is Information / Review; no skip-list; files not on the index are included.

**Architecture:** Keep `check_name3(index)` in the engine. Rewrite `rules/name3.py`: directory names still come from the index (plus `Namespaces/` children); files come from a walk of `environments/`, not from paramset/passport/entity lists. Catalog defaults become Information / Review. Discovery does not change.

**Tech Stack:** Python 3.12+, pytest, existing `RepoIndex` / `RepoBuilder` / `paramset_stem`.

**Spec (English):** `docs/superpowers/specs/2026-09-07-name3-design.md`  
**Spec (Russian):** `docs/superpowers/specs/ru/2026-09-07-name3-design.md`

## Global Constraints

- Do not rename files or directories. No autofix.
- Do not call `compute` / Effective Set for NAME-3.
- Do not check YAML keys or enum values.
- Do not scan files outside `environments/` (no `appdefs/` at repo root).
- Do not scan non-YAML/JSON/Jinja files (`.md`, `.png`, `.txt`).
- Do not flag directory names other than cluster, environment, and namespace (`Inventory/`, `parameters/`, `cloud-passport/` stay silent as directories).
- Kebab-case: full match `^[a-z0-9]+(?:-[a-z0-9]+)*$`.
- No skip-list. `env_definition` is a finding.
- Stem via `paramset_stem` (strip `.j2` then `.yml` / `.yaml` / `.json`).
- File suffixes: `.yml`, `.yaml`, `.json`, `.yml.j2`, `.yaml.j2`, `.json.j2`. Include hidden files. Do not descend into `.git`.
- File kind is `File` (not `ParameterSet` / `Cloud Passport`).
- Information / Review. Severity `information`. Message: `{kind} {name!r} is not kebab-case.`
- Hint: `Review whether this name can be kebab-case. Do not rename it if generation or other logic still depends on the current spelling.`
- Do not call `str.capitalize()` on `kind`.
- Catalog description stays `Filenames, directories, and namespaces use kebab-case`.
- `RULE_ORDER` unchanged.
- A fixture repo with `env_definition.yml` is not an empty NAME-3 block.
- Prefer `.venv/bin/python -m pytest`.
- Work in an isolated git worktree (not on `master`). Include the already-amended spec files on the branch if they are still uncommitted.

---

## File map

| Path | Change |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | NAME-3 defaults → Information / Review |
| `src/envgene_linter/rules/name3.py` | Walk `environments/`; drop skip-list; Information; new hint |
| `docs/algorithms/name3.md` | Match amended spec |
| `docs/algorithms/ru/name3.md` | Russian algorithm |
| `tests/test_name3.py` | New expectations |
| `tests/test_rulemeta.py` | Catalog Information / Review |
| `tests/test_cli.py` | Console `information`; HTML chips; `env_definition` on typical `check` |
| `tests/test_report.py` | Leave empty `render()` blocks as-is |

---

### Task 1: Catalog Information / Review

**Files:**
- Modify: `src/envgene_linter/rulemeta.py`
- Modify: `tests/test_rulemeta.py`
- Include if uncommitted: `docs/superpowers/specs/2026-09-07-name3-design.md`, `docs/superpowers/specs/ru/2026-09-07-name3-design.md`

**Interfaces:**
- Consumes: existing `RuleMeta`, `IssueType`, `Action`
- Produces: `RULES["NAME-3"].default_issue_type is IssueType.INFORMATION`; `default_action is Action.REVIEW`

- [ ] **Step 1: Change the catalog assertions**

In `tests/test_rulemeta.py` `test_catalog_defaults_for_known_rules`, replace the NAME-3 TYPE/ACTION lines:

```python
    assert RULES["NAME-3"].description == "Filenames, directories, and namespaces use kebab-case"
    assert RULES["NAME-3"].default_issue_type is IssueType.INFORMATION
    assert RULES["NAME-3"].default_action is Action.REVIEW
```

Leave PLACE-* and NAME-1 / NAME-2 assertions unchanged.

- [ ] **Step 2: Run the catalog test (expect FAIL)**

Run: `.venv/bin/python -m pytest tests/test_rulemeta.py::test_catalog_defaults_for_known_rules -v`

Expected: FAIL (`IssueType.WARNING` is not `INFORMATION`, or `Action.FIX` is not `REVIEW`)

- [ ] **Step 3: Update the catalog**

In `src/envgene_linter/rulemeta.py`, the NAME-3 entry:

```python
    "NAME-3": RuleMeta(
        "NAME-3",
        "Filenames, directories, and namespaces use kebab-case",
        IssueType.INFORMATION,
        Action.REVIEW,
    ),
```

- [ ] **Step 4: Re-run the catalog test (expect PASS)**

Run: `.venv/bin/python -m pytest tests/test_rulemeta.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/rulemeta.py tests/test_rulemeta.py \
  docs/superpowers/specs/2026-09-07-name3-design.md \
  docs/superpowers/specs/ru/2026-09-07-name3-design.md
git commit -m "$(cat <<'EOF'
Set NAME-3 catalog defaults to Information/Review.

EOF
)"
```

If the spec files are already committed, omit them from `git add`.

---

### Task 2: Walk `environments/` and drop the skip-list

**Files:**
- Modify: `src/envgene_linter/rules/name3.py`
- Modify: `tests/test_name3.py`

**Interfaces:**
- Consumes: `RepoIndex.root`, `RepoIndex.clusters`, `paramset_stem`, `RULES["NAME-3"]`, `Location`
- Produces: `check(index: RepoIndex) -> list[Finding]` — Information / Review; kind `File` for files; no skip-list

- [ ] **Step 1: Replace `tests/test_name3.py` with the failing tests**

```python
from envgene_linter.discovery import build_index
from envgene_linter.model import Action, IssueType, Severity
from envgene_linter.rules.name3 import check

_HINT = (
    "Review whether this name can be kebab-case. "
    "Do not rename it if generation or other logic still depends on the current spelling."
)


def _name3(repo):
    return check(build_index(repo.root))


def test_cluster_not_kebab(repo):
    repo.env("Cluster_01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("Cluster_01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    findings = [item for item in _name3(repo) if item.key == "Cluster_01"]
    assert len(findings) == 1
    item = findings[0]
    assert item.rule == "NAME-3"
    assert item.severity is Severity.INFORMATION
    assert item.issue_type is IssueType.INFORMATION
    assert item.action is Action.REVIEW
    assert item.message == "Cluster directory 'Cluster_01' is not kebab-case."
    assert item.hint == _HINT
    assert item.scope == "Cluster directory"


def test_kebab_cluster_and_env_dirs_are_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    kinds = {item.scope for item in _name3(repo)}
    assert "Cluster directory" not in kinds
    assert "Environment directory" not in kinds


def test_env_not_kebab(repo):
    repo.env("cluster-01", "Env_01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "Env_01", "cloud-deploy", {"LOG_LEVEL": "info"})
    findings = [item for item in _name3(repo) if item.key == "Env_01"]
    assert len(findings) == 1
    assert findings[0].message == "Environment directory 'Env_01' is not kebab-case."


def test_namespace_not_kebab(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "environments/cluster-01/env-01/Namespaces/Foo"
    path.mkdir(parents=True)
    findings = [item for item in _name3(repo) if item.key == "Foo"]
    assert len(findings) == 1
    assert findings[0].message == "Namespace 'Foo' is not kebab-case."


def test_paramset_stem_not_kebab(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["Cloud_Deploy"]})
    repo.env_paramset("cluster-01", "env-01", "Cloud_Deploy", {"LOG_LEVEL": "info"})
    findings = [item for item in _name3(repo) if item.key == "Cloud_Deploy"]
    assert len(findings) == 1
    assert findings[0].message == "File 'Cloud_Deploy' is not kebab-case."
    assert findings[0].scope == "File"


def test_env_definition_is_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    findings = [item for item in _name3(repo) if item.key == "env_definition"]
    assert len(findings) == 1
    assert findings[0].scope == "File"
    assert findings[0].severity is Severity.INFORMATION
    assert findings[0].action is Action.REVIEW
    assert findings[0].message == "File 'env_definition' is not kebab-case."


def test_yaml_outside_index_is_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = (
        repo.root
        / "environments/cluster-01/env-01/Inventory/credentials/Foo.yml"
    )
    path.parent.mkdir(parents=True)
    path.write_text("user: x\n", encoding="utf-8")
    findings = [item for item in _name3(repo) if item.key == "Foo"]
    assert len(findings) == 1
    assert findings[0].scope == "File"


def test_hidden_yaml_is_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "environments/cluster-01/.Secret.yml"
    path.write_text("k: v\n", encoding="utf-8")
    findings = [item for item in _name3(repo) if item.key == ".Secret"]
    assert len(findings) == 1
    assert findings[0].scope == "File"


def test_hidden_cluster_directory_is_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    (repo.root / "environments" / ".scratch").mkdir(parents=True)
    findings = [item for item in _name3(repo) if item.key == ".scratch"]
    assert len(findings) == 1
    assert findings[0].scope == "Cluster directory"


def test_inventory_dir_is_not_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    assert all(item.key != "Inventory" for item in _name3(repo))


def test_markdown_under_environments_is_not_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "environments/cluster-01/README.md"
    path.write_text("# hi\n", encoding="utf-8")
    assert all(item.key not in {"README", "README.md"} for item in _name3(repo))


def test_appdefs_at_repo_root_is_not_reported(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    path = repo.root / "appdefs" / "Cloud_App.yml"
    path.parent.mkdir(parents=True)
    path.write_text("name: Cloud_App\n", encoding="utf-8")
    assert all(item.key != "Cloud_App" for item in _name3(repo))


def test_kebab_file_stem_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["cloud-deploy"]})
    repo.env_paramset("cluster-01", "env-01", "cloud-deploy", {"LOG_LEVEL": "info"})
    assert all(item.key != "cloud-deploy" for item in _name3(repo))
```

- [ ] **Step 2: Run NAME-3 tests (expect FAIL)**

Run: `.venv/bin/python -m pytest tests/test_name3.py -v`

Expected: FAIL (`Severity.WARNING` vs `INFORMATION`, skip-list still hiding `env_definition`, kind still `ParameterSet`, hidden cluster skipped)

- [ ] **Step 3: Replace `src/envgene_linter/rules/name3.py`**

```python
"""NAME-3: filenames, directories, and namespaces use kebab-case."""

from __future__ import annotations

import re
from pathlib import Path

from ..discovery import paramset_stem
from ..model import Finding, Location, RepoIndex, Severity
from ..rulemeta import RULES

_KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FILE_SUFFIXES = (".yml.j2", ".yaml.j2", ".json.j2", ".yml", ".yaml", ".json")
_HINT = (
    "Review whether this name can be kebab-case. "
    "Do not rename it if generation or other logic still depends on the current spelling."
)


def check(index: RepoIndex) -> list[Finding]:
    findings: list[Finding] = []
    for cluster in index.clusters.values():
        _maybe(findings, cluster.name, "Cluster directory", cluster.path)
        for env in cluster.environments:
            _maybe(findings, env.name, "Environment directory", env.path)
            ns_root = env.path / "Namespaces"
            if ns_root.is_dir():
                for child in ns_root.iterdir():
                    if child.is_dir():
                        _maybe(findings, child.name, "Namespace", child)
    for path in _environment_files(index.root):
        _maybe(findings, paramset_stem(path), "File", path)
    findings.sort(key=lambda item: (item.path.as_posix(), item.key, item.line))
    return findings


def _maybe(findings: list[Finding], name: str, kind: str, path: Path) -> None:
    if _KEBAB.fullmatch(name):
        return
    findings.append(_finding(name, kind, path))


def _finding(name: str, kind: str, path: Path) -> Finding:
    meta = RULES["NAME-3"]
    return Finding(
        rule="NAME-3",
        severity=Severity.INFORMATION,
        path=path,
        line=1,
        column=1,
        issue_type=meta.default_issue_type,
        action=meta.default_action,
        key=name,
        scope=kind,
        message=f"{kind} {name!r} is not kebab-case.",
        hint=_HINT,
        related=(),
        locations=(Location(path, 1, 1),),
    )


def _environment_files(root: Path) -> list[Path]:
    environments = root / "environments"
    if not environments.is_dir():
        return []
    files: list[Path] = []
    for path in environments.rglob("*"):
        if not path.is_file():
            continue
        if any(part == ".git" for part in path.parts):
            continue
        name = path.name
        if any(name.endswith(suffix) for suffix in _FILE_SUFFIXES):
            files.append(path)
    return sorted(files)
```

Do not iterate `ParamsetFile` / `NamedEntityFile` / `PassportFile`. Do not keep `_SKIP`. Do not skip names that start with `.`.

- [ ] **Step 4: Re-run NAME-3 tests (expect PASS)**

Run: `.venv/bin/python -m pytest tests/test_name3.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/rules/name3.py tests/test_name3.py
git commit -m "$(cat <<'EOF'
Report every non-kebab YAML under environments as NAME-3 review.

EOF
)"
```

---

### Task 3: Console and HTML

**Files:**
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `check_name3` already called from `run_check`; `RULES["NAME-3"]` Information / Review
- Produces: console prints `information`; HTML chips Information / Review; typical `check` includes `env_definition`

- [ ] **Step 1: Update CLI tests**

`test_check_no_findings` can no longer expect an empty NAME-3 block (every `repo.env(...)` writes `env_definition.yml`). Replace the exact full-output equality with:

```python
def test_check_no_findings(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    result = CliRunner().invoke(main, ["check", str(repo.root)])
    assert result.exit_code == 0
    assert result.output.startswith(
        "PLACE-1\nNo findings\n\nPLACE-2\nNo findings\n\n"
        "PLACE-3\nNo findings\n\nNAME-1\nNo findings\n\n"
        "NAME-2\nNo findings\n\nNAME-3\n"
    )
    name3 = result.output[result.output.index("NAME-3") :]
    assert "No findings" not in name3
    assert "information" in name3
    assert "env_definition" in name3
    assert "File 'env_definition' is not kebab-case." in name3
```

`test_check_reports_name3_after_name2`: `assert "warning" in name3` → `assert "information" in name3`. Keep `Cluster_01`.

`test_html_name3_section`: replace Warning/Fix chips with Information/Review:

```python
    assert "NAME-3: Filenames, directories, and namespaces use kebab-case" in body
    assert "Information" in body
    assert "Review" in body
    assert "chip-information" in body
    assert "chip-review" in body
```

Do not assert `chip-warning` / `chip-fix` / `Warning` / `Fix` in that test (this fixture has no PLACE/NAME-2 warnings).

`test_html_flag_writes_report_and_keeps_console`: `assert "No findings" in path.read_text(...)` will fail because HTML omits empty rules and NAME-3 now has a finding. Replace that line with:

```python
    assert "NAME-3: Filenames, directories, and namespaces use kebab-case" in path.read_text(encoding="utf-8")
    assert "env_definition" in path.read_text(encoding="utf-8")
```

(or read `body = path.read_text(...)` once). Console `html.stdout == plain.stdout` stays.

Leave `test_report.py` alone: those tests call `render([])` / `render` with explicit findings and never run NAME-3.

- [ ] **Step 2: Run CLI tests (expect FAIL before edits, PASS after)**

If you write the test edits first, run:

`.venv/bin/python -m pytest tests/test_cli.py::test_check_no_findings tests/test_cli.py::test_check_reports_name3_after_name2 tests/test_cli.py::test_html_name3_section tests/test_cli.py::test_html_flag_writes_report_and_keeps_console -v`

Expected after Step 1 + Task 2 code: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "$(cat <<'EOF'
Expect NAME-3 information findings on typical env_definition.yml.

EOF
)"
```

---

### Task 4: Algorithm docs

**Files:**
- Modify: `docs/algorithms/name3.md`
- Modify: `docs/algorithms/ru/name3.md`

**Interfaces:**
- Consumes: amended spec
- Produces: algorithm docs matching Information / Review and the `environments/` walk

- [ ] **Step 1: Rewrite `docs/algorithms/name3.md` so it matches the spec**

Required content (keep the same section numbering style as now):

1. Standard sentence: reports, does not rename; Information / Review because some names are used in generation logic.
2. What is checked: index for cluster/env; `Namespaces/` children including hidden; walk of matching files under `environments/`; kind `File`; do not iterate paramset/passport/entity lists; do not skip `.` prefix.
3. Kebab regex. **No skip-list.** File filter suffixes and `.git`. Stem = `paramset_stem`.
4. Finding fields: `Severity.INFORMATION`, Information, Review, new hint.
5. Console prints `information`. HTML chips Information / Review. Typical fixture with `env_definition.yml` is not an empty NAME-3 block.
6. Worked example `Cluster_01`: Information / Review. Paramset `Cloud_Deploy.yml` uses kind `File`. Same repo also has `File` `'env_definition'`.
7. Non-examples: kebab dirs silent (but `env_definition` still a finding). `env_definition` **is** a finding. `Inventory/` directory is **not** a finding (not cluster/env/namespace). Files outside `environments/` are not checked. `.md` is not checked.

- [ ] **Step 2: Rewrite `docs/algorithms/ru/name3.md` to the same contract** (Russian prose, English identifiers).

- [ ] **Step 3: Commit**

```bash
git add docs/algorithms/name3.md docs/algorithms/ru/name3.md
git commit -m "$(cat <<'EOF'
Document NAME-3 as an environments YAML review rule.

EOF
)"
```

---

### Task 5: Full suite

**Files:** none expected beyond fixes if something failed

- [ ] **Step 1: Run the full suite**

Run: `.venv/bin/python -m pytest -q`

Expected: all passed (count will be higher than 133 because Task 2 added tests).

If `test_html_name1_section` / `test_html_name2_section` fail only because the page now also contains Information/Review from `env_definition`, that is fine — those tests already assert presence of chips, not absence of NAME-3. If any test still expects `NAME-3\nNo findings` from a live `check` of a repo with `env_definition.yml`, update it the same way as `test_check_no_findings`.

- [ ] **Step 2: Commit only if you had to change more files**

---

## Self-review (spec coverage)

| Spec item | Task |
| --- | --- |
| Information / Review catalog and findings | 1, 2 |
| Walk all YAML/JSON/Jinja under `environments/` | 2 |
| No skip-list; `env_definition` reported | 2, 3 |
| Kind `File`; cluster/env/namespace kinds unchanged | 2 |
| `Inventory/` directory silent | 2 |
| Hidden YAML and hidden cluster reported | 2 |
| No files outside `environments/`; no `.md` | 2 |
| Hint review sentence | 2 |
| Console `information`; HTML Information / Review | 3 |
| Typical `check` is not empty NAME-3 | 3 |
| Algorithm docs | 4 |
| Full pytest | 5 |
