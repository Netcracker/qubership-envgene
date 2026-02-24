from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, Field, model_validator
from pydantic.alias_generators import to_camel
import requests

from artifact_searcher.utils.constants import DEFAULT_REQUEST_TIMEOUT


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="ignore"
    )


class MavenConfig(BaseSchema):
    target_snapshot: str
    target_staging: str
    target_release: str
    full_repository_url: Optional[str] = ""
    repository_domain_name: str = Field(json_schema_extra={"error_message": "Application registry does not define URL"})
    snapshot_group: Optional[str] = ""
    release_group: Optional[str] = ""

    @field_validator('full_repository_url')
    def check_full_repository_url(cls, full_repository_url):
        if full_repository_url:
            raise ValueError(f"Full URL {full_repository_url} is not supported, please use domain URL")
        return full_repository_url

    @field_validator('repository_domain_name')
    def ensure_trailing_slash(cls, value):
        return value.rstrip("/") + "/"


class DockerConfig(BaseSchema):
    auth_config: str
    snapshot_uri: str
    staging_uri: str
    release_uri: str
    group_uri: str
    snapshot_repo_name: str
    staging_repo_name: str
    release_repo_name: str
    group_name: str


class GoConfig(BaseSchema):
    auth_config: str
    repository_domain_name: str
    go_target_snapshot: str
    go_target_release: str
    go_proxy_repository: str


class RawConfig(BaseSchema):
    auth_config: str
    repository_domain_name: str
    raw_target_snapshot: str
    raw_target_release: str
    raw_target_staging: str
    raw_target_proxy: str


class NpmConfig(BaseSchema):
    auth_config: str
    repository_domain_name: str
    npm_target_snapshot: str
    npm_target_release: str


class HelmConfig(BaseSchema):
    auth_config: str
    repository_domain_name: str
    helm_target_staging: str
    helm_target_release: str


class HelmAppConfig(BaseSchema):
    auth_config: str
    repository_domain_name: str
    helm_staging_repo_name: str
    helm_release_repo_name: str
    helm_group_repo_name: str
    helm_dev_repo_name: str


REGDEF_V2_VERSION = "2.0"


class Provider(str, Enum):
    NEXUS = "nexus"
    ARTIFACTORY = "artifactory"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class GcpOIDC(BaseSchema):
    url: str = Field(alias="URL")
    custom_params: Optional[list[dict[str, str]]] = None


class AuthConfig(BaseSchema):
    credentials_id: Optional[str] = None
    auth_type: Optional[str] = None
    provider: Provider
    auth_method: str
    aws_region: Optional[str] = None
    aws_domain: Optional[str] = None
    aws_role_arn: Optional[str] = Field(default=None, alias="awsRoleARN")
    aws_role_session_prefix: Optional[str] = None
    gcp_oidc: Optional[GcpOIDC] = Field(default=None, alias="gcpOIDC")
    gcp_reg_project: Optional[str] = None
    gcp_reg_pool_id: Optional[str] = None
    gcp_reg_provider_id: Optional[str] = None
    gcp_reg_sa_email: Optional[str] = Field(default=None, alias="gcpRegSAEmail")
    gcp_region: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_acr_resource: Optional[str] = Field(default=None, alias="azureACRResource")
    azure_acr_name: Optional[str] = Field(default=None, alias="azureACRName")
    azure_artifacts_resource: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_conditional_fields(self):
        if self.auth_method != "anonymous" and not self.credentials_id:
            raise ValueError("credentialsId is required when authMethod is not 'anonymous'")
        
        if self.provider == Provider.AWS and self.auth_method == "assume_role" and not self.aws_role_arn:
            raise ValueError("awsRoleARN is required when provider is 'aws' and authMethod is 'assume_role'")
        
        if self.provider == Provider.GCP and self.auth_method == "federation" and not self.gcp_oidc:
            raise ValueError("gcpOIDC is required when provider is 'gcp' and authMethod is 'federation'")
        
        if self.provider == Provider.NEXUS and self.auth_method not in ["user_pass", "anonymous"]:
            raise ValueError(f"Nexus provider requires authMethod to be 'user_pass' or 'anonymous', got '{self.auth_method}'")
        
        if self.provider == Provider.ARTIFACTORY and self.auth_method not in ["user_pass", "anonymous"]:
            raise ValueError(f"Artifactory provider requires authMethod to be 'user_pass' or 'anonymous', got '{self.auth_method}'")
        
        if self.provider == Provider.AWS and self.auth_method not in ["secret", "assume_role", "anonymous"]:
            raise ValueError(f"AWS provider requires authMethod to be 'secret', 'assume_role', or 'anonymous', got '{self.auth_method}'")
        
        if self.provider == Provider.GCP and self.auth_method not in ["federation", "service_account", "anonymous"]:
            raise ValueError(f"GCP provider requires authMethod to be 'federation', 'service_account', or 'anonymous', got '{self.auth_method}'")
        
        if self.provider == Provider.AZURE and self.auth_method not in ["oauth2", "anonymous"]:
            raise ValueError(f"Azure provider requires authMethod to be 'oauth2' or 'anonymous', got '{self.auth_method}'")
        
        return self


class MavenConfigV2(BaseSchema):
    auth_config: str
    repository_domain_name: str
    target_snapshot: Optional[str] = ""
    target_staging: Optional[str] = ""
    target_release: Optional[str] = ""
    snapshot_group: Optional[str] = ""
    release_group: Optional[str] = ""

    @field_validator('repository_domain_name')
    def ensure_trailing_slash(cls, value):
        return value.rstrip("/") + "/"


class BaseRegistry(BaseSchema):
    name: str
    maven_config: MavenConfig | MavenConfigV2
    
    def resolve_auth_headers(self, env_creds: Optional[dict] = None) -> Optional[dict]:
        raise NotImplementedError("Subclasses must implement resolve_auth_headers()")


class RegistryV2(BaseRegistry):
    version: str = REGDEF_V2_VERSION
    auth_config: dict[str, AuthConfig] = {}
    maven_config: MavenConfigV2
    docker_config: Optional[DockerConfig] = None
    go_config: Optional[GoConfig] = None
    raw_config: Optional[RawConfig] = None
    npm_config: Optional[NpmConfig] = None
    helm_config: Optional[HelmConfig] = None
    helm_app_config: Optional[HelmAppConfig] = None
    
    def resolve_auth_headers(self, env_creds: Optional[dict] = None) -> Optional[dict]:
        from artifact_searcher.auth_resolver import resolve_v2_auth_headers
        return resolve_v2_auth_headers(self, env_creds or {})


class ArtifactInfo(BaseSchema):
    url: Optional[str]
    app_name: Optional[str] = ""
    app_version: Optional[str] = ""
    repo: Optional[str] = ""
    path: Optional[str] = ""
    local_path: Optional[str] = ""
    name: Optional[str] = ""


class Registry(BaseRegistry):
    credentials_id: Optional[str] = ""
    maven_config: MavenConfig
    docker_config: Optional[DockerConfig] = None
    go_config: Optional[GoConfig] = None
    raw_config: Optional[RawConfig] = None
    npm_config: Optional[NpmConfig] = None
    helm_config: Optional[HelmConfig] = None
    helm_app_config: Optional[HelmAppConfig] = None
    
    def resolve_auth_headers(self, env_creds: Optional[dict] = None) -> Optional[dict]:
        return None


def parse_registry(data: dict) -> Registry | RegistryV2:
    if data.get("version") == REGDEF_V2_VERSION or "authConfig" in data:
        return RegistryV2.model_validate(data)
    return Registry.model_validate(data)


# artifact definition
class Application(BaseSchema):
    name: str
    artifact_id: str
    group_id: str
    registry: Registry | RegistryV2
    solution_descriptor: bool = False

    @field_validator('registry', mode='before')
    @classmethod
    def parse_registry_field(cls, v):
        if isinstance(v, dict):
            return parse_registry(v)
        return v


class FileExtension(str, Enum):
    ZIP = 'zip'
    JSON = 'json'


class Credentials(BaseSchema):
    username: str
    password: str
