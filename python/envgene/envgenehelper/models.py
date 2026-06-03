from enum import Enum

from pydantic import BaseModel, Field


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
    keep_versions_per_app: int = Field(default=10, ge=0)


class OperationType(CaseInsensitiveEnum):
    DEPLOY = "DEPLOY"
    CLEAN = "CLEAN"

    @classmethod
    def _missing_(cls, value):
        if not value:
            return cls.DEPLOY

        return super()._missing_(value)
