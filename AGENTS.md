# AI Agent Rules for qubership-envgene Repository

This document contains guidelines and rules for AI coding assistants working with this repository.

## Documentation Standards

### Markdown Formatting Rules

#### Lists

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

#### Table of Contents

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

#### Dashes

**CRITICAL: Always use a regular hyphen-minus (`-`) as a dash in prose. Never use em dashes (`—`) or en dashes (`–`).**

❌ **INCORRECT:**

```markdown
EnvGene searches these locations — from bottom to top — and uses the first match.
```

✅ **CORRECT:**

```markdown
EnvGene searches these locations - from bottom to top - and uses the first match.
```

**Why:** Em dashes are a typographic convention that varies by locale and style guide. A plain hyphen-minus is universally readable, renders consistently across all Markdown renderers, and avoids accidental character encoding issues.

#### Semicolons in prose

**Guideline:** Semicolons (`;`) are **not** forbidden, but avoid dense "clause; clause" chains in documentation when separate sentences or lists would read more clearly.

**Prefer:**

- One main idea per sentence, separated by a period.
- Bullet or numbered lists for parallel steps, outcomes, or options.
- A comma plus a coordinating conjunction (`and`, `or`) when the second part is short.

**When a semicolon is still appropriate:**

- **Complex list items** where each item already contains commas (the usual US-style role of `;` inside lists).
- **Literal syntax** in code, paths, or URIs where `;` is required - leave unchanged.
- **Rare compact one-line definitions** where brevity is more important than flow - use sparingly.

**Avoid:**

- Joining two independent statements in prose only to keep one long line - split into two sentences instead.
- Using `;` between fragments inside bullets as a substitute for a period or a new bullet.

❌ **HARDER TO READ:**

```markdown
Item 1 is generated automatically; item 2 is created manually by the user.
```

✅ **CLEARER:**

```markdown
Item 1 is generated automatically. Item 2 is created manually by the user.
```

**Why:** Semicolons are easy to overuse in technical English. Dense use can make specs feel monotonous and is often harder for readers whose first language is not English. Periods and lists align with the rest of these documentation rules.

---

#### Line length

**CRITICAL: Wrap prose lines at 120 characters maximum.**

**Scope:**

- Applies to prose paragraphs and list items in any Markdown file.
- **Excluded:** tables, fenced code blocks, URLs, and image references.
- **New or rewritten content only.** When editing an existing document, wrap paragraphs you add or rewrite at 120
  chars. Do NOT reflow surrounding existing prose to match - that produces large, noisy diffs unrelated to the
  task.

**How to wrap:**

- Break at natural sentence or clause boundaries (after a period or comma, or before a conjunction).
- Indent continuation lines of list items so they align with the first non-bullet character (3 spaces for `- `
  bullets, 3 spaces for `1. ` numbered lists).
- Keep a blank line before and after each paragraph (already required by the Lists rule above).

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

#### Semicolons

**Avoid semicolons in prose. Split into separate sentences instead.**

❌ **AVOID:**

```markdown
Native callouts render with icons; bold-text variants are plain blockquotes.
```

✅ **PREFER:**

```markdown
Native callouts render with icons. Bold-text variants are plain blockquotes.
```

**Scope:** Applies to **new and modified content only**. Existing content using semicolons is
not affected by this rule and does not need rewriting unless the surrounding lines are being
edited for other reasons.

**Why:** Two short sentences read more naturally on screen than one compound sentence linked by
a semicolon. Also reduces AI-stylized rhythm in generated text.

---

#### Callouts (Notes, Warnings, Tips)

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

**Why:** Native callouts render with icons and colour highlighting on GitHub and other renderers.
Bold-text variants are plain blockquotes.

---

#### Line Length

**Prose lines wrap at 120 characters.**

Excluded from this limit:

- Table rows (lines starting with `|`)
- Code blocks (fenced)
- URLs and other continuous tokens longer than 120 characters

**Scope:** Applies to **new and modified content only**. Existing content that exceeds 120 characters
is not affected by this rule and does not need reformatting unless the surrounding lines are being
edited for other reasons.

**Why:** Long prose lines complicate diff review and side-by-side comparison. 120 leaves room for
meaningful wrap without forcing tight columns.

---

#### Heading case

**Use sentence case for all headings: capitalize the first word and proper nouns only.**

Proper nouns include product names, feature names, brand names, and code identifiers
(`envgeneNullValue`, `ParameterSet`, `Cloud Passport`, `EnvGene`).

❌ **INCORRECT:**

```markdown
## How to Resolve Credentials
### Verification Step (Required)
#### Generated `credentials.yml` (Username/Password)
```

✅ **CORRECT:**

```markdown
## How to resolve credentials
### Verification step (required)
#### Generated `credentials.yml` (username/password)
```

**Scope:** Applies to **new and modified content only**. Existing headings in Title Case are not
affected by this rule and do not need rewriting unless the surrounding lines are being edited
for other reasons.

**Recommended (not required):** When editing a Markdown file for any other reason, consider
bringing its remaining Title Case headings to sentence case in the same PR. For large files
(many headings, large TOC), a separate dedicated migration PR is preferred to keep the original
change reviewable. Reviewers may suggest opportunistic migration but must not block merge over it.

**Why:** Aligns with the GitHub Docs convention and modern dev-doc style guides (Google,
Microsoft, Mozilla, GitHub). Sentence case has fewer rules (no debate about which prepositions
or conjunctions to capitalize), keeps proper nouns visually distinct from generic words,
translates more cleanly to non-English locales, and is the established convention across modern
technical documentation.

---

#### Tables

**CRITICAL: All Markdown tables MUST have vertically aligned pipe characters (`|`).**

##### ❌ INCORRECT Format

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|-------|----------|
| Short | Value | Data |
| Very long value here | Val | D |
```

**Problem:** Pipes are not aligned, causing Markdown linting warnings and poor readability.

##### ✅ CORRECT Format

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

##### Common Mistake

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

##### Real Example from Repository

```markdown
| Location                                              | Scope                | Use When                        |
|-------------------------------------------------------|----------------------|---------------------------------|
| `/environments/<cluster>/<env>/Inventory/parameters/` | Environment-specific | One environment only            |
| `/environments/<cluster>/parameters/`                 | Cluster-wide         | All environments in cluster     |
| `/environments/parameters/`                           | Global               | Multiple clusters               |
```

##### Delimiter Row Style

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

#### Avoid AI-Stylistics

**Documentation is written for humans, not stylized like AI output.**

Common AI-stylistics to avoid:

- Em dashes (`—`) and en dashes (`–`). See [Dashes](#dashes).
- Semicolons. See [Semicolons](#semicolons).
- Filler intensifiers: `simply`, `just`, `easily`, `truly`, `incredibly`, `seamlessly`,
  `robust`, `comprehensive`, `cutting-edge`, `leverage`, `delve`, `tapestry`, `landscape`.
- Throat-clearing openings: `It's worth noting that...`, `It's important to remember...`,
  `Let's explore...`, `In this section, we'll discuss...`.
- `Not only X, but also Y` and `Not just X, but Y` patterns.
- Empty closings: `In conclusion`, `To summarize`, `As we've seen`.

**Scope:** Applies to **new and modified content only**.

**Why:** AI-generated text leans on these patterns heavily. Their absence makes documentation
feel more direct and trustworthy. Read sentences aloud. If it sounds like a press release or a
chatbot, rewrite.

---

#### Heading renames and cross-links

When renaming a Markdown heading, the GitHub-generated anchor (`#section-name`) also changes.
Cross-links in other files that point to the old anchor become broken (CI link-checker fails).

**Before pushing after a heading rename:**

1. Grep the repository for references to the OLD anchor:

   ```bash
   grep -rnE "#old-anchor-name" --include='*.md' .
   ```

2. Update each matching cross-link to the NEW anchor in all affected files.

3. Update the link text in `[text](#anchor)` to match the new heading text where appropriate.

For a broader audit of all cross-links in the repo:

```bash
grep -rhoE '\]\([^)]+#[^)]+\)' --include='*.md' . | sort -u
```

**Why:** A heading rename inside one file silently breaks references in unrelated files. The
CI link-checker (lychee) catches this only after push.

---

#### Pre-flight markdownlint check

Before declaring documentation changes done, run markdownlint with the project's config:

```bash
npx --yes markdownlint-cli@latest --config .github/linters/.markdown-lint.yml <changed-files>
```

The project config (`.github/linters/.markdown-lint.yml`) relaxes `MD013` line length to 1000,
and disables `MD012`, `MD033`, `MD051`. Running markdownlint without `--config` uses the
default settings (line length 80) which produces many false positives unrelated to the project
rules and may hide real issues like `MD009` (trailing spaces) or `MD040` (fenced block missing
language).

**Why:** The CI super-linter runs markdownlint with the project config. Running locally with
the same config gives a true preview of the CI result, catches real issues, and avoids
distraction from false positives.

---

## Object Examples in Documentation

### Source of Truth for Object Schemas

**CRITICAL: Never invent object structures. Always derive examples from authoritative sources.**

The two authoritative sources are:

- **`docs/envgene-objects.md`** - human-readable descriptions, field explanations, and canonical examples for all EnvGene objects
- **`schemas/`** - JSON Schema files that define required fields, allowed values, and types

#### Rules

1. **Before writing any YAML/JSON example** for an EnvGene object, read the corresponding entry in `docs/envgene-objects.md` AND the matching schema file under `schemas/`.
2. **Validate every example against the schema**: all fields marked `"required"` in the schema
   must be present. No fields may be included that do not exist in the schema (unless
   `additionalProperties: true`).
3. **Do not guess**: if an object is not described in `docs/envgene-objects.md` and has no schema file, write explicitly:

   > No schema or description found for this object in `docs/envgene-objects.md` or `schemas/`. Cannot provide a validated example.

4. **Do not add fictional fields** such as `type:` or `applications:` to objects that have no such fields in their schema.
5. **Use real field names**: cross-check field names and allowed enum values against the schema. Do not invent field names based on intuition.

#### How much of the object to show

In tutorials and how-to guides, show only the **relevant part** of the object, not the full structure. Use `# ...` comments to signal omitted fields so the reader knows the snippet is intentionally incomplete.

- **Reference docs** → show the full object.
- **Tutorials / how-to guides** → show only the fields being explained. Collapse the rest with `# ...`.

This keeps examples focused on the concept being taught and avoids becoming outdated when unrelated fields change.

#### ❌ INCORRECT - invented fields and unnecessary noise

```yaml
# Namespace template - WRONG: invented fields, full object shown in tutorial context
name: "{{ current_env.name }}-bss"
type: namespace          # does not exist in namespace.schema.json
applications:            # does not exist in namespace.schema.json
  - name: "Cloud-BSS"
credentialsId: ""
isServerSideMerge: false
cleanInstallApprovalRequired: false
mergeDeployParametersAndE2EParameters: false
deployParameterSets:
  - "bss"
```

#### ✅ CORRECT - focused snippet, validated field names, omissions annotated

```yaml
# Namespace template - only the relevant section is shown
---
name: "{{ current_env.environmentName }}-bss"
# ... other required fields (see schemas/namespace.schema.json) ...
profile:
  name: dev-bss-override
  baseline: dev
# ... deployParameterSets, e2eParameters, etc. ...
```

---

## Documentation Structure (Diátaxis Framework)

This repository follows the [Diátaxis documentation framework](https://github.com/evildmp/diataxis-documentation-framework).

### Documentation Types

1. **How-to Guides** (`/docs/how-to/`)
   - Goal-oriented, practical steps
   - Solve specific problems
   - Minimal theory, maximum action
   - Target: ~200-400 lines

2. **Explanation** (`/docs/explanation/`)
   - Conceptual understanding
   - "Why" questions
   - Background and context
   - Design decisions and trade-offs

3. **Reference** (`/docs/`)
   - Technical specifications
   - Object schemas
   - API documentation
   - Factual, precise

4. **Tutorials** (`/docs/tutorials/`)
   - Learning-oriented
   - Step-by-step for beginners
   - Complete working example

### When Creating Documentation

**✅ DO:**

- Keep how-to guides focused and practical
- Separate theory into explanation documents
- Link between documentation types
- Use clear, descriptive titles
- Include realistic examples from the codebase

**❌ DON'T:**

- Mix how-to and explanation in one document
- Create long (>500 lines) how-to guides
- Include detailed theory in practical guides
- Use fantasy/made-up examples

---

## Use case design

Use cases live in `/docs/use-cases/`. They describe observable system behavior in a structured
format (Pre-requisites, Trigger, Steps, Results) and serve both as documentation and as
test-design input.

### Apply equivalence class partitioning

**Do not enumerate variants of an identical-behavior UC. Merge them into a single parameterized
UC.**

When two or more candidate UCs would describe the same observable behavior with only a parameter
difference (e.g., job name, trigger flag, environment kind), they belong to the same equivalence
class. They must be merged into a single UC with the variable parameterized via the Trigger
section.

❌ **INCORRECT (enumerated variants):**

```markdown
### UC-X-1: Validation fails at `generate_effective_set`
...

### UC-X-2: Validation fails at `cmdb_import`
...
```

Two UCs that differ only in job name. Both invoke the same validator and produce the same error
message format. This is one equivalence class, not two.

✅ **CORRECT (parameterized trigger):**

```markdown
### UC-X-1: Validation fails

**Trigger:**

> [!NOTE]
> One of the following conditions must be met:

1. Instance pipeline is started with `GENERATE_EFFECTIVE_SET: true`
2. Instance pipeline is started with `CMDB_IMPORT: true`
```

### When to split UCs

Split into separate UCs only when behavior differs in an observable way:

- Different validators or handlers (e.g., parameter validator vs credential validator).
- Different error message format or different output structure.
- Different post-conditions or side effects.

### When to merge UCs

Merge into a single parameterized UC when:

- Same observable behavior.
- Same error message format.
- Same outcome.
- Differences are limited to parameter values (job name, flag values, environment names).

### Abstract steps over implementation mechanics

Steps describe what happens, not how it is implemented. Avoid `Reads X`, `Iterates Y`,
`Detects Z` phrasing - it leaks implementation that the documentation cannot guarantee will
match.

❌ **INCORRECT:**

```markdown
**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
    1. Reads the existing Cloud and Namespace YAMLs from the Environment Instance.
    2. Iterates over `deployParameters`, `e2eParameters`, and ...
    3. Detects a value equal to `envgeneNullValue`.
    4. Aborts with a validation error.
```

✅ **CORRECT:**

```markdown
**Steps:**

1. The `generate_effective_set` job runs.
2. Parameter validation detects an unresolved `envgeneNullValue`.
3. The job aborts with a validation error.
```

### Results: observable outcomes only

Document what the operator observes, not downstream consequences that the documented component
does not control.

❌ **INCORRECT:**

```markdown
**Results:**

1. The job fails with the message: ...
2. No Effective Set is produced.
3. Deployment is blocked.
```

`Deployment is blocked` assumes authority over deployment that the documented component does
not have.

✅ **CORRECT:**

```markdown
**Results:**

1. The job fails with the message: ...
```

### Scope

Applies to **new and modified UCs only**. Existing UCs that violate these rules are not
affected and do not need rewriting unless the surrounding lines are being edited for other
reasons.

### Why

- **Equivalence Class Partitioning** is the standard test-design technique (ISTQB) and aligns
  with BDD Scenario Outlines and modern API documentation style (Stripe, GitHub, Google API
  Design Guide).
- Matrix decomposition (UC per combination of variables) creates combinatorial bloat where
  most UCs are clones differing in one word.
- Implementation-detail leaks bind documentation to a specific code shape. Abstraction
  decouples docs from implementation churn.

---

## EnvGene-Specific Documentation Rules

### Avoid Duplication in Description

**Don't repeat the same information multiple times in the Description section.**

#### ❌ INCORRECT (duplicated info)

```markdown
## Description

Parameters are defined two ways:
- Inline
- Via ParameterSets

Template-level parameters are defined two ways:  <!-- DUPLICATE -->
- Inline
- Via ParameterSets
```

#### ✅ CORRECT (concise, mentioned once)

```markdown
## Description

This guide shows how to override template-level parameters.

Template-level parameters are defined in two ways:
- Inline
- Via ParameterSets

[Rest of description...]
```

---

## Code Style

### YAML

- Use 2-space indentation
- Quote string values consistently
- Add comments for complex logic
- Use meaningful key names

### Documentation File Naming

- Use kebab-case: `override-template-parameters.md`
- Be descriptive: `billing-prod-deploy.yml` not `override.yml`

---

## Testing Documentation Changes

Before committing documentation:

1. Check Markdown syntax
2. Verify all links work
3. Ensure tables are aligned
4. Review for clarity and accuracy
