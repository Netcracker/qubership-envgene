from pathlib import Path

from envgenehelper import find_files_by_basename
from envgenehelper.yaml_helper import openYaml

from deployment_plan.application_entries import (
    DEPLOY_PLAN_FILE,
    ApplicationDeploymentEntry,
    application_entries_from_deploy_plan_entities,
    application_entries_from_sd,
)

SD_DESCRIPTOR_BASENAME = "sd"


def deploy_plan_entities(deploy_plan_path: Path) -> list[dict]:
    entities = openYaml(deploy_plan_path)
    if not isinstance(entities, list):
        raise ValueError(f"Deploy plan at {deploy_plan_path} must be a YAML list")
    return entities


def resolve_application_entries(
    env_instances_dir: Path,
    render_env_dir: Path | None = None,
) -> list[ApplicationDeploymentEntry] | None:
    deploy_plan_path = env_instances_dir / "Inventory" / DEPLOY_PLAN_FILE
    if deploy_plan_path.is_file():
        return application_entries_from_deploy_plan_entities(deploy_plan_entities(deploy_plan_path))

    if render_env_dir is None:
        return None

    sd_basename = str(render_env_dir / "Inventory" / "solution-descriptor" / SD_DESCRIPTOR_BASENAME)
    sd_path = next(iter(find_files_by_basename(sd_basename)), None)
    if not sd_path:
        return None

    sd_config = openYaml(filePath=sd_path, safe_load=True)
    if "applications" not in sd_config:
        raise ValueError("Missing 'applications' key in solution descriptor")
    return application_entries_from_sd(sd_config)
