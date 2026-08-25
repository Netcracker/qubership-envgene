# Instance pipeline

Technical design of the Instance pipeline: the jobs and steps that `orchestrator.py` runs.

| Document                                                         | Purpose                                                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [flow](/docs/technical-design/instance-pipeline/flow.md)         | The full flow: jobs, steps, functions, and each step's trigger. Source of truth for the triggers. |
| [steps](/docs/technical-design/instance-pipeline/steps/)         | Per-step design: inputs, processing, result, and error handling, one file per step.               |
| [sub-flows](/docs/technical-design/instance-pipeline/sub-flows/) | Per-scenario projections: which steps fire for a given operation.                                 |
