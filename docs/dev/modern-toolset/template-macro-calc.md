# template_macro_calc

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

Render namespace templates and compute the deployPostfix to namespace mapping, along with the solution structure and
environments.

## Trigger

- Always. Runs as job 3, step 10 on the first pass and step 14 on the second pass.

## Inputs

| Source            | Item                       | Notes                                              |
|-------------------|----------------------------|----------------------------------------------------|
| Pipeline variable | ENV_NAME                   | Names the environment to process                   |
| Repository        | Environment template files | Rendered for the template name from env_definition |
| Repository        | env_definition             | Supplies the template name                         |

## Outputs

| Target          | Item                               | Notes                                |
|-----------------|------------------------------------|--------------------------------------|
| Downstream jobs | deployPostfix to namespace mapping | Per environment namespace            |
| Downstream jobs | Solution structure                 | Computed from the rendered templates |
| Downstream jobs | Environments                       | Computed from the rendered templates |

## Actions

1. Read the template name from env_definition.
2. Render the namespace templates for that template name.
3. Compute the deployPostfix to namespace mapping for each environment namespace.

Two passes run for this component.

- Pass one at step 10 computes the input-independent mapping needed by generate_dp.
- Pass two at step 14 recomputes the parts that depend on the processed deploy plan, scoped to the filtered namespaces.

## Implementation

- Path: to be created. To be split from render_config_env and build_env.

## Backward compatibility

- Old flow: no separate step. Namespace rendering happens inside env_build.
- New flow: a dedicated component runs namespace rendering and mapping in two passes.

## Open items

- [ ] phase1: create the function.
- [ ] phase2: render only the necessary namespaces.
- [ ] TBD (design): which macros belong to pass one versus pass two.
