from functools import lru_cache
from os import getenv
from pathlib import Path

from envgene_shared.utils.logger import logger
from envgene_shared.utils.yaml_utils import openYaml, get_empty_yaml, validate_yaml_by_scheme_or_fail


def getenv_with_error(var_name, *, no_log=False):
    var = getenv(var_name)
    if not var:
        raise ValueError(f'Required value was not given and is not set in environment as {var_name}')
    if not no_log:
        logger.debug(f"{var_name}: {var}")
    return var


def get_schema_dir() -> Path:
    return Path(getenv("JSON_SCHEMAS_DIR", "/schemas"))


def get_project_root() -> Path:
    project_dir = getenv("CI_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)
    return Path.cwd()


@lru_cache(maxsize=1)
def get_envgene_config_yaml():
    envgene_config_path = get_project_root()/"configuration"/"config.yml"
    try:
        config = openYaml(envgene_config_path)
    except FileNotFoundError:
        logger.warning(f'Failed to find config file in {envgene_config_path}')
        return get_empty_yaml()
    validate_yaml_by_scheme_or_fail(input_yaml_content=config, schema_file_path=get_schema_dir() / "config.schema.json")
    logger.debug(f"Config content: {config}")
    return config
