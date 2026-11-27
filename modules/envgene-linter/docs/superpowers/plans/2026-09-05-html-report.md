# HTML check report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `envgene-linter check <repo> --html` prints the console report and writes `envgene-linter-report.html` in the instance-repo root, findings grouped by file.

**Architecture:** New `html_report.py` renders a self-contained page from the existing `Finding` list. `cli.py` adds `--html`, writes after stdout. Console `report.py` and the engine stay unchanged.

**Tech Stack:** Python 3.12+, click, pytest, stdlib `html`.

**Spec (English):** `docs/superpowers/specs/2026-09-05-html-report-design.md`  
**Spec (Russian):** `docs/superpowers/specs/ru/2026-09-05-html-report-design.md`

## Global Constraints

- Do not change discovery, Effective Set, PLACE-1/2/3, or `report.py`.
- `--html` is a flag with no path argument. File is always `<repo>/envgene-linter-report.html`.
- Console stdout without `--html` is unchanged. With `--html`, stdout is the same console report; write note is stderr.
- No JavaScript, no `<script>`, escape every field with `html.escape`.
- No autofix, JSON, `--strict`, `--rules`, baseline, or instance-repo `.gitignore` edits.
- Write failure after console print: stderr `cannot write HTML report <path>: <reason>`, exit 2.
- Successful write stderr: `Wrote HTML report to envgene-linter-report.html`
- Prefer `.venv/bin/python -m pytest`.
- No new algorithm docs; no PLACE-* lab trees.

---

## File map

| Path | Change |
| --- | --- |
| `src/envgene_linter/html_report.py` | Create |
| `src/envgene_linter/cli.py` | `--html` |
| `tests/test_html_report.py` | Create |
| `tests/test_cli.py` | Flag and write-failure cases |

---

### Task 1: HTML renderer

**Files:**

- Create: `src/envgene_linter/html_report.py`
- Test: `tests/test_html_report.py`

**Interfaces:**

- Consumes: `Finding`, `RULE_ORDER` from `report.py`
- Produces:
  - `REPORT_FILENAME = "envgene-linter-report.html"`
  - `report_path(root: Path) -> Path` → `root / REPORT_FILENAME`
  - `render_html(findings: list[Finding], root: Path) -> str`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_html_report.py
from pathlib import Path

from envgene_linter.html_report import REPORT_FILENAME, render_html, report_path
from envgene_linter.model import Finding, Severity


def _finding(**overrides) -> Finding:
    data = dict(
        rule="PLACE-2",
        severity=Severity.WARNING,
        path=Path("environments/c/e/Inventory/parameters/p.yml"),
        line=4,
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


def test_two_findings_one_file_one_heading():
    a = _finding(rule="PLACE-1", message="ma", hint="ha")
    b = _finding(rule="PLACE-2", line=8, message="mb", hint="hb")
    body = render_html([a, b], Path("/repo"))
    heading = "environments/c/e/Inventory/parameters/p.yml"
    assert body.count(heading) >= 1
    assert body.index("PLACE-1") < body.index("PLACE-2")
    assert "ma" in body and "mb" in body
    assert "ha" in body and "hb" in body
    assert "warning" in body
    assert "line 4" in body and "line 8" in body


def test_two_files_two_headings():
    a = _finding(path=Path("environments/parameters/shared.yml"), rule="PLACE-3")
    b = _finding(path=Path("environments/c/e/Inventory/parameters/p.yml"), rule="PLACE-2")
    body = render_html([b, a], Path("/repo"))
    first = body.index("environments/c/e/Inventory/parameters/p.yml")
    second = body.index("environments/parameters/shared.yml")
    assert first < second


def test_zero_findings_says_no_findings():
    body = render_html([], Path("/repo"))
    assert "No findings" in body
    assert "PLACE-1: 0, PLACE-2: 0, PLACE-3: 0" in body
    assert "finding-file" not in body


def test_angle_brackets_are_escaped():
    body = render_html([_finding(message="x < y & z")], Path("/repo"))
    assert "x &lt; y &amp; z" in body
    assert "x < y" not in body


def test_no_script_tags():
    body = render_html([_finding()], Path("/repo"))
    assert "<script" not in body
    assert "Do not commit this file" in body
    assert "envgene-linter check --html" in body
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_html_report.py -v`  
Expected: FAIL — `ModuleNotFoundError: envgene_linter.html_report`

- [ ] **Step 3: Write html_report.py**

```python
# src/envgene_linter/html_report.py
"""Self-contained HTML check report for an instance repository."""

from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path

from .model import Finding
from .report import RULE_ORDER

REPORT_FILENAME = "envgene-linter-report.html"

_CSS = """
:root { color-scheme: light; }
body {
  font: 15px/1.45 system-ui, sans-serif;
  max-width: 56rem;
  margin: 2rem auto;
  padding: 0 1.25rem 3rem;
  color: #1a1a1a;
}
h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
h2.finding-file {
  font-size: 0.95rem;
  font-family: ui-monospace, monospace;
  margin: 1.75rem 0 0.6rem;
}
.muted { color: #555; }
.note { background: #fff6d6; border: 1px solid #ead48a; padding: 0.7rem 0.9rem; }
.finding {
  margin: 0.75rem 0 1.15rem;
  padding: 0.85rem 1rem;
  border: 1px solid #e2e2e2;
  border-left: 4px solid #c9a227;
  border-radius: 6px;
  background: #fafafa;
}
.finding p { margin: 0.35rem 0; }
.finding p:first-child { margin-top: 0; }
.finding p:last-child { margin-bottom: 0; }
.meta { font-family: ui-monospace, monospace; font-size: 0.88em; }
"""


def report_path(root: Path) -> Path:
    return root / REPORT_FILENAME


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def render_html(findings: list[Finding], root: Path) -> str:
    counts = {rule: 0 for rule in RULE_ORDER}
    by_file: dict[str, list[Finding]] = defaultdict(list)
    for item in findings:
        counts[item.rule] = counts.get(item.rule, 0) + 1
        by_file[_relative(item.path, root)].append(item)
    summary = ", ".join(f"{rule}: {counts[rule]}" for rule in RULE_ORDER)
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>envgene-linter report</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        "<h1>envgene-linter report</h1>",
        f'<p class="muted">{html.escape(summary)}</p>',
        '<p class="note">Generated by <code>envgene-linter check --html</code>. '
        "Do not commit this file; it is overwritten on every run.</p>",
    ]
    if not findings:
        parts.append("<p>No findings</p>")
    else:
        for rel in sorted(by_file):
            parts.append(f'<h2 class="finding-file">{html.escape(rel)}</h2>')
            ordered = sorted(
                by_file[rel],
                key=lambda item: (
                    RULE_ORDER.index(item.rule) if item.rule in RULE_ORDER else len(RULE_ORDER),
                ),
            )
            for item in ordered:
                parts.append('<div class="finding">')
                parts.append(
                    f'<p class="meta">{html.escape(item.rule)} · '
                    f"{html.escape(item.severity.value)} · line {item.line}</p>"
                )
                parts.append(f"<p>{html.escape(item.message)}</p>")
                parts.append(f"<p>{html.escape(item.hint)}</p>")
                parts.append("</div>")
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)
```

Note: `test_two_files_two_headings` sorts by relative path. `environments/c/...` comes before `environments/parameters/...`. The test passes `[b, a]` (c-path first in the list); after sort, `environments/c/...` is still first. Good.

For paths that are already relative (`environments/...`) and `root` is `/repo`, `resolve()` may not sit under `/repo`. `_relative` then falls back to `path.as_posix()`, which is what the tests use. Keep that fallback.

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_html_report.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/html_report.py tests/test_html_report.py
git commit -m "Render a self-contained HTML check report grouped by file."
```

---

### Task 2: `--html` on check

**Files:**

- Modify: `src/envgene_linter/cli.py`
- Modify: `tests/test_cli.py`

**Interfaces:**

- Consumes: `render_html`, `report_path`, `REPORT_FILENAME`
- Produces: `check --html` writes the file after stdout; write errors exit 2

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_cli.py`:

```python
from envgene_linter.html_report import REPORT_FILENAME


def test_html_flag_writes_report_and_keeps_console(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    runner = CliRunner()
    plain = runner.invoke(main, ["check", str(repo.root)])
    html = runner.invoke(main, ["check", str(repo.root), "--html"])
    assert html.exit_code == 0
    assert html.output == plain.output
    path = repo.root / REPORT_FILENAME
    assert path.is_file()
    assert "No findings" in path.read_text(encoding="utf-8")
    assert "Wrote HTML report to envgene-linter-report.html" in html.output
    # click.testing merges stdout+stderr into output; the write line must not be in stdout-only
    # if the runner mixes streams. Assert the file exists and console PLACE headers still lead.
    assert html.output.startswith("PLACE-1\n")


def test_without_html_flag_no_report_file(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    CliRunner().invoke(main, ["check", str(repo.root)])
    assert not (repo.root / REPORT_FILENAME).exists()


def test_html_write_failure_exits_2_after_console(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY": 1})
    blocker = repo.root / REPORT_FILENAME
    blocker.mkdir()
    result = CliRunner().invoke(main, ["check", str(repo.root), "--html"])
    assert result.exit_code == 2
    assert result.output.startswith("PLACE-1\n")
    assert "cannot write HTML report" in result.output
```

`CliRunner` combines stdout and stderr. The write-success line will appear in `result.output` after the console text. Do **not** require `html.output == plain.output` if that fails because of the stderr line. If they differ only by the write notice, assert:

```python
    assert html.output.startswith(plain.output)
    assert "Wrote HTML report to envgene-linter-report.html" in html.output
```

Use that form instead of equality if needed. The spec's "same bytes on stdout" is satisfied if stdout starts with the console report and the write line is stderr (mixed into `output` by Click).

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`  
Expected: FAIL — unknown option `--html` or file not written

- [ ] **Step 3: Wire the flag**

```python
# src/envgene_linter/cli.py
from .html_report import report_path, render_html


@main.command("check")
@click.argument("repo", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--html",
    "write_html",
    is_flag=True,
    help="Write envgene-linter-report.html in the repository root (do not commit it).",
)
def check_cmd(repo: Path, write_html: bool) -> None:
    try:
        result = run_check(repo)
    except DiscoveryError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(2) from exc
    click.echo(render(result.findings), nl=False)
    for note in result.skipped:
        click.echo(note, err=True)
    if not write_html:
        return
    path = report_path(repo)
    try:
        path.write_text(render_html(result.findings, repo), encoding="utf-8")
    except OSError as exc:
        click.echo(f"cannot write HTML report {path}: {exc}", err=True)
        raise SystemExit(2) from exc
    click.echo("Wrote HTML report to envgene-linter-report.html", err=True)
```

Keep the unused `sys` import only if it is already used; if `sys` is unused, leave it (do not do drive-by cleanup unless the file already imported it unused — it is unused today; do not remove it in this task unless you touch that line).

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_cli.py tests/test_html_report.py tests/test_lab.py -v`  
Expected: PASS

- [ ] **Step 5: Full suite and commit**

Run: `.venv/bin/python -m pytest -q`  
Expected: all green

```bash
git add src/envgene_linter/cli.py tests/test_cli.py
git commit -m "Write the HTML report when check is passed --html."
```

---

## Self-review (plan vs spec)

| Spec | Task |
| --- | --- |
| `html_report.py`, filename, `render_html` | 1 |
| Group by file, cards, escape, no script, summary, empty page | 1 |
| `--html`, write after console, stderr note | 2 |
| Write failure exit 2 | 2 |
| No `--html` → no file | 2 |
| Console renderer / engine / rules untouched | both |
