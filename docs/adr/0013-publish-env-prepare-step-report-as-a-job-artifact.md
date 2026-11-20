# ADR-0013: Publish the env_prepare step report as a standalone job artifact

Status: Proposed

## Context and problem statement

An upstream orchestration pipeline drives the Instance pipeline among other tools, and needs to build its
own aggregation report and show operation status and troubleshooting information for each environment. To
do that it needs a machine-readable record of the `env_prepare` job's step results. Today that record
exists only as the end-of-job log summary, which is human-oriented text, and, when Metrics Collector is
configured, as an internal file that is hidden, gated on that integration, and shaped for a different
consumer. The orchestrator has nothing it can read straight from the job artifacts.

## Decision drivers

- The upstream pipeline must read the report from the job artifacts by convention, without parsing logs.
- The report must be present whether or not Metrics Collector is deployed.
- The report must stay consistent with the step results the Metrics Collector event already reports, so
  two records of the same run never disagree.

## Considered options

- Option A: a standalone, always-published `EnvPrepareReport` artifact, rendered from the same step-result
  source that feeds the log summary and the Metrics Collector event.
- Option B: reuse the existing internal Metrics Collector completion file as the artifact.
- Option C: emit the richer growing pipeline report with per-job stages now.
- Option D: produce the report by parsing the end-of-job log summary text.

## Decision outcome

Chosen: Option A, because it gives the consumer a stable, always-present, conventionally-located file while
sharing the event's single step-result source, so the artifact and the event cannot diverge.

The report is written for each environment at a fixed path under the job's `logs/` subtree. Placing it
there reuses the log lifecycle: the artifact survives the size-limit trim and the "do not save artifacts"
setting, both of which already keep the `logs/` subtree, so the report publishes on every run without any
new save-strategy handling.

## Pros and cons of the options

### Option A: standalone always-published report (chosen)

- Good, because the consumer finds the report at a fixed artifact path on every run, independent of the
  Metrics Collector integration.
- Good, because rendering it from the same step-result source as the event keeps the two records
  consistent by construction.
- Neutral, because living under the `logs/` subtree reuses the existing log lifecycle instead of adding a
  new publish rule.
- Bad, because the step results now exist in two serialized forms, the artifact and the event, that must
  be kept consistent as the report evolves.

### Option B: reuse the internal Metrics Collector file

- Good, because it adds no new writer.
- Bad, because that file is produced only when Metrics Collector is configured, so the consumer gets
  nothing in the common case where the integration is absent.
- Bad, because it is shaped as the pipeline report with its own fields rather than the bare step report
  the consumer wants, and it is written to an internal location, not the job artifacts.

### Option C: emit the growing pipeline report with stages now

- Good, because it would serve the eventual cross-job aggregation model directly.
- Bad, because that model is unsettled and far larger than the current need, so it would commit the
  consumer contract to a shape still being designed.

### Option D: parse the log summary text

- Bad, because the structured step results are the source of truth, and reparsing formatted log text is
  fragile and breaks the moment the summary wording changes.

## Consequences

- Positive: the upstream orchestration pipeline gets a machine-readable, per-environment step report from
  the job artifacts, present regardless of whether Metrics Collector is deployed.
- Positive: placing the report under the `logs/` subtree reuses the existing log lifecycle, so no change
  to the artifact save-strategy or size-limit behavior is needed.
- Negative: the step results are now serialized in two places, the artifact and the Metrics Collector
  event, which must be kept consistent; a shared source mitigates this but the coupling remains.
- Negative: because the report always publishes under `logs/`, it appears even when the operator has asked
  for no artifacts, so "no artifacts published" is no longer strictly true for this file.

## More information

- Specs: [env-prepare-report delta spec](/openspec/changes/env-prepare-report-artifact/specs/env-prepare-report/spec.md)
- Proposal: [env-prepare-report-artifact proposal](/openspec/changes/env-prepare-report-artifact/proposal.md)
