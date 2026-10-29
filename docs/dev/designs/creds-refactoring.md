# Creds code refactoring

- [Problem](#problem)
- [Where the creds code lives](#where-the-creds-code-lives)
- [Repeated logic](#repeated-logic)
- [Out of scope](#out-of-scope)

## Problem

Creds code spreads over six places, about 2800 lines of Python. Several places solve the same task
with their own code: parse the `${creds.get("id").field}` macro, find shared creds, walk the env
directories, and read or write YAML. A fix in one place does not reach the others.

This is a task to plan, not a settled design. Each item needs a check that the behavior is the same
before code is merged.

## Where the creds code lives

| Place | Files | Role |
|---|---|---|
| `modules/envgene-shared/envgene_shared/crypto/` | `crypt.py`, `cred_store.py`, `sops_handler.py`, `fernet_handler.py` | encryption, cred store |
| `modules/envgene-shared/envgene_shared/` | `crypt_cli.py`, `utils/crypt_utils.py` | CLI, encryption config, ES cred file rules |
| `modules/envgene/envgenehelper/` | `creds_helper.py`, `external_credential_helper.py`, `deployer.py`, `env_helper.py`, `business_helper.py` | `creds.get` macros, merge, validation, external creds |
| `scripts/build_env/` | `create_credentials.py` | env creds, shared creds |
| `scripts/creds_rotation/` | nine files | creds rotation |
| `scripts/cloud_passport/` | `main.py`, `cloud_passport.py`, `cmdb.py` | discovery creds, Cloud Passport creds |

## Repeated logic

- **Parsing the `${creds.get("id").field}` macro.** Three places use their own regular expression:
  `check_is_envgen_cred` and `get_cred_id_and_property_from_cred_macros` in `creds_helper.py`, `pattern` in
  `scripts/creds_rotation/utils/cred_utils.py`, and `SECRET_PATTERN` with `convert_secret` in
  `scripts/cloud_passport/main.py`. The rotation pattern accepts only `username`, `password`, and `secret`.
- **Finding shared creds by `sharedMasterCredentialFiles`.** `findSharedCredentials` in `create_credentials.py`
  and `scan_dir_for_creds` with `read_shared_cred_files` in `scripts/creds_rotation/utils/cred_utils.py`.
- **Walking env directories and reading YAML.** Creds rotation has its own `scandir_recursive`, an async YAML
  reader, and `write_yaml_to_file` on PyYAML. The shared modules have `findAllYamlsInDir`, `openYaml`, and
  `writeYamlToFile` on ruyaml. The output of the two writers differs.
- **Two encryption APIs in `crypt.py`.** The file API (`encrypt_file`, `decrypt_file`, `crypt_SOPS` with
  `in_place`) serves only `crypt_cli` and the pre-commit hook. The bytes API
  (`encrypt_bytes`, `decrypt_bytes`) serves the cred store. The file API can be a thin layer over the bytes API.

## Out of scope

- `getEnvCredentials` in `business_helper.py`. The repository code does not call it. The CMDB import plugin
  may call it. Check the plugin first.
- The Effective Set Calculator CLI in Java.
