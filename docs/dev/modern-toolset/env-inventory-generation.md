# env_inventory_generation

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

Generate the EnvGene environment inventory and environment-specific parameters. It also sets the environment
template version.

## Trigger

- Inventory generation is needed, driven by `ENV_INVENTORY_CONTENT`, `ENV_SPECIFIC_PARAMS`, or `ENV_TEMPLATE_NAME`.
- Skipped in template test mode.

## Inputs

| Source   | Item                    | Notes                             |
|----------|-------------------------|-----------------------------------|
| Variable | `ENV_INVENTORY_CONTENT` | Inventory content input.          |
| Variable | `ENV_SPECIFIC_PARAMS`   | Environment-specific parameters.  |
| Variable | `ENV_TEMPLATE_NAME`     | Environment template name.        |
| Variable | `ENV_TEMPLATE_VERSION`  | Overrides `envTemplate.artifact`. |

## Outputs

| Target                         | Item                   | Notes                            |
|--------------------------------|------------------------|----------------------------------|
| `Inventory/env_definition.yml` | `envTemplate.artifact` | Set from generation or override. |

## Actions

1. Generate the environment inventory and environment-specific parameters.
2. Write `envTemplate.artifact` to `Inventory/env_definition.yml`.
3. Override `envTemplate.artifact` from `ENV_TEMPLATE_VERSION` when provided.

## Implementation

- Path: `qubership-envgene` `scripts/build_env/env_inventory_generation.py`.

## Backward compatibility

- Old flow: runs as a separate job.
- New flow: runs as a step in the single job.

## Open items

- [ ] phase2: check use-case readiness and test coverage.
