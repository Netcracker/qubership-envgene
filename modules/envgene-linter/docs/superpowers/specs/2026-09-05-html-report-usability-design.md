# envgene-linter: HTML report usability (heading, collapse, all files)

Date: 2026-09-05  
Status at design time: approved in conversation; awaiting file review\

## Reading order and later changes

These three HTML specs describe successive stages on the same date: [original report](2026-09-05-html-report-design.md) → [redesign](2026-09-05-html-report-redesign-design.md) → [usability](2026-09-05-html-report-usability-design.md). Later stages replace the earlier requirements they explicitly change; the remaining requirements carry forward. Status lines record the original review state.

This is the last of the three HTML stages. It replaces the redesign requirements for headings, section expansion, label size, and location display. Later rule specs extend the catalog and `RULE_ORDER`. The PLACE-3 key checks below are historical: [PLACE-4](2026-09-07-place4-design.md) later replaces them with contract-key checks in ParameterSets; PLACE-3 retains passport-file placement checks.

Follow-up to [2026-09-05-html-report-redesign-design.md](2026-09-05-html-report-redesign-design.md). Card fields, chips, `--html`, gitignore, and no-JS stay. This cycle changes how a rule section looks and how every copy of a key is listed.

## Goal

The HTML (and console) must list **every file** that participates in a multi-copy finding. A rule section is one closed `<details>` block titled `PLACE-1: Same value belongs on a higher layer`. Labels stay small so FILE/ISSUE values are what you read.

## In plain terms

PLACE-1 says the key is the same in three environments. FILE must show three `path:line:column` lines, not one representative. Click the rule title to open the cards. No JavaScript: `<details>` / `<summary>`.

## Out of scope

- JavaScript accordion
- Changing which cases trigger PLACE-* findings
- Autofix / JSON
- Rewriting ISSUE / FIX SUGGESTION sentences again
- Algorithm doc refresh

## `Finding.locations`

New field: `locations: tuple[Location, ...] = ()`.

```python
@dataclass(frozen=True)
class Location:
    path: Path
    line: int
    column: int
```

A location identifies a source file and a key position; line and column numbers start at 1. The primary location is stored in `Finding.path`, `Finding.line`, and `Finding.column`. Empty `locations` means “show only that primary location”, not “show no files”.

Rules fill `locations` from the source files that supplied the matching values (the owners). Preserve the owner order supplied by the rule; remove duplicate `(path, line, column)` entries while retaining their first occurrence. Renderers do not sort these locations again. In the table, “matching” means having the same value in the comparison that produced this finding.

| Rule | Case | Fill |
| --- | --- | --- |
| PLACE-1 | env → cluster | source file and `position()` for each environment with the matching value |
| PLACE-1 | cluster → repository | source file and `position()` for each cluster with the matching value |
| PLACE-3 | contract key repeated in envs | source position for every environment in the matching group (historical PLACE-3 case) |
| PLACE-2 | restatement | leave empty |
| PLACE-3 | misplaced passport / repo-layer key | leave empty |

`related` is unchanged and still not shown on the page.

Primary `path` / `line` / `column` keep the first owner’s source position. They must also appear in `locations` when that tuple is non-empty.

## FILE and console

Shared location selection for HTML and console (`Finding.file_locations()`): if `locations` is non-empty, use those; else one `Location` from the primary fields.

**HTML FILE value:** one monospace line per location: `{relative/path}:{line}:{column}`.

For example, two matching copies produce one finding card whose FILE value contains:

```text
environments/cluster-01/env-a/Inventory/parameters/app.yml:4:3
environments/cluster-01/env-b/Inventory/parameters/app.yml:7:3
```

The ISSUE, TYPE, ACTION, and FIX SUGGESTION rows appear once for that finding.

**Console:** replace the single `{path}:{line}` line with one `{path}:{line}:{column}` line per location. Then `severity`, `message`, `hint` as now. This also adds a column to single-location findings, even without `--html`. Empty rule blocks unchanged (`PLACE-2\nNo findings`).

## Page

### Rule heading

One summary line, exact shape:

```text
PLACE-1: Same value belongs on a higher layer
```

`{id}: {description}` when the rule is in the catalog. Unknown rule: summary is just the id (no colon, no blurb).

Georgia, same visual weight as today’s `h2.rule-id`.

### Collapse

Each rule that has findings is a `<details>` **without** `open` (closed until click). `<summary>` is the heading line. Cards go inside `<details>`.

No JS. No `<script>`.

Around the `<details>`: a thin 1px `#e2e2e2` border, slight radius, a little padding, so an open section is one boxed group and does not bleed into the next rule.

Zero findings: title + `No findings`. No `<details>`.

### Labels

`FILE`, `ISSUE`, `TYPE`, `ACTION`, `FIX SUGGESTION` stay the same words. Smaller and quieter than values: about `0.7rem`, normal (not bold) weight, muted color (`#666`). Label column about `6.5rem`. Values unchanged (chips, message, hint).

## Tests

- PLACE-1 with two env copies: `len(locations) == 2`; HTML FILE contains both relative paths and both `:line:column`; console contains both `path:line:column`
- PLACE-2: `locations == ()`; FILE is the single primary
- Heading is `PLACE-1: Same value belongs on a higher layer` in one element (summary)
- Rendered HTML contains `<details>` and `<summary>`, no `open` attribute on those details
- A rule section wrapper/border class exists (assert class or `details` styling hook)
- Labels still present; no need to assert CSS pixels
- Existing escape / no-script / gitignore tests stay

## Code changes

| File | Role |
| --- | --- |
| `src/envgene_linter/model.py` | `Location`, `Finding.locations` |
| `src/envgene_linter/rules/place1.py` | fill `locations` |
| `src/envgene_linter/rules/place3.py` | fill `locations` for matching environment values only (historical case) |
| `src/envgene_linter/html_report.py` | `<details>`, one-line title, FILE list, quieter labels |
| `src/envgene_linter/report.py` | print all location lines |
| tests | `test_html_report.py`, `test_report.py`, place1/place3 assertions for finding fields |

## Algorithm / docs

No new algorithm file. The English spec is the contract for this stage, subject to the later changes linked above.
