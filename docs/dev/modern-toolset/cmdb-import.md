# cmdb_import

> Phase: phase1 - Change: as-is - Repo: env-generator (extend)

- [Purpose](#purpose)
- [Trigger](#trigger)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Actions](#actions)
- [Implementation](#implementation)
- [Backward compatibility](#backward-compatibility)
- [Open items](#open-items)

## Purpose

Import registries, application definitions, and tenants into CMDB.

## Trigger

- `CMDB_IMPORT` is true, in the old flow.

## Inputs

| Source    | Item                    |
|-----------|-------------------------|
| Generated | Registries              |
| Generated | Application definitions |
| Generated | Tenants                 |

## Outputs

| Target | Item             | Notes                            |
|--------|------------------|----------------------------------|
| CMDB   | Imported records | Registries, definitions, tenants |

## Actions

1. Run `null_validation`.
2. Import the definitions.

## Implementation

- Path: env-generator deploytool, using the `cmdb_format` scripts.

## Backward compatibility

- Old flow: called when `CMDB_IMPORT` is true.
- New flow: not called.

## Open items

- [ ] phase1: retained for the old flow only, not called in the new flow.
