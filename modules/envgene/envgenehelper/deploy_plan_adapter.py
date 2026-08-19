from pathlib import Path

from dpg.v1.internal.deployment_plan.models import DeployPlan, DeployPlanEntity, GenerationType  # noqa: F401 - re-exported
from envgenehelper.business_helper import get_current_env_dir_from_env_vars, INVENTORY_DIR_NAME
from envgenehelper.errors import ReferenceError
from envgenehelper.logger import logger
from envgenehelper.sd_helper import get_sd_dir, SD_FILE_NAME
from envgenehelper.yaml_helper import openYaml, writeYamlToFile

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


def adapt_sd_to_deploy_plan(namespace_by_deploy_postfix: dict, file_name: str = SD_FILE_NAME,
                             output_path: Path = None) -> EnvgeneDeployPlan:
    sd_path = get_sd_dir().joinpath(file_name)
    sd_data = openYaml(sd_path, allow_default=True, default_yaml=dict) or {}
    apps = sd_data.get("applications", [])

    entities = []
    for app in apps:
        deploy_postfix = app.get("deployPostfix")
        namespace = namespace_by_deploy_postfix.get(deploy_postfix)
        if namespace is None:
            raise ReferenceError(
                f"No namespace found for deployPostfix '{deploy_postfix}' in the committed environment instance")
        entities.append(DeployPlanEntity(version=app.get("version"), deployPostfix=deploy_postfix, namespace=namespace))

    logger.info(f"Adapted {sd_path} into a deploy plan ({len(entities)} application(s))")
    deploy_plan = EnvgeneDeployPlan(entities=entities)
    deploy_plan.write(output_path)
    return deploy_plan
