from dpg.v1.cmd import DeploymentPlanGeneratorCommand
from envgenehelper.business_helper import get_current_env_dir_from_env_vars, INVENTORY_DIR_NAME
from envgenehelper.deploy_plan_adapter import DEPLOY_PLAN_FILE_NAME, EnvgeneDeployPlan

from build_env.namespace_render import NAMESPACE_MAP_FILE
from pipeline.pipeline_parameters import PipelineParametersHandler

_INTERMEDIATE_PLAN_FILE = "deploy-plan-calculated.yml"


def run_generate_deployment_plan(ctx: PipelineParametersHandler) -> None:
    application_versions = ctx.params.get("APPLICATION_VERSIONS")
    if not application_versions:
        raise ValueError("APPLICATION_VERSIONS is required when PIPELINE_TYPE=GITLAB_DEPLOY")

    inventory_dir = get_current_env_dir_from_env_vars() / INVENTORY_DIR_NAME
    namespace_map_path = inventory_dir / NAMESPACE_MAP_FILE
    if not namespace_map_path.is_file():
        raise FileNotFoundError(f"Missing namespace map at {namespace_map_path}")

    intermediate_plan_path = inventory_dir / _INTERMEDIATE_PLAN_FILE
    deploy_plan_path = inventory_dir / DEPLOY_PLAN_FILE_NAME

    # calculate() - what to deploy and in what order, map() - in which namespace "
    calculated_plan = DeploymentPlanGeneratorCommand.calculate(
        applications=application_versions,
        output_file=intermediate_plan_path,
        rootdir=ctx.work_dir,
    )
    deploy_plan = DeploymentPlanGeneratorCommand.map(
        deploy_plan=calculated_plan,
        map=namespace_map_path,
        output_file=deploy_plan_path,
    )
    ctx.deploy_plan = EnvgeneDeployPlan(entities=deploy_plan.entities)

    intermediate_plan_path.unlink(missing_ok=True)
