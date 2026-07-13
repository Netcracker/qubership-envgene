import json
import os

import pytest
import yaml
import shutil
from pathlib import Path
from pytest_bdd import given, parsers, then, when

from cucumber_tests.framework.workspace import (
    TEST_ENV_DEFINITION_CONTENT,
    TEST_YAML_CONTENT,
    create_file,
    delete_file_if_exists,
)
from cucumber_tests.framework.golden_compare import compare_directories


# Entity -> (subdirectory, has_inventory_folder)
# has_inventory_folder=True means env scope puts files under .../Inventory/<subdir>
_ENTITY_DIRS = {
    "paramset":                 ("parameters",               True),
    "credentials":              ("credentials",              True),
    "resource_profile":         ("resource_profiles",        True),
    "shared_template_variable": ("shared_template_variables", False),
}


def _entity_dir(workspace, entity: str, scope: str) -> "Path":
    """Return the target directory for *entity* at *scope* using workspace.entity_dir()."""
    subdir, has_inv = _ENTITY_DIRS[entity]
    if scope == "env" and has_inv:
        return workspace.entity_dir(subdir, scope, inventory="Inventory")
    elif scope == "env":
        return workspace.entity_dir(subdir, scope, inventory="")
    else:
        return workspace.entity_dir(subdir, scope)


# ── Environment/cluster context setup ────────────────────────────────────────


@given(parsers.parse('environment is "{cluster}/{env}"'))
def set_environment(workspace, cluster, env):
    """Override default cluster/env names for this scenario."""
    workspace.cluster_name = cluster
    workspace.env_name = env


# ── env_definition.yml ────────────────────────────────────────────────────────


@given("the target environment inventory file does not exist")
def inv_does_not_exist(workspace):
    pass


@given("the target environment inventory file exists")
def inv_exists(workspace):
    inv_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name) / "Inventory"
    inv_dir.mkdir(parents=True, exist_ok=True)
    
    data_path = Path(__file__).parent.parent / "test_data" / "einv" / "env_definition.yml"
    if data_path.exists():
        content = data_path.read_text(encoding="utf-8")
    else:
        content = TEST_ENV_DEFINITION_CONTENT
        
    (inv_dir / "env_definition.yml").write_text(content, encoding="utf-8")


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
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    file_path = env_dir / "Inventory" / filename
    assert file_path.exists(), f"File {filename} was not created"
    workspace.last_checked_file_path = file_path


@then(parsers.parse('the "{filename}" file is updated'))
def file_is_updated(workspace, filename):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    file_path = env_dir / "Inventory" / filename
    assert file_path.exists(), f"File {filename} was not updated (does not exist)"
    workspace.last_checked_file_path = file_path


@then(parsers.parse('the "{filename}" file is deleted'))
def file_is_deleted(workspace, filename):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    assert not (env_dir / "Inventory" / filename).exists(), f"File {filename} was not deleted"


# ── Generic entity steps (paramsets, credentials, resource_profiles, shtv) ───


@given(
    parsers.parse(
        'the target {entity} file "{name}" does not exist at "{scope}" scope'
    )
)
def target_entity_not_exist(workspace, entity, name, scope):
    """Ensure entity file is absent before test."""
    path = _entity_dir(workspace, entity, scope) / f"{name}.yml"
    delete_file_if_exists(path)


@given(
    parsers.parse(
        'the target {entity} file "{name}" exists at "{scope}" scope'
    )
)
def target_entity_exists(workspace, entity, name, scope):
    """Ensure entity file is present before test."""
    path = _entity_dir(workspace, entity, scope) / f"{name}.yml"
    subdir, _ = _ENTITY_DIRS[entity]
    
    data_path = Path(__file__).parent.parent / "test_data" / "einv" / subdir / f"{name}.yml"
    if data_path.exists():
        content = data_path.read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    else:
        create_file(path)


@then(
    parsers.parse(
        'the {entity} file "{filename}" is created at "{scope}" scope'
    )
)
@then(
    parsers.parse(
        'the {entity} file "{filename}" is updated at "{scope}" scope'
    )
)
def entity_file_exists(workspace, entity, filename, scope):
    path = _entity_dir(workspace, entity, scope) / filename
    assert path.exists(), (
        f"{entity} file {filename} was not found at {scope} scope.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    workspace.last_checked_file_path = path


@then(
    parsers.parse(
        'the {entity} file "{filename}" is deleted at "{scope}" scope'
    )
)
def entity_file_deleted(workspace, entity, filename, scope):
    path = _entity_dir(workspace, entity, scope) / filename
    assert not path.exists(), (
        f"{entity} file {filename} was NOT deleted at {scope} scope.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    workspace.last_checked_file_path = path


# ── Per-entity pipeline When-steps ────────────────────────────────────────────


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
        param_set["name"] = name
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps({"paramSets": [param_set]})
    workspace.last_payload = param_set.get("content")
    workspace.run_pipeline(extra_env=workspace.extra_env)


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
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps({"credentials": [cred]})
    workspace.last_payload = cred.get("content")
    workspace.run_pipeline(extra_env=workspace.extra_env)


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for resource_profile "{name}" at "{scope}" scope'
    )
)
def pipeline_inv_content_rp(workspace, action, name, scope):
    item = {"action": action, "place": scope}
    if action != "delete":
        item["content"] = {"name": name, "applications": []}
    else:
        item["name"] = name
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps({"resourceProfiles": [item]})
    workspace.last_payload = item.get("content")
    workspace.run_pipeline(extra_env=workspace.extra_env)


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for shared_template_variable "{name}" at "{scope}" scope'
    )
)
def pipeline_inv_content_shtv(workspace, action, name, scope):
    item = {"action": action, "place": scope, "name": name}
    if action != "delete":
        item["content"] = {"key": "value"}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps({"sharedTemplateVariables": [item]})
    workspace.last_payload = item.get("content")
    workspace.run_pipeline(extra_env=workspace.extra_env)


# ── Atomic rollback ───────────────────────────────────────────────────────────


@given("the repository has an initial state for rollback testing")
def repo_has_initial_state(workspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    (env_dir / "Inventory").mkdir(exist_ok=True)
    create_file(env_dir / "Inventory" / "env_definition.yml", TEST_ENV_DEFINITION_CONTENT)

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
    compare_directories(
        workspace.pre_run_snapshot_dir,
        workspace.base_dir,
        ignore_patterns=["build.env", "configuration/config.yml", "*.bat"],
    )


# ── UC-EINV-INIT steps ────────────────────────────────────────────────────────


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
    workspace.run_pipeline(extra_env=workspace.extra_env)


# ── UC-EINV-BASIC-1 steps ─────────────────────────────────────────────────────


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for "envDefinition" with minimal content'
    )
)
def pipeline_inv_content_envdef_minimal(workspace, action):
    """Creates env_definition.yml with only the mandatory inventory + envTemplate fields."""
    env_def = {
        "action": action,
        "content": {
            "inventory": {
                "environmentName": workspace.env_name,
                "cloudName": workspace.cluster_name,
            },
            "envTemplate": {
                "name": "test",
                "artifact": "project-env-template:v1.2.3",
            },
        },
    }
    content = {"envDefinition": env_def}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.last_payload = env_def.get("content")
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then("the generated env_definition contains minimal required fields")
def env_definition_has_required_fields(workspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    inv_file = env_dir / "Inventory" / "env_definition.yml"
    assert inv_file.exists(), "env_definition.yml does not exist"
    data = yaml.safe_load(inv_file.read_text(encoding="utf-8"))
    assert "inventory" in data, "Missing 'inventory' key"
    assert "envTemplate" in data, "Missing 'envTemplate' key"


# ── UC-EINV-TV steps ──────────────────────────────────────────────────────────


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


# ── Invalid content ───────────────────────────────────────────────────────────


@when(
    parsers.parse(
        'the Instance pipeline is started with ENV_INVENTORY_CONTENT specifying "{action}" for "envDefinition" with invalid content'
    )
)
def pipeline_inv_content_invalid(workspace, action):
    env_def = {
        "action": action,
        "content": {"inventory": "this should be an object, not a string"},
    }
    content = {"envDefinition": env_def}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.run_pipeline(extra_env=workspace.extra_env)


@then("the pipeline logs contain a readable error message explaining the failure reason")
def pipeline_logs_contain_error(workspace):
    workspace.assert_logs_contain("Validation failed")


@then(parsers.parse('the pipeline logs contain "{text}"'))
def pipeline_logs_contain_text(workspace, text):
    workspace.assert_logs_contain(text)


# ── Shared assertions ─────────────────────────────────────────────────────────


@then("its content matches the payload")
def content_matches_payload(workspace):
    workspace.assert_yaml_content_matches(workspace.last_checked_file_path, workspace.last_payload)


@then("the environment directory is deleted")
def env_dir_is_deleted(workspace):
    env_dir = workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name
    if env_dir.exists():
        contents = list(env_dir.rglob('*'))
        assert not contents, f"Directory {env_dir} was not deleted and is not empty. Contents: {contents}"


@then("its parent directory is not deleted")
def parent_dir_not_deleted(workspace):
    workspace.assert_file_exists(workspace.last_checked_file_path.parent)


@then("the pipeline succeeds")
def pipeline_succeeds(workspace):
    workspace.assert_success()


@then(parsers.parse('it validates "{node}" against the request schema'))
def validates_request_schema(workspace, node):
    workspace.assert_success(f"Pipeline failed request schema validation for {node}")


@then(parsers.parse('it validates "{node}" against the "{schema_name}" schema'))
def validates_content_schema(workspace, node, schema_name):
    workspace.assert_success(f"Pipeline failed content schema validation for {node} against {schema_name}")


# ── Template Version Update (TV-1) ──────────────────────────────────────────────

@when(parsers.parse('the Instance pipeline is started with ENV_TEMPLATE_VERSION set to "{version}" and update mode "{mode}"'))
def pipeline_env_template_version(workspace, version, mode):
    env_def = {"action": "create_or_replace"}
    env_def["content"] = {
        "inventory": {},
        "envTemplate": {"name": "test", "artifact": "env-templates:1.0.0"},
    }
    content = {"envDefinition": env_def}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.extra_env["ENV_TEMPLATE_VERSION"] = version
    workspace.extra_env["ENV_TEMPLATE_VERSION_UPDATE_MODE"] = mode
    workspace.initial_env_template_artifact = "env-templates:1.0.0"
    workspace.run_pipeline(extra_env=workspace.extra_env)

@then(parsers.parse('the "env_definition.yml" file has envTemplate.artifact equal to "{version}"'))
def envdef_has_artifact(workspace, version):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    file_path = env_dir / "Inventory" / "env_definition.yml"
    actual_content = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    assert actual_content.get("envTemplate", {}).get("artifact") == version

@then(parsers.parse('the "env_definition.yml" file has generatedVersions.generateEnvironmentLatestVersion equal to "{version}"'))
def envdef_has_generated_versions(workspace, version):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    file_path = env_dir / "Inventory" / "env_definition.yml"
    actual_content = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    assert actual_content.get("generatedVersions", {}).get("generateEnvironmentLatestVersion") == version

@then('the "env_definition.yml" file envTemplate.artifact is not changed')
def envdef_artifact_not_changed(workspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    file_path = env_dir / "Inventory" / "env_definition.yml"
    actual_content = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    assert actual_content.get("envTemplate", {}).get("artifact") == workspace.initial_env_template_artifact

# ── Rollback (Negative) ──────────────────────────────────────────────────────

@when('the Instance pipeline is started with invalid ENV_INVENTORY_CONTENT that fails during processing')
def pipeline_invalid_content_rollback(workspace):
    workspace.pre_run_snapshot_dir = workspace.base_dir.parent / "snapshot_neg"
    if workspace.pre_run_snapshot_dir.exists():
        shutil.rmtree(workspace.pre_run_snapshot_dir)
    shutil.copytree(workspace.base_dir, workspace.pre_run_snapshot_dir)

    env_def = {
        "action": "create_or_replace",
        "content": {"inventory": "invalid_string_not_object"},
    }
    content = {"envDefinition": env_def}
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["ENV_INVENTORY_CONTENT"] = json.dumps(content)
    workspace.run_pipeline(extra_env=workspace.extra_env)
