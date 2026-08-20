import json
import os

import yaml
import shutil
from pathlib import Path
from pytest_bdd import given, parsers, then, when
from cryptography.fernet import Fernet

from cucumber_tests.framework.workspace import (
    TEST_ENV_DEFINITION_CONTENT,
    TEST_YAML_CONTENT,
    create_file,
    delete_file_if_exists,
)
from cucumber_tests.framework.golden_compare import compare_directories


# Entity -> (subdirectory, has_inventory_folder)
# has_inventory_folder=True means env scope puts files under .../Inventory/
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


@then("the repository state is identical to the initial state")
def repo_state_identical(workspace):
    compare_directories(
        workspace.pre_run_snapshot_dir,
        workspace.base_dir,
        ignore_patterns=["build.env", "envgene-vars.env", "configuration/config.yml", "*.bat", "sops", "run_effective_set_cli.*", "artifacts"],
    )


# ── UC-EINV-BASIC-1 steps ─────────────────────────────────────────────────────


@then("the generated env_definition contains minimal required fields")
def env_definition_has_required_fields(workspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    inv_file = env_dir / "Inventory" / "env_definition.yml"
    assert inv_file.exists(), "env_definition.yml does not exist"
    data = yaml.safe_load(inv_file.read_text(encoding="utf-8"))
    assert "inventory" in data, "Missing 'inventory' key"
    assert "envTemplate" in data, "Missing 'envTemplate' key"


# ── Shared assertions ─────────────────────────────────────────────────────────


@then("its parent directory is not deleted")
def parent_dir_not_deleted(workspace):
    workspace.assert_file_exists(workspace.last_checked_file_path.parent)


@then("the environment directory is deleted")
def env_dir_is_deleted(workspace):
    env_dir = workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name
    if env_dir.exists():
        contents = list(env_dir.rglob('*'))
        assert not contents, f"Directory {env_dir} was not deleted and is not empty. Contents: {contents}"


@then(parsers.parse('the decrypted credentials file "{filename}" at "{scope}" scope matches the reference "{ref_name}"'))
def decrypted_creds_match(workspace, filename, scope, ref_name):
    key = b"c2VjcmV0LWtleS1tdXN0LWJlLTMyLWJ5dGVzLWxvbmc="
    fernet = Fernet(key)

    path = workspace.entity_dir("credentials", scope) / filename
    actual_yaml = yaml.safe_load(path.read_text(encoding='utf-8'))

    # Decrypt values
    def decrypt_node(node):
        if isinstance(node, dict):
            return {k: decrypt_node(v) for k, v in node.items()}
        elif isinstance(node, list):
            return [decrypt_node(v) for v in node]
        elif isinstance(node, str) and node.startswith("[encrypted:AES256_Fernet]"):
            token = node[len("[encrypted:AES256_Fernet]"):]
            return fernet.decrypt(token.encode('utf-8')).decode('utf-8')
        return node

    decrypted_actual = decrypt_node(actual_yaml)

    # Read the golden reference
    ref_path = Path(__file__).parent.parent / "test_data" / "goldens" / ref_name / "environments"
    if scope == "env":
        ref_path = ref_path / workspace.cluster_name / workspace.env_name / "Inventory" / "credentials" / filename
    elif scope == "cluster":
        ref_path = ref_path / workspace.cluster_name / "credentials" / filename
    else:
        ref_path = ref_path / "credentials" / filename

    import os
    if os.environ.get('UPDATE_GOLDEN') == '1':
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        ref_path.write_text(yaml.dump(decrypted_actual, sort_keys=False, Dumper=yaml.SafeDumper), encoding='utf-8')
        print(f"Updated golden credential file at {ref_path}")
        return

    expected_yaml = yaml.safe_load(ref_path.read_text(encoding='utf-8'))

    assert decrypted_actual == expected_yaml, f"Decrypted credentials do not match expected reference {ref_name}"


@then("the pipeline succeeds")
def pipeline_succeeds(workspace):
    workspace.assert_success()


@then(parsers.parse('the pipeline logs contain a readable error message explaining the failure reason'))
def pipeline_logs_contain_error(workspace):
    workspace.assert_logs_contain("Validation failed")


@then(parsers.parse('the pipeline logs contain "{text}"'))
@then(parsers.parse('the pipeline log contains "{text}"'))
def pipeline_logs_contain_text(workspace, text):
    workspace.assert_logs_contain(text)


@then(parsers.parse('the pipeline log does not contain "{text}"'))
def pipeline_logs_not_contain_text(workspace, text):
    workspace.assert_logs_not_contain(text)




