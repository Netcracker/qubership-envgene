# Spec Delta

## Purpose

The Instance pipeline publishes a machine-readable record of the `env_prepare` job's step results as a job
artifact, so an upstream orchestration pipeline can read operation status and troubleshooting information
without parsing logs.

## ADDED Requirements

### Requirement: EnvPrepareReport artifact publication

The `env_prepare` job SHALL write an `EnvPrepareReport` artifact for each environment it processes, at
`logs/<cluster>/<env>/env-prepare-report.json` inside the job artifacts, at the end of the run.

#### Scenario: Single environment run writes the report

- **WHEN** the `env_prepare` job runs for a single environment `<cluster>/<env>`
- **THEN** the job artifacts contain `logs/<cluster>/<env>/env-prepare-report.json` with `kind`
  `EnvPrepareReport` and `apiVersion` `v1`

#### Scenario: Report is written even when the pipeline fails

- **WHEN** the `env_prepare` job fails on one of its steps
- **THEN** the job artifacts still contain the environment's `env-prepare-report.json`

#### Scenario: Each environment in a multi-environment run writes its own report

- **WHEN** the `env_prepare` job runs for several environments through the fan-out
- **THEN** the job artifacts contain one `logs/<cluster>/<env>/env-prepare-report.json` per environment,
  with no cross-environment aggregation

### Requirement: EnvPrepareReport step content

The `EnvPrepareReport` SHALL list one `steps` entry per `env_prepare` step the job registers, in the job's
run order, followed by the `copy_env_artifact` step, each entry carrying `name`, `status`, and the step
`time`.

#### Scenario: A step that ran reports its status and time

- **WHEN** an `env_prepare` step runs to completion
- **THEN** its `steps` entry has `status` `SUCCESS` and a `time` field in `H:MM:SS` format

#### Scenario: A skipped step omits its time

- **WHEN** an `env_prepare` step is skipped because its precondition is not met
- **THEN** its `steps` entry has `status` `SKIPPED` and no `time` field

#### Scenario: A failed step and the steps after it

- **WHEN** an `env_prepare` step fails
- **THEN** its `steps` entry has `status` `FAILED`, and each registered step that did not run afterward
  has `status` `SKIPPED`

### Requirement: EnvPrepareReport is always published

The `EnvPrepareReport` SHALL be published on every run, independent of `METRICS_COLLECTOR_URL` and
`SAVE_ARTIFACTS_STRATEGY`, and SHALL survive the artifact size-limit trim.

#### Scenario: Published when Metrics Collector is not configured

- **WHEN** the `env_prepare` job runs with `METRICS_COLLECTOR_URL` unset
- **THEN** the job artifacts contain the environment's `env-prepare-report.json`

#### Scenario: Published when artifact saving is disabled

- **WHEN** the `env_prepare` job runs with `SAVE_ARTIFACTS_STRATEGY` set to `NEVER`
- **THEN** the job artifacts contain the environment's `env-prepare-report.json`

#### Scenario: Preserved when the artifact size limit trims the publish set

- **WHEN** the published artifacts exceed the size limit and the pipeline trims them to the `logs/` subtree
- **THEN** the job artifacts still contain the environment's `env-prepare-report.json`

### Requirement: EnvPrepareReport steps match the Metrics Collector event

WHEN Metrics Collector is configured, the `EnvPrepareReport` `steps` SHALL carry the same step results as
the Metrics Collector activity event for the same run.

#### Scenario: Report steps equal the activity event steps

- **WHEN** the `env_prepare` job runs with `METRICS_COLLECTOR_URL` set
- **THEN** the `steps` in `env-prepare-report.json` list the same step names, statuses, and times as the
  `steps` in the Metrics Collector activity event for that run
