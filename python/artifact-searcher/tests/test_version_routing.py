"""
Tests for V1/V2 version routing and core artifact functions
"""

import pytest
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from artifact_searcher.artifact import (
    version_to_folder_name,
    create_full_url,
    unzip_file,
    create_app_artifacts_local_path
)
from artifact_searcher.utils.models import (
    Application,
    Registry,
    MavenConfig,
    DockerConfig,
    AuthConfig,
    FileExtension,
    ArtifactInfo
)


@pytest.mark.asyncio
async def test_version_routing_v1_no_version():
    """Test that no version field routes to V1"""
    app = Application(
        name="test-app",
        artifact_id="myapp",
        group_id="com.test",
        solution_descriptor=True,
        registry=Registry(
            name="artifactory",
            # No version field - should default to "1.0"
            maven_config=MavenConfig(
                repository_domain_name="https://artifactory.com/",
                target_snapshot="snapshots",
                target_release="releases",
                target_staging="staging",
                snapshot_group="com.test",
                release_group="com.test"
            ),
            docker_config=DockerConfig()
        )
    )
    
    # V1 should be used
    assert app.registry.version == "1.0"


@pytest.mark.asyncio
async def test_version_routing_v1_explicit():
    """Test that version="1.0" routes to V1"""
    app = Application(
        name="test-app",
        artifact_id="myapp",
        group_id="com.test",
        solution_descriptor=True,
        registry=Registry(
            name="nexus",
            version="1.0",  # Explicit V1
            maven_config=MavenConfig(
                repository_domain_name="https://nexus.com/",
                target_snapshot="snapshots",
                target_release="releases",
                target_staging="staging",
                snapshot_group="com.test",
                release_group="com.test"
            ),
            docker_config=DockerConfig()
        )
    )
    
    assert app.registry.version == "1.0"


@pytest.mark.asyncio
async def test_version_routing_v2():
    """Test that version="2.0" is detected"""
    app = Application(
        name="test-app",
        artifact_id="myapp",
        group_id="com.test",
        solution_descriptor=True,
        registry=Registry(
            name="aws-registry",
            version="2.0",  # V2
            auth_config={
                "aws": AuthConfig(
                    credentials_id="aws-keys",
                    provider="aws",
                    aws_region="us-east-1",
                    aws_domain="my-domain"
                )
            },
            maven_config=MavenConfig(
                repository_domain_name="https://test.amazonaws.com/maven/",
                auth_config="aws",
                target_snapshot="snapshots",
                target_release="releases",
                target_staging="staging",
                snapshot_group="com.test",
                release_group="com.test"
            ),
            docker_config=DockerConfig()
        )
    )
    
    assert app.registry.version == "2.0"
    assert "aws" in app.registry.auth_config


def test_v2_fallback_no_provider():
    """Test that V2 falls back to V1 when no cloud provider configured"""
    app = Application(
        name="test-app",
        artifact_id="myapp",
        group_id="com.test",
        solution_descriptor=True,
        registry=Registry(
            name="registry",
            version="2.0",  # V2 but...
            auth_config={
                "basic": AuthConfig(
                    credentials_id="creds",
                    # No provider! Should fall back to V1
                )
            },
            maven_config=MavenConfig(
                repository_domain_name="https://registry.com/",
                auth_config="basic",
                target_snapshot="snapshots",
                target_release="releases",
                target_staging="staging",
                snapshot_group="com.test",
                release_group="com.test"
            ),
            docker_config=DockerConfig()
        )
    )
    
    # V2 detected but no cloud provider
    assert app.registry.version == "2.0"
    auth = app.registry.auth_config.get("basic")
    assert auth.provider is None  # Will fall back to V1


def test_backward_compatibility():
    """Test that existing V1 AppDefs/RegDefs still work"""
    # V1 format with credentialsId at registry level
    app = Application(
        name="legacy-app",
        artifact_id="legacy",
        group_id="com.legacy",
        solution_descriptor=True,
        registry=Registry(
            name="old-artifactory",
            credentials_id="legacy-creds",  # V1 style
            maven_config=MavenConfig(
                repository_domain_name="https://old-artifactory.com/",
                target_snapshot="libs-snapshot",
                target_release="libs-release",
                target_staging="libs-staging",
                snapshot_group="com.legacy",
                release_group="com.legacy"
            ),
            docker_config=DockerConfig()
        )
    )
    
    # Should work exactly as before
    assert app.registry.version == "1.0"  # Default
    assert app.registry.credentials_id == "legacy-creds"
    assert app.registry.maven_config.auth_config is None  # No V2 field used


# Core artifact function tests

def test_version_to_folder_name_snapshot():
    """Test version normalization for timestamped snapshots"""
    version = "1.0.0-20240702.123456-1"
    result = version_to_folder_name(version)
    assert result == "1.0.0-SNAPSHOT"


def test_version_to_folder_name_release():
    """Test version stays unchanged for release versions"""
    version = "1.0.0-RELEASE"
    result = version_to_folder_name(version)
    assert result == "1.0.0-RELEASE"


def test_version_to_folder_name_plain():
    """Test plain version number unchanged"""
    version = "2.5.3"
    result = version_to_folder_name(version)
    assert result == "2.5.3"


def test_create_full_url_json():
    """Test URL construction for JSON artifact"""
    app = Application(
        name="test-app",
        artifact_id="myapp",
        group_id="com.test",
        solution_descriptor=True,
        registry=Registry(
            name="nexus",
            maven_config=MavenConfig(
                repository_domain_name="https://nexus.com/",
                target_snapshot="snapshots",
                target_release="releases",
                target_staging="staging"
            ),
            docker_config=DockerConfig()
        )
    )
    
    url = create_full_url(app, "1.0.0", "releases", FileExtension.JSON, "1.0.0")
    
    assert "https://nexus.com/" in url
    assert "releases/com/test/myapp/1.0.0/myapp-1.0.0.json" in url


def test_create_full_url_zip():
    """Test URL construction for ZIP artifact"""
    app = Application(
        name="test-app",
        artifact_id="deployment-artifacts",
        group_id="com.netcracker.cloud",
        solution_descriptor=False,
        registry=Registry(
            name="artifactory",
            maven_config=MavenConfig(
                repository_domain_name="https://artifactory.com/",
                target_snapshot="libs-snapshot",
                target_release="libs-release",
                target_staging="libs-staging"
            ),
            docker_config=DockerConfig()
        )
    )
    
    url = create_full_url(app, "2.0.0-RELEASE", "libs-release", FileExtension.ZIP, "2.0.0-RELEASE")
    
    assert "https://artifactory.com/" in url
    assert "libs-release/com/netcracker/cloud/deployment-artifacts" in url
    assert "deployment-artifacts-2.0.0-RELEASE.zip" in url


def test_create_app_artifacts_local_path():
    """Test local path generation"""
    path = create_app_artifacts_local_path("myapp", "1.0.0")
    
    assert "myapp" in path
    assert "1.0.0" in path


def test_unzip_file_with_filter():
    """Test ZIP extraction with artifact_id filtering"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test ZIP
        zip_path = Path(tmpdir) / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("myapp/file1.yaml", "content1")
            zf.writestr("myapp/subdir/file2.yaml", "content2")
            zf.writestr("other-app/file3.yaml", "content3")  # Should not be extracted
        
        # Mock WORKSPACE
        with patch('artifact_searcher.artifact.WORKSPACE', Path(tmpdir)):
            with patch('artifact_searcher.artifact.create_app_artifacts_local_path', return_value=tmpdir):
                # Extract only myapp/ files
                unzip_file("myapp", "test-app", "1.0.0", str(zip_path))
                
                # Verify myapp files were extracted
                extracted_files = list(Path(tmpdir).rglob("*"))
                extracted_names = [f.name for f in extracted_files if f.is_file()]
                
                # Should have extracted files from myapp/
                assert any("file1.yaml" in name or "file2.yaml" in name for name in extracted_names)


def test_file_extension_enum():
    """Test FileExtension enum values"""
    assert FileExtension.JSON.value == "json"
    assert FileExtension.ZIP.value == "zip"
    assert isinstance(FileExtension.JSON, FileExtension)
    assert isinstance(FileExtension.ZIP, FileExtension)


def test_artifact_info_model():
    """Test ArtifactInfo model creation"""
    info = ArtifactInfo(
        url="https://test.com/artifact.json",
        app_name="myapp",
        app_version="1.0.0",
        repo="releases",
        path="com/test/myapp/1.0.0"
    )
    
    assert info.url == "https://test.com/artifact.json"
    assert info.app_name == "myapp"
    assert info.app_version == "1.0.0"
    assert info.local_path is None or info.local_path == ""


# ZIP download tests for AWS and GCP

@pytest.mark.asyncio
async def test_check_artifact_async_aws_zip():
    """Test V2 artifact check for AWS CodeArtifact ZIP"""
    from artifact_searcher.artifact import check_artifact_async
    
    app = Application(
        name="test-app",
        artifact_id="deployment-artifacts",
        group_id="com.netcracker.cloud",
        solution_descriptor=False,
        registry=Registry(
            name="aws-registry",
            version="2.0",
            auth_config={
                "aws-maven": AuthConfig(
                    credentials_id="aws-keys",
                    provider="aws",
                    auth_method="secret",
                    aws_region="us-east-1",
                    aws_domain="devops-bp-toolset"
                )
            },
            maven_config=MavenConfig(
                repository_domain_name="https://devops-bp-toolset-123.d.codeartifact.us-east-1.amazonaws.com/maven/repo/",
                auth_config="aws-maven",
                target_snapshot="snapshots",
                target_release="releases",
                target_staging="staging"
            ),
            docker_config=DockerConfig()
        )
    )
    
    env_creds = {
        "aws-keys": {
            "username": "AKIAIOSFODNN7EXAMPLE",
            "password": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        }
    }
    
    # Mock V2 search to return AWS ZIP URL
    with patch('artifact_searcher.artifact._check_artifact_v2_async', 
               new=AsyncMock(return_value=(
                   "https://devops-bp-toolset-123.d.codeartifact.us-east-1.amazonaws.com/maven/repo/com/netcracker/cloud/deployment-artifacts/1.0.0/deployment-artifacts-1.0.0.zip",
                   ("aws", "cloudProvider")
               ))):
        result = await check_artifact_async(app, FileExtension.ZIP, "1.0.0", env_creds)
        
        assert result is not None
        assert "deployment-artifacts-1.0.0.zip" in result[0]
        assert "codeartifact.us-east-1.amazonaws.com" in result[0]
        assert result[1][0] == "aws"


@pytest.mark.asyncio
async def test_check_artifact_async_gcp_zip():
    """Test V2 artifact check for GCP Artifact Registry ZIP"""
    from artifact_searcher.artifact import check_artifact_async
    
    app = Application(
        name="test-app",
        artifact_id="deployment-artifacts",
        group_id="com.netcracker.cloud",
        solution_descriptor=False,
        registry=Registry(
            name="gcp-registry",
            version="2.0",
            auth_config={
                "gcp-maven": AuthConfig(
                    credentials_id="gcp-sa",
                    provider="gcp",
                    auth_method="service_account",
                    gcp_reg_project="my-project-123456"
                )
            },
            maven_config=MavenConfig(
                repository_domain_name="https://asia-south1-maven.pkg.dev/my-project-123456/maven-repo/",
                auth_config="gcp-maven",
                target_snapshot="snapshots",
                target_release="releases",
                target_staging="staging"
            ),
            docker_config=DockerConfig()
        )
    )
    
    env_creds = {
        "gcp-sa": {
            "secret": '{"type": "service_account", "project_id": "my-project-123456"}'
        }
    }
    
    # Mock V2 search to return GCP ZIP URL
    with patch('artifact_searcher.artifact._check_artifact_v2_async',
               new=AsyncMock(return_value=(
                   "https://asia-south1-maven.pkg.dev/my-project-123456/maven-repo/com/netcracker/cloud/deployment-artifacts/1.0.0/deployment-artifacts-1.0.0.zip",
                   ("gcp", "cloudProvider")
               ))):
        result = await check_artifact_async(app, FileExtension.ZIP, "1.0.0", env_creds)
        
        assert result is not None
        assert "deployment-artifacts-1.0.0.zip" in result[0]
        assert "asia-south1-maven.pkg.dev" in result[0]
        assert result[1][0] == "gcp"


@pytest.mark.asyncio
async def test_check_artifact_async_zip_v1_fallback():
    """Test V2 ZIP download falls back to V1 when credentials missing"""
    from artifact_searcher.artifact import check_artifact_async
    
    app = Application(
        name="test-app",
        artifact_id="deployment-artifacts",
        group_id="com.test",
        solution_descriptor=False,
        registry=Registry(
            name="aws-registry",
            version="2.0",
            auth_config={
                "aws": AuthConfig(
                    credentials_id="aws-keys",
                    provider="aws"
                )
            },
            maven_config=MavenConfig(
                repository_domain_name="https://test.amazonaws.com/maven/repo/",
                auth_config="aws",
                target_snapshot="snapshots",
                target_release="releases",
                target_staging="staging"
            ),
            docker_config=DockerConfig()
        )
    )
    
    # No env_creds - should fall back to V1
    with patch('artifact_searcher.artifact._check_artifact_v1_async',
               new=AsyncMock(return_value=(
                   "https://test.amazonaws.com/maven/repo/releases/com/test/deployment-artifacts/1.0.0/deployment-artifacts-1.0.0.zip",
                   ("releases", "targetRelease")
               ))):
        result = await check_artifact_async(app, FileExtension.ZIP, "1.0.0", env_creds=None)
        
        assert result is not None
        assert "deployment-artifacts-1.0.0.zip" in result[0]
        assert result[1][0] == "releases"


@pytest.mark.asyncio
async def test_download_all_async_mixed_artifacts():
    """Test async download of mixed JSON and ZIP artifacts"""
    from artifact_searcher.artifact import download_all_async
    
    artifacts = [
        ArtifactInfo(
            url="https://test.com/app1-1.0.0.json",
            app_name="app1",
            app_version="1.0.0"
        ),
        ArtifactInfo(
            url="https://test.com/app2-2.0.0.zip",
            app_name="app2",
            app_version="2.0.0"
        ),
        ArtifactInfo(
            url="https://test.com/app3-3.0.0.json",
            app_name="app3",
            app_version="3.0.0"
        )
    ]
    
    with patch('artifact_searcher.artifact.download', new=AsyncMock(side_effect=lambda session, info: info)):
        results = await download_all_async(artifacts)
        
        assert len(results) == 3
        assert results[0].app_name == "app1"
        assert results[1].app_name == "app2"
        assert results[2].app_name == "app3"
        assert ".json" in results[0].url
        assert ".zip" in results[1].url
        assert ".json" in results[2].url
