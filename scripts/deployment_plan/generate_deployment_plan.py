import os
from pathlib import Path

from dpg.v1.cmd import DeploymentPlanGeneratorCommand
from dpg.v1.internal.deployment_plan import DeploymentPlanCalculator
from envgenehelper import logger
from envgenehelper.business_helper import get_version
from envgenehelper.collections_helper import split_multi_value_param

from build_env.namespace_render import NAMESPACE_MAP_FILE
from envgenehelper.deploy_plan_adapter import DEPLOY_PLAN_FILE_NAME, EnvgeneDeployPlan
from pipeline.pipeline_parameters import PipelineParametersHandler

_INTERMEDIATE_PLAN_FILE = "deploy-plan-calculated.yml"


def _inventory_dir(ctx: PipelineParametersHandler) -> Path:
    return ctx.work_dir / "environments" / ctx.cluster_name / ctx.env_name / "Inventory"


def _parse_applications(application_versions: str) -> list[str]:
    application_versions = application_versions.replace("\\n", "\n")
    applications = split_multi_value_param(application_versions)
    if not applications:
        raise ValueError("APPLICATION_VERSIONS is empty")
    return applications


def _resolve_app_name(application: str) -> str:
    if application.endswith((".yaml", ".yml", ".json")):
        return application
    parsed = DeploymentPlanCalculator._parse_app(application)
    name, _ = get_version(parsed["version"])
    return name


def _appdef_paths(appdefs_dir: Path, app_name: str) -> list[Path]:
    base = appdefs_dir / app_name
    return [Path(f"{base}{ext}") for ext in (".yml", ".yaml")]


def _find_appdef(*appdefs_dirs: Path, app_name: str) -> Path | None:
    for appdefs_dir in appdefs_dirs:
        for candidate in _appdef_paths(appdefs_dir, app_name):
            if candidate.is_file():
                return candidate
    return None


def _validate_appdefs(ctx: PipelineParametersHandler, applications: list[str]) -> None:
    env_appdefs = (
        ctx.work_dir / "environments" / ctx.cluster_name / ctx.env_name / "AppDefs"
    )
    repo_appdefs = ctx.work_dir / "appdefs"
    missing = []

    for application in applications:
        app_name = _resolve_app_name(application)
        if app_name.endswith((".yaml", ".yml", ".json")):
            continue

        if _find_appdef(env_appdefs, repo_appdefs, app_name=app_name) is None:
            missing.append(app_name)

    if missing:
        raise FileNotFoundError(
            f"Missing AppDefs for requested applications: {', '.join(sorted(missing))}"
        )


def run_generate_deployment_plan(ctx: PipelineParametersHandler) -> None:
    application_versions = ctx.params.get("APPLICATION_VERSIONS")
    if not application_versions:
        raise ValueError("APPLICATION_VERSIONS is required when PIPELINE_TYPE=GITLAB_DEPLOY")

    inventory_dir = _inventory_dir(ctx)
    namespace_map_path = inventory_dir / NAMESPACE_MAP_FILE
    if not namespace_map_path.is_file():
        raise FileNotFoundError(f"Missing namespace map at {namespace_map_path}")

    applications = _parse_applications(application_versions)
    _validate_appdefs(ctx, applications)

    os.environ.setdefault("LOCAL_APPDEFS_PATH", "appdefs")
    os.environ.setdefault("LOCAL_REGDEFS_PATH", "regdefs")

    intermediate_plan_path = inventory_dir / _INTERMEDIATE_PLAN_FILE
    deploy_plan_path = inventory_dir / DEPLOY_PLAN_FILE_NAME

    logger.info(f"Calculating deployment plan for {len(applications)} application(s)")
    DeploymentPlanGeneratorCommand.calculate(
        applications=applications,
        output_file=intermediate_plan_path,
        rootdir=ctx.work_dir,
    )

    logger.info(f"Mapping namespaces from {namespace_map_path}")
    deploy_plan = DeploymentPlanGeneratorCommand.map(
        deploy_plan=intermediate_plan_path,
        map=namespace_map_path,
        output_file=deploy_plan_path,
    )
    ctx.deploy_plan = EnvgeneDeployPlan(entities=deploy_plan.entities)

    intermediate_plan_path.unlink(missing_ok=True)
    logger.info(f"Deployment plan written to {deploy_plan_path}")
