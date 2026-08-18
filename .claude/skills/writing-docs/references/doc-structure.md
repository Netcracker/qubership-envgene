# Document structure and voice

How to structure a document and shape its sections: the Diataxis document types, and the voice and
structure rules that keep each section carrying only what it uniquely contributes.

- [Document structure and voice](#document-structure-and-voice)
  - [Documentation structure (Diataxis framework)](#documentation-structure-diataxis-framework)
    - [Documentation types](#documentation-types)
    - [When creating documentation](#when-creating-documentation)
  - [Section voice and structure](#section-voice-and-structure)
    - [Section adds only what it uniquely contributes](#section-adds-only-what-it-uniquely-contributes)
    - [Section value audit](#section-value-audit)
    - [Don't silently extend the spec](#dont-silently-extend-the-spec)
    - [Observable behavior over implementation detail](#observable-behavior-over-implementation-detail)
    - [Avoid duplication in description](#avoid-duplication-in-description)
      - [❌ Incorrect (duplicated info)](#-incorrect-duplicated-info)
      - [✅ Correct (concise, mentioned once)](#-correct-concise-mentioned-once)
    - [Declarative tone (reference docs)](#declarative-tone-reference-docs)
    - [Tables: one fact per row](#tables-one-fact-per-row)
    - [Validation rule sections](#validation-rule-sections)
  - [Doc index updates](#doc-index-updates)

## Documentation structure (Diataxis framework)

This repository follows the [Diataxis documentation framework](https://github.com/evildmp/diataxis-documentation-framework).

### Documentation types

1. **How-to Guides** (`/docs/how-to/`)
   - Goal-oriented, practical steps
   - Solve specific problems
   - Minimal theory, maximum action
   - Target: ~200-400 lines

2. **Explanation** (`/docs/features/`)
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

### When creating documentation

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

## Section voice and structure

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

### Section value audit

**During refactors and final reviews, ask of each section: what unique fact does it carry? If most content
is restated from elsewhere, drop or trim.**

Checklist for each section:

1. Name the load-bearing fact (unique observable, rule, or definition).
2. Check where else it is said (catalog, table, sibling sections, parent section).
3. If the unique fact is small (one sentence), fold into a neighboring section.
4. If everything is derivable from elsewhere, drop the section. Cross-link from the catalog if an explicit
   pointer is needed.

❌ **INCORRECT** (section earns no keep):

A subsection that rehashes the catalog table and restates a dispatching rule already implied by sibling
sections covering each context.

✅ **CORRECT** (drop the section):

The dispatching rule is derivable from sibling sections. Drop the subsection. Cross-link from the catalog
table only if an explicit pointer is needed.

**Scope:** Applies to **new and modified content only**.

**Why:** Sections without unique content fragment the doc and add maintenance burden. Restated content drifts
from its canonical source. Apply this audit during refactors, not only when first writing a section, because
content accumulates restated facts as the doc evolves.

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

### Observable behavior over implementation detail

Documentation works best when it foregrounds observable behavior - what users, downstream tools, or
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

### Avoid duplication in description

**Don't repeat the same information multiple times in the Description section.**

#### ❌ Incorrect (duplicated info)

```markdown
## Description

Parameters are defined two ways:
- Inline
- Via ParameterSets

Template-level parameters are defined two ways:  <!-- DUPLICATE -->
- Inline
- Via ParameterSets
```

#### ✅ Correct (concise, mentioned once)

```markdown
## Description

This guide shows how to override template-level parameters.

Template-level parameters are defined in two ways:
- Inline
- Via ParameterSets

[Rest of description...]
```

---

### Declarative tone (reference docs)

**Reference documentation describes the system as it is. Do not describe transitions, before/after diffs,
or mark elements as "new".**

Feature specifications and object schemas live in the Diataxis Reference quadrant. Implementation history
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

### Tables: one fact per row

In documentation tables, each row carries one identifier or entity. Composite cells listing multiple
alternatives separated by punctuation are split into separate rows. Column names describe properties
the document already defines, not invented labels.

❌ **INCORRECT:**

- Packing alternative values into one cell separated by "or" or commas.
- Adding a column labeled in vocabulary the document has not introduced elsewhere.
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
declaratively, and factor out shared failure behavior into a single note.**

A validation section catalogs semantic checks the system applies on top of schema validation. The pattern:

1. **Open with a note that establishes shared context** - what schema validation already covers, the
   default failure behavior (fail vs warn), and the error-message contract. Do not repeat these in
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
- A single note block at the top of the section describing the default failure behavior and the
  error-message contract.
- Cross-link to the object definition for field semantics.
- Subsections per phase ("During X generation", "During Y import").

**Scope:** Applies to **new and modified content only**.

**Why:** Declarative invariants are easier to scan and harder to misinterpret than procedural
descriptions of validator behavior. Phase grouping helps readers locate rules relevant to the
operation they care about. Shared failure semantics factored out reduces noise and prevents
inconsistencies between rules.

---

## Doc index updates

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
