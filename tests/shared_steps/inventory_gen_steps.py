import json
import yaml
import pytest
from pytest_bdd import scenarios, given, when, then, parsers


@given('the target environment inventory file does not exist')
def inv_does_not_exist(workspace):
    pass

@given('the target environment inventory file exists')
def inv_exists(workspace):
    workspace.builder.create_inventory_file("test-cluster", "test-env", {"envDefinition": {}})

@when(parsers.parse('the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for "envDefinition"'))
def pipeline_inv_content_envdef(workspace, action):
    env_def = {"action": action}
    if action != "delete":
        env_def["content"] = {
            "inventory": {},
            "envTemplate": {
                "name": "test",
                "artifact": "env-templates:1.0.0"
            }
        }
    content = {"envDefinition": env_def}
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.run_pipeline(extra_env=workspace.extra_env)

@then(parsers.parse('the "{filename}" file is created'))
def file_is_created(workspace, filename):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    assert (env_dir / "Inventory" / filename).exists(), f"File {filename} was not created"

@then(parsers.parse('the "{filename}" file is deleted'))
def file_is_deleted(workspace, filename):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    assert not (env_dir / "Inventory" / filename).exists(), f"File {filename} was not deleted"

@given(parsers.parse('the target paramset file "{name}" does not exist at "{scope}" scope'))
def target_paramset_not_exist(workspace, name, scope):
    base_dir = workspace.base_dir / "environments"
    if scope == "env":
        target = base_dir / "test-cluster" / "test-env" / "Inventory" / "parameters"
    elif scope == "cluster":
        target = base_dir / "test-cluster" / "Inventory" / "parameters"
    else:
        target = base_dir / "Inventory" / "parameters"
    
    file_path = target / f"{name}.yml"
    if file_path.exists():
        file_path.unlink()
    assert not file_path.exists()

@when(parsers.parse('the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for paramset "{name}" at "{scope}" scope'))
def pipeline_inv_content_paramset(workspace, action, name, scope):
    param_set = {"action": action, "place": scope}
    if action != "delete":
        param_set["content"] = {
            "name": name,
            "parameters": {}
        }
    else:
        param_set["content"] = {"name": name}
    content = {"paramSets": [param_set]}
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.run_pipeline(extra_env=workspace.extra_env)

@then(parsers.parse('the paramset file "{filename}" is created at "{scope}" scope'))
def paramset_file_created(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    if scope == "env":
        target = base_dir / "test-cluster" / "test-env" / "Inventory" / "parameters"
    elif scope == "cluster":
        target = base_dir / "test-cluster" / "Inventory" / "parameters"
    else:
        target = base_dir / "Inventory" / "parameters"
        
    assert (target / filename).exists(), f"Paramset file {filename} was not created at {scope} scope"

@given(parsers.parse('the target credentials file "{name}" does not exist at "{scope}" scope'))
def target_credentials_not_exist(workspace, name, scope):
    base_dir = workspace.base_dir / "environments"
    if scope == "env":
        target = base_dir / "test-cluster" / "test-env" / "Inventory" / "credentials"
    elif scope == "cluster":
        target = base_dir / "test-cluster" / "credentials"
    else:
        target = base_dir / "credentials"
        
    file_path = target / f"{name}.yml"
    if file_path.exists():
        file_path.unlink()
    assert not file_path.exists()

@when(parsers.parse('the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for credentials "{name}" at "{scope}" scope'))
def pipeline_inv_content_creds(workspace, action, name, scope):
    cred = {"action": action, "place": scope, "name": name}
    if action != "delete":
        cred["content"] = {
            name: {
                "type": "usernamePassword",
                "data": {
                    "username": "user",
                    "password": "password"
                }
            }
        }
    content = {"credentials": [cred]}
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.run_pipeline(extra_env=workspace.extra_env)

@then(parsers.parse('the credentials file "{filename}" is created at "{scope}" scope'))
def creds_file_created(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    if scope == "env":
        target = base_dir / "test-cluster" / "test-env" / "Inventory" / "credentials"
    elif scope == "cluster":
        target = base_dir / "test-cluster" / "credentials"
    else:
        target = base_dir / "credentials"
        
    assert (target / filename).exists(), f"Credentials file {filename} was not created at {scope} scope.\nSTDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"

@when('the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying multiple operations where one fails')
def pipeline_inv_content_fail(workspace):
    content = {
        "envDefinition": {
            "action": "create_or_replace",
            "content": {
                "inventory": {},
                "envTemplate": {
                    "name": "test",
                    "artifact": "env-templates:1.0.0"
                }
            }
        },
        "paramSets": [
            {
                "action": "invalid_action_to_fail",
                "place": "env",
                "content": {"name": "fail", "parameters": {}}
            }
        ]
    }
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.run_pipeline(extra_env=workspace.extra_env)

@then('no inventory files are created or modified')
def no_inventory_files_modified(workspace):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    assert not (env_dir / "Inventory" / "env_definition.yml").exists(), "Inventory should not have been created"
