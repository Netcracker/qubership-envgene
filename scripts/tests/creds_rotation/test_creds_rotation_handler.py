from envgenehelper.errors import ValidationError
import pytest
import os

from creds_rotation.utils.error_constants import ErrorCodes, ErrorMessages
from scripts.tests.base_test import BaseTest
from envgenehelper import copy_path, delete_dir, json
from creds_rotation.creds_rotation_handler import run_cred_rotation
import yaml

test_data = [
    ("cluster-02", "env-01")
]

g_inventory_dir = str(BaseTest.test_data_dir)
g_test_dir = str(BaseTest.output_dir / "tmpcred" / "cred_test")
g_cred_dir = str(BaseTest.test_data_dir / "test_cred_rotation")
os.environ["CI_PROJECT_DIR"] = g_inventory_dir


@pytest.fixture(scope="function")
def setup_env(cluster_name, env_name):
    delete_dir(g_test_dir)
    copy_path(g_inventory_dir, g_test_dir)
    os.rename(f"{g_test_dir}/test_environments", f"{g_test_dir}/environments")
    os.remove(f"{g_test_dir}/configuration/secret-stores.yml")
    os.environ["CLUSTER_NAME"] = cluster_name
    os.environ["ENVIRONMENT_NAME"] = env_name
    with open(f"{g_cred_dir}/payload.json") as f:
        os.environ["CRED_ROTATION_PAYLOAD"] = f.read()
    os.environ["CI_PROJECT_DIR"] = f"{g_test_dir}"
    yield
    delete_dir(g_test_dir)


@pytest.mark.parametrize("cluster_name, env_name", test_data)
def test_rotation_fails_without_force(setup_env, cluster_name, env_name):
    os.environ["CRED_ROTATION_FORCE"] = "false"
    with pytest.raises(Exception) as exc_info:
        run_cred_rotation()
    assert "Credentials updates are skipped because CRED_ROTATION_FORCE is not enabled" in str(exc_info.value)
    with open(f"{g_cred_dir}/affected-sensitive-parameters.yaml") as f:
        expected = yaml.safe_load(f)
    with open(f"{g_test_dir}/affected-sensitive-parameters.yaml") as f:
        generated = yaml.safe_load(f)
    assert expected == generated


@pytest.mark.parametrize("cluster_name, env_name", test_data)
def test_secret_changed_present(setup_env, cluster_name, env_name):
    os.environ["CRED_ROTATION_FORCE"] = "true"
    run_cred_rotation()
    with open(f"{g_test_dir}/environments/cluster-02/credentials/sample-cloud-name-creds.yml") as f:
        content = f.read()
    assert "secretChanged" in content, "'secretChanged' not found in YAML file"
    assert "userChanged" in content, "'userChanged' not found in YAML file"
    assert "passwordChanged" in content, "'passwordChanged' not found in YAML file"


@pytest.mark.parametrize("cluster_name, env_name", [("cluster-01", "env-extcred")])
def test_fail_rotation_external_cred(setup_env, cluster_name, env_name):
    copy_path(f"{g_inventory_dir}/configuration/secret-stores.yml", f"{g_test_dir}/configuration")
    os.environ["CRED_ROTATION_FORCE"] = "true"
    os.environ["CRED_ROTATION_PAYLOAD"] = "not-a-json-payload"
    with pytest.raises(ValidationError) as exc_info:
        run_cred_rotation()
    assert ErrorMessages.EXTERNAL_MODE_NOT_SUPPORTED in str(exc_info.value)
    assert exc_info.value.error_code == ErrorCodes.INVALID_STATE_CODE
    assert not os.path.exists(f"{g_test_dir}/affected-sensitive-parameters.yaml")