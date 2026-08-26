import os
import os.path
import logging
import requests
import logging
import re
import copy

from .types import (
    RegistryInfo,
    RegistryType,
    AuthGCPFederation,
    AuthGCPServiceAccount,
    AuthManageIdentity,
    AuthAzureOAuth2,
    AuthSTSAssumeRole,
    AuthSTSSecret,
    AuthUserPassword,
    AuthRegistry
)

from qubership_pipelines_common_library.v2.artifacts_finder.model.artifact_provider import ArtifactProvider
from qubership_pipelines_common_library.v2.artifacts_finder.model.artifact import Artifact
from qubership_pipelines_common_library.v2.artifacts_finder.utils.artifact_finder_utils import ArtifactProviderFactory
from qubership_pipelines_common_library.v2.artifacts_finder.artifact_finder import ArtifactFinder

shared_session = requests.Session()

class ArtifactoryUtils:

    AWS_DOMAIN_NAME_MATCH = r"https:\/\/([a-zA-Z0-9_-]+)-[a-zA-Z0-9]+\.d\.codeartifact\.[a-z0-9-]+\.amazonaws\.com"
    AWS_REGION_NAME_MATCH = r"codeartifact\.([a-z0-9-]+)\.amazonaws\.com"
    AWS_REGION_PATTERN = r"^[a-z]{2}-[a-z]+-\d+$"

    @staticmethod
    def detect_auth_method(
        type_reg: RegistryType,
        url: str,
        authmethod: str,
        reg_key: str,
        reg_secret: str,
        reg_region: str = "",
        reg_domain: str = "",
        reg_project: str = "",
        reg_repo: str = "",
        reg_session_prefix: str = "",
        reg_role_arn: str = "",
        pub_reg_oidc_url: str = "",
        pub_reg_oidc_provider: str = "",
        pub_reg_oidc_method: str = "secret",
        pub_reg_provider_id: str = "",
        pub_reg_pool_id: str = "",
        pub_reg_sa_email: str = "",
        pub_reg_oidc_client_id: str = "",
        pub_reg_oidc_client_secret: str = "",
        pub_reg_oidc_custom_params: str = "",
    ) -> AuthRegistry:
        if type_reg == RegistryType.AWS:
            # https://docs.aws.amazon.com/codeartifact/latest/ug/maven-mvn.html
            # https://<domain_name>-<domain_owner_id>.d.codeartifact.<region>.amazonaws.com/<format>/<domain_name>/<repo_name>/
            try:
                if reg_domain == "":
                    reg_domain = re.search(ArtifactoryUtils.AWS_DOMAIN_NAME_MATCH, url).group(1)
                if reg_region == "":
                    reg_region = re.search(ArtifactoryUtils.AWS_REGION_NAME_MATCH, url).group(1)
                    # Validate that the extracted region follows AWS region naming pattern
                    # AWS regions follow pattern: <continent>-<direction>-<number> or <continent>-<country>-<number>
                    # Examples: us-east-1, eu-west-1, ap-southeast-2, etc.

                    if not re.match(ArtifactoryUtils.AWS_REGION_PATTERN, reg_region):
                        logging.warning(f"Invalid AWS region format '{reg_region}'. Expected format: <continent>-<direction>-<number> (e.g., us-east-1)")
                        return None
            except Exception:
                logging.warning("It is not possible to retrieve the region and domain from the AWS URL.")
                return None

        if (type_reg == RegistryType.GCP or
            type_reg == RegistryType.AWS or 
            type_reg == RegistryType.AZURE) and authmethod:
            if authmethod == "assume_role":
                return AuthSTSAssumeRole(
                    access_key=reg_key,
                    secret_key=reg_secret,
                    domain=reg_domain,
                    region_name=reg_region,
                    repository=reg_repo,
                    auth_type=authmethod,
                    session_prefix=reg_session_prefix,
                    role_arn=reg_role_arn,
                )
            elif authmethod == "secret":
                return AuthSTSSecret(
                    access_key=reg_key,
                    secret_key=reg_secret,
                    domain=reg_domain,
                    region_name=reg_region,
                    repository=reg_repo,
                )
            elif authmethod == "federation":
                if pub_reg_oidc_method == "secret":
                    effective_client_id = reg_key  # PUB_REG_KEY
                    effective_client_secret = reg_secret  # PUB_REG_SECRET
                else:
                    effective_client_id = pub_reg_oidc_client_id
                    effective_client_secret = pub_reg_oidc_client_secret
                
                
                return AuthGCPFederation(
                    project=reg_project,
                    region_name=reg_region,
                    repository=reg_repo,
                    auth_type=authmethod,
                    oidc_url=pub_reg_oidc_url,
                    oidc_method=pub_reg_oidc_method,
                    provider_id=pub_reg_provider_id,
                    pool_id=pub_reg_pool_id,
                    sa_email=pub_reg_sa_email,
                    oidc_client_id=effective_client_id or "",
                    oidc_client_secret=effective_client_secret or "",
                    oidc_custom_params=pub_reg_oidc_custom_params,
                )
            elif authmethod == "service_account":  
                reg_secret = _clean_and_validate_json_string(reg_secret)
                return AuthGCPServiceAccount(
                    service_account_key_content=reg_secret,
                    project=reg_project,
                    region_name=reg_region,
                    repository=reg_repo,
                )
            elif authmethod == "managed-identity":
                return AuthManageIdentity(
                    client_id=reg_key,
                    client_secret=reg_secret,
                )
            elif authmethod == "oauth2-client":
                return AuthAzureOAuth2(
                    client_id=reg_key,
                    client_secret=reg_secret,
                )
        elif authmethod == "basic_auth":
            return AuthUserPassword(
                registry_url=url,
                username=reg_key,
                password=reg_secret
            )

        return None

    @staticmethod
    def detect_artifact_provider(registry_info: RegistryInfo) -> ArtifactProvider:
        __auth_config = dict()
        if registry_info.auth_config is not None:
            __auth_config = dict(registry_info.auth_config)

        provider = None 

        try:
            if registry_info.type == RegistryType.ARTIFACTORY:
                provider = ArtifactProviderFactory.create_artifactory_provider(__auth_config, dict())
            elif registry_info.type == RegistryType.NEXUS:
                provider = ArtifactProviderFactory.create_nexus_provider(__auth_config, dict())
            elif registry_info.type == RegistryType.AWS:
                provider = ArtifactProviderFactory.create_aws_provider(__auth_config, dict())
            elif registry_info.type == RegistryType.GCP:
                provider = ArtifactProviderFactory.create_gcp_provider(__auth_config, dict())
            return provider
        except Exception as e:
            raise Exception(f"Failure with detect_registry is : {e}")

    @staticmethod
    def download_file_from_artifactory(path: str, url: str, registry_info: RegistryInfo):
        """
        Function to download file

        Parameters:
        path: destination for file without filename (folder, example: ./folder_with_zip)
        url: url to file
        """
        filename = url.replace("%2F", "/").split('/')[-1]
        try:
            provider = ArtifactoryUtils.detect_artifact_provider(registry_info)
            finder = ArtifactFinder(artifact_provider=provider)
            finder.download_artifact(url, f"{path}/{filename}")
        except RuntimeError:
            raise Exception("Error with download file: {}".format(url))

        return f"{path}/{filename}"

    @staticmethod
    def search_artifacts_on_registry(app_name: str, app_version: str, app_info: dict,
                                    artifact_extension: str, registry_info: RegistryInfo): 
        artifact = Artifact(
            group_id=app_info.group_id,
            artifact_id=app_info.artifact_id,
            version=app_version,
            extension=artifact_extension
        )
        logging.debug(f'Application info: {app_info}')

        for k, repo in {
            "targetRelease": registry_info.maven_config.targetRelease,
            "targetSnapshot": registry_info.maven_config.targetSnapshot,
            "targetStaging": registry_info.maven_config.targetStaging,
        }.items():
            if registry_info.auth_config is not None and "repository" in registry_info.auth_config:
                registry_info.auth_config.repository = repo

            provider = ArtifactoryUtils.detect_artifact_provider(registry_info)
            finder = ArtifactFinder(artifact_provider=provider)

            try:
                urls = finder.find_artifact_urls(artifact=artifact)
            except Exception as e:
                if k == "targetRelease":
                    release_artifact = copy.copy(artifact)
                    release_artifact.version = app_version + "-RELEASE"
                else:
                    raise Exception(f"Failed during search_artifacts_on_registry due to Error: {e}")

                try:
                    urls = finder.find_artifact_urls(artifact=artifact)
                except Exception as e:
                    raise Exception(f"Failed during search_artifacts_on_registry due to Error: {e}")

            # need to verify which artifact has valid expectation
            rurl = None
            for url in urls:
                partsurl = url.split("/")
                if f"{app_version}.{artifact_extension}" in partsurl[-1] or f"{app_version}-RELEASE.{artifact_extension}" in partsurl[-1]:
                    rurl = url
                    break

            if rurl is not None:
                registry_type = k 
                for reg, repo in {
                    "targetRelease": registry_info.maven_config.targetRelease,
                    "targetSnapshot": registry_info.maven_config.targetSnapshot,
                    "targetStaging": registry_info.maven_config.targetStaging,
                }.items():
                    if len(repo) > 0 and repo in rurl:
                        registry_type = reg
                        break

                return rurl, rurl.replace("%2F", "/").split('/')[-1], {"release_status": registry_type == "targetRelease"}, registry_type

        raise ValueError(f"Unable to locate artifact `{app_name}:{app_version}` in registry: {registry_info.url}; Type: {registry_info.type}; MavenConfig: {registry_info.maven_config}.")


def _clean_and_validate_json_string(json_string: str) -> str:
    """
    Clean and validate a JSON string, handling common formatting issues.
    
    This function attempts to parse and clean JSON strings that may contain:
    - Single quotes instead of double quotes
    - Escaped quotes that need to be unescaped
    - Escaped newlines in private_key fields that need to be converted to actual newlines
    
    Args:
        json_string: The JSON string to clean and validate
        
    Returns:
        str: A clean, valid JSON string
        
    Raises:
        ValueError: If the JSON string cannot be cleaned and validated
    """
    import json
    
    try:
        json_data = json.loads(json_string)
        # Handle \\n to \n conversion in private_key field
        if 'private_key' in json_data:
            json_data['private_key'] = json_data['private_key'].replace('\\n', '\n')
        cleaned_json = json.dumps(json_data, ensure_ascii=False)
        return cleaned_json
    except json.JSONDecodeError:
        pass
    
    # If parsing fails, try cleaning single quotes first
    try:
        cleaned_secret = json_string.replace("'", '"')
        json_data = json.loads(cleaned_secret)
        if 'private_key' in json_data:
            json_data['private_key'] = json_data['private_key'].replace('\\n', '\n')
        cleaned_json = json.dumps(json_data, ensure_ascii=False)
        return cleaned_json
    except json.JSONDecodeError:
        pass
    
    # If still fails, try more aggressive cleaning
    try:
        cleaned_secret = json_string.replace("'", '"')
        cleaned_secret = cleaned_secret.replace('\\"', '"')
        json_data = json.loads(cleaned_secret)
        if 'private_key' in json_data:
            json_data['private_key'] = json_data['private_key'].replace('\\n', '\n')
        cleaned_json = json.dumps(json_data, ensure_ascii=False)
        return cleaned_json
    except json.JSONDecodeError as e:
        raise ValueError(f"Unable to clean and validate JSON string: {e}")
