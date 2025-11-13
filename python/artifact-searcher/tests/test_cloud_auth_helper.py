"""
Tests for CloudAuthHelper
"""

import pytest
from artifact_searcher.cloud_auth_helper import CloudAuthHelper
from artifact_searcher.utils.models import Registry, AuthConfig, MavenConfig, DockerConfig


def test_resolve_auth_config_aws():
    """Test resolving AWS authConfig"""
    registry = Registry(
        name="test",
        version="2.0",
        auth_config={
            "aws-maven": AuthConfig(
                credentials_id="aws-keys",
                provider="aws",
                auth_method="secret",
                aws_region="us-east-1",
                aws_domain="my-domain"
            )
        },
        maven_config=MavenConfig(
            repository_domain_name="https://test.com/maven/",
            auth_config="aws-maven",
            target_snapshot="snapshots",
            target_release="releases",
            target_staging="staging",
            snapshot_group="com.test",
            release_group="com.test"
        ),
        docker_config=DockerConfig()
    )
    
    auth_config = CloudAuthHelper.resolve_auth_config(registry, "maven")
    
    assert auth_config is not None
    assert auth_config.provider == "aws"
    assert auth_config.aws_region == "us-east-1"
    assert auth_config.aws_domain == "my-domain"


def test_resolve_auth_config_missing_reference():
    """Test resolving authConfig with missing reference"""
    registry = Registry(
        name="test",
        version="2.0",
        auth_config={
            "aws-maven": AuthConfig(
                credentials_id="aws-keys",
                provider="aws"
            )
        },
        maven_config=MavenConfig(
            repository_domain_name="https://test.com/",
            auth_config="missing-ref",  # This reference doesn't exist!
            target_snapshot="snapshots",
            target_release="releases",
            target_staging="staging",
            snapshot_group="com.test",
            release_group="com.test"
        ),
        docker_config=DockerConfig()
    )
    
    auth_config = CloudAuthHelper.resolve_auth_config(registry, "maven")
    
    # Should return None when reference is missing
    assert auth_config is None


def test_resolve_credentials_success():
    """Test credential resolution"""
    auth_config = AuthConfig(
        credentials_id="aws-keys",
        provider="aws",
        auth_method="secret"
    )
    
    env_creds = {
        "aws-keys": {
            "username": "AKIAIOSFODNN7EXAMPLE",
            "password": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        }
    }
    
    creds = CloudAuthHelper.resolve_credentials(auth_config, env_creds)
    
    assert creds["username"] == "AKIAIOSFODNN7EXAMPLE"
    assert "password" in creds


def test_resolve_credentials_missing():
    """Test credential resolution with missing cred"""
    auth_config = AuthConfig(
        credentials_id="missing-key",
        provider="aws"
    )
    
    env_creds = {"other-key": {"username": "test"}}
    
    with pytest.raises(KeyError, match="missing-key"):
        CloudAuthHelper.resolve_credentials(auth_config, env_creds)


def test_extract_repository_name_aws():
    """Test extracting repository name from AWS CodeArtifact URL"""
    url = "https://my-domain-123456789012.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo/"
    
    repo_name = CloudAuthHelper._extract_repository_name(url)
    
    assert repo_name == "my-repo"


def test_extract_repository_name_gcp():
    """Test extracting repository name from GCP Artifact Registry URL"""
    url = "https://us-central1-maven.pkg.dev/my-project-123456/my-repo/"
    
    repo_name = CloudAuthHelper._extract_repository_name(url)
    
    assert repo_name == "my-repo"


def test_extract_repository_name_generic():
    """Test extracting repository name from generic URL (fallback)"""
    url = "https://artifactory.company.com/repository/maven-releases/"
    
    repo_name = CloudAuthHelper._extract_repository_name(url)
    
    assert repo_name == "maven-releases"


def test_extract_region_aws_from_url():
    """Test extracting AWS region from URL"""
    url = "https://domain-123.d.codeartifact.us-west-2.amazonaws.com/maven/repo/"
    auth_config = AuthConfig(credentials_id="test", provider="aws")
    
    region = CloudAuthHelper._extract_region(url, auth_config)
    
    assert region == "us-west-2"


def test_extract_region_from_auth_config():
    """Test preferring explicit region from authConfig"""
    url = "https://domain-123.d.codeartifact.us-west-2.amazonaws.com/maven/repo/"
    auth_config = AuthConfig(
        credentials_id="test",
        provider="aws",
        aws_region="eu-west-1"  # Explicit region should take precedence
    )
    
    region = CloudAuthHelper._extract_region(url, auth_config)
    
    assert region == "eu-west-1"  # Should use authConfig region


def test_extract_region_gcp():
    """Test extracting GCP region from URL"""
    url = "https://europe-west1-maven.pkg.dev/project/repo/"
    auth_config = AuthConfig(credentials_id="test", provider="gcp")
    
    region = CloudAuthHelper._extract_region(url, auth_config)
    
    assert region == "europe-west1"


def test_extract_region_fallback():
    """Test region extraction fallback to default"""
    url = "https://unknown-format.com/repo/"
    auth_config = AuthConfig(credentials_id="test")
    
    region = CloudAuthHelper._extract_region(url, auth_config)
    
    assert region == "us-east-1"  # Default fallback
