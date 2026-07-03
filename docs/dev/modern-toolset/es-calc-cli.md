# ES Calc CLI

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

Computes the Effective Set for the pipeline, topology, deployment, and runtime contexts.

## Trigger

- `GENERATE_EFFECTIVE_SET` is true.

## Inputs

| Item                                | Notes                      |
|-------------------------------------|----------------------------|
| Rendered environment instance       |                            |
| SBOMs                               | Software bill of materials |
| Solution Descriptor or deploy plan  | Either input is accepted   |

## Outputs

| Target                              | Item                | Notes               |
|-------------------------------------|---------------------|---------------------|
| `environments/<env>/effective-set/` | Effective Set files | One set per context |

## Actions

1. Read the rendered environment instance, SBOMs, and the Solution Descriptor or deploy plan.
2. Run the Java CLI through `run-java.sh`.
3. Compute the Effective Set for the pipeline, topology, deployment, and runtime contexts.
4. Write the result under `environments/<env>/effective-set/`.

## Implementation

- Path: `qubership-envgene build_effective_set_generator/scripts/effective_set_entrypoint.py`, which runs the Java
   CLI through `run-java.sh`.

## Backward compatibility

- Old flow: unchanged.
- New flow: partial Effective Set generation scopes output to the filtered namespaces.

## Open items

- [ ] phase1: support the deploy plan as well as the Solution Descriptor as input.
