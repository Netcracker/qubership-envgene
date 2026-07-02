# base_modules — Shared Decrypt Shell Scripts

Provides reusable shell scripts for credential file decryption that are included by other module Docker images. Not a standalone image.

## Scripts (`scripts/`)

| File | Responsibility |
|------|---------------|
| `decrypt.sh` | Decrypts a single credential file. Selects Fernet or SOPS based on `DECRYPT_TYPE` env var; constructs key variable name from `env_name` prefix |
| `decrypt_fernet.py` | Python helper called by `decrypt.sh`; Click CLI: `decrypt_cred_file --file_path --secret_key` |
| `get_include_list.sh` | Generates a list of files to include for sparse checkout |
| `show_validate.py` | Validation output helper |

## decrypt.sh Variables

| Variable | Description |
|----------|-------------|
| `env_name` | Environment name — used to build the key variable name |
| `encrypt_file_path` | Path to the file to decrypt |
| `DECRYPT_TYPE` | `fernet`, `sops`, or `none` |
| `module_fernet_key_name` | Override the Fernet key variable name (default: `CREDENTIALS_SECRET_KEY_<env_name>`) |
| `module_age_key_name` | Override the AGE key variable name (default: `AGE_SECRET_KEY_<env_name>`) |

The actual key value is read from an environment variable dynamically constructed at runtime (indirect variable expansion via `${!FERNET_KEY}`).
