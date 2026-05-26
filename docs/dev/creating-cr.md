# Creating a change request issue

- [Description](#description)
- [When to create a CR](#when-to-create-a-cr)
- [Sections](#sections)
  - [Context](#context)
  - [Design reference](#design-reference)
  - [In scope changes](#in-scope-changes)
  - [Out of scope changes](#out-of-scope-changes)
  - [Acceptance](#acceptance)
  - [Implementation notes](#implementation-notes)
- [Issue body template](#issue-body-template)
- [Creating the issue](#creating-the-issue)

## Description

> [!NOTE]
> This is the convention for **implementation-phase CRs only** - handing a settled design to a
> developer. For design proposals, investigation, or docs-only changes, see
> [When to create a CR](#when-to-create-a-cr) for alternatives.

A change request (CR) issue hands a settled design to a developer for implementation. By the
time it is filed, design decisions are complete and reviewable. The CR cuts the implementation
slice and states how the work will be verified.

The design lives in a documentation PR or in a merged `docs/features/X.md`.

This guide explains when to create a CR, what each section of the body contains, and shows
good and bad examples per section. It also provides a copypaste body template.

## When to create a CR

Create a CR when all of these hold:

- A design exists and is reviewable as a doc PR or as merged content under `docs/features/`.
- The work to implement is bounded and can start without further design decisions.
- The acceptance can be stated as observable, testable conditions.

Do not create a CR when:

- The design is not settled. File an analysis issue instead.
- The work is a pure bugfix. Use the bug template.
- The work is a docs-only change with no implementation. Open a PR directly.

## Sections

The issue body has six sections. Four are required, two are optional.

### Context

Required. Two to five sentences. State the situation and the specific problem that motivates
the change. Anchor with a system, component, or existing behavior.

Avoid:

- Restating the design - the design reference link covers that.
- Previewing this CR's scope - that's In scope changes.
- Enumerating the files, fields, schema tokens, or jobs that the CR will modify - that
  enumeration is In scope content.

Good:

> EnvGene's `generate_effective_set` regenerates the full deployment context for every
> namespace in the env_instance on each run. The pipeline has no way to express "this namespace
> should be cleaned". Operators work around the gap by manually editing `env_instance` and
> `sd.yml` between runs, which has no audit trail and is error-prone.

Bad (states the action, not the situation):

> We want to add cleanup support.

Bad (previews scope and enumerates implementation surface):

> Phase 2 extends external-credential support to the system-credential catalog
> (`integration.yml`, `deployer.yml`, AppDef, RegDef), the pipeline and topology Effective Set
> contexts, and adds validations specific to system credentials.

### Design reference

Required. A permalink to where the design lives. The link must survive the design PR's merge
and the deletion of the source branch. Use one of:

- A PR reference like `#1198`. GitHub auto-links it, and the PR stays accessible after merge.
- A commit-SHA permalink to a feature doc, for example
  `https://github.com/Netcracker/qubership-envgene/blob/<sha>/docs/features/cleanup.md`. The
  SHA freezes the design version the CR was scoped to.
- A previous design issue whose body contains the spec.

Avoid branch-pinned URLs (`.../blob/<branch>/...`). They break when the branch is deleted.

If no design reference exists, the work is not ready for a CR.

### In scope changes

Required. A numbered list of changes this CR makes. Each item names what is modified or added,
and at what level (file, schema field, job, parameter).

Each item must include an inline link to the specific design section that describes it. Use an
anchor link in the SHA-pinned permalink to the design doc:
`https://github.com/Netcracker/qubership-envgene/blob/<sha>/docs/features/<file>.md#<anchor>`.
If an item has no matching design section (it is a derived change such as a test or refactor),
state that explicitly and link to the file-level permalink instead.

Two structures are allowed:

- **Flat.** All items are atomic top-level entries. Use when changes do not cluster.
- **Grouped.** A top-level item names a feature, category, or component. Sub-items are the
  atomic changes that compose it. Use when several atomic changes share a thematic umbrella.

Rules for both:

- Each item (top-level and sub-item) includes its own anchor link.
- Nest at most one level deep. Do not create three-level lists.
- A grouped top-level item with one sub-item is flattened - the grouping carries no signal.

Good:

````markdown
1. Add optional field `cleaned` (boolean, default absent) to the
   [namespace schema](https://github.com/Netcracker/qubership-envgene/blob/<sha>/docs/features/cleanup.md#namespace-object).
2. Add CLEAN behavior to
   [`env_build_job`](https://github.com/Netcracker/qubership-envgene/blob/<sha>/docs/features/cleanup.md#env_build_job).
   When activated, it sets `cleaned: true` on the named namespaces. All other env_instance
   content is left untouched.
3. Add a marker-driven branch to
   [`generate_effective_set_job`](https://github.com/Netcracker/qubership-envgene/blob/<sha>/docs/features/cleanup.md#generate_effective_set_job).
   For each namespace with `cleaned: true`, emit `cleanup/<ns>/` using the existing cleanup
   context logic.
````

Bad:

> 1. Implement cleanup.

The bad example does not let the reader judge whether the scope is sized correctly, and has no
link to the design section that describes the change.

### Out of scope changes

Optional. Recommended whenever the design covers more ground than the implementation slice,
when adjacent improvements were considered and deferred, or when the boundary is non-obvious.

Each exclusion should be specific enough that the implementer can identify the boundary
without ambiguity. Acceptable specifiers include:

- A qualifier (`CMDB import while cleaned markers exist`, not `CMDB import`).
- A constraint (`VALS only`, `instance repo only`).
- A deferral or follow-up reference (`phase 3`, `tracked in #1234`).
- A consequence (`continues to reject env_instances`, `fails at validation`).

Bare category names leave the boundary open to interpretation.

Good:

> - CMDB-side cleanup. The `cmdb_import` flow continues to reject env_instances containing
>   cleaned namespaces.
> - Dynamic pipeline path. CLEAN parameters apply only to the static pipeline.
> - Productization. This CR delivers the PoC behavior only.

Empty is allowed when the design and the implementation slice are identical and no adjacent work
could be confused with this CR. State `none` explicitly in that case.

### Acceptance

Required. Observable, testable conditions that determine the CR is complete.

Each condition should be:

- **Observable.** Verifiable by someone external to the implementer.
- **Specific.** Names concrete values, files, or behaviors, not generalities like "works well".
- **Falsifiable.** Binary yes/no, not subjective.
- **Independent.** Verifiable without depending on other conditions where possible.
- **Distinct from implementation.** States what is true, not how it was built.

Cover both happy path and failure cases.

Each condition is self-contained. State the test context (backend, fixture, mode) inline within
the conditions that depend on it, not as a global preamble. Test context that applies to every
condition uniformly belongs in Implementation notes.

Use either declarative form ("X resolves to Y") or Given/When/Then. Both are valid - the
principles above apply equally.

Good:

> - Given a static pipeline run with `OPERATION_TYPE=CLEAN` and `NAMESPACE_NAMES=ns-a,ns-b`, the
>   resulting env_instance has `cleaned: true` on `ns-a/namespace.yml` and `ns-b/namespace.yml`.
>   No other `namespace.yml` is modified.
> - Given the same run, the effective set contains `cleanup/ns-a/parameters.yaml` and
>   `cleanup/ns-b/parameters.yaml`.
> - Given a subsequent DEPLOY run with the same scope, `cleaned: true` is no longer present in
>   `ns-a/namespace.yml` or `ns-b/namespace.yml`.

Bad:

> - The CLEAN operation works.
> - Tests pass.

The bad examples are unfalsifiable. "Works" does not name what is observed.

### Implementation notes

Optional. Pragmatic guidance for the implementer that does not belong in the design or in
acceptance. Use any subset of the categories below - usually only one or two apply:

- Branch hint. "Implement in PoC branch `poc/cleanup-mode`. Do not merge to `main` until
  productization is approved."
- Library hint. "Use `qubership-pipelines-common-python-library` v2 `secret_manager` for
  external credential lookups."
- Contact hint. "Questions on SOPS scope-flag behavior - ask @user."
- Prior art hint. "Follow the credential-resolution pattern from the CP discovery integration:
  `envgen.creds.get('<id>').secret`."
- Horizon hint. "PoC only. Productization is a separate CR."
- Test setup. "Acceptance verified against a Vault Secret Store. Bring up via `make vault-up`."

Include only categories that apply. Omit the section entirely if nothing applies.

Do not put design decisions here. Decisions belong in the design doc.

## Issue body template

Copypaste the block below as the issue body, then fill each section. The skill produces the
same structure. Sections marked optional may be omitted when empty.

````markdown
## Context

<situation and the specific problem that motivates the change, 2-5 sentences>

## Design reference

<permalink: PR ref like `#1198`, or a commit-SHA URL to a feature doc. No branch-pinned URLs.>

## In scope changes

1. <change>
2. <change>

## Out of scope changes

<optional - bullets, or "none">

## Acceptance

- <observable, testable condition>
- <observable, testable condition>

## Implementation notes

<optional - branch, libraries, contacts, horizon hints>
````

## Creating the issue

Use the local skill `doc-pr-to-issue`. The skill takes a documentation PR URL or a path to a
feature doc, parses the content, and produces a draft issue body that follows the template
above. Review the draft, fill out of scope changes and implementation notes where the skill
cannot derive them, and post.

The skill lives at `~/.claude/skills/doc-pr-to-issue/` for now. Team publication is a separate
decision.
