import yaml
from pathlib import Path
from pytest_bdd import then, parsers


def _get_parameters_yaml(workspace) -> tuple:
    """Return (path, data) for the topology parameters.yaml for the current ENV_NAMES."""
    env_names = workspace.extra_env.get("ENV_NAMES")
    assert env_names, "ENV_NAMES was not set in the workspace"
    cluster, env = env_names.split("/")

    # The effective-set-generator writes topology/parameters.yaml under effective-set/
    primary = Path(workspace.base_dir) / "environments" / cluster / env / "effective-set" / "topology" / "parameters.yaml"
    fallback = Path(workspace.base_dir) / "environments" / cluster / env / "effective-set" / "parameters.yaml"

    path = primary if primary.exists() else fallback
    assert path.exists(), (
        f"parameters.yaml not found. Tried:\n  {primary}\n  {fallback}\n"
        f"Workspace stderr:\n{workspace.stderr[-2000:]}"
    )
    with open(path) as f:
        data = yaml.safe_load(f)
    return path, data


@then('the topology context in "parameters.yaml" contains a cluster object with values:')
def verify_topology_cluster_object(workspace, datatable):
    _, data = _get_parameters_yaml(workspace)

    # The Java effective-set-generator outputs 'cluster' at the top level of parameters.yaml,
    # NOT nested under a 'topology' key. Read it directly.
    cluster_obj = data.get("cluster", {})

    # datatable is a list of lists: [[header1, header2, ...], [val1, val2, ...]]
    if isinstance(datatable, list):
        headers = datatable[0]
        values = datatable[1]
        expected = dict(zip(headers, values))
    else:
        # Legacy string format
        lines = [line.strip() for line in str(datatable).strip().split("\n")]
        headers = [col.strip() for col in lines[0].strip("|").split("|")]
        values = [col.strip() for col in lines[1].strip("|").split("|")]
        expected = dict(zip(headers, values))

    # Assert each value
    for key, expected_value in expected.items():
        actual_value = str(cluster_obj.get(key, ""))
        assert actual_value == expected_value, (
            f"Expected {key} to be '{expected_value}', but got '{actual_value}' in cluster object: {cluster_obj}"
        )


@then('the cluster object in "parameters.yaml" has null or empty values for api_url, api_port, public_url, and protocol')
def verify_topology_cluster_null(workspace):
    """TC-CETC-007: When cloud.yml has no URL/port fields, the generator outputs None for those keys."""
    _, data = _get_parameters_yaml(workspace)
    cluster_obj = data.get("cluster", {})

    for key in ("api_url", "api_port", "public_url", "protocol"):
        value = cluster_obj.get(key)
        assert value is None or value == "" or value == "None", (
            f"Expected '{key}' to be null/empty, but got: '{value}' in cluster object: {cluster_obj}"
        )
