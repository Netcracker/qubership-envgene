# Parameter catalog

How to write a parameter catalog under `docs/`. A parameter catalog lists the launch or configuration
parameters of EnvGene, one entry per parameter, each stating its effect, its allowed values, its default, and
whether it is mandatory. It is a lookup register in the Diataxis Reference quadrant.

- [Parameter catalog](#parameter-catalog)
  - [What a parameter catalog is](#what-a-parameter-catalog-is)
  - [Canonical shape](#canonical-shape)
  - [The recognised-parameters contract callout](#the-recognised-parameters-contract-callout)
  - [The per-entry template](#the-per-entry-template)
  - [Deprecated parameters and value formats](#deprecated-parameters-and-value-formats)
  - [The group-by-repository variant](#the-group-by-repository-variant)
  - [Distinct from a macro catalog and a feature doc](#distinct-from-a-macro-catalog-and-a-feature-doc)

## What a parameter catalog is

A parameter catalog lives at the top level of `docs/` and sits in the Diataxis Reference quadrant. The two
real exemplars are [`instance-pipeline-parameters.md`](/docs/instance-pipeline-parameters.md), the pipeline
launch parameters, and [`envgene-repository-variables.md`](/docs/envgene-repository-variables.md), the CI/CD
variables. Each is a flat list of parameters, one per `###` heading, under a rigid per-entry template.

The reader has a parameter name or a goal and needs its contract - what it does, what values it takes, its
default, and whether it is required. The catalog answers that lookup. It does not teach a workflow built on the
parameter - that goes to a how-to or feature doc, cross-linked from the entry.

## Canonical shape

Mined from [`instance-pipeline-parameters.md`](/docs/instance-pipeline-parameters.md), the skeleton is an
opening contract callout, a `## Parameters` section holding one `### <PARAM_NAME>` per entry, then a
`## Deprecated Parameters` section and the value-format sections:

```markdown
# Instance Pipeline Parameters

> [!IMPORTANT]

## Parameters
### `ENV_NAMES`
### `CLUSTER_NAME`
### `PIPELINE_TYPE`
...
## Deprecated Parameters
### `SD_DELTA`
...
## Parameter value formats
## Multiple Values Support
```

Each entry heading is the parameter name in backticks. The entries sit in a stable order the reader can scan,
not alphabetical for its own sake - related parameters stay together.

## The recognised-parameters contract callout

The catalog opens with a `> [!IMPORTANT]` callout stating that only the listed parameters are recognised and
anything else is silently ignored. Mined verbatim from
[`instance-pipeline-parameters.md`](/docs/instance-pipeline-parameters.md):

```markdown
> [!IMPORTANT]
> EnvGene recognises and processes **only the parameters listed on this page**. Passing any variable not documented here
> has no effect on pipeline behaviour and will be silently ignored.
>
> Do not rely on undocumented parameters - they are not part of the EnvGene contract and may be removed or conflict with
> future additions without notice.
```

This callout is the contract of the whole document - the list is exhaustive. Carry it when the parameter set
it catalogs is a closed recognised set.

## The per-entry template

Every entry follows the same rigid label template so the reader scans the same slots in every parameter. The
real field labels, in order:

- `**Description**:` - what the parameter controls, in one or more sentences. Where processing is conditional,
  the description states the condition (for example "Processed at both `PIPELINE_TYPE: GITLAB_DEPLOY` and
  `PIPELINE_TYPE: LEGACY`").
- `**Allowed values**:` - the enum, present only when the parameter takes a fixed value set
  (`PIPELINE_TYPE` lists `GITLAB_DEPLOY`, `LEGACY`). Omit this label for free-form values.
- `**Default Value**:` - the default, or `None`.
- `**Mandatory**:` - `Yes`, `No`, or `No` with the condition that makes it required ("No. Required when
  `CLUSTER_NAME` and `ENVIRONMENT_NAME` are not provided").
- `**Example**:` - a real value, or a short bullet list of example values for the single and multiple cases.

Keep the labels and their order identical across every entry. A reader relies on finding `**Default Value**`
in the same place in every entry. Present only the labels the entry needs - drop `**Allowed values**` for a
free-form parameter rather than writing an empty one.

## Deprecated parameters and value formats

Deprecated parameters are not deleted from the catalog - they move to a `## Deprecated Parameters` section
under a one-line note ("The following parameters are planned for removal") and keep the same per-entry
template, with the `**Description**` pointing to the replacement ("Deprecated. Use `SD_REPO_MERGE_MODE`
instead"). This keeps a reader who still passes the old parameter from landing on nothing.

Cross-cutting value rules that apply to many parameters go in their own sections after the entries rather than
repeating in each one. [`instance-pipeline-parameters.md`](/docs/instance-pipeline-parameters.md) carries
`## Parameter value formats` (how a structured value may be passed as YAML, JSON, or JSON-in-string) and
`## Multiple Values Support` (the delimiters for a multi-value parameter), each stated once and referenced by
the entries that need them.

## The group-by-repository variant

When the parameters split across more than one scope, group them under a `##` per scope instead of one flat
`## Parameters`. [`envgene-repository-variables.md`](/docs/envgene-repository-variables.md) uses this variant:
its top-level sections are `## Instance EnvGene Repository`, `## Template EnvGene Repository`, and
`## Discovery EnvGene Repository`, each holding its own `### <VARIABLE>` entries under the same per-entry
template. A variable that exists in more than one repository disambiguates in the heading itself
(`### DOCKER_REGISTRY (in instance repository)`). Use the flat form when every parameter shares one scope and
the grouped form when the scope is itself a lookup axis.

## Distinct from a macro catalog and a feature doc

A parameter catalog is keyed by a launch or pipeline parameter - a value the operator passes to a run. A
[macro catalog](/.claude/skills/writing-docs/references/macro-catalog.md) is keyed by a template macro and
carries a resolution scope, which a parameter catalog has no equivalent of. The entry templates differ too -
the parameter catalog uses `**Default Value**` / `**Mandatory**`, the macro catalog uses `**Type:**` /
`**Basic usage:**`. Keep them as separate documents.

Against a [feature doc](/.claude/skills/writing-docs/references/feature.md) the border is the "why". A
parameter catalog states a parameter's contract with no rationale narrative - it is a lookup register. When an
entry starts explaining why the capability behind the parameter exists or how it behaves end to end, that
explanation belongs in the feature doc, cross-linked.
