# Markdown formatting

Formatting rules for Markdown source: lists, tables of contents, line length, callouts, heading
numbering, tables, link text, and file naming.

- [Lists](#lists)
- [Table of contents](#table-of-contents)
- [Line length](#line-length)
- [Callouts (notes, warnings, tips)](#callouts-notes-warnings-tips)
- [Heading numbering](#heading-numbering)
- [Tables](#tables)
- [Link text](#link-text)
- [Heading renames and cross-links](#heading-renames-and-cross-links)
- [Documentation file naming](#documentation-file-naming)

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

## Table of contents

**CRITICAL: Documents with 10+ headings MUST include a Table of Contents after the main title.**

**When to add ToC:**

- Documents with **3 or more headings** (`#`, `##`, `###`, etc.)
- Place ToC immediately after the main document title (H1)
- ToC is a plain list WITHOUT a heading (no `## Table of Contents`)
- Description/overview section comes AFTER the ToC

**Format:**

```markdown
# Document Title

- [Section 1](#section-1)
  - [Subsection 1.1](#subsection-11)
  - [Subsection 1.2](#subsection-12)
- [Section 2](#section-2)
  - [Subsection 2.1](#subsection-21)

## Description

Brief description or overview...

## Section 1

Content...
```

**Examples from repository:**

✅ `docs/how-to/credential-encryption.md` (17 headings, has ToC)
✅ `docs/features/env-inventory-generation.md` (many headings, has ToC)

**Link format:**

- Use GitHub-style anchor links: `#section-name`
- Convert to lowercase, replace spaces with hyphens
- Remove special characters
- Example: `### Step 1: Install Tools` → `#step-1-install-tools`

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
- Keep an empty line before and after each paragraph (already required by the Lists rule above).

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

## Callouts (notes, warnings, tips)

**CRITICAL: Always use GitHub-flavored Markdown native callout syntax, not bold-text workarounds.**

Available types: `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`.

❌ **INCORRECT:**

```markdown
> **Note:** EnvGene also supports dot-notation keys.

> **Warning:** This will overwrite existing values.
```

✅ **CORRECT:**

```markdown
> [!NOTE]
> EnvGene also supports dot-notation keys.

> [!WARNING]
> This will overwrite existing values.

> [!TIP]
> Use cluster-wide scope to avoid repetition across environments.

> [!IMPORTANT]
> The `name` field must exactly match the filename without the extension.

> [!CAUTION]
> Setting `mergeEnvSpecificResourceProfiles: false` replaces the template override entirely.
```

**Why:** Native callouts render with icons and color highlighting on GitHub and other renderers.
Bold-text variants are plain blockquotes.

---

## Heading numbering

**Do not number headings unless they enumerate alternative workflows.**

Visual hierarchy (`#` → `##` → `###`) and the document's table of contents already convey
structure. Adding numeric prefixes (`## 1. Overview`, `### 2.1 Step one`) duplicates that
information and creates fragile cross-references that break when sections are added or
reordered.

❌ **INCORRECT** (sequential topics in a feature document):

```markdown
## 1. Passport file
## 2. Resolution
## 3. Merge into cloud.yml
## 4. Parameter traceability
```

✅ **CORRECT** (same content, no numbering):

```markdown
## Passport file
## Resolution
## Merge into cloud.yml
## Parameter traceability
```

✅ **ACCEPTABLE** (alternative workflows, where numbering enumerates choices):

```markdown
## 1. Creating a cluster without a Cloud Passport
## 2. Creating a cluster with a manually assembled Cloud Passport
## 3. Creating a cluster using Cloud Passport Discovery
```

**Scope:** Applies to **new and modified content only**. Existing numbered headings are not
affected by this rule unless the surrounding lines are being edited for other reasons.

**Why:** Numbered headings duplicate the structure already shown by heading level and the TOC.
They make in-text references (`see section 3.2`) fragile under reorganization, and they are not
the convention in this repository (only 2 of ~36 docs use numbering, and only for enumerated
alternative workflows). Modern dev-doc style guides (Google, Microsoft, Mozilla, GitHub Docs)
do not number headings in user-facing documentation.

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

## Heading renames and cross-links

When renaming a Markdown heading, the GitHub-generated anchor (`#section-name`) also changes.
Cross-links in other files that point to the old anchor become broken (CI link-checker fails).

**Before pushing after a heading rename:**

1. Grep the repository for references to the OLD anchor:

   ```bash
   grep -rnE "#old-anchor-name" --include='*.md' .
   ```

2. Update each matching cross-link to the NEW anchor in all affected files.

3. Update the link text in `[text](#anchor)` to match the new heading text where appropriate.

For a broader audit of all cross-links in the repository:

```bash
grep -rhoE '\]\([^)]+#[^)]+\)' --include='*.md' . | sort -u
```

**Why:** A heading rename inside one file silently breaks references in unrelated files. The
CI link-checker (lychee) catches this only after push.

---

## Documentation file naming

- Use kebab-case: `override-template-parameters.md`
- Be descriptive: `billing-prod-deploy.yml` not `override.yml`
