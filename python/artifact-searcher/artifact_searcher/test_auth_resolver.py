import base64
import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from artifact_searcher.auth_resolver import resolve_v2_auth_headers
from artifact_searcher.utils.models import AuthConfig, Provider, RegistryV2, MavenConfigV2


@pytest.fixture
def env_creds():
    return {
        "aws-cred": {
            "data": {
                "username": "AKIA_ACCESS_KEY",
                "password": "secret_key_value"
            }
        },
        "gcp-cred": {
            "data": {
                "secret": '{"type": "service_account", "project_id": "my-project"}'
            }
        },
        "nexus-cred": {
            "data": {
                "username": "nexus_user",
                "password": "nexus_pass"
            }
        },
        "artifactory-cred": {
            "data": {
                "username": "artifactory_user",
                "password": "artifactory_pass"
            }
        },
        "anonymous-cred": {
            "data": {}
        }
    }


@pytest.fixture
def base_registry_v2():
    return RegistryV2(
        version="2.0",
        name="test-registry",
        auth_config={},
        maven_config=MavenConfigV2(
            auth_config="test-auth",
            repository_domain_name="https://registry.example.com"
        )
    )


class TestAnonymousAccess:
    def test_nexus_anonymous_auth(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "test-auth": AuthConfig(provider=Provider.NEXUS, auth_method="anonymous")
        }
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        assert result is None

    def test_artifactory_anonymous_auth(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "test-auth": AuthConfig(provider=Provider.ARTIFACTORY, auth_method="anonymous")
        }
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        assert result is None

    def test_missing_authconfig_reference(self, base_registry_v2, env_creds):
        base_registry_v2.maven_config.auth_config = "nonexistent"
        base_registry_v2.auth_config = {}
        
        with pytest.raises(ValueError, match="AuthConfig 'nonexistent' not found"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)


class TestAWSAuthentication:
    def test_aws_secret_success(self, base_registry_v2, env_creds, monkeypatch):
        # Mock v1 library module for AWSCodeArtifactHelper
        fake_utils_aws = MagicMock()
        
        monkeypatch.setitem(sys.modules, 'qubership_pipelines_common_library.v1.utils.utils_aws', fake_utils_aws)
        
        # Mock AWSCodeArtifactHelper.get_authorization_token static method
        mock_helper_class = MagicMock()
        mock_helper_class.get_authorization_token.return_value = "aws_token_123"
        
        fake_utils_aws.AWSCodeArtifactHelper = mock_helper_class
        
        base_registry_v2.auth_config = {
            "aws-auth": AuthConfig(
                credentials_id="aws-cred",
                provider=Provider.AWS,
                auth_method="secret",
                aws_region="us-east-1",
                aws_domain="my-domain"
            )
        }
        base_registry_v2.maven_config.auth_config = "aws-auth"
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        assert result == {"Authorization": "Bearer aws_token_123"}
        mock_helper_class.get_authorization_token.assert_called_once_with(
            access_key="AKIA_ACCESS_KEY",
            secret_key="secret_key_value",
            domain="my-domain",
            region_name="us-east-1"
        )

    def test_aws_invalid_auth_method(self, base_registry_v2, env_creds):
        # JSON schema validation should catch invalid authMethod enum value
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'invalid_method' is not one of"):
            AuthConfig(
                credentials_id="aws-cred",
                provider=Provider.AWS,
                auth_method="invalid_method",
                aws_region="us-east-1"
            )

    def test_aws_missing_region(self, base_registry_v2, env_creds):
        # JSON schema validation should catch missing awsRegion for AWS secret auth
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'awsRegion' is a required property"):
            AuthConfig(
                credentials_id="aws-cred",
                provider=Provider.AWS,
                auth_method="secret",
                aws_domain="my-domain"
            )

    def test_aws_missing_credentials(self, base_registry_v2, env_creds):
        env_creds["aws-cred"]["data"] = {"username": "access_key"}
        
        base_registry_v2.auth_config = {
            "aws-auth": AuthConfig(
                credentials_id="aws-cred",
                provider=Provider.AWS,
                auth_method="secret",
                aws_region="us-east-1",
                aws_domain="my-domain"
            )
        }
        base_registry_v2.maven_config.auth_config = "aws-auth"
        
        with pytest.raises(ValueError, match="AWS secret auth requires both username and password in credentials"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)


class TestGCPAuthentication:
    def test_gcp_service_account_success(self, base_registry_v2, env_creds, monkeypatch):
        # Create fake module
        fake_gcp_creds = MagicMock()
        monkeypatch.setitem(sys.modules, 'qubership_pipelines_common_library.v2.artifacts_finder.auth.gcp_credentials', fake_gcp_creds)
        
        # Setup mock
        mock_gcp_provider = MagicMock()
        fake_gcp_creds.GcpCredentialsProvider = mock_gcp_provider
        
        mock_creds = MagicMock()
        mock_creds.gcp_authorization_token = "gcp_token_123"
        mock_gcp_provider.return_value.with_service_account_key.return_value.get_credentials.return_value = mock_creds
        
        base_registry_v2.auth_config = {
            "gcp-auth": AuthConfig(
                credentials_id="gcp-cred",
                provider=Provider.GCP,
                auth_method="service_account",
                gcp_reg_project="my-project"
            )
        }
        base_registry_v2.maven_config.auth_config = "gcp-auth"
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        assert result == {"Authorization": "Bearer gcp_token_123"}
        mock_gcp_provider.return_value.with_service_account_key.assert_called_once_with(
            service_account_key_content='{"type": "service_account", "project_id": "my-project"}'
        )

    def test_gcp_invalid_auth_method(self, base_registry_v2, env_creds):
        # JSON schema validation should catch invalid authMethod enum value
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'invalid' is not one of"):
            base_registry_v2.auth_config = {
                "gcp-auth": AuthConfig(
                    credentials_id="gcp-cred",
                    provider=Provider.GCP,
                    auth_method="invalid"
                )
            }

    def test_gcp_missing_secret(self, base_registry_v2, env_creds):
        env_creds["gcp-cred"]["data"] = {}
        
        base_registry_v2.auth_config = {
            "gcp-auth": AuthConfig(
                credentials_id="gcp-cred",
                provider=Provider.GCP,
                auth_method="service_account"
            )
        }
        base_registry_v2.maven_config.auth_config = "gcp-auth"
        
        # Empty cred_data should raise error about missing secret
        with pytest.raises(ValueError, match="GCP service_account requires credential with 'secret' field"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)

    def test_gcp_invalid_json(self, base_registry_v2, env_creds):
        env_creds["gcp-cred"]["data"]["secret"] = "not valid json"
        
        base_registry_v2.auth_config = {
            "gcp-auth": AuthConfig(
                credentials_id="gcp-cred",
                provider=Provider.GCP,
                auth_method="service_account"
            )
        }
        base_registry_v2.maven_config.auth_config = "gcp-auth"
        
        with pytest.raises(ValueError, match="GCP service account key must be valid JSON"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)


class TestNexusArtifactoryAuthentication:
    @pytest.mark.parametrize("provider,cred_id,username,password", [
        (Provider.NEXUS, "nexus-cred", "nexus_user", "nexus_pass"),
        (Provider.ARTIFACTORY, "artifactory-cred", "artifactory_user", "artifactory_pass"),
    ])
    def test_basic_auth_success(self, provider, cred_id, username, password, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "basic-auth": AuthConfig(
                credentials_id=cred_id,
                provider=provider,
                auth_method="user_pass"
            )
        }
        base_registry_v2.maven_config.auth_config = "basic-auth"
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        expected_token = base64.b64encode(f"{username}:{password}".encode()).decode()
        assert result == {"Authorization": f"Basic {expected_token}"}

    def test_basic_auth_no_provider_with_user_pass(self, base_registry_v2, env_creds):
        # JSON schema validation should catch missing provider (required field)
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'provider' is a required property"):
            base_registry_v2.auth_config = {
                "basic-auth": AuthConfig(
                    credentials_id="nexus-cred",
                    auth_method="user_pass"
                )
            }

    def test_basic_auth_no_provider_no_method(self, base_registry_v2, env_creds):
        # JSON schema validation should catch missing provider and authMethod (both required)
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'provider' is a required property"):
            base_registry_v2.auth_config = {
                "basic-auth": AuthConfig(
                    credentials_id="nexus-cred"
                )
            }

    def test_basic_auth_missing_password(self, base_registry_v2, env_creds):
        env_creds["nexus-cred"]["data"] = {"username": "user"}
        
        # JSON schema validation should catch missing authMethod (required field)
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'authMethod' is a required property"):
            base_registry_v2.auth_config = {
                "basic-auth": AuthConfig(
                    credentials_id="nexus-cred",
                    provider=Provider.NEXUS
                )
            }


class TestCredentialHandling:
    def test_missing_provider_field(self, base_registry_v2, env_creds):
        # JSON schema validation should catch missing provider (required field)
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'provider' is a required property"):
            AuthConfig(
                credentials_id="test-cred",
                auth_method="user_pass"
            )

    def test_missing_auth_method_field(self, base_registry_v2, env_creds):
        # JSON schema validation should catch missing authMethod (required field)
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'authMethod' is a required property"):
            AuthConfig(
                credentials_id="test-cred",
                provider=Provider.NEXUS
            )

    def test_credentials_id_required_for_non_anonymous(self, base_registry_v2, env_creds):
        # JSON schema validation should catch missing credentialsId for non-anonymous auth
        with pytest.raises(ValueError, match="AuthConfig validation failed.*'credentialsId' is a required property"):
            AuthConfig(
                provider=Provider.NEXUS,
                auth_method="user_pass"
            )
