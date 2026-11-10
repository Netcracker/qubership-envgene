"""Step definitions for envgeneNullValue validation scenarios (UC-NVV-*).

The injection steps mutate the pre-generated instance in the workspace so the
generate_effective_set stage validates exactly the values the scenarios state.
"""
import yaml
from pytest_bdd import given, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace

# Secret material layout per credential type, as produced by
# check_cred_value / create_credentials in envgenehelper.
_CRED_TYPE_TO_NULL_DATA = {
    "usernamePassword": {"username": "envgeneNullValue", "password": "envgeneNullValue"},
    "secret": {"secret": "envgeneNullValue"},
    "vault": {"secretId": "envgeneNullValue"},
}


@given(parsers.parse('a deploy parameter "{param}" is set to "{value}" in namespace "{ns}"'))
def set_namespace_deploy_param(workspace: EnvGeneWorkspace, param: str, value: str, ns: str):
    """Overwrite one deployParameter of a rendered namespace object with the given
    value (e.g. envgeneNullValue), simulating a generated instance that left an
    unresolved parameter behind."""
    ns_file = (workspace.base_dir / "environments" / workspace.cluster_name
               / workspace.env_name / "Namespaces" / ns / "namespace.yml")
    assert ns_file.exists(), f"Namespace file not found: {ns_file}"

    data = yaml.safe_load(ns_file.read_text(encoding="utf-8")) or {}
    data.setdefault("deployParameters", {})[param] = value
    ns_file.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")


@given(parsers.parse('the environment instance has these unresolved credentials:'))
def set_unresolved_credentials(workspace: EnvGeneWorkspace, table):
    """Replace the secret material of each listed credential with envgeneNullValue in
    Credentials/credentials.yml. Resolved credentials not in the table stay untouched."""
    creds_file = (workspace.base_dir / "environments" / workspace.cluster_name
                  / workspace.env_name / "Credentials" / "credentials.yml")
    assert creds_file.exists(), f"Credentials file not found: {creds_file}"

    creds = yaml.safe_load(creds_file.read_text(encoding="utf-8")) or {}
    for row in table:
        cred_id, cred_type = row["cred_id"], row["type"]
        assert cred_id in creds, f"Credential '{cred_id}' not found in {creds_file}"
        assert cred_type in _CRED_TYPE_TO_NULL_DATA, f"Unsupported credential type '{cred_type}'"
        creds[cred_id]["data"] = _CRED_TYPE_TO_NULL_DATA[cred_type]

    creds_file.write_text(yaml.dump(creds, default_flow_style=False), encoding="utf-8")
