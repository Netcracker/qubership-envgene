import json
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Iterable, List

import py_serializable as serializable
from artifact_searcher.utils.models import Registry, RegistryV2, Application
from cyclonedx.model import BomRef
from cyclonedx.model.component import ComponentType, Component
from cyclonedx.model.license import License
from cyclonedx.schema.schema import SchemaVersion1Dot6, SchemaVersion1Dot0, SchemaVersion1Dot1, SchemaVersion1Dot2, \
    SchemaVersion1Dot3, SchemaVersion1Dot4, SchemaVersion1Dot5
from envgenehelper import logger
from pydantic import BaseModel, ConfigDict, field_validator, model_validator, Field
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="ignore"
    )


class SBOMOutput(BaseSchema):
    registries: Dict[str, Registry | RegistryV2]
    sboms: Dict[str, Any]


class ImageType(str, Enum):
    image = 'image'
    service = 'service'


class ArtifactType(str, Enum):
    ZIP = 'zip'
    SPAR = 'spar',
    JAR = 'jar'
    POM = 'pom'


class Artifact(BaseSchema):
    id: str
    type: ArtifactType | str
    classifier: Optional[str] = ""


class Service(BaseSchema):
    service_name: str
    image_type: ImageType
    docker_tag: str
    full_image_name: Optional[str] = ""
    docker_repository_name: Optional[str] = ""
    docker_registry: Optional[str] = ""
    image_name: Optional[str] = ""
    version: Optional[str] = ""
    git_branch: Optional[str] = ""
    promote_artifacts: Optional[str] = ""
    deploy_param: Optional[str] = ""
    qualifier: Optional[str] = ""
    docker_digest: Optional[str] = ""
    git_revision: Optional[str] = ""
    git_url: Optional[str] = ""

    # cyclone not supported bool for properties
    @field_validator('promote_artifacts', mode='before')
    def cast_to_str(cls, promote_artifacts):
        return str(promote_artifacts)

    @model_validator(mode='after')
    def extract_docker_registry(self):
        if self.full_image_name and not self.docker_registry and '/' in self.full_image_name:
            self.docker_registry = self.full_image_name.split('/')[0]
        return self

    def set_full_image_name(self, app: Application, mvn_repo_pointer: str):
        repos_map = {
            "snapshotUri": "targetSnapshot",
            "stagingUri": "targetStaging",
            "releaseUri": "targetRelease",
            "groupUri": "snapshotGroup"
        }
        if not self.full_image_name:
            if not app.registry.docker_config:
                logger.warning(
                    f"Docker config is not defined in registry '{app.registry.name}' for app '{app.name}' "
                    f"service '{self.service_name}'. Full image name will be incomplete.")
                docker_repo_value = ""
            else:
                docker_cfg = app.registry.docker_config.model_dump(by_alias=True)
                if mvn_repo_pointer == "repositoryName":
                    docker_repo_value = docker_cfg.get("groupUri") or ""
                else:
                    docker_repo_value = next(
                        (value for key, value in docker_cfg.items() if
                         'uri' in key.lower() and repos_map.get(key) == mvn_repo_pointer), None)
                if not docker_repo_value:
                    docker_repo_value = ""
                    logger.warning(
                        f"Docker repository wasn't found in registry '{app.registry.name}' for app '{app.name}' "
                        f"service '{self.service_name}' (mvn_repo_pointer='{mvn_repo_pointer}'). "
                        f"Full image name will be incomplete.")
            path_parts = [p for p in [docker_repo_value or '', self.docker_repository_name or '', self.image_name or '']
                          if p]
            self.full_image_name = f"{'/'.join(path_parts)}:{self.docker_tag}"
            self.docker_registry = docker_repo_value
        return self


# Configuration, Smartplug and Jobs enitities have the same structure, no info about mandatory
class Configuration(BaseSchema):
    name: str
    version: str
    git_branch: Optional[str] = ""
    type: Optional[str] = ""
    artifacts: Optional[list[Artifact]] = Field(default_factory=list)
    git_revision: Optional[str] = ""
    build_id_dtrust: Optional[str] = ""
    maven_repository: Optional[str] = ""
    git_url: Optional[str] = ""


class AppChart(BaseSchema):
    helm_chart_name: str
    helm_chart_version: str


class DeploymentDescriptor(BaseSchema):
    services: Optional[list[Service]] = Field(default_factory=list)
    configurations: Optional[list[Configuration]] = Field(default_factory=list)
    smartplug: Optional[list[Configuration]] = Field(default_factory=list)
    charts: Optional[list[AppChart]] = Field(default_factory=list)

    @classmethod
    def by_path_with_app(cls, path: Path, app: Application, mvn_repo_pointer):
        # factory method
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        dd = cls.model_validate(data)
        for service in dd.services:
            service.set_full_image_name(app, mvn_repo_pointer)
        return dd

    @classmethod
    def from_json_with_app(cls, data, app: Application, mvn_repo_pointer):
        # factory method
        dd = cls.model_validate(data)
        for service in dd.services:
            service.set_full_image_name(app, mvn_repo_pointer)
        return dd


class Attachment(BaseSchema):
    content_type: str
    encoding: str = 'base64'
    content: str


class Content(BaseSchema):
    attachment: Attachment


class Data(BaseSchema):
    name: str
    contents: Content
    type: str = 'configuration'


# TODO data dirty hack due to https://github.com/CycloneDX/cyclonedx-python-lib/issues/578

@serializable.serializable_class
class CustomComponent(Component):
    def __init__(
            self,
            name: str,
            type: ComponentType,
            mime_type: Optional[str] = None,
            data: Optional[List[Dict[str, Any]]] = None,
            bom_ref: str = None
    ):
        super().__init__(name=name, type=type, mime_type=mime_type, bom_ref=bom_ref)
        self._licenses = []
        self._data = data

    @property
    @serializable.view(SchemaVersion1Dot6)
    def data(self) -> List[Dict[str, Any]]:
        return self._data

    @data.setter
    def data(self, data: List[Dict[str, Any]]) -> None:
        self._data = data

    @property
    @serializable.view(SchemaVersion1Dot0)
    def licenses(self):
        return self._licenses

    @licenses.setter
    def licenses(self, licenses: Iterable[License]) -> None:
        self._licenses = licenses

    @property
    @serializable.view(SchemaVersion1Dot0)
    def modified(self) -> bool:
        return self._modified

    @modified.setter
    def modified(self, modified: bool) -> None:
        self._modified = modified

    @property
    @serializable.json_name('bom-ref')
    @serializable.type_mapping(BomRef)
    @serializable.view(SchemaVersion1Dot1)
    @serializable.view(SchemaVersion1Dot2)
    @serializable.view(SchemaVersion1Dot3)
    @serializable.view(SchemaVersion1Dot4)
    @serializable.view(SchemaVersion1Dot5)
    @serializable.view(SchemaVersion1Dot6)
    @serializable.xml_attribute()
    @serializable.xml_name('bom-ref')
    def bom_ref(self) -> BomRef:
        """
        An optional identifier which can be used to reference the component elsewhere in the BOM. Every bom-ref MUST be
        unique within the BOM.

        Returns:
            `BomRef`
        """
        return self._bom_ref


@serializable.serializable_enum
class MimeType(str, Enum):
    SOLUTION = 'application/vnd.qubership.solution'
    SOLUTION_DESCRIPTOR = 'application/vnd.qubership.solution-descriptor'
    DEPLOYMENT_DESCRIPTOR = 'application/vnd.qubership.deployment-descriptor'
    APPLICATION = 'application/vnd.qubership.application'
    SERVICE = 'application/vnd.qubership.service'
    IMAGE = 'application/vnd.docker.image'
    RESOURCE_PROFILE = 'application/vnd.qubership.resource-profile-baseline'
    ENVGENE_TEMPLATE = 'application/vnd.qubership.envgene.template'
    ZIP = 'application/zip'
    OSGI_BUNDLE = 'application/vnd.osgi.bundle'
    SMARTPLUG = 'application/vnd.qubership.configuration.smartplug'
    CDN = 'application/vnd.qubership.configuration.cdn'
    CONFIGURATION = 'application/vnd.qubership.configuration'
    JAR = 'application/java-archive'
    POM = 'application/xml'
    OCTET = 'application/octet-stream'
    APP_CHART = 'application/vnd.qubership.app.chart'


ARTIFACT_TYPE_TO_MIME = {
    ArtifactType.ZIP: MimeType.ZIP,
    ArtifactType.SPAR: MimeType.OSGI_BUNDLE,
    ArtifactType.JAR: MimeType.JAR,
    ArtifactType.POM: MimeType.POM
}


class EntityType(str, Enum):
    SERVICE = 'service'
    CONFIGURATION = 'configuration'


class Extensions(str, Enum):
    JSON = 'json'
    YAML = 'yaml'
    YML = 'yml'
    ZIP = 'zip'
