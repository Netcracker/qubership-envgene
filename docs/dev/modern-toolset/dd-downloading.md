# dd_downloading

> Phase: phase1 - Change: new - Repo: qubership-envgene (core)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Downloads deployment descriptors as input for SBOM generation and for the argocd repo generator. Runs as job 3, step 16.

## Trigger

- Applications are present in the input.

## Inputs

| Source              | Item             | Notes                     |
|---------------------|------------------|---------------------------|
| Solution Descriptor | Application list | Primary source            |
| Deploy plan         | Application list | To be supported in phase1 |

## Outputs

| Target                | Item                        | Notes        |
|-----------------------|-----------------------------|--------------|
| SBOM generation       | Deployment descriptor files | JSON and ZIP |
| argocd repo generator | Deployment descriptor files | JSON and ZIP |

## Actions

1. Read the application list from the Solution Descriptor or the deploy plan.
2. Download the deployment descriptor for each application.
3. Write the descriptors as JSON and ZIP for downstream consumers.

## Implementation

- Path: currently inside `build_effective_set_generator/scripts/effective_set_entrypoint.py`. To be separated.

## Backward compatibility

- Old flow: the download is coupled to Effective Set generation.
- New flow: the download runs as a shared input step, separated from Effective Set generation.

## Open items

- [ ] phase1: separate it from SBOM generation.
- [ ] phase1: support the deploy plan as well as the Solution Descriptor as input.
