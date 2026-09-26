# envgene-linter: HTML report redesign (rule groups + AI fields)

Date: 2026-09-05  
Status at design time: approved in conversation; awaiting file review\

## Reading order and later changes

As of September 26, 2026, HTML cards display FILE, ISSUE, ACTION, and FIX SUGGESTION.
The TYPE row and its chips have been removed. Internal finding types and console severity remain unchanged.
This update supersedes the TYPE display requirements below.

These three HTML specs describe successive stages on the same date: [original report](2026-09-05-html-report-design.md) → [redesign](2026-09-05-html-report-redesign-design.md) → [usability](2026-09-05-html-report-usability-design.md). Later stages replace the earlier requirements they explicitly change; the remaining requirements carry forward. Status lines record the original review state.

This is the middle stage, retained as history. The usability stage later replaces the separate rule heading/subtitle with a collapsed section, lists all locations in FILE, adds columns and multiple locations to console output, and reduces label size.

Supersedes the **page layout, card fields, and `.gitignore` policy** in [2026-09-05-html-report-design.md](2026-09-05-html-report-design.md). CLI flag, output path, write-after-console, write-failure exit 2, no-JS, and `html.escape` stay as that spec defined them.

## Goal

`envgene-linter check <repo> --html` still prints the console report, then writes `<repo>/envgene-linter-report.html`. The page is grouped **by rule**, not by file. Each card is labeled for a later AI fix pass: **FILE**, **ISSUE**, **TYPE**, **ACTION**, **FIX SUGGESTION**.

The report is local-only. On every successful `--html` write, the instance repository `.gitignore` must list `envgene-linter-report.html`.

## In plain terms

A person (or a future AI assistant) opens one HTML file. They see **Envgene Linter Report**, then one section per rule that actually fired. Under **PLACE-1** they read a short English sentence about the rule, then cards with label/value rows. A chip is a small rounded label, such as `Warning` or `Fix`. **ACTION** is a single word (`Fix` today). **FIX SUGGESTION** is what to do. The AI will look at ACTION first, then FIX SUGGESTION. This cycle does not run any fixer.

## Out of scope (this cycle)

- JSON report, autofix, an agent that applies the suggestions
- Changing the console **layout** (still rule blocks with path:line, severity, message, hint)
- `--strict`, `--rules`, baseline, `[EXCEPTION …]`
- New TYPE/ACTION values on current PLACE-* findings (fields exist; current rules emit Warning + Fix)
- Merging passport into the Effective Set
- Changing PLACE-* detection logic (only the finding **texts**, plus `column` / type / action on the model)

## CLI and file (unchanged except gitignore)

```text
envgene-linter check <repo> --html
```

Always:

```text
<instance-repo-root>/envgene-linter-report.html
```

Overwrite each run. Console on stdout first, then write HTML. Success stderr: `Wrote HTML report to envgene-linter-report.html`. Write failure: stderr + exit **2** after console has been printed.

Without `--html`: do not write the HTML file, do not edit `.gitignore`.

## Instance `.gitignore`

After a successful HTML write, ensure the instance root `.gitignore` contains a line that names the report file. The accepted unanchored entry `envgene-linter-report.html` also matches that filename in subdirectories; `/envgene-linter-report.html` is anchored to the instance root.

- If `.gitignore` does not exist, create it with one line: `envgene-linter-report.html`
- If it exists and a trimmed line is already `envgene-linter-report.html` or `/envgene-linter-report.html`, leave the file unchanged
- Otherwise append `envgene-linter-report.html` (preserve existing content and a trailing newline)

If the HTML file was written but `.gitignore` cannot be updated: one warning on stderr; exit code stays the success code of the check (do not fail the run for a gitignore problem).

Do not rewrite or reorder other gitignore entries. Do not add the report to *this* linter project's `.gitignore` as part of the feature (the file lives in the scanned instance).

## Rule catalog

The three-rule catalog and defaults below describe this stage. Later rule specs extend the catalog and `RULE_ORDER`; they do not require a new HTML layout.

New small module (suggested: `src/envgene_linter/rulemeta.py`). Not inside `html_report.py`.

Each known rule:

| Field | Meaning |
| --- | --- |
| `id` | `PLACE-1`, `PLACE-2`, `PLACE-3` |
| `description` | One English sentence for the section subtitle |
| `default_issue_type` | `Warning` / `Error` / `Information` |
| `default_action` | `Fix` today; `Review` is allowed in the enum for later rules |

HTML does not hardcode PLACE-* names for TYPE or ACTION. It prints whatever is on the finding. The catalog supplies defaults and the section subtitle.

Section subtitles (fixed copy):

| Rule | Description |
| --- | --- |
| PLACE-1 | Same value belongs on a higher layer |
| PLACE-2 | Higher layer restates a lower-layer value |
| PLACE-3 | Cloud Passport keys and files are misplaced |

Current defaults: all three rules → TYPE `Warning`, ACTION `Fix`.

A finding whose `rule` is not in the catalog: section heading is the raw ID, no subtitle. TYPE and ACTION still come from the finding.

## Finding model

Keep: `rule`, `severity`, `path`, `line`, `key`, `scope`, `message`, `hint`, `related`.

Add:

| Field | Type | Source |
| --- | --- | --- |
| `column` | `int` | Second value of existing `LoadedYaml.position` / `Provenance.position` (1-based, start of the key). Already implemented in `yamlio`; rules currently store only `position[0]`. |
| `issue_type` | enum | From the rule catalog default unless a rule overrides it |
| `action` | enum | From the rule catalog default unless a rule overrides it |

Display names (chip text, exact):

- TYPE: `Error`, `Warning`, `Information`
- ACTION: `Fix`, `Review`

`severity` stays. Current rules keep `Severity.WARNING`. Do not delete it; console still prints `warning`.

Passport-file findings that have no YAML key position keep `line=1`, `column=1`.

## ISSUE and FIX SUGGESTION (also console message / hint)

The PLACE-3 key checks and their text below are historical. [PLACE-4](2026-09-07-place4-design.md) later moves Cloud Passport contract-key checks out of PLACE-3 and supplies new messages and hints. PLACE-3 retains passport-file placement checks.

The HTML fields use `Finding.message` and `Finding.hint`, the same fields used by the console. This stage replaces their text with the shorter English strings below. Console therefore changes **text only**, not layout.

Do not put `related` on the page. Keep `related` on the model for tests / later use. Do not list sibling files or env names inside the new FIX SUGGESTION.

### PLACE-1 (environment → cluster)

- ISSUE: `Key {key} has the same value in {n} environments of cluster {cluster}.`
- FIX SUGGESTION: `Move {key} to environments/{cluster}/parameters/ and remove the environment copies.`

### PLACE-1 (cluster → repository)

- ISSUE: `Key {key} has the same value in {n} clusters.`
- FIX SUGGESTION: `Move {key} to a repository paramset and remove the cluster copies.`

### PLACE-2

- ISSUE: `Key {key} at the {layer} layer repeats the lower-layer value.`
- FIX SUGGESTION: `Remove {key} from this file, or change the value if the override is intentional.`

`{layer}` is the existing layer word (`environment`, `cluster`, …).

### PLACE-3 (passport file not at cluster)

- ISSUE: `Passport {stem} is not at the cluster layer.`
- FIX SUGGESTION: keep the current file-location hint (`_file_hint`).

### PLACE-3 (contract key at repository)

- ISSUE: `{key} is a Cloud Passport key authored at the repository layer.`
- FIX SUGGESTION: `Move {key} to a cluster-layer paramset.`

### PLACE-3 (contract key repeated in environments)

- ISSUE: `{key} is a Cloud Passport key repeated in environments of cluster {cluster}.`
- FIX SUGGESTION: `Move {key} to the cluster layer unless an environment needs a different value.`

## Page

One HTML document. Inline CSS. No JavaScript. No `<script>` tags. `lang="en"`. Escape every finding field and every path (`html.escape`).

### Header

- Visible title and `<title>`: `Envgene Linter Report`
- Title font: `Georgia, "Times New Roman", serif` (also the rule ID heading)
- Body font: system UI, light theme, no extra assets
- No per-rule counts in the header
- No “do not commit” note (gitignore handles that)

### Sections

Only rules that have at least one finding. Order: `PLACE-1`, `PLACE-2`, `PLACE-3`, then any other rule ID sorted by name.

```text
PLACE-1
Same value belongs on a higher layer

  [card]
  [card]
```

Zero findings: still write the file. Title + `No findings`. No rule sections.

### Card (table + chips)

Two-column table (label | value). Label column about `9rem`. Labels exactly:

`FILE` · `ISSUE` · `TYPE` · `ACTION` · `FIX SUGGESTION`

| Label | Value |
| --- | --- |
| FILE | `{relative/path}:{line}:{column}` (POSIX `/`, relative to instance root; if the path is outside the root, display the supplied path with POSIX separators) |
| ISSUE | `Finding.message` |
| TYPE | chip with `issue_type` display name |
| ACTION | chip with `action` display name |
| FIX SUGGESTION | `Finding.hint` |

Do not show `scope` or `related`.

Chip colors (inline CSS classes):

| Value | Fill | Border |
| --- | --- | --- |
| Warning | `#fff3cd` | `#e0c36a` |
| Error | `#fde8e8` | `#e39a9a` |
| Information | `#e8eef5` | `#b0bec5` |
| Fix | `#e8f0fe` | `#9db7e8` |
| Review | `#eeeeee` | `#bbbbbb` |

Unknown type/action: still print the text; use the Review-style gray chip.

Rounded pill (`border-radius: 999px`). Card: light gray background, 1px `#e2e2e2` border, slight radius.

## Console

`report.py` grouping and block shape stay, including empty rule blocks (`PLACE-2` then `No findings`). Path line stays `{path}:{line}` (no column). Severity line stays. New shorter message/hint apply.

## Code changes

| File                                            | Role                                              |
|-------------------------------------------------|---------------------------------------------------|
| `src/envgene_linter/model.py`                   | `column`, `issue_type`, `action` (+ small enums)  |
| `src/envgene_linter/rulemeta.py`                | Catalog: ID, description, defaults                |
| `src/envgene_linter/rules/place1.py` (and 2, 3) | `column`; catalog defaults; new texts             |
| `src/envgene_linter/html_report.py`             | Group by rule; table+chips; new title             |
| `src/envgene_linter/cli.py`                     | After HTML write, ensure instance `.gitignore`    |
| `tests/test_html_report.py`                     | New page contract                                 |
| `tests/test_cli.py`                             | gitignore create/append; no edit without `--html` |
| Rule / Finding constructors in tests            | New fields; updated message/hint assertions       |

`yamlio.position` is unchanged. Engine and Effective Set are unchanged.

## Tests

Renderer / CLI:

- Grouping is by rule: two PLACE-1 findings in different files → one PLACE-1 heading, two cards, no per-file `h2`
- A rule with zero findings does not appear
- Unknown rule ID still renders a section titled with that ID
- FILE contains `:line:column`
- Labels `FILE`, `ISSUE`, `TYPE`, `ACTION`, `FIX SUGGESTION` are present
- TYPE/ACTION appear as chips (class or the agreed colors)
- Title is `Envgene Linter Report`
- `<` in message is `&lt;`
- No `<script`
- Zero findings → `No findings`
- `--html` writes the report and ensures `.gitignore` lists it
- Existing `.gitignore` keeps prior lines and gains the report name if missing
- Already-listed report name → `.gitignore` bytes unchanged
- Without `--html`, no HTML file is created or overwritten, and `.gitignore` is untouched
- gitignore unwritable after a successful HTML write → stderr warning, not exit 2
- Unwritable HTML target → exit 2 (unchanged)

Rule text: existing PLACE-* tests that pin `message` / `hint` update to the strings above. Column: at least one test that a finding’s `column` matches `position()[1]` (the yamlio fixture that already expects `(2, 3)` is enough if a rule test threads it through).

## Algorithm / docs

No new algorithm file. The English spec is the contract for this stage, subject to the later changes linked above; the Russian copy is its reader translation.
