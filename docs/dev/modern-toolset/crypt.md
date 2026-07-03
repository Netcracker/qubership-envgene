# crypt

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

SOPS decrypts credential files at the start of the job and encrypts them again at the end.

## Trigger

- Always.

## Inputs

| Source                | Item             | Notes                                  |
|-----------------------|------------------|----------------------------------------|
| Environment directory | Credential files | Encrypted at rest before the job runs. |

## Outputs

| Target                | Item                          | Notes                           |
|-----------------------|-------------------------------|---------------------------------|
| Environment directory | Decrypted credential files    | Available during the job.       |
| Environment directory | Re-encrypted credential files | Written before commit and push. |

## Actions

1. Decrypt all credential files for the environment at the start of the job (step 4).
2. Run the job against the decrypted files.
3. Encrypt all credential files for the environment before commit and push (step 21).

## Implementation

- Path: `qubership-envgene` `envgenehelper` functions `decrypt_all_cred_files_for_env` and
   `encrypt_all_cred_files_for_env`, called in `scripts/build_env/main.py`.
- The Effective Set image exposes the same behaviour via
   `build_effective_set_generator/scripts/crypt_manager.py` functions `decrypt_cred_files` and `encrypt_cred_files`.

## Backward compatibility

- Old flow: per-job decrypt and encrypt brackets around each job.
- New flow: one decrypt at the start and one encrypt at the end replace those brackets.

## Open items

- [ ] phase1: decide whether crypt also encrypts `ARGO_DPG_CONTEXT.env`. See argocd-repo-generator. TBD (design) how the
   sync job then decrypts it.
