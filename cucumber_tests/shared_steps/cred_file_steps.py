import subprocess

from pytest_bdd import given, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace, TEST_AGE_PUBLIC_KEY
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
