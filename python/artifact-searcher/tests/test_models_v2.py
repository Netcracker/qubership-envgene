"""
Tests for RegDef V2 model extensions
"""

import pytest
from artifact_searcher.utils.models import (
    AuthConfig,
    MavenConfig,
    DockerConfig,
    Registry,
    Application
)


def test_authconfig_aws():
    """Test AWS AuthConfig parsing"""
    auth_data = {
        "credentialsId": "aws-keys",
        "authType": "longLived",
        "provider": "aws",
        "authMethod": "secret",
        "awsRegion": "us-east-1",
        "awsDomain": "my-domain"
    }
    auth = AuthConfig(**auth_data)
    
    assert auth.credentials_id == "aws-keys"
    assert auth.provider == "aws"
    assert auth.auth_method == "secret"
    assert auth.aws_region == "us-east-1"
    assert auth.aws_domain == "my-domain"


def test_authconfig_gcp():
    """Test GCP AuthConfig parsing"""
    auth_data = {
        "credentialsId": "gcp-sa",
        "authType": "shortLived",
        "provider": "gcp",
        "authMethod": "service_account",
        "gcpRegProject": "my-project-123456"
    }
    auth = AuthConfig(**auth_data)
    
    assert auth.credentials_id == "gcp-sa"
    assert auth.provider == "gcp"
    assert auth.auth_method == "service_account"
    assert auth.gcp_reg_project == "my-project-123456"


def test_maven_config_with_auth_config():
    """Test MavenConfig with authConfig reference"""
    maven_data = {
        "targetSnapshot": "snapshots",
        "targetStaging": "staging",
        "targetRelease": "releases",
        "repositoryDomainName": "https://test.com/maven/",
        "snapshotGroup": "com.test",
        "releaseGroup": "com.test",
        "authConfig": "aws-maven"  # V2 field
    }
    maven_config = MavenConfig(**maven_data)
    
    assert maven_config.auth_config == "aws-maven"
    assert maven_config.repository_domain_name == "https://test.com/maven/"


def test_registry_v2_parsing():
    """Test V2 Registry with authConfig"""
    reg_data = {
        "name": "aws-registry",
        "version": "2.0",
        "authConfig": {
            "aws-maven": AuthConfig(
                credentials_id="aws-keys",
                provider="aws",
                auth_method="secret",
                aws_region="us-east-1",
                aws_domain="my-domain"
            )
        },
        "mavenConfig": {
            "repositoryDomainName": "https://test.com/maven/",
            "authConfig": "aws-maven",
            "targetSnapshot": "snapshots",
            "targetRelease": "releases",
            "targetStaging": "staging",
            "snapshotGroup": "com.test",
            "releaseGroup": "com.test"
        },
        "dockerConfig": {}
    }
    
    registry = Registry(**reg_data)
    
    assert registry.version == "2.0"
    assert "aws-maven" in registry.auth_config
    assert registry.maven_config.auth_config == "aws-maven"
    assert registry.auth_config["aws-maven"].provider == "aws"


def test_registry_v1_backward_compat():
    """Test V1 Registry still works (no version field)"""
    reg_data = {
        "name": "artifactory",
        "credentialsId": "art-creds",
        "mavenConfig": {
            "repositoryDomainName": "https://artifactory.com/",
            "targetSnapshot": "libs-snapshot",
            "targetRelease": "libs-release",
            "targetStaging": "libs-staging",
            "snapshotGroup": "com.company",
            "releaseGroup": "com.company"
        },
        "dockerConfig": {}
    }
    
    registry = Registry(**reg_data)
    
    # Should default to V1
    assert registry.version == "1.0"
    assert registry.credentials_id == "art-creds"
    assert registry.auth_config is None or registry.auth_config == {}


def test_registry_v1_explicit_version():
    """Test V1 Registry with explicit version="1.0"""
    reg_data = {
        "name": "nexus",
        "version": "1.0",
        "credentialsId": "nexus-creds",
        "mavenConfig": {
            "repositoryDomainName": "https://nexus.com/",
            "targetSnapshot": "snapshots",
            "targetRelease": "releases",
            "targetStaging": "staging",
            "snapshotGroup": "com.test",
            "releaseGroup": "com.test"
        },
        "dockerConfig": {}
    }
    
    registry = Registry(**reg_data)
    
    assert registry.version == "1.0"
    assert registry.credentials_id == "nexus-creds"


def test_application_with_v2_registry():
    """Test Application with V2 Registry"""
    app_data = {
        "name": "test-app",
        "artifactId": "myapp",
        "groupId": "com.test",
        "solutionDescriptor": True,
        "registry": {
            "name": "aws-reg",
            "version": "2.0",
            "authConfig": {
                "aws": AuthConfig(
                    credentials_id="aws-keys",
                    provider="aws",
                    aws_region="us-east-1",
                    aws_domain="test-domain"
                )
            },
            "mavenConfig": {
                "repositoryDomainName": "https://test.amazonaws.com/maven/repo/",
                "authConfig": "aws",
                "targetSnapshot": "snapshots",
                "targetRelease": "releases",
                "targetStaging": "staging",
                "snapshotGroup": "com.test",
                "releaseGroup": "com.test"
            },
            "dockerConfig": {}
        }
    }
    
    app = Application(**app_data)
    
    assert app.name == "test-app"
    assert app.registry.version == "2.0"
    assert app.registry.maven_config.auth_config == "aws"
    assert "aws" in app.registry.auth_config
