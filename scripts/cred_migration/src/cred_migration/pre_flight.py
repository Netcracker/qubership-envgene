"""Pre-flight checks before apply.

- Dirty git working tree: `git status --porcelain` MUST be empty for tracked-file changes;
  untracked files ignored (per State handling section).
- Store auth env vars: for each store type in `secret-stores.yml`, the required env vars must be
  present in the process environment.
- Single-store assumption: `secret-stores.yml` MUST contain exactly one entry (Assumption 1).
"""

import os
import subprocess


class PreFlightError(RuntimeError):
    """Raised when a pre-flight check fails; apply aborts with exit code 3."""


# Per-store required auth env vars (mirrors Invocation table in design doc).
_REQUIRED_ENV_VARS = {
    "vault": ("VAULT_ADDR", "VAULT_TOKEN"),
    "openbao": ("VAULT_ADDR", "VAULT_TOKEN"),
    "gcp": ("GOOGLE_APPLICATION_CREDENTIALS",),
    "aws": ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_DEFAULT_REGION"),
    "azure": ("AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET"),
}


def check_git_clean(repo_root):
    """Raise PreFlightError if the git working tree has modified tracked files.

    Untracked files are ignored (per design doc State handling section).
    """
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    dirty_lines = [
        ln for ln in result.stdout.splitlines()
        if ln and not ln.startswith("??")  # ignore untracked
    ]
    if dirty_lines:
        raise PreFlightError(
            "git working tree is dirty (tracked-file changes present):\n"
            + "\n".join(dirty_lines)
        )


def check_store_auth_env(store_types):
    """Raise PreFlightError if any required env var is missing for the given store types."""
    missing = []
    for store_type in store_types:
        required = _REQUIRED_ENV_VARS.get(store_type, ())
        for var in required:
            if not os.environ.get(var):
                missing.append(f"{var} (required for {store_type})")
    if missing:
        raise PreFlightError(
            "missing required Store auth env vars:\n" + "\n".join(missing)
        )


def check_single_store(secret_stores):
    """Raise PreFlightError if secret-stores.yml contains multiple entries (Assumption 1)."""
    if not isinstance(secret_stores, dict):
        raise PreFlightError("secret-stores.yml must be a mapping of store-id -> config")
    if len(secret_stores) > 1:
        raise PreFlightError(
            f"multiple stores in secret-stores.yml violates Assumption 1: {sorted(secret_stores)}"
        )
