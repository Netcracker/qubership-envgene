import os
from pathlib import Path

from .constants import APPDEF_SCHEMA_FILE, REGDEF_V1_SCHEMA_FILE, REGDEF_V2_SCHEMA_FILE
from .logger import logger
from .yaml_helper import findAllYamlsInDir, openYaml, validate_yaml_by_scheme_or_fail


def ensure_required_keys(context: dict, required: list[str]):
    missing = [var for var in required if var not in context]
    if missing:
        raise ValueError(
            f"Required variables: {', '.join(required)}. "
            f"Not found: {', '.join(missing)}"
        )


def ensure_valid_fields(context: dict, fields: list[str]):
    invalid = []
    for field in fields:
        value = context.get(field)
        if not value:
            invalid.append(f"{field}={value!r}")

    if invalid:
        raise ValueError(
            f"Invalid or empty fields found: {', '.join(invalid)}. "
            f"Required fields: {', '.join(fields)}"
        )


def validate_appregdefs(appdef_dir, regdef_dir, schemas_dir):
    """Validate AppDef and RegDef files against their respective schemas.

    Args:
        appdef_dir: Path to the AppDefs directory.
        regdef_dir: Path to the RegDefs directory.
        schemas_dir: Path to the directory containing schema JSON files.
    """
    schemas_path = Path(schemas_dir)

    if os.path.exists(appdef_dir):
        appdef_files = findAllYamlsInDir(appdef_dir)
        if not appdef_files:
            logger.warning(f"No AppDef YAMLs found in {appdef_dir}")
        for file in appdef_files:
            logger.info(f"AppDef file: {file}")
            validate_yaml_by_scheme_or_fail(file, str(schemas_path / APPDEF_SCHEMA_FILE))

    if os.path.exists(regdef_dir):
        regdef_files = findAllYamlsInDir(regdef_dir)
        if not regdef_files:
            logger.warning(f"No RegDef YAMLs found in {regdef_dir}")
        for file in regdef_files:
            logger.info(f"Validating RegDef file: {file}")
            regdef_content = openYaml(file)
            version = str(regdef_content.get('version', '1.0'))
            schema_file = REGDEF_V2_SCHEMA_FILE if version != '1.0' else REGDEF_V1_SCHEMA_FILE
            validate_yaml_by_scheme_or_fail(file, str(schemas_path / schema_file))
