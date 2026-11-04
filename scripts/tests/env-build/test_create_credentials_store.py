import copy

import pytest

from build_env.create_credentials import CredentialCollector, create_credentials, getNamespaceCreds, getTenantCreds
from build_env.render_config_env import EnvGenerator
from envgenehelper import CredentialMode, open_current_env_instance_store
from envgenehelper.yaml_helper import readYaml

TENANT = """name: tenant
credential: tenant-cred
deployParameters:
  TENANT_LIST:
    - ${creds.get("tenant-list-cred").username}
    - plain
globalE2EParameters:
  environmentParameters: {}
"""

CLOUD = """name: cloud
defaultCredentialsId: cloud-cred
maasConfig:
  credentialsId: ""
vaultConfig:
  credentialsId: ""
consulConfig:
  tokenSecret: ""
dbaasConfigs:
  - credentialsId: dbaas-cred
deployParameters:
  CLOUD_LIST:
    - ${creds.get("cloud-list-cred").username}
    - nested:
        - ${creds.get("cloud-nested-cred").password}
e2eParameters: {}
technicalConfigurationParameters: {}
"""

NAMESPACE = """name: env-app
credentialsId: ns-cred
deployParameters:
  NS_LIST:
    - ${creds.get("ns-list-cred").username}
e2eParameters: {}
technicalConfigurationParameters: {}
"""

APPLICATION = """name: app
deployParameters:
  APP_LIST:
    - ${creds.get("app-list-cred").username}
    - 1
technicalConfigurationParameters: {}
"""


def test_create_credentials_does_not_change_store_objects(tmp_path):
    env_dir = tmp_path / "environments" / "cluster" / "env"
    paths = {
        env_dir / "tenant.yml": TENANT,
        env_dir / "cloud.yml": CLOUD,
        env_dir / "Applications" / "cloud-app.yml": APPLICATION,
        env_dir / "Namespaces" / "app" / "namespace.yml": NAMESPACE,
        env_dir / "Namespaces" / "app" / "Applications" / "app.yml": APPLICATION,
    }
    with open_current_env_instance_store(env_dir) as objects:
        for path, text in paths.items():
            objects.put(path, readYaml(text))
        snapshot = {path: copy.deepcopy(objects.get(path)) for path in paths}

        create_credentials(env_dir, tmp_path / "environments", readYaml("inventory: {}\nenvTemplate: {}\n"), [], EnvGenerator())

        for path, expected in snapshot.items():
            assert objects.get(path) == expected
        creds = objects.get(env_dir / "Credentials" / "credentials.yml")
    assert {"tenant-list-cred", "cloud-nested-cred", "ns-list-cred", "app-list-cred"} <= set(creds)


@pytest.mark.parametrize("missing_field", ["credential", "globalE2EParameters"])
def test_tenant_without_field_for_credentials_fails(missing_field):
    tenant = readYaml(TENANT)
    del tenant[missing_field]

    with pytest.raises(ValueError):
        getTenantCreds(tenant, "tenant", CredentialCollector(CredentialMode.LOCAL))


def test_namespace_without_credentials_id_fails():
    with pytest.raises(ValueError):
        getNamespaceCreds(readYaml("name: env-core\n"), "tenant", "cloud", "env-core",
                          CredentialCollector(CredentialMode.LOCAL))
