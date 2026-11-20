# Proposal

## Why

An upstream orchestration pipeline needs a machine-readable record of the Instance pipeline's
`env_prepare` steps so it can build its own aggregation report and surface operation status and
troubleshooting information. Today that record exists only as the end-of-job log summary and, when Metrics
Collector is configured, as a hidden, differently shaped internal file, so the orchestrator has nothing it
can read straight from the job artifacts.

## What Changes

- The `env_prepare` job writes an `EnvPrepareReport` artifact at the end of a single-environment run,
  carrying the per-step results already shown in the job log summary.
- The report is published at `env-prepare-report.json` in the root of the job artifacts, so an upstream
  pipeline can locate it by a fixed path.
- The report is always published. It does not depend on `METRICS_COLLECTOR_URL`, and it is not suppressed
  by `SAVE_ARTIFACTS_STRATEGY`. The artifact size-limit trim is extended to preserve the report file.
- Report generation is fail-safe. A write error is logged and the run continues, so the report never fails
  the job.
- In a multi-environment fan-out run the report is not produced, and report generation does not fail the
  run.
- When Metrics Collector is configured, the report's step list matches the step list in the Metrics
  Collector activity event for the same run, because both are rendered from the same source.
- A JSON schema for the `EnvPrepareReport` object is added to the EnvGene object schemas as the consumer
  contract.
- The feature and reference documentation describe the artifact, its location, and its fields.

Out of scope, deferred to later changes: multi-environment support, the growing `EnvGenePipelineReport`
model with per-job stages, the `start`/`running`/`stop` event redesign, pipeline configuration or
environment context in the report, and error codes or traces. The step duration keeps its current `time`
representation in this change. The move to a millisecond duration field is a separate later change.

## Capabilities

### New Capabilities

- `env-prepare-report`: the Instance pipeline publishes a single-environment `env_prepare` step report as
  a job artifact at a fixed location, with a stable object shape and a defined publish lifecycle.

### Modified Capabilities

<!-- None. No existing capability's requirements change. -->

## Impact

- Instance pipeline `env_prepare` job: adds the `EnvPrepareReport` artifact to its single-environment
  output.
- Job artifacts: a new file at the artifacts root, `env-prepare-report.json`, preserved by the size-limit
  trim.
- EnvGene objects: a new `EnvPrepareReport` object and its JSON schema under `schemas/`.
- Metrics Collector activity: no behavior change, but the report shares the event's step list, so the two
  stay consistent. See the ADR under [docs/adr](/docs/adr) for the decision and rejected alternatives.
- Documentation: the Metrics Collector feature and technical-design docs gain the artifact and its
  contract.
- No pipeline parameters are added or changed.
