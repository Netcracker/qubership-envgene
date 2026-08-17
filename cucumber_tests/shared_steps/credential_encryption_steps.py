"""Step definitions for credential file encryption BDD scenarios."""
import os
import sys
import subprocess
import yaml
from pathlib import Path
from cryptography.fernet import Fernet
from pytest_bdd import given, when, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace

_FERNET_KEY = "c2VjcmV0LWtleS1tdXN0LWJlLTMyLWJ5dGVzLWxvbmc="
_FERNET_PREFIX = "[encrypted:AES256_Fernet]"
_FAKE_AGE_PRIVATE_KEY = "AGE-SECRET-KEY-1FAKEPRIVATEKEYFORTEST0000000000000000000000000000000000"
_FAKE_AGE_PUBLIC_KEY = "age1y4hfj9zz05dtqycfk55y4csddch6w2lu9l6wx7r68at5x897ea3qjh0gl9"

_PLAINTEXT_CREDS = {
    "test-cred": {
        "type": "usernamePassword",
        "data": {
            "username": "plain-user",
            "password": "plain-pass",
            "secret": "plain-secret",
        }
    }
}


def _write_creds(workspace: EnvGeneWorkspace, content: dict):
    creds_file = workspace.creds_dir / "credentials.yml"
    creds_file.parent.mkdir(parents=True, exist_ok=True)
    creds_file.write_text(yaml.dump(content), encoding="utf-8")


def _build_env(workspace: EnvGeneWorkspace, extra_env: dict = None) -> dict:
    project_root = str(Path(__file__).parent.parent.parent.resolve())
    env = os.environ.copy()
    env["CI_PROJECT_DIR"] = str(workspace.base_dir)
    env["SECRET_KEY"] = _FERNET_KEY
    env["ENVGENE_AGE_PRIVATE_KEY"] = ""
    env["PUBLIC_AGE_KEYS"] = ""

    scripts_root = str(Path(project_root) / "scripts")
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in [project_root, scripts_root, existing_pythonpath] if p
    )

    if extra_env:
        for key, value in extra_env.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value

    return env


def _run_crypt_manager(workspace: EnvGeneWorkspace, subcommand: str, extra_env: dict = None):
    project_root = str(Path(__file__).parent.parent.parent.resolve())
    workspace.write_config()
    env = _build_env(workspace, extra_env)

    result = subprocess.run(
        [sys.executable, "-m", "scripts.utils.crypt_manager", subcommand],
        env=env,
        capture_output=True,
        text=True,
        cwd=project_root,
    )
    workspace.stdout = result.stdout
    workspace.stderr = result.stderr
    workspace.returncode = result.returncode
    return result


def _write_sops_mock(workspace: EnvGeneWorkspace):
    sops_bat = workspace.base_dir / "sops.bat"
    sops_bat.write_text(
        "@echo off\n"
        "exit /b 0\n",
        encoding="utf-8",
    )
    sops_sh = workspace.base_dir / "sops"
    sops_sh.write_text(
        "#!/bin/sh\n"
        "exit 0\n",
        encoding="utf-8",
    )
    os.chmod(sops_sh, 0o755)


@given(parsers.parse('a credentials file "{filename}" exists with plaintext values'))
def creds_file_with_plaintext(workspace: EnvGeneWorkspace, filename: str):
    _write_creds(workspace, _PLAINTEXT_CREDS)


@given(parsers.parse('a credentials file "{filename}" is already encrypted with Fernet'))
def creds_file_already_fernet_encrypted(workspace: EnvGeneWorkspace, filename: str):
    fernet = Fernet(_FERNET_KEY.encode())
    encrypted = {
        "test-cred": {
            "type": "usernamePassword",
            "data": {
                "username": f"{_FERNET_PREFIX}{fernet.encrypt(b'plain-user').decode()}",
                "password": f"{_FERNET_PREFIX}{fernet.encrypt(b'plain-pass').decode()}",
                "secret": f"{_FERNET_PREFIX}{fernet.encrypt(b'plain-secret').decode()}",
            }
        }
    }
    _write_creds(workspace, encrypted)


@given(parsers.parse('a credentials file "{filename}" is already encrypted with SOPS'))
def creds_file_already_sops_encrypted(workspace: EnvGeneWorkspace, filename: str):
    content = (
        "test-cred:\n"
        "    type: usernamePassword\n"
        "    data:\n"
        "        username: ENC[AES256_GCM,data:abc123==,tag:xyz,type:str]\n"
        "        password: ENC[AES256_GCM,data:def456==,tag:uvw,type:str]\n"
        "        secret: ENC[AES256_GCM,data:ghi789==,tag:rst,type:str]\n"
        "sops:\n"
        "    kms: []\n"
        "    age:\n"
        "    -   recipient: age1testkey\n"
        "        enc: |\n"
        "            -----BEGIN AGE ENCRYPTED FILE-----\n"
        "            dGVzdA==\n"
        "            -----END AGE ENCRYPTED FILE-----\n"
        "    lastmodified: '2024-01-01T00:00:00Z'\n"
        "    mac: ENC[AES256_GCM,data:test==,tag:test,type:str]\n"
        "    version: 3.7.3\n"
    )
    creds_file = workspace.creds_dir / "credentials.yml"
    creds_file.write_text(content, encoding="utf-8")


@when("the encrypt_cred_files module runs")
def run_encrypt_cred_files(workspace: EnvGeneWorkspace):
    _run_crypt_manager(workspace, "encrypt_cred_files")


@when("the encrypt_cred_files module runs without SECRET_KEY")
def run_encrypt_without_secret_key(workspace: EnvGeneWorkspace):
    _run_crypt_manager(workspace, "encrypt_cred_files", extra_env={"SECRET_KEY": ""})


@when("the encrypt_cred_files module runs without ENVGENE_AGE_PUBLIC_KEY")
def run_encrypt_without_age_key(workspace: EnvGeneWorkspace):
    _run_crypt_manager(
        workspace,
        "encrypt_cred_files",
        extra_env={"PUBLIC_AGE_KEYS": "", "ENVGENE_AGE_PUBLIC_KEY": ""},
    )


@when("the encrypt_cred_files module runs with SOPS mock")
def run_encrypt_with_sops_mock(workspace: EnvGeneWorkspace):
    _write_sops_mock(workspace)
    _run_crypt_manager(
        workspace,
        "encrypt_cred_files",
        extra_env={
            "PUBLIC_AGE_KEYS": _FAKE_AGE_PUBLIC_KEY,
            "ENVGENE_AGE_PUBLIC_KEY": _FAKE_AGE_PUBLIC_KEY,
            "ENVGENE_AGE_PRIVATE_KEY": _FAKE_AGE_PRIVATE_KEY,
            "PATH": f"{str(workspace.base_dir)}{os.pathsep}{os.environ.get('PATH', '')}",
        },
    )


@then("the encrypt module completes successfully")
def encrypt_module_success(workspace: EnvGeneWorkspace):
    assert workspace.returncode == 0, (
        f"encrypt_cred_files failed with code {workspace.returncode}.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )


@then("the encrypt module fails")
def encrypt_module_fails(workspace: EnvGeneWorkspace):
    assert workspace.returncode != 0, (
        f"encrypt_cred_files should have failed but returned 0.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )


@then(parsers.parse('the credentials file "{filename}" has encrypted sensitive fields'))
def creds_have_encrypted_fields(workspace: EnvGeneWorkspace, filename: str):
    creds_file = workspace.creds_dir / filename
    content = yaml.safe_load(creds_file.read_text(encoding="utf-8"))

    def has_encrypted(node):
        if isinstance(node, dict):
            return any(has_encrypted(v) for v in node.values())
        if isinstance(node, str):
            return node.startswith(_FERNET_PREFIX) or node.startswith("ENC[")
        return False

    assert has_encrypted(content), (
        f"No encrypted fields found in {filename}. Content: {content}"
    )


@then(parsers.parse('the credentials file "{filename}" has no encrypted fields'))
def creds_have_no_encrypted_fields(workspace: EnvGeneWorkspace, filename: str):
    creds_file = workspace.creds_dir / filename
    content = yaml.safe_load(creds_file.read_text(encoding="utf-8"))

    def has_encrypted(node):
        if isinstance(node, dict):
            return any(has_encrypted(v) for v in node.values())
        if isinstance(node, str):
            return node.startswith(_FERNET_PREFIX) or node.startswith("ENC[")
        return False

    assert not has_encrypted(content), (
        f"Encrypted fields found when none expected. Content: {content}"
    )


def _find_field(node, target):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == target:
                return v
            result = _find_field(v, target)
            if result is not None:
                return result
    return None


@then(parsers.parse('the credentials file "{filename}" field "{field}" is not encrypted'))
def creds_field_not_encrypted(workspace: EnvGeneWorkspace, filename: str, field: str):
    creds_file = workspace.creds_dir / filename
    content = yaml.safe_load(creds_file.read_text(encoding="utf-8"))
    value = _find_field(content, field)
    assert value is not None, f"Field '{field}' not found in {filename}"
    assert not str(value).startswith(_FERNET_PREFIX) and not str(value).startswith("ENC["), (
        f"Field '{field}' is encrypted: {value}"
    )


@then(parsers.parse('the credentials file "{filename}" field "{field}" starts with "{prefix}"'))
def creds_field_starts_with(workspace: EnvGeneWorkspace, filename: str, field: str, prefix: str):
    creds_file = workspace.creds_dir / filename
    content = yaml.safe_load(creds_file.read_text(encoding="utf-8"))
    value = _find_field(content, field)
    assert value is not None, f"Field '{field}' not found in {filename}"
    assert str(value).startswith(prefix), (
        f"Field '{field}' = {value!r} does not start with {prefix!r}"
    )


@then(parsers.parse('the credentials file "{filename}" is valid YAML'))
def creds_is_valid_yaml(workspace: EnvGeneWorkspace, filename: str):
    creds_file = workspace.creds_dir / filename
    content = yaml.safe_load(creds_file.read_text(encoding="utf-8"))
    assert content is not None, f"YAML file {filename} is empty or null"
    assert isinstance(content, dict), f"YAML file {filename} root is not a dict"
