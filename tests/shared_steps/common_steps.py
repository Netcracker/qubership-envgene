from pytest_bdd import given, then, when, parsers
import os
from pathlib import Path
from tests.framework.golden_compare import compare_directories

@then(parsers.parse('the pipeline log shows "{message}"'))
def pipeline_log_shows(workspace, message):
    """
    Generic step to verify that the subprocess stdout/stderr contains a specific message.
    Automatically handles cross-platform slashes and placeholder replacements.
    """
    expected = message.replace("<path>", str(workspace.base_dir)).replace('\\', '/')
    output = workspace.stdout.replace('\\', '/') + "\n" + workspace.stderr.replace('\\', '/')

    if "<application-name>" in expected:
        prefix = expected.split("<application-name>")[0]
        found = any(line.endswith(prefix) or prefix in line for line in output.splitlines())
    else:
        found = expected in output

    if not found:
        clean_msg = message.replace("<path>", "").replace('\\', '/')
        if "<application-name>" in clean_msg:
            prefix = clean_msg.split("<application-name>")[0]
            found = any(prefix in line for line in output.splitlines())
        else:
            found = clean_msg in output

    assert found, f"Expected message not found in logs: {message}\nOutput: {output}"

@given(parsers.parse('the pipeline has {param} set to "{value}"'))
def set_pipeline_param(workspace, param, value):
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
        
    # Special case: allow empty strings if value is exactly empty
    if value == "":
        workspace.extra_env[param] = ""
    else:
        workspace.extra_env[param] = value

@then('the effective set is generated successfully')
def effective_set_generated(workspace):
    assert workspace.returncode == 0, f"Pipeline failed to generate effective set. STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"

@then('the pipeline fails')
def pipeline_fails(workspace):
    assert workspace.returncode != 0, "Pipeline should have failed but returned 0"

@then(parsers.parse('the environment instance "{cluster}/{env}" matches the reference "{reference_path}"'))
def environment_matches_reference(workspace, cluster, env, reference_path):
    """
    Deep compares the generated environment directory against a golden reference.
    Runs via the external API `workspace.builder.get_env_dir` to support
    both internal and external workspace implementations.
    """
    actual_dir = workspace.builder.get_env_dir(cluster, env)
    
    # Resolve reference path relative to the test execution root (project root)
    base_expected_dir = Path.cwd() / "test_data" / "golden" / reference_path
    
    # Support both legacy flat golden directories and new nested structure
    nested_expected_dir = base_expected_dir / "environments" / cluster / env
    if nested_expected_dir.exists():
        expected_dir = nested_expected_dir
    else:
        expected_dir = base_expected_dir
    
    # Ignore Credentials directory because its files are encrypted with non-deterministic keys (Fernet)
    compare_directories(expected_dir, actual_dir, ignore_patterns=['Credentials'])

@then(parsers.parse('the workspace matches the reference "{reference_path}"'))
def workspace_matches_reference(workspace, reference_path):
    """
    Deep compares the entire workspace directory against a golden reference.
    Useful for testing root-level generated files like /appdefs and /regdefs.
    """
    actual_dir = workspace.base_dir
    expected_dir = Path.cwd() / "test_data" / "golden" / reference_path
    
    # Ignore Credentials directory because its files are encrypted with non-deterministic keys (Fernet)
    import os
    # Ignore extra framework generated files
    ignore_patterns = ['Credentials', os.path.normpath('configuration/credentials'), os.path.normpath('configuration/config.yml'), 'tmp', 'sops', 'sops.bat', os.path.normpath('configuration/registry.yml'), 'build.env', '__pycache__', 'sboms', 'inventory', 'blueprints', 'environments']
    compare_directories(expected_dir, actual_dir, ignore_patterns=ignore_patterns)

@then(parsers.parse('the generated definitions match the reference "{reference_path}"'))
def definitions_match_reference(workspace, reference_path):
    """
    Compares /appdefs and /regdefs in the workspace root against the golden reference.
    """
    actual_appdefs = workspace.base_dir / "appdefs"
    expected_appdefs = Path.cwd() / "test_data" / "golden" / reference_path / "appdefs"
    if expected_appdefs.exists():
        compare_directories(expected_appdefs, actual_appdefs)

    actual_regdefs = workspace.base_dir / "regdefs"
    expected_regdefs = Path.cwd() / "test_data" / "golden" / reference_path / "regdefs"
    if expected_regdefs.exists():
        compare_directories(expected_regdefs, actual_regdefs)
