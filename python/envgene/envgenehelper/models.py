from enum import Enum


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
