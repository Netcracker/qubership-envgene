# Common Patterns and Pitfalls

## Pattern: Snapshot for Rollback Tests

When a UC requires asserting that the repository state is unchanged after a
failure, take a snapshot before the pipeline runs:

```python
@given("the repository has an initial state for rollback testing")
def repo_has_initial_state(workspace: EnvGeneWorkspace):
    import shutil
    # ... setup initial files ...
    workspace.pre_run_snapshot_dir = workspace.base_dir.parent / "snapshot"
    if workspace.pre_run_snapshot_dir.exists():
        shutil.rmtree(workspace.pre_run_snapshot_dir)
    shutil.copytree(workspace.base_dir, workspace.pre_run_snapshot_dir)

@then("the repository state is identical to the initial state")
def repo_state_identical(workspace: EnvGeneWorkspace):
    from cucumber_tests.framework.golden_compare import compare_directories
    compare_directories(
        workspace.pre_run_snapshot_dir,
        workspace.base_dir,
        ignore_patterns=["build.env", "configuration/config.yml", "*.bat", "sops"],
    )
```

## Pattern: Large File Generation

Never store large files in Git. Use sparse files at runtime:

```python
@given(parsers.parse('the SBOM directory has a total size of {size_mb:d} MB'))
def sbom_dir_has_large_size(workspace: EnvGeneWorkspace, size_mb: int):
    workspace.builder.create_mock_sboms("app-a", count=3, size_mb=size_mb)
```

## Pattern: JSON Payload as Pipeline Parameter

Many features receive their instructions as a JSON string in an environment
variable. Store it via `workspace.extra_env`:

```python
@given(parsers.parse('the ENV_INVENTORY_CONTENT specifies "{action}" for "envDefinition"'))
def pipeline_inv_content_envdef(workspace: EnvGeneWorkspace, action: str):
    env_def = {"action": action}
    if action != "delete":
        env_def["content"] = {
            "inventory": {},
            "envTemplate": {"name": "test", "artifact": "env-templates:1.0.0"},
        }
    content = {"envDefinition": env_def}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.last_payload = env_def.get("content")
```

## Pitfall: Missing `test_<feature>.py`

Without the runner file, pytest-bdd silently skips all scenarios in the
feature file. Always verify with `--collect-only` that scenarios are discovered.

## Pitfall: Duplicate Step Definitions

Importing `*` from multiple step modules can cause `AmbiguousSteDefinition`
errors if the same step text is defined in more than one module. Always check
shared_steps before implementing a new step.

## Pitfall: Credential Files with Non-Deterministic Encryption

Files encrypted with Fernet (non-deterministic keys) cannot be compared via
golden references. Pass `ignore_patterns=['Credentials']` to
`compare_directories()`.
