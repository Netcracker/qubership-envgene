# process_sd

> Phase: phase1 - Change: as-is - Repo: qubership-envgene (core)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Process the Solution Descriptor input. This is job 3, step 12 in the pipeline.

## Trigger

- A Solution Descriptor is provided, either through `SD_SOURCE_TYPE` set to `json` with `SD_DATA`, or
   `SD_SOURCE_TYPE` set to `artifact` with `SD_VERSION`.

## Inputs

| Source   | Item             | Notes                                            |
|----------|------------------|--------------------------------------------------|
| Pipeline | `SD_SOURCE_TYPE` | Selects the input mode, `json` or `artifact`.    |
| Pipeline | `SD_DATA`        | Solution Descriptor payload for `json` mode.     |
| Pipeline | `SD_VERSION`     | Solution Descriptor version for `artifact` mode. |

## Outputs

| Target   | Item                          | Notes                    |
|----------|-------------------------------|--------------------------|
| Pipeline | Processed Solution Descriptor | Consumed by later steps. |

## Actions

1. Read the Solution Descriptor input according to `SD_SOURCE_TYPE`.
2. Process the Solution Descriptor data.

## Implementation

- Path: `qubership-envgene` `scripts/build_env/process_sd.py`.
- Old flow path: `build_pipegene/scripts/process_sd_job.py`.

## Backward compatibility

- Old flow: `process_sd_job.py` is called and performs the processing.
- New flow: with `PIPELINE_TYPE` set to `GITAB_DEPLOY` the deploy plan path is used instead, so this step is not called.

The processing itself is identical in both flows. The decision to store the Solution Descriptor is taken later in
`git_commit`.

## Open items

- [ ] phase1: not called in the new flow, called in the old flow.
