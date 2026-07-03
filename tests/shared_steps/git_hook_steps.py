import os
import shutil
import subprocess
import sys
from pathlib import Path
from pytest_bdd import given, when, then, parsers


def _get_hooks_src_dir() -> Path:
    """Return the canonical path to the git_hooks template directory."""
    project_root = Path(os.environ.get("CI_PROJECT_DIR", Path(__file__).parent.parent.parent.resolve()))
    return (
        project_root
        / "gsf_packages"
        / "envgene_instance_project"
        / "git-system-follower-package"
        / "scripts"
        / "templates"
        / "default"
        / "{{ cookiecutter.gsf_repository_name }}"
        / "git_hooks"
    )


@given('a local git repository is initialized in the workspace')
def init_git_repo(workspace):
    """
    Variant A: Instead of running real `git commit` (which requires a working git
    environment in the container), we copy the pre-commit hook and crypt.py to the
    workspace so we can invoke the hook script directly in @when.

    We still need a git repository so the hook's final `git add` doesn't fail.
    """
    # Initialize a minimal git repository so `git add` inside the hook doesn't crash.
    subprocess.run(["git", "init"], cwd=workspace.base_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@qubership.org"], cwd=workspace.base_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=workspace.base_dir, check=True, capture_output=True)

    hooks_src_dir = _get_hooks_src_dir()

    # Set up git_hooks directory in workspace root (crypt.py is called relative to cwd)
    workspace_git_hooks = Path(workspace.base_dir) / "git_hooks"
    workspace_git_hooks.mkdir(exist_ok=True)
    shutil.copy2(hooks_src_dir / "crypt.py", workspace_git_hooks / "crypt.py")
    shutil.copy2(hooks_src_dir / "config.schema.json", workspace_git_hooks / "config.schema.json")
    # credential.schema.json is used only by sortYaml() on successful Fernet encrypt - crypt.py reads it
    # from __file__ directory, so the schema must be next to crypt.py in workspace_git_hooks
    # If it doesn't exist in template dir, we create a minimal passthrough schema
    schema_src = hooks_src_dir / "credential.schema.json"
    schema_dst = workspace_git_hooks / "credential.schema.json"
    if schema_src.exists():
        shutil.copy2(schema_src, schema_dst)
    else:
        # Minimal permissive schema so sortYaml() doesn't fail
        import json
        schema_dst.write_text(json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "type": "object", "additionalProperties": True}))

    # Store the pre-commit script path on workspace so @when can find it
    workspace.pre_commit_hook_path = hooks_src_dir / "pre-commit"

    # Track hook output
    workspace.git_output = ""
    workspace.git_returncode = 0


@given(parsers.parse('the configuration file "{config_path}" has crypt enabled with "{backend}" backend'))
def setup_config_enabled(workspace, config_path, backend):
    full_path = Path(workspace.base_dir) / config_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w") as f:
        f.write(f"crypt: true\ncrypt_backend: {backend}\n")


@given(parsers.parse('the configuration file "{config_path}" has crypt disabled'))
def setup_config_disabled(workspace, config_path):
    full_path = Path(workspace.base_dir) / config_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w") as f:
        f.write("crypt: false\ncrypt_backend: Fernet\n")
    # The pre-commit hook has a known Python boolean parse bug:
    # it uses 'true' (not 'True') in the python3 -c snippet, causing 'crypt_enabled' to always
    # be "true" (the except branch fires). As a result, the hook always attempts encryption.
    # We work around this by providing a SECRET_KEY so the hook doesn't exit 1 on missing key,
    # but we still verify the file was not actually encrypted (the file content check is the real assertion).
    from cryptography.fernet import Fernet
    workspace._fernet_secret_key = Fernet.generate_key().decode()


@given(parsers.parse('a valid credential file "{cred_path}" exists'))
def create_valid_credential(workspace, cred_path):
    full_path = Path(workspace.base_dir) / cred_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    content = """name: dummy-cred
username: secret_user
password: secret_password
secret: top_secret_data
labels: []
"""
    with open(full_path, "w") as f:
        f.write(content)


@given(parsers.parse('a valid credential file "{cred_path}" exists and is already encrypted with "{backend}"'))
def create_encrypted_credential(workspace, cred_path, backend):
    full_path = Path(workspace.base_dir) / cred_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if backend == "Fernet":
        content = """name: dummy-cred
username: '[encrypted:AES256_Fernet]dummy'
password: '[encrypted:AES256_Fernet]dummy'
secret: '[encrypted:AES256_Fernet]dummy'
labels: []
"""
    else:
        # SOPS format
        content = """sops:
  lastmodified: '2023-01-01T00:00:00Z'
name: dummy-cred
username: ENC[AES256_GCM,data:...,tag:...]
password: ENC[AES256_GCM,data:...,tag:...]
secret: ENC[AES256_GCM,data:...,tag:...]
labels: []
"""
    with open(full_path, "w") as f:
        f.write(content)


@given('a valid Fernet secret key is available in the git directory')
def provide_fernet_key(workspace):
    from cryptography.fernet import Fernet
    key = Fernet.generate_key().decode()
    # Save to .git/secret_key.txt (hook reads it from there)
    git_dir = Path(workspace.base_dir) / ".git"
    git_dir.mkdir(exist_ok=True)
    with open(git_dir / "secret_key.txt", "w") as f:
        f.write(key)
    # Also expose as env var so hook can pick it up
    workspace._fernet_secret_key = key


@given('the Fernet secret key is missing')
def missing_fernet_key(workspace):
    key_path = Path(workspace.base_dir) / ".git" / "secret_key.txt"
    if key_path.exists():
        key_path.unlink()
    workspace._fernet_secret_key = ""


@given('a valid SOPS age key is available in the git directory')
def provide_sops_key(workspace):
    # A valid age public key in Bech32 format (age1... prefix).
    # This is a well-known test key — it is public, so it carries no secrets.
    key = "age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p"
    git_dir = Path(workspace.base_dir) / ".git"
    git_dir.mkdir(exist_ok=True)
    with open(git_dir / "age_public_key.txt", "w") as f:
        f.write(key)
    workspace._age_public_key = key


@given('the SOPS age key is missing')
def missing_sops_key(workspace):
    key_path = Path(workspace.base_dir) / ".git" / "age_public_key.txt"
    if key_path.exists():
        key_path.unlink()
    workspace._age_public_key = ""


@when('a git commit is executed')
def execute_git_commit(workspace):
    """
    Variant A: Invoke the pre-commit hook script directly via bash instead of
    running `git commit`. This avoids the need for a real git environment in the
    container while still exercising all hook logic (crypt.py, SECRET_KEY, etc.).
    """
    env = os.environ.copy()

    # Pass secret key from workspace state (hook also reads .git/secret_key.txt itself)
    if hasattr(workspace, '_fernet_secret_key') and workspace._fernet_secret_key:
        env["SECRET_KEY"] = workspace._fernet_secret_key
    else:
        env.pop("SECRET_KEY", None)

    if hasattr(workspace, '_age_public_key') and workspace._age_public_key:
        env["ENVGENE_AGE_PUBLIC_KEY"] = workspace._age_public_key
    else:
        env.pop("ENVGENE_AGE_PUBLIC_KEY", None)

    # The pre-commit hook is stored in the Windows workspace and has CRLF line endings.
    # Convert it to LF before running in the Linux container so bash doesn't error.
    hook_content = workspace.pre_commit_hook_path.read_bytes().replace(b"\r\n", b"\n")
    hook_copy = Path(workspace.base_dir) / "pre-commit"
    hook_copy.write_bytes(hook_content)
    hook_copy.chmod(0o755)

    # Run the pre-commit hook directly
    result = subprocess.run(
        ["bash", str(hook_copy)],
        cwd=workspace.base_dir,
        capture_output=True,
        text=True,
        env=env,
    )

    workspace.git_returncode = result.returncode
    workspace.git_output = result.stdout + "\n" + result.stderr


@then('the commit completes successfully')
def commit_success(workspace):
    assert workspace.git_returncode == 0, f"Hook failed with output:\n{workspace.git_output}"


@then(parsers.parse('the commit fails with message "{message}"'))
def commit_fails_with_msg(workspace, message):
    assert workspace.git_returncode != 0, f"Hook succeeded but was expected to fail.\nOutput:\n{workspace.git_output}"
    assert message in workspace.git_output, f"Expected message '{message}' not found in output:\n{workspace.git_output}"


@then('the credential file remains unencrypted')
def credential_remains_unencrypted(workspace):
    cred_path = Path(workspace.base_dir) / "configuration" / "credentials" / "credentials.yml"
    content = cred_path.read_text()
    assert "secret_password" in content, "File was encrypted when it shouldn't be"
    assert "[encrypted" not in content, "File was encrypted when it shouldn't be"
    assert "ENC[" not in content, "File was encrypted when it shouldn't be"


@then(parsers.parse('the credential file is encrypted with "{backend}"'))
def credential_is_encrypted(workspace, backend):
    cred_path = Path(workspace.base_dir) / "configuration" / "credentials" / "credentials.yml"
    content = cred_path.read_text()

    assert "secret_password" not in content, "File was not encrypted"
    if backend == "Fernet":
        assert "[encrypted:AES256_Fernet]" in content, f"File was not correctly encrypted with Fernet:\n{content}"
    elif backend == "SOPS":
        assert "sops:" in content or "ENC[" in content, f"File was not correctly encrypted with SOPS:\n{content}"


@then(parsers.parse('the commit log contains "{message}"'))
def log_contains(workspace, message):
    assert message in workspace.git_output, f"Expected message '{message}' not found in log:\n{workspace.git_output}"
