"""Glob-based file discovery per Scope of migration.

Source files: cred definitions migration processes (rewrites in Git).
Consumer files: reference creds via macros / built-in fields (rewrites macros in Git).
To-delete files: generated env-scoped Credentials + deployer creds + orphaned Shared creds.
"""

from pathlib import Path


def _glob(root, pattern):
    """Return sorted list of matching Path objects under root."""
    return sorted(Path(root).glob(pattern))


# ---- Source cred files ----

def find_source_cred_files_instance(repo_root):
    """Collect all Instance-repo source cred files (Cloud Passport creds + Shared + System).

    Excludes generated env-scoped `Credentials/credentials.yml` (to-delete, not a source).
    """
    root = Path(repo_root)
    found = []
    found.extend(_glob(root, "environments/*/cloud-passport/*-creds.yml"))
    found.extend(_glob(root, "environments/credentials/*.yml"))
    found.extend(_glob(root, "environments/*/credentials/*.yml"))
    found.extend(_glob(root, "environments/*/*/Inventory/credentials/*.yml"))
    found.extend(_glob(root, "configuration/credentials/*.yml"))
    return found


def find_source_cred_files_template(repo_root):
    """Collect Template-repo Credential Template files."""
    root = Path(repo_root)
    return _glob(root, "templates/env_templates/*/external-credentials.yml.j2")


# ---- Consumer files (macros to rewrite) ----

def find_consumer_files_instance(repo_root):
    """Instance-repo consumer files: Cloud Passport mains, ParameterSets, system configs."""
    root = Path(repo_root)
    found = []
    # Cloud Passport main file (exclude *-creds.yml)
    for p in _glob(root, "environments/*/cloud-passport/*.yml"):
        if not p.name.endswith("-creds.yml"):
            found.append(p)
    # ParameterSets at all three scopes
    found.extend(_glob(root, "environments/parameters/*.yml"))
    found.extend(_glob(root, "environments/*/parameters/*.yml"))
    found.extend(_glob(root, "environments/*/*/Inventory/parameters/*.yml"))
    # System configs with cred macros
    for extra in ("configuration/integration.yml", "configuration/registry.yml"):
        p = root / extra
        if p.exists():
            found.append(p)
    # Deployer config (not deployer-creds - that's to-delete)
    found.extend(_glob(root, "environments/*/*/app-deployer/deployer.yml"))
    return found


def find_consumer_files_template(repo_root):
    """Template-repo consumer files: env templates + parameter templates."""
    root = Path(repo_root)
    found = []
    for name in ("cloud.yml.j2", "namespace.yml.j2", "tenant.yml.j2"):
        found.extend(_glob(root, f"templates/env_templates/*/{name}"))
    # namespace variants (namespace-a.yml.j2 etc.)
    for p in _glob(root, "templates/env_templates/*/namespace*.yml.j2"):
        if p not in found:
            found.append(p)
    found.extend(_glob(root, "templates/parameters/*/*.yml"))
    return sorted(found)


# ---- To-delete files ----

def find_generated_env_credentials(repo_root):
    """Env-scoped generated `Credentials/credentials.yml` files."""
    return _glob(Path(repo_root), "environments/*/*/Credentials/credentials.yml")


def find_deployer_cred_files(repo_root):
    """Env-scoped `app-deployer/deployer-creds.yml` files (out of scope per No-CMDB)."""
    return _glob(Path(repo_root), "environments/*/*/app-deployer/deployer-creds.yml")
