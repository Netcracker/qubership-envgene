import os

import pytest
from aiohttp import web
from unittest.mock import patch, Mock

os.environ["DEFAULT_REQUEST_TIMEOUT"] = "0.2"  # for test cases to run quicker
from artifact_searcher.utils import models
from artifact_searcher.artifact import check_artifact_async
from artifact_searcher.artifact import check_artifact
from artifact_searcher.utils.models import FileExtension

TEST_REPO = "https://repo.example.com/repository/"
GROUP_ID = "com.example"
ARTIFACT_ID = "demo"
VERSION = "1.0.0"

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
    app_web.router.add_get(f"{index_path}repo/com/example/app/1.0.0-SNAPSHOT/maven-metadata.xml",
                           maven_metadata_handler)
    app_web.router.add_get(f"{index_path}repo/com/example/app/1.0.0-SNAPSHOT/app-1.0.0-20240702.123456-1.json",
                           maven_metadata_handler)
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

@patch("artifact_searcher.artifact.requests.head")
@patch("artifact_searcher.artifact.create_artifact_name")
@patch("artifact_searcher.artifact.version_to_folder_name")
@patch("artifact_searcher.artifact.MavenConfig.is_nexus")
def test_artifact_found(mock_nexus, mock_folder, mock_name, mock_head):

    mock_nexus.return_value = False
    mock_folder.return_value = VERSION
    mock_name.return_value = "demo-1.0.0.zip"

    response = Mock()
    response.status_code = 200
    mock_head.return_value = response

    result = check_artifact(
        TEST_REPO,
        GROUP_ID,
        ARTIFACT_ID,
        VERSION,
        FileExtension.ZIP
    )

    assert result == (
        "https://repo.example.com/repository/com/example/demo/1.0.0/demo-1.0.0.zip"
    )


@patch("artifact_searcher.artifact.requests.head")
@patch("artifact_searcher.artifact.create_artifact_name")
@patch("artifact_searcher.artifact.version_to_folder_name")
@patch("artifact_searcher.artifact.MavenConfig.is_nexus")
def test_artifact_not_found(mock_nexus, mock_folder, mock_name, mock_head):

    mock_nexus.return_value = False
    mock_folder.return_value = VERSION
    mock_name.return_value = "demo-1.0.0.zip"

    response = Mock()
    response.status_code = 404
    mock_head.return_value = response

    result = check_artifact(
        TEST_REPO,
        GROUP_ID,
        ARTIFACT_ID,
        VERSION,
        FileExtension.ZIP
    )

    assert result is None


@patch("artifact_searcher.artifact.MavenConfig.is_nexus")
@patch("artifact_searcher.artifact.convert_nexus_repo_url_to_index_view")
def test_nexus_repo_conversion(mock_convert, mock_detect):

    mock_detect.return_value = True
    mock_convert.return_value = "https://nexus.example.com/service/rest/repository/browse/"

    check_artifact(
        TEST_REPO,
        GROUP_ID,
        ARTIFACT_ID,
        VERSION,
        FileExtension.ZIP
    )

    mock_convert.assert_called_once()
