import re
import json
from typing import Optional, Dict
from loguru import logger

try:
    from qubership_pipelines_common_library.v1.maven_client import MavenArtifactSearcher
except ImportError:
    logger.warning("qubership_pipelines_common_library not available - V2 cloud registry support disabled")
    MavenArtifactSearcher = None

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    GCP_AUTH_AVAILABLE = True
except ImportError:
    GCP_AUTH_AVAILABLE = False
    logger.debug("google-auth not available - GCP direct download fallback disabled")

from artifact_searcher.utils.models import Registry, AuthConfig


class CloudAuthHelper:
    
    @staticmethod
    def resolve_auth_config(registry: Registry, artifact_type: str = "maven") -> Optional[AuthConfig]:
        if artifact_type != "maven":
            logger.warning(f"Unsupported artifact type: {artifact_type}. Only 'maven' is supported.")
            return None
        
        config = registry.maven_config
        auth_ref = getattr(config, 'auth_config', None)
        if not auth_ref:
            logger.debug("No authConfig reference in maven config")
            return None
        
        if not registry.auth_config:
            logger.warning(f"Registry has no authConfig dictionary but maven config references '{auth_ref}'")
            return None
        
        auth_config = registry.auth_config.get(auth_ref)
        if not auth_config:
            available_keys = list(registry.auth_config.keys()) if registry.auth_config else []
            logger.error(f"AuthConfig reference '{auth_ref}' not found. Available: {available_keys}")
            return None
        
        logger.info(f"Resolved authConfig '{auth_ref}' -> provider: {auth_config.provider}")
        return auth_config

    @staticmethod
    def resolve_credentials(auth_config: AuthConfig, env_creds: Dict[str, dict]) -> dict:
        cred_id = auth_config.credentials_id
        
        # Anonymous access - no credentials needed (for Artifactory/Nexus V2)
        if not cred_id:
            logger.info("No credentials_id specified - using anonymous access")
            return {}
        
        if not env_creds:
            raise ValueError("env_creds is empty or None - cannot resolve credentials")
        
        if cred_id not in env_creds:
            available = list(env_creds.keys())
            raise KeyError(f"Credential '{cred_id}' not found in env_creds. Available: {available}")
        
        cred_entry = env_creds[cred_id]
        logger.info(f"Resolved credentials for '{cred_id}'")

        if isinstance(cred_entry, dict) and "data" in cred_entry:
            creds = cred_entry["data"]
        else:
            creds = cred_entry
        
        if auth_config.provider == "aws":
            if "username" not in creds or "password" not in creds:
                raise ValueError(f"AWS credentials must have 'username' and 'password'. Got: {list(creds.keys())}")
        elif auth_config.provider == "gcp":
            if auth_config.auth_method == "service_account":
                if "secret" not in creds:
                    raise ValueError(f"GCP service_account credentials must have 'secret'. Got: {list(creds.keys())}")
        elif auth_config.provider in ["artifactory", "nexus"]:
            # Allow anonymous access for Artifactory/Nexus
            # Only validate credentials if they are provided
            if "username" in creds and not creds.get("username"):
                logger.warning(f"{auth_config.provider} has empty username - using anonymous access")
            if "password" in creds and not creds.get("password"):
                logger.warning(f"{auth_config.provider} has empty password - using anonymous access")
        
        return creds

    @staticmethod
    def _extract_repository_name(url: str) -> str:
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
        logger.warning(f"Using generic extraction for repo name: {repo}")
        return repo
    
    @staticmethod
    def _extract_region(url: str, auth_config: AuthConfig) -> str:
        if auth_config.provider == "aws" and auth_config.aws_region:
            return auth_config.aws_region
        aws_match = re.search(r'\.([a-z0-9-]+)\.amazonaws\.com', url)
        if aws_match:
            return aws_match.group(1)
        gcp_match = re.search(r'([a-z0-9-]+)-maven\.pkg\.dev', url)
        if gcp_match:
            return gcp_match.group(1)
        
        logger.warning(f"Could not extract region from URL: {url}, using default")
        return "us-east-1"

    # Default timeout for MavenArtifactSearcher: (connect_timeout, read_timeout)
    DEFAULT_SEARCHER_TIMEOUT = (30, 180)  # 30s connect, 180s read

    @staticmethod
    def create_maven_searcher(registry: Registry, env_creds: Dict[str, dict]) -> 'MavenArtifactSearcher':
        if MavenArtifactSearcher is None:
            raise ImportError("qubership_pipelines_common_library not available")
        
        auth_config = CloudAuthHelper.resolve_auth_config(registry, "maven")
        if not auth_config:
            raise ValueError("Could not resolve authConfig for maven artifacts")
        if not auth_config.provider:
            raise ValueError("AuthConfig has no provider specified")
        if auth_config.provider not in ["aws", "gcp", "artifactory", "nexus"]:
            raise ValueError(f"Unsupported provider: {auth_config.provider}. Supported: aws, gcp, artifactory, nexus")
        
        creds = CloudAuthHelper.resolve_credentials(auth_config, env_creds)
        registry_url = registry.maven_config.repository_domain_name
        # Pass timeout to avoid indefinite hanging in requests.Session
        searcher = MavenArtifactSearcher(registry_url, params={"timeout": CloudAuthHelper.DEFAULT_SEARCHER_TIMEOUT})
        
        if auth_config.provider == "aws":
            return CloudAuthHelper._configure_aws(searcher, auth_config, creds, registry_url)
        elif auth_config.provider == "gcp":
            return CloudAuthHelper._configure_gcp(searcher, auth_config, creds, registry_url)
        elif auth_config.provider == "artifactory":
            return CloudAuthHelper._configure_artifactory(searcher, creds)
        elif auth_config.provider == "nexus":
            return CloudAuthHelper._configure_nexus(searcher, creds)

    @staticmethod
    def _configure_aws(searcher: 'MavenArtifactSearcher', auth_config: AuthConfig, creds: dict,
                       registry_url: str) -> 'MavenArtifactSearcher':
        access_key = creds["username"]
        secret_key = creds["password"]
        if not auth_config.aws_domain:
            raise ValueError("AWS auth requires aws_domain in authConfig")
        
        region = CloudAuthHelper._extract_region(registry_url, auth_config)
        repo_name = CloudAuthHelper._extract_repository_name(registry_url)
        
        logger.info(f"Configuring AWS CodeArtifact: domain={auth_config.aws_domain}, region={region}")
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
        if auth_config.auth_method != "service_account":
            raise ValueError(f"GCP auth_method '{auth_config.auth_method}' not supported")
        
        service_account_data = creds["secret"]
        # Handle both string (JSON) and dict (parsed YAML) formats
        if isinstance(service_account_data, dict):
            # Already parsed - convert to JSON string for the common library
            service_account_json = json.dumps(service_account_data)
            logger.debug("Converted GCP service account dict to JSON string")
        elif isinstance(service_account_data, str):
            # Already a JSON string
            service_account_json = service_account_data
        else:
            raise ValueError(f"GCP service account must be dict or JSON string, got: {type(service_account_data)}")
        
        if not auth_config.gcp_reg_project:
            raise ValueError("GCP auth requires gcp_reg_project in authConfig")
        
        region = CloudAuthHelper._extract_region(registry_url, auth_config)
        repo_name = CloudAuthHelper._extract_repository_name(registry_url)
        
        logger.info(f"Configuring GCP Artifact Registry: project={auth_config.gcp_reg_project}, region={region}")
        return searcher.with_gcp_artifact_registry(
            credential_params={"service_account_key": service_account_json},
            project=auth_config.gcp_reg_project,
            region_name=region,
            repository=repo_name
        )

    @staticmethod
    def _configure_artifactory(searcher: 'MavenArtifactSearcher', creds: dict) -> 'MavenArtifactSearcher':
        username = creds.get("username", "")
        password = creds.get("password", "")
        logger.info("Configuring JFrog Artifactory with credentials")
        return searcher.with_artifactory(username=username, password=password)

    @staticmethod
    def _configure_nexus(searcher: 'MavenArtifactSearcher', creds: dict) -> 'MavenArtifactSearcher':
        username = creds.get("username", "")
        password = creds.get("password", "")
        logger.info("Configuring Sonatype Nexus with credentials")
        return searcher.with_nexus(username=username, password=password)

    @staticmethod
    def get_gcp_access_token(service_account_json: str) -> Optional[str]:
        """
        Generate a GCP OAuth access token from service account credentials.
        Used for direct HTTP downloads when the common library method times out.
        """
        if not GCP_AUTH_AVAILABLE:
            logger.warning("google-auth library not available - cannot generate GCP access token")
            return None
        
        try:
            if isinstance(service_account_json, str):
                sa_info = json.loads(service_account_json)
            else:
                sa_info = service_account_json
            
            credentials = service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            credentials.refresh(Request())
            logger.debug("Generated fresh GCP OAuth access token")
            return credentials.token
        except Exception as e:
            logger.error(f"Failed to generate GCP access token: {e}")
            return None
    
    @staticmethod
    def get_gcp_credentials_from_registry(registry: Registry, env_creds: Dict[str, dict]) -> Optional[str]:
        """
        Extract GCP service account JSON from registry auth config and env_creds.
        Returns the service account JSON string for token generation.
        """
        auth_config = CloudAuthHelper.resolve_auth_config(registry, "maven")
        if not auth_config or auth_config.provider != "gcp":
            return None
        
        try:
            creds = CloudAuthHelper.resolve_credentials(auth_config, env_creds)
            service_account_data = creds.get("secret")
            if isinstance(service_account_data, dict):
                return json.dumps(service_account_data)
            return service_account_data
        except Exception as e:
            logger.warning(f"Failed to extract GCP credentials: {e}")
            return None
