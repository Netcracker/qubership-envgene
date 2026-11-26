# Document structure and voice

How to structure a document and shape its sections: the Diataxis document types as a cross-type map, and
the cross-type voice and structure rules that keep each section carrying only what it uniquely contributes.
Rules specific to one document type live in that type's reference (for example feature-doc rules in
`references/feature.md`, how-to rules in `references/how-to.md`), not here.

- [Document structure and voice](#document-structure-and-voice)
  - [Documentation structure (Diataxis framework)](#documentation-structure-diataxis-framework)
    - [Documentation types](#documentation-types)
    - [When creating documentation](#when-creating-documentation)
  - [Section voice and structure](#section-voice-and-structure)
    - [Section adds only what it uniquely contributes](#section-adds-only-what-it-uniquely-contributes)
    - [Section value audit](#section-value-audit)
    - [Don't silently extend the spec](#dont-silently-extend-the-spec)
    - [Avoid duplication in description](#avoid-duplication-in-description)
      - [❌ Incorrect (duplicated info)](#-incorrect-duplicated-info)
      - [✅ Correct (concise, mentioned once)](#-correct-concise-mentioned-once)
    - [Declarative tone](#declarative-tone)
    - [Tables: one fact per row](#tables-one-fact-per-row)
  - [Document scope and naming](#document-scope-and-naming)
    - [Title names the job](#title-names-the-job)
    - [One document, one job](#one-document-one-job)
  - [Doc index updates](#doc-index-updates)

## Documentation structure (Diataxis framework)

This repository follows the [Diataxis documentation framework](https://github.com/evildmp/diataxis-documentation-framework).

### Documentation types

This is the cross-type map: one line per Diataxis quadrant, so a doc lands in the right directory. For the
per-type detail - the canonical shape, line targets, and do/don't specifics - read that type's reference.

1. **How-to Guides** (`/docs/how-to/`) - goal-oriented, terse recipes for a task the reader came to do.
   See [`references/how-to.md`](/.apm/skills/writing-docs/references/how-to.md).

2. **Explanation** (`/docs/features/`)
   - Conceptual understanding
   - "Why" questions
   - Background and context
   - Design decisions and trade-offs

3. **Reference** (`/docs/`) - factual, precise lookup registers with no "why" narrative. The catalog splits
   this quadrant into five per-type references: an object-model reference
   ([`references/object-model-reference.md`](/.apm/skills/writing-docs/references/object-model-reference.md)),
   a parameter catalog ([`references/parameter-catalog.md`](/.apm/skills/writing-docs/references/parameter-catalog.md)),
   a macro catalog ([`references/macro-catalog.md`](/.apm/skills/writing-docs/references/macro-catalog.md)),
   a policy or architecture note
   ([`references/policy-architecture-note.md`](/.apm/skills/writing-docs/references/policy-architecture-note.md)),
   and the glossary ([`references/glossary.md`](/.apm/skills/writing-docs/references/glossary.md)).

4. **Tutorials** (`/docs/tutorials/`) - learning-oriented, a complete worked example that teaches a
   beginner one capability end to end. See
   [`references/tutorial.md`](/.apm/skills/writing-docs/references/tutorial.md).

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

### Declarative tone

**Documentation describes the system as it is now. Do not narrate the change that produced the current state:
no transitions, before/after diffs, elements marked "new", or history of what was merged, renamed, split,
moved, or deprecated.**

This applies to every state-describing doc - reference specs and object schemas (the Diataxis Reference
quadrant), feature and explanation docs, and technical-design docs such as the pipeline flow and architecture.
Implementation history - what changed, what was added, what one component absorbed from another - belongs in
tickets, PR descriptions, and commit messages, not in the doc itself. When one component absorbs another's
function, describe only the result ("component B performs the function") and never the move itself ("the
function, formerly in component A, is now part of B"). The reader looks the doc up to learn the current state;
they cannot act on how it got there, and the narration ages the moment the next change lands.

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

Change-narration reads the same way - state the result, not the move. For example:

- ❌ `The push, formerly a separate step, is now part of the generator.`
- ✅ `The generator pushes the effective set.`

**Exception:** Migration documents and changelogs are explicitly about transitions. They describe how to
move from state X to state Y and are not subject to this rule.

**Scope:** Applies to **new and modified content only**.

**Why:** Docs are looked up to learn what something IS. Mixed transitional content makes them brittle -
phrases like "new", "AS IS", or "formerly merged into" age poorly as the system evolves, and force readers to
mentally filter what is current from what is historical.

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

## Document scope and naming

### Title names the job

A document's title and filename name the job the document actually does, in the reader's terms. When the
content changes, the title and filename change with it. A name that still describes an older or narrower
scope sends readers to the wrong place and hides the document from a search for what it now covers.

❌ **INCORRECT:**

- A guide retitled to cover four registries but still filed as `configure-cloud-artifact-registries.md`, so
  the filename claims "cloud" while the body now covers on-prem Nexus and Artifactory.
- A title that names one object the document happens to mention (`Create a Registry Definition`) when the
  document is really about authenticating to a registry.
- A tutorial extended with a second scenario but still titled and filed for the first one only.

✅ **CORRECT:**

- Rename the file and the heading together when the scope changes, and update the index readmes and inbound
  links in the same change (see [Doc index updates](#doc-index-updates)).
- Take the title from the reader's goal ("Configure registry authentication"), not from one object in the
  body.

**Scope:** Applies to **new and modified content only**. When an edit changes what a document covers, bring
its title and filename into line in the same change.

**Why:** The title and filename are the first thing a reader matches against their task. A stale name is a
silent miss: the link checker still passes, but readers and searches land on a promise the body no longer
keeps.

---

### One document, one job

A document does one job for one reader. Name that job in the opening lines, and let every section serve it.
When a draft fuses several jobs - a one-time setup, a migration, and a recurring task, each with its own
reader and cadence - it serves none of them well: the reader doing one job wades through the other two.

This cuts by job and cadence, not by Diataxis type: the Diataxis separation (see
[Documentation types](#documentation-types)) keeps how-to, explanation, and reference apart, while this
rule separates one-time setup, migration, and recurring work even within one quadrant. See also
[Section value audit](#section-value-audit).

A useful test: state the document's job in one sentence ("set a sensitive parameter for an existing
environment"). If a step does not serve that sentence - it onboards infrastructure, or discovers what an
existing setup already holds - it belongs to a different job. Framing matters too: a step that exists only
to consume or verify the result is not an authoring step, and it reads wrong when numbered among them.

❌ **INCORRECT:**

- A "create credentials" guide that opens by *finding* credentials that already exist - a discovery step
  from a migration, not a creation step.
- A guide that interleaves connecting to a secret store (once per repository), converting an existing
  template (once per template), and adding one parameter (recurring) as a single procedure.
- One page that documents both the initial cluster setup and the day-to-day task that later runs on it.

✅ **CORRECT:**

- The document names its single job up front, and each section advances it.
- One-time setup and migration are their own documents, or clearly separated sections, referenced by the
  task document rather than inlined into it.
- A reference doc that states what an object is and links to the how-to that configures it, rather than
  absorbing the procedure.

**Scope:** Applies to **new and modified content only**.

**Why:** A reader arrives with one job. A document scoped to that job is shorter, is easier to keep correct,
and does not force the reader to work out which steps are theirs. Fused jobs also drift: a change made for
one job disturbs the steps of another that happens to share the page.

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
