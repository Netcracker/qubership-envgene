# Technical-design doc

How to write a technical-design doc under `docs/technical-design/`. A technical-design doc specifies the
internal wiring of EnvGene - which job or step, in what order, what each reads and writes - for an EnvGene
developer. It is implementation-defining: it pins down how the system is built, not only how it behaves.

- [Technical-design doc](#technical-design-doc)
  - [What a technical-design doc is](#what-a-technical-design-doc-is)
  - [Three sub-shapes](#three-sub-shapes)
    - [Step doc](#step-doc)
    - [Flow doc](#flow-doc)
    - [Sub-flow doc](#sub-flow-doc)
  - [Location convention](#location-convention)
  - [Distinct from a feature doc](#distinct-from-a-feature-doc)

## What a technical-design doc is

A technical-design doc lives under `docs/technical-design/`. Its reader is an EnvGene developer, not an
operator. It documents the pipeline as jobs, steps, and functions, and the exact contract each one holds.
The [instance-pipeline README](/docs/technical-design/instance-pipeline/README.md) names the three roles
the docs under it play: the flow (jobs, steps, functions, and each step's trigger), the per-step design
(one file per step), and the per-scenario projections (which steps fire for a given operation).

## Three sub-shapes

Technical-design docs come in three real sub-shapes, each with its own skeleton.

### Step doc

A step doc is the rigid contract for one pipeline step. Mined from
[`steps/env-build.md`](/docs/technical-design/instance-pipeline/steps/env-build.md), the template is
fixed and every section is present in order:

```markdown
# `env_build`

## Description
## Input parameters
## Processing flow
## Result
## Error handling
## Example
## Related documentation
```

The sections carry a contract, not prose:

- `## Description` - one or two sentences naming what the step renders or writes.
- `## Input parameters` - a table with columns Parameter, Source, Required, Default, Values / format,
  Effect. One row per parameter.
- `## Processing flow` - numbered phases, each a bold phrase, with sub-numbered actions the step takes.
- `## Result` - a numbered list of what exists after the step runs (files written, what is left
  untouched).
- `## Error handling` - each failure keyed to its processing-flow step (for example `5c.`), stating the
  condition and the post-failure state.
- `## Example` - links to real sample files under `docs/samples/`.
- `## Related documentation` - links to the neighboring steps and the feature docs.

### Flow doc

A flow doc describes a whole pipeline as jobs, steps, and functions, and is the source of truth for each
step's trigger. Mined from [`flow.md`](/docs/technical-design/instance-pipeline/flow.md), the skeleton is
a `## Flow` section with numbered jobs, each job holding its numbered steps:

```markdown
# Modern toolset flow

## Flow

### 1 job `env_prepare`

#### 1.1 step `preprocess`
#### 1.2 step `get_passport`
...

### 2 job `sync`

#### 2.1 step `preprocess`
#### 2.2 step `sync`
```

The `## Flow` preamble defines the three levels (job, step, function). Each job states its own trigger.
Each step states its `Triggers:` gate, an optional `Design:` link to the step doc, and its `Functions:`
with per-function input, output, and actions. The flow doc owns the triggers - the step and sub-flow docs
resolve them, they do not redefine them.

### Sub-flow doc

A sub-flow doc projects the flow onto one operation and enumerates the variants. Mined from
[`sub-flows/clean.md`](/docs/technical-design/instance-pipeline/sub-flows/clean.md), the skeleton opens
with `## Launch parameters` and then one section per variant:

```markdown
# CLEAN sub-flows

## Launch parameters
## CLEAN a whole environment
## CLEAN selected namespaces
```

`## Launch parameters` is a table of the parameters that select the sub-flow (Parameter, Values, Role).
Each variant section carries the resolved flow (which numbered steps fire), the launch-parameter YAML,
and the actions. The sub-flow states up front that the step triggers are the single source of truth in
the flow doc and that it only resolves them for the scenario.

## Location convention

Technical-design docs live under `docs/technical-design/`. The shape, not the path, is what makes a doc
a technical-design doc: a top-level pipeline doc that describes job wiring,
[`docs/envgene-pipelines.md`](/docs/envgene-pipelines.md), is a technical-design doc by shape even though
it sits at top level rather than under `docs/technical-design/`.

## Distinct from a feature doc

The border between a technical-design doc and a
[feature doc](/.apm/skills/writing-docs/references/feature.md) is a deterministic test. A
technical-design doc specifies the internal wiring - which job or step, in what order, what each reads
and writes - for an EnvGene developer, and is implementation-defining: a different internal implementation
would force a rewrite, because the doc pins the wiring itself.

If instead a different implementation with the same observable outcome would not force a rewrite, the
content is implementation-independent and belongs in a feature doc, written for the operator. The step
I/O contract - the `## Input parameters`, `## Processing flow`, `## Result`, and `## Error handling` of a
step doc - is the clearest marker: it names exact files, parameters, and ordering, so it can only live in
a technical-design doc. A feature doc that carries such a contract is misfiled (see
[Distinct from a technical-design doc](/.apm/skills/writing-docs/references/feature.md#distinct-from-a-technical-design-doc)).
