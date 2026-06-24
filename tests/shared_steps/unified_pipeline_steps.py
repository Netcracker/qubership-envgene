from pytest_bdd import given, when, then, parsers
from tests.framework.workspace import EnvGeneWorkspace
import shutil
from pathlib import Path

@given(parsers.parse('the pipeline parameter "{param}" is set to "{value}"'))
def set_pipeline_parameter(workspace: EnvGeneWorkspace, param: str, value: str):
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
    
    # Process escaped newlines and literal quotes from the feature file
    processed_value = value.replace('\\n', '\n').replace('\\"', '"')
    workspace.extra_env[param] = processed_value

@when('the unified pipeline orchestrator runs')
def run_unified_pipeline_orchestrator(workspace: EnvGeneWorkspace):
    # Ensure extra_env is initialized
    extra_env = getattr(workspace, 'extra_env', {})
    workspace.run_pipeline(extra_env=extra_env)

@then('the orchestrator completes successfully')
def orchestrator_completes_successfully(workspace: EnvGeneWorkspace):
    assert workspace.returncode == 0, f"Unified pipeline failed with return code {workspace.returncode}.\nSTDOUT:\n{workspace.stdout}\nSTDERR:\n{workspace.stderr}"

@given(parsers.parse('the workspace is initialized with test data from "{test_data_path}"'))
def initialize_workspace_with_test_data(workspace: EnvGeneWorkspace, test_data_path: str):
    source_dir = Path("f:/project/qubership-envgene/test_data") / test_data_path
    if not source_dir.exists():
        raise FileNotFoundError(f"Test data directory {source_dir} does not exist.")
    
    # Copy all contents of the test data directory directly into the workspace base_dir
    # This simulates a workspace with predefined environments, config, etc.
    shutil.copytree(source_dir, workspace.base_dir, dirs_exist_ok=True)
