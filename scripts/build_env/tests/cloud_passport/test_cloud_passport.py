import pytest
from unittest.mock import patch, MagicMock
from copy import deepcopy
from cloud_passport import process_cloud_definition


cloud_yaml_template = {
    "maasConfig": {"enable": True, "credentialsId": "", "maasUrl": "", "maasInternalAddress": ""},
    "vaultConfig": {"enable": True, "credentialsId": "", "url": ""},
    "dbaasConfigs": [{"enable": True, "credentialsId": "", "apiUrl": "", "aggregatorUrl": ""}],
    "consulConfig": {"enabled": True, "tokenSecret": "", "publicUrl": "", "internalUrl": ""},
    "deployParameters": {},
    "dashboardUrl" : ""
}


passport_yaml_no_services = {
    "cloud": {
        "CLOUD_API_HOST": "api.cluster-01.qubership.org",
        "CLOUD_API_PORT": "6443",
        "CLOUD_DASHBOARD_URL": "https://dashboard.cluster-01.qubership.org"
    }
    # No "maas", "vault", "dbaas", or "consul" sections
}

def test_process_cloud_definition_disable_all_services():
    cloud_yaml = deepcopy(cloud_yaml_template)

    with patch("cloud_passport.openYaml", return_value=cloud_yaml), \
         patch("cloud_passport.writeYamlToFile", MagicMock()), \
         patch("cloud_passport.beautifyYaml", MagicMock()), \
         patch("cloud_passport.mergeDeployParametersFromPassport", MagicMock()), \
         patch("cloud_passport.process_and_update_key", MagicMock()), \
         patch("cloud_passport.store_value_to_yaml", side_effect=lambda d, k, v, c: d.update({k: v})):
        
        process_cloud_definition(passport_yaml_no_services, "/tmp/env_dir", "test-comment")


    assert cloud_yaml["maasConfig"]["enable"] is False
    assert cloud_yaml["vaultConfig"]["enable"] is False
    for cfg in cloud_yaml["dbaasConfigs"]:
        assert cfg["enable"] is False
    assert cloud_yaml["consulConfig"]["enabled"] is False