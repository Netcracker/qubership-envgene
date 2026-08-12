from os import getenv
from pathlib import Path

from dpg.v1.internal.deployment_plan.models import DeployPlan, DeployPlanEntity, \
    GenerationType  # noqa: F401 - re-exported
from envgenehelper.business_helper import (
    INVENTORY_DIR_NAME,
    get_current_env_dir_from_env_vars,
    parse_bg_ns_target,
)
from envgenehelper.errors import ReferenceError
from envgene_shared.utils.logger import logger
from envgenehelper.sd_helper import get_sd_dir, SD_FILE_NAME
from envgene_shared.utils.yaml_utils import openYaml, writeYamlToFile

DEPLOY_PLAN_FILE_NAME = "deploy-plan.yml"
DELTA_DEPLOY_PLAN_FILE_NAME = "delta-deploy-plan.yml"


class EnvgeneDeployPlan(DeployPlan):
    dp_path: Path | None = None

    @staticmethod
    def path() -> Path:
        return get_current_env_dir_from_env_vars() / INVENTORY_DIR_NAME / DEPLOY_PLAN_FILE_NAME

    @staticmethod
    def delta_path() -> Path:
        return get_current_env_dir_from_env_vars() / INVENTORY_DIR_NAME / DELTA_DEPLOY_PLAN_FILE_NAME

    @classmethod
    def read(cls, deploy_plan_path: Path = None) -> "EnvgeneDeployPlan":
        deploy_plan_path = deploy_plan_path or cls.path()
        raw = openYaml(deploy_plan_path, allow_default=True, default_yaml=list) or []
        plan = cls.from_dict(raw)
        plan.dp_path = deploy_plan_path
        return plan

    def write(self, deploy_plan_path: Path = None) -> None:
        deploy_plan_path = deploy_plan_path or self.path()
        writeYamlToFile(deploy_plan_path, self.to_dict())
        self.dp_path = deploy_plan_path


def resolve_namespace_entry(namespace_entry, bg_ns_target, deploy_postfix: str):
    if not isinstance(namespace_entry, dict):
        return namespace_entry
    if bg_ns_target is None:
        raise ValueError(
            f"BG_NS_TARGET must be set to 'ORIGIN' or 'PEER' "
            f"for deployPostfix '{deploy_postfix}'"
        )
    return namespace_entry[bg_ns_target.name.lower()]


def adapt_sd_to_deploy_plan(namespace_by_deploy_postfix: dict, file_name: str = SD_FILE_NAME,
                            output_path: Path = None) -> EnvgeneDeployPlan:
    sd_path = get_sd_dir().joinpath(file_name)
    sd_data = openYaml(sd_path, allow_default=True, default_yaml=dict) or {}
    apps = sd_data.get("applications", [])
    bg_ns_target = parse_bg_ns_target(getenv("BG_NS_TARGET"))

    if apps and not namespace_by_deploy_postfix:
        raise RuntimeError(
            "No namespaces map found for this environment - it looks like it hasn't been built yet. "
            "Please set ENV_BUILDER=true and run pipeline"
        )

    entities = []
    for app in apps:
        deploy_postfix = app.get("deployPostfix")
        namespace = namespace_by_deploy_postfix.get(deploy_postfix)
        if namespace is None:
            raise ReferenceError(
                f"No namespace found for deployPostfix '{deploy_postfix}' in the committed environment instance")
        namespace = resolve_namespace_entry(namespace, bg_ns_target, deploy_postfix)
        entities.append(DeployPlanEntity(version=app.get("version"), deployPostfix=deploy_postfix, namespace=namespace))

    logger.info(f"Adapted {sd_path} into a deploy plan ({len(entities)} application(s))")
    deploy_plan = EnvgeneDeployPlan(entities=entities)
    deploy_plan.write(output_path)
    return deploy_plan
