import os

import pytest
from aiohttp import web

os.environ["DEFAULT_REQUEST_TIMEOUT"] = "0.2"  # for test cases to run quicker
from artifact_searcher.utils import models
from artifact_searcher.artifact import check_artifact_async, _parse_snapshot_version


class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code


@pytest.mark.parametrize(
    "index_path",
    [
        ("/repository/"),
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


async def test_v2_registry_routes_to_cloud_auth(monkeypatch):
    auth_cfg = models.AuthConfig(
        credentials_id="aws-creds",
        provider="aws",
        auth_method="secret",
        aws_domain="test-domain",
        aws_region="us-east-1",
    )
    mvn_cfg = models.MavenConfig(
        target_snapshot="snapshots",
        target_staging="staging",
        target_release="releases",
        repository_domain_name="https://test.codeartifact.us-east-1.amazonaws.com/maven/repo/",
        auth_config="aws-maven",
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="aws-registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
        version="2.0",
        auth_config={"aws-maven": auth_cfg},
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=reg,
        solution_descriptor=False,
    )
    env_creds = {"aws-creds": {"username": "key", "password": "secret"}}

    async def mock_v2_async(*args, **kwargs):
        return ("http://url", ("v2_downloaded", "/tmp/artifact.json"))

    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v2_async", mock_v2_async)

    result = await check_artifact_async(app, models.FileExtension.JSON, "1.0.0", env_creds=env_creds)
    assert result is not None
    assert result[1][0] == "v2_downloaded"


async def test_v2_registry_fallback_to_v1_on_error(monkeypatch):
    """Test V2 falls back to V1 when V2 search fails"""
    auth_cfg = models.AuthConfig(
        credentials_id="aws-creds",
        provider="aws",
        auth_method="secret",
        aws_domain="test-domain",
        aws_region="us-east-1",
    )
    mvn_cfg = models.MavenConfig(
        target_snapshot="snapshots",
        target_staging="staging",
        target_release="releases",
        repository_domain_name="https://test.codeartifact.us-east-1.amazonaws.com/maven/repo/",
        auth_config="aws-maven",
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="aws-registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
        version="2.0",
        auth_config={"aws-maven": auth_cfg},
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=reg,
        solution_descriptor=False,
    )
    env_creds = {"aws-creds": {"username": "key", "password": "secret"}}

    async def mock_v2_async(*args, **kwargs):
        raise Exception("V2 cloud auth failed")

    async def mock_v1_async(*args, **kwargs):
        return ("http://v1-url", ("v1_repo", "v1_pointer"))

    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v2_async", mock_v2_async)
    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v1_async", mock_v1_async)

    result = await check_artifact_async(app, models.FileExtension.JSON, "1.0.0", env_creds=env_creds)
    assert result is not None
    assert result[0] == "http://v1-url"
    assert result[1][0] == "v1_repo"


async def test_v1_registry_skips_v2(monkeypatch):
    """Test V1 registry (version=1.0) goes directly to V1 search"""
    mvn_cfg = models.MavenConfig(
        target_snapshot="snapshots",
        target_staging="staging",
        target_release="releases",
        repository_domain_name="https://nexus.example.com/repository/",
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="nexus-registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
        version="1.0",
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=reg,
        solution_descriptor=False,
    )

    v2_called = False
    v1_called = False

    async def mock_v2_async(*args, **kwargs):
        nonlocal v2_called
        v2_called = True
        return None

    async def mock_v1_async(*args, **kwargs):
        nonlocal v1_called
        v1_called = True
        return ("http://v1-url", ("v1_repo", "v1_pointer"))

    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v2_async", mock_v2_async)
    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v1_async", mock_v1_async)

    result = await check_artifact_async(app, models.FileExtension.JSON, "1.0.0")
    
    assert v1_called
    assert not v2_called
    assert result is not None


async def test_v2_missing_env_creds_fallback(monkeypatch):
    """Test V2 with AWS/GCP but no env_creds falls back to V1"""
    auth_cfg = models.AuthConfig(
        credentials_id="aws-creds",
        provider="aws",
        auth_method="secret",
        aws_domain="test-domain",
        aws_region="us-east-1",
    )
    mvn_cfg = models.MavenConfig(
        target_snapshot="snapshots",
        target_staging="staging",
        target_release="releases",
        repository_domain_name="https://test.codeartifact.us-east-1.amazonaws.com/maven/repo/",
        auth_config="aws-maven",
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="aws-registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
        version="2.0",
        auth_config={"aws-maven": auth_cfg},
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=reg,
        solution_descriptor=False,
    )

    async def mock_v1_async(*args, **kwargs):
        return ("http://v1-url", ("v1_repo", "v1_pointer"))

    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v1_async", mock_v1_async)

    # Call without env_creds
    result = await check_artifact_async(app, models.FileExtension.JSON, "1.0.0")
    
    assert result is not None
    assert result[0] == "http://v1-url"


async def test_v2_missing_auth_config_fallback(monkeypatch):
    """Test V2 without auth_config falls back to V1"""
    mvn_cfg = models.MavenConfig(
        target_snapshot="snapshots",
        target_staging="staging",
        target_release="releases",
        repository_domain_name="https://test.codeartifact.us-east-1.amazonaws.com/maven/repo/",
        # No auth_config
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="aws-registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
        version="2.0",
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=reg,
        solution_descriptor=False,
    )
    env_creds = {"aws-creds": {"username": "key", "password": "secret"}}

    async def mock_v1_async(*args, **kwargs):
        return ("http://v1-url", ("v1_repo", "v1_pointer"))

    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v1_async", mock_v1_async)

    result = await check_artifact_async(app, models.FileExtension.JSON, "1.0.0", env_creds=env_creds)
    
    assert result is not None
    assert result[0] == "http://v1-url"


async def test_v2_gcp_registry(monkeypatch):
    """Test V2 with GCP Artifact Registry"""
    auth_cfg = models.AuthConfig(
        credentials_id="gcp-creds",
        provider="gcp",
        auth_method="service_account",
        gcp_project="test-project",
        gcp_location="us-central1",
        gcp_repository="test-repo",
    )
    mvn_cfg = models.MavenConfig(
        target_snapshot="snapshots",
        target_staging="staging",
        target_release="releases",
        repository_domain_name="https://us-central1-maven.pkg.dev/test-project/test-repo/",
        auth_config="gcp-maven",
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="gcp-registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
        version="2.0",
        auth_config={"gcp-maven": auth_cfg},
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=reg,
        solution_descriptor=False,
    )
    env_creds = {"gcp-creds": {"username": "_json_key", "password": '{"type": "service_account"}'}}

    async def mock_v2_async(*args, **kwargs):
        return ("http://gcp-url", ("v2_downloaded", "/tmp/artifact.json"))

    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v2_async", mock_v2_async)

    result = await check_artifact_async(app, models.FileExtension.JSON, "1.0.0", env_creds=env_creds)
    
    assert result is not None
    assert result[1][0] == "v2_downloaded"


async def test_check_artifact_async_with_classifier(monkeypatch):
    """Test check_artifact_async passes classifier parameter correctly"""
    mvn_cfg = models.MavenConfig(
        target_snapshot="snapshots",
        target_staging="staging",
        target_release="releases",
        repository_domain_name="https://nexus.example.com/repository/",
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="nexus-registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=reg,
        solution_descriptor=False,
    )

    classifier_passed = None

    async def mock_v1_async(*args, **kwargs):
        nonlocal classifier_passed
        classifier_passed = kwargs.get('classifier', args[4] if len(args) > 4 else "")
        return ("http://url", ("repo", "pointer"))

    monkeypatch.setattr("artifact_searcher.artifact._check_artifact_v1_async", mock_v1_async)

    await check_artifact_async(app, models.FileExtension.JSON, "1.0.0", classifier="sources")
    
    assert classifier_passed == "sources"


def test_parse_snapshot_version_with_matching_extension():
    """Test _parse_snapshot_version finds matching extension"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <metadata>
      <versioning>
        <snapshotVersions>
          <snapshotVersion>
            <classifier></classifier>
            <extension>json</extension>
            <value>1.0.0-20240702.123456-1</value>
          </snapshotVersion>
          <snapshotVersion>
            <classifier></classifier>
            <extension>zip</extension>
            <value>1.0.0-20240702.123456-2</value>
          </snapshotVersion>
        </snapshotVersions>
      </versioning>
    </metadata>
    """
    
    dummy_registry = models.Registry(
        name="dummy",
        maven_config=models.MavenConfig(
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases",
            repository_domain_name="http://dummy.repo/"
        ),
        docker_config=models.DockerConfig()
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=dummy_registry,
        solution_descriptor=False,
    )
    
    result = _parse_snapshot_version(metadata_xml, app, 1, models.FileExtension.JSON, "1.0.0-SNAPSHOT")
    
    assert result == "1.0.0-20240702.123456-1"


def test_parse_snapshot_version_with_classifier():
    """Test _parse_snapshot_version finds matching extension and classifier"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <metadata>
      <versioning>
        <snapshotVersions>
          <snapshotVersion>
            <classifier></classifier>
            <extension>json</extension>
            <value>1.0.0-20240702.123456-1</value>
          </snapshotVersion>
          <snapshotVersion>
            <classifier>sources</classifier>
            <extension>json</extension>
            <value>1.0.0-20240702.123456-2</value>
          </snapshotVersion>
        </snapshotVersions>
      </versioning>
    </metadata>
    """
    
    dummy_registry = models.Registry(
        name="dummy",
        maven_config=models.MavenConfig(
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases",
            repository_domain_name="http://dummy.repo/"
        ),
        docker_config=models.DockerConfig()
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=dummy_registry,
        solution_descriptor=False,
    )
    
    result = _parse_snapshot_version(metadata_xml, app, 1, models.FileExtension.JSON, "1.0.0-SNAPSHOT", "sources")
    
    assert result == "1.0.0-20240702.123456-2"


def test_parse_snapshot_version_no_matching_version():
    """Test _parse_snapshot_version returns None when no match found"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <metadata>
      <versioning>
        <snapshotVersions>
          <snapshotVersion>
            <classifier></classifier>
            <extension>zip</extension>
            <value>1.0.0-20240702.123456-1</value>
          </snapshotVersion>
        </snapshotVersions>
      </versioning>
    </metadata>
    """
    
    dummy_registry = models.Registry(
        name="dummy",
        maven_config=models.MavenConfig(
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases",
            repository_domain_name="http://dummy.repo/"
        ),
        docker_config=models.DockerConfig()
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=dummy_registry,
        solution_descriptor=False,
    )
    
    # Looking for JSON but only ZIP available
    result = _parse_snapshot_version(metadata_xml, app, 1, models.FileExtension.JSON, "1.0.0-SNAPSHOT")
    
    assert result is None


def test_parse_snapshot_version_empty_snapshot_versions():
    """Test _parse_snapshot_version returns None when no snapshotVersions"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <metadata>
      <versioning>
        <snapshotVersions>
        </snapshotVersions>
      </versioning>
    </metadata>
    """
    
    dummy_registry = models.Registry(
        name="dummy",
        maven_config=models.MavenConfig(
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases",
            repository_domain_name="http://dummy.repo/"
        ),
        docker_config=models.DockerConfig()
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=dummy_registry,
        solution_descriptor=False,
    )
    
    result = _parse_snapshot_version(metadata_xml, app, 1, models.FileExtension.JSON, "1.0.0-SNAPSHOT")
    
    assert result is None


def test_parse_snapshot_version_old_style_metadata():
    """Test _parse_snapshot_version supports old-style <snapshot> metadata (Maven 2 format)"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <metadata modelVersion="1.1.0">
      <groupId>com.netcracker.cloud.code2prod.deployment-descriptor</groupId>
      <artifactId>c2p-test-sd-1</artifactId>
      <version>feature-sd_public_cloud_registry_testing-SNAPSHOT</version>
      <versioning>
        <snapshot>
          <timestamp>20260102.092159</timestamp>
          <buildNumber>1</buildNumber>
        </snapshot>
        <lastUpdated>20260102092159</lastUpdated>
      </versioning>
    </metadata>
    """
    
    dummy_registry = models.Registry(
        name="dummy",
        maven_config=models.MavenConfig(
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases",
            repository_domain_name="http://dummy.repo/"
        ),
        docker_config=models.DockerConfig()
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=dummy_registry,
        solution_descriptor=False,
    )
    
    result = _parse_snapshot_version(
        metadata_xml, app, 1, models.FileExtension.JSON, 
        "feature-sd_public_cloud_registry_testing-SNAPSHOT"
    )
    
    assert result == "feature-sd_public_cloud_registry_testing-20260102.092159-1"


def test_parse_snapshot_version_old_style_missing_timestamp():
    """Test _parse_snapshot_version returns None when <snapshot> has no timestamp"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <metadata modelVersion="1.1.0">
      <versioning>
        <snapshot>
          <buildNumber>1</buildNumber>
        </snapshot>
      </versioning>
    </metadata>
    """
    
    dummy_registry = models.Registry(
        name="dummy",
        maven_config=models.MavenConfig(
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases",
            repository_domain_name="http://dummy.repo/"
        ),
        docker_config=models.DockerConfig()
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=dummy_registry,
        solution_descriptor=False,
    )
    
    result = _parse_snapshot_version(metadata_xml, app, 1, models.FileExtension.JSON, "1.0.0-SNAPSHOT")
    
    assert result is None


def test_parse_snapshot_version_old_style_missing_buildnumber():
    """Test _parse_snapshot_version returns None when <snapshot> has no buildNumber"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <metadata modelVersion="1.1.0">
      <versioning>
        <snapshot>
          <timestamp>20260102.092159</timestamp>
        </snapshot>
      </versioning>
    </metadata>
    """
    
    dummy_registry = models.Registry(
        name="dummy",
        maven_config=models.MavenConfig(
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases",
            repository_domain_name="http://dummy.repo/"
        ),
        docker_config=models.DockerConfig()
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=dummy_registry,
        solution_descriptor=False,
    )
    
    result = _parse_snapshot_version(metadata_xml, app, 1, models.FileExtension.JSON, "1.0.0-SNAPSHOT")
    
    assert result is None


def test_parse_snapshot_version_prefers_new_style_over_old():
    """Test _parse_snapshot_version prefers new-style <snapshotVersions> when both are present"""
    metadata_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <metadata>
      <versioning>
        <snapshot>
          <timestamp>20240101.120000</timestamp>
          <buildNumber>99</buildNumber>
        </snapshot>
        <snapshotVersions>
          <snapshotVersion>
            <classifier></classifier>
            <extension>json</extension>
            <value>1.0.0-20240702.123456-1</value>
          </snapshotVersion>
        </snapshotVersions>
      </versioning>
    </metadata>
    """
    
    dummy_registry = models.Registry(
        name="dummy",
        maven_config=models.MavenConfig(
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases",
            repository_domain_name="http://dummy.repo/"
        ),
        docker_config=models.DockerConfig()
    )
    app = models.Application(
        name="test-app",
        artifact_id="test-artifact",
        group_id="com.test",
        registry=dummy_registry,
        solution_descriptor=False,
    )
    
    result = _parse_snapshot_version(metadata_xml, app, 1, models.FileExtension.JSON, "1.0.0-SNAPSHOT")
    
    # Should use new-style value, not old-style
    assert result == "1.0.0-20240702.123456-1"
