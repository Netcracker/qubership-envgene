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

1. **Keep cell content concise** — Long text makes alignment difficult
2. **Simplify when possible** — Remove examples from cells if they make text too long
3. **Uniform width per column** — Each cell in a column should have the same width (add trailing spaces)
4. **Don't add spaces endlessly** — If alignment fails repeatedly, the problem is content length, not spacing

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

---

## Documentation Structure (Diátaxis Framework)

This repository follows the [Diátaxis documentation framework](https://diataxis.fr/).

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
