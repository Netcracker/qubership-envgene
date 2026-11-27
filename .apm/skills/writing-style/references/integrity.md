# Accuracy and vocabulary

Rules that keep any text this repository ships truthful and consistent: verify identifiers before stating
them, reuse existing vocabulary, define every term once, do not re-gloss, and link in-repo with repo-root
paths. These apply to every text - docs, readmes, and the prose of issues, CRs, PRs, ADRs, proposals, and
specs.

- [Verify, don't fabricate](#verify-dont-fabricate)
- [Use existing vocabulary](#use-existing-vocabulary)
- [Define every term](#define-every-term)
- [Don't re-gloss established terms](#dont-re-gloss-established-terms)
- [In-repo links](#in-repo-links)

## Verify, don't fabricate

When a statement names a specific identifier - a parameter, environment variable, file path, library
symbol - that identifier is confirmed in the source it describes. Unverifiable identifiers are open
questions, not statements of fact.

For object schemas and example fields, see also the object-examples rules in the `writing-docs` skill
(`references/examples-and-samples.md`).

❌ **INCORRECT:**

- Naming a CI variable for a service by extending a pattern from a sibling service, without checking
  the implementation.
- Listing a config file path from memory without grepping the repository.
- Assuming a library exposes an env-var auth method by analogy with another component.

✅ **CORRECT:**

- Grep or read the source code to confirm the identifier before stating it.
- Mark the identifier as an open question until verifiable.

**Scope:** Applies to **new and modified content only**.

**Why:** Text in this repository is consumed as authoritative. A fabricated detail propagates into tickets,
validation rules, and tooling assumptions.

---

## Use existing vocabulary

Before you name a concept, find the term the product already uses for it. Search the other docs, the
schemas, and the code, not just the current document, and reuse that term. A fresh coinage for a concept
that already has an established name forces readers to hold two glossaries for one idea.

Three habits prevent the usual coinage traps:

- Reuse the established term. If the concept is already named anywhere in the product (a schema field, a
  documented object, another doc), use that name, not a parallel one. Coining `tier` for a concept the
  product calls `baseline` is the classic miss.
- Check for a collision before minting a term. A candidate label that already means something else in the
  product, for example `custom parameters` when `custom_params` is a distinct existing concept, is worse
  than a plain description. Grep for the candidate first.
- Do not oppose a term against its own umbrella. When two things are both instances of one concept, for
  example a baseline and custom values are both performance parameters, phrase them by source or role, not
  as opposites, so the umbrella relationship stays clear.

If the product genuinely has no term for the concept, prefer a plain description over minting a new label,
even one you define. A coined label is a cost the reader pays on every read. Introduce a real new term only
when the description is too clumsy to repeat, and then define it once.

❌ **INCORRECT:**

- Coining a new term (`tier`, `standalone override`) when the product already names the concept or a plain
  description would do.
- A label that collides with an existing, different concept.
- Phrasing a subset and its umbrella as opposites (`baseline` versus `performance parameters`).

✅ **CORRECT:**

- Reuse the product's established term, found by searching docs, schemas, and code.
- Describe the concept plainly when no term exists, and coin only as a last resort with a definition.

**Scope:** Applies to **new and modified content only**.

**Why:** Parallel or colliding vocabulary forces readers to maintain two mental glossaries and produces
ambiguous cross-references. A coinage the reader must learn is a cost that a reused term or a plain
description avoids.

---

## Define every term

**Every domain term a document uses is defined. A term used in one document is defined in that document. A term
used across documents is defined once in the glossary, and each document links to it.**

Three rules govern terminology. This rule governs whether a definition exists and where it lives.
[Use existing vocabulary](#use-existing-vocabulary) governs which term to pick.
[Don't re-gloss established terms](#dont-re-gloss-established-terms) governs how often to restate it.

The glossary lives at [/docs/glossary.md](/docs/glossary.md). A term needs a definition when a competent reader
from outside this repository could misread it. This covers ordinary words used with a specific meaning here,
such as Environment or Effective Set.

- **Single-document term.** Define it on first use in that document, as a sentence, a parenthetical, or a short
  definitions list.
- **Cross-document term.** Add or reuse a glossary entry, then link to it from each document instead of
  restating the definition.
- **Promotion.** When a term defined in one document starts appearing in a second, write a glossary entry for
  it and replace the inline definition in both documents with a link.

❌ **INCORRECT:**

- Using a shared term such as Deploy Postfix with a fresh inline definition in each document that mentions it.
- Introducing a term with no definition in the document or the glossary, leaving the reader to infer it.

✅ **CORRECT:**

- A term local to one how-to guide is defined in that guide.
- A term shared by [calculator-cli.md](/docs/features/calculator-cli.md) and
  [envgene-objects.md](/docs/envgene-objects.md) has one glossary entry that both documents link to.

**Scope:** Applies to **new and modified content only**. Existing multi-document terms are back-filled into the
glossary only when the surrounding lines are edited for other reasons.

**Why:** An undefined term forces the reader to guess or search. A term defined once and linked keeps every
document consistent when the definition changes, and it stops the same concept from drifting into different
meanings across documents.

---

## Don't re-gloss established terms

**Once the document defines a term, use it bare. Do not append the definition, type tag, or
location to every reference.**

The rule covers both classes of re-glossing - inline type or definition tags, and inline location or
path bindings.

❌ **INCORRECT - definition repeated** (every mention re-glosses the type tag):

```markdown
The runtime context does not accept external Credentials (`type: external`).
Local Credentials (`type: usernamePassword` / `secret`) are emitted as plain text.
Built-in credential references resolve to a Credential (`type: external` or `type: usernamePassword` / `secret`).
```

❌ **INCORRECT - location repeated** (every mention restates the path):

```markdown
The generator reads the schema at `/schemas/credentials.schema.json`.
If the schema at `/schemas/credentials.schema.json` is missing, the build fails.
Validation rules at `/schemas/credentials.schema.json` are checked before output.
```

✅ **CORRECT** (terms used bare):

```markdown
The runtime context does not accept external Credentials.
Local Credentials are emitted as plain text.
Built-in credential references resolve to a Credential.
```

```markdown
The credentials schema lives at `/schemas/credentials.schema.json`.

The generator reads the schema. If the schema is missing, the build fails. Validation rules
are checked before output.
```

**Exceptions where the inline detail is justified:**

- **First mention** in the document, especially when the term appears before its definition section in
  reading order. The parenthetical serves as a forward-defining hint.
- **Conditions or filters** that pick a subset, not a redefinition. "External Credential with `create: true`"
  is a filter, not a redefinition of "external".
- **Taxonomy tables** that explicitly map terms to bindings, like a Components or Glossary table.
- **Operational instructions** where the reader copies the exact path or value to act on it.

**Scope:** Applies to **new and modified content only**.

**Why:** Each repetition of a binding is a maintenance liability - when a type renames, an enum value
is added, or a path moves, every parenthetical or location must be updated. Established vocabulary
lets readers internalize the term and frees the text from re-glossing, whether the gloss is a type
tag or a file path.

---

## In-repo links

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
