# cert_apply

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

Import trusted certificates into the Java keystore so the Effective Set CLI can reach registries.

## Trigger

- Always.

## Inputs

| Source     | Item                               | Notes                           |
|------------|------------------------------------|---------------------------------|
| Image      | `/default_cert.pem`                | Default trusted certificate     |
| Repository | Files under `configuration/certs/` | Additional trusted certificates |

## Outputs

| Target                        | Item                  | Notes                                       |
|-------------------------------|-----------------------|---------------------------------------------|
| `/etc/ssl/certs/keystore.jks` | Imported certificates | Java keystore used by the Effective Set CLI |

## Actions

1. Read `/default_cert.pem` and each file under `configuration/certs/`.
2. Import the certificates into `/etc/ssl/certs/keystore.jks`.

## Implementation

- Path: `build_effective_set_generator/scripts/effective_set_job.py` cert handling block, and
  `scripts/utils/handle_certs.sh`.

## Backward compatibility

- Old flow: unchanged. Certificate import runs as part of the Effective Set job.
- New flow: unchanged.

## Open items

- [ ] phase2: move certificate import out of the `before_script` into an explicit step.
