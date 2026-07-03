# sbom_generation

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

Generate a per-application SBOM and merge discovered registries into the environment configuration.

## Trigger

- Applications are present, from the Solution Descriptor or the deploy plan.

## Inputs

| Source   | Item                              | Notes                                   |
|----------|-----------------------------------|-----------------------------------------|
| Pipeline | Application list                  | From Solution Descriptor or deploy plan |
| Pipeline | Downloaded deployment descriptors | Per application                         |

## Outputs

| Output                          | Notes                    |
|---------------------------------|--------------------------|
| Per-application SBOM JSON files | One file per application |
| configuration/registry.yml      | Merged registry entries  |

## Actions

1. Generate SBOMs for each application.
2. Apply the SBOM retention policy, which keeps a set number of versions per application and enforces a size limit.

## Implementation

- Path: qubership-envgene python/sbom_generator
- Path: build_effective_set_generator/scripts/sboms_retention_policy.py

## Backward compatibility

- Old flow: SBOM generation unchanged.
- New flow: SBOM generation unchanged, plus retention policy applied.

## Open items

- [ ] phase1 - support the deploy plan as well as the Solution Descriptor as input.
