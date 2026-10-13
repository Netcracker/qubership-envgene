from types import SimpleNamespace

import pytest

from deployment_plan.store_data_provider import StoreDataProvider
from envgenehelper import open_current_env_instance_store
from sd.process_sd import get_appdef_for_app

APPDEF = {
    "name": "application-1",
    "registryName": "registry-1",
    "artifactId": "application-1",
    "groupId": "org.qubership",
    "solutionDescriptor": True,
}

REGDEF = {
    "name": "registry-1",
    "credentialsId": "registry-cred",
    "mavenConfig": {
        "repositoryDomainName": "https://maven.qubership.org/",
        "fullRepositoryUrl": "",
        "targetSnapshot": "snapshot",
        "targetStaging": "staging",
        "targetRelease": "release",
        "releaseGroup": "",
        "snapshotGroup": "",
    },
    "dockerConfig": {
        "snapshotUri": "docker.qubership.org/snapshot",
        "stagingUri": "docker.qubership.org/staging",
        "releaseUri": "docker.qubership.org/release",
        "groupUri": "docker.qubership.org/group",
        "snapshotRepoName": "docker-snapshot",
        "stagingRepoName": "docker-staging",
        "releaseRepoName": "docker-release",
        "groupName": "docker-group",
    },
    "helmConfig": {},
    "helmAppConfig": {},
}


class NoPlugins:
    def run(self, **kwargs):
        return []


@pytest.fixture
def env_instance_store(tmp_path):
    env_dir = tmp_path / "environments" / "cluster-01" / "env-01"
    with open_current_env_instance_store(env_dir, base_dir=tmp_path) as opened_store:
        opened_store.put(tmp_path / "appdefs" / "application-1.yml", dict(APPDEF))
        opened_store.put(tmp_path / "regdefs" / "registry-1.yml", dict(REGDEF))
        yield opened_store


def test_process_sd_reads_app_and_reg_def_from_store(tmp_path, env_instance_store):
    ctx = SimpleNamespace(committed_regdefs_dir=tmp_path / "regdefs", transient_regdefs_dir=None)

    app_def = get_appdef_for_app("application-1:1.0.0", NoPlugins(), ctx)

    assert app_def.name == "application-1"
    assert app_def.registry.name == "registry-1"
    assert not (tmp_path / "appdefs").exists()
    assert "registry" not in env_instance_store.get(tmp_path / "appdefs" / "application-1.yml")


def test_process_sd_fails_for_app_def_absent_in_store(tmp_path, env_instance_store):
    ctx = SimpleNamespace(committed_regdefs_dir=tmp_path / "regdefs", transient_regdefs_dir=None)

    with pytest.raises(FileNotFoundError):
        get_appdef_for_app("absent:1.0.0", NoPlugins(), ctx)


def test_deploy_plan_provider_reads_app_and_reg_def_from_store(tmp_path, env_instance_store):
    provider = StoreDataProvider(root_dir=tmp_path)

    assert provider.get_app_def(application="application-1").registry == "registry-1"
    assert provider.get_reg_def(registry="registry-1").maven["release_repo"] == "release"
