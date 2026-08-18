# Workspace API Reference

## Key Properties

| Property | Type | Description |
|---|---|---|
| `base_dir` | `Path` | Root directory of the test workspace |
| `sboms_dir` | `Path` | `/sboms/` directory |
| `config_data` | `dict` | In-memory config (written to `config.yml` on run) |
| `stdout` | `str` | Captured stdout from last pipeline run |
| `stderr` | `str` | Captured stderr from last pipeline run |
| `returncode` | `int` | Return code from last pipeline run |
| `builder` | `DataBuilder` | Factory for creating test artifacts |
| `cluster_name` | `str` | Default: `"test-cluster"` — override via `Given environment is "<cluster>/<env>"` |
| `env_name` | `str` | Default: `"test-env"` — override via `Given environment is "<cluster>/<env>"` |
| `extra_env` | `dict` | Extra environment variables passed to pipeline subprocess |

## Key Methods

| Method | Description |
|---|---|
| `run_pipeline(extra_env)` | Execute the unified pipeline orchestrator |
| `assert_success(message)` | Assert `returncode == 0` |
| `assert_failure(message)` | Assert `returncode != 0` |
| `assert_logs_contain(text)` | Assert text in `stdout+stderr` (case-insensitive) |
| `assert_file_exists(path)` | Assert path exists |
| `assert_file_not_exists(path)` | Assert path does not exist |
| `assert_dir_deleted(path)` | Assert directory is gone |
| `get_yaml(path)` | Load and return YAML file as dict |
| `assert_yaml_content_matches(path, payload)` | Deep-compare YAML file to dict |
| `entity_dir(subdir, scope, inventory)` | Resolve entity directory by scope (`env`/`cluster`/`site`) |

## DataBuilder Methods

| Method | Description |
|---|---|
| `get_env_dir(cluster, env)` | Get (and create) environment directory path |
| `create_mock_sboms(app, count, size_mb)` | Create dummy SBOM files with distinct mtimes |
| `modify_first_sbom_size(app, size_mb)` | Inflate first SBOM file via sparse seek |
| `create_inventory_file(cluster, env, content)` | Create `env_definition.yml` |
| `create_paramset_file(place, name, content, cluster, env)` | Create paramset YAML |
| `create_credentials_file(place, name, content, cluster, env)` | Create credentials YAML |
| `create_resource_profile_file(place, name, content, cluster, env)` | Create resource profile YAML |
| `set_bg_state_files(origin_state, peer_state, cluster, env)` | Create BG state marker files |
| `create_bg_namespaces(origin_ns, peer_ns, different_content, cluster, env)` | Create BG namespace dirs |

## Entity Scope Paths

`workspace.entity_dir(subdir, scope)` resolves to:

| Scope | Path |
|---|---|
| `env` | `environments/<cluster>/<env>/Inventory/<subdir>` |
| `cluster` | `environments/<cluster>/<subdir>` |
| `site` | `environments/<subdir>` |
