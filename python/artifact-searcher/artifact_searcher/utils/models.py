from enum import Enum
from typing import Optional

import jsonschema
from envgenehelper import get_regdef_v2_schema
from pydantic import BaseModel, ConfigDict, field_validator, Field
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

    @staticmethod
    def is_nexus(repository_domain_name: str) -> bool:
        if not repository_domain_name.endswith("/repository/"):
            return False

        base = repository_domain_name[: -len("repository/")]
        status_url = f"{base}service/rest/v1/status"

        try:
            resp = requests.get(status_url, timeout=DEFAULT_REQUEST_TIMEOUT)
            return resp.status_code == 200
        except Exception:
            return False

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

    def resolve_auth(self, env_creds: Optional[dict] = None) -> Optional[dict]:
        """Returns auth headers dict for V1 registries (basic auth).
        Returns None if no credentials configured."""
        if not self.credentials_id or not env_creds:
            return None
        cred_data = env_creds.get(self.credentials_id, {}).get("data", {})
        username = cred_data.get("username")
        password = cred_data.get("password")
        if username and password:
            import base64
            token = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {token}"}
        return None


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
    
    def resolve_auth(self, env_creds: Optional[dict] = None) -> Optional[dict]:
        """Returns auth headers dict for V2 registries (unified API with V1).
        Returns None if anonymous or no credentials configured."""
        from artifact_searcher.auth_resolver import resolve_v2_auth_headers
        return resolve_v2_auth_headers(self, env_creds or {})


_REGDEF_V2_SCHEMA = get_regdef_v2_schema()


def parse_registry(data: dict) -> Registry | RegistryV2:
    if data.get("version") == REGDEF_V2_VERSION or "authConfig" in data:
        jsonschema.validate(instance=data, schema=_REGDEF_V2_SCHEMA)
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
