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

    is_nexus: bool = False

    @field_validator('full_repository_url')
    def check_full_repository_url(cls, full_repository_url):
        if full_repository_url:
            raise ValueError(f"Full URL {full_repository_url} is not supported, please use domain URL")
        return full_repository_url

    @field_validator('repository_domain_name')
    def ensure_trailing_slash(cls, value):
        return value.rstrip("/") + "/"

    @model_validator(mode="after")
    def detect_nexus(self):
        if not self.repository_domain_name.endswith("/repository/"):
            return self
        base = self.repository_domain_name[: -len("repository/")]
        status_url = f"{base}service/rest/v1/status"
        try:
            resp = requests.get(status_url, timeout=DEFAULT_REQUEST_TIMEOUT)
            self.is_nexus = resp.status_code == 200
        except Exception:
            self.is_nexus = False

        return self


class DockerConfig(BaseSchema):
    snapshot_uri: Optional[str] = ""
    staging_uri: Optional[str] = ""
    release_uri: Optional[str] = ""
    group_uri: Optional[str] = ""
    snapshot_repo_name: Optional[str] = ""
    staging_repo_name: Optional[str] = ""
    release_repo_name: Optional[str] = ""
    group_name: Optional[str] = ""


class GoConfig(BaseSchema):
    go_target_snapshot: Optional[str] = ""
    go_target_release: Optional[str] = ""
    go_proxy_repository: Optional[str] = ""


class RawConfig(BaseSchema):
    raw_target_snapshot: Optional[str] = ""
    raw_target_release: Optional[str] = ""
    raw_target_staging: Optional[str] = ""
    raw_target_proxy: Optional[str] = ""


class NpmConfig(BaseSchema):
    npm_target_snapshot: Optional[str] = ""
    npm_target_release: Optional[str] = ""


class HelmConfig(BaseSchema):
    helm_target_staging: Optional[str] = ""
    helm_target_release: Optional[str] = ""


class HelmAppConfig(BaseSchema):
    helm_staging_repo_name: Optional[str] = ""
    helm_release_repo_name: Optional[str] = ""
    helm_group_repo_name: Optional[str] = ""
    helm_dev_repo_name: Optional[str] = ""


class ArtifactInfo(BaseSchema):
    url: Optional[str]
    app_name: Optional[str] = ""
    app_version: Optional[str] = ""
    repo: Optional[str] = ""
    path: Optional[str] = ""
    local_path: Optional[str] = ""
    name: Optional[str] = ""


class Registry(BaseSchema):
    credentials_id: Optional[str] = ""
    name: str
    maven_config: MavenConfig
    docker_config: Optional[DockerConfig] = None
    go_config: Optional[GoConfig] = None
    raw_config: Optional[RawConfig] = None
    npm_config: Optional[NpmConfig] = None
    helm_config: Optional[HelmConfig] = None
    helm_app_config: Optional[HelmAppConfig] = None


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


class DockerConfigV2(BaseSchema):
    auth_config: str
    snapshot_uri: str
    staging_uri: str
    release_uri: str
    group_uri: str
    snapshot_repo_name: str
    staging_repo_name: str
    release_repo_name: str
    group_name: str


class GoConfigV2(BaseSchema):
    auth_config: str
    repository_domain_name: str
    go_target_snapshot: str
    go_target_release: str
    go_proxy_repository: str


class RawConfigV2(BaseSchema):
    auth_config: str
    repository_domain_name: str
    raw_target_snapshot: str
    raw_target_release: str
    raw_target_staging: str
    raw_target_proxy: str


class NpmConfigV2(BaseSchema):
    auth_config: str
    repository_domain_name: str
    npm_target_snapshot: str
    npm_target_release: str


class HelmConfigV2(BaseSchema):
    auth_config: str
    repository_domain_name: str
    helm_target_staging: str
    helm_target_release: str


class HelmAppConfigV2(BaseSchema):
    auth_config: str
    repository_domain_name: str
    helm_staging_repo_name: str
    helm_release_repo_name: str
    helm_group_repo_name: str
    helm_dev_repo_name: str


class RegistryV2(BaseSchema):
    name: str
    version: str = REGDEF_V2_VERSION
    auth_config: dict[str, AuthConfig] = {}
    maven_config: MavenConfigV2
    docker_config: Optional[DockerConfigV2] = None
    go_config: Optional[GoConfigV2] = None
    raw_config: Optional[RawConfigV2] = None
    npm_config: Optional[NpmConfigV2] = None
    helm_config: Optional[HelmConfigV2] = None
    helm_app_config: Optional[HelmAppConfigV2] = None
    
    def resolve_auth_headers(self, env_creds: Optional[dict] = None) -> Optional[dict]:
        from artifact_searcher.auth_resolver import resolve_v2_auth_headers
        return resolve_v2_auth_headers(self, env_creds or {})


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
