# HTML report usability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** List every copy path on multi-file findings, collapse each rule behind a closed `<details>` titled `PLACE-1: …`, and quiet the card labels.

**Architecture:** Add `Location` and `Finding.locations`. `Finding.file_locations()` is the single helper for HTML and console. PLACE-1 and PLACE-3 env-agreement fill `locations`. `report.py` prints every `path:line:column`. `html_report.py` uses `<details>`/`<summary>` and a multi-line FILE cell.

**Tech Stack:** Python 3.12+, pytest, existing `html.escape`. No JavaScript.

**Spec (English):** `docs/superpowers/specs/2026-09-05-html-report-usability-design.md`  
**Spec (Russian):** `docs/superpowers/specs/ru/2026-09-05-html-report-usability-design.md`

## Global Constraints

- Do not change who PLACE-* fires. Do not rewrite ISSUE / FIX SUGGESTION sentences.
- `related` is unchanged and not shown on the page.
- No JavaScript, no `<script>`, escape every field with `html.escape`.
- `<details>` for rules with findings must **not** have an `open` attribute.
- Heading shape: `{id}: {description}` for catalog rules; unknown rule is the id only (no colon).
- Empty `locations` → one primary `Location(path, line, column)`.
- Console empty rule blocks stay `PLACE-2\nNo findings`. Console location lines are `{path}:{line}:{column}`.
- No new algorithm docs. No JSON / autofix.
- Prefer `.venv/bin/python -m pytest`.

---

## File map

| Path | Change |
| --- | --- |
| `src/envgene_linter/model.py` | `Location`, `Finding.locations`, `Finding.file_locations()` |
| `src/envgene_linter/rules/place1.py` | fill `locations` on both constructors |
| `src/envgene_linter/rules/place3.py` | fill `locations` on env-agreement only |
| `src/envgene_linter/report.py` | all location lines |
| `src/envgene_linter/html_report.py` | `<details>`, one-line title, FILE list, quieter labels |
| `tests/test_model.py` | create — `file_locations` |
| `tests/test_place1.py` / `test_place3.py` | pin `locations` length |
| `tests/test_report.py` | `:column` and multi-line FILE |
| `tests/test_html_report.py` | details / heading / multi FILE |

---

### Task 1: Location model and `file_locations`

**Files:**
- Modify: `src/envgene_linter/model.py`
- Create: `tests/test_model.py`

**Interfaces:**
- Consumes: existing `Finding`
- Produces:
  - `@dataclass(frozen=True) class Location` with `path: Path`, `line: int`, `column: int`
  - `Finding.locations: tuple[Location, ...] = ()`
  - `Finding.file_locations(self) -> tuple[Location, ...]`: return `locations` if non-empty, else `(Location(self.path, self.line, self.column),)`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_model.py
from pathlib import Path

from envgene_linter.model import Finding, Location, Severity


def _finding(**overrides) -> Finding:
    data = dict(
        rule="PLACE-2",
        severity=Severity.WARNING,
        path=Path("a.yml"),
        line=4,
        column=3,
        key="K",
        scope="s",
        message="m",
        hint="h",
    )
    data.update(overrides)
    return Finding(**data)


def test_file_locations_falls_back_to_primary():
    finding = _finding()
    assert finding.locations == ()
    assert finding.file_locations() == (Location(Path("a.yml"), 4, 3),)


def test_file_locations_uses_explicit_tuple():
    extra = Location(Path("b.yml"), 8, 5)
    finding = _finding(locations=(extra,))
    assert finding.file_locations() == (extra,)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_model.py -v`

Expected: FAIL (`Location` or `file_locations` missing)

- [ ] **Step 3: Implement**

In `src/envgene_linter/model.py`, add `Location` just above `Finding`, and add the field + method:

```python
@dataclass(frozen=True)
class Location:
    path: Path
    line: int
    column: int


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
    locations: tuple[Location, ...] = ()

    def file_locations(self) -> tuple[Location, ...]:
        if self.locations:
            return self.locations
        return (Location(self.path, self.line, self.column),)
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_model.py tests/test_report.py tests/test_html_report.py tests/test_rulemeta.py -v`

Expected: PASS (new field has a default)

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/model.py tests/test_model.py
git commit -m "$(cat <<'EOF'
Add Finding.locations and file_locations for multi-copy paths.

EOF
)"
```

---

### Task 2: Fill locations on PLACE-1 and PLACE-3

**Files:**
- Modify: `src/envgene_linter/rules/place1.py`
- Modify: `src/envgene_linter/rules/place3.py`
- Modify: `tests/test_place1.py`
- Modify: `tests/test_place3.py`

**Interfaces:**
- Consumes: `Location`, `owned.provenance.file.path`, `owned.provenance.position`
- Produces: PLACE-1 both constructors and PLACE-3 env-agreement set `locations` to unique owner positions, first owner still primary. PLACE-2 and other PLACE-3 constructors leave `locations` default empty.

Shared helper (put in `place1.py` and a copy in `place3.py` — do not add a new module):

```python
from ..model import Finding, Location, ...

def _locations_from_owners(owners: list[tuple[str, EffectiveLeaf]]) -> tuple[Location, ...]:
    seen: set[tuple[str, int, int]] = set()
    out: list[Location] = []
    for _, owned in owners:
        line, column = owned.provenance.position
        path = owned.provenance.file.path
        marker = (str(path), line, column)
        if marker in seen:
            continue
        seen.add(marker)
        out.append(Location(path, line, column))
    return tuple(out)
```

In PLACE-3 env-agreement the group variable is `group` (same shape: `list[tuple[str, EffectiveLeaf]]`). Pass `group` into the same helper (define `_locations_from_owners` in `place3.py` too).

Both PLACE-1 `Finding(...)` calls add `locations=_locations_from_owners(owners)`.  
PLACE-3 env-agreement adds `locations=_locations_from_owners(group)`.

- [ ] **Step 1: Pin failing asserts**

In `tests/test_place1.py` `test_value_repeated_in_every_environment_should_move_to_the_cluster`, after existing asserts:

```python
    assert len(findings[0].locations) == 2
    paths = {item.path.name for item in findings[0].locations}
    assert paths == {"env-params.yml"}
    env_dirs = {item.path.parts[-4] for item in findings[0].locations}
    assert env_dirs == {"env-01", "env-02"}
```

In `test_value_repeated_in_every_cluster_should_move_to_the_repository`:

```python
    assert len(findings[0].locations) == 2
```

In `tests/test_place3.py` `test_two_envs_same_catalog_key_is_a_finding`:

```python
    assert len(findings[0].locations) == 2
```

In `tests/test_place2.py` `test_env_copying_cluster_is_a_finding` (optional but do it):

```python
    assert findings[0].locations == ()
```

- [ ] **Step 2: Run place tests — expect FAIL**

Run: `.venv/bin/python -m pytest tests/test_place1.py::test_value_repeated_in_every_environment_should_move_to_the_cluster tests/test_place3.py::test_two_envs_same_catalog_key_is_a_finding -v`

Expected: FAIL (`locations` empty)

- [ ] **Step 3: Fill `locations` in the three constructors**

- [ ] **Step 4: Run place tests**

Run: `.venv/bin/python -m pytest tests/test_place1.py tests/test_place2.py tests/test_place3.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/rules/place1.py src/envgene_linter/rules/place3.py tests/test_place1.py tests/test_place2.py tests/test_place3.py
git commit -m "$(cat <<'EOF'
Record every agreeing copy path on PLACE-1 and PLACE-3 findings.

EOF
)"
```

---

### Task 3: Console lists every location

**Files:**
- Modify: `src/envgene_linter/report.py`
- Modify: `tests/test_report.py`

**Interfaces:**
- Consumes: `Finding.file_locations()`
- Produces: each finding’s first lines are `path:line:column` (one per location), then severity, message, hint.

```python
def _location_lines(finding: Finding) -> str:
    return "\n".join(
        f"{item.path}:{item.line}:{item.column}" for item in finding.file_locations()
    )


def _block(rule: str, findings: list[Finding]) -> str:
    if not findings:
        return f"{rule}\nNo findings"
    chunks = [
        f"{_location_lines(finding)}\n{finding.severity.value}\n{finding.message}\n{finding.hint}"
        for finding in findings
    ]
    return f"{rule}\n" + "\n\n".join(chunks)
```

- [ ] **Step 1: Update `tests/test_report.py` so current cases fail**

Every existing `{path}:{line}` expected string becomes `{path}:{line}:{column}`. Findings in this file do not set `column` (default `1`) unless you add it.

`test_render_one_finding` expected first data line:

```text
environments/c/e/Inventory/parameters/p.yml:4:1
```

(was `:4`)

Add one new test:

```python
from envgene_linter.model import Location

def test_render_lists_all_locations():
    finding = Finding(
        rule="PLACE-1",
        severity=Severity.WARNING,
        path=Path("a.yml"),
        line=1,
        column=2,
        key="K",
        scope="s",
        message="ma",
        hint="ha",
        locations=(
            Location(Path("a.yml"), 1, 2),
            Location(Path("b.yml"), 8, 5),
        ),
    )
    output = render([finding])
    assert "a.yml:1:2\nb.yml:8:5\nwarning\nma\nha\n" in output
```

- [ ] **Step 2: Run `tests/test_report.py` — expect FAIL**

Run: `.venv/bin/python -m pytest tests/test_report.py -v`

Expected: FAIL (still `path:line` without column / second file)

- [ ] **Step 3: Implement `_location_lines` in `report.py`**

- [ ] **Step 4: Run report + cli tests**

Run: `.venv/bin/python -m pytest tests/test_report.py tests/test_cli.py -v`

Expected: PASS (`test_cli` checks substrings, not exact path:line)

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/report.py tests/test_report.py
git commit -m "$(cat <<'EOF'
Print every finding location with column on the console.

EOF
)"
```

---

### Task 4: HTML details, one-line title, multi-line FILE

**Files:**
- Modify: `src/envgene_linter/html_report.py`
- Modify: `tests/test_html_report.py`

**Interfaces:**
- Consumes: `Finding.file_locations()`, `RULES`, `_relative`
- Produces: `render_html` as specified below

- [ ] **Step 1: Replace / extend HTML tests**

Keep gitignore tests and `_finding`. Change the rest as follows.

```python
def test_two_place1_findings_one_rule_heading():
    a = _finding(rule="PLACE-1", path=Path("environments/a.yml"), message="ma", hint="ha")
    b = _finding(rule="PLACE-1", path=Path("environments/b.yml"), line=8, column=5, message="mb", hint="hb")
    body = render_html([a, b], Path("/repo"))
    assert body.count("<details") == 1
    assert 'open' not in body.lower().replace("opener", "")
    assert "<summary" in body
    assert "PLACE-1: Same value belongs on a higher layer" in body
    assert "PLACE-2" not in body
    assert body.count('class="finding"') == 2
    assert "FILE" in body and "ISSUE" in body
    assert "environments/a.yml:4:3" in body
    assert "environments/b.yml:8:5" in body
    assert 'class="rule-section"' in body


def test_file_lists_all_locations():
    finding = _finding(
        rule="PLACE-1",
        path=Path("environments/a.yml"),
        locations=(
            Location(Path("environments/a.yml"), 4, 3),
            Location(Path("environments/b.yml"), 8, 5),
        ),
    )
    body = render_html([finding], Path("/repo"))
    assert "environments/a.yml:4:3" in body
    assert "environments/b.yml:8:5" in body


def test_unknown_rule_has_heading_without_catalog_blurb():
    body = render_html([_finding(rule="OTHER")], Path("/repo"))
    assert "<summary" in body
    assert "OTHER" in body
    assert "OTHER:" not in body
    assert "Same value belongs on a higher layer" not in body


def test_zero_findings_says_no_findings():
    body = render_html([], Path("/repo"))
    assert "No findings" in body
    assert "<details" not in body
    assert "<h2" not in body
```

Keep `test_rule_order_place1_then_place3`, escape, no-script, chip, gitignore tests. Add `Location` to the test imports.

For `open` absence: assert `' open'` not in body and `open=` not in body (safer than `open` in body.lower()).

```python
    assert " open" not in body
    assert "open=" not in body
```

- [ ] **Step 2: Run HTML tests — expect FAIL**

Run: `.venv/bin/python -m pytest tests/test_html_report.py -v`

Expected: FAIL (no `<details>`, heading still split)

- [ ] **Step 3: Update `html_report.py`**

CSS changes (replace `h2.rule-id` / `.rule-desc` / label grid):

```css
details.rule-section {
  border: 1px solid #e2e2e2;
  border-radius: 6px;
  padding: 0.65rem 0.85rem 0.35rem;
  margin: 0 0 1rem;
}
details.rule-section + details.rule-section { margin-top: 0.85rem; }
summary.rule-id {
  font: 600 1.15rem/1.3 Georgia, "Times New Roman", serif;
  cursor: pointer;
  margin: 0 0 0.6rem;
}
.finding {
  margin: 0 0 0.85rem;
  border: 1px solid #e2e2e2;
  border-radius: 6px;
  background: #fafafa;
  overflow: hidden;
  display: grid;
  grid-template-columns: 6.5rem 1fr;
  font-size: 0.95rem;
}
.label {
  padding: 0.5rem 0.7rem;
  background: #f3f3f3;
  font-size: 0.7rem;
  font-weight: 400;
  color: #666;
  border-bottom: 1px solid #eee;
}
```

Keep the rest of the existing CSS (h1, chips, `.finding > div:nth-last-child(-n+2)`, etc.).

`_card` FILE cell:

```python
def _file_html(item: Finding, root: Path) -> str:
    lines = []
    for loc in item.file_locations():
        text = f"{_relative(loc.path, root)}:{loc.line}:{loc.column}"
        lines.append(f'<span class="file">{html.escape(text)}</span>')
    return "<br>\n".join(lines)
```

Use that as the FILE value instead of a single loc.

`render_html` rule loop:

```python
        for rule in sorted(by_rule, key=_rule_sort_key):
            meta = RULES.get(rule)
            title = f"{rule}: {meta.description}" if meta is not None else rule
            parts.append('<details class="rule-section">')
            parts.append(f'<summary class="rule-id">{html.escape(title)}</summary>')
            for item in by_rule[rule]:
                parts.extend(_card(item, root))
            parts.append("</details>")
```

Do not emit `open`.

- [ ] **Step 4: Run HTML + full suite**

Run: `.venv/bin/python -m pytest tests/test_html_report.py tests/test_cli.py -v`

Then: `.venv/bin/python -m pytest -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/envgene_linter/html_report.py tests/test_html_report.py
git commit -m "$(cat <<'EOF'
Collapse rule sections and list every copy path in FILE.

EOF
)"
```

---

### Task 5: Full suite

- [ ] **Step 1:** `.venv/bin/python -m pytest -q` — expect all pass
- [ ] **Step 2:** Commit only if you had a leftover fix
