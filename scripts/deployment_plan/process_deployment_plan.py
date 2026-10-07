from dpg.v1.cmd import DeploymentPlanGeneratorCommand
from dpg.v1.internal.deployment_plan.deployment_plan import DeploymentPlanCalculator
from envgenehelper.business_helper import (
    get_current_env_dir_from_env_vars,
    INVENTORY_DIR_NAME,
    parse_bg_ns_target,
)
from envgene_shared.utils.collections_utils import split_multi_value_param
from envgene_shared.utils.yaml_utils import openYaml, writeYamlToFile
from envgenehelper.deploy_plan_adapter import EnvgeneDeployPlan, resolve_namespace_entry

from build_env.namespace_render import NAMESPACE_MAP_FILE
from pipeline.pipeline_parameters import PipelineParametersHandler

_INTERMEDIATE_CALCULATED_FILE = "deploy-plan-calculated.yml"
_INTERMEDIATE_MAPPED_FILE = "deploy-plan-mapped.yml"


def bind_namespaces(deploy_plan, namespace_map: dict, bg_ns_target):
    bound_plan = deploy_plan.model_copy(deep=True)

    for entity in bound_plan.entities:
        if entity.deploy_postfix:
            namespace_entry = namespace_map.get(entity.deploy_postfix)
            if namespace_entry is None:
                raise ValueError(
                    f"deployPostfix '{entity.deploy_postfix}' is not present in the namespace map"
                )
            entity.namespace = resolve_namespace_entry(
                namespace_entry,
                bg_ns_target,
                entity.deploy_postfix,
            )
            continue

        for deploy_postfix, namespace_entry in namespace_map.items():
            if namespace_entry == entity.namespace or (
                isinstance(namespace_entry, dict) and entity.namespace in namespace_entry.values()
            ):
                entity.deploy_postfix = deploy_postfix
                break
        else:
            raise ValueError(
                f"namespace '{entity.namespace}' is not present in the namespace map"
            )

    return bound_plan


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
    namespace_map = openYaml(namespace_map_path, allow_default=True, default_yaml=dict) or {}
    deploy_plan = bind_namespaces(
        calculated_plan,
        namespace_map,
        parse_bg_ns_target(ctx.params.get("BG_NS_TARGET")),
    )
    writeYamlToFile(mapped_plan_path, deploy_plan.to_dict())

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
