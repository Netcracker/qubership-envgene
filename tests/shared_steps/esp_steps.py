"""Step definitions for UC-EINV-ESP-* (ENV_SPECIFIC_PARAMS) scenarios."""
import json
import yaml
from pytest_bdd import given, when, then, parsers


# ── Shared background helper ─────────────────────────────────────────────────

@given("the target environment inventory file exists with cluster URL")
def inv_exists_with_cluster_url(workspace):
    """Creates a minimal env_definition.yml that already has clusterUrl set."""
    inv_dir = workspace.builder.get_env_dir("test-cluster", "test-env") / "Inventory"
    inv_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "inventory": {
            "environmentName": "test-env",
            "cloudName": "test-cluster",
            "clusterUrl": "https://old-cluster.example.com:6443",
        },
        "envTemplate": {
            "name": "test",
            "artifact": "project-env-template:v1.2.3",
            "additionalTemplateVariables": {
                "EXISTING_KEY": "existing-value",
            },
            "envSpecificParamsets": {},
        },
    }
    with open(inv_dir / "env_definition.yml", "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def _run_esp(workspace, params: dict):
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
    workspace.extra_env["ENV_SPECIFIC_PARAMS"] = json.dumps(params)
    # Always disable ENV_BUILD so that the pipeline runs only inventory generation
    workspace.extra_env.setdefault("ENV_BUILD", "false")
    workspace.run_pipeline(extra_env=workspace.extra_env)


# ── When steps ───────────────────────────────────────────────────────────────

@when("the Instance pipeline is started with ENV_SPECIFIC_PARAMS containing additionalTemplateVariables")
def esp_with_additional_vars(workspace):
    _run_esp(workspace, {"additionalTemplateVariables": {"MERGED_KEY": "merged-value"}})


@when(parsers.parse('the Instance pipeline is started with ENV_SPECIFIC_PARAMS containing clusterEndpoint "{endpoint}"'))
def esp_with_cluster_endpoint(workspace, endpoint):
    _run_esp(workspace, {"clusterParams": {"clusterEndpoint": endpoint}})


@when(parsers.parse('the Instance pipeline is started with ENV_SPECIFIC_PARAMS containing clusterToken "{token}"'))
def esp_with_cluster_token(workspace, token):
    _run_esp(workspace, {"clusterParams": {"clusterToken": token}})


@when(parsers.parse('the Instance pipeline is started with ENV_SPECIFIC_PARAMS merging additionalTemplateVariables key "{key}" value "{value}"'))
def esp_merge_additional_var(workspace, key, value):
    _run_esp(workspace, {"additionalTemplateVariables": {key: value}})


@when(parsers.parse('the Instance pipeline is started with ENV_SPECIFIC_PARAMS setting cloudName to "{cloud_name}"'))
def esp_set_cloud_name(workspace, cloud_name):
    _run_esp(workspace, {"cloudName": cloud_name})


@when(parsers.parse('the Instance pipeline is started with ENV_SPECIFIC_PARAMS setting tenantName to "{tenant_name}"'))
def esp_set_tenant_name(workspace, tenant_name):
    _run_esp(workspace, {"tenantName": tenant_name})


@when(parsers.parse('the Instance pipeline is started with ENV_SPECIFIC_PARAMS setting deployer to "{deployer}"'))
def esp_set_deployer(workspace, deployer):
    _run_esp(workspace, {"deployer": deployer})


@when(parsers.parse('the Instance pipeline is started with ENV_SPECIFIC_PARAMS merging envSpecificParamsets for "{ns}" with "{paramset}"'))
def esp_merge_env_specific_paramsets(workspace, ns, paramset):
    _run_esp(workspace, {"envSpecificParamsets": {ns: [paramset]}})


# ── Then steps ───────────────────────────────────────────────────────────────

def _load_inv(workspace):
    env_dir = workspace.builder.get_env_dir("test-cluster", "test-env")
    inv_file = env_dir / "Inventory" / "env_definition.yml"
    assert inv_file.exists(), f"env_definition.yml not found at {inv_file}"
    return yaml.safe_load(inv_file.read_text(encoding="utf-8"))


@then("the pipeline completes successfully")
def pipeline_completes_successfully(workspace):
    assert workspace.returncode == 0, (
        f"Pipeline failed with rc={workspace.returncode}\n"
        f"STDOUT:\n{workspace.stdout}\nSTDERR:\n{workspace.stderr}"
    )


@then("the env_definition.yml contains the merged additionalTemplateVariables")
def inv_has_merged_additional_vars(workspace):
    data = _load_inv(workspace)
    atv = (data.get("envTemplate") or {}).get("additionalTemplateVariables") or {}
    assert "MERGED_KEY" in atv, f"MERGED_KEY not found in additionalTemplateVariables: {atv}"
    assert atv["MERGED_KEY"] == "merged-value"


@then(parsers.parse('the env_definition.yml clusterUrl equals "{expected}"'))
def inv_cluster_url_equals(workspace, expected):
    data = _load_inv(workspace)
    actual = (data.get("inventory") or {}).get("clusterUrl")
    assert actual == expected, f"clusterUrl: expected {expected!r}, got {actual!r}"


@then(parsers.parse('the env_definition.yml additionalTemplateVariables contains key "{key}" with value "{value}"'))
def inv_atv_contains_key(workspace, key, value):
    data = _load_inv(workspace)
    atv = (data.get("envTemplate") or {}).get("additionalTemplateVariables") or {}
    assert key in atv, f"Key {key!r} not in additionalTemplateVariables: {atv}"
    assert str(atv[key]) == value, f"Key {key!r}: expected {value!r}, got {atv[key]!r}"


@then(parsers.parse('the env_definition.yml inventory.cloudName equals "{expected}"'))
def inv_cloud_name_equals(workspace, expected):
    data = _load_inv(workspace)
    actual = (data.get("inventory") or {}).get("cloudName")
    assert actual == expected, f"cloudName: expected {expected!r}, got {actual!r}"


@then(parsers.parse('the env_definition.yml inventory.tenantName equals "{expected}"'))
def inv_tenant_name_equals(workspace, expected):
    data = _load_inv(workspace)
    actual = (data.get("inventory") or {}).get("tenantName")
    assert actual == expected, f"tenantName: expected {expected!r}, got {actual!r}"


@then(parsers.parse('the env_definition.yml inventory.deployer equals "{expected}"'))
def inv_deployer_equals(workspace, expected):
    data = _load_inv(workspace)
    actual = (data.get("inventory") or {}).get("deployer")
    assert actual == expected, f"deployer: expected {expected!r}, got {actual!r}"


@then(parsers.parse('the env_definition.yml envTemplate.envSpecificParamsets for "{ns}" contains "{paramset}"'))
def inv_esp_contains(workspace, ns, paramset):
    data = _load_inv(workspace)
    esp = (data.get("envTemplate") or {}).get("envSpecificParamsets") or {}
    ns_list = esp.get(ns) or []
    assert paramset in ns_list, (
        f"envSpecificParamsets[{ns!r}] does not contain {paramset!r}: {ns_list}"
    )
