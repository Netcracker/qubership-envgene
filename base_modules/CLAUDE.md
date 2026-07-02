# base_modules — Legacy, Unused in This Branch

This directory contains only this file. On `main`, `base_modules/scripts/` held shell decrypt helpers (`decrypt.sh`, `decrypt_fernet.py`, `get_include_list.sh`, `show_validate.py`) included by other module Docker images.

In this branch that functionality was replaced by Python-native code, no shell wrapper needed:

| Old responsibility | Now lives in |
|---------------------|---------------|
| Decrypt/encrypt a credential file (Fernet or SOPS) | `envgenehelper.crypt` — `decrypt_file()`, `encrypt_file()`, backend dispatch via `crypt_backends/fernet_handler.py` and `crypt_backends/sops_handler.py` |
| CLI entry point for encrypt/decrypt/validate | `scripts/utils/crypt_manager.py` (Click CLI: `decrypt_cred_files`, `encrypt_cred_files`, `validate_creds`, `validate_parameters`) |
| Sparse checkout file list | `scripts/utils/sparse_checkout.py` |

Do not add new code here — extend `envgenehelper.crypt` or `scripts/utils/crypt_manager.py` instead.
