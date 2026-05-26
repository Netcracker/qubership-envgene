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

#### Heading numbering

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

#### Declarative tone (reference docs)

**Reference documentation describes the system as it is. Do not describe transitions, before/after diffs,
or mark elements as "new".**

Feature specifications and object schemas live in the Diátaxis Reference quadrant. Implementation history
(what changed, what was added, what was deprecated) belongs in tickets, PR descriptions, and commit
messages, not in the reference docs themselves.

❌ **INCORRECT** (transitional, history-laden):

```markdown
The existing Credential is extended by introducing a new type `external`...

| Section                     | ...
| `docker_registry` (**new**) | ...

For local Credentials the **existing** macro is used, **unchanged from today**.

# AS IS Credential          # TO BE Credential
```

✅ **CORRECT** (state-only, declarative):

```markdown
A Credential of `type: external` describes...

| Section            | ...
| `docker_registry`  | ...

For local Credentials the `envgen.creds.get(...)` macro is used.

# Local Credential          # External Credential
```

**Exception:** Migration documents and changelogs are explicitly about transitions. They describe how to
move from state X to state Y and are not subject to this rule.

**Scope:** Applies to **new and modified content only**.

**Why:** Reference docs are looked up to learn what something IS. Mixed transitional content makes the spec
brittle - phrases like "new" or "AS IS" age poorly as the system evolves, and force readers to mentally
filter what is current vs what is historical.

---

#### In-repo links

**Use repo-root absolute paths for in-repo cross-references, not GitHub URLs.**

For links between Markdown files inside this repository, use paths starting from the repository
root (`/docs/...`, `/schemas/...`). Do not use absolute GitHub URLs
(`https://github.com/Netcracker/qubership-envgene/blob/main/...`), and do not use relative paths
(`../how-to/...`).

External references (links to other repositories, third-party docs, blog posts) keep their full
`https://` URL. This rule applies to in-repo cross-references only.

❌ **INCORRECT** (absolute GitHub URL pins to `main` regardless of context):

```markdown
See [Creating a cluster](https://github.com/Netcracker/qubership-envgene/blob/main/docs/how-to/create-cluster.md).
```

❌ **INCORRECT** (relative path breaks when files move):

```markdown
See [Creating a cluster](../how-to/create-cluster.md).
```

✅ **CORRECT** (repo-root absolute path):

```markdown
See [Creating a cluster](/docs/how-to/create-cluster.md).
```

**Scope:** Applies to **new and modified content only**. Existing absolute or relative links are
not affected unless the surrounding lines are being edited for other reasons.

**Why:** Repo-root absolute paths render correctly on GitHub regardless of branch or fork. GitHub
URLs pin to a specific branch (usually `main`), so a fork or feature-branch viewer following the
link is taken back to `main` instead of staying in the current context. Relative paths break when
the linking file or the target file is moved.

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

For a broader audit of all cross-links in the repository:

```bash
grep -rhoE '\]\([^)]+#[^)]+\)' --include='*.md' . | sort -u
```

**Why:** A heading rename inside one file silently breaks references in unrelated files. The
CI link-checker (lychee) catches this only after push.

---

#### Doc index updates

**Add new docs to (and remove deleted docs from) the index readmes.**

The repository has two parallel index readmes that mirror the same structure:

- `/README.md` (root project readme, "Documentation" section)
- `/docs/README.md` (docs hub readme)

When you add a tutorial, how-to, feature, or migration doc, add a link in both readmes under
the matching section. When you rename or remove a doc, update both readmes to keep links live.
Match the description style of sibling entries (short, verb-leading phrase, same capitalization
convention).

Per-directory readmes (`/docs/features/README.md`, `/docs/use-cases/README.md`, etc.) are
meta-docs that explain what kind of content the directory holds. They are not navigation
indices and do not need a per-doc entry.

**Why:** GitHub's link-checker catches dead links but does not warn when a new doc is missing
from the index. Readers discover docs through the index readmes, not by browsing directories.

---

#### Pre-flight linter checks

Before declaring documentation changes done, run the same linters that CI will run.

**Markdown structure (`markdownlint`):**

```bash
npx --yes markdownlint-cli@latest --config .github/linters/.markdown-lint.yml <changed-files>
```

The project config (`.github/linters/.markdown-lint.yml`) relaxes `MD013` line length to 1000,
and disables `MD012`, `MD033`, `MD051`. Running markdownlint without `--config` uses the
default settings (line length 80) which produces many false positives unrelated to the project
rules and may hide real issues like `MD009` (trailing spaces) or `MD040` (fenced block missing
language).

**Natural-language terminology (`textlint` with `textlint-rule-terminology`):**

CI runs textlint on prose to flag terminology preferences (for example, em dashes should be
hyphens, `repo` should be `repository`, `READMEs` should be `readmes`, `Blank line` should be
`Empty line`). The textlint config lives in the shared `netcracker/.github` repository and is
pulled in at CI time; there is no local config file to reference. To preview locally:

```bash
npx --yes textlint --rule terminology <changed-files>
```

This runs the default terminology rule set. CI may flag a few additional terms layered on top
by the shared config. Treat the CI report as authoritative.

**Why:** The CI super-linter runs both linters. Running locally gives a true preview of the CI
result, catches real issues, and avoids distraction from false positives that arise when
running linters with default (non-project) settings.

---

## Documentation content rules

These rules govern content and scope. The Markdown formatting rules above govern syntax. These rules
govern what the documentation says, across all documentation types.

### Section adds only what it uniquely contributes

A documentation section should add only the information specific to the concept it introduces.
Cross-cutting facts - schemas, notations, rules, examples of canonical types - are cross-linked to
their canonical location, not restated.

❌ **INCORRECT:**

- Re-describing the full schema of an object that already has its own section.
- Repeating notation rules in every section that uses the notation.
- Re-deriving constraints already stated in upstream sections.

✅ **CORRECT:**

- Link to the canonical definition for the concept.
- Add only the new facts unique to the current section.

**Scope:** Applies to **new and modified content only**.

**Why:** Restated information ages out of sync with the canonical copy. Readers wonder which copy is
authoritative. Lengthens reviews without adding value.

---

### Verify, don't fabricate

When a documentation statement names a specific identifier - a parameter, environment variable, file
path, library symbol - that identifier is confirmed in the source it describes. Unverifiable
identifiers are open questions, not statements of fact.

For object schemas and example fields, see also
[Object Examples in Documentation](#object-examples-in-documentation).

❌ **INCORRECT:**

- Naming a CI variable for a service by extending a pattern from a sibling service, without checking
  the implementation.
- Listing a config file path from memory without grepping the repository.
- Assuming a library exposes an env-var auth method by analogy with another component.

✅ **CORRECT:**

- Grep or read the source code to confirm the identifier before stating it.
- Mark the identifier as an open question until verifiable.

**Scope:** Applies to **new and modified content only**.

**Why:** Documentation is consumed as authoritative. A fabricated detail propagates into tickets,
validation rules, and tooling assumptions.

---

### Don't silently extend the spec

If a section would read more cleanly under a hypothetical spec extension - a wider enum, a new
notation, a relaxed constraint - do not apply the extension in the draft. File the proposed extension
as an open question and write the section against the current spec.

❌ **INCORRECT:**

- Drafting a section that implies a notation works in a wider scope than the spec currently allows.
- Adding examples that assume a constraint has been relaxed.

✅ **CORRECT:**

- Write to the current spec, accepting any awkwardness in the section.
- File the proposed extension as an open question, separately.

**Scope:** Applies to **new and modified content only**.

**Why:** Spec changes propagate to validation rules, schemas, tooling, and migration. They deserve
explicit decisions, not implicit drafting assumptions.

---

### Use existing vocabulary

If the document already defines terms, types, and notations for a domain, reuse them. Parallel
vocabulary - new section titles, column labels, role names - for concepts the document already covers
is avoided.

❌ **INCORRECT:**

- Inventing a column name that describes the same property an existing column already covers.
- Adding a structural subsection that duplicates an existing section type.
- Coining a new term when the document already names the same concept.

✅ **CORRECT:**

- Reuse the document's existing terms for the same concepts.
- If new vocabulary is genuinely needed, introduce it in a definitions section.

**Scope:** Applies to **new and modified content only**.

**Why:** Parallel vocabulary forces readers to maintain two mental glossaries and produces ambiguous
cross-references.

---

### Observable behaviour over implementation detail

Documentation works best when it foregrounds observable behaviour - what users, downstream tools, or
consuming systems can rely on. Internal mechanism - phases, ordering of components, runtime fallback
paths - is worth including when it is part of what readers depend on. Otherwise the observable outcome
often communicates more clearly.

A useful self-check: would a reasonable alternative implementation that produces the same outcome
invalidate this paragraph? If yes, the mechanism is load-bearing - keep it. If no, the observable
outcome alone may carry the message.

❌ **INCORRECT** (when mechanism is not load-bearing):

- Describing the sequence of internal components (step 1: X reads file. Step 2: Y exports value).
- Naming runtime phases that have no user-visible meaning.

✅ **CORRECT:**

- Stating the observable outcome (the value is available to downstream consumer Y).
- Documenting mechanism only when it is part of the commitment (timing, atomicity, ordering).

**Scope:** Applies to **new and modified content only**.

**Why:** Implementation choices evolve faster than the observables they deliver. Documenting mechanism
that is not load-bearing forces stale doc updates with every implementation change.

---

### Tables: one fact per row

In documentation tables, each row carries one identifier or entity. Composite cells listing multiple
alternatives separated by punctuation are split into separate rows. Column names describe properties
the document already defines, not invented labels.

❌ **INCORRECT:**

- Packing alternative values into one cell separated by "or" or commas.
- Adding a column labelled in vocabulary the document has not introduced elsewhere.
- Composite cells listing multiple identifiers when each could be its own row.

✅ **CORRECT:**

- One identifier per row.
- Column labels reuse the document's existing vocabulary.
- Alternatives appear as separate rows or in prose below the table.

**Scope:** Applies to **new and modified content only**.

**Why:** Tables in documentation are dense lookups. Composite cells and free-text columns reduce their
lookup value.

---

### Validation rule sections

**When documenting semantic validation rules in a feature spec, group them by phase, state invariants
declaratively, and factor out shared failure behaviour into a single note.**

A validation section catalogs semantic checks the system applies on top of schema validation. The pattern:

1. **Open with a note that establishes shared context** - what schema validation already covers, the
   default failure behaviour (fail vs warn), and the error-message contract. Do not repeat these in
   each rule.
2. **Group rules by phase** - each phase (a generation stage, an import operation, a runtime check)
   gets its own subsection.
3. **State invariants, not actions** - write what must be true. The reader infers the negative case.
4. **Name each rule** with a short bold noun-phrase followed by a period, then the explanation.
5. **Mark exceptions inline** - non-failure cases (warnings, deferred checks) are noted in the rule
   name itself.
6. **Cross-link, do not restate** - reference the canonical object definitions and field semantics
   rather than duplicating them.

❌ **INCORRECT:**

- Describing the validator's actions ("The validator iterates over...", "The check runs after...")
  instead of the invariant.
- Repeating "If this fails, generation stops with an error" in every rule.
- Listing field constraints already documented in the object schema.
- Mixing rules across phases in one undifferentiated list.

✅ **CORRECT:**

- "Every X of type Y has a Z field referencing a known W." (invariant form)
- A single note block at the top of the section describing the default failure behaviour and the
  error-message contract.
- Cross-link to the object definition for field semantics.
- Subsections per phase ("During X generation", "During Y import").

**Scope:** Applies to **new and modified content only**.

**Why:** Declarative invariants are easier to scan and harder to misinterpret than procedural
descriptions of validator behaviour. Phase grouping helps readers locate rules relevant to the
operation they care about. Shared failure semantics factored out reduces noise and prevents
inconsistencies between rules.

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

---

## Commits and Pull Requests

### Commit messages

Use Conventional Commits format: `<type>: <description>`. Types in use here: `feat`, `fix`,
`docs`, `chore`, `refactor`, `test`, `ci`, `perf`, `style`. The repository convention is no
scope prefix.

Subject line:

- Imperative mood (`Add X`, not `Added X` or `Adds X`).
- Under 72 characters.
- No trailing period.

Body (when needed):

- Empty line before body.
- Explain WHY the change is needed and trade-offs, not WHAT (the diff already shows what).
- Wrap at 72 characters.
- Reference issues in a footer (`Closes #123`, `Refs #456`).

### Commit type for docs-only changes

If a commit touches only documentation files (`*.md`, `AGENTS.md`, `CLAUDE.md`, files under `docs/`), use
`docs:` as the commit type. The post-merge build workflow skips Docker image rebuilds for commit types
other than `feat:`, `fix:`, and `BREAKING CHANGE`. A doc-only change marked `feat:` or `fix:` triggers
unnecessary image builds.

Tests and linters run on every PR regardless of commit type.

### Pull request description for docs-only changes

Documentation PRs omit the "Test plan" section by default. The doc-quality gates (super-linter,
textlint, link-checker, markdownlint) cover correctness. Include a Test plan section only when
explicitly requested or when the change has runtime implications beyond text.

### Commit granularity

**One logical change per commit.** A commit should be a single coherent unit that a reviewer
can read in one pass.

Split into separate commits when:

- A rule, convention, or schema is added (AGENTS.md, lint config) along with content that
  follows it - put the rule change in its own commit so the rule can be reviewed separately
  from its application.
- Mechanical changes (mass rename, formatting sweep) are mixed with semantic changes - put
  the mechanical change in its own commit so the semantic diff is readable.
- A pre-existing issue is fixed in passing - put the fix in its own commit so it can be
  backported or reverted independently.

Keep in the same commit:

- Test with the code or doc it covers.
- Migration script with the schema change that requires it.
- Anchor renames with the heading change that triggered them.

### Pull request scope

**One focused goal per PR.**

- PR description states the problem, the decision, and trade-offs.
- Target size: under 500 lines of changed prose for docs PRs, under 400 lines for code PRs.
  Larger changes belong in a stack of dependent PRs (mention the order in each description).
- Refactor PRs go separately from feature PRs. Rule additions go separately from
  rule-application PRs.
- Do not include unrelated cleanup. File a follow-up issue instead.
