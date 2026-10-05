import json
import logging
import re

from .middleware import UnifiedRegDef
from dpg.v1.utils.registry import RegistryInfo, MavenConfig, RegistryType, AuthUserPassword, ArtifactoryUtils

_GCP_MAVEN_URL_RE = re.compile(
    r"https://([a-z0-9-]+)-maven\.pkg\.dev/([^/]+)/([^/]+)"
)

def transform_params_registry(registry: UnifiedRegDef, params: dict) -> RegistryInfo:
    __type_reg = RegistryType.ARTIFACTORY
    __maven_config = MavenConfig(**{
        "targetRelease": registry.maven.get("release_repo"),
        "targetStaging": registry.maven.get("staging_repo"),
        "targetSnapshot": registry.maven.get("snapshot_repo")
    })

    __url = registry.maven.get('repo_domain_name', '')
    if not __url:
        __url = registry.maven.get('full_repo_url', '')

    __auth_config = AuthUserPassword(
            registry_url=__url,
            username="",
            password=""
        )

    __type_reg = RegistryType(params.get('MAVEN_PROVIDER', 'artifactory').lower())
    __pub_auth_method = params.get('PUB_REG_METHOD', None)
    __priv_auth_method = params.get('NON_PUB_REG_METHOD', None)
    reg_key = params.get('PUB_REG_KEY', None)
    reg_secret = params.get('PUB_REG_SECRET', None)
    reg_region = params.get('PUB_REG_REGION', "")
    reg_domain = params.get('PUB_REG_DOMAIN', "")
    reg_repo = params.get('PUB_REG_REPOSITORY', "")
    reg_project = params.get('PUB_REG_PROJECT', "")

    if __type_reg == RegistryType.GCP and params.get('PUB_REG_METHOD') == 'service_account':
        if not reg_project:
            sa_secret = params.get('PUB_REG_SECRET', '')
            try:
                reg_project = json.loads(sa_secret).get('project_id', '')
                if reg_project:
                    logging.debug(f"reg_project extracted from SA key: {reg_project}")
                else:
                    logging.warning("PUB_REG_PROJECT is not set and SA key has no project_id — GCP registry query will fail")
            except json.JSONDecodeError:
                logging.warning("PUB_REG_PROJECT is not set and PUB_REG_SECRET is not valid JSON — GCP registry query will fail")
        if not reg_region or not reg_repo:
            m = _GCP_MAVEN_URL_RE.match(__url)
            if m:
                if not reg_region:
                    reg_region = m.group(1)
                    logging.debug(f"reg_region extracted from registry URL: {reg_region}")
                if not reg_repo:
                    reg_repo = m.group(3)
                    logging.debug(f"reg_repo extracted from registry URL: {reg_repo}")
            elif not reg_region or not reg_repo:
                logging.warning(f"PUB_REG_REGION or PUB_REG_REPOSITORY not set and could not be parsed from URL '{__url}' — GCP registry query will fail")
    non_pub_reg_key = params.get('NON_PUB_REG_KEY', None)
    non_pub_reg_secret = params.get('NON_PUB_REG_SECRET', None)
    secret_key= params.get('PUB_REG_SECRET', None)
    reg_session_prefix = params.get('PUB_REG_ROLE_SESSION_PREFIX', "")
    reg_role_arn = params.get('PUB_REG_ROLE_ARN', "")
    pub_reg_oidc_url = params.get('PUB_REG_OIDC_URL', "")
    pub_reg_oidc_provider = params.get('PUB_REG_OIDC_PROVIDER', "secret")
    # Additional GCP federation parameters
    pub_reg_oidc_method = params.get('PUB_REG_OIDC_METHOD', "secret")
    pub_reg_provider_id = params.get('PUB_REG_PROVIDER_ID', "")
    pub_reg_pool_id = params.get('PUB_REG_POOL_ID', "")
    pub_reg_sa_email = params.get('PUB_REG_SA_EMAIL', "")
    # External OIDC provider parameters
    pub_reg_oidc_client_id = params.get('PUB_REG_OIDC_CLIENT_ID', "")
    pub_reg_oidc_client_secret = params.get('PUB_REG_OIDC_CLIENT_SECRET', "")
    pub_reg_oidc_custom_params = params.get('PUB_REG_OIDC_CUSTOM_PARAM', "")

    if __pub_auth_method:
        # For E2EParameters, pass all federation and assume_role parameters
        __auth_config = ArtifactoryUtils.detect_auth_method(
            type_reg=__type_reg,
            url=__url,
            authmethod=__pub_auth_method,
            reg_key=reg_key,
            reg_secret=reg_secret,
            reg_region=reg_region,
            reg_domain=reg_domain,
            reg_repo=reg_repo,
            reg_project=reg_project,
            reg_session_prefix=reg_session_prefix,
            reg_role_arn=reg_role_arn,
            pub_reg_oidc_url=pub_reg_oidc_url,
            pub_reg_oidc_provider=pub_reg_oidc_provider,
            pub_reg_oidc_method=pub_reg_oidc_method,
            pub_reg_provider_id=pub_reg_provider_id,
            pub_reg_pool_id=pub_reg_pool_id,
            pub_reg_sa_email=pub_reg_sa_email,
            pub_reg_oidc_client_id=pub_reg_oidc_client_id,
            pub_reg_oidc_client_secret=pub_reg_oidc_client_secret,
            pub_reg_oidc_custom_params=pub_reg_oidc_custom_params
        )
    elif __priv_auth_method:
        __auth_config = ArtifactoryUtils.detect_auth_method(
            type_reg=__type_reg,
            url=__url,
            authmethod=__priv_auth_method,
            reg_key=non_pub_reg_key,
            reg_secret=non_pub_reg_secret
        )


    return RegistryInfo(
        url=__url,
        type=__type_reg,
        maven_config=__maven_config,
        auth_config=__auth_config
    )
