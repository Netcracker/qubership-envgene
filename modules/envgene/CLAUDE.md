# envgenehelper — Core Python Library

Pip-installable package (`envgenehelper`, v0.0.1 — version is a setuptools formality, not published anywhere; see root `CLAUDE.md` "Python module layout"). Python 3.12+. All public symbols are reexported from `__init__.py`. Imported by every other Python module in the repository. Depends on `envgene-shared` (`envgene_shared` package) for logger, YAML/file utilities, collections utilities, and credential crypto — see `modules/envgene-shared/CLAUDE.md`.

## Module Reference

| File | Responsibility |
|------|---------------|
| `yaml_helper.py` | All YAML I/O (ruyaml), deep merge with comment preservation, schema-ordered sort (`sortYaml` → `jschon_tools.process_json_doc`, an external pip dependency in this branch, not a local package), JSON schema validation (`validate_yaml_by_scheme_or_fail`) |
| `business_helper.py` | Env directory navigation (`find_env_instances_dir`, `get_current_env_dir_from_env_vars`), `env_definition.yml` read/write, `NamespaceFile` / `NamespaceRole`, cloud passport lookup, BG domain helpers |
| `creds_helper.py` | Credential macro detection (`check_is_cred`), macro expansion (`expand_cred_macro_and_return_value`), credential YAML merging, `validate_creds` |
| `sd_helper.py` | SD merge algorithms: `basic_merge`, `extended_merge`, `basic_exclusion_merge`; `MergeType` enum; `calculate_merge_mode` |
| `effective_set_helper.py` | `GenerationMode` (FULL/PARTIAL), `PartialMergeMode` (FORWARD/REVERSE), `resolve_es_generation_mode`, `get_es_generation_mode` |
| `config_helper.py` | Reads `configuration/config.yml`, loads regdef V1/V2 JSON schemas, auto-detects schema version |
| `env_helper.py` | `Environment` dataclass — loads inventory + credentials together |
| `errors.py` | `EnvGeneError` hierarchy — always raise typed errors, never bare exceptions. Codes format: `ENVGENE-XXXX` |
| `collections_helper.py` | `dict_merge` (None = absent, b wins), `compare_dicts` → (diff_paths, removed_paths), `split_multi_value_param` |
| `file_helper.py` | File/dir utilities, `findFiles` with pattern/regular expression filters |
| `params_helper.py` | `validate_parameters` — checks for `envgeneNullValue` in deployParameters, e2eParameters, technicalConfigurationParameters |
| `deployer.py` | CMDB deployer config resolution, credential macro resolution in deployer files |
| `http_helper.py` | `ApiClient` with GET/download, raises `IntegrationError` |
| `git_helper.py` | `GitRepoManager` — `sparse_checkout(paths, fetch=True)`, configure/stage/detached-commit/cherry-pick+push via GitPython; `GitContext` (platform detection from env); `GitLabClient` (pipeline jobs, artifact download, project variables) |
| `repo_paths.py` | `REPO_ROOT_PATHS`, `get_env_artifact_paths()`, `get_shared_entity_paths()`, `get_sparse_checkout_paths()` — path whitelists used by `GitRepoManager.sparse_checkout` / `stage_changes` |
| `retry/` | Generic retry helper: `RetryPolicy`, `retry_call`, `parse_duration`, `Duration`; `GIT_RETRY_POLICY` (10 attempts, exponential backoff) used by `git_helper.py` |
| `plugin_engine/` | Plugin discovery: `IPluginRegistry` metaclass, `PluginEngine` scans `plugins_dir` for `main.py` files |
| `yaml_validator.py` | Whitelist-based structural validation (type, regular expression, allowNone) |
| `models.py` | `TemplateVersionUpdateMode(StrEnum)`, `SbomRetentionConfig(BaseModel)` |
| `constants.py` | `cleanup_targets` list, `CI_JOB_ARTIFACT_MAX_SIZE_MB = 600` |

## Important Conventions

- `envgeneNullValue` (case-insensitive) is the sentinel for mandatory-but-unset values; `is_envgenenullvalue()` checks it.
- `ruyaml` is used everywhere (not PyYAML) — it preserves comments and round-trips safely. YAML null is rendered as `"null"` string; the thread-local processor and `jschon.create_catalog('2020-12')` call are defined in `envgene_shared.utils.yaml_utils` and re-exported by `yaml_helper.py`.
- Credential file conventions (`UNENCRYPTED_REGEX_STR`, `is_cred_file`) live in `envgene_shared.utils.constants` / `envgene_shared.utils.file_utils` — see `modules/envgene-shared/CLAUDE.md`.

## Tests

```bash
pip install -e modules/envgene
cd modules/envgene
python -m pytest envgenehelper/
```

Test files: `test_creds_helper.py`, `test_deploy_plan_adapter.py`, `test_effective_set_helper.py`, `test_file_helper.py`, `test_git_helper.py`, `test_repo_paths.py`. (Tests for collections, crypt, and YAML utilities moved to `modules/envgene-shared`.)
