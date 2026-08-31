"""Feature-specific step definitions for external credentials scenarios."""
import os
import yaml
from pathlib import Path
from cryptography.fernet import Fernet
from pytest_bdd import then, parsers

_FERNET_KEY = b"c2VjcmV0LWtleS1tdXN0LWJlLTMyLWJ5dGVzLWxvbmc="
_GOLDEN_DIR = Path(__file__).parent.parent / "test_data" / "golden"


def _decrypt_node(node, fernet):
    if isinstance(node, dict):
        return {k: _decrypt_node(v, fernet) for k, v in node.items()}
    elif isinstance(node, list):
        return [_decrypt_node(v, fernet) for v in node]
    elif isinstance(node, str) and node.startswith("[encrypted:AES256_Fernet]"):
        token = node[len("[encrypted:AES256_Fernet]"):]
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    return node


@then(parsers.parse('the rendered env credentials match the reference "{ref_name}"'))
def rendered_env_creds_match(workspace, ref_name):
    fernet = Fernet(_FERNET_KEY)
    creds_path = (
        workspace.environments_dir
        / workspace.cluster_name
        / workspace.env_name
        / "Credentials"
        / "credentials.yml"
    )
    assert creds_path.exists(), (
        f"Credentials file not found: {creds_path}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    actual = _decrypt_node(yaml.safe_load(creds_path.read_text(encoding="utf-8")), fernet)

    ref_file = _GOLDEN_DIR / ref_name / "credentials.yml"
    if os.environ.get("UPDATE_GOLDEN") == "1":
        ref_file.parent.mkdir(parents=True, exist_ok=True)
        ref_file.write_text(yaml.dump(actual, sort_keys=False), encoding="utf-8")
        return

    assert ref_file.exists(), (
        f"Golden not found: {ref_file}. Run with UPDATE_GOLDEN=1 to create it."
    )
    expected = yaml.safe_load(ref_file.read_text(encoding="utf-8"))
    assert actual == expected, (
        f"Credentials mismatch for '{ref_name}'\nExpected: {expected}\nActual: {actual}"
    )
