# envgene-shared — Shared Utilities and Credential Crypto

Pip-installable package (`envgene_shared` — version is a setuptools formality, not published anywhere; see root `CLAUDE.md` "Python module layout"). Python 3.12+. Provides shared credential discovery, encryption/decryption, and common utilities. All other Python modules in the repository depend on this package; `envgenehelper` imports logger, YAML/file utilities, and crypto from here.

## Module Reference

### `crypto/`

| File | Responsibility |
|------|---------------|
| `crypt.py` | Encrypt/decrypt entry points: `encrypt_file`, `decrypt_file`; batch ops: `encrypt_all_cred_files_for_env`, `decrypt_all_cred_files_for_env`; `is_encrypted`, `detect_crypt_backend_from_file`, `get_all_necessary_cred_files` (respects `ENV_NAMES` for scoped discovery) |
| `fernet_handler.py` | AES-256 Fernet: `crypt_Fernet`, `is_encrypted_Fernet`, `_reuse_old_fernet_tokens` for minimize-diff |
| `sops_handler.py` | SOPS/AGE via subprocess: `crypt_SOPS`, `is_encrypted_SOPS`, `_sops_edit` trick for minimize-diff |

### `utils/`

| File | Responsibility |
|------|---------------|
| `constants.py` | Crypto and file-detection constants: `FERNET_STR`, `UNENCRYPTED_REGEX_STR` (`"^type$"` — the `type` field is never encrypted), `VALID_EXTENSIONS`, `TARGET_REGEX`, `FERNET_ID`, `SOPS_ID` |
| `crypt_utils.py` | `get_crypt()`, `get_crypt_backend()` (reads `configuration/config.yml`), `validate_crypto_requirements`, `is_empty_cred_file`, `is_effective_set_cred_file`, `analyze_cred_file` |
| `file_utils.py` | `check_file_exists`, `getRelPath`, `get_files_with_filter`, `is_cred_file` (credential file detection by name/path pattern), `writeToFile` |
| `yaml_utils.py` | YAML I/O (`openYaml`, `readYaml`, `writeYamlToFile`), schema validation (`validate_yaml_by_scheme_or_fail`, `validate_yaml_data_by_schema`), deep-access helpers (`get_or_create_nested_yaml_attribute`, `ensure_nested_attr_exists`); thread-local `yaml`/`safe_yaml` processors; `jschon.create_catalog('2020-12')` called at module import time |
| `business_utils.py` | `getenv_with_error`, `get_schema_dir` (→ `JSON_SCHEMAS_DIR` env or `/schemas`), `get_project_root` (→ `CI_PROJECT_DIR` or cwd), `get_envgene_config_yaml` |
| `collections_utils.py` | `compare_dicts` → `(diff_paths, removed_paths)`; `split_multi_value_param` (comma/semicolon/space/newline) |
| `logger.py` | Color-coded logger named `"envgene"`, level from `ENVGENE_LOG_LEVEL` |

### `schemas/`

Bundled copies of `config.schema.json` and `credential.schema.json` used for internal validation within this package (e.g., `validate_yaml_by_scheme_or_fail` in `crypt.py`). The canonical copies live in the top-level `schemas/` directory.

### `crypt_cli.py`

Click CLI (`python -m envgene_shared.crypt_cli`) with four commands: `decrypt_cred_file`, `encrypt_cred_file`, `decrypt_all`, `encrypt_all`. Options `--secret-key` / `--age-private-key` / `--age-public-key` / `--json-schemas-dir` fall back to `SECRET_KEY` / `ENVGENE_AGE_PRIVATE_KEY` / `PUBLIC_AGE_KEYS` / `JSON_SCHEMAS_DIR` env vars.

## Important Conventions

- `UNENCRYPTED_REGEX_STR = "^type$"` — the `type` key in credential files is **never encrypted**.
- `ruyaml` is used for all YAML I/O (not PyYAML) — preserves comments, round-trips safely. YAML null is rendered as `"null"` string (processor configured that way in `yaml_utils.py`).
- Parallel encryption uses `ThreadPoolExecutor`; Fernet always runs sequentially (token reuse requires ordering).

## Tests

```bash
pip install -e "modules/envgene-shared[dev]"
cd modules/envgene-shared
python -m pytest envgene_shared/tests/
```

Test files: `tests/crypto/test_crypt.py`, `tests/utils/test_collections_utils.py`, `tests/utils/test_file_utils.py`, `tests/utils/test_yaml_utils.py`.
