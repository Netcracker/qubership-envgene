# HTML report redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Regroup the HTML report by rule, render FILE / ISSUE / TYPE / ACTION / FIX SUGGESTION table-cards with chips, store column / issue_type / action on findings, shorten ISSUE and FIX SUGGESTION copy, and add the report filename to the instance `.gitignore`.

**Architecture:** `rulemeta.py` holds per-rule description and default TYPE/ACTION. `Finding` gains `column`, `issue_type`, and `action`. `html_report.py` groups by rule and paints the table+chips page. `cli.py` calls `ensure_report_ignored` after a successful HTML write. PLACE-* rules fill the new fields and emit the shorter English strings. Console layout in `report.py` stays.

**Tech Stack:** Python 3.12+, click, pytest, ruamel.yaml (existing `position()`), stdlib `html`.

**Spec (English):** `docs/superpowers/specs/2026-09-05-html-report-redesign-design.md`  
**Spec (Russian):** `docs/superpowers/specs/ru/2026-09-05-html-report-redesign-design.md`

## Global Constraints

- Do not change discovery, Effective Set, or PLACE-* detection (who fires). Only finding fields and texts.
- `report.py` block shape stays, including empty `PLACE-2\nNo findings` console blocks. Path stays `{path}:{line}` (no column).
- `--html` still writes `<repo>/envgene-linter-report.html` after console stdout. Write failure: stderr `cannot write HTML report <path>: <reason>`, exit 2.
- Successful HTML write stderr: `Wrote HTML report to envgene-linter-report.html`
- No JavaScript, no `<script>`, escape every field with `html.escape`.
- No JSON, autofix, `--strict`, `--rules`, baseline, or passport merge into Effective Set.
- Current PLACE-* findings: TYPE `Warning`, ACTION `Fix`. Enums also include Error, Information, Review.
- Prefer `.venv/bin/python -m pytest`.
- No new algorithm docs.

---

## File map

| Path | Change |
| --- | --- |
| `src/envgene_linter/model.py` | `IssueType`, `Action`; Finding `column`, `issue_type`, `action` |
| `src/envgene_linter/rulemeta.py` | Create — catalog |
| `src/envgene_linter/html_report.py` | Rule groups, table+chips, `ensure_report_ignored` |
| `src/envgene_linter/cli.py` | After HTML write, update instance `.gitignore` |
| `src/envgene_linter/rules/place1.py` | `column`; catalog defaults; new texts |
| `src/envgene_linter/rules/place2.py` | same |
| `src/envgene_linter/rules/place3.py` | same (`column=1` for passport-file findings) |
| `tests/test_rulemeta.py` | Create |
| `tests/test_html_report.py` | New page + gitignore unit tests |
| `tests/test_cli.py` | gitignore wiring |
| `tests/test_place1.py` / `test_place2.py` / `test_place3.py` | New hint/message pins; one column assert |

`report.py` and `yamlio.py` are not modified.

---

### Task 1: Finding fields and rule catalog

**Files:**
- Modify: `src/envgene_linter/model.py`
- Create: `src/envgene_linter/rulemeta.py`
- Create: `tests/test_rulemeta.py`

**Interfaces:**
- Consumes: existing `Finding`, `Severity`
- Produces:
  - `class IssueType(Enum)` values `ERROR = "Error"`, `WARNING = "Warning"`, `INFORMATION = "Information"`
  - `class Action(Enum)` values `FIX = "Fix"`, `REVIEW = "Review"`
  - `Finding.column: int = 1`
  - `Finding.issue_type: IssueType = IssueType.WARNING`
  - `Finding.action: Action = Action.FIX`
  - `@dataclass(frozen=True) class RuleMeta` with `id: str`, `description: str`, `default_issue_type: IssueType`, `default_action: Action`
  - `RULES: dict[str, RuleMeta]` keyed by id
  - `def defaults_for(rule_id: str) -> tuple[IssueType, Action]`

New Finding fields have defaults so existing `Finding(...)` calls and `report.py` tests keep passing.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_rulemeta.py
from pathlib import Path

from envgene_linter.model import Action, Finding, IssueType, Severity
from envgene_linter.rulemeta import RULES, defaults_for


def test_catalog_defaults_for_place_rules():
    assert set(RULES) == {"PLACE-1", "PLACE-2", "PLACE-3"}
    assert RULES["PLACE-1"].description == "Same value belongs on a higher layer"
    assert RULES["PLACE-2"].description == "Higher layer restates a lower-layer value"
    assert RULES["PLACE-3"].description == "Cloud Passport keys and files are misplaced"
    for item in RULES.values():
        assert item.default_issue_type is IssueType.WARNING
        assert item.default_action is Action.FIX


def test_defaults_for_returns_catalog_pair():
    assert defaults_for("PLACE-2") == (IssueType.WARNING, Action.FIX)


def test_finding_new_fields_default():
    finding = Finding(
        rule="PLACE-1",
        severity=Severity.WARNING,
        path=Path("a.yml"),
        line=4,
        key="K",
        scope="s",
        message="m",
        hint="h",
    )
    assert finding.column == 1
    assert finding.issue_type is IssueType.WARNING
    assert finding.action is Action.FIX
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_rulemeta.py -v`

Expected: FAIL (import error: `rulemeta` or `IssueType` missing)

- [ ] **Step 3: Write minimal implementation**

In `src/envgene_linter/model.py`, add the enums near `Severity` and extend `Finding`:

```python
class IssueType(Enum):
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"


class Action(Enum):
    FIX = "Fix"
    REVIEW = "Review"
```

```python
@dataclass(frozen=True)
class Finding:
    rule: str
    severity: Severity
    path: Path
    line: int
    key: str
    scope: str
    message: str
    hint: str
    related: tuple[str, ...] = ()
    column: int = 1
    issue_type: IssueType = IssueType.WARNING
    action: Action = Action.FIX
```

Create `src/envgene_linter/rulemeta.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from .model import Action, IssueType


@dataclass(frozen=True)
class RuleMeta:
    id: str
    description: str
    default_issue_type: IssueType
    default_action: Action


RULES: dict[str, RuleMeta] = {
    "PLACE-1": RuleMeta(
        "PLACE-1",
        "Same value belongs on a higher layer",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-2": RuleMeta(
        "PLACE-2",
        "Higher layer restates a lower-layer value",
        IssueType.WARNING,
        Action.FIX,
    ),
    "PLACE-3": RuleMeta(
        "PLACE-3",
        "Cloud Passport keys and files are misplaced",
        IssueType.WARNING,
        Action.FIX,
    ),
}


def defaults_for(rule_id: str) -> tuple[IssueType, Action]:
    item = RULES[rule_id]
    return item.default_issue_type, item.default_action
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_rulemeta.py tests/test_report.py tests/test_html_report.py -v`

Expected: PASS (old HTML tests still see the old page; Finding still constructs)

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/model.py src/envgene_linter/rulemeta.py tests/test_rulemeta.py
git commit -m "$(cat <<'EOF'
Add finding type, action, column defaults and a rule catalog.

EOF
)"
```

---

### Task 2: HTML page grouped by rule

**Files:**
- Modify: `src/envgene_linter/html_report.py`
- Modify: `tests/test_html_report.py`

**Interfaces:**
- Consumes: `Finding` (including `column`, `issue_type`, `action`), `RULES` from `rulemeta`, `RULE_ORDER`, existing `report_path` / `_relative` / `REPORT_FILENAME`
- Produces: `render_html(findings: list[Finding], root: Path) -> str` — title `Envgene Linter Report`; sections only for rules that have findings; cards with labels FILE, ISSUE, TYPE, ACTION, FIX SUGGESTION

- [ ] **Step 1: Replace `tests/test_html_report.py` with the new contract**

Keep `_finding` and `test_report_path_is_visible_file_in_repo_root`. Replace the rest. Add `column` / type / action only when a test needs a non-default.

```python
from pathlib import Path

from envgene_linter.html_report import REPORT_FILENAME, render_html, report_path
from envgene_linter.model import Action, Finding, IssueType, Severity


def _finding(**overrides) -> Finding:
    data = dict(
        rule="PLACE-2",
        severity=Severity.WARNING,
        path=Path("environments/c/e/Inventory/parameters/p.yml"),
        line=4,
        column=3,
        key="K",
        scope="s",
        message="problem text",
        hint="fix it",
    )
    data.update(overrides)
    return Finding(**data)


def test_report_path_is_visible_file_in_repo_root(tmp_path):
    assert report_path(tmp_path) == tmp_path / "envgene-linter-report.html"
    assert REPORT_FILENAME == "envgene-linter-report.html"


def test_two_place1_findings_one_rule_heading():
    a = _finding(rule="PLACE-1", path=Path("environments/a.yml"), message="ma", hint="ha")
    b = _finding(rule="PLACE-1", path=Path("environments/b.yml"), line=8, column=5, message="mb", hint="hb")
    body = render_html([a, b], Path("/repo"))
    assert body.count("PLACE-1") >= 1
    assert "Same value belongs on a higher layer" in body
    assert "PLACE-2" not in body
    assert body.count('class="finding"') == 2
    assert "FILE" in body and "ISSUE" in body and "TYPE" in body
    assert "ACTION" in body and "FIX SUGGESTION" in body
    assert "environments/a.yml:4:3" in body
    assert "environments/b.yml:8:5" in body
    assert "ma" in body and "mb" in body
    assert "ha" in body and "hb" in body
    assert "Warning" in body and "Fix" in body
    assert 'class="finding-file"' not in body


def test_rule_order_place1_then_place3():
    a = _finding(rule="PLACE-3", path=Path("environments/z.yml"))
    b = _finding(rule="PLACE-1", path=Path("environments/a.yml"))
    body = render_html([a, b], Path("/repo"))
    assert body.index("PLACE-1") < body.index("PLACE-3")
    assert "PLACE-2" not in body


def test_unknown_rule_has_heading_without_catalog_blurb():
    body = render_html([_finding(rule="OTHER")], Path("/repo"))
    assert "OTHER" in body
    assert "Same value belongs on a higher layer" not in body


def test_zero_findings_says_no_findings():
    body = render_html([], Path("/repo"))
    assert "No findings" in body
    assert "Envgene Linter Report" in body
    assert "PLACE-1: 0" not in body
    assert "<h2" not in body


def test_angle_brackets_are_escaped():
    body = render_html([_finding(message="x < y & z")], Path("/repo"))
    assert "x &lt; y &amp; z" in body
    assert "x < y" not in body


def test_no_script_tags():
    body = render_html([_finding()], Path("/repo"))
    assert "<script" not in body
    assert "Do not commit this file" not in body
    assert "Envgene Linter Report" in body
    assert "chip-warning" in body
    assert "chip-fix" in body


def test_unknown_type_uses_gray_chip():
    body = render_html(
        [_finding(issue_type=IssueType.INFORMATION, action=Action.REVIEW)],
        Path("/repo"),
    )
    assert "Information" in body
    assert "Review" in body
    assert "chip-information" in body
    assert "chip-review" in body
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_html_report.py -v`

Expected: FAIL (old grouping / missing labels / old title)

- [ ] **Step 3: Replace `render_html` (keep `report_path` and `_relative`)**

Rewrite `src/envgene_linter/html_report.py` to this file (imports + helpers + CSS + `render_html`). Do not add `ensure_report_ignored` yet (Task 3).

```python
"""Self-contained HTML check report for an instance repository."""

from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path

from .model import Action, Finding, IssueType
from .report import RULE_ORDER
from .rulemeta import RULES

REPORT_FILENAME = "envgene-linter-report.html"

_CHIP_CLASS = {
    IssueType.WARNING.value: "chip-warning",
    IssueType.ERROR.value: "chip-error",
    IssueType.INFORMATION.value: "chip-information",
    Action.FIX.value: "chip-fix",
    Action.REVIEW.value: "chip-review",
}

_CSS = """
:root { color-scheme: light; }
body {
  font: 15px/1.45 system-ui, sans-serif;
  max-width: 56rem;
  margin: 2rem auto;
  padding: 0 1.25rem 3rem;
  color: #1a1a1a;
}
h1 {
  font: 700 1.7rem/1.2 Georgia, "Times New Roman", serif;
  margin: 0 0 1.4rem;
}
h2.rule-id {
  font: 600 1.15rem/1.3 Georgia, "Times New Roman", serif;
  margin: 1.75rem 0 0.2rem;
}
.rule-desc { color: #555; margin: 0 0 0.7rem; }
.finding {
  margin: 0 0 0.85rem;
  border: 1px solid #e2e2e2;
  border-radius: 6px;
  background: #fafafa;
  overflow: hidden;
  display: grid;
  grid-template-columns: 9rem 1fr;
  font-size: 0.95rem;
}
.label {
  padding: 0.5rem 0.7rem;
  background: #f3f3f3;
  font-weight: 700;
  border-bottom: 1px solid #eee;
}
.value {
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid #eee;
}
.finding .label:last-of-type, .finding .value:last-child { border-bottom: 0; }
.file { font-family: ui-monospace, monospace; font-size: 0.88em; }
.chip {
  display: inline-block;
  border-radius: 999px;
  padding: 0.12rem 0.6rem;
  font-size: 0.8rem;
  border: 1px solid #bbb;
  background: #eee;
}
.chip-warning { background: #fff3cd; border-color: #e0c36a; }
.chip-error { background: #fde8e8; border-color: #e39a9a; }
.chip-information { background: #e8eef5; border-color: #b0bec5; }
.chip-fix { background: #e8f0fe; border-color: #9db7e8; }
.chip-review { background: #eee; border-color: #bbb; }
"""


def report_path(root: Path) -> Path:
    return root / REPORT_FILENAME


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()


def _rule_sort_key(rule: str) -> tuple[int, int | str]:
    if rule in RULE_ORDER:
        return (0, RULE_ORDER.index(rule))
    return (1, rule)


def _chip(value: str) -> str:
    cls = _CHIP_CLASS.get(value, "chip-review")
    return f'<span class="chip {cls}">{html.escape(value)}</span>'


def _card(item: Finding, root: Path) -> list[str]:
    loc = f"{_relative(item.path, root)}:{item.line}:{item.column}"
    rows = (
        ("FILE", f'<span class="file">{html.escape(loc)}</span>'),
        ("ISSUE", html.escape(item.message)),
        ("TYPE", _chip(item.issue_type.value)),
        ("ACTION", _chip(item.action.value)),
        ("FIX SUGGESTION", html.escape(item.hint)),
    )
    parts = ['<div class="finding">']
    for label, value in rows:
        parts.append(f'<div class="label">{html.escape(label)}</div>')
        parts.append(f'<div class="value">{value}</div>')
    parts.append("</div>")
    return parts


def render_html(findings: list[Finding], root: Path) -> str:
    by_rule: dict[str, list[Finding]] = defaultdict(list)
    for item in findings:
        by_rule[item.rule].append(item)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Envgene Linter Report</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        "<h1>Envgene Linter Report</h1>",
    ]
    if not findings:
        parts.append("<p>No findings</p>")
    else:
        for rule in sorted(by_rule, key=_rule_sort_key):
            parts.append(f'<h2 class="rule-id">{html.escape(rule)}</h2>')
            meta = RULES.get(rule)
            if meta is not None:
                parts.append(f'<p class="rule-desc">{html.escape(meta.description)}</p>')
            for item in by_rule[rule]:
                parts.extend(_card(item, root))
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)
```

- [ ] **Step 4: Run HTML tests**

Run: `.venv/bin/python -m pytest tests/test_html_report.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/html_report.py tests/test_html_report.py
git commit -m "$(cat <<'EOF'
Regroup the HTML report by rule and render labeled table cards.

EOF
)"
```

---

### Task 3: Ignore the report in the instance `.gitignore`

**Files:**
- Modify: `src/envgene_linter/html_report.py`
- Modify: `src/envgene_linter/cli.py`
- Modify: `tests/test_html_report.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Consumes: `REPORT_FILENAME`, `report_path`, `render_html`
- Produces: `ensure_report_ignored(root: Path) -> None`  
  Creates or appends `envgene-linter-report.html`. No-op if a trimmed line is already `envgene-linter-report.html` or `/envgene-linter-report.html`.  
  CLI: after a successful HTML write, call it; on `OSError` print `cannot update .gitignore <path>: <reason>` on stderr and do **not** change the exit code. Then print the existing Wrote line.

- [ ] **Step 1: Add failing unit tests to `tests/test_html_report.py`**

```python
from envgene_linter.html_report import ensure_report_ignored


def test_ensure_report_ignored_creates_gitignore(tmp_path):
    ensure_report_ignored(tmp_path)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == "envgene-linter-report.html\n"


def test_ensure_report_ignored_appends(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.pyc\n", encoding="utf-8")
    ensure_report_ignored(tmp_path)
    assert gitignore.read_text(encoding="utf-8") == "*.pyc\nenvgene-linter-report.html\n"


def test_ensure_report_ignored_skips_when_present(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("/envgene-linter-report.html\n", encoding="utf-8")
    before = gitignore.read_bytes()
    ensure_report_ignored(tmp_path)
    assert gitignore.read_bytes() == before
```

- [ ] **Step 2: Run those three tests**

Run: `.venv/bin/python -m pytest tests/test_html_report.py::test_ensure_report_ignored_creates_gitignore tests/test_html_report.py::test_ensure_report_ignored_appends tests/test_html_report.py::test_ensure_report_ignored_skips_when_present -v`

Expected: FAIL (`ensure_report_ignored` missing)

- [ ] **Step 3: Implement `ensure_report_ignored` in `html_report.py`**

```python
def ensure_report_ignored(root: Path) -> None:
    path = root / ".gitignore"
    names = {REPORT_FILENAME, f"/{REPORT_FILENAME}"}
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if any(line.strip() in names for line in text.splitlines()):
            return
        if text and not text.endswith("\n"):
            text += "\n"
        path.write_text(f"{text}{REPORT_FILENAME}\n", encoding="utf-8")
        return
    path.write_text(f"{REPORT_FILENAME}\n", encoding="utf-8")
```

- [ ] **Step 4: Re-run the three unit tests**

Run: `.venv/bin/python -m pytest tests/test_html_report.py::test_ensure_report_ignored_creates_gitignore tests/test_html_report.py::test_ensure_report_ignored_appends tests/test_html_report.py::test_ensure_report_ignored_skips_when_present -v`

Expected: PASS

- [ ] **Step 5: Add failing CLI tests in `tests/test_cli.py`**

Update `test_html_flag_writes_report_and_keeps_console` to also assert gitignore. Add three new tests. Change `test_html_flag_writes_findings_with_file_heading` to assert a rule section (not a file `h2`).

```python
def test_html_flag_writes_report_and_keeps_console(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    runner = CliRunner()
    plain = runner.invoke(main, ["check", str(repo.root)])
    html = runner.invoke(main, ["check", str(repo.root), "--html"])
    assert html.exit_code == 0
    assert html.stdout == plain.stdout
    path = repo.root / REPORT_FILENAME
    assert path.is_file()
    assert "No findings" in path.read_text(encoding="utf-8")
    assert "Wrote HTML report to envgene-linter-report.html" in html.stderr
    assert "envgene-linter-report.html" in (repo.root / ".gitignore").read_text(encoding="utf-8")


def test_html_flag_writes_findings_with_file_heading(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"MONITORING_URL": "https://m.example.com"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"MONITORING_URL": "https://m.example.com"})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--html"])
    assert result.exit_code == 0
    body = (repo.root / REPORT_FILENAME).read_text(encoding="utf-8")
    assert "PLACE-1" in body
    assert "FILE" in body
    assert "environments/cluster-01/env-01/Inventory/parameters/env-params.yml" in body
    assert "MONITORING_URL" in body


def test_without_html_flag_no_report_file(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    CliRunner().invoke(main, ["check", str(repo.root)])
    assert not (repo.root / REPORT_FILENAME).exists()
    assert not (repo.root / ".gitignore").exists()


def test_html_keeps_existing_gitignore_lines(repo):
    gitignore = repo.root / ".gitignore"
    gitignore.write_text("*.pyc\n", encoding="utf-8")
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    result = CliRunner().invoke(main, ["check", str(repo.root), "--html"])
    assert result.exit_code == 0
    text = gitignore.read_text(encoding="utf-8")
    assert text.startswith("*.pyc\n")
    assert "envgene-linter-report.html" in text


def test_html_gitignore_failure_warns_and_keeps_exit_0(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    (repo.root / ".gitignore").mkdir()
    result = CliRunner().invoke(main, ["check", str(repo.root), "--html"])
    assert result.exit_code == 0
    assert (repo.root / REPORT_FILENAME).is_file()
    assert "cannot update .gitignore" in result.stderr
    assert "Wrote HTML report to envgene-linter-report.html" in result.stderr
```

Leave `test_html_write_failure_exits_2_after_console` as it is.

- [ ] **Step 6: Run CLI HTML tests to verify new ones fail**

Run: `.venv/bin/python -m pytest tests/test_cli.py -k html -v`

Expected: FAIL on gitignore assertions (`test_html_flag_writes_report_and_keeps_console`, `test_without_html_flag_no_report_file` if a leftover file appears — should fail because CLI does not write gitignore yet; `test_without_html` still passes until wiring exists and someone writes gitignore without `--html`, so it stays green. `test_html_keeps_existing` and `test_html_gitignore_failure` fail.)

- [ ] **Step 7: Wire CLI**

In `src/envgene_linter/cli.py`:

```python
from .html_report import ensure_report_ignored, report_path, render_html
```

After a successful `path.write_text(...)`:

```python
    try:
        ensure_report_ignored(repo)
    except OSError as exc:
        click.echo(f"cannot update .gitignore {repo / '.gitignore'}: {exc}", err=True)
    click.echo("Wrote HTML report to envgene-linter-report.html", err=True)
```

Optional help tweak (same flag): `help="Write envgene-linter-report.html in the repository root and ignore it."`

- [ ] **Step 8: Run CLI + HTML tests**

Run: `.venv/bin/python -m pytest tests/test_cli.py tests/test_html_report.py -v`

Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add src/envgene_linter/html_report.py src/envgene_linter/cli.py tests/test_html_report.py tests/test_cli.py
git commit -m "$(cat <<'EOF'
Ignore the HTML report in the instance repository gitignore.

EOF
)"
```

---

### Task 4: Column, catalog fields, and shorter rule texts

**Files:**
- Modify: `src/envgene_linter/rules/place1.py`
- Modify: `src/envgene_linter/rules/place2.py`
- Modify: `src/envgene_linter/rules/place3.py`
- Modify: `tests/test_place1.py`
- Modify: `tests/test_place2.py` (only if a hint pin breaks — `Remove LOG_LEVEL` still matches)
- Modify: `tests/test_place3.py` (message still contains `repository` / `cluster-01`; add exact strings where cheap)

**Interfaces:**
- Consumes: `defaults_for` or `RULES[rule_id]`, `leaf.provenance.position -> tuple[int, int]`
- Produces: every `Finding(...)` sets `column` (passport file findings: `column=1`) and `issue_type` / `action` from the catalog. Messages and hints are exactly the spec strings.

Exact texts:

PLACE-1 env → cluster:

```python
message = (
    f"Key {leaf.key} has the same value in {len(owners)} environments "
    f"of cluster {cluster.name}."
)
hint = (
    f"Move {leaf.key} to environments/{cluster.name}/parameters/ "
    f"and remove the environment copies."
)
```

PLACE-1 cluster → repository:

```python
message = f"Key {leaf.key} has the same value in {len(owners)} clusters."
hint = (
    f"Move {leaf.key} to a repository paramset and remove the cluster copies."
)
```

PLACE-2:

```python
message = (
    f"Key {leaf.key} at the {layer.value} layer repeats the lower-layer value."
)
hint = (
    f"Remove {leaf.key} from this file, or change the value if the override "
    f"is intentional."
)
```

PLACE-3 file: `message=f"Passport {item.stem} is not at the cluster layer."` — hint stays `_file_hint(...)`. `line=1`, `column=1`.

PLACE-3 repository key:

```python
message = f"{key} is a Cloud Passport key authored at the repository layer."
hint = f"Move {key} to a cluster-layer paramset."
```

PLACE-3 env agreement:

```python
message = (
    f"{key} is a Cloud Passport key repeated in environments of cluster "
    f"{cluster.name}."
)
hint = (
    f"Move {key} to the cluster layer unless an environment needs a different value."
)
```

On every Finding, after `line=...`:

```python
from ..rulemeta import RULES

meta = RULES["PLACE-1"]  # or PLACE-2 / PLACE-3
# ...
line, column = leaf.provenance.position
Finding(
    ...,
    line=line,
    column=column,
    issue_type=meta.default_issue_type,
    action=meta.default_action,
    ...
)
```

For PLACE-1, `position` is used twice today (`line=leaf.provenance.position[0]`). Unpack once.

Keep `related=` as it is now (not shown on the HTML page). Do not put sibling file lists into `hint`.

- [ ] **Step 1: Pin copy and column on the existing PLACE-1 tests**

In `tests/test_place1.py`, extend `test_value_repeated_in_every_environment_should_move_to_the_cluster` (keep the current asserts, add these):

```python
    from envgene_linter.yamlio import load

    assert findings[0].message == (
        "Key MONITORING_URL has the same value in 2 environments of cluster cluster-01."
    )
    assert findings[0].hint == (
        "Move MONITORING_URL to environments/cluster-01/parameters/ "
        "and remove the environment copies."
    )
    loaded = load(findings[0].path)
    _, col = loaded.position(("parameters", "MONITORING_URL"))
    assert findings[0].column == col
    assert findings[0].issue_type.value == "Warning"
    assert findings[0].action.value == "Fix"
```

In `test_value_repeated_in_every_cluster_should_move_to_the_repository`, replace the hint substring assert with:

```python
    assert findings[0].message == "Key E2E_BASE_URL has the same value in 2 clusters."
    assert findings[0].hint == (
        "Move E2E_BASE_URL to a repository paramset and remove the cluster copies."
    )
```

- [ ] **Step 2: Run the place1 tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_place1.py -v`

Expected: FAIL on the new exact `message` / `hint` / `column`

- [ ] **Step 3: Update PLACE-1 / PLACE-2 / PLACE-3 `Finding(...)` calls**

Apply the strings and fields above in all six constructors (2 in place1, 1 in place2, 3 in place3).

- [ ] **Step 4: Run place + report + html + cli tests**

Run: `.venv/bin/python -m pytest tests/test_place1.py tests/test_place2.py tests/test_place3.py tests/test_report.py tests/test_html_report.py tests/test_cli.py -v`

Expected: PASS. If `test_place3` still looks for `"repository" in message` / `"cluster-01" in message`, those substrings remain. If a test expected `environments/parameters/` in a PLACE-1 hint, it must use the new repository hint. `test_place2` `Remove LOG_LEVEL` still matches.

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/rules/place1.py src/envgene_linter/rules/place2.py src/envgene_linter/rules/place3.py tests/test_place1.py tests/test_place2.py tests/test_place3.py
git commit -m "$(cat <<'EOF'
Put column and shorter fix copy on PLACE findings.

EOF
)"
```

---

### Task 5: Full suite

**Files:** none unless a test failed in Task 4 that you deferred

- [ ] **Step 1: Run the full suite**

Run: `.venv/bin/python -m pytest -q`

Expected: PASS, all tests (currently 86 plus the new ones; count will rise)

- [ ] **Step 2: Commit only if Task 4 left a leftover fix**

If the suite is already green and nothing is uncommitted, skip. If you had to fix an assertion, commit that fix with:

```bash
git commit -m "$(cat <<'EOF'
Align leftover tests with the redesigned HTML report.

EOF
)"
```
