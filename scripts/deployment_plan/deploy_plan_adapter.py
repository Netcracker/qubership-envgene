from dataclasses import dataclass
from pathlib import Path
import tempfile

from envgenehelper import find_files_by_basename
from envgenehelper.yaml_helper import openYaml, writeYamlToFile

DEPLOY_PLAN_FILE = "deploy-plan.yml"
SD_DESCRIPTOR_BASENAME = "sd"
SD_FROM_DEPLOY_PLAN_VERSION = 2.1
SD_FROM_DEPLOY_PLAN_TYPE = "deploy"


@dataclass(frozen=True)
class ApplicationDeploymentEntry:
    version: str
    deploy_postfix: str
    namespace: str | None = None


def deploy_plan_entities(deploy_plan_path: Path) -> list[dict]:
    entities = openYaml(deploy_plan_path)
    if not isinstance(entities, list):
        raise ValueError(f"Deploy plan at {deploy_plan_path} must be a YAML list")
    return entities


def deploy_plan_to_sd_config(entities: list[dict]) -> dict:
    return {
        "version": SD_FROM_DEPLOY_PLAN_VERSION,
        "type": SD_FROM_DEPLOY_PLAN_TYPE,
        "applications": [
            {
                "version": entity["version"],
                "deployPostfix": entity.get("deployPostfix", ""),
            }
            for entity in entities
        ],
    }


def materialize_sd_from_deploy_plan(deploy_plan_path: Path) -> Path:
    sd_config = deploy_plan_to_sd_config(deploy_plan_entities(deploy_plan_path))
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", prefix="sd-from-deploy-plan-", delete=False)
    sd_path = Path(tmp.name)
    tmp.close()
    writeYamlToFile(sd_path, sd_config)
    return sd_path


def application_entries_from_sd(sd_config: dict) -> list[ApplicationDeploymentEntry]:
    applications = sd_config.get("applications", [])
    return [
        ApplicationDeploymentEntry(
            version=app["version"],
            deploy_postfix=app.get("deployPostfix", ""),
        )
        for app in applications
    ]


def application_entries_from_deploy_plan_entities(entities: list[dict]) -> list[ApplicationDeploymentEntry]:
    return [
        ApplicationDeploymentEntry(
            version=entity["version"],
            deploy_postfix=entity.get("deployPostfix", ""),
            namespace=entity.get("namespace") or None,
        )
        for entity in entities
    ]


def resolve_sd_path(
    inventory_dir: Path,
    *,
    sd_path: Path | None = None,
    gitlab_deploy: bool = False,
) -> Path | None:
    deploy_plan_path = inventory_dir / DEPLOY_PLAN_FILE
    if gitlab_deploy:
        if not deploy_plan_path.is_file():
            raise FileNotFoundError(f"Missing deploy plan at {deploy_plan_path}")
        return materialize_sd_from_deploy_plan(deploy_plan_path)

    if deploy_plan_path.is_file():
        return materialize_sd_from_deploy_plan(deploy_plan_path)

    if sd_path is not None and sd_path.is_file():
        return sd_path

    return None


def resolve_application_entries(
    env_instances_dir: Path,
    render_env_dir: Path | None = None,
    *,
    gitlab_deploy: bool = False,
) -> list[ApplicationDeploymentEntry] | None:
    inventory_dir = env_instances_dir / "Inventory"
    deploy_plan_path = inventory_dir / DEPLOY_PLAN_FILE

    if gitlab_deploy:
        if not deploy_plan_path.is_file():
            raise FileNotFoundError(f"Missing deploy plan at {deploy_plan_path}")
        return application_entries_from_deploy_plan_entities(deploy_plan_entities(deploy_plan_path))

    if deploy_plan_path.is_file():
        return application_entries_from_deploy_plan_entities(deploy_plan_entities(deploy_plan_path))

    if render_env_dir is None:
        return None

    sd_basename = str(render_env_dir / "Inventory" / "solution-descriptor" / SD_DESCRIPTOR_BASENAME)
    resolved_sd_path = next(iter(find_files_by_basename(sd_basename)), None)
    if not resolved_sd_path:
        return None

    sd_config = openYaml(filePath=resolved_sd_path, safe_load=True)
    if "applications" not in sd_config:
        raise ValueError("Missing 'applications' key in solution descriptor")
    return application_entries_from_sd(sd_config)
