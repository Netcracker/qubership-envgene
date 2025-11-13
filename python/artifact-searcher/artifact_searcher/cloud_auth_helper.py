"""
CloudAuthHelper - Authentication bridge for RegDef V2 cloud registries
"""

import re
from typing import Optional, Dict
from loguru import logger

try:
    from qubership_pipelines_common_library.v1.maven_client import MavenArtifactSearcher
except ImportError:
    logger.warning("qubership_pipelines_common_library not available - V2 cloud registry support disabled")
    MavenArtifactSearcher = None

from artifact_searcher.utils.models import Registry, AuthConfig


class CloudAuthHelper:
    
    @staticmethod
    def resolve_auth_config(registry: Registry, artifact_type: str = "maven") -> Optional[AuthConfig]:
        """Resolves authConfig reference for given artifact type"""
        if artifact_type == "maven":
            config = registry.maven_config
        elif artifact_type == "docker":
            config = registry.docker_config
        else:
            logger.warning(f"Unsupported artifact type: {artifact_type}")
            return None
        
        auth_ref = getattr(config, 'auth_config', None)
        if not auth_ref:
            logger.debug(f"No authConfig reference in {artifact_type} config")
            return None
        
        if not registry.auth_config:
            logger.warning(
                f"Registry has no authConfig dictionary but {artifact_type} "
                f"references '{auth_ref}'"
            )
            return None
        
        auth_config = registry.auth_config.get(auth_ref)
        if not auth_config:
            available_keys = list(registry.auth_config.keys()) if registry.auth_config else []
            logger.error(f"AuthConfig reference '{auth_ref}' not found. Available: {available_keys}")
            return None
        
        logger.info(f"Resolved authConfig '{auth_ref}' → provider: {auth_config.provider}, method: {auth_config.auth_method}")
        return auth_config
    
    @staticmethod
    def resolve_credentials(auth_config: AuthConfig, env_creds: Dict[str, dict]) -> dict:
        """Resolves credentials from credentialsId"""
        cred_id = auth_config.credentials_id
        
        if not env_creds:
            raise ValueError("env_creds is empty or None - cannot resolve credentials")
        
        if cred_id not in env_creds:
            available = list(env_creds.keys())
            raise KeyError(f"Credential '{cred_id}' not found in env_creds. Available: {available}")
        
        creds = env_creds[cred_id]
        logger.info(f"Resolved credentials for '{cred_id}'")
        
        if auth_config.provider == "aws":
            if "username" not in creds or "password" not in creds:
                raise ValueError(f"AWS credentials must have 'username' and 'password'. Got: {list(creds.keys())}")
        elif auth_config.provider == "gcp":
            if auth_config.auth_method == "service_account":
                if "secret" not in creds:
                    raise ValueError(f"GCP service_account credentials must have 'secret'. Got: {list(creds.keys())}")
        
        return creds
    
    @staticmethod
    def _extract_repository_name(url: str) -> str:
        """Extract repository name from Maven URL (AWS CodeArtifact or GCP Artifact Registry)"""
        url = url.rstrip("/")
        if "codeartifact" in url and "/maven/" in url:
            parts = url.split("/maven/")
            if len(parts) > 1:
                repo = parts[1].split("/")[0]
                logger.debug(f"Extracted AWS CodeArtifact repo: {repo}")
                return repo
        if "pkg.dev" in url:
            parts = url.split("/")
            if len(parts) >= 5:
                repo = parts[4]
                logger.debug(f"Extracted GCP Artifact Registry repo: {repo}")
                return repo
        repo = url.split("/")[-1]
        logger.warning(f"Using generic extraction for repo name: {repo} from {url}")
        return repo
    
    @staticmethod
    def _extract_region(url: str, auth_config: AuthConfig) -> str:
        """Extract region from URL or auth_config"""
        if auth_config.provider == "aws" and auth_config.aws_region:
            return auth_config.aws_region
        aws_match = re.search(r'\.([a-z0-9-]+)\.amazonaws\.com', url)
        if aws_match:
            region = aws_match.group(1)
            logger.debug(f"Extracted AWS region from URL: {region}")
            return region
        gcp_match = re.search(r'([a-z0-9-]+)-maven\.pkg\.dev', url)
        if gcp_match:
            region = gcp_match.group(1)
            logger.debug(f"Extracted GCP region from URL: {region}")
            return region
        
        logger.warning(f"Could not extract region from URL: {url}, using default")
        return "us-east-1"
    
    @staticmethod
    def create_maven_searcher(registry: Registry, env_creds: Dict[str, dict]) -> 'MavenArtifactSearcher':
        """Creates authenticated MavenArtifactSearcher for V2 registry"""
        if MavenArtifactSearcher is None:
            raise ImportError("qubership_pipelines_common_library not available. Cannot create Maven Client for V2 cloud registries.")
        auth_config = CloudAuthHelper.resolve_auth_config(registry, "maven")
        if not auth_config:
            raise ValueError("Could not resolve authConfig for maven artifacts")
        if not auth_config.provider:
            raise ValueError("AuthConfig has no provider specified")
        
        if auth_config.provider not in ["aws", "gcp"]:
            raise ValueError(f"Unsupported provider: {auth_config.provider}. Supported: aws, gcp")
        
        creds = CloudAuthHelper.resolve_credentials(auth_config, env_creds)
        registry_url = registry.maven_config.repository_domain_name
        searcher = MavenArtifactSearcher(registry_url)
        if auth_config.provider == "aws":
            return CloudAuthHelper._configure_aws(searcher, auth_config, creds, registry_url)
        elif auth_config.provider == "gcp":
            return CloudAuthHelper._configure_gcp(searcher, auth_config, creds, registry_url)
    
    @staticmethod
    def _configure_aws(searcher: 'MavenArtifactSearcher', auth_config: AuthConfig, creds: dict,
                       registry_url: str) -> 'MavenArtifactSearcher':
        """Configure AWS CodeArtifact authentication"""
        access_key = creds["username"]
        secret_key = creds["password"]
        if not auth_config.aws_domain:
            raise ValueError("AWS auth requires aws_domain in authConfig")
        
        region = CloudAuthHelper._extract_region(registry_url, auth_config)
        repo_name = CloudAuthHelper._extract_repository_name(registry_url)
        
        logger.info(f"Configuring AWS CodeArtifact: domain={auth_config.aws_domain}, region={region}, repository={repo_name}")
        return searcher.with_aws_code_artifact(
            access_key=access_key,
            secret_key=secret_key,
            domain=auth_config.aws_domain,
            region_name=region,
            repository=repo_name
        )
    
    @staticmethod
    def _configure_gcp(searcher: 'MavenArtifactSearcher', auth_config: AuthConfig, creds: dict,
                       registry_url: str) -> 'MavenArtifactSearcher':
        """Configure GCP Artifact Registry authentication"""
        if auth_config.auth_method != "service_account":
            raise ValueError(f"GCP auth_method '{auth_config.auth_method}' not supported. Only 'service_account' is supported.")
        
        service_account_json = creds["secret"]
        if not auth_config.gcp_reg_project:
            raise ValueError("GCP auth requires gcp_reg_project in authConfig")
        
        region = CloudAuthHelper._extract_region(registry_url, auth_config)
        repo_name = CloudAuthHelper._extract_repository_name(registry_url)
        
        logger.info(f"Configuring GCP Artifact Registry: project={auth_config.gcp_reg_project}, region={region}, repository={repo_name}")
        
        credential_params = {"service_account_key": service_account_json}
        
        return searcher.with_gcp_artifact_registry(
            credential_params=credential_params,
            project=auth_config.gcp_reg_project,
            region_name=region,
            repository=repo_name
        )


# Convenience function for direct use
def create_maven_searcher_from_registry(registry: Registry, env_creds: Dict[str, dict]) -> 'MavenArtifactSearcher':
    """Convenience wrapper for CloudAuthHelper.create_maven_searcher"""
    return CloudAuthHelper.create_maven_searcher(registry, env_creds)
