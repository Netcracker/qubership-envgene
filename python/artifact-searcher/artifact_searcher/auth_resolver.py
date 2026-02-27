import base64
import json
from typing import Optional

from artifact_searcher.utils.models import AuthConfig, Provider, RegistryV2
from envgenehelper import logger

AUTH_METHOD_USER_PASS = "user_pass"
AUTH_METHOD_SECRET = "secret"
AUTH_METHOD_SERVICE_ACCOUNT = "service_account"
AUTH_METHOD_ANONYMOUS = "anonymous"
AUTH_METHOD_ASSUME_ROLE = "assume_role"
AUTH_METHOD_FEDERATION = "federation"
AUTH_METHOD_OAUTH2 = "oauth2"

AWS_SERVICE_CODEARTIFACT = "codeartifact"
AWS_TOKEN_KEY = "authorizationToken"
GCP_TOKEN_ATTR = "gcp_authorization_token"

CRED_FIELD_USERNAME = "username"
CRED_FIELD_PASSWORD = "password"
CRED_FIELD_SECRET = "secret"
CRED_FIELD_DATA = "data"


def resolve_v2_auth_headers(registry: RegistryV2, env_creds: dict) -> Optional[dict]:
    """Resolve V2 registry authConfig into HTTP Authorization headers.
    Returns None for anonymous access."""
    auth_config = registry.maven_config.auth_config
    if auth_config not in registry.auth_config:
        raise ValueError(
            f"AuthConfig '{auth_config}' not found in registry '{registry.name}'. "
            f"Available: {list(registry.auth_config.keys())}")

    auth_cfg = registry.auth_config[auth_config]
    
    if auth_cfg.auth_method == AUTH_METHOD_ANONYMOUS:
        logger.info(f"Anonymous access for registry '{registry.name}'")
        return None
    
    cred_data = _get_cred_data(auth_cfg.credentials_id, env_creds)

    if auth_cfg.provider == Provider.AWS:
        if auth_cfg.auth_method == AUTH_METHOD_SECRET:
            logger.info(f"Resolving AWS ECR secret auth for registry '{registry.name}'")
            return _aws_bearer(auth_cfg, cred_data)
        elif auth_cfg.auth_method == AUTH_METHOD_ASSUME_ROLE:
            logger.info(f"Resolving AWS assume role auth for registry '{registry.name}'")
            return _aws_assume_role(auth_cfg, cred_data)
        else:
            raise ValueError(f"Unsupported AWS authMethod: {auth_cfg.auth_method}")

    if auth_cfg.provider == Provider.GCP:
        if auth_cfg.auth_method == AUTH_METHOD_SERVICE_ACCOUNT:
            logger.info(f"Resolving GCP service account auth for registry '{registry.name}'")
            return _gcp_bearer(auth_cfg, cred_data)
        elif auth_cfg.auth_method == AUTH_METHOD_FEDERATION:
            logger.info(f"Resolving GCP federation (OIDC) auth for registry '{registry.name}'")
            return _gcp_federation(auth_cfg, cred_data)
        else:
            raise ValueError(f"Unsupported GCP authMethod: {auth_cfg.auth_method}")

    if auth_cfg.provider == Provider.AZURE:
        if auth_cfg.auth_method == AUTH_METHOD_OAUTH2:
            logger.info(f"Resolving Azure OAuth2 auth for registry '{registry.name}'")
            return _azure_oauth2(auth_cfg, cred_data)
        else:
            raise ValueError(f"Unsupported Azure authMethod: {auth_cfg.auth_method}")

    if auth_cfg.provider in (Provider.NEXUS, Provider.ARTIFACTORY):
        if auth_cfg.auth_method == AUTH_METHOD_USER_PASS:
            logger.info(f"Resolving basic auth for {auth_cfg.provider.value} registry '{registry.name}'")
            return _basic_auth(cred_data)
        else:
            raise ValueError(f"Unsupported {auth_cfg.provider.value} authMethod: {auth_cfg.auth_method}")

    raise ValueError(
        f"Unsupported auth configuration (provider='{auth_cfg.provider}', "
        f"authMethod='{auth_cfg.auth_method}') for registry '{registry.name}'")


def _get_cred_data(cred_id: str, env_creds: dict) -> dict:
    if not env_creds or cred_id not in env_creds:
        raise ValueError(f"Credential '{cred_id}' not found in decrypted credentials")
    return env_creds[cred_id].get(CRED_FIELD_DATA, {})


def _aws_bearer(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    if not auth_cfg.aws_region:
        raise ValueError("AWS authConfig must specify 'awsRegion'")

    username = cred_data.get(CRED_FIELD_USERNAME)
    password = cred_data.get(CRED_FIELD_PASSWORD)
    if not username or not password:
        raise ValueError(f"AWS {auth_cfg.auth_method} auth requires both username (access key) and password (secret key)")

    from qubership_pipelines_common_library.v2.artifacts_finder.auth.aws_credentials import AwsCredentialsProvider
    provider = AwsCredentialsProvider().with_direct_credentials(
        access_key=username,
        secret_key=password,
        region_name=auth_cfg.aws_region,
    )
    token = provider.get_ecr_authorization_token()
    logger.debug(f"AWS ECR token obtained for region '{auth_cfg.aws_region}'")
    return {"Authorization": f"Bearer {token}"}


def _gcp_bearer(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    sa_key = cred_data.get(CRED_FIELD_SECRET)
    if not sa_key:
        raise ValueError("GCP service_account requires credential with 'secret' field containing SA JSON key")

    try:
        json.loads(sa_key)
    except json.JSONDecodeError:
        raise ValueError("GCP service account key must be valid JSON")

    try:
        from qubership_pipelines_common_library.v2.artifacts_finder.auth.gcp_credentials import GcpCredentialsProvider
    except ImportError as e:
        raise ValueError(f"GCP dependencies not available: {e}")

    creds = GcpCredentialsProvider().with_service_account_key(
        service_account_key_content=sa_key,
    ).get_credentials()
    logger.info(f"GCP token obtained for registry '{auth_cfg.gcp_reg_project}'")
    return {"Authorization": f"Bearer {getattr(creds, GCP_TOKEN_ATTR)}"}


def _aws_assume_role(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    if not auth_cfg.aws_role_arn:
        raise ValueError("AWS assume_role requires awsRoleARN to be specified")

    username = cred_data.get(CRED_FIELD_USERNAME)
    password = cred_data.get(CRED_FIELD_PASSWORD)
    if not username or not password:
        raise ValueError("AWS assume_role requires both username (access key) and password (secret key)")

    raise NotImplementedError("AWS assume_role auth is not yet implemented")


def _gcp_federation(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    if not auth_cfg.gcp_oidc:
        raise ValueError("GCP federation requires gcpOIDC configuration")

    raise NotImplementedError("GCP federation (OIDC) auth is not yet implemented")


def _azure_oauth2(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    if not auth_cfg.azure_tenant_id:
        raise ValueError("Azure OAuth2 requires azureTenantId")
    
    raise NotImplementedError("Azure OAuth2 auth is not yet implemented")


def _basic_auth(cred_data: dict) -> dict:
    username = cred_data.get(CRED_FIELD_USERNAME)
    password = cred_data.get(CRED_FIELD_PASSWORD)
    if not username or not password:
        raise ValueError("Basic auth requires both username and password in credentials")
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}
