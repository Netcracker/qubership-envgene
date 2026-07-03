# null_validation

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

Fail fast when any `envgeneNullValue` remains unset in credentials or parameters, before the Effective Set CLI runs.

## Trigger

- Always, before the Effective Set CLI.

## Inputs

| Source           | Item               | Notes                         |
|------------------|--------------------|-------------------------------|
| Credential files | Credential entries | Checked for unset values      |
| Tenant object    | Parameters         | Source of parameters to check |
| Cloud object     | Parameters         | Source of parameters to check |
| Namespace object | Parameters         | Source of parameters to check |

## Outputs

| Target       | Item              | Notes                                      |
|--------------|-------------------|--------------------------------------------|
| Pipeline job | Validation result | The job fails when an unset value is found |

## Actions

1. Validate credentials for unset `username`, `password`, `secret`, or `secretId`.
2. Validate `deployParameters`, `e2eParameters`, and `technicalConfigurationParameters` in the tenant, cloud, and
   namespaces for unset values.

## Implementation

- Path: qubership-envgene `envgenehelper` `creds_helper.validate_creds` and `params_helper.validate_parameters`, exposed
   through `crypt_manager.py`.

## Backward compatibility

- Old flow: two separate calls inside the Effective Set job.
- New flow: one grouped step that also runs in `cmdb_import`.

## Open items

- [ ] phase1: confirm the step is present and covers both credentials and parameters.
