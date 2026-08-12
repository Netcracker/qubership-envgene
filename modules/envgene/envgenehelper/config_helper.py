from functools import lru_cache
from importlib.resources import files
from os import getenv, path
import json
from pathlib import Path

from envgene_shared.utils.yaml_utils import openYaml, get_empty_yaml, validate_yaml_by_scheme_or_fail
from envgene_shared.utils.business_utils import getenv_with_error, get_envgene_config_yaml
from envgene_shared.utils.logger import logger
import jsonschema


REGDEF_V2_VERSION = "2.0"

def get_regdef_schema() -> dict:
    """Load RegDef V1 schema from package resources"""
    return json.loads(files("envgenehelper").joinpath("schemas/regdef.schema.json").read_text(encoding="utf-8"))


def get_regdef_v2_schema() -> dict:
    """Load RegDef V2 schema from package resources"""
    return json.loads(files("envgenehelper").joinpath("schemas/regdef-v2.schema.json").read_text(encoding="utf-8"))


def get_regdef_schema_for_content(content: dict) -> dict:
    """Get the appropriate schema (V1 or V2) based on registry definition content"""
    if content.get("version") == REGDEF_V2_VERSION or "authConfig" in content:
        return get_regdef_v2_schema()
    return get_regdef_schema()


def validate_regdef_or_fail(yaml_file_path: str):
    """Validate a registry definition YAML file (V1 or V2) by path"""
    content = openYaml(yaml_file_path)
    schema = get_regdef_schema_for_content(content)
    validate_yaml_by_scheme_or_fail(yaml_file_path=yaml_file_path, input_schema_content=schema)

