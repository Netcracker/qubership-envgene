from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TemplateVersionUpdateMode(str, Enum):
    PERSISTENT = "PERSISTENT"
    TEMPORARY = "TEMPORARY"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value = value.upper()
            for m in cls:
                if m.value == value:
                    return m
        return None


class SbomRetentionConfig(BaseModel):
    enabled: bool = Field(default=False)
    keep_versions_per_app: Optional[int] = Field(default=None, ge=0)
