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

Required. Two to five sentences. State the situation and the specific problem that motivates the
change. Do not restate the design - the design reference link covers that.

Good:

> EnvGene's `generate_effective_set` regenerates the full deployment context for every
> namespace in the env_instance on each run. The pipeline has no way to express "this namespace
> should be cleaned". Operators work around the gap by manually editing `env_instance` and
> `sd.yml` between runs, which has no audit trail and is error-prone.

Bad:

> We want to add cleanup support.

The bad example states the action, not the situation. The reader cannot judge urgency or fit
from it.

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

Good:

> 1. Add optional field `cleaned` (boolean, default absent) to the namespace schema.
> 2. Add CLEAN behavior to `env_build_job`. When activated, it sets `cleaned: true` on the named
>    namespaces. All other env_instance content is left untouched.
> 3. Add a marker-driven branch to `generate_effective_set_job`. For each namespace with
>    `cleaned: true`, emit `cleanup/<ns>/` using the existing cleanup context logic.

Bad:

> 1. Implement cleanup.

The bad example does not let the reader judge whether the scope is sized correctly.

### Out of scope changes

Optional. Recommended whenever the design covers more ground than the implementation slice,
when adjacent improvements were considered and deferred, or when the boundary is non-obvious.

Good:

> - CMDB-side cleanup. The `cmdb_import` flow continues to reject env_instances containing
>   cleaned namespaces.
> - Dynamic pipeline path. CLEAN parameters apply only to the static pipeline.
> - Productization. This CR delivers the PoC behavior only.

Empty is allowed when the design and the implementation slice are identical and no adjacent work
could be confused with this CR. State `none` explicitly in that case.

### Acceptance

Required. Observable, testable conditions that determine the CR is complete. State each as a
condition that can be verified by running the system, not as a description of what was
implemented.

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
acceptance. Use this for:

- Branch hint. "Implement in PoC branch `poc/cleanup-mode`. Do not merge to `main` until
  productization is approved."
- Library hint. "Use `qubership-pipelines-common-python-library` v2 `secret_manager` for
  external credential lookups."
- Contact hint. "Questions on SOPS scope-flag behavior - ask @user."
- Prior art hint. "Follow the credential-resolution pattern from the CP discovery integration:
  `envgen.creds.get('<id>').secret`."
- Horizon hint. "PoC only. Productization is a separate CR."

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
