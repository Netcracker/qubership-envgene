# env_build

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

Renders the environment instance from the template.

## Trigger

- `ENV_BUILD` is set.

## Inputs

| Source               | Item                | Notes                        |
|----------------------|---------------------|------------------------------|
| Environment template | Template files      | Source of the instance       |
| Parameter rendering  | Rendered parameters | Values applied to the render |
| Resource profiles    | Resource profiles   | Applied during the build     |

## Outputs

| Target               | Item                  | Notes                          |
|----------------------|-----------------------|--------------------------------|
| Environment instance | Tenant                | Rendered from the template     |
| Environment instance | Cloud                 | Rendered from the template     |
| Environment instance | Namespaces            | Rendered from the template     |
| Environment instance | Blue-Green domains    | Rendered from the template     |
| Environment instance | Composite structure   | Rendered from the template     |
| Credentials          | Generated credentials | Produced by create_credentials |

## Actions

1. Render the environment instance for tenant, cloud, namespaces, Blue-Green domains, and composite structure.
2. Run create_credentials.
3. Run app_reg_def_process for the remaining appregdefs.
4. Run apply_ns_build_filter.

## Implementation

- Path: qubership-envgene scripts/build_env/main.py
   render_environment and build_environment, which call render_config_env, build_env, create_credentials, and
   apply_ns_build_filter.

## Backward compatibility

- Unchanged in phase1.

## Open items

- [ ] phase2 split the step, extracting template_macro_calc.
