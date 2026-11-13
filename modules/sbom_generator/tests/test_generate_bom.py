import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from aioresponses import aioresponses
from artifact_searcher.artifact import version_to_folder_name
from artifact_searcher.utils.models import (
    AuthConfig, Application, Credentials, DockerConfig, FileExtension, HelmAppConfig, HelmAppConfigV2, MavenConfig,
    MavenConfigV2, Provider, Registry, RegistryV2,
)
from envgenehelper.deploy_plan_adapter import EnvgeneDeployPlan, DeployPlanEntity
from envgenehelper.models import ArtifactCoordinateSource
from sbom_generator.generate_bom import Generator, exclude_resolved_apps, _stable_bom_ref
from sbom_generator.utils.models import ImageType, Service
from tests.utils import load_json, make_app, make_chart_tgz

from effective_set.dd_downloading import download_dd_and_chart_artifacts, resolve_chart_url

APP_RESOLVER_PATH = Path("app_resolver")
ARTIFACTS_PATH = Path("artifacts")
SBOMS_PATH = Path("sboms")
AUTO = ArtifactCoordinateSource.AUTO
REGDEF = ArtifactCoordinateSource.REGDEF
REGISTRY_HELM_BASE = "https://registry.example.com/example.helm.charts"

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
                                  chart_url: str, chart_files: dict[str, str], dd_name: str = "",
                                  chart_status: int = 200, dd_metadata: dict | None = None):
        app_version = next(
            (item.version.split(':')[1] for item in sd if item.version.split(':')[0] == app.name), None)
        input_url = TestSBOMGenerator.create_artifact_url(app=app, app_version=app_version,
                                                          extension=FileExtension.JSON)
        if not dd_name:
            dd_name = app.name
        dd_payload = load_json(ARTIFACTS_PATH.joinpath(dd_name))
        if dd_metadata is not None:
            dd_payload = {**dd_payload, "metadata": {**dd_payload.get("metadata", {}), **dd_metadata}}
        mock_aio_response.head(input_url, payload=dd_payload, status=200)
        mock_aio_response.get(input_url, payload=dd_payload, status=200)
        mock_aio_response.get(chart_url, body=make_chart_tgz(chart_files), status=chart_status)

    @staticmethod
    def download_dd_artifacts(applications: list[Application], app_versions: list[str], tmp_path: Path,
                              artifact_coordinate_source=ArtifactCoordinateSource.AUTO):
        app_by_name = {app.name: app for app in applications}

        def _appdef_for(appver, plugins, ctx=None):
            return app_by_name[appver.split(':')[0]]

        with patch("effective_set.dd_downloading.get_appdef_for_app", side_effect=_appdef_for), \
                patch("effective_set.dd_downloading.get_app_artifacts_dir", return_value=tmp_path):
            dd_artifacts = download_dd_and_chart_artifacts(app_versions, {}, artifact_coordinate_source)
        return dd_artifacts

    def test_generate_bom_by_sd_content(self, mock_aio_response, tmp_path):
        app_vers = [
            DeployPlanEntity(version='sample-om:1.0.0-RELEASE', deploy_postfix='sample-om')
        ]
        sd_content = EnvgeneDeployPlan(entities=app_vers)
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("sd_content_apps"))]

        for app in applications:
            TestSBOMGenerator.create_get_artifacts_mock(
                app, app_vers, mock_aio_response, f"{REGISTRY_HELM_BASE}/sample-om-chart-1.0.0.tgz",
                {"sample-om-chart/charts/sample-api/resource-profiles/dev.yaml": "REPLICAS: 1\n"})
        dd_artifacts = TestSBOMGenerator.download_dd_artifacts(
            applications, [item.version for item in app_vers], tmp_path)

        output = Generator.generate_bom_by_content(sd_content, dd_artifacts, SBOMS_PATH, ArtifactCoordinateSource.AUTO)

        assert 'sample-om:1.0.0-RELEASE' in output.sboms
        sbom = output.sboms['sample-om:1.0.0-RELEASE']
        service = next(c for c in sbom.get('components', []) if c.get('name') == 'sample-api')
        baseline = next(c for c in service['components'] if c.get('name') == 'resource-profile-baselines')
        assert [d['name'] for d in baseline['data']] == ['dev.yaml']
        assert output.registries

    def test_generate_bom_multi_service(self, mock_aio_response, tmp_path):
        app_vers = [
            DeployPlanEntity(version='sample-monitoring:1.2.3-RELEASE', deploy_postfix='sample-monitoring'),
        ]
        sd_content = EnvgeneDeployPlan(entities=app_vers)
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("sub_entity_app"))]
        for app in applications:
            TestSBOMGenerator.create_get_artifacts_mock(
                app, app_vers, mock_aio_response, "https://helm.example.com/charts/sample-monitoring-1.2.3.tgz",
                {"sample-monitoring/charts/metrics-operator/charts/common-lib/Chart.yaml": "name: common-lib\n"})
        dd_artifacts = TestSBOMGenerator.download_dd_artifacts(
            applications, [item.version for item in app_vers], tmp_path)

        output = Generator.generate_bom_by_content(sd_content, dd_artifacts, SBOMS_PATH, ArtifactCoordinateSource.AUTO)

        assert 'sample-monitoring:1.2.3-RELEASE' in output.sboms
        sbom = output.sboms['sample-monitoring:1.2.3-RELEASE']
        component_names = {c.get('name') for c in sbom.get('components', [])}
        assert {'metrics-operator', 'blackbox-exporter'} <= component_names
        assert 'common-lib' not in component_names

    @staticmethod
    def generate_sbom_for_dd_metadata(mock_aio_response, tmp_path, dd_metadata, sbom_dir_path=SBOMS_PATH):
        app_vers = [
                    DeployPlanEntity(version='sample-om:1.0.0-RELEASE', deploy_postfix='sample-om')
                ]
        sd_content = EnvgeneDeployPlan(entities=app_vers)
        sample_om = Application.model_validate(load_json(APP_RESOLVER_PATH.joinpath("sd_content_apps"))[0])
        TestSBOMGenerator.create_get_artifacts_mock(
            sample_om, app_vers, mock_aio_response, f"{REGISTRY_HELM_BASE}/sample-om-chart-1.0.0.tgz",
            {"sample-om-chart/charts/sample-api/resource-profiles/dev.yaml": "REPLICAS: 1\n"},
            dd_metadata=dd_metadata)
        dd_artifacts = TestSBOMGenerator.download_dd_artifacts([sample_om], [app_vers[0].version], tmp_path)
        return Generator.generate_bom_by_content(sd_content, dd_artifacts, sbom_dir_path, AUTO)

    @pytest.mark.parametrize('dd_metadata,expected_layouts', [
        ({'deployContextLayout': 'compact'}, ['compact']),
        ({'deployContextLayout': 'full'}, ['full']),
        ({}, []),
    ])
    def test_dd_deploy_context_layout_is_copied_to_sbom_property(
            self, mock_aio_response, tmp_path, dd_metadata, expected_layouts):
        output = TestSBOMGenerator.generate_sbom_for_dd_metadata(mock_aio_response, tmp_path, dd_metadata)

        dd_component = output.sboms['sample-om:1.0.0-RELEASE']['metadata']['component']['components'][0]
        layouts = [p['value'] for p in dd_component['properties'] if p['name'] == 'deploy_context_layout']
        assert layouts == expected_layouts

    def test_existing_sbom_is_not_regenerated_for_compact_dd(self, mock_aio_response, tmp_path):
        sbom_dir_path = tmp_path / 'sboms'
        existing_sbom_path = sbom_dir_path / 'sample-om' / 'sample-om-1.0.0-RELEASE.sbom.json'
        existing_sbom_path.parent.mkdir(parents=True)
        existing_sbom_path.write_text('{}', encoding='utf-8')

        output = TestSBOMGenerator.generate_sbom_for_dd_metadata(
            mock_aio_response, tmp_path, {'deployContextLayout': 'compact'}, sbom_dir_path)

        assert output.sboms == {}
        assert existing_sbom_path.read_text(encoding='utf-8') == '{}'

    def test_stable_bom_ref_is_deterministic(self):
        assert _stable_bom_ref('service', 'v1') == _stable_bom_ref('service', 'v1')
        assert len(_stable_bom_ref('service', 'v1')) == 16

    def test_downloads_all_dds_but_only_unresolved_app_charts(self, mock_aio_response, tmp_path):
        resolved = 'sample-om:1.0.0-RELEASE'
        missing = 'BUSYBOX-APP:1.0.0-RELEASE'
        app_vers = [DeployPlanEntity(version=v, deploy_postfix='any') for v in (resolved, missing)]
        sample_om = Application.model_validate(load_json(APP_RESOLVER_PATH.joinpath("sd_content_apps"))[0])
        busybox = Application.model_validate(load_json(APP_RESOLVER_PATH.joinpath("busybox_app"))[0])
        sample_om_dd_url = TestSBOMGenerator.create_artifact_url(sample_om, '1.0.0-RELEASE', FileExtension.JSON)
        mock_aio_response.head(sample_om_dd_url, status=200)
        mock_aio_response.get(sample_om_dd_url, payload=load_json(ARTIFACTS_PATH.joinpath("sample-om")), status=200)
        TestSBOMGenerator.create_get_artifacts_mock(
            busybox, app_vers, mock_aio_response, f"{REGISTRY_HELM_BASE}/busybox-app-1.0.0.tgz",
            {"busybox-app/Chart.yaml": "name: busybox-app\n"}, "busybox-app")

        with patch("effective_set.dd_downloading.get_appdef_for_app",
                   side_effect=lambda appver, plugins, ctx=None: busybox if appver == missing else sample_om), \
                patch("effective_set.dd_downloading.get_app_artifacts_dir", return_value=tmp_path):
            dd_artifacts = download_dd_and_chart_artifacts(
                [resolved, missing], {}, ArtifactCoordinateSource.AUTO, unresolved_app_versions=[missing])

        assert [Path(dd.local_target_path).exists() for dd in dd_artifacts] == [True, True]
        assert not (tmp_path / 'sample-om' / '1.0.0-RELEASE' / 'chart').exists()
        assert (tmp_path / 'BUSYBOX-APP' / '1.0.0-RELEASE' / 'chart' / 'busybox-app' / 'Chart.yaml').exists()

    def test_unfetchable_chart_fails_naming_its_url(self, mock_aio_response, tmp_path):
        app_vers = [DeployPlanEntity(version='sample-om:1.0.0-RELEASE', deploy_postfix='sample-om')]
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("sd_content_apps"))]
        TestSBOMGenerator.create_get_artifacts_mock(
            applications[0], app_vers, mock_aio_response, f"{REGISTRY_HELM_BASE}/sample-om-chart-1.0.0.tgz", {},
            chart_status=404)

        with pytest.raises(ValueError, match="sample-om-chart-1.0.0.tgz"):
            TestSBOMGenerator.download_dd_artifacts(applications, ['sample-om:1.0.0-RELEASE'], tmp_path)

    def test_chart_url_from_dd_when_helm_registry_is_present(self):
        dd = {"charts": [{"helm_chart_name": "app", "helm_chart_version": "1.0", "helm_registry": "https://h",
                          "full_chart_name": "https://h/charts/app-1.0.tgz"}]}

        assert resolve_chart_url(dd, self._registry(), {}, AUTO, "app:1.0") == "https://h/charts/app-1.0.tgz"

    def test_chart_url_from_regdef_group_repo_after_delivery(self):
        dd = {"charts": [{"helm_chart_name": "app", "helm_chart_version": "1.0"}]}

        assert (resolve_chart_url(dd, self._registry(), {}, AUTO, "app:1.0")
                == "https://nexus.example.com/nc.helm.charts/app-1.0.tgz")

    def test_chart_url_from_maven_host_for_regdef_v2(self):
        dd = {"charts": [{"helm_chart_name": "app", "helm_chart_version": "1.0"}]}
        registry = RegistryV2(
            name="v2",
            auth_config={"anon": AuthConfig(provider=Provider.NEXUS, auth_method="anonymous")},
            maven_config=MavenConfigV2(repository_domain_name="https://maven.example.com/", auth_config="anon",
                                       target_release="r", target_snapshot="s", target_staging="st"),
            helm_app_config=HelmAppConfigV2(auth_config="anon", repository_domain_name="https://helm.example.com/",
                                            helm_staging_repo_name="", helm_release_repo_name="",
                                            helm_group_repo_name="nc.helm.charts", helm_dev_repo_name=""))

        assert resolve_chart_url(dd, registry, {}, AUTO, "app:1.0") == "https://maven.example.com/nc.helm.charts/app-1.0.tgz"

    def test_chart_url_from_helm_map_repositories_override(self):
        dd = {"charts": [{"helm_chart_name": "app", "helm_chart_version": "1.0"}]}
        helm_map = {"nc.helm.charts": {"url": "https://mirror.example.com/helm/"}}

        assert (resolve_chart_url(dd, self._registry(), helm_map, AUTO, "app:1.0")
                == "https://mirror.example.com/helm/app-1.0.tgz")

    def test_chart_url_ignores_override_for_other_group_repo(self):
        dd = {"charts": [{"helm_chart_name": "app", "helm_chart_version": "1.0"}]}
        helm_map = {"other.helm.charts": {"url": "https://mirror.example.com/helm"}}

        assert (resolve_chart_url(dd, self._registry(), helm_map, AUTO, "app:1.0")
                == "https://nexus.example.com/nc.helm.charts/app-1.0.tgz")

    def test_regdef_ignores_full_chart_name(self):
        dd = {"charts": [{"helm_chart_name": "app", "helm_chart_version": "1.0", "helm_registry": "https://h",
                          "full_chart_name": "https://h/charts/app-1.0.tgz"}]}

        assert (resolve_chart_url(dd, self._registry(), {}, REGDEF, "app:1.0")
                == "https://nexus.example.com/nc.helm.charts/app-1.0.tgz")

    def test_regdef_applies_helm_map_repositories_override(self):
        dd = {"charts": [{"helm_chart_name": "app", "helm_chart_version": "1.0", "helm_registry": "https://h",
                          "full_chart_name": "https://h/charts/app-1.0.tgz"}]}
        helm_map = {"nc.helm.charts": {"url": "https://mirror.example.com/helm"}}

        assert (resolve_chart_url(dd, self._registry(), helm_map, REGDEF, "app:1.0")
                == "https://mirror.example.com/helm/app-1.0.tgz")

    def test_regdef_downloads_chart_from_registry_definition(self, mock_aio_response, tmp_path):
        app_vers = [DeployPlanEntity(version='sample-monitoring:1.2.3-RELEASE', deploy_postfix='sample-monitoring')]
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("sub_entity_app"))]
        TestSBOMGenerator.create_get_artifacts_mock(
            applications[0], app_vers, mock_aio_response, f"{REGISTRY_HELM_BASE}/sample-monitoring-1.2.3.tgz",
            {"sample-monitoring/Chart.yaml": "name: sample-monitoring\n"})

        TestSBOMGenerator.download_dd_artifacts(
            applications, ['sample-monitoring:1.2.3-RELEASE'], tmp_path, REGDEF)

        assert (tmp_path / 'sample-monitoring' / '1.2.3-RELEASE' / 'chart' / 'sample-monitoring' / 'Chart.yaml').exists()

    def test_regdef_emits_image_from_registry_definition(self, mock_aio_response, tmp_path):
        app_vers = [DeployPlanEntity(version='sample-om:1.0.0-RELEASE', deploy_postfix='sample-om')]
        applications = [Application.model_validate(app) for app in
                        load_json(APP_RESOLVER_PATH.joinpath("sd_content_apps"))]
        TestSBOMGenerator.create_get_artifacts_mock(
            applications[0], app_vers, mock_aio_response, f"{REGISTRY_HELM_BASE}/sample-om-chart-1.0.0.tgz", {})
        dd_artifacts = TestSBOMGenerator.download_dd_artifacts(
            applications, ['sample-om:1.0.0-RELEASE'], tmp_path, REGDEF)

        output = Generator.generate_bom_by_content(EnvgeneDeployPlan(entities=app_vers), dd_artifacts, SBOMS_PATH,
                                                   REGDEF)

        service = next(c for c in output.sboms['sample-om:1.0.0-RELEASE']['components'] if c['name'] == 'sample-api')
        props = {p["name"]: p["value"] for p in service["properties"]}
        assert props["full_image_name"] == "registry.example.com:25083/sample-product/sample-api:1.0.0"
        assert props["docker_registry"] == "registry.example.com:25083"

    def test_dd_without_charts_fails(self):
        with pytest.raises(ValueError, match="app:1.0"):
            resolve_chart_url({"charts": []}, self._registry(), {}, AUTO, "app:1.0")

    @pytest.mark.parametrize("chart, missing_field", [
        ({"helm_chart_name": "app", "helm_chart_version": "1.0", "helm_registry": "https://h"}, "full_chart_name"),
        ({"helm_chart_version": "1.0"}, "helm_chart_name"),
        ({"helm_chart_name": "app"}, "helm_chart_version"),
    ])
    def test_chart_without_required_field_fails_naming_app_and_field(self, chart, missing_field):
        with pytest.raises(ValueError, match=rf"app:1\.0 has no charts\[0\]\.{missing_field}"):
            resolve_chart_url({"charts": [chart]}, self._registry(), {}, AUTO, "app:1.0")

    def test_registry_without_group_repo_fails(self):
        dd = {"charts": [{"helm_chart_name": "app", "helm_chart_version": "1.0"}]}
        registry = self._registry()
        registry.helm_app_config = None

        with pytest.raises(ValueError, match="helmGroupRepoName"):
            resolve_chart_url(dd, registry, {}, AUTO, "app:1.0")

    @staticmethod
    def _registry() -> Registry:
        return Registry(
            name="test-registry",
            maven_config=MavenConfig(
                repository_domain_name="https://nexus.example.com/",
                target_release="example.maven.mvn",
                target_snapshot="snapshots",
                target_staging="staging"
            ),
            helm_app_config=HelmAppConfig(helm_group_repo_name="nc.helm.charts")
        )

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
            TestSBOMGenerator.create_get_artifacts_mock(
                app, app_vers, mock_aio_response, f"{REGISTRY_HELM_BASE}/busybox-app-1.0.0.tgz", {}, "busybox-app")
        dd_artifacts = TestSBOMGenerator.download_dd_artifacts(
            applications, [item.version for item in app_vers], tmp_path)

        output = Generator.generate_bom_by_content(sd_content, dd_artifacts, SBOMS_PATH, ArtifactCoordinateSource.AUTO)

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

        service.set_full_image_name(app, "targetRelease", AUTO)

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

        service.set_full_image_name(app, "targetRelease", AUTO)

        assert "//" not in service.full_image_name
        assert service.full_image_name == "nexus.example.com:25080/sample-platform/my-service:build123"

    def test_set_full_image_name_regdef_replaces_embedded_image(self):
        service = Service(
            service_name="my-service",
            image_type=ImageType.image,
            docker_tag="build123",
            docker_repository_name="sample-platform",
            image_name="my-service",
            full_image_name="offsite.example.com:5000/sample-platform/my-service:build123"
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

        service.set_full_image_name(app, "targetRelease", REGDEF)

        assert service.full_image_name == "nexus.example.com:25080/sample-platform/my-service:build123"
        assert service.docker_registry == "nexus.example.com:25080"

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
