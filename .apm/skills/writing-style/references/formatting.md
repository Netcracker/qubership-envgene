# Markdown and YAML formatting

The universal Markdown and YAML style rules every text this repository ships obeys: line length, lists,
link text, tables, and block-style YAML in examples. These are the layout rules, not document mechanics -
tables of contents, callouts, and heading numbering live in the `writing-docs` document-authoring skill.

- [Line length](#line-length)
- [Lists](#lists)
- [Link text](#link-text)
- [Tables](#tables)
- [YAML in examples](#yaml-in-examples)

## Line length

**CRITICAL: Wrap prose lines at 120 characters maximum.**

**Scope:**

- Applies to prose paragraphs and list items in any Markdown file.
- **Excluded:** tables, fenced code blocks, URLs, and image references.
- **New or rewritten content only.** When editing an existing document, wrap paragraphs you add or rewrite at 120
  chars. Do NOT reflow surrounding existing prose to match - that produces large, noisy diffs unrelated to the
  task.

**How to wrap:**

- Break at natural sentence or clause boundaries (after a period or comma, or before a conjunction).
- Indent continuation lines of list items so they align with the first non-bullet character (3 spaces for `-`
  bullets, 3 spaces for `1.` numbered lists).
- Keep an empty line before and after each paragraph (already required by the Lists rule below).

❌ **DON'T (hard wrap mid-word):**

```markdown
The Effective Set calculator emits well-known deploy parameter names for selected built-in cred
ential references.
```

✅ **DO (break at sentence or clause boundary):**

```markdown
The Effective Set calculator emits well-known deploy parameter names for selected built-in
credential references.
```

**Why:** 120 characters keeps Markdown source readable in side-by-side diffs and code reviews without horizontal
scrolling. Capping the rule to new content avoids whitespace-only churn in legacy files.

---

## Lists

**CRITICAL: All lists (bullet or numbered) MUST have empty lines before and after them.**

❌ **INCORRECT (no empty lines):**

```markdown
Template-level parameters are defined in two ways:
- Directly on the object
- Via ParameterSets
When you need environment-specific values...
```

✅ **CORRECT (with empty lines):**

```markdown
Template-level parameters are defined in two ways:

- Directly on the object
- Via ParameterSets

When you need environment-specific values...
```

**Why:** Markdown linters require empty lines around lists for proper parsing and rendering.

---

## Link text

**Link text names the destination. Do not use `click here` or `this page`.**

❌ **INCORRECT:**

```markdown
For setup steps, [click here](/docs/how-to/setup.md).
The schema reference is available [here](/schemas/credential.schema.json).
```

✅ **CORRECT:**

```markdown
For setup steps, see the [setup how-to](/docs/how-to/setup.md).
The [credential schema](/schemas/credential.schema.json) lists the required fields.
```

**Scope:** Applies to **new and modified content only**.

**Why:** Link text is read out of context by screen readers, search engines, and readers who
scan. `Click here` carries no information when extracted. A destination-naming link tells the
reader where they will land.

---

## Tables

**CRITICAL: All Markdown tables MUST have vertically aligned pipe characters (`|`).**

### ❌ Incorrect format

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|-------|----------|
| Short | Value | Data |
| Very long value here | Val | D |
```

**Problem:** Pipes are not aligned, causing Markdown linting warnings and poor readability.

### ✅ Correct format

```markdown
| Column 1             | Column 2 | Column 3 |
|----------------------|----------|----------|
| Short                | Value    | Data     |
| Very long value here | Val      | D        |
```

**Requirements:**

1. All `|` characters in header row, separator row, and data rows MUST be vertically aligned
2. Add padding spaces to ensure proper column alignment
3. Each column should have consistent width across all rows
4. Separator row (`---`) should match the width of the widest content in that column

**How to achieve alignment:**

1. **Keep cell content concise** - Long text makes alignment difficult
2. **Simplify when possible** - Remove examples from cells if they make text too long
3. **Uniform width per column** - Each cell in a column should have the same width (add trailing spaces)
4. **Don't add spaces endlessly** - If alignment fails repeatedly, the problem is content length, not spacing

### Common mistake

❌ **DON'T: Try to align long, varying content with spaces**

```markdown
| Location                                                        | Use When                                  |
|-----------------------------------------------------------------|-------------------------------------------|
| `/environments/<cluster>/<env>/Inventory/resource_profiles/`   | One environment only (e.g., prod-env-01)  |
| `/environments/<cluster>/resource_profiles/`                   | All environments in cluster (e.g., prod-*)|
| `/environments/resource_profiles/`                             | Multiple clusters (e.g., all production)  |
```

**Problem:** Different content lengths in "Use When" column → pipes will never align no matter how many spaces you add.

✅ **DO: Simplify content first, then align**

```markdown
| Location                                                     | Use When             |
|--------------------------------------------------------------|----------------------|
| `/environments/<cluster>/<env>/Inventory/resource_profiles/` | One environment only |
| `/environments/<cluster>/resource_profiles/`                 | All environments     |
| `/environments/resource_profiles/`                           | Global               |
```

**Solution:** Shortened "Use When" text → pipes naturally align because each cell in the column has the same width.

### Real example from repository

```markdown
| Location                                              | Scope                | Use When                        |
|-------------------------------------------------------|----------------------|---------------------------------|
| `/environments/<cluster>/<env>/Inventory/parameters/` | Environment-specific | One environment only            |
| `/environments/<cluster>/parameters/`                 | Cluster-wide         | All environments in cluster     |
| `/environments/parameters/`                           | Global               | Multiple clusters               |
```

### Delimiter row style

The delimiter row uses `|---|` form - no spaces between `|` and `-`. Dashes are padded to match
column width for vertical alignment.

❌ **INCORRECT:**

```markdown
| Field    | Required |
| -------- | -------- |
| `name`   | yes      |
```

✅ **CORRECT:**

```markdown
| Field    | Required |
|----------|----------|
| `name`   | yes      |
```

---

## YAML in examples

**Use block-style YAML for object examples. Never use inline flow maps or flow sequences.**

❌ **INCORRECT (inline flow map):**

```yaml
profile: {name: dev-bss-override, baseline: dev}
```

✅ **CORRECT (block style):**

```yaml
profile:
  name: dev-bss-override
  baseline: dev
```

**Scope:** Applies to **new and modified content only**.

**Why:** Block style matches how the repository writes YAML everywhere, reads top to bottom without
mentally unpacking braces, and diffs one key per line. Inline flow maps pack several keys onto one line
and obscure which key changed.
