from enum import Enum
from typing import Optional

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
    keep_versions_per_app: Optional[int] = Field(default=None, ge=0)


class OperationType(CaseInsensitiveEnum):
    DEPLOY = "DEPLOY"
    CLEAN = "CLEAN"

    @classmethod
    def _missing_(cls, value):
        if not value:
            return cls.DEPLOY

        return super()._missing_(value)
