from enum import Enum
from typing import Any, ClassVar, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, RootModel, ValidationInfo, field_validator, model_validator

from envgene_shared.utils.yaml_utils import validate_yaml_by_scheme_or_fail


class CaseInsensitiveEnum(str, Enum):

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.upper()

            for member in cls:
                if member.value == value:
                    return member

        return None


class TemplateVersionUpdateMode(CaseInsensitiveEnum):
    PERSISTENT = "PERSISTENT"
    TEMPORARY = "TEMPORARY"


class SbomRetentionConfig(BaseModel):
    enabled: bool = Field(default=False)
    keep_versions_per_app: Optional[int] = Field(default=None, ge=0)


class OperationType(CaseInsensitiveEnum):
    DEPLOY = "DEPLOY"
    CLEAN = "CLEAN"
    BGD = "BGD"

    @classmethod
    def _missing_(cls, value):
        if not value:
            return cls.DEPLOY

        return super()._missing_(value)


class BgdOperation(CaseInsensitiveEnum):
    WARMUP = "WARMUP"
    COMMIT = "COMMIT"
    PROMOTE = "PROMOTE"
    ROLLBACK = "ROLLBACK"
    INIT_DOMAIN = "INIT-DOMAIN"


class DeltaDeployType(CaseInsensitiveEnum):
    NONE = "NONE"
    DIFF_AND_HEAL = "DIFF_AND_HEAL"
    DIFF = "DIFF"

class PipelineType(CaseInsensitiveEnum):
    GITLAB_DEPLOY = "GITLAB_DEPLOY"


class SaveArtifactsStrategy(CaseInsensitiveEnum):
    ALWAYS = "ALWAYS"
    NEVER = "NEVER"


class ExternalCredentialProvisioning(CaseInsensitiveEnum):
    APPLY = "APPLY"
    SKIP = "SKIP"


class SecretStore(BaseModel):
    type: Literal["vault", "openbao", "gcp", "aws", "azure"]
    projectId: Optional[str] = None
    mountPath: Optional[str] = None
    vaultName: Optional[str] = None
    region: Optional[str] = None

    
class PropertyMapping(BaseModel):
    name: str

class ExternalCredential(BaseModel):
    type: Literal["external"]
    secretStore: Optional[str] = None
    remoteRefPath: str
    create: bool = False
    properties: list[PropertyMapping] = Field(default_factory=list)

    @field_validator("secretStore")
    @classmethod
    def default_secret_store(cls, v: Optional[str]) -> str:
        if v is None:
            return "default_store"

        cleaned = v.strip()
        return cleaned if cleaned else "default_store"


class SchemaValidatedModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True, arbitrary_types_allowed=True)
    SCHEMA_NAME: ClassVar[str]

    @model_validator(mode="before")
    @classmethod
    def _validate_by_json_schema(cls, data: Any, info: ValidationInfo) -> Any:
        if isinstance(data, dict) and not (info.context and info.context.get("schema_validated")):
            validate_yaml_by_scheme_or_fail(input_yaml_content=data, schema_name=cls.SCHEMA_NAME)
        return data

    def validate_schema(self) -> None:
        if hasattr(self, "SCHEMA_NAME") and self.SCHEMA_NAME:
            validate_yaml_by_scheme_or_fail(
                input_yaml_content=self.model_dump(exclude_unset=True, by_alias=True),
                schema_name=self.SCHEMA_NAME,
            )


class ProfileOverrideModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: Optional[str] = None
    baseline: Optional[str] = None


class ApplicationModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "application.schema.json"

    name: str
    deployParameters: dict[str, Any] = Field(default_factory=dict)
    technicalConfigurationParameters: dict[str, Any] = Field(default_factory=dict)


class NamespaceModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "namespace.schema.json"

    name: str
    credentialsId: Optional[str] = None
    isServerSideMerge: bool
    labels: list[str] = Field(default_factory=list)
    cleanInstallApprovalRequired: bool
    mergeDeployParametersAndE2EParameters: bool
    profile: Optional[ProfileOverrideModel] = None
    deployParameters: dict[str, Any] = Field(default_factory=dict)
    e2eParameters: dict[str, Any] = Field(default_factory=dict)
    technicalConfigurationParameters: dict[str, Any] = Field(default_factory=dict)
    deployParameterSets: list[str] = Field(default_factory=list)
    e2eParameterSets: list[str] = Field(default_factory=list)
    technicalConfigurationParameterSets: list[str] = Field(default_factory=list)
    version: Optional[Union[int, float]] = None


class MaasConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    credentialsId: Optional[str] = None
    maasUrl: Optional[str] = None
    maasInternalAddress: Optional[str] = None
    enable: Optional[bool] = None


class VaultConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    credentialsId: Optional[str] = None
    url: Optional[str] = None
    enable: Optional[bool] = None


class DbaasConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    credentialsId: Optional[str] = None
    apiUrl: Optional[str] = None
    aggregatorUrl: Optional[str] = None
    enable: Optional[bool] = None


class ConsulConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    tokenSecret: Optional[str] = None
    publicUrl: Optional[str] = None
    internalUrl: Optional[str] = None
    enabled: Optional[bool] = None


class CloudModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "cloud.schema.json"

    name: str
    apiUrl: str
    apiPort: Union[int, str]
    privateUrl: Optional[str] = None
    publicUrl: Optional[str] = None
    dashboardUrl: str
    labels: list[str]
    defaultCredentialsId: str
    protocol: str
    dbMode: Optional[str] = None
    databases: list[dict[str, Any]] = Field(default_factory=list)
    mergeDeployParametersAndE2EParameters: Optional[bool] = None
    profile: Optional[ProfileOverrideModel] = None
    deployParameters: dict[str, Any]
    e2eParameters: dict[str, Any]
    technicalConfigurationParameters: dict[str, Any]
    deployParameterSets: list[str] = Field(default_factory=list)
    e2eParameterSets: list[str] = Field(default_factory=list)
    technicalConfigurationParameterSets: list[str] = Field(default_factory=list)
    maasConfig: MaasConfigModel
    vaultConfig: VaultConfigModel
    dbaasConfigs: list[DbaasConfigModel] = Field(default_factory=list)
    consulConfig: ConsulConfigModel
    version: Optional[Union[int, float]] = None


class GlobalE2EParametersModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    pipelineDefaultRecipients: Optional[str] = None
    recipientsStrategy: Optional[str] = None
    mergeTenantsAndE2EParameters: Optional[bool] = None
    environmentParameters: dict[str, Any] = Field(default_factory=dict)


class TenantModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "tenant.schema.json"

    name: str
    registryName: str
    description: Optional[str] = None
    owners: Optional[str] = None
    defaultBranch: Optional[str] = None
    gitRepository: Optional[str] = None
    credential: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    deployParameters: dict[str, Any] = Field(default_factory=dict)
    globalE2EParameters: Optional[GlobalE2EParametersModel] = None


class ServiceParameterModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    value: Union[str, int, bool]


class ResourceProfileServiceModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    parameters: list[ServiceParameterModel]


class ResourceProfileApplicationModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    version: Optional[Union[str, int, float]] = None
    sd: Optional[str] = None
    services: list[ResourceProfileServiceModel]


class ResourceProfileModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "resource-profile.schema.json"

    name: Optional[str] = None
    version: Optional[Union[str, int, float]] = None
    baseline: Optional[str] = None
    description: Optional[str] = None
    applications: list[ResourceProfileApplicationModel] = Field(default_factory=list)


class CompositeComponentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: Literal["namespace", "bgdomain"]


class CompositeStructureModel(SchemaValidatedModel):
    model_config = ConfigDict(extra="forbid")
    SCHEMA_NAME: ClassVar[str] = "composite-structure.schema.json"

    name: str
    baseline: CompositeComponentModel
    satellites: list[CompositeComponentModel] = Field(default_factory=list)


class ParamsetApplicationModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    appName: str
    parameters: dict[str, Any]


class ParamsetModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "paramset.schema.json"

    name: str
    version: Optional[Union[int, float]] = None
    parameters: Optional[dict[str, Any]] = None
    applications: Optional[list[ParamsetApplicationModel]] = None


class AppDefMetadataModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    helmReleaseNameStrategy: Optional[str] = None


class AppDefModel(SchemaValidatedModel):
    model_config = ConfigDict(extra="forbid")
    SCHEMA_NAME: ClassVar[str] = "appdef.schema.json"

    name: str
    registryName: str
    artifactId: str
    groupId: str
    supportParallelDeploy: bool
    solutionDescriptor: Optional[bool] = None
    metadata: Optional[AppDefMetadataModel] = None
    deployParameters: dict[str, str]
    technicalConfigurationParameters: dict[str, str]


class RegDefV1Model(SchemaValidatedModel):
    model_config = ConfigDict(extra="forbid")
    SCHEMA_NAME: ClassVar[str] = "regdef.schema.json"

    name: str
    credentialsId: str
    mavenConfig: dict[str, str]
    dockerConfig: dict[str, str]
    goConfig: Optional[dict[str, str]] = None
    rawConfig: Optional[dict[str, str]] = None
    npmConfig: Optional[dict[str, str]] = None
    helmConfig: Optional[dict[str, str]] = None
    helmAppConfig: Optional[dict[str, str]] = None


class RegDefV2Model(SchemaValidatedModel):
    model_config = ConfigDict(extra="forbid")
    SCHEMA_NAME: ClassVar[str] = "regdef-v2.schema.json"

    version: Literal["2.0"] = "2.0"
    name: str
    authConfig: Optional[dict[str, dict[str, Any]]] = None
    mavenConfig: dict[str, str]
    dockerConfig: Optional[dict[str, str]] = None
    goConfig: Optional[dict[str, str]] = None
    rawConfig: Optional[dict[str, str]] = None
    npmConfig: Optional[dict[str, str]] = None
    helmConfig: Optional[dict[str, str]] = None
    helmAppConfig: Optional[dict[str, str]] = None


class CredentialEntryModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["usernamePassword", "secret", "vaultAppRole", "external"]
    data: Optional[dict[str, str]] = None
    secretStore: Optional[str] = "default_store"
    remoteRefPath: Optional[str] = None
    create: Optional[bool] = None
    properties: Optional[list[PropertyMapping]] = None


class CredentialsMapModel(RootModel[dict[str, CredentialEntryModel]]):
    SCHEMA_NAME: ClassVar[str] = "credential.schema.json"

    @model_validator(mode="before")
    @classmethod
    def _validate_by_json_schema(cls, data: Any, info: ValidationInfo) -> Any:
        if isinstance(data, dict) and not (info.context and info.context.get("schema_validated")):
            validate_yaml_by_scheme_or_fail(input_yaml_content=data, schema_name=cls.SCHEMA_NAME)
        return data


class EnvDefinitionModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "env-definition.schema.json"

    inventory: Optional[dict[str, Any]] = None
    envTemplate: dict[str, Any]
    generatedVersions: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    security: Optional[dict[str, Any]] = None


class TemplateDescriptorModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "template-descriptor.schema.json"

    tenant: str
    cloud: Union[str, dict[str, Any]]
    namespaces: list[dict[str, Any]]
    composite_structure: Optional[str] = None
    external_credential_template: Optional[str] = None
    description: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
    parametersets: Optional[list[Any]] = None


SCHEMA_TO_MODEL: dict[str, type[BaseModel]] = {
    ApplicationModel.SCHEMA_NAME: ApplicationModel,
    NamespaceModel.SCHEMA_NAME: NamespaceModel,
    CloudModel.SCHEMA_NAME: CloudModel,
    TenantModel.SCHEMA_NAME: TenantModel,
    ResourceProfileModel.SCHEMA_NAME: ResourceProfileModel,
    CompositeStructureModel.SCHEMA_NAME: CompositeStructureModel,
    ParamsetModel.SCHEMA_NAME: ParamsetModel,
    AppDefModel.SCHEMA_NAME: AppDefModel,
    RegDefV1Model.SCHEMA_NAME: RegDefV1Model,
    RegDefV2Model.SCHEMA_NAME: RegDefV2Model,
    CredentialsMapModel.SCHEMA_NAME: CredentialsMapModel,
    EnvDefinitionModel.SCHEMA_NAME: EnvDefinitionModel,
    TemplateDescriptorModel.SCHEMA_NAME: TemplateDescriptorModel,
}


def validate_model_by_schema_name(data: dict[str, Any], schema_name: str, *, schema_validated=False) -> BaseModel | None:
    model_cls = SCHEMA_TO_MODEL.get(schema_name)
    if model_cls is not None:
        return model_cls.model_validate(data, context={"schema_validated": schema_validated})
    if not schema_validated:
        validate_yaml_by_scheme_or_fail(input_yaml_content=data, schema_name=schema_name)
    return None
