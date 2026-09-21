import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from aioresponses import aioresponses
from artifact_searcher.artifact import version_to_folder_name
from artifact_searcher.utils.models import (
    AuthConfig, Application, Credentials, DockerConfig, FileExtension, MavenConfig, MavenConfigV2,
    Provider, Registry, RegistryV2,
)
from envgenehelper.deploy_plan_adapter import EnvgeneDeployPlan, DeployPlanEntity
from sbom_generator.generate_bom import Generator, exclude_resolved_apps, _stable_bom_ref
from sbom_generator.utils.models import ImageType, Service
from tests.utils import load_json, load_zip, make_app

from effective_set.dd_downloading import download_dd_and_zip_artifacts

APP_RESOLVER_PATH = Path("app_resolver")
ARTIFACTS_PATH = Path("artifacts")
SBOMS_PATH = Path("sboms")

cred = Credentials(username="", password="")


@pytest.fixture
def mock_aio_response():
    with aioresponses() as m:
        yield m


class TestSBOMGenerator:

    @pytest.fixture(autouse=True)
    def mock_cred_config(self):
        with patch("envgenehelper.get_cred_config", return_value={}):
            yield

    @staticmethod
    def create_artifact_url(app: Application, app_version: str, extension: FileExtension):
        domain = app.registry.maven_config.repository_domain_name
        repo = app.registry.maven_config.target_release
        folder = version_to_folder_name(version=app_version)
        domain = domain.rstrip('/')
        input_url = (f"{domain}/{repo}/{app.group_id.replace('.', '/')}/{app.artifact_id}"
                     f"/{folder}/{app.artifact_id}-{app_version}.{extension.value}")
        return input_url

    @staticmethod
    def create_get_artifacts_mock(app: Application, sd: list[DeployPlanEntity], mock_aio_response,
                                  dd_name: str = "", zip_name: str = ""):
        app_version = next(
            (item.version.split(':')[1] for item in sd if item.version.split(':')[0] == app.name), None)
        input_url = TestSBOMGenerator.create_artifact_url(app=app, app_version=app_version,
                                                          extension=FileExtension.JSON)
        if not dd_name:
            dd_name = app.name
        mock_aio_response.head(input_url, payload=load_json(ARTIFACTS_PATH.joinpath(dd_name)), status=200)
        mock_aio_response.get(input_url, payload=load_json(ARTIFACTS_PATH.joinpath(dd_name)), status=200)
        if not zip_name:
            zip_name = app.name
        input_url = TestSBOMGenerator.create_artifact_url(app=app, app_version=app_version,
                                                          extension=FileExtension.ZIP)
        mock_aio_response.get(input_url, body=load_zip(ARTIFACTS_PATH.joinpath(zip_name)), status=200)

    @staticmethod
    def download_dd_artifacts(applications: list[Application], app_versions: list[str], tmp_path: Path):
        app_by_name = {app.name: app for app in applications}

        def _appdef_for(appver, plugins):
            return app_by_name[appver.split(':')[0]]

        with patch("effective_set.dd_downloading.get_appdef_for_app", side_effect=_appdef_for), \
                patch("effective_set.dd_downloading.get_app_artifacts_dir", return_value=tmp_path):
            dd_artifacts, _ = download_dd_and_zip_artifacts(app_versions)
        return dd_artifacts

    def test_generate_bom_by_sd_content(self, mock_aio_response, tmp_path):
        app_vers = [
            DeployPlanEntity(version='sample-om:1.0.0-RELEASE', deploy_postfix='sample-om')
        ]
        sd_content = EnvgeneDeployPlan(entities=app_vers)
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("sd_content_apps"))]

        for app in applications:
            TestSBOMGenerator.create_get_artifacts_mock(app, app_vers, mock_aio_response)
        dd_artifacts = TestSBOMGenerator.download_dd_artifacts(
            applications, [item.version for item in app_vers], tmp_path)

        output = Generator.generate_bom_by_content(sd_content, dd_artifacts, SBOMS_PATH)

        assert 'sample-om:1.0.0-RELEASE' in output.sboms
        sbom = output.sboms['sample-om:1.0.0-RELEASE']
        component_names = {c.get('name') for c in sbom.get('components', [])}
        assert 'sample-api' in component_names
        assert output.registries

    def test_generate_bom_multi_service(self, mock_aio_response, tmp_path):
        app_vers = [
            DeployPlanEntity(version='sample-monitoring:1.2.3-RELEASE', deploy_postfix='sample-monitoring'),
        ]
        sd_content = EnvgeneDeployPlan(entities=app_vers)
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("sub_entity_app"))]
        for app in applications:
            TestSBOMGenerator.create_get_artifacts_mock(app, app_vers, mock_aio_response)
        dd_artifacts = TestSBOMGenerator.download_dd_artifacts(
            applications, [item.version for item in app_vers], tmp_path)

        output = Generator.generate_bom_by_content(sd_content, dd_artifacts, SBOMS_PATH)

        assert 'sample-monitoring:1.2.3-RELEASE' in output.sboms
        sbom = output.sboms['sample-monitoring:1.2.3-RELEASE']
        component_names = {c.get('name') for c in sbom.get('components', [])}
        assert 'metrics-operator' in component_names
        assert 'blackbox-exporter' in component_names

    def test_stable_bom_ref_is_deterministic(self):
        assert _stable_bom_ref('service', 'v1') == _stable_bom_ref('service', 'v1')
        assert len(_stable_bom_ref('service', 'v1')) == 16

    def test_v2_docker_config_compatibility(self):
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("v2_docker_apps"))]

        assert len(applications) == 1
        app = applications[0]

        assert app.name == 'sample-om'
        assert app.artifact_id == 'sample-om'
        assert app.group_id == 'com.company.product.bss.om'
        assert isinstance(app.registry, RegistryV2)
        assert app.registry.version == '2.0'
        assert app.registry.maven_config.repository_domain_name == 'https://registry.example.com/'
        assert app.registry.docker_config.snapshot_uri == 'registry.example.com:25081'

    def test_v1_registry_auth_unified_interface(self):
        env_creds = {
            "test-cred": {
                "data": {
                    "username": "user",
                    "password": "pass"
                }
            }
        }

        registry = Registry(
            name="test-registry",
            credentials_id="test-cred",
            maven_config=MavenConfig(
                repository_domain_name="https://nexus.example.com",
                target_release="example.maven.mvn",
                target_snapshot="snapshots",
                target_staging="staging"
            ),
            docker_config=DockerConfig()
        )

        auth_headers = registry.resolve_auth(env_creds)

        assert auth_headers is not None
        assert "Authorization" in auth_headers
        expected_token = base64.b64encode(b"user:pass").decode()
        assert auth_headers["Authorization"] == f"Basic {expected_token}"

    def test_v2_registry_auth_unified_interface(self):
        env_creds = {
            "nexus-cred": {
                "type": "user_pass",
                "data": {
                    "username": "nexususer",
                    "password": "nexuspass"
                }
            }
        }

        registry = RegistryV2(
            name="test-v2-registry",
            version="2.0",
            auth_config={
                "nexus-auth": AuthConfig(
                    credentials_id="nexus-cred",
                    provider=Provider.NEXUS,
                    auth_method="user_pass"
                )
            },
            maven_config=MavenConfigV2(
                repository_domain_name="https://nexus.example.com/repository/",
                auth_config="nexus-auth",
                target_release="example.maven.mvn",
                target_snapshot="snapshots",
                target_staging="staging"
            )
        )

        auth_headers = registry.resolve_auth(env_creds)

        assert auth_headers is not None
        assert "Authorization" in auth_headers

    def test_image_no_namespace_no_double_slash_in_sbom(self, mock_aio_response, tmp_path):
        app_version = "1.0.0-RELEASE"
        app_vers = [
            DeployPlanEntity(version=f'BUSYBOX-APP:{app_version}', deploy_postfix='BUSYBOX-APP')
        ]
        sd_content = EnvgeneDeployPlan(entities=app_vers)
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("busybox_app"))]

        for app in applications:
            TestSBOMGenerator.create_get_artifacts_mock(app, app_vers, mock_aio_response, "busybox-app", "busybox-app")
        dd_artifacts = TestSBOMGenerator.download_dd_artifacts(
            applications, [item.version for item in app_vers], tmp_path)

        output = Generator.generate_bom_by_content(sd_content, dd_artifacts, SBOMS_PATH)

        sbom_key = next(iter(output.sboms))
        components = output.sboms[sbom_key].get("components", [])
        busybox = next((c for c in components if c.get("name") == "busybox"), None)

        assert busybox is not None
        props = {p["name"]: p["value"] for p in busybox.get("properties", [])}
        full_image_name = props.get("full_image_name", "")

        assert "//" not in full_image_name
        assert full_image_name == "registry.example.com:25083/busybox:1.38.0"

    def test_set_full_image_name_no_namespace_no_double_slash(self):
        service = Service(
            service_name="busybox",
            image_type=ImageType.image,
            docker_tag="1.38.0",
            docker_repository_name="",
            image_name="busybox",
            full_image_name=""
        )
        app = MagicMock()
        app.name = "test-app"
        app.registry.name = "test-registry"
        app.registry.docker_config.model_dump.return_value = {
            "releaseUri": "nexus.example.com:25080",
            "snapshotUri": "",
            "stagingUri": "",
            "groupUri": ""
        }

        service.set_full_image_name(app, "targetRelease")

        assert "//" not in service.full_image_name
        assert service.full_image_name == "nexus.example.com:25080/busybox:1.38.0"

    def test_set_full_image_name_with_namespace(self):
        service = Service(
            service_name="my-service",
            image_type=ImageType.image,
            docker_tag="build123",
            docker_repository_name="sample-platform",
            image_name="my-service",
            full_image_name=""
        )
        app = MagicMock()
        app.name = "test-app"
        app.registry.name = "test-registry"
        app.registry.docker_config.model_dump.return_value = {
            "releaseUri": "nexus.example.com:25080",
            "snapshotUri": "",
            "stagingUri": "",
            "groupUri": ""
        }

        service.set_full_image_name(app, "targetRelease")

        assert "//" not in service.full_image_name
        assert service.full_image_name == "nexus.example.com:25080/sample-platform/my-service:build123"

    def test_both_v1_v2_registries_have_resolve_auth(self):
        v1_registry = Registry(
            name="v1",
            maven_config=MavenConfig(
                repository_domain_name="https://test.com",
                target_release="example.maven.mvn",
                target_snapshot="snapshots",
                target_staging="staging"
            ),
            docker_config=DockerConfig()
        )

        v2_registry = RegistryV2(
            name="v2",
            version="2.0",
            auth_config={
                "anon": AuthConfig(
                    provider=Provider.ARTIFACTORY,
                    auth_method="anonymous"
                )
            },
            maven_config=MavenConfigV2(
                repository_domain_name="https://test.com/repository/",
                auth_config="anon",
                target_release="example.maven.mvn",
                target_snapshot="snapshots",
                target_staging="staging"
            )
        )

        assert callable(v1_registry.resolve_auth)
        assert callable(v2_registry.resolve_auth)
        assert v1_registry.resolve_auth({}) is None
        assert v2_registry.resolve_auth({}) is None

    def test_exclude_resolved_apps_returns_only_missing(self, tmp_path):
        existing_app = make_app('sample-core:1.0.0')
        missing_app = make_app('sample-access:1.0.0')

        sbom_dir = tmp_path / 'sboms' / 'sample-core'
        sbom_dir.mkdir(parents=True)
        (sbom_dir / 'sample-core-1.0.0.sbom.json').touch()

        sd = EnvgeneDeployPlan(entities=[existing_app, missing_app])

        result = exclude_resolved_apps(sd, tmp_path / 'sboms')

        assert result == [missing_app]

    def test_exclude_resolved_apps_all_missing(self, tmp_path):
        apps = [make_app('sample-core:1.0.0'), make_app('sample-access:1.0.0')]
        sd = EnvgeneDeployPlan(entities=apps)

        result = exclude_resolved_apps(sd, tmp_path / 'sboms')

        assert result == apps

    def test_exclude_resolved_apps_all_resolved(self, tmp_path):
        apps = [make_app('sample-core:1.0.0'), make_app('sample-access:1.0.0')]

        for app in apps:
            app_name = app.version.split(':')[0]
            app_ver_filename = app.version.replace(':', '-')
            sbom_dir = tmp_path / 'sboms' / app_name
            sbom_dir.mkdir(parents=True)
            (sbom_dir / f'{app_ver_filename}.sbom.json').touch()

        sd = EnvgeneDeployPlan(entities=apps)

        result = exclude_resolved_apps(sd, tmp_path / 'sboms')

        assert result == []
