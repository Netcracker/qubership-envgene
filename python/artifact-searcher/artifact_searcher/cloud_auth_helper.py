import json
import re
from typing import Dict, Optional

from envgenehelper import logger

from artifact_searcher.utils.models import AuthConfig, Registry

try:
    from qubership_pipelines_common_library.v1.maven_client import MavenArtifactSearcher
except ImportError:
    MavenArtifactSearcher = None

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    GCP_AUTH_AVAILABLE = True
except ImportError:
    GCP_AUTH_AVAILABLE = False


# Timeout for MavenArtifactSearcher: (connect_timeout, read_timeout)
DEFAULT_SEARCHER_TIMEOUT = (30, 60)


class CloudAuthHelper:
    """Helper for V2 cloud registry authentication (AWS, GCP, Artifactory, Nexus)."""

    @staticmethod
    def resolve_auth_config(registry: Registry, artifact_type: str = "maven") -> Optional[AuthConfig]:
        """Resolve authConfig from registry maven config reference."""
        if artifact_type != "maven":
            return None

        auth_ref = getattr(registry.maven_config, 'auth_config', None)
        if not auth_ref:
            return None

        if not registry.auth_config:
            logger.warning(f"No authConfig dict but maven config references '{auth_ref}'")
            return None

        auth_config = registry.auth_config.get(auth_ref)
        if not auth_config:
            logger.error(f"AuthConfig '{auth_ref}' not found. Available: {list(registry.auth_config.keys())}")
            return None

        logger.info(f"Resolved authConfig '{auth_ref}' -> provider: {auth_config.provider}")
        return auth_config

    @staticmethod
    def resolve_credentials(auth_config: AuthConfig, env_creds: Optional[Dict[str, dict]]) -> Optional[dict]:
        """Resolve credentials from env_creds based on auth_config.credentials_id.
        
        Returns:
            dict: Credential data if found and non-anonymous
            None: For anonymous access (no credentialsId or empty username/password)
        """
        cred_id = auth_config.credentials_id
        if not cred_id:
            logger.info("No credentialsId specified, using anonymous access")
            return None

        if not env_creds or cred_id not in env_creds:
            raise KeyError(f"Credential '{cred_id}' not found in env_creds")

        cred_entry = env_creds[cred_id]
        
        # Extract credential data from the new structure: {"type": "...", "data": {...}}
        cred_type = cred_entry.get("type") if isinstance(cred_entry, dict) else None
        cred_data = cred_entry.get("data", cred_entry) if isinstance(cred_entry, dict) else cred_entry
        
        # Check for anonymous access (empty username/password for usernamePassword type)
        if cred_type == "usernamePassword":
            username = cred_data.get("username", "")
            password = cred_data.get("password", "")
            if not username and not password:
                logger.info(f"Credential '{cred_id}' is anonymous (empty username/password)")
                return None
            creds = {"username": username, "password": password}
        elif cred_type == "secret":
            # For GCP service account JSON or other secret-based credentials
            if "secret" in cred_data:
                creds = cred_data
            else:
                # Handle case where data itself is the secret
                creds = {"secret": cred_data}
        else:
            # Fallback for unknown credential types
            creds = cred_data
        
        logger.info(f"Resolved credentials for '{cred_id}' (type: {cred_type})")

        # Validate required fields per provider
        if auth_config.provider == "aws":
            if "username" not in creds or "password" not in creds:
                raise ValueError(f"AWS credentials must have 'username' and 'password'")
        elif auth_config.provider == "gcp" and auth_config.auth_method == "service_account":
            if "secret" not in creds:
                raise ValueError(f"GCP service_account credentials must have 'secret'")

        return creds

    @staticmethod
    def _extract_repository_name(url: str) -> str:
        """Extract repository name from registry URL."""
        url = url.rstrip("/")
        # AWS CodeArtifact: .../maven/<repo>/...
        if "codeartifact" in url and "/maven/" in url:
            parts = url.split("/maven/")
            if len(parts) > 1:
                return parts[1].split("/")[0]
        # GCP Artifact Registry: https://<region>-maven.pkg.dev/<project>/<repo>/
        if "pkg.dev" in url:
            parts = url.split("/")
            if len(parts) >= 5:
                return parts[4]
        return url.split("/")[-1]

    
    @staticmethod
    def _extract_region(url: str, auth_config: AuthConfig) -> str:
        """Extract region from URL or auth_config. Prefers explicit config over URL extraction."""
        if auth_config.provider == "aws" and auth_config.aws_region:
            return auth_config.aws_region
        aws_match = re.search(r'\.([a-z0-9-]+)\.amazonaws\.com', url)
        if aws_match:
            return aws_match.group(1)
        gcp_match = re.search(r'([a-z0-9-]+)-maven\.pkg\.dev', url)
        if gcp_match:
            return gcp_match.group(1)
        logger.warning(f"Could not extract region from URL '{url}', using default 'us-east-1'")
        return "us-east-1"

    @staticmethod
    def create_maven_searcher(registry: Registry, env_creds: Optional[Dict[str, dict]]) -> 'MavenArtifactSearcher':
        """Create configured MavenArtifactSearcher for the registry provider.
        
        Provider auto-detection: If auth_config.provider is not specified, it will be
        auto-detected from the registry URL.
        """
        if MavenArtifactSearcher is None:
            raise ImportError("qubership_pipelines_common_library not available")

        auth_config = CloudAuthHelper.resolve_auth_config(registry, "maven")
        if not auth_config:
            raise ValueError("Could not resolve authConfig for maven artifacts")
        
        registry_url = registry.maven_config.repository_domain_name
        
        # Provider is required in RegDef v2
        provider = auth_config.provider
        if not provider:
            logger.error(f"V2 fallback: provider field is required in authConfig for registry '{registry.name}'")
            raise ValueError(f"Provider field is required in authConfig for registry '{registry.name}'")
        
        if provider not in ["aws", "gcp", "artifactory", "nexus"]:
            raise ValueError(f"Unsupported provider: {provider}")

        # Resolve credentials (returns None for anonymous access)
        creds = CloudAuthHelper.resolve_credentials(auth_config, env_creds)
        searcher = MavenArtifactSearcher(registry_url, params={"timeout": DEFAULT_SEARCHER_TIMEOUT})

        # AWS and GCP require credentials - cannot work anonymously
        if provider in ["aws", "gcp"] and creds is None:
            raise ValueError(f"{provider.upper()} requires credentials - anonymous access not supported")

        if provider == "aws":
            return CloudAuthHelper._configure_aws(searcher, auth_config, creds, registry_url)
        elif provider == "gcp":
            return CloudAuthHelper._configure_gcp(searcher, auth_config, creds, registry_url)
        elif provider == "artifactory":
            return CloudAuthHelper._configure_artifactory(searcher, creds)
        else:  # nexus
            return CloudAuthHelper._configure_nexus(searcher, creds)

    @staticmethod
    def _configure_aws(searcher: 'MavenArtifactSearcher', auth_config: AuthConfig,
                       creds: dict, registry_url: str) -> 'MavenArtifactSearcher':
        if not auth_config.aws_domain:
            raise ValueError("AWS auth requires aws_domain in authConfig")
        region = CloudAuthHelper._extract_region(registry_url, auth_config)
        repo_name = CloudAuthHelper._extract_repository_name(registry_url)
        logger.info(f"Configuring AWS CodeArtifact: domain={auth_config.aws_domain}, region={region}")
        return searcher.with_aws_code_artifact(
            access_key=creds["username"],
            secret_key=creds["password"],
            domain=auth_config.aws_domain,
            region_name=region,
            repository=repo_name
        )

    @staticmethod
    def _configure_gcp(searcher: 'MavenArtifactSearcher', auth_config: AuthConfig,
                       creds: dict, registry_url: str) -> 'MavenArtifactSearcher':
        if auth_config.auth_method != "service_account":
            raise ValueError(f"GCP auth_method '{auth_config.auth_method}' not supported")
        if not auth_config.gcp_reg_project:
            raise ValueError("GCP auth requires gcp_reg_project in authConfig")

        sa_data = creds["secret"]
        sa_json = json.dumps(sa_data) if isinstance(sa_data, dict) else sa_data
        region = CloudAuthHelper._extract_region(registry_url, auth_config)
        repo_name = CloudAuthHelper._extract_repository_name(registry_url)

        logger.info(f"Configuring GCP Artifact Registry: project={auth_config.gcp_reg_project}, region={region}")
        return searcher.with_gcp_artifact_registry(
            credential_params={"service_account_key": sa_json},
            project=auth_config.gcp_reg_project,
            region_name=region,
            repository=repo_name
        )

    @staticmethod
    def _configure_artifactory(searcher: 'MavenArtifactSearcher', creds: Optional[dict]) -> 'MavenArtifactSearcher':
        """Configure Artifactory authentication. Supports anonymous access if creds is None."""
        if creds is None:
            logger.info("Configuring Artifactory with anonymous access (no credentials)")
            return searcher.with_artifactory(username=None, password=None)
        
        return searcher.with_artifactory(
            username=creds.get("username", ""),
            password=creds.get("password", "")
        )

    @staticmethod
    def _configure_nexus(searcher: 'MavenArtifactSearcher', creds: Optional[dict]) -> 'MavenArtifactSearcher':
        """Configure Nexus authentication. Supports anonymous access if creds is None."""
        if creds is None:
            logger.info("Configuring Nexus with anonymous access (no credentials)")
            return searcher.with_nexus(username=None, password=None)
        
        return searcher.with_nexus(
            username=creds.get("username", ""),
            password=creds.get("password", "")
        )

    @staticmethod
    def get_gcp_access_token(service_account_json: str) -> Optional[str]:
        """Generate fresh GCP OAuth access token from service account JSON."""
        if not GCP_AUTH_AVAILABLE:
            return None
        try:
            sa_info = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
            credentials = service_account.Credentials.from_service_account_info(
                sa_info, scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            credentials.refresh(Request())
            return credentials.token
        except Exception as e:
            logger.error(f"Failed to generate GCP access token: {e}")
            return None

    @staticmethod
    def get_gcp_credentials_from_registry(registry: Registry, env_creds: Optional[Dict[str, dict]]) -> Optional[str]:
        """Extract GCP service account JSON from registry for token generation."""
        auth_config = CloudAuthHelper.resolve_auth_config(registry, "maven")
        if not auth_config or auth_config.provider != "gcp":
            return None
        try:
            creds = CloudAuthHelper.resolve_credentials(auth_config, env_creds)
            sa_data = creds.get("secret")
            return json.dumps(sa_data) if isinstance(sa_data, dict) else sa_data
        except Exception:
            return None
