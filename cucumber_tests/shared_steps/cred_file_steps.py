import subprocess

import yaml
from pytest_bdd import given, then, when, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace, TEST_AGE_PUBLIC_KEY
from cucumber_tests.shared_steps.calculator_cli_steps import _find_deployment_file
from envgene_shared.crypto.sops_handler import is_encrypted_SOPS_text
from envgene_shared.utils.file_utils import is_cred_file


def _cred_files(workspace: EnvGeneWorkspace):
    return sorted(
        path for path in workspace.base_dir.rglob("*")
        if path.is_file() and is_cred_file(str(path.relative_to(workspace.base_dir)))
    )


@given("the cred files of the environment are SOPS-encrypted with the test key")
def encrypt_cred_files(workspace: EnvGeneWorkspace):
    for path in _cred_files(workspace):
        text = path.read_text(encoding="utf-8")
        if not text.strip() or text.strip() == "{}" or is_encrypted_SOPS_text(text):
            continue
        subprocess.run(
            ["sops", "encrypt", "--in-place", "--age", TEST_AGE_PUBLIC_KEY, "--encrypted-regex", "^data$", str(path)],
            check=True, capture_output=True, text=True,
        )


@given("the cred files are recorded as a baseline")
@when("the cred files are recorded as a baseline")
def record_cred_files_baseline(workspace: EnvGeneWorkspace):
    workspace.cred_baseline = {path: path.read_bytes() for path in _cred_files(workspace)}


@then("every cred file is byte-equal to the baseline")
def every_cred_file_byte_equal(workspace: EnvGeneWorkspace):
    current = {path: path.read_bytes() for path in _cred_files(workspace)}
    changed = [str(path) for path in set(current) | set(workspace.cred_baseline)
               if current.get(path) != workspace.cred_baseline.get(path)]
    assert not changed, f"Cred files differ from the baseline: {changed}"


@then(parsers.parse('the cred file "{path}" is byte-equal to the baseline'))
def cred_file_byte_equal(workspace: EnvGeneWorkspace, path: str):
    file_path = workspace.base_dir / path
    assert file_path.read_bytes() == workspace.cred_baseline[file_path], f"{path} differs from the baseline"


@then(parsers.parse('the cred file "{path}" is SOPS-encrypted'))
def cred_file_is_sops_encrypted(workspace: EnvGeneWorkspace, path: str):
    file_path = workspace.base_dir / path
    workspace.assert_file_exists(file_path)
    assert is_encrypted_SOPS_text(file_path.read_text(encoding="utf-8")), f"{path} is not SOPS-encrypted"


@then(parsers.parse('the decrypted cred file "{path}" has "{key}" equal to "{expected}"'))
def decrypted_cred_file_value(workspace: EnvGeneWorkspace, path: str, key: str, expected: str):
    value = workspace.get_decrypted_yaml(workspace.base_dir / path)
    for part in key.split("."):
        value = value[part]
    assert value == expected, f"{path}: {key} is '{value}', expected '{expected}'"


def _leaves(value, prefix=""):
    if isinstance(value, dict):
        return {key: leaf for name, child in value.items() if name != "sops"
                for key, leaf in _leaves(child, f"{prefix}{name}.").items()}
    return {prefix.rstrip("."): value}


def _raw_value(file_path, key):
    return _leaves(yaml.safe_load(file_path.read_text(encoding="utf-8")))[key]


def _is_ciphertext(value):
    return isinstance(value, str) and value.startswith("ENC[")


@then(parsers.parse('in the cred file "{path}" the value of "{key}" is encrypted'))
def cred_value_is_encrypted(workspace: EnvGeneWorkspace, path: str, key: str):
    value = _raw_value(workspace.base_dir / path, key)
    assert _is_ciphertext(value), f"{path}: {key} is not encrypted: {value}"


@then(parsers.parse('in the cred file "{path}" the value of "{key}" is plain'))
def cred_value_is_plain(workspace: EnvGeneWorkspace, path: str, key: str):
    value = _raw_value(workspace.base_dir / path, key)
    assert not _is_ciphertext(value), f"{path}: {key} is encrypted: {value}"


@then(parsers.parse('in the cred file "{path}" only the value of "{key}" has a new ciphertext'))
def only_one_ciphertext_changed(workspace: EnvGeneWorkspace, path: str, key: str):
    file_path = workspace.base_dir / path
    before = _leaves(yaml.safe_load(workspace.cred_baseline[file_path].decode("utf-8")))
    after = _leaves(yaml.safe_load(file_path.read_text(encoding="utf-8")))
    changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
    assert changed == [key], f"{path}: changed values {changed}, expected only {key}"


@then(parsers.parse('the "{app_name}" collision-credentials.yaml is SOPS-encrypted'))
def collision_credentials_is_sops_encrypted(workspace: EnvGeneWorkspace, app_name: str):
    file_path = _find_deployment_file(workspace, app_name, "collision-credentials.yaml")
    assert is_encrypted_SOPS_text(file_path.read_text(encoding="utf-8")), f"{file_path} is not SOPS-encrypted"


@then(parsers.parse('in the "{app_name}" collision-credentials.yaml the value of "{key}" is encrypted'))
def collision_credentials_value_is_encrypted(workspace: EnvGeneWorkspace, app_name: str, key: str):
    file_path = _find_deployment_file(workspace, app_name, "collision-credentials.yaml")
    value = _raw_value(file_path, key)
    assert _is_ciphertext(value), f"{file_path}: {key} is not encrypted: {value}"


@then(parsers.parse('the "{app_name}" collision-credentials.yaml is byte-equal to the baseline'))
def collision_credentials_byte_equal(workspace: EnvGeneWorkspace, app_name: str):
    file_path = _find_deployment_file(workspace, app_name, "collision-credentials.yaml")
    assert file_path.read_bytes() == workspace.cred_baseline[file_path], f"{file_path} differs from the baseline"


@then("the deployment credentials files are not SOPS-encrypted")
def deployment_credentials_not_encrypted(workspace: EnvGeneWorkspace):
    env_dir = workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name
    deployment_dir = env_dir / "effective-set" / "deployment"
    files = list(deployment_dir.rglob("credentials.yaml"))
    assert files, f"No credentials.yaml under {deployment_dir}"
    encrypted = [str(f) for f in files if is_encrypted_SOPS_text(f.read_text(encoding="utf-8"))]
    assert not encrypted, f"SOPS-encrypted deployment credentials files: {encrypted}"
