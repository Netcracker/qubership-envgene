from urllib.parse import urlsplit

from envgenehelper import dumpYamlToStr
from jinja2 import Environment, FileSystemLoader, ChainableUndefined, BaseLoader


def create_jinja_env(templates_dir: str = "") -> Environment:
    loader = FileSystemLoader(templates_dir) if templates_dir else BaseLoader()
    if templates_dir:
        env = Environment(
            loader=loader,
            undefined=ChainableUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
    else:
        env = Environment(
            undefined=ChainableUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
    JinjaFilters.register(env)
    return env


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
