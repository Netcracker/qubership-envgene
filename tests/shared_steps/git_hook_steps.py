import os
import shutil
import subprocess
from pathlib import Path
from pytest_bdd import given, when, then, parsers

@given('a local git repository is initialized in the workspace')
def init_git_repo(workspace):
    # Initialize a new git repository in the workspace
    subprocess.run(["git", "init"], cwd=workspace.base_dir, check=True, capture_output=True)
    
    # Configure dummy user for commits
    subprocess.run(["git", "config", "user.email", "test@qubership.org"], cwd=workspace.base_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=workspace.base_dir, check=True)
    
    # Copy pre-commit hook and crypt.py
    project_root = Path(os.environ.get("CI_PROJECT_DIR", Path(__file__).parent.parent.parent.resolve()))
    hooks_src_dir = project_root / "gsf_packages" / "envgene_instance_project" / "git-system-follower-package" / "scripts" / "templates" / "default" / "{{ cookiecutter.gsf_repository_name }}" / "git_hooks"
    
    # Create .git/hooks directory and copy pre-commit
    git_hooks_dir = Path(workspace.base_dir) / ".git" / "hooks"
    git_hooks_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(hooks_src_dir / "pre-commit", git_hooks_dir / "pre-commit")
    
    # The pre-commit script must be executable
    os.chmod(git_hooks_dir / "pre-commit", 0o755)
    
    # The pre-commit script calls `python git_hooks/crypt.py`
    workspace_git_hooks = Path(workspace.base_dir) / "git_hooks"
    workspace_git_hooks.mkdir(exist_ok=True)
    shutil.copy2(hooks_src_dir / "crypt.py", workspace_git_hooks / "crypt.py")
    
    # Make sure we store output
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
        f.write("crypt: false\n")

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
    with open(Path(workspace.base_dir) / ".git" / "secret_key.txt", "w") as f:
        f.write(key)

@given('the Fernet secret key is missing')
def missing_fernet_key(workspace):
    key_path = Path(workspace.base_dir) / ".git" / "secret_key.txt"
    if key_path.exists():
        key_path.unlink()

@given('a valid SOPS age key is available in the git directory')
def provide_sops_key(workspace):
    # Dummy age key format
    key = "AGE-SECRET-KEY-10000000000000000000000000000000000000000000000000000000000"
    with open(Path(workspace.base_dir) / ".git" / "age_public_key.txt", "w") as f:
        f.write(key)

@given('the SOPS age key is missing')
def missing_sops_key(workspace):
    key_path = Path(workspace.base_dir) / ".git" / "age_public_key.txt"
    if key_path.exists():
        key_path.unlink()

@when('a git commit is executed')
def execute_git_commit(workspace):
    subprocess.run(["git", "add", "."], cwd=workspace.base_dir)
    # The pre-commit hook is triggered by git commit
    # We must ensure that python3 is mapped to python on windows if needed, or that the bash script can find python.
    # We will use bash to run git commit so it uses the proper bash environment if needed on windows.
    # In the docker container, it's just standard git.
    
    # We need to set the environment variables manually if running outside git bash on windows
    env = os.environ.copy()
    env["SECRET_KEY"] = ""  # Let the script read it from .git
    
    result = subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=workspace.base_dir, capture_output=True, text=True, env=env)
    workspace.git_returncode = result.returncode
    workspace.git_output = result.stdout + "\n" + result.stderr

@then('the commit completes successfully')
def commit_success(workspace):
    assert workspace.git_returncode == 0, f"Git commit failed with output:\n{workspace.git_output}"

@then(parsers.parse('the commit fails with message "{message}"'))
def commit_fails_with_msg(workspace, message):
    assert workspace.git_returncode != 0, "Git commit succeeded but was expected to fail"
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
        # Note: If SOPS binary is not installed in the test environment, the python script will fail.
        # But we verify what the output contains. The actual crypt.py might write ENC[ or fail if sops is missing.
        assert "sops:" in content or "ENC[" in content, f"File was not correctly encrypted with SOPS:\n{content}"

@then(parsers.parse('the commit log contains "{message}"'))
def log_contains(workspace, message):
    assert message in workspace.git_output, f"Expected message '{message}' not found in log:\n{workspace.git_output}"
