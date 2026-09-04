"""Shared step definitions for unified pipeline orchestrator scenarios."""
from pytest_bdd import given, when, then, parsers
from cucumber_tests.framework.workspace import EnvGeneWorkspace
import shutil
from pathlib import Path
import os


@given(parsers.parse('the pipeline parameter "{param}" is set to "{value}"'))
def set_pipeline_parameter(workspace: EnvGeneWorkspace, param: str, value: str):
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}

    # Process escaped newlines and literal quotes from the feature file
    processed_value = value.replace('\\n', '\n').replace('\\"', '"')
    workspace.extra_env[param] = processed_value


@given(parsers.parse('the config parameter "{param}" is set to {value}'))
def set_config_parameter_raw(workspace: EnvGeneWorkspace, param: str, value: str):
    if value.lower() == 'true':
        val = True
    elif value.lower() == 'false':
        val = False
    elif value.isdigit():
        val = int(value)
    else:
        val = value.strip('"\'')
    workspace.config_data[param] = val


@when('the unified pipeline orchestrator runs')
def run_unified_pipeline_orchestrator(workspace: EnvGeneWorkspace):
    sops_mock = workspace.base_dir / "sops.bat"
    sops_mock.write_text("@echo off\nif \"%1\" == \"--decrypt\" (\n  type %4\n) else if \"%1\" == \"--extract\" (\n  echo extracted\n) else if \"%1\" == \"edit\" (\n  python %EDITOR% %4\n) else (\n  exit /b 0\n)\n")
    sops_sh_mock = workspace.base_dir / "sops"
    sops_sh_mock.write_text("#!/bin/sh\nif [ \"$1\" = \"--decrypt\" ]; then\n  cat \"$4\"\nelif [ \"$1\" = \"--extract\" ]; then\n  echo extracted\nelif [ \"$1\" = \"edit\" ]; then\n  python $EDITOR \"$4\"\nelse\n  exit 0\nfi\n")
    os.chmod(sops_sh_mock, 0o755)
    # Ensure extra_env is initialized
    extra_env = getattr(workspace, 'extra_env', {})
    workspace.run_pipeline(extra_env=extra_env)


@then('the orchestrator fails with return code {expected_code:d}')
def orchestrator_fails_with_return_code(workspace: EnvGeneWorkspace, expected_code: int):
    assert workspace.returncode == expected_code, f"Expected return code {expected_code}, got {workspace.returncode}.\nSTDOUT:\n{workspace.stdout}\nSTDERR:\n{workspace.stderr}"


@then('the orchestrator fails')
def orchestrator_fails(workspace: EnvGeneWorkspace):
    workspace.assert_failure("Pipeline should have failed but returned 0")


@then(parsers.parse('the pipeline log contains "{message}"'))
def pipeline_log_contains(workspace: EnvGeneWorkspace, message: str):
    workspace.assert_logs_contain(message)


@then('the orchestrator completes successfully')
def orchestrator_completes_successfully(workspace: EnvGeneWorkspace):
    workspace.assert_success("Unified pipeline failed")


@given(parsers.parse('the pipeline parameter "ENV_INVENTORY_CONTENT" is loaded from "{file_path}"'))
def set_env_inventory_content_from_file(workspace: EnvGeneWorkspace, file_path: str):
    """Read a JSON file and set its contents as ENV_INVENTORY_CONTENT.

    Args:
        file_path: Path relative to `cucumber_tests/test_data/` (e.g.
                   ``einv/env_inventory_content/uc_einv_ed_1_create.json``).
    """
    project_root = Path(os.environ.get("CI_PROJECT_DIR", Path(__file__).parent.parent.parent.resolve()))
    full_path = project_root / "cucumber_tests" / "test_data" / file_path
    if not full_path.exists():
        raise FileNotFoundError(f"ENV_INVENTORY_CONTENT file not found: {full_path}")
    content = full_path.read_text(encoding="utf-8")
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = content


@given(parsers.parse('the workspace is initialized with test data from "{test_data_path}"'))
def initialize_workspace_with_test_data(workspace: EnvGeneWorkspace, test_data_path: str):
    import yaml as _yaml
    project_root = Path(os.environ.get("CI_PROJECT_DIR", Path(__file__).parent.parent.parent.resolve()))
    source_dir = project_root / "cucumber_tests" / "test_data" / test_data_path
    if not source_dir.exists():
        raise FileNotFoundError(f"Test data directory {source_dir} does not exist.")

    # Copy all contents of the test data directory directly into the workspace base_dir
    shutil.copytree(source_dir, workspace.base_dir, dirs_exist_ok=True)

    # Workaround for legacy test_data using 'configurations' instead of 'configuration'
    legacy_config = workspace.base_dir / "configurations"
    if legacy_config.exists():
        shutil.copytree(legacy_config, workspace.base_dir / "configuration", dirs_exist_ok=True)

    # Preserve existing config.yml so write_config() merges instead of overwriting
    config_file = workspace.base_dir / "configuration" / "config.yml"
    if config_file.exists():
        loaded = _yaml.safe_load(config_file.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            workspace.config_data.update(loaded)


@given(parsers.parse('a deploy parameter "{param}" is set to "{value}" in the environment instance'))
def set_deploy_param_null(workspace: EnvGeneWorkspace, param: str, value: str):
    """Inject an envgeneNullValue into a deploy parameter of a namespace template override."""
    import yaml
    env_dir = workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name
    overrides_dir = env_dir / "Inventory" / "overrides"
    overrides_dir.mkdir(parents=True, exist_ok=True)
    override_file = overrides_dir / "deploy_params_override.yml"
    override_file.write_text(yaml.dump({"namespaces": {workspace.env_name: {"deployParameters": {param: value}}}}))


@given(parsers.parse('a credential "{cred_id}" has "{value}" for username in the environment instance'))
def set_credential_null(workspace: EnvGeneWorkspace, cred_id: str, value: str):
    """Inject an envgeneNullValue into credentials."""
    import yaml
    env_dir = workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name
    creds_dir = env_dir / "Credentials"
    creds_dir.mkdir(parents=True, exist_ok=True)
    creds_file = creds_dir / "credentials.yml"
    creds_file.write_text(yaml.dump({cred_id: {"type": "usernamePassword", "data": {"username": value, "password": value}}}))
