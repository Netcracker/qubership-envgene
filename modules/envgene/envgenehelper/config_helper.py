from functools import lru_cache
from os import getenv

from envgene_shared.utils.yaml_utils import get_empty_yaml, get_schema, openYaml, validate_yaml_by_scheme_or_fail
from envgene_shared.utils.business_utils import getenv_with_error, get_envgene_config_yaml
from envgene_shared.utils.logger import logger
from .constants import CI_JOB_ARTIFACT_MAX_SIZE_MB, SBOM_RETENTION_MAX_SIZE_MB
from .models import SaveArtifactsStrategy


REGDEF_V2_VERSION = "2.0"

def get_regdef_schema() -> dict:
    return get_schema("regdef.schema.json")


def get_regdef_v2_schema() -> dict:
    return get_schema("regdef-v2.schema.json")


def get_regdef_schema_for_content(content: dict) -> dict:
    """Get the appropriate schema (V1 or V2) based on registry definition content"""
    return get_schema(get_regdef_schema_name_for_content(content))


def get_regdef_schema_name_for_content(content: dict) -> str:
    if content.get("version") == REGDEF_V2_VERSION or "authConfig" in content:
        return "regdef-v2.schema.json"
    return "regdef.schema.json"


def validate_regdef_or_fail(yaml_file_path: str):
    """Validate a registry definition YAML file (V1 or V2) by path"""
    content = openYaml(yaml_file_path)
    validate_yaml_by_scheme_or_fail(yaml_file_path=yaml_file_path,
                                    schema_name=get_regdef_schema_name_for_content(content))


def get_artifact_size_limit_mb() -> int:
    env_override = getenv("ARTIFACT_SIZE_LIMIT_MB")
    if env_override:
        return int(env_override)
    return get_envgene_config_yaml().get("save_artifacts", {}).get("size_limit_mb", CI_JOB_ARTIFACT_MAX_SIZE_MB)


def get_save_artifacts_strategy() -> SaveArtifactsStrategy:
    env_override = getenv("SAVE_ARTIFACTS_STRATEGY")
    if env_override:
        return SaveArtifactsStrategy(env_override)
    value = get_envgene_config_yaml().get("save_artifacts", {}).get("strategy", "ALWAYS")
    return SaveArtifactsStrategy(value)


def get_sbom_retention_size_limit_mb() -> int:
    env_override = getenv("SBOM_RETENTION_SIZE_LIMIT_MB")
    if env_override:
        return int(env_override)
    return get_envgene_config_yaml().get("sbom_retention", {}).get("size_limit_mb", SBOM_RETENTION_MAX_SIZE_MB)

