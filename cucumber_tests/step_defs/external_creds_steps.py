from pathlib import Path
from typing import Any, Iterator

import yaml

from cucumber_tests.framework.workspace import EnvGeneWorkspace
from pytest_bdd import given, parsers, then
from cryptography.fernet import Fernet


ES_DIR_NAME = "effective-set"
EXTERNAL_CREDENTIAL_DIR = "external-credential"
EXTERNAL_CREDENTIAL_FILE = "external-credentials.yaml"
ENVIRONMENTS = "environments"
DEPLOYMENT = "deployment"
PIPELINE = "pipeline"
TOPOLOGY = "topology"
CREDENTIALS_FILE = "credentials.yaml"
ENVIRONMENT_CREDENTIALS_FOLDER = "Credentials"


def _get_env_credential_types(workspace: EnvGeneWorkspace) -> tuple[Path, set[str]]:
    env_cred_file = (
        workspace.base_dir
        / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
        / ENVIRONMENT_CREDENTIALS_FOLDER / "credentials.yml"
    )

    assert env_cred_file.exists(), (f"Environment credentials file does not exist: {env_cred_file}")

    content = (yaml.safe_load(env_cred_file.read_text(encoding="utf-8")) or {})

    found_types = {
        credential["type"]
        for credential in content.values()
        if isinstance(credential, dict) and isinstance(credential.get("type"), str)
    }

    return env_cred_file, found_types


def _get_deployment_credential_value(workspace: EnvGeneWorkspace, credential_name: str) -> tuple[Path, Any]:
    deployment_dir = (
        workspace.base_dir
        / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
        / ES_DIR_NAME / DEPLOYMENT
    )

    assert deployment_dir.exists(), (f"effective-set/deployment directory does not exist: {deployment_dir}")

    credentials_files = list(deployment_dir.rglob("credentials.yaml"))

    assert credentials_files, (f"No credentials.yaml found under {deployment_dir}")

    for credentials_file in credentials_files:
        content = yaml.safe_load(credentials_file.read_text(encoding="utf-8")) or {}
        if credential_name in content:
            return credentials_file, content[credential_name]

    raise AssertionError(
        f"Credential '{credential_name}' not found in any credentials.yaml under {deployment_dir}.\n"
        f"Files checked: {[str(path) for path in credentials_files]}"
    )


def _assert_eso_reference(value, credentials_file, credential_name, secret_name) -> None:
    assert isinstance(value, dict), (
        f"Expected '{credential_name}' to be an ESO reference mapping "
        f"in {credentials_file}, but got: {value!r}"
    )
    assert value.get("normalizedSecretName") == secret_name, (
        f"Expected '{credential_name}' to have normalizedSecretName '{secret_name}', "
        f"but got '{value.get('normalizedSecretName')}' in {credentials_file}"
    )


def _get_application_deployment_credentials(workspace: EnvGeneWorkspace, app_name: str) -> tuple[Path, dict]:
    deployment_dir = (
        workspace.base_dir
        / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
        / ES_DIR_NAME / DEPLOYMENT
    )
    app_creds_files = list(deployment_dir.rglob(f"{app_name}/values/credentials.yaml"))
    assert app_creds_files, (
        f"No credentials.yaml found for application '{app_name}' under {deployment_dir}"
    )
    content = yaml.safe_load(app_creds_files[0].read_text(encoding="utf-8")) or {}
    return app_creds_files[0], content


def _assert_all_vals_references(value: Any, credentials_file: Path, path: str = "",) -> None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            current_path = f"{path}.{key}" if path else str(key)
            _assert_all_vals_references(nested_value, credentials_file, current_path)
        return
    if isinstance(value, list):
        for index, nested_value in enumerate(value):
            _assert_all_vals_references(nested_value, credentials_file, f"{path}[{index}]")
        return
    assert isinstance(value, str) and value.startswith("ref+"), (
        f"Expected VALS reference (ref+...) for '{path}' in {credentials_file}, but got: {value!r}"
    )


def _assert_all_eso_references(value: Any, credentials_file: Path, path: str = "") -> None:
    if isinstance(value, dict):
        # secretStoreId uniquely identifies an ESO reference.
        if "secretStoreId" in value:
            return
        for key, nested_value in value.items():
            current_path = f"{path}.{key}" if path else str(key)
            _assert_all_eso_references(nested_value, credentials_file, current_path)
        return
    if isinstance(value, list):
        for index, nested_value in enumerate(value):
            _assert_all_eso_references(nested_value, credentials_file, f"{path}[{index}]")
        return

    assert False, (
        f"Expected ESO reference at '{path}' in {credentials_file}, but got: {value!r}"
    )


def _get_external_credential_context_file(workspace: EnvGeneWorkspace) -> Path:
    return (
        workspace.base_dir
        / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
        / ES_DIR_NAME / EXTERNAL_CREDENTIAL_DIR / EXTERNAL_CREDENTIAL_FILE
    )


def _get_external_credential_context_entry(workspace: EnvGeneWorkspace, cred_name: str) -> tuple[Path, dict]:
    context_file = _get_external_credential_context_file(workspace)
    assert context_file.exists(), f"External credential context file does not exist: {context_file}"
    content = decrypt(workspace, context_file)
    credentials = content.get("credentials", {})
    assert cred_name in credentials, (
        f"Credential '{cred_name}' not found in context file {context_file}.\n"
        f"Available credentials: {list(credentials.keys())}"
    )
    return context_file, credentials[cred_name]


def decrypt(workspace: EnvGeneWorkspace, file_path: Path) -> dict[str, Any]:
    key = b"c2VjcmV0LWtleS1tdXN0LWJlLTMyLWJ5dGVzLWxvbmc="
    fernet = Fernet(key) 
    
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
    
    actual_yaml = workspace.get_yaml(file_path)         
    return decrypt_node(actual_yaml)


@then(parsers.parse('the environment credentials file contains only credentials of type "{credential_type}"'))
def environment_credentials_file_contains_single_type(workspace: EnvGeneWorkspace, credential_type: str):
    env_cred_file, found_types = _get_env_credential_types(workspace)
    
    assert found_types == {credential_type}, (
        f"Expected only credentials of type '{credential_type}' in {env_cred_file}, but found types: {found_types}"
    )


@then(parsers.parse('the environment credentials file contains no credentials of type "{credential_type}"'))
def environment_credentials_file_contains_no_type(workspace: EnvGeneWorkspace, credential_type: str):
    env_cred_file, found_types = _get_env_credential_types(workspace)

    assert credential_type not in found_types, (
        f"Expected no credentials of type '{credential_type}' in {env_cred_file}, but found types: {found_types}"
    )


@then(parsers.parse('the deployment credentials value for "{credential_name}" contains "{expected}"'))
def deployment_credentials_value_contains(workspace: EnvGeneWorkspace, credential_name: str, expected: str):
    credentials_file, value = _get_deployment_credential_value(workspace, credential_name)
    serialized_value = yaml.safe_dump(value, default_flow_style=False)

    assert expected in serialized_value, (
        f"Expected credential '{credential_name}' to contain '{expected}',"
        f"but got:\n{serialized_value}\nFile: {credentials_file}"  
    )


@then(parsers.parse('the deployment credentials value for "{credential_name}" does not contain "{unexpected}"'))
def deployment_credentials_value_does_not_contain(workspace: EnvGeneWorkspace, credential_name: str, unexpected: str):
    credentials_file, value = _get_deployment_credential_value(workspace, credential_name)
    serialized_value = yaml.safe_dump(value, default_flow_style=False)

    assert unexpected not in serialized_value, (
        f"Expected credential '{credential_name}' not to contain '{unexpected}', "
        f"but got:\n{serialized_value}\nFile: {credentials_file}"
    )


@then(parsers.parse(
    'the deployment credentials value for "{credential_name}" is an ESO reference '
    'to "{secret_name}" with key "{secret_key}"'
))
def deployment_credentials_value_is_eso_reference(
    workspace: EnvGeneWorkspace, credential_name: str, secret_name: str, secret_key: str
):
    credentials_file, value = _get_deployment_credential_value(workspace, credential_name)
    _assert_eso_reference(value, credentials_file, credential_name, secret_name)

    secret_keys = value.get("secretKeys")
    assert isinstance(secret_keys, list), (
        f"Expected '{credential_name}' to have a secretKeys list, but got: {secret_keys!r}"
    )

    remote_key_names = {item.get("remoteKeyName") for item in secret_keys if isinstance(item, dict)}
    assert secret_key in remote_key_names, (
        f"Expected '{credential_name}' to contain remote key '{secret_key}', "
        f"but found: {remote_key_names} in file {credentials_file}"
    )


@then(parsers.parse(
    'the deployment credentials value for "{credential_name}" is an ESO reference '
    'to "{secret_name}" with no secret keys'
))
def deployment_credentials_value_is_eso_reference_without_secret_keys(
    workspace: EnvGeneWorkspace, credential_name, secret_name
):
    credentials_file, value = _get_deployment_credential_value(workspace, credential_name)
    _assert_eso_reference(value, credentials_file, credential_name, secret_name)

    secret_keys = value.get("secretKeys")
    assert not secret_keys, (
        f"Expected '{credential_name}' to have no secret keys, "
        f"but got: {secret_keys!r} in file {credentials_file}"
    )


@then(parsers.parse('the deployment credentials for application "{app_name}" hold VALS references'))
def deployment_credentials_for_app_are_vals(workspace: EnvGeneWorkspace, app_name: str):
    credentials_file, content = _get_application_deployment_credentials(workspace, app_name)

    assert content, f"Credentials file is empty: {credentials_file}"
    _assert_all_vals_references(content, credentials_file)


@then(parsers.parse('the deployment credentials for application "{app_name}" hold ESO references'))
def deployment_credentials_for_app_are_eso(workspace: EnvGeneWorkspace, app_name: str):
    credentials_file, content = _get_application_deployment_credentials(workspace, app_name)

    assert content, f"Credentials file is empty: {credentials_file}"
    _assert_all_eso_references(content, credentials_file)


@then(parsers.parse('the external credential context entry "{cred_name}" has strategy "{strategy}"'))
def external_credential_context_entry_has_strategy(workspace: EnvGeneWorkspace, cred_name: str, strategy: str):
    context_file, entry = _get_external_credential_context_entry(workspace, cred_name)
    actual = entry.get("strategy")
    assert actual == strategy, (
        f"Expected credential '{cred_name}' strategy to be '{strategy}', but got '{actual}' in {context_file}"
    )


@then(parsers.parse('the external credential context entry "{cred_name}" has vals "{vals_ref}"'))
def external_credential_context_entry_has_vals_ref(workspace: EnvGeneWorkspace, cred_name: str, vals_ref: str):
    context_file, entry = _get_external_credential_context_entry(workspace, cred_name)
    actual = entry.get("vals")
    assert actual == vals_ref, (
        f"Expected credential '{cred_name}' strategy to be '{vals_ref}', but got '{actual}' in {context_file}"
    )


@then(parsers.parse(
    'the external credential context entry "{cred_name}" has data field "{field}" equal to "{expected_value}"'
))
def external_credential_context_entry_has_data_field(
    workspace: EnvGeneWorkspace, cred_name: str, field: str, expected_value: str
):
    context_file, entry = _get_external_credential_context_entry(workspace, cred_name)
    data = entry.get("data")
    assert isinstance(data, dict), (
        f"Expected credential '{cred_name}' data to be a mapping, but got {data!r} in {context_file}"
    )
    actual = data.get(field)
    assert actual == expected_value, (
        f"Expected credential '{cred_name}' data.{field} to be '{expected_value}', "
        f"but got '{actual}' in {context_file}"
    )


@then(parsers.parse('the external credential context entry "{cred_name}" has no data field'))
def external_credential_context_entry_has_no_data(workspace: EnvGeneWorkspace, cred_name: str):
    context_file, entry = _get_external_credential_context_entry(workspace, cred_name)
    assert "data" not in entry, (
        f"Expected credential '{cred_name}' to have no data field, "
        f"but found data={entry.get('data')!r} in {context_file}"
    )


@then(parsers.parse(
    'the external credential context entry "{cred_name}" has a scalar data value "{expected_value}"'
))
def external_credential_context_entry_has_scalar_data(
    workspace: EnvGeneWorkspace, cred_name: str, expected_value: str
):
    context_file, entry = _get_external_credential_context_entry(workspace, cred_name)
    data = entry.get("data")
    assert isinstance(data, str), (
        f"Expected credential '{cred_name}' data to be a scalar string, but got {data!r} in {context_file}"
    )
    assert data == expected_value, (
        f"Expected credential '{cred_name}' data to be '{expected_value}' but got '{data}' in {context_file}"
    )


@then('the external credential context file does not exist')
def external_credential_context_file_is_absent(workspace: EnvGeneWorkspace):
    context_file = _get_external_credential_context_file(workspace)
    assert not context_file.exists(), (
        f"Expected external credential context file to be absent, but found: {context_file}"
    )

