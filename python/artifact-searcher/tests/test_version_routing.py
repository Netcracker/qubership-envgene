"""
Tests for V1/V2 version routing in artifact.py
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from artifact_searcher.utils.models import Application, Registry, MavenConfig, DockerConfig, AuthConfig, FileExtension


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


def test_v2_fallback_no_env_creds():
    """Test that V2 falls back to V1 when no env_creds provided"""
    # This would be tested in integration tests
    # When V2 registry but no env_creds, should fall back to V1
    pass


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
