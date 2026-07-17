from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


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


class SecretStore(BaseModel):
    type: Literal["vault", "gcp", "aws", "azure"]
    url: str
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
