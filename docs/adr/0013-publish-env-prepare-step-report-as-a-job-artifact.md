# ADR-0013: Publish the env_prepare step report as a standalone job artifact

Status: Proposed

## Context and problem statement

An upstream orchestration pipeline drives the Instance pipeline among other tools, and needs to build its
own aggregation report and show operation status and troubleshooting information. To do that it needs a
machine-readable record of the `env_prepare` job's step results. Today that record exists only as the
end-of-job log summary, which is human-oriented text, and, when Metrics Collector is configured, as an
internal file that is hidden, gated on that integration, and shaped for a different consumer. The
orchestrator has nothing it can read straight from the job artifacts.

## Decision drivers

- The upstream pipeline must read the report from the job artifacts at a fixed, discoverable path, without
  parsing logs.
- The report must be present whether or not Metrics Collector is deployed, and whether or not the job
  saves its other artifacts.
- The report must stay consistent with the step results the Metrics Collector event already reports, so
  two records of the same run never disagree.
- Writing the report must never change the job's outcome.

## Considered options

- Option A: a standalone `EnvPrepareReport` artifact at a fixed artifacts-root path, rendered from the same
  step-result source that feeds the log summary and the Metrics Collector event.
- Option B: reuse the existing internal Metrics Collector completion file as the artifact.
- Option C: emit the richer growing pipeline report with per-job stages now.
- Option D: produce the report by parsing the end-of-job log summary text.

## Decision outcome

Chosen: Option A, because it gives the consumer a stable file at a fixed path on every run while sharing
the event's single step-result source, so the artifact and the event cannot diverge.

The report is written to `env-prepare-report.json` in the root of the job artifacts, for a single-
environment run only. To keep it present even when the job trims its artifacts to stay under the size
limit, the trim's keep-set is extended to this named file. Under the "do not save artifacts" setting the
finalizer deletes nothing, so the report survives there as well. Writing is fail-safe: a write error is
logged and the run continues, the same contract the Metrics Collector completion write already follows.

## Pros and cons of the options

### Option A: standalone always-published report (chosen)

- Good, because the consumer finds the report at a fixed root path on every single-environment run,
  independent of the Metrics Collector integration and of the artifact-save setting.
- Good, because rendering it from the same step-result source as the event keeps the two records
  consistent by construction.
- Neutral, because a named root file makes the "preserve on trim" intent explicit, through one keep-set
  entry, rather than hiding it behind an unrelated directory.
- Bad, because the step results now exist in two serialized forms, the artifact and the event, that must
  be kept consistent as the report evolves.
- Bad, because the size-limit trim gains a named-file exception, a small special case in the publish
  logic.

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

- Positive: the upstream orchestration pipeline gets a machine-readable step report from the job
  artifacts, at a fixed root path, present regardless of whether Metrics Collector is deployed.
- Positive: writing is fail-safe, so adding the report cannot change the job's pass or fail outcome.
- Negative: the step results are now serialized in two places, the artifact and the Metrics Collector
  event, which must be kept consistent; a shared source mitigates this but the coupling remains.
- Negative: the size-limit trim carries a special case for a named file, a small coupling in the publish
  logic.
- Negative: because the report always publishes, it appears even when the operator has asked for no
  artifacts, so "no artifacts published" is no longer strictly true for this file.
- Negative: a multi-environment fan-out run produces no report. The consumer need is per single-
  environment run, so the fan-out stays crash-free but unserved; a later change can add it if needed.

## More information

- Specs: [env-prepare-report delta spec](/openspec/changes/env-prepare-report-artifact/specs/env-prepare-report/spec.md)
- Proposal: [env-prepare-report-artifact proposal](/openspec/changes/env-prepare-report-artifact/proposal.md)
