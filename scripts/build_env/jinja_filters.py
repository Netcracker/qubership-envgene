from urllib.parse import urlsplit

from envgenehelper import dumpYamlToStr
from jinja2 import Environment


def urlsplit_filter(value, part=None):
    if not isinstance(value, str): return ""
    try:
        parts = urlsplit(value)
    except ValueError as e:
        return f"Invalid url: {e}"
    if part:
        return getattr(parts, part, "")
    return parts


JINJA_FILTERS = {
    "urlsplit": urlsplit_filter,
    "to_nice_yaml": dumpYamlToStr
}


class JinjaFilters:
    @staticmethod
    def register(env: Environment, filters=None):
        if filters is None:
            filters = JINJA_FILTERS.keys()
        for name in filters:
            if name in JINJA_FILTERS:
                env.filters[name] = JINJA_FILTERS[name]
