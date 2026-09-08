from pathlib import Path
from typing import Any
import yaml

from pytest_bdd import given, parsers, then
from cucumber_tests.framework.workspace import EnvGeneWorkspace
from cryptography.fernet import Fernet
#from cucumber_tests.shared_steps.calculator_cli_steps import effective_set_deployment_params_contain # noqa: F401,F403

ES_DIR_NAME = "effective-set"
EXTERNAL_CREDENTIAL_DIR = "external-credential"
EXTERNAL_CREDENTIAL_FILE = "external-credentials.yaml"
ENVIRONMENTS = "environments"
DEPLOYMENT = "deployment"
PIPELINE = "pipeline"
TOPOLOGY = "topology"
CREDENTIALS_FILE = "credentials.yaml"
ENVIRONMENT_CREDENTIALS_FOLDER = "Credentials"


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


def _get_external_credential_context_file(workspace: EnvGeneWorkspace) -> Path:
    return (
        workspace.base_dir
        / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
        / ES_DIR_NAME / EXTERNAL_CREDENTIAL_DIR/ EXTERNAL_CREDENTIAL_FILE
    )


def _read_external_credential_context(workspace: EnvGeneWorkspace) -> dict[str, Any]:
    context_file =  _get_external_credential_context_file(workspace)
    return decrypt(workspace, context_file)


def _get_pipeline_directory(workspace: EnvGeneWorkspace) -> Path:
    return (
            workspace.base_dir
            / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
            / ES_DIR_NAME / PIPELINE
        )
    

@then(parsers.parse('the external credential context file contains "{expected_text}"'))
def external_credential_context_contains(workspace: EnvGeneWorkspace, expected_text: str):
    context = _read_external_credential_context(workspace)
    content = yaml.safe_dump(context)
    print(f'content={content}')

    assert expected_text in content, (
        f"Expected '{expected_text}' in external credential context file, "
        f"but it was not found.\n"
        f"Decrypted content:\n{content}"
    )


@then(parsers.parse('the external credential context entry "{entry_name}" has no data field'))
def external_credential_context_entry_has_no_data(workspace, entry_name):
    content = _read_external_credential_context(workspace)

    entry = content["credentials"][entry_name]

    assert "data" not in entry, (
        f"Expected '{entry_name}' to have no data field, "
        f"but got: {entry}"
    )


@then("the external credential context file is absent")
def external_credential_context_file_is_absent(workspace: EnvGeneWorkspace):
    context_file = _get_external_credential_context_file(workspace)

    workspace.assert_file_not_exists(context_file)


@then(parsers.parse('the deployment credentials file does not contain "{entry_name}"'))
def deployment_credentials_file_does_not_contain(workspace: EnvGeneWorkspace, entry_name: str):
    deployment_dir = (
        workspace.base_dir
        / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
        / ES_DIR_NAME / DEPLOYMENT
    )

    credentials_files = list(deployment_dir.rglob(CREDENTIALS_FILE))

    assert credentials_files, (f"No credentials.yaml found under {deployment_dir}")

    for credentials_file in credentials_files:
        content = credentials_file.read_text(encoding="utf-8")        
        assert entry_name not in content, (
            f"'{entry_name}' was unexpectedly found in {credentials_file}"
        )


@then(parsers.parse('the pipeline credentials file contains "{entry_name}"'))
def pipeline_credentials_file_contains(workspace: EnvGeneWorkspace, entry_name: str):
    pipeline_cred_file = _get_pipeline_directory(workspace) / CREDENTIALS_FILE
    
    assert pipeline_cred_file.exists(), (f"Pipeline credentials file does not exist: {pipeline_cred_file}")

    content = pipeline_cred_file.read_text(encoding="utf-8")

    assert entry_name in content, (f"'{entry_name}' was not found in {pipeline_cred_file}")


@then(parsers.parse('the per-consumer pipeline credentials file "{consumer_name}" contains "{entry_name}"'))
def per_consumer_pipeline_credentials_file_contains(workspace: EnvGeneWorkspace, consumer_name: str, entry_name: str):
    pipeline_dir = _get_pipeline_directory(workspace)
    credentials_files = list(pipeline_dir.glob(f"{consumer_name}-*-{CREDENTIALS_FILE}"))

    assert len(credentials_files) == 1, (
        f"Expected exactly one credentials file for consumer "
        f"'{consumer_name}', found {len(credentials_files)}: {credentials_files}"
    )

    credentials_file = credentials_files[0]
    content = credentials_file.read_text(encoding="utf-8")

    assert entry_name in content, (f"'{entry_name}' was not found in {credentials_file}")


@then(parsers.parse('the topology credentials file contains "{entry_name}"'))
def topology_credentials_file_contains(workspace: EnvGeneWorkspace, entry_name: str):
    topology_cred_file = (
            workspace.base_dir
            / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
            / ES_DIR_NAME / TOPOLOGY / CREDENTIALS_FILE
        )
    
    assert topology_cred_file.exists(), (f"Topology credentials file does not exist: {topology_cred_file}")

    content = topology_cred_file.read_text(encoding="utf-8")

    assert entry_name in content, (f"'{entry_name}' was not found in {topology_cred_file}")


@then(parsers.parse('the environment credentials file contains "{entry_name}"'))
def environment_credentials_file_contains(workspace: EnvGeneWorkspace, entry_name: str):
    env_cred_file = (
            workspace.base_dir
            / ENVIRONMENTS / workspace.cluster_name / workspace.env_name
            / ENVIRONMENT_CREDENTIALS_FOLDER / "credentials.yml"
        )
    
    assert env_cred_file.exists(), (f"Enviroment credentials file does not exist: {env_cred_file}")

    content = env_cred_file.read_text(encoding="utf-8")
    normalized_content = content.replace('"', "").replace("'", "")

    assert entry_name in normalized_content, (f"'{entry_name}' was not found in {env_cred_file}")