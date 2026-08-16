from dpg.v1.cmd import DeploymentPlanGeneratorCommand
from dpg.v1.internal.deployment_plan.deployment_plan import DeploymentPlanCalculator
from envgenehelper.business_helper import get_current_env_dir_from_env_vars, INVENTORY_DIR_NAME
from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.deploy_plan_adapter import EnvgeneDeployPlan

from build_env.namespace_render import NAMESPACE_MAP_FILE
from pipeline.pipeline_parameters import PipelineParametersHandler

_INTERMEDIATE_CALCULATED_FILE = "deploy-plan-calculated.yml"
_INTERMEDIATE_MAPPED_FILE = "deploy-plan-mapped.yml"


def merge_deployment_plan(ctx: PipelineParametersHandler) -> None:
    application_versions = ctx.params.get("APPLICATION_VERSIONS")
    deploy_postfixes_filter = ctx.params.get("DEPLOY_POSTFIXES_FILTER")
    namespace_names_filter = ctx.params.get("NAMESPACE_NAMES_FILTER")
    component_names_filter = ctx.params.get("COMPONENT_NAMES_FILTER")
    wave_names_filter = ctx.params.get("WAVE_NAMES_FILTER")
    if not application_versions:
        raise ValueError("APPLICATION_VERSIONS is required when PIPELINE_TYPE=GITLAB_DEPLOY")

    inventory_dir = get_current_env_dir_from_env_vars() / INVENTORY_DIR_NAME
    namespace_map_path = inventory_dir / NAMESPACE_MAP_FILE
    if not namespace_map_path.is_file():
        raise FileNotFoundError(f"Missing namespace map at {namespace_map_path}")

    calculated_plan_path = inventory_dir / _INTERMEDIATE_CALCULATED_FILE
    mapped_plan_path = inventory_dir / _INTERMEDIATE_MAPPED_FILE

    # calculate() - what to deploy and in what order, map() - in which namespace "
    calculated_plan = DeploymentPlanGeneratorCommand.calculate(
        applications=application_versions,
        output_file=calculated_plan_path,
        rootdir=ctx.work_dir,
    )
    deploy_plan = DeploymentPlanGeneratorCommand.map(
        deploy_plan=calculated_plan,
        map=namespace_map_path,
        output_file=mapped_plan_path,
    )

    filtered_deploy_plan = DeploymentPlanGeneratorCommand.filter(
        deploy_plan=deploy_plan,
        deploy_postfix_filter=deploy_postfixes_filter,
        component_names_filter=component_names_filter,
        wave_filter=wave_names_filter,
        namespace_filter=namespace_names_filter
    )

    delta = EnvgeneDeployPlan(entities=filtered_deploy_plan.entities)
    merged = DeploymentPlanCalculator.merge(source=ctx.deploy_plan, dest=delta)
    ctx.deploy_plan = EnvgeneDeployPlan(entities=merged.entities)
    ctx.deploy_plan.write()
    ctx.deploy_plan_delta = delta
    ctx.deploy_plan_delta.write(EnvgeneDeployPlan.delta_path())

    calculated_plan_path.unlink(missing_ok=True)
    mapped_plan_path.unlink(missing_ok=True)


def reduce_deployment_plan(ctx: PipelineParametersHandler) -> None:
    namespace_names = split_multi_value_param(ctx.params.get("NAMESPACE_NAMES") or "")

    if namespace_names:
        reduced_deploy_plan = DeploymentPlanGeneratorCommand.filter(
            deploy_plan=ctx.deploy_plan,
            namespace_filter=";".join(f"!{ns}" for ns in namespace_names),
        )
        reduced_entities = reduced_deploy_plan.entities
    else:
        reduced_entities = []

    ctx.deploy_plan = EnvgeneDeployPlan(entities=reduced_entities)
    ctx.deploy_plan.write()
