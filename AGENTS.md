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

**Why:** Native callouts render with icons and colour highlighting on GitHub and other renderers; bold-text variants are plain blockquotes.

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

---

## Object Examples in Documentation

### Source of Truth for Object Schemas

**CRITICAL: Never invent object structures. Always derive examples from authoritative sources.**

The two authoritative sources are:

- **`docs/envgene-objects.md`** - human-readable descriptions, field explanations, and canonical examples for all EnvGene objects
- **`schemas/`** - JSON Schema files that define required fields, allowed values, and types

#### Rules

1. **Before writing any YAML/JSON example** for an EnvGene object, read the corresponding entry in `docs/envgene-objects.md` AND the matching schema file under `schemas/`.
2. **Validate every example against the schema**: all fields marked `"required"` in the schema must be present; no fields may be included that do not exist in the schema (unless `additionalProperties: true`).
3. **Do not guess**: if an object is not described in `docs/envgene-objects.md` and has no schema file, write explicitly:

   > No schema or description found for this object in `docs/envgene-objects.md` or `schemas/`. Cannot provide a validated example.

4. **Do not add fictional fields** such as `type:` or `applications:` to objects that have no such fields in their schema.
5. **Use real field names**: cross-check field names and allowed enum values against the schema. Do not invent field names based on intuition.

#### How much of the object to show

In tutorials and how-to guides, show only the **relevant part** of the object, not the full structure. Use `# ...` comments to signal omitted fields so the reader knows the snippet is intentionally incomplete.

- **Reference docs** → show the full object.
- **Tutorials / how-to guides** → show only the fields being explained; collapse the rest with `# ...`.

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
