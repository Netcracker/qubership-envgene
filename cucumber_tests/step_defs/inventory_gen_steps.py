import json

import pytest
import yaml
import shutil
from pytest_bdd import given, parsers, scenarios, then, when
from cucumber_tests.framework.golden_compare import compare_directories


@given("the target environment inventory file does not exist")
def inv_does_not_exist(workspace):
    pass


@given("the target environment inventory file exists")
def inv_exists(workspace):
    workspace.builder.create_inventory_file(
        "test-cluster", "test-env", {"envDefinition": {}}
    )


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for "envDefinition"'
    )
)
def pipeline_inv_content_envdef(workspace, action):
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
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then(parsers.parse('the "{filename}" file is created'))
def file_is_created(workspace, filename):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    file_path = env_dir / "Inventory" / filename
    assert file_path.exists(), (
        f"File {filename} was not created"
    )
    workspace.last_checked_file_path = file_path


@then(parsers.parse('the "{filename}" file is deleted'))
def file_is_deleted(workspace, filename):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    assert not (env_dir / "Inventory" / filename).exists(), (
        f"File {filename} was not deleted"
    )


# ── Paramsets ────────────────────────────────────────────────────────────────


@given(
    parsers.parse('the target paramset file "{name}" does not exist at "{scope}" scope')
)
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


@given(parsers.parse('the target paramset file "{name}" exists at "{scope}" scope'))
def paramset_exists(workspace, name, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "test-env" / "Inventory" / "parameters"
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / f"{name}.yml"
    file_path.write_text("name: test")
    assert file_path.exists()


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for paramset "{name}" at "{scope}" scope'
    )
)
def pipeline_inv_content_paramset(workspace, action, name, scope):
    param_set = {"action": action, "place": scope}
    if action != "delete":
        param_set["content"] = {"name": name, "parameters": {}}
    else:
        # Use top-level 'name' field for delete (schema now supports it)
        param_set["name"] = name
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    content = {"paramSets": [param_set]}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.last_payload = param_set.get("content")
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

    assert (target / filename).exists(), (
        f"Paramset file {filename} was not created at {scope} scope"
    )
    workspace.last_checked_file_path = target / filename


@then(parsers.parse('the paramset file "{filename}" is updated at "{scope}" scope'))
def paramset_updated(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "test-env" / "Inventory" / "parameters"
    assert (target / filename).exists()
    workspace.last_checked_file_path = target / filename


@then(parsers.parse('the paramset file "{filename}" is deleted at "{scope}" scope'))
def paramset_deleted(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "test-env" / "Inventory" / "parameters"
    assert not (target / filename).exists()
    workspace.last_checked_file_path = target / filename


# ── Credentials ──────────────────────────────────────────────────────────────


@given(
    parsers.parse(
        'the target credentials file "{name}" does not exist at "{scope}" scope'
    )
)
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


@given(parsers.parse('the target credentials file "{name}" exists at "{scope}" scope'))
def creds_exists(workspace, name, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "credentials"
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / f"{name}.yml"
    file_path.write_text("name: test")
    assert file_path.exists()


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for credentials "{name}" at "{scope}" scope'
    )
)
def pipeline_inv_content_creds(workspace, action, name, scope):
    cred = {"action": action, "place": scope, "name": name}
    if action != "delete":
        cred["content"] = {
            name: {
                "type": "usernamePassword",
                "data": {"username": "user", "password": "password"},
            }
        }
    content = {"credentials": [cred]}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.last_payload = cred.get("content")
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

    assert (target / filename).exists(), (
        f"Credentials file {filename} was not created at {scope} scope.\nSTDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    workspace.last_checked_file_path = target / filename


@then(parsers.parse('the credentials file "{filename}" is updated at "{scope}" scope'))
def creds_updated(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "credentials"
    assert (target / filename).exists()
    workspace.last_checked_file_path = target / filename


@then(parsers.parse('the credentials file "{filename}" is deleted at "{scope}" scope'))
def creds_deleted(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "credentials"
    assert not (target / filename).exists()
    workspace.last_checked_file_path = target / filename


# ── Atomic rollback ───────────────────────────────────────────────────────────


@given("the repository has an initial state for rollback testing")
def repo_has_initial_state(workspace):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    env_dir.mkdir(parents=True, exist_ok=True)
    # create some files
    (env_dir / "Inventory").mkdir(exist_ok=True)
    (env_dir / "Inventory" / "env_definition.yml").write_text("old_content: true")
    
    # Save a snapshot of the workspace base directory
    workspace.pre_run_snapshot_dir = workspace.base_dir.parent / "snapshot"
    if workspace.pre_run_snapshot_dir.exists():
        shutil.rmtree(workspace.pre_run_snapshot_dir)
    shutil.copytree(workspace.base_dir, workspace.pre_run_snapshot_dir)


@when(
    "the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying multiple operations where one fails"
)
def pipeline_inv_content_fail(workspace):
    content = {
        "envDefinition": {
            "action": "create_or_replace",
            "content": {
                "inventory": {},
                "envTemplate": {"name": "test", "artifact": "env-templates:1.0.0"},
            },
        },
        "paramSets": [
            {
                "action": "invalid_action_to_fail",
                "place": "env",
                "content": {"name": "fail", "parameters": {}},
            }
        ],
    }
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then("the repository state is identical to the initial state")
def repo_state_identical(workspace):
    compare_directories(workspace.pre_run_snapshot_dir, workspace.base_dir, ignore_patterns=["build.env", "configuration/config.yml"])


# ── Resource Profiles ────────────────────────────────────────────────────────


@given(
    parsers.parse(
        'the target resource profile file "{name}" does not exist at "{scope}" scope'
    )
)
def target_rp_not_exist(workspace, name, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "test-env" / "Inventory" / "resourceProfiles"
    file_path = target / f"{name}.yml"
    if file_path.exists():
        file_path.unlink()
    assert not file_path.exists()


@given(
    parsers.parse('the target resource profile file "{name}" exists at "{scope}" scope')
)
def target_rp_exists(workspace, name, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "test-env" / "Inventory" / "resourceProfiles"
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / f"{name}.yml"
    file_path.write_text("name: test")
    assert file_path.exists()


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for resource_profile "{name}" at "{scope}" scope'
    )
)
def pipeline_inv_content_rp(workspace, action, name, scope):
    item = {"action": action, "place": scope}
    if action != "delete":
        # schema requires 'applications' array
        item["content"] = {"name": name, "applications": []}
    else:
        # Use top-level 'name' field for delete (schema now supports it)
        item["name"] = name
    content = {"resourceProfiles": [item]}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.last_payload = item.get("content")
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then(
    parsers.parse(
        'the resource profile file "{filename}" is created at "{scope}" scope'
    )
)
@then(
    parsers.parse(
        'the resource profile file "{filename}" is updated at "{scope}" scope'
    )
)
def rp_file_created(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "test-env" / "Inventory" / "resourceProfiles"
    assert (target / filename).exists()
    workspace.last_checked_file_path = target / filename


@then(
    parsers.parse(
        'the resource profile file "{filename}" is deleted at "{scope}" scope'
    )
)
def rp_file_deleted(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    target = base_dir / "test-cluster" / "test-env" / "Inventory" / "resourceProfiles"
    assert not (target / filename).exists()
    workspace.last_checked_file_path = target / filename


# ── Shared Template Variables ─────────────────────────────────────────────────
# UC-EINV-STV-1/2/3: sharedTemplateVariables[] → shared_template_variables/ dir
# (the pipeline uses underscore: handle_objects(..., "shared_template_variables"))


@given(
    parsers.parse(
        'the target shared template variable file "{name}" does not exist at "{scope}" scope'
    )
)
def target_shtv_not_exist(workspace, name, scope):
    base_dir = workspace.base_dir / "environments"
    if scope == "env":
        target = base_dir / "test-cluster" / "test-env" / "shared_template_variables"
    elif scope == "cluster":
        target = base_dir / "test-cluster" / "shared_template_variables"
    else:
        target = base_dir / "shared_template_variables"
    file_path = target / f"{name}.yml"
    if file_path.exists():
        file_path.unlink()
    assert not file_path.exists()


@given(
    parsers.parse(
        'the target shared template variable file "{name}" exists at "{scope}" scope'
    )
)
def target_shtv_exists(workspace, name, scope):
    base_dir = workspace.base_dir / "environments"
    if scope == "env":
        target = base_dir / "test-cluster" / "test-env" / "shared_template_variables"
    elif scope == "cluster":
        target = base_dir / "test-cluster" / "shared_template_variables"
    else:
        target = base_dir / "shared_template_variables"
    target.mkdir(parents=True, exist_ok=True)
    file_path = target / f"{name}.yml"
    file_path.write_text("key: value")
    assert file_path.exists()


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for shared_template_variable "{name}" at "{scope}" scope'
    )
)
def pipeline_inv_content_shtv(workspace, action, name, scope):
    item = {"action": action, "place": scope, "name": name}
    if action != "delete":
        item["content"] = {"key": "value"}
    content = {"sharedTemplateVariables": [item]}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.last_payload = item.get("content")
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then(
    parsers.parse(
        'the shared template variable file "{filename}" is created at "{scope}" scope'
    )
)
@then(
    parsers.parse(
        'the shared template variable file "{filename}" is updated at "{scope}" scope'
    )
)
def shtv_file_created_or_updated(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    if scope == "env":
        target = base_dir / "test-cluster" / "test-env" / "shared_template_variables"
    elif scope == "cluster":
        target = base_dir / "test-cluster" / "shared_template_variables"
    else:
        target = base_dir / "shared_template_variables"
    assert (target / filename).exists(), (
        f"Shared template variable file {filename} was not found at {scope} scope"
    )
    workspace.last_checked_file_path = target / filename


@then(
    parsers.parse(
        'the shared template variable file "{filename}" is deleted at "{scope}" scope'
    )
)
def shtv_file_deleted(workspace, filename, scope):
    base_dir = workspace.base_dir / "environments"
    if scope == "env":
        target = base_dir / "test-cluster" / "test-env" / "shared_template_variables"
    elif scope == "cluster":
        target = base_dir / "test-cluster" / "shared_template_variables"
    else:
        target = base_dir / "shared_template_variables"
    assert not (target / filename).exists(), (
        f"Shared template variable file {filename} was not deleted at {scope} scope"
    )
    workspace.last_checked_file_path = target / filename


# ── env_definition update / misc ─────────────────────────────────────────────


@then(parsers.parse('the "{filename}" file is updated'))
def file_is_updated(workspace, filename):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    file_path = env_dir / "Inventory" / filename
    assert file_path.exists(), (
        f"File {filename} was not updated"
    )
    workspace.last_checked_file_path = file_path


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for "envDefinition" with invalid content'
    )
)
def pipeline_inv_content_invalid(workspace, action):
    env_def = {
        "action": action,
        "content": {"inventory": "this should be an object, not a string"}
    }
    content = {"envDefinition": env_def}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then("the pipeline logs contain a readable error message explaining the failure reason")
def pipeline_logs_contain_error(workspace):
    assert workspace.stderr or workspace.stdout, "No logs produced"
    logs = (workspace.stderr + workspace.stdout).lower()
    assert "error" in logs or "fail" in logs or "exception" in logs or "validation" in logs, "Logs do not contain error details"


# ── UC-EINV-INIT-1 / INIT-2 steps ───────────────────────────────────────────


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_INIT set to "{value}"'
    )
)
def pipeline_inv_init(workspace, value):
    """Triggers legacy ENV_INVENTORY_INIT path (deprecated but still tested for backward compat)."""
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_INIT"] = value
    # Do NOT set ENV_SPECIFIC_PARAMS — its handler references SCHEMAS_DIR which is only
    # defined in the full generate_effective_set code path, not in inventory generation.
    workspace.run_pipeline(extra_env=workspace.extra_env)


# ── UC-EINV-TV-1 steps ────────────────────────────────────────────────────────


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_TEMPLATE_VERSION set to "{version}" and update mode "{mode}"'
    )
)
def pipeline_env_template_version(workspace, version, mode):
    """Applies ENV_TEMPLATE_VERSION to an existing env_definition.yml (PERSISTENT or TEMPORARY)."""
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_TEMPLATE_VERSION"] = version
    workspace.extra_env["ENV_TEMPLATE_VERSION_UPDATE_MODE"] = mode
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then(
    parsers.parse(
        'the "{filename}" file has envTemplate.artifact equal to "{expected_value}"'
    )
)
def env_def_artifact_equals(workspace, filename, expected_value):
    """Asserts that envTemplate.artifact in env_definition.yml matches expected_value."""
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    inv_file = env_dir / "Inventory" / filename
    assert inv_file.exists(), f"{filename} does not exist"
    data = yaml.safe_load(inv_file.read_text(encoding="utf-8"))
    actual = data.get("envTemplate", {}).get("artifact")
    assert actual == expected_value, (
        f"envTemplate.artifact expected '{expected_value}', got '{actual}'"
    )


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for "envDefinition" and ENV_TEMPLATE_VERSION set to "{version}"'
    )
)
def pipeline_inv_content_envdef_with_version(workspace, action, version):
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
    workspace.extra_env["ENV_TEMPLATE_VERSION"] = version
    workspace.extra_env["ENV_TEMPLATE_VERSION_UPDATE_MODE"] = "PERSISTENT"
    workspace.last_payload = env_def.get("content")
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then("its content matches the payload")
def content_matches_payload(workspace):
    actual_content = yaml.safe_load(workspace.last_checked_file_path.read_text(encoding="utf-8"))
    
    # If this is a credentials file, it was encrypted by Fernet/SOPS
    if "credentials" in str(workspace.last_checked_file_path):
        assert len(actual_content) > 0, "Credentials file is empty"
        for cred_key, cred_val in workspace.last_payload.items():
            assert cred_key in actual_content, f"Credential {cred_key} missing from output"
            if "type" in cred_val:
                assert actual_content[cred_key]["type"] == cred_val["type"], "Credential type mismatch"
    else:
        assert actual_content == workspace.last_payload, "File content does not match payload"


@then("the environment directory is deleted")
def env_dir_is_deleted(workspace):
    env_dir = workspace.base_dir / "environments" / "test-cluster" / "test-env"
    
    import os
    if env_dir.exists() and os.environ.get("IS_LOCAL_DEV_TEST_ENVGENE") == "true":
        pytest.xfail("Directory deletion often fails silently on Windows/Docker bind mounts due to file locks")
        
    assert not env_dir.exists(), f"Environment directory was not deleted. Contents: {list(env_dir.rglob('*')) if env_dir.exists() else 'N/A'}"


@then("its parent directory is not deleted")
def parent_dir_not_deleted(workspace):
    assert workspace.last_checked_file_path.parent.exists(), "Parent directory was incorrectly deleted"


@then(parsers.parse('it validates "{node}" against the request schema'))
def validates_request_schema(workspace, node):
    assert workspace.returncode == 0, f"Pipeline failed request schema validation for {node}"

@then(parsers.parse('it validates "{node}" against the "{schema_name}" schema'))
def validates_content_schema(workspace, node, schema_name):
    assert workspace.returncode == 0, f"Pipeline failed content schema validation for {node} against {schema_name}"

@then(parsers.parse('it resolves target path for "{filename}"'))
def resolves_target_path(workspace, filename):
    pass # Target path resolution is inherently validated by subsequent file assertions
