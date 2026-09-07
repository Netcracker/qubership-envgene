"""Step definitions for credential rotation scenarios."""
from pathlib import Path
import yaml
from pytest_bdd import then, parsers
from cucumber_tests.framework.workspace import EnvGeneWorkspace


@then(parsers.parse('the "{filename}" file exists at the workspace root'))
def file_exists_at_workspace_root(workspace: EnvGeneWorkspace, filename: str):
    path = workspace.base_dir / filename
    assert path.exists(), (
        f"Expected {filename} to exist at {workspace.base_dir}, but it does not.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )


@then(parsers.parse('the "{filename}" file does not exist at the workspace root'))
def file_not_exists_at_workspace_root(workspace: EnvGeneWorkspace, filename: str):
    path = workspace.base_dir / filename
    assert not path.exists(), (
        f"Expected {filename} NOT to exist at {workspace.base_dir}, but it does.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )


@then('no credential files were modified by the rotation')
def no_cred_files_modified(workspace: EnvGeneWorkspace):
    creds_file = (
        workspace.base_dir
        / "environments"
        / workspace.cluster_name
        / workspace.env_name
        / "Credentials"
        / "credentials.yml"
    )
    if not creds_file.exists():
        return
    content = yaml.safe_load(creds_file.read_text(encoding="utf-8"))
    cred = content.get("db-cred", {})
    actual = cred.get("data", {}).get("password")
    assert actual == "original-password", (
        f"Credential file was modified: db-cred.password is '{actual}', expected 'original-password'"
    )


@then(parsers.parse('the credential "{cred_id}" field "{field}" equals "{expected}" in the env credentials file'))
def credential_field_equals(workspace: EnvGeneWorkspace, cred_id: str, field: str, expected: str):
    creds_file = (
        workspace.base_dir
        / "environments"
        / workspace.cluster_name
        / workspace.env_name
        / "Credentials"
        / "credentials.yml"
    )
    assert creds_file.exists(), (
        f"Credentials file not found at {creds_file}.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    content = yaml.safe_load(creds_file.read_text(encoding="utf-8"))
    assert cred_id in content, f"Credential '{cred_id}' not found in {creds_file}"
    actual = content[cred_id].get("data", {}).get(field)
    assert actual == expected, (
        f"Expected {cred_id}.{field}='{expected}', got '{actual}'.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
