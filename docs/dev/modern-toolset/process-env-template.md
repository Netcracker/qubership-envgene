# process_env_template

> Phase: phase1 - Change: as-is with a bug fix - Repo: qubership-envgene (core)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Resolve and download the environment template from the registry.

## Trigger

- Always.

## Inputs

| Source         | Item                                        | Notes                                                      |
|----------------|---------------------------------------------|------------------------------------------------------------|
| Caller         | `ENV_TEMPLATE_VERSION`                      | Requested version, set earlier by env_inventory_generation |
| env_definition | `envTemplate.artifact`                      | Template artifact reference                                |
| env_definition | `envTemplate.bgNsArtifacts.origin` and peer | Blue-green namespace artifact references                   |
| Registry       | Artifact definition                         | Read via artifact_searcher                                 |

## Outputs

| Target            | Item                       | Notes                                                 |
|-------------------|----------------------------|-------------------------------------------------------|
| Working directory | Environment template files | Downloaded and unpacked                               |
| Caller            | Resolved template version  | Returned value, recorded later by app_reg_def_process |

## Actions

1. Read `envTemplate.artifact`, `envTemplate.bgNsArtifacts.origin`, and peer from env_definition.
2. Resolve the concrete version, expanding a `-SNAPSHOT` value to its timestamped form.
3. Download and unpack the template into the working directory.
4. Return the resolved version to the caller.

> [!NOTE]
> This component reads the requested version but does not write it back. The requested version is set by
> env_inventory_generation. The resolved version is recorded later by app_reg_def_process through
> update_generated_versions.

## Implementation

- Path: `qubership-envgene scripts/build_env/env_template/process_env_template.py`.
- Uses artifact_searcher.
- New resolving logic reads the deployment descriptor.
- Old resolving logic reads `configuration/registry.yml`.

## Backward compatibility

- Old flow: unchanged behaviour.
- New flow: unchanged behaviour.

## Open items

- [ ] Phase1: fix the template version setting bug.
- [ ] Phase1: when the step is split from app_reg_def_process, carry the returned resolved version to whoever
   records it.
