from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, Field
from pydantic.alias_generators import to_camel


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
    docker_config: DockerConfig
    go_config: Optional[GoConfig] = None
    raw_config: Optional[RawConfig] = None
    npm_config: Optional[NpmConfig] = None
    helm_config: Optional[HelmConfig] = None
    helm_app_config: Optional[HelmAppConfig] = None


class Application(BaseSchema):
    name: str
    artifact_id: str
    group_id: str
    registry: Registry
    solution_descriptor: bool


class FileExtension(str, Enum):
    ZIP = 'zip'
    JSON = 'json'


class Credentials(BaseSchema):
    username: str
    password: str
