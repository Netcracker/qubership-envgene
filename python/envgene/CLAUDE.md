# envgenehelper — Core Python Library

Pip-installable package (`envgenehelper`, v0.0.1). Python 3.12+. All public symbols are re-exported from `__init__.py`. Imported by every other Python module in the repo.

## Module Reference

| File | Responsibility |
|------|---------------|
| `yaml_helper.py` | All YAML I/O (ruyaml), deep merge with comment preservation, schema-ordered sort (`sortYaml` → jschon-sort), JSON schema validation (`validate_yaml_by_scheme_or_fail`) |
| `business_helper.py` | Env directory navigation (`find_env_instances_dir`, `get_current_env_dir_from_env_vars`), `env_definition.yml` read/write, `NamespaceFile` / `NamespaceRole`, cloud passport lookup, BG domain helpers |
| `creds_helper.py` | Credential macro detection (`check_is_cred`), macro expansion (`expand_cred_macro_and_return_value`), credential YAML merging, `validate_creds` |
| `crypt.py` | Encrypt/decrypt entry points, credential file detection (`is_cred_file`), batch encrypt/decrypt (`encrypt_all_cred_files_for_env`) |
| `crypt_backends/fernet_handler.py` | AES-256 Fernet; `_reuse_old_fernet_tokens` for minimize-diff |
| `crypt_backends/sops_handler.py` | SOPS/AGE via subprocess; `_sops_edit` trick for minimize-diff |
| `sd_helper.py` | SD merge algorithms: `basic_merge`, `extended_merge`, `basic_exclusion_merge`; `MergeType` enum; `calculate_merge_mode` |
| `effective_set_helper.py` | `GenerationMode` (FULL/PARTIAL), `PartialMergeMode` (FORWARD/REVERSE), `resolve_es_generation_mode`, `get_es_generation_mode` |
| `config_helper.py` | Reads `configuration/config.yml`, loads regdef V1/V2 JSON schemas, auto-detects schema version |
| `env_helper.py` | `Environment` dataclass — loads inventory + credentials together |
| `errors.py` | `EnvGeneError` hierarchy — always raise typed errors, never bare exceptions. Codes format: `ENVGENE-XXXX` |
| `collections_helper.py` | `dict_merge` (None = absent, b wins), `compare_dicts` → (diff_paths, removed_paths), `split_multi_value_param` |
| `file_helper.py` | File/dir utilities, `findFiles` with pattern/regexp filters |
| `params_helper.py` | `validate_parameters` — checks for `envgeneNullValue` in deployParameters, e2eParameters, technicalConfigurationParameters |
| `deployer.py` | CMDB deployer config resolution, credential macro resolution in deployer files |
| `http_helper.py` | `ApiClient` with GET/download, raises `IntegrationError` |
| `plugin_engine/` | Plugin discovery: `IPluginRegistry` metaclass, `PluginEngine` scans `plugins_dir` for `main.py` files |
| `yaml_validator.py` | Whitelist-based structural validation (type, regexp, allowNone) |
| `models.py` | `TemplateVersionUpdateMode(StrEnum)`, `SbomRetentionConfig(BaseModel)` |
| `constants.py` | `cleanup_targets` list, `CI_JOB_ARTIFACT_MAX_SIZE_MB = 600` |
| `logger.py` | Color-coded logger named `"envgene"`, level from `ENVGENE_LOG_LEVEL` |

## Important Conventions

- `envgeneNullValue` (case-insensitive) is the sentinel for mandatory-but-unset values; `is_envgenenullvalue()` checks it.
- `ruyaml` is used everywhere (not PyYAML) — it preserves comments and round-trips safely.
- YAML null is rendered as `"null"` string (processor configured that way).
- The `type` key in credential files is **never encrypted** (`UNENCRYPTED_REGEX_STR = "^type$"`).
- `jschon.create_catalog('2020-12')` is called at module import time in `yaml_helper.py`.

## Tests

```bash
cd python/envgene
python -m pytest envgenehelper/
```
Test files: `test_collections.py`, `test_creds_helper.py`, `test_crypt.py`, `test_file_helper.py`, `test_yaml_helper.py`.
