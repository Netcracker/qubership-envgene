
import pytest
import os
os.environ["CI_PROJECT_DIR"] = os.path.abspath("../../test_data")

from envgenehelper import *
from creds_rotation_handler import cred_rotation
import yaml

test_data = [
      ("cluster-02", "env-01")
]

g_inventory_dir = getAbsPath("../../test_data")
g_test_dir = getAbsPath("../../tmpcred/cred_test/")
g_cred_dir = getAbsPath("../../test_data/test_cred_rotation")


@pytest.fixture(scope="function")
def setup_env(cluster_name, env_name):
    delete_dir(getAbsPath("../../tmpcred/"))
    copy_path(g_inventory_dir, g_test_dir)
    os.rename(f"{g_test_dir}/test_environments", f"{g_test_dir}/environments")
    os.environ["CLUSTER_NAME"] = cluster_name
    os.environ["ENV_NAME"] = env_name
    with open(f"{g_cred_dir}/payload.json") as f:
        os.environ["CRED_ROTATION_PAYLOAD"] = f.read()
    os.environ["CI_PROJECT_DIR"] = f"{g_test_dir}"
    yield
    delete_dir(getAbsPath("../../tmpcred/"))

@pytest.mark.parametrize("cluster_name, env_name", test_data)
def test_rotation_fails_without_force(setup_env, cluster_name, env_name):
    os.environ["CRED_ROTATION_FORCE"] = "false"
    with pytest.raises(Exception) as exc_info:
        cred_rotation()
    assert "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled" in str(exc_info.value)
    with open(f"{g_cred_dir}/affected-sensitive-parameters.yaml") as f:
        expected = yaml.safe_load(f)
    with open(f"{g_test_dir}/affected-sensitive-parameters.yaml") as f:
        generated = yaml.safe_load(f)
    assert expected == generated

@pytest.mark.parametrize("cluster_name, env_name", test_data)
def test_secret_changed_present(setup_env, cluster_name, env_name):
    os.environ["CRED_ROTATION_FORCE"] = "true"
    cred_rotation()
    with open(f"{g_test_dir}/environments/cluster-02/credentials/sample-cloud-name-creds.yml") as f:
        content = f.read()
    assert "secretChanged" in content, "'secretChanged' not found in YAML file"
    assert "userChanged" in content, "'userChanged' not found in YAML file"
    assert "passwordChanged" in content, "'passwordChanged' not found in YAML file"