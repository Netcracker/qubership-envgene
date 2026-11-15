# Policy or architecture note

How to write a policy or architecture note under `docs/`. A policy note states a standing rule - what is
allowed, forbidden, or constrained in one small domain. An architecture note classifies a small domain into a
few named cases and tells the reader how to tell which case applies. Both are short, declarative, and
bullet- and small-table-driven. They sit in the Diataxis Reference quadrant.

- [Policy or architecture note](#policy-or-architecture-note)
  - [What a policy or architecture note is](#what-a-policy-or-architecture-note-is)
  - [Canonical shape: the policy note](#canonical-shape-the-policy-note)
  - [Canonical shape: the architecture note](#canonical-shape-the-architecture-note)
  - [Distinct from a feature doc](#distinct-from-a-feature-doc)

## What a policy or architecture note is

A policy or architecture note lives at the top level of `docs/` and sits in the Diataxis Reference quadrant.
This is the lightest document type in the catalog - a one-paragraph scope sentence followed by three or four
short `##` sections. The two real exemplars are [`credential-value-policy.md`](/docs/credential-value-policy.md),
a policy note, and [`deployment-architecture.md`](/docs/deployment-architecture.md), an architecture note -
each about 35 to 40 lines.

The reader needs one fact they can act on - a rule to obey, or which of a few cases they are in. The note
states it and stops. It carries no mechanism narrative - how the policy is enforced or how the architecture
works internally belongs in a feature or technical-design doc, cross-linked.

## Canonical shape: the policy note

A policy note opens with a one-paragraph scope sentence naming what the policy applies to, then states the
rule across three or four short `##` sections carried by bullet lists and the occasional small sentence. Mined
from [`credential-value-policy.md`](/docs/credential-value-policy.md), the skeleton reads:

```markdown
# Credential value policy

## Recommended characters
## Forbidden characters
## Size constraints
```

The opening paragraph scopes it ("This policy applies to credential values in EnvGene. It covers...") with a
bullet list of what is in scope. Each `##` section is a short declarative list - `## Forbidden characters`
lists the four characters and nothing else, `## Size constraints` states the recommended maximum in one
sentence. State the rule, not the reasoning behind it. The note is a standing contract the reader obeys, not
an argument for the contract.

## Canonical shape: the architecture note

An architecture note opens with a one-paragraph scope sentence, carries one `##` per named case, and closes
with a `## Determine ...` section holding a decision table. Mined from
[`deployment-architecture.md`](/docs/deployment-architecture.md), the skeleton reads:

```markdown
# Deployment architecture

## CMDB
## No-CMDB v1
## No-CMDB v2
## Determine an environment's architecture
```

The opening paragraph states the classification ("operates each environment in one of three deployment
architectures") and what distinguishes the cases. Each case `##` is two or three sentences describing that
case declaratively. The closing `## Determine ...` section carries the decision rule as a small table keyed by
the deciding field. Mined verbatim:

```markdown
| Architecture | Condition                                   |
|--------------|---------------------------------------------|
| No-CMDB v1   | `noCmdbVersion` is `v1`, or neither is set  |
| No-CMDB v2   | `noCmdbVersion` is `v2`                     |
| CMDB         | `noCmdbVersion` is unset, `deployer` is set |
```

The table is the payload - it lets the reader read off their case from the fields they can inspect. State the
precedence rule in prose above the table when one field overrides another ("`inventory.noCmdbVersion` takes
precedence over `inventory.deployer`").

## Distinct from a feature doc

A policy or architecture note states a standing rule or classifies a small domain, in a page, with no
mechanism narrative. A [feature doc](/.claude/skills/writing-docs/references/feature.md) explains a capability
and why it exists at length, in the Explanation quadrant. The border is the "why" and the length: the moment
the note starts explaining how the policy is enforced inside the pipeline, or how an architecture delivers its
output step by step, that explanation belongs in the feature doc (or a technical-design doc for internal
wiring), cross-linked, and the note keeps only the rule or the classification. If a note grows past roughly 50
lines it is usually absorbing explanation that should be its own document. See
[One document, one job](/.claude/skills/writing-docs/references/doc-structure.md#one-document-one-job).
