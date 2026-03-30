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


def _get_cred_data(cred_id: str, env_creds: dict) -> dict:
    if not env_creds or cred_id not in env_creds:
        raise ValueError(f"Credential '{cred_id}' not found in decrypted credentials")
    return env_creds[cred_id].get(CRED_FIELD_DATA, {})


def _validate_user_pass_creds(cred_data: dict, context: str) -> tuple[str, str]:
    username = cred_data.get(CRED_FIELD_USERNAME)
    password = cred_data.get(CRED_FIELD_PASSWORD)
    if not username or not password:
        raise ValueError(f"{context} requires both username and password in credentials")
    return username, password


def _aws_bearer(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    username, password = _validate_user_pass_creds(cred_data, "AWS secret auth")

    from qubership_pipelines_common_library.v1.utils.utils_aws import AWSCodeArtifactHelper

    token = AWSCodeArtifactHelper.get_authorization_token(
        access_key=username,
        secret_key=password,
        domain=auth_cfg.aws_domain,
        region_name=auth_cfg.aws_region
    )
    logger.debug(f"AWS CodeArtifact token obtained for domain '{auth_cfg.aws_domain}' in region '{auth_cfg.aws_region}'")
    return {"Authorization": f"Bearer {token}"}


def _aws_assume_role(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    if not auth_cfg.aws_role_arn:
        raise ValueError("AWS assume_role requires awsRoleARN to be specified")

    _validate_user_pass_creds(cred_data, "AWS assume_role")
    raise NotImplementedError("AWS assume_role auth is not yet implemented")


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
    logger.debug(f"GCP token obtained for registry '{auth_cfg.gcp_reg_project}'")
    return {"Authorization": f"Bearer {getattr(creds, GCP_TOKEN_ATTR)}"}


def _gcp_federation(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    if not auth_cfg.gcp_oidc:
        raise ValueError("GCP federation requires gcpOIDC configuration")

    raise NotImplementedError("GCP federation (OIDC) auth is not yet implemented")


def _azure_oauth2(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    if not auth_cfg.azure_tenant_id:
        raise ValueError("Azure OAuth2 requires azureTenantId")

    raise NotImplementedError("Azure OAuth2 auth is not yet implemented")


def _basic_auth(auth_cfg: AuthConfig, cred_data: dict) -> dict:
    username, password = _validate_user_pass_creds(cred_data, "Basic auth")
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


_PROVIDER_HANDLERS = {
    (Provider.AWS, AUTH_METHOD_SECRET): _aws_bearer,
    (Provider.AWS, AUTH_METHOD_ASSUME_ROLE): _aws_assume_role,
    (Provider.GCP, AUTH_METHOD_SERVICE_ACCOUNT): _gcp_bearer,
    (Provider.GCP, AUTH_METHOD_FEDERATION): _gcp_federation,
    (Provider.AZURE, AUTH_METHOD_OAUTH2): _azure_oauth2,
    (Provider.NEXUS, AUTH_METHOD_USER_PASS): _basic_auth,
    (Provider.ARTIFACTORY, AUTH_METHOD_USER_PASS): _basic_auth,
}


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
        logger.debug(f"Anonymous access for registry '{registry.name}'")
        return None

    cred_data = _get_cred_data(auth_cfg.credentials_id, env_creds)

    handler = _PROVIDER_HANDLERS.get((auth_cfg.provider, auth_cfg.auth_method))
    if not handler:
        raise ValueError(
            f"Unsupported auth configuration (provider='{auth_cfg.provider.value}', "
            f"authMethod='{auth_cfg.auth_method}') for registry '{registry.name}'")

    return handler(auth_cfg, cred_data)
