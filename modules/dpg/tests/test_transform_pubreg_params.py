import pytest
from dpg.v1.utils.data_provider.transformer import transform_params_registry
from dpg.v1.utils.data_provider.middleware import UnifiedRegDef
from dpg.v1.utils.registry.types import (
    RegistryInfo,
    RegistryType,
    MavenConfig,
    AuthGCPFederation,
    AuthGCPServiceAccount,
    AuthManageIdentity,
    AuthAzureOAuth2,
    AuthSTSAssumeRole,
    AuthUserPassword,
    AuthRegistry
)


@pytest.mark.unit
class TestTransformParamsRegistry:
    @pytest.mark.parametrize("registry,params,expected_result", [
        # ===== E2E PARAMETERS TEST CASES =====
        # Test case 1: Basic Artifactory with no authentication
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://artifactory.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'artifactory',
                'PUB_REG_METHOD': None,
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': None,
                'PUB_REG_SECRET': None,
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://artifactory.example.com',
                'type': RegistryType.ARTIFACTORY,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthUserPassword(registry_url='https://artifactory.example.com', username='', password='')
            }
        ),
        # Test case 2: Artifactory with basic authentication
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://artifactory.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'artifactory',
                'PUB_REG_METHOD': 'basic_auth',
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': 'username',
                'PUB_REG_SECRET': 'password',
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://artifactory.example.com',
                'type': RegistryType.ARTIFACTORY,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthUserPassword(registry_url='https://artifactory.example.com', username='username', password='password')
            }
        ),
        # Test case 3: AWS with assume role
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://domain-123456.d.codeartifact.us-east-1.amazonaws.com/maven/domain/repo',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'aws',
                'PUB_REG_METHOD': 'assume_role',
                'PUB_REG_REGION': 'us-east-1',
                'PUB_REG_DOMAIN': 'domain',
                'PUB_REG_REPOSITORY': 'https://domain-123456.d.codeartifact.us-east-1.amazonaws.com/maven/domain/repo',
                'PUB_REG_KEY': 'access_key',
                'PUB_REG_SECRET': 'secret_key',
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://domain-123456.d.codeartifact.us-east-1.amazonaws.com/maven/domain/repo',
                'type': RegistryType.AWS,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthSTSAssumeRole(access_key='access_key', secret_key='secret_key', domain='domain', region_name='us-east-1', repository='https://domain-123456.d.codeartifact.us-east-1.amazonaws.com/maven/domain/repo', role_arn='', auth_type='assume_role', session_prefix='')
            }
        ),
        # Test case 4: GCP with federation
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://gcp.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'gcp',
                'PUB_REG_METHOD': 'federation',
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': None,
                'PUB_REG_SECRET': 'federation_token',
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://gcp.example.com',
                'type': RegistryType.GCP,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthGCPFederation(project='', region_name='', repository='', auth_type='federation', oidc_url='', oidc_method='secret', provider_id='', pool_id='', sa_email='', oidc_client_id='', oidc_client_secret='federation_token', oidc_custom_params='')
            }
        ),
        # Test case 5: Private authentication takes priority
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://artifactory.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'artifactory',
                'PUB_REG_METHOD': None,
                'NON_PUB_REG_METHOD': 'basic_auth',
                'PUB_REG_KEY': None,
                'PUB_REG_SECRET': None,
                'NON_PUB_REG_KEY': 'private_user',
                'NON_PUB_REG_SECRET': 'private_pass'
            },
            {
                'url': 'https://artifactory.example.com',
                'type': RegistryType.ARTIFACTORY,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthUserPassword(registry_url='https://artifactory.example.com', username='private_user', password='private_pass')
            }
        ),
        # Test case 6: Public authentication takes priority over private
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://artifactory.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'artifactory',
                'PUB_REG_METHOD': 'basic_auth',
                'NON_PUB_REG_METHOD': 'oauth2',
                'PUB_REG_KEY': 'public_user',
                'PUB_REG_SECRET': 'public_pass',
                'NON_PUB_REG_KEY': 'private_user',
                'NON_PUB_REG_SECRET': 'private_pass'
            },
            {
                'url': 'https://artifactory.example.com',
                'type': RegistryType.ARTIFACTORY,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthUserPassword(registry_url='https://artifactory.example.com', username='public_user', password='public_pass')
            }
        ),
        # Test case 7: Azure with managed identity
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://azure.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'azure',
                'PUB_REG_METHOD': 'managed-identity',
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': 'client_id',
                'PUB_REG_SECRET': 'client_secret',
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://azure.example.com',
                'type': RegistryType.AZURE,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthManageIdentity(client_id='client_id', client_secret='client_secret')
            }
        ),
        # Test case 8: GCP with service account
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://gcp.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'gcp',
                'PUB_REG_METHOD': 'service_account',
                'PUB_REG_PROJECT': 'my-project',
                'PUB_REG_REGION': 'us-central1',
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': None,
                'PUB_REG_SECRET': '{"type": "service_account", "project_id": "my-project", "private_key_id": "key123", "private_key": "-----BEGIN PRIVATE KEY-----\\n-----END PRIVATE KEY-----\\n", "client_email": "test@my-project.iam.gserviceaccount.com", "client_id": "123456789", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}',
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://gcp.example.com',
                'type': RegistryType.GCP,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthGCPServiceAccount(service_account_key_content='{"type": "service_account", "project_id": "my-project", "private_key_id": "key123", "private_key": "-----BEGIN PRIVATE KEY-----\\n-----END PRIVATE KEY-----\\n", "client_email": "test@my-project.iam.gserviceaccount.com", "client_id": "123456789", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}', project='my-project', region_name='us-central1')
            }
        ),
        # Test case 9: Fallback to fullRepositoryUrl when repositoryDomainName is empty
        (
            {
                'mavenConfig': {
                    'fullRepositoryUrl': 'https://fallback.example.com/repo',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'artifactory',
                'PUB_REG_METHOD': None,
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': None,
                'PUB_REG_SECRET': None,
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://fallback.example.com/repo',
                'type': RegistryType.ARTIFACTORY,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthUserPassword(registry_url='https://fallback.example.com/repo', username='', password='')
            }
        ),
        # Test case 10: Artifactory with basic authentication
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://artifactory.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'artifactory',
                'PUB_REG_METHOD': 'basic_auth',
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': 'username',
                'PUB_REG_SECRET': 'password',
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://artifactory.example.com',
                'type': RegistryType.ARTIFACTORY,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthUserPassword(registry_url='https://artifactory.example.com', username='username', password='password')
            }
        ),
        # Test case 11: GCP with federation authentication
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://gcp.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'gcp',
                'PUB_REG_METHOD': 'federation',
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': None,
                'PUB_REG_SECRET': 'federation_token',
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://gcp.example.com',
                'type': RegistryType.GCP,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthGCPFederation(project='', region_name='', repository='', auth_type='federation', oidc_url='', oidc_method='secret', provider_id='', pool_id='', sa_email='', oidc_client_id='', oidc_client_secret='federation_token', oidc_custom_params='')
            }
        ),
        # Test case 12: Artifactory with no authentication (fallback to fullRepositoryUrl)
        (
            {
                'mavenConfig': {
                    'fullRepositoryUrl': 'https://fallback.example.com/repo',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'artifactory',
                'PUB_REG_METHOD': None,
                'NON_PUB_REG_KEY': None,
                'PUB_REG_SECRET': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://fallback.example.com/repo',
                'type': RegistryType.ARTIFACTORY,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthUserPassword(registry_url='https://fallback.example.com/repo', username='', password='')
            }
        ),
        # Test case 13: AWS with assume_role and additional parameters
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://domain-123456.d.codeartifact.us-east-1.amazonaws.com/maven/domain/repo',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'aws',
                'PUB_REG_REGION': 'us-east-1',
                'PUB_REG_METHOD': 'assume_role',
                'PUB_REG_KEY': 'access_key',
                'PUB_REG_SECRET': 'secret_key',
                'PUB_REG_DOMAIN': 'domain',
                'PUB_REG_REPOSITORY': 'https://domain-123456-DIFF.d.codeartifact.us-east-1.amazonaws.com/maven/domain/repo',
                'parametersLevelVariable': 'value1',
                'ParameterFromSet-TEST-E2E-PARAMS2': 'ANOTHER_value',
                'parametersLevelVariable2': 'value2',
                'parameterFromSet-TEST-E2E-PARAMS': 'value'
            },
            {
                'url': 'https://domain-123456.d.codeartifact.us-east-1.amazonaws.com/maven/domain/repo',
                'type': RegistryType.AWS,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthSTSAssumeRole(access_key='access_key', secret_key='secret_key', domain='domain', region_name='us-east-1', repository='https://domain-123456-DIFF.d.codeartifact.us-east-1.amazonaws.com/maven/domain/repo', role_arn='', auth_type='assume_role', session_prefix='')
            }
        ),
        # Test case 14: Azure with OAuth2 client authentication
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://azure.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                'MAVEN_PROVIDER': 'azure',
                'PUB_REG_METHOD': 'oauth2-client',
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': 'client_id',
                'PUB_REG_SECRET': 'client_secret',
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://azure.example.com',
                'type': RegistryType.AZURE,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthAzureOAuth2(client_id='client_id', client_secret='client_secret')
            }
        ),
        # Test case 15: Default provider (artifactory) when none specified
        (
            {
                'mavenConfig': {
                    'repositoryDomainName': 'https://artifactory.example.com',
                    'targetRelease': 'release',
                    'targetStaging': 'staging',
                    'targetSnapshot': 'snapshot'
                },
            },
            {
                # No MAVEN_PROVIDER specified - should default to artifactory
                'PUB_REG_METHOD': None,
                'NON_PUB_REG_METHOD': None,
                'PUB_REG_KEY': None,
                'PUB_REG_SECRET': None,
                'NON_PUB_REG_KEY': None,
                'NON_PUB_REG_SECRET': None
            },
            {
                'url': 'https://artifactory.example.com',
                'type': RegistryType.ARTIFACTORY,
                'maven_config': MavenConfig(targetRelease='release',targetStaging='staging',targetSnapshot='snapshot'),
                'auth_config': AuthUserPassword(registry_url='https://artifactory.example.com', username='', password='')
            }
        )
    ])
    def test_transform_params_registry(self, registry, params, expected_result):
        maven_config = registry.get('mavenConfig', {})
        unified_registry = UnifiedRegDef(
            name='test',
            maven={
                'repo_domain_name': maven_config.get('repositoryDomainName', ''),
                'full_repo_url': maven_config.get('fullRepositoryUrl', ''),
                'release_repo': maven_config.get('targetRelease', ''),
                'staging_repo': maven_config.get('targetStaging', ''),
                'snapshot_repo': maven_config.get('targetSnapshot', ''),
            }
        )

        result = transform_params_registry(unified_registry, params)

        assert isinstance(result, RegistryInfo)
        assert result.url == expected_result['url']
        assert result.type == expected_result['type']
        assert isinstance(result.maven_config, MavenConfig)
        assert result.maven_config == expected_result['maven_config']
        assert type(result.auth_config) == type(expected_result['auth_config'])
        assert result.auth_config == expected_result['auth_config']
