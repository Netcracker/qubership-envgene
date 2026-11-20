# Markdown document mechanics

Document-level Markdown rules: tables of contents, callouts, heading numbering, heading renames and
cross-links, and documentation file naming. The universal layout rules every text obeys - line length,
lists, link text, tables, and block-style YAML - live in the `writing-style` skill
(`references/formatting.md`).

- [Table of contents](#table-of-contents)
- [Callouts (notes, warnings, tips)](#callouts-notes-warnings-tips)
- [Heading numbering](#heading-numbering)
- [Heading renames and cross-links](#heading-renames-and-cross-links)
- [Documentation file naming](#documentation-file-naming)

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
