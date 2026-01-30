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
    """Helper to connect to cloud registries using V2 authentication.
    
    This class knows how to authenticate with different types of artifact registries:
    - AWS CodeArtifact (uses AWS access keys)
    - GCP Artifact Registry (uses service account JSON)
    - Artifactory (uses username/password)
    - Nexus (uses username/password or anonymous access)
    
    It creates a MavenArtifactSearcher configured for each specific provider.
    """

    @staticmethod
    def resolve_auth_config(registry: Registry, artifact_type: str = "maven") -> Optional[AuthConfig]:
        """Find the authentication settings for this registry.
        
        Each registry can have multiple authConfig entries (for different artifact types).
        This looks up which authConfig to use based on what the maven_config references.
        
        Returns:
            AuthConfig object with provider and credentials info, or None if not configured
        """
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
        """Get the actual username/password or secrets from the credentials vault.
        
        The authConfig tells us the credentials ID to look up. This function finds
        those credentials in the environment's credential store and extracts them.
        
        Special handling:
        - Empty username/password = anonymous access (returns None)
        - Different credential types: usernamePassword, secret (for GCP service accounts)
        
        Returns:
            dict with username/password or secret, or None for anonymous access
        """
        cred_id = auth_config.credentials_id
        if not cred_id:
            logger.info("No credentialsId specified, using anonymous access")
            return None

        if not env_creds or cred_id not in env_creds:
            raise KeyError(f"Credential '{cred_id}' not found in env_creds")

        cred_entry = env_creds[cred_id]
        
        # Credentials can be structured as {"type": "usernamePassword", "data": {"username": "..."}}
        # or as a flat dict {"username": "...", "password": "..."}
        cred_type = cred_entry.get("type") if isinstance(cred_entry, dict) else None
        cred_data = cred_entry.get("data", cred_entry) if isinstance(cred_entry, dict) else cred_entry
        
        # For Nexus/Artifactory: empty username+password means anonymous/public access
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

        # Make sure we have the right credential format for each cloud provider
        # AWS needs username (access key ID) and password (secret access key)
        if auth_config.provider == "aws":
            if "username" not in creds or "password" not in creds:
                raise ValueError(f"AWS credentials must have 'username' and 'password'")
        # GCP needs a service account JSON file (stored as 'secret')
        elif auth_config.provider == "gcp" and auth_config.auth_method == "service_account":
            if "secret" not in creds:
                raise ValueError(f"GCP service_account credentials must have 'secret'")

        return creds

    @staticmethod
    def _extract_repository_name(url: str) -> str:
        """Extract the repository name from a registry URL.
        
        For CodeArtifact: https://domain-owner.d.codeartifact.region.amazonaws.com/maven/repo-name/
        Returns 'repo-name'
        
        For Artifact Registry: https://region-maven.pkg.dev/project/repo-name/
        Returns 'repo-name'
        """
        parts = [p for p in url.rstrip('/').split('/') if p]
        if parts:
            repo_name = parts[-1]
            logger.debug(f"Extracted repository name: {repo_name} from URL: {url}")
            return repo_name
        raise ValueError(f"Could not extract repository name from URL: {url}")

    @staticmethod
    def _extract_region(url: str, auth_config: AuthConfig) -> str:
        """Figure out which cloud region to use.
        
        Tries these sources in order:
        1. Explicit region in authConfig (if configured)
        2. Extract from URL pattern (e.g., 'us-west-2.amazonaws.com')
        3. Default to 'us-east-1' if can't determine
        """
        if auth_config.provider == "aws" and auth_config.aws_region:
            logger.debug(f"Using explicit AWS region: {auth_config.aws_region}")
            return auth_config.aws_region
        aws_match = re.search(r'\.([a-z0-9-]+)\.amazonaws\.com', url)
        if aws_match:
            region = aws_match.group(1)
            logger.debug(f"Extracted AWS region from URL: {region}")
            return region
        logger.debug("AWS region not found in URL, defaulting to us-east-1")
        return "us-east-1"

    @staticmethod
    def _detect_provider(url: str, auth_config: AuthConfig) -> Optional[str]:
        """Auto-detect provider from URL patterns for on-premise registries only.
        
        Auto-detection is ONLY for Nexus and Artifactory (on-premise registries).
        AWS and GCP (cloud registries) require explicit provider specification.
        
        Returns:
            Provider name or None if cannot be detected
        """
        # If provider is explicitly set, use it
        if auth_config.provider:
            logger.debug(f"Using explicit provider: {auth_config.provider}")
            return auth_config.provider
        
        url_lower = url.lower()
        
        # Auto-detect ONLY for on-premise registries (Nexus and Artifactory)
        # AWS and GCP must be explicitly specified
        
        # Artifactory patterns
        if "artifactory" in url_lower or "/artifactory/" in url_lower:
            logger.info(f"Auto-detected provider: artifactory from URL pattern")
            return "artifactory"
        
        # Nexus patterns
        if "nexus" in url_lower or "/nexus/" in url_lower or "/service/rest/" in url_lower:
            logger.info(f"Auto-detected provider: nexus from URL pattern")
            return "nexus"
        
        # AWS and GCP require explicit provider - no auto-detection
        logger.warning(f"Could not auto-detect provider from URL: {url}. AWS and GCP require explicit provider specification.")
        return None

    @staticmethod
    def create_maven_searcher(registry: Registry, env_creds: Optional[Dict[str, dict]]) -> 'MavenArtifactSearcher':
        """Create a searcher object that knows how to find artifacts in this registry.
        
        This is the main entry point for V2 artifact searching. It:
        1. Reads the registry configuration to determine the provider type
        2. Loads the appropriate credentials from the vault
        3. Creates and configures a MavenArtifactSearcher for that specific provider
        
        Returns:
            Configured MavenArtifactSearcher ready to search for and download artifacts
        """
        if MavenArtifactSearcher is None:
            raise ImportError("qubership_pipelines_common_library not available")

        auth_config = CloudAuthHelper.resolve_auth_config(registry, "maven")
        if not auth_config:
            raise ValueError("Could not resolve authConfig for maven artifacts")
        
        registry_url = registry.maven_config.repository_domain_name
        
        # Try to detect provider if not explicitly set
        # Auto-detection works for Nexus and Artifactory (on-premise registries)
        # AWS and GCP must be explicitly specified
        provider = CloudAuthHelper._detect_provider(registry_url, auth_config)
        if not provider:
            logger.error(f"V2 fallback: Could not determine provider for registry '{registry.name}'. Please specify provider in authConfig or use recognizable URL pattern (nexus/artifactory)")
            raise ValueError(f"Could not determine provider for registry '{registry.name}'")
        
        if provider not in ["aws", "gcp", "artifactory", "nexus"]:
            raise ValueError(f"Unsupported provider: {provider}")

        # Nexus URLs need special handling:
        # Download URLs use: http://nexus/repository/repo-name/...
        # Search API uses:   http://nexus/service/rest/v1/search/...
        # So we need to remove the /repository/ suffix before initializing the searcher
        if provider == "nexus" and registry_url.endswith("/repository/"):
            registry_url = registry_url[:-len("repository/")]
            logger.info(f"Nexus: adjusted registry URL to {registry_url} for search API")

        # Get the credentials (or None if anonymous access is allowed)
        creds = CloudAuthHelper.resolve_credentials(auth_config, env_creds)
        
        # Create the base searcher object - provider-specific config comes next
        searcher = MavenArtifactSearcher(registry_url, params={"timeout": DEFAULT_SEARCHER_TIMEOUT})

        # Check if anonymous access is allowed for this provider type
        # AWS and GCP APIs require authentication - they don't support anonymous access
        if provider in ["aws", "gcp"] and creds is None:
            raise ValueError(f"{provider.upper()} requires credentials - anonymous access not supported")

        if provider == "aws":
            return CloudAuthHelper._configure_aws(searcher, auth_config, creds, registry_url)
        elif provider == "gcp":
            return CloudAuthHelper._configure_gcp(searcher, auth_config, creds, registry_url)
        elif provider == "artifactory":
            return CloudAuthHelper._configure_artifactory(searcher, creds)
        else:  # nexus
            return CloudAuthHelper._configure_nexus(searcher, creds, registry)

    @staticmethod
    def _configure_aws(searcher: 'MavenArtifactSearcher', auth_config: AuthConfig,
                       creds: dict, registry_url: str) -> 'MavenArtifactSearcher':
        """Set up the searcher to work with AWS CodeArtifact.
        
        AWS needs:
        - Access key (stored as username)
        - Secret key (stored as password)
        - Domain name (from authConfig)
        - Region (from authConfig or URL)
        - Repository name (from URL)
        """
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
        """Set up the searcher to work with GCP Artifact Registry.
        
        GCP needs:
        - Service account JSON (stored as secret)
        - Project name (from authConfig or extracted from URL)
        - Region (from URL, like 'us-central1')
        - Repository name (from URL)
        """
        if auth_config.auth_method != "service_account":
            raise ValueError(f"GCP auth_method '{auth_config.auth_method}' not supported")
        
        # Extract project from authConfig or URL
        project = auth_config.gcp_reg_project
        if not project:
            # Extract from GCP URL pattern: https://<region>-maven.pkg.dev/<project>/<repo>/
            match = re.search(r'pkg\.dev/([^/]+)/', registry_url)
            if match:
                project = match.group(1)
                logger.info(f"Extracted GCP project from URL: {project}")
            else:
                raise ValueError("GCP auth requires gcp_reg_project in authConfig or valid GCP URL format (https://<region>-maven.pkg.dev/<project>/<repo>/)")

        sa_data = creds["secret"]
        sa_json = json.dumps(sa_data) if isinstance(sa_data, dict) else sa_data
        region = CloudAuthHelper._extract_region(registry_url, auth_config)
        repo_name = CloudAuthHelper._extract_repository_name(registry_url)

        logger.info(f"Configuring GCP Artifact Registry: project={project}, region={region}")
        return searcher.with_gcp_artifact_registry(
            credential_params={"service_account_key": sa_json},
            project=project,
            region_name=region,
            repository=repo_name
        )

    @staticmethod
    def _configure_artifactory(searcher: 'MavenArtifactSearcher', creds: Optional[dict]) -> 'MavenArtifactSearcher':
        """Set up the searcher to work with Artifactory.
        
        Artifactory is simpler - just username and password.
        Can work anonymously if the repository allows public access.
        """
        if creds is None:
            logger.info("Configuring Artifactory with anonymous access (no credentials)")
            return searcher.with_artifactory(username=None, password=None)
        
        return searcher.with_artifactory(
            username=creds.get("username", ""),
            password=creds.get("password", "")
        )

    @staticmethod
    def _configure_nexus(searcher: 'MavenArtifactSearcher', creds: Optional[dict], registry: Registry) -> 'MavenArtifactSearcher':
        """Set up the searcher to work with Nexus Repository Manager.
        
        Nexus is simple - just username and password, or anonymous if allowed.
        
        Important: The MavenArtifactSearcher library searches across ALL repositories
        in Nexus (we can't limit to a specific repository). This is a library limitation,
        not a bug in our code. Nexus will return results from any repository the user
        has access to.
        """
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
