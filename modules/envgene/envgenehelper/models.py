from enum import Enum
from typing import Annotated, Any, ClassVar, Literal, Optional, Union, get_args, get_origin

from pydantic import (
    BaseModel, ConfigDict, Field, PlainValidator, PrivateAttr, RootModel, TypeAdapter, ValidationInfo,
    field_validator, model_validator,
)
from ruyaml import CommentedMap, CommentedSeq

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


def _require_mapping(value: Any) -> Any:
    if not isinstance(value, dict):
        raise ValueError(f"Input should be a mapping, got {type(value).__name__}")
    return value


YamlMapping = Annotated[dict[str, Any], PlainValidator(_require_mapping)]


def _unwrap(annotation):
    if get_origin(annotation) is Annotated:
        return _unwrap(get_args(annotation)[0])
    return annotation


def _pair_types(annotation):
    origin = get_origin(_unwrap(annotation))
    args = get_args(_unwrap(annotation))
    if origin is dict and len(args) == 2:
        return args
    if origin is list and len(args) == 1:
        return (int, args[0])
    return (Any, Any)


def _coerce(annotation, value):
    if annotation in (Any, object):
        return value
    origin = get_origin(annotation)
    if origin is None and isinstance(value, annotation):
        return value
    strict = annotation in (str, int, float, bool)
    coerced = TypeAdapter(annotation).validate_python(value, strict=strict)
    if isinstance(value, dict) and isinstance(coerced, dict) and coerced == value:
        return value
    return coerced


class CheckedMap(CommentedMap):
    def __init__(self, data=None, annotation=None):
        CommentedMap.__init__(self)
        self._annotation = annotation or dict[str, Any]
        self._quiet = True
        if isinstance(data, dict):
            for key, value in data.items():
                self[key] = value
            if hasattr(data, "copy_attributes"):
                data.copy_attributes(self)
        self._quiet = False

    def _stored(self, key, value):
        if self._quiet:
            return value
        key_type, value_type = _pair_types(self._annotation)
        _coerce(key_type, key)
        return _coerce(value_type, value)

    def __setitem__(self, key, value):
        CommentedMap.__setitem__(self, key, self._stored(key, value))

    def insert(self, pos, key, value, comment=None):
        CommentedMap.insert(self, pos, key, self._stored(key, value), comment)

    def update(self, *args, **kwargs):
        incoming = {}
        for arg in args:
            incoming.update(arg)
        incoming.update(kwargs)
        for key, value in incoming.items():
            self[key] = value

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]


class CheckedList(list):
    def __init__(self, items=(), annotation=None):
        list.__init__(self)
        self._annotation = annotation or list[Any]
        for item in items:
            self.append(item)

    def _stored(self, item):
        return _coerce(_pair_types(self._annotation)[1], item)

    def append(self, item):
        list.append(self, self._stored(item))

    def insert(self, index, item):
        list.insert(self, index, self._stored(item))

    def extend(self, items):
        list.extend(self, [self._stored(item) for item in items])

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            list.__setitem__(self, index, [self._stored(item) for item in value])
            return
        list.__setitem__(self, index, self._stored(value))

    def __iadd__(self, items):
        self.extend(items)
        return self


def _container_annotation(annotation):
    annotation = _unwrap(annotation)
    if get_origin(annotation) is Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return _container_annotation(args[0])
    return annotation


def _guard_container(value, annotation):
    annotation = _container_annotation(annotation)
    origin = get_origin(annotation)
    if origin is list and isinstance(value, list) and not isinstance(value, CheckedList):
        return CheckedList(value, annotation)
    if origin is dict and isinstance(value, dict) and not isinstance(value, CheckedMap):
        return CheckedMap(value, annotation)
    return value


def bind_yaml(value: Any, node: Any) -> None:
    if isinstance(value, YamlBacked) and isinstance(node, dict):
        value._yaml = node if isinstance(node, CommentedMap) else CommentedMap(node)
        for key in value.keys():
            bind_yaml(value._child(key), value._yaml.get(key))
    elif isinstance(value, list) and isinstance(node, list):
        for item, item_node in zip(value, node):
            bind_yaml(item, item_node)


def _to_yaml_value(value: Any, current: Any) -> Any:
    if isinstance(value, YamlBacked):
        return value.to_yaml()
    if isinstance(value, CheckedMap):
        copied = CommentedMap()
        for key, item in value.items():
            copied[key] = _to_yaml_value(item, None)
        value.copy_attributes(copied)
        return copied
    if isinstance(value, list) and any(isinstance(item, YamlBacked) for item in value):
        seq = current if isinstance(current, CommentedSeq) else CommentedSeq()
        items = [_to_yaml_value(item, None) for item in value]
        seq.clear()
        seq.extend(items)
        return seq
    if isinstance(current, type(value)) and current == value:
        return current
    return value


class YamlBacked:
    @property
    def ca(self):
        return self._node().ca

    def _node(self) -> CommentedMap:
        if self._yaml is None:
            self._yaml = CommentedMap()
        return self._yaml

    def __getitem__(self, key):
        if key not in self.keys():
            raise KeyError(key)
        return self._child(key)

    def __setitem__(self, key, value):
        self.store_value(key, value)

    def __contains__(self, key) -> bool:
        return key in self.keys()

    def __iter__(self):
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self.keys())

    def get(self, key, default=None):
        return self[key] if key in self else default

    def items(self) -> list:
        return [(key, self._child(key)) for key in self.keys()]

    def values(self) -> list:
        return [self._child(key) for key in self.keys()]

    def _store_node_value(self, key, value, comment) -> None:
        node = self._node()
        node.pop(key, None)
        node[key] = value
        bind_yaml(self._child(key), value)
        node.ca.items.pop(key, None)
        if comment:
            node.yaml_add_eol_comment(comment, key=key)

    def to_yaml(self) -> CommentedMap:
        node = self._node()
        for key in self.keys():
            node[key] = _to_yaml_value(self._child(key), node.get(key))
        return node


class YamlModel(YamlBacked, BaseModel):
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
    _yaml: Optional[CommentedMap] = PrivateAttr(default=None)

    def _child(self, key):
        if key in type(self).model_fields:
            return getattr(self, key)
        return self.__pydantic_extra__[key]

    def keys(self) -> list:
        present = set(self.model_fields_set) | set(self.__pydantic_extra__ or {})
        ordered = [key for key in self._node() if key in present]
        return ordered + sorted(present - set(ordered))

    def store_value(self, key, value, comment="") -> None:
        setattr(self, key, value)
        self._store_node_value(key, self._child(key), comment)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        field = self.__class__.model_fields.get(name)
        if field is None:
            return
        guarded = _guard_container(getattr(self, name), field.annotation)
        if guarded is not getattr(self, name):
            object.__setattr__(self, name, guarded)

    def model_post_init(self, context):
        for name, field in self.__class__.model_fields.items():
            guarded = _guard_container(getattr(self, name), field.annotation)
            if guarded is not getattr(self, name):
                object.__setattr__(self, name, guarded)


class PropertyMapping(YamlModel):
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


def _is_schema_entry(data: Any, info: ValidationInfo) -> bool:
    return (isinstance(data, dict) and info.field_name is None
            and not (info.context and info.context.get("schema_validated")))


class SchemaValidatedModel(YamlModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    SCHEMA_NAME: ClassVar[str]

    @model_validator(mode="before")
    @classmethod
    def _validate_by_json_schema(cls, data: Any, info: ValidationInfo) -> Any:
        if _is_schema_entry(data, info):
            validate_yaml_by_scheme_or_fail(input_yaml_content=data, schema_name=cls.SCHEMA_NAME)
        return data

    def validate_schema(self) -> None:
        if hasattr(self, "SCHEMA_NAME") and self.SCHEMA_NAME:
            validate_yaml_by_scheme_or_fail(
                input_yaml_content=self.model_dump(exclude_unset=True, by_alias=True),
                schema_name=self.SCHEMA_NAME,
            )


class ProfileOverrideModel(YamlModel):
    model_config = ConfigDict(extra="allow")
    name: Optional[str] = None
    baseline: Optional[str] = None


class ApplicationModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "application.schema.json"

    name: str
    deployParameters: YamlMapping = Field(default_factory=dict)
    technicalConfigurationParameters: YamlMapping = Field(default_factory=dict)


class NamespaceModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "namespace.schema.json"

    name: str
    credentialsId: Optional[str] = None
    isServerSideMerge: bool
    labels: list[str] = Field(default_factory=list)
    cleanInstallApprovalRequired: bool
    mergeDeployParametersAndE2EParameters: bool
    profile: Optional[ProfileOverrideModel] = None
    deployParameters: YamlMapping = Field(default_factory=dict)
    e2eParameters: YamlMapping = Field(default_factory=dict)
    technicalConfigurationParameters: YamlMapping = Field(default_factory=dict)
    deployParameterSets: list[str] = Field(default_factory=list)
    e2eParameterSets: list[str] = Field(default_factory=list)
    technicalConfigurationParameterSets: list[str] = Field(default_factory=list)
    version: Optional[Union[int, float]] = None


class MaasConfigModel(YamlModel):
    model_config = ConfigDict(extra="allow")
    credentialsId: Optional[str] = None
    maasUrl: Optional[str] = None
    maasInternalAddress: Optional[str] = None
    enable: Optional[bool] = None


class VaultConfigModel(YamlModel):
    model_config = ConfigDict(extra="allow")
    credentialsId: Optional[str] = None
    url: Optional[str] = None
    enable: Optional[bool] = None


class DbaasConfigModel(YamlModel):
    model_config = ConfigDict(extra="allow")
    credentialsId: Optional[str] = None
    apiUrl: Optional[str] = None
    aggregatorUrl: Optional[str] = None
    enable: Optional[bool] = None


class ConsulConfigModel(YamlModel):
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
    databases: list[YamlMapping] = Field(default_factory=list)
    mergeDeployParametersAndE2EParameters: Optional[bool] = None
    profile: Optional[ProfileOverrideModel] = None
    deployParameters: YamlMapping
    e2eParameters: YamlMapping
    technicalConfigurationParameters: YamlMapping
    deployParameterSets: list[str] = Field(default_factory=list)
    e2eParameterSets: list[str] = Field(default_factory=list)
    technicalConfigurationParameterSets: list[str] = Field(default_factory=list)
    maasConfig: MaasConfigModel
    vaultConfig: VaultConfigModel
    dbaasConfigs: list[DbaasConfigModel] = Field(default_factory=list)
    consulConfig: ConsulConfigModel
    version: Optional[Union[int, float]] = None


class GlobalE2EParametersModel(YamlModel):
    model_config = ConfigDict(extra="allow")
    pipelineDefaultRecipients: Optional[str] = None
    recipientsStrategy: Optional[str] = None
    mergeTenantsAndE2EParameters: Optional[bool] = None
    environmentParameters: YamlMapping = Field(default_factory=dict)


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
    deployParameters: YamlMapping = Field(default_factory=dict)
    globalE2EParameters: Optional[GlobalE2EParametersModel] = None


class ServiceParameterModel(YamlModel):
    model_config = ConfigDict(extra="allow")
    name: str
    value: Union[str, int, bool]


class ResourceProfileServiceModel(YamlModel):
    model_config = ConfigDict(extra="allow")
    name: str
    parameters: list[ServiceParameterModel]


class ResourceProfileApplicationModel(YamlModel):
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


class CompositeComponentModel(YamlModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    type: Literal["namespace", "bgdomain"]


class CompositeStructureModel(SchemaValidatedModel):
    model_config = ConfigDict(extra="forbid")
    SCHEMA_NAME: ClassVar[str] = "composite-structure.schema.json"

    name: str
    baseline: CompositeComponentModel
    satellites: list[CompositeComponentModel] = Field(default_factory=list)


class ParamsetApplicationModel(YamlModel):
    model_config = ConfigDict(extra="allow")
    appName: str
    parameters: dict[str, Any]


class ParamsetModel(SchemaValidatedModel):
    SCHEMA_NAME: ClassVar[str] = "paramset.schema.json"

    name: str
    version: Optional[Union[int, float]] = None
    parameters: Optional[dict[str, Any]] = None
    applications: Optional[list[ParamsetApplicationModel]] = None


class AppDefMetadataModel(YamlModel):
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


class CredentialEntryModel(YamlModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["usernamePassword", "secret", "vaultAppRole", "external"]
    data: Optional[dict[str, str]] = None
    secretStore: Optional[str] = "default_store"
    remoteRefPath: Optional[str] = None
    create: Optional[bool] = None
    properties: Optional[list[PropertyMapping]] = None


class CredentialsMapModel(YamlBacked, RootModel[dict[str, CredentialEntryModel]]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    SCHEMA_NAME: ClassVar[str] = "credential.schema.json"
    _yaml: Optional[CommentedMap] = PrivateAttr(default=None)

    @model_validator(mode="before")
    @classmethod
    def _validate_by_json_schema(cls, data: Any, info: ValidationInfo) -> Any:
        if isinstance(data, dict) and not (info.context and info.context.get("schema_validated")):
            validate_yaml_by_scheme_or_fail(input_yaml_content=data, schema_name=cls.SCHEMA_NAME)
        return data

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name == "root":
            guarded = _guard_container(self.root, dict[str, CredentialEntryModel])
            if guarded is not self.root:
                object.__setattr__(self, "root", guarded)

    def model_post_init(self, context):
        guarded = _guard_container(self.root, dict[str, CredentialEntryModel])
        if guarded is not self.root:
            object.__setattr__(self, "root", guarded)

    def _child(self, key):
        return self.root[key]

    def keys(self) -> list:
        return list(self.root)

    def store_value(self, key, value, comment="") -> None:
        entry = type(self).model_validate({key: value}, context={"schema_validated": True}).root[key]
        self.root[key] = entry
        self._store_node_value(key, value, comment)


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
