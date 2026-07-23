from pathlib import Path

from dpg.v1.internal.deployment_plan.models import DeployPlan, DeployPlanEntity, GenerationType  # noqa: F401 - re-exported
from envgenehelper.business_helper import get_current_env_dir_from_env_vars, INVENTORY_DIR_NAME
from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.logger import logger
from envgenehelper.sd_helper import get_sd_dir, SD_FILE_NAME
from envgenehelper.yaml_helper import openYaml, writeYamlToFile

DEPLOY_PLAN_FILE_NAME = "deploy-plan.yml"
DELTA_DEPLOY_PLAN_FILE_NAME = "delta-deploy-plan.yml"


class EnvgeneDeployPlan(DeployPlan):
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
        return cls.from_dict(raw)

    def write(self, deploy_plan_path: Path = None) -> None:
        writeYamlToFile(deploy_plan_path or self.path(), self.to_dict())


def adapt_sd_to_deploy_plan(namespace_by_deploy_postfix: dict, file_name: str = SD_FILE_NAME,
                             output_path: Path = None) -> EnvgeneDeployPlan:
    sd_path = get_sd_dir().joinpath(file_name)
    sd_data = openYaml(sd_path, allow_default=True, default_yaml=dict) or {}
    apps = sd_data.get("applications", [])

    entities = []
    for app in apps:
        deploy_postfix = app.get("deployPostfix")
        namespace = namespace_by_deploy_postfix.get(deploy_postfix, deploy_postfix)
        entities.append(DeployPlanEntity(version=app.get("version"), deployPostfix=deploy_postfix, namespace=namespace))

    logger.info(f"Adapted {sd_path} into a deploy plan ({len(entities)} application(s))")
    deploy_plan = EnvgeneDeployPlan(entities=entities)
    deploy_plan.write(output_path)
    return deploy_plan


def clean_namespaces(namespace_by_deploy_postfix: dict, namespace_names: str) -> None:
    if not namespace_names:
        EnvgeneDeployPlan(entities=[]).write()
        logger.info("Operation type CLEAN: NAMESPACE_NAMES is empty, env-cleanup (all namespaces)")
        return

    # { "namespace_name": "deploy_postfix" } - invert the map DeployPostfixNamespaceMapStep already built
    ns_map = {namespace: postfix for postfix, namespace in namespace_by_deploy_postfix.items()}
    ns_for_cleanup = {}

    for ns_name in split_multi_value_param(namespace_names):
        deploy_postfix = ns_map.get(ns_name)
        if deploy_postfix is None:
            raise ValueError(f"Operation type CLEAN: namespace '{ns_name}' has no matching namespace folder")
        ns_for_cleanup[ns_name] = deploy_postfix

    postfixes_for_cleanup = set(ns_for_cleanup.values())

    deploy_plan = EnvgeneDeployPlan.read()
    postfixes_from_plan = {e.deploy_postfix for e in deploy_plan.entities}
    for ns_name, dp in ns_for_cleanup.items():
        if dp not in postfixes_from_plan:
            # case incorrect ns from namespace_names or accidentally launched 2 clean up same ns
            logger.warning(f"Operation type CLEAN: deployPostfix '{dp}' (namespace '{ns_name}') not found in deploy-plan")

    remaining_entities = [e for e in deploy_plan.entities if e.deploy_postfix not in postfixes_for_cleanup]
    EnvgeneDeployPlan(entities=remaining_entities).write()
