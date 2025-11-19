import pytest
import aiohttp
from aiohttp import web
from artifact_searcher.utils import models
from artifact_searcher.artifact import resolve_snapshot_version_async, check_artifact_async

class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code

@pytest.mark.parametrize(
    "index_path",
    [
        ("/repository/"),
        ("/service/rest/repository/browse/"),
    ],
)
async def test_resolve_snapshot_version(aiohttp_server, index_path, monkeypatch):
    async def maven_metadata_handler(request):
        return web.Response(
            text="""
            <metadata>
              <versioning>
                <snapshotVersions>
                  <snapshotVersion>
                    <classifier></classifier>
                    <extension>pom</extension>
                    <value>1.0.0-20240702.123456-3</value>
                  </snapshotVersion>
                  <snapshotVersion>
                    <classifier>graph</classifier>
                    <extension>json</extension>
                    <value>1.0.0-20240702.123456-2</value>
                  </snapshotVersion>
                  <snapshotVersion>
                    <classifier></classifier>
                    <extension>json</extension>
                    <value>1.0.0-20240702.123456-1</value>
                  </snapshotVersion>
                </snapshotVersions>
              </versioning>
            </metadata>
            """,
            content_type="application/xml",
        )

    app_web = web.Application()
    app_web.router.add_get(f"{index_path}repo/com/example/app/1.0.0-SNAPSHOT/maven-metadata.xml", maven_metadata_handler)
    app_web.router.add_get(f"{index_path}repo/com/example/app/1.0.0-SNAPSHOT/app-1.0.0-20240702.123456-1.json", maven_metadata_handler)
    server = await aiohttp_server(app_web)

    base_url = str(server.make_url("/repository/"))

    if index_path.startswith("/service/rest/"):
        status_url = str(server.make_url("/service/rest/v1/status"))
        def mock_get(url, *args, **kwargs):
            if url == status_url:
                return MockResponse(200)
        monkeypatch.setattr("artifact_searcher.utils.models.requests.get", mock_get)

    mvn_cfg = models.MavenConfig(
        target_snapshot="repo",
        target_staging="repo",
        target_release="repo",
        repository_domain_name=base_url,
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
    )
    app = models.Application(
        name="app",
        artifact_id="app",
        group_id="com.example",
        registry=reg,
        solution_descriptor=False,
    )

    result = await check_artifact_async(app, models.FileExtension.JSON, "1.0.0-SNAPSHOT")
    assert result is not None
    full_url, _ = result

    sample_url = f"{base_url.rstrip('/repository/')}{index_path}repo/com/example/app/1.0.0-SNAPSHOT/app-1.0.0-20240702.123456-1.json"
    assert full_url == sample_url, f"expected: {sample_url}, received: {full_url}"

