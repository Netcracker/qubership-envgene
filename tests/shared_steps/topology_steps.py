import yaml
from pathlib import Path
from pytest_bdd import then, parsers

@then('the topology context in "parameters.yaml" contains a cluster object with values:')
def verify_topology_cluster_object(workspace, datatable):
    # Fetch the environment name from the extra_env we set earlier
    env_names = workspace.extra_env.get("ENV_NAMES")
    assert env_names, "ENV_NAMES was not set in the workspace"
    
    cluster, env = env_names.split("/")
    
    # The calculator generates effective set in environments/<cluster>/<env>/effective_set
    parameters_yaml_path = Path(workspace.base_dir) / "environments" / cluster / env / "effective_set" / "parameters.yaml"
    
    assert parameters_yaml_path.exists(), f"parameters.yaml not found at {parameters_yaml_path}"
    
    with open(parameters_yaml_path, "r") as f:
        data = yaml.safe_load(f)
        
    topology = data.get("topology", {})
    cluster_obj = topology.get("cluster", {})
    
    # Parse datatable
    # The datatable is a string that represents the table from the feature file
    lines = [line.strip() for line in datatable.strip().split("\n")]
    headers = [col.strip() for col in lines[0].strip("|").split("|")]
    values = [col.strip() for col in lines[1].strip("|").split("|")]
    
    expected = dict(zip(headers, values))
    
    # Assert each value
    for key, expected_value in expected.items():
        actual_value = str(cluster_obj.get(key, ""))
        assert actual_value == expected_value, f"Expected {key} to be '{expected_value}', but got '{actual_value}' in {cluster_obj}"
