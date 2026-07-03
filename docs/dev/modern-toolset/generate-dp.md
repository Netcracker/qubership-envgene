# generate_dp

> Phase: phase1 - Change: new - Repo: env-generator (extend)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Build the deploy plan from user input.

## Trigger

- `PIPELINE_TYPE == GITAB_DEPLOY`

## Inputs

| Source     | Item                                                                                               | Notes                                         |
|------------|----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| User input | `APPLICATION_VERSION`                                                                              | Processed to download the Solution Descriptor |
| AppReg     | AppReg definitions                                                                                 | -                                             |
| Filters    | `DEPLOY_POSTFIXES_FILTER`, `NAMESPACE_NAMES_FILTER`, `COMPONENT_NAMES_FILTER`, `WAVE_NAMES_FILTER` | Applied to the deploy plan                    |

## Outputs

| Target | Item        | Notes                 |
|--------|-------------|-----------------------|
| Job    | Deploy plan | Filtered and enriched |

## Actions

1. Process `APPLICATION_VERSION` by downloading the Solution Descriptor and merging it.
2. Filter the deploy plan.
3. Enrich the deploy plan by replacing `deployPostfix` values with namespaces using the mapping from
   `template_macro_calc`.

## Implementation

- Path: to be created. Deploy plan generation moves here from `argocd-repo-generator`.

## Backward compatibility

- Old flow: not called.
- New flow: called.

## Open items

- [ ] phase1 create the function.
- [ ] phase1 move to GitHub.
- [ ] TBD (design) the deploy plan contract.
