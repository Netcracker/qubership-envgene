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
            repository_domain_name="https://registry.example.com",
            target_snapshot="snapshots",
            target_staging="staging",
            target_release="releases"
        )
    )


class TestAnonymousAccess:
    def test_no_auth_config_reference(self, base_registry_v2, env_creds):
        base_registry_v2.maven_config.auth_config = None
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        assert result is None

    def test_empty_credentials(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "anonymous": AuthConfig(credentials_id="anonymous-cred")
        }
        base_registry_v2.maven_config.auth_config = "anonymous"
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        assert result is None

    def test_missing_authconfig_reference(self, base_registry_v2, env_creds):
        base_registry_v2.maven_config.auth_config = "nonexistent"
        
        with pytest.raises(ValueError, match="AuthConfig 'nonexistent' not found"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)


class TestAWSAuthentication:
    def test_aws_secret_success(self, base_registry_v2, env_creds, monkeypatch):
        # Create fake modules
        fake_aws_creds = MagicMock()
        fake_boto3 = MagicMock()
        fake_botocore_config = MagicMock()
        
        monkeypatch.setitem(sys.modules, 'qubership_pipelines_common_library.v2.artifacts_finder.auth.aws_credentials', fake_aws_creds)
        monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)
        monkeypatch.setitem(sys.modules, 'botocore.config', fake_botocore_config)
        
        # Setup mocks
        mock_aws_provider = MagicMock()
        fake_aws_creds.AwsCredentialsProvider = mock_aws_provider
        mock_creds = MagicMock()
        mock_creds.access_key = "access"
        mock_creds.secret_key = "secret"
        mock_creds.session_token = "token"
        mock_aws_provider.return_value.with_direct_credentials.return_value.get_credentials.return_value = mock_creds
        
        # Mock boto3 client to return token in correct format
        mock_client = MagicMock()
        mock_client.get_authorization_token.return_value = {"authorizationToken": "aws_token_123"}
        fake_boto3.client.return_value = mock_client
        fake_botocore_config.Config = MagicMock()
        
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
        mock_aws_provider.return_value.with_direct_credentials.assert_called_once_with(
            access_key="AKIA_ACCESS_KEY",
            secret_key="secret_key_value",
            region_name="us-east-1"
        )
        fake_boto3.client.assert_called_once()

    def test_aws_invalid_auth_method(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "aws-auth": AuthConfig(
                credentials_id="aws-cred",
                provider=Provider.AWS,
                auth_method="invalid_method",
                aws_region="us-east-1",
                aws_domain="my-domain"
            )
        }
        base_registry_v2.maven_config.auth_config = "aws-auth"
        
        with pytest.raises(ValueError, match="AWS provider requires authMethod='secret' or 'assume_role'"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)

    def test_aws_missing_region(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "aws-auth": AuthConfig(
                credentials_id="aws-cred",
                provider=Provider.AWS,
                auth_method="secret",
                aws_domain="my-domain"
            )
        }
        base_registry_v2.maven_config.auth_config = "aws-auth"
        
        with pytest.raises(ValueError, match="AWS authConfig must specify 'awsRegion'"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)

    def test_aws_missing_domain(self, base_registry_v2, env_creds, monkeypatch):
        # Mock modules to prevent ImportError
        fake_aws_creds = MagicMock()
        fake_boto3 = MagicMock()
        fake_botocore_config = MagicMock()
        
        monkeypatch.setitem(sys.modules, 'qubership_pipelines_common_library.v2.artifacts_finder.auth.aws_credentials', fake_aws_creds)
        monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)
        monkeypatch.setitem(sys.modules, 'botocore.config', fake_botocore_config)
        
        base_registry_v2.auth_config = {
            "aws-auth": AuthConfig(
                credentials_id="aws-cred",
                provider=Provider.AWS,
                auth_method="secret",
                aws_region="us-east-1"
            )
        }
        base_registry_v2.maven_config.auth_config = "aws-auth"
        
        with pytest.raises(ValueError, match="AWS authConfig must specify 'awsDomain'"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)

    def test_aws_missing_credentials(self, base_registry_v2, env_creds, monkeypatch):
        # Mock modules to prevent ImportError
        fake_aws_creds = MagicMock()
        fake_boto3 = MagicMock()
        fake_botocore_config = MagicMock()
        
        monkeypatch.setitem(sys.modules, 'qubership_pipelines_common_library.v2.artifacts_finder.auth.aws_credentials', fake_aws_creds)
        monkeypatch.setitem(sys.modules, 'boto3', fake_boto3)
        monkeypatch.setitem(sys.modules, 'botocore.config', fake_botocore_config)
        
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
        
        with pytest.raises(ValueError, match="AWS .* auth requires both username .* and password"):
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

    def test_gcp_federation_not_implemented(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "gcp-auth": AuthConfig(
                credentials_id="gcp-cred",
                provider=Provider.GCP,
                auth_method="federation"
            )
        }
        base_registry_v2.maven_config.auth_config = "gcp-auth"
        
        with pytest.raises(NotImplementedError, match="GCP federation .* is not yet implemented"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)

    def test_gcp_invalid_auth_method(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "gcp-auth": AuthConfig(
                credentials_id="gcp-cred",
                provider=Provider.GCP,
                auth_method="invalid"
            )
        }
        base_registry_v2.maven_config.auth_config = "gcp-auth"
        
        with pytest.raises(ValueError, match="GCP provider requires authMethod='service_account' or 'federation'"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)

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
        
        # Empty cred_data triggers anonymous detection before reaching GCP validation
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        assert result is None

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
        base_registry_v2.auth_config = {
            "basic-auth": AuthConfig(
                credentials_id="nexus-cred",
                auth_method="user_pass"
            )
        }
        base_registry_v2.maven_config.auth_config = "basic-auth"
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        expected_token = base64.b64encode(b"nexus_user:nexus_pass").decode()
        assert result == {"Authorization": f"Basic {expected_token}"}

    def test_basic_auth_no_provider_no_method(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "basic-auth": AuthConfig(
                credentials_id="nexus-cred"
            )
        }
        base_registry_v2.maven_config.auth_config = "basic-auth"
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        expected_token = base64.b64encode(b"nexus_user:nexus_pass").decode()
        assert result == {"Authorization": f"Basic {expected_token}"}

    def test_basic_auth_missing_password(self, base_registry_v2, env_creds):
        env_creds["nexus-cred"]["data"] = {"username": "user"}
        
        base_registry_v2.auth_config = {
            "basic-auth": AuthConfig(
                credentials_id="nexus-cred",
                provider=Provider.NEXUS
            )
        }
        base_registry_v2.maven_config.auth_config = "basic-auth"
        
        with pytest.raises(ValueError, match="Basic auth requires both username and password"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)


class TestAzureAuthentication:
    def test_azure_not_implemented(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "azure-auth": AuthConfig(
                credentials_id="nexus-cred",
                provider=Provider.AZURE,
                auth_method="oauth2"
            )
        }
        base_registry_v2.maven_config.auth_config = "azure-auth"
        
        with pytest.raises(NotImplementedError, match="Azure auth is not yet implemented"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)


class TestCredentialHandling:
    def test_missing_credential_id(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "test-auth": AuthConfig(credentials_id="nonexistent")
        }
        base_registry_v2.maven_config.auth_config = "test-auth"
        
        with pytest.raises(ValueError, match="Credential 'nonexistent' not found"):
            resolve_v2_auth_headers(base_registry_v2, env_creds)

    def test_empty_env_creds(self, base_registry_v2):
        base_registry_v2.auth_config = {
            "test-auth": AuthConfig(credentials_id="any-cred")
        }
        base_registry_v2.maven_config.auth_config = "test-auth"
        
        with pytest.raises(ValueError, match="Credential 'any-cred' not found"):
            resolve_v2_auth_headers(base_registry_v2, {})

    def test_none_env_creds(self, base_registry_v2):
        base_registry_v2.auth_config = {
            "test-auth": AuthConfig(credentials_id="any-cred")
        }
        base_registry_v2.maven_config.auth_config = "test-auth"
        
        with pytest.raises(ValueError, match="Credential 'any-cred' not found"):
            resolve_v2_auth_headers(base_registry_v2, None)


class TestUnsupportedConfiguration:
    def test_unsupported_provider_method_combo(self, base_registry_v2, env_creds):
        base_registry_v2.auth_config = {
            "test-auth": AuthConfig(
                credentials_id="nexus-cred",
                provider=Provider.NEXUS,
                auth_method="oauth2"
            )
        }
        base_registry_v2.maven_config.auth_config = "test-auth"
        
        result = resolve_v2_auth_headers(base_registry_v2, env_creds)
        
        expected_token = base64.b64encode(b"nexus_user:nexus_pass").decode()
        assert result == {"Authorization": f"Basic {expected_token}"}
