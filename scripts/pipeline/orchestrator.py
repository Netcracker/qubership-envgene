import os
import sys
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from os import getenv

from envgenehelper import logger, decrypt_all_cred_files_for_env, encrypt_all_cred_files_for_env, validate_creds, validate_parameters
from envgenehelper.business_helper import is_inventory_generation_needed
from envgenehelper.plugin_engine import PluginEngine
from envgenehelper.effective_set_helper import GenerationMode, resolve_partial_merge_mode, is_committed_sd_enabled, \
    apply_no_sd_mode
from envgenehelper.sd_helper import SD_FILE_NAME, DELTA_SD_FILE_NAME, get_sd_dir

from bg_manage.bg_manage import run_change_bg_state, run_warmup
from build_env.appregdef_render import run_appregdef_render
from build_env.namespace_render import compute_namespace_map
from build_env.env_template.set_template_version import update_version
from build_env.main import run_build_environment
from cloud_passport.main import run_cloud_passport
from creds_rotation.creds_rotation_handler import run_cred_rotation
from effective_set.effective_set_entrypoint import run_gitlab_deploy_effective_set, run_legacy_sd_effective_set
from effective_set.sboms_retention_policy import sboms_retention_policy
from deployment_plan.process_deployment_plan import merge_deployment_plan, reduce_deployment_plan
from envgenehelper.models import TemplateVersionUpdateMode, OperationType
from git_commit.git_commit import git_commit
from inventory.env_inventory_generation import run_inventory_generation
from pipeline.multi_env_runner import fan_out
from pipeline.pipeline_parameters import PipelineParametersHandler
from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.deploy_plan_adapter import adapt_sd_to_deploy_plan, EnvgeneDeployPlan
from sd.process_sd import handle_sd


class StepStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class StepResult:
    name: str
    status: StepStatus
    duration_ms: int | None = None


class PipelineStep(ABC):

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def should_run(self, ctx: PipelineParametersHandler) -> bool: ...

    @abstractmethod
    def execute(self, ctx: PipelineParametersHandler) -> None: ...


class PassportStep(PipelineStep):

    @property
    def name(self) -> str:
        return "get_passport"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        get_passport = bool(ctx.params.get('GET_PASSPORT'))
        return get_passport

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_cloud_passport()


class CredentialRotationStep(PipelineStep):
    @property
    def name(self) -> str:
        return "credential_rotation"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        cred_rotation = ctx.params.get("CRED_ROTATION_PAYLOAD")
        if cred_rotation and ctx.params.get('GET_PASSPORT'):
            raise ValueError("CRED_ROTATION_PAYLOAD and GET_PASSPORT cannot be used together")
        return cred_rotation

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_cred_rotation()


class ChangeBgState(PipelineStep):
    @property
    def name(self) -> str:
        return "change_bg_state"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return (ctx.is_gitlab_deploy()
                and OperationType(ctx.params.get('OPERATION_TYPE')) == OperationType.BGD)

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_change_bg_state(ctx)


class WarmupStep(PipelineStep):
    @property
    def name(self) -> str:
        return "warmup"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return ctx.is_gitlab_deploy() and ctx.is_bgd_warmup()

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_warmup(ctx)


class InventoryGenerationStep(PipelineStep):
    @property
    def name(self) -> str:
        return "env_inventory_generation"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return is_inventory_generation_needed(ctx.params)

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_inventory_generation(ctx)


class ProcessSdStep(PipelineStep):
    @property
    def name(self) -> str:
        return "process_sd"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        if ctx.is_gitlab_deploy() or OperationType(ctx.params.get('OPERATION_TYPE')) != OperationType.DEPLOY:
            return False
        sd_version = ctx.params.get("SD_VERSION")
        sd_data = ctx.params.get("SD_DATA")
        if sd_version and sd_data:
            raise ValueError("SD_VERSION and SD_DATA cannot be provided at the same time")
        return bool(sd_version or sd_data)

    def execute(self, ctx: PipelineParametersHandler) -> None:
        handle_sd(ctx)
        if ctx.es_generation_mode == GenerationMode.PARTIAL:
            ctx.partial_merge_mode = resolve_partial_merge_mode()


class MigrateSdToDeployPlanStep(PipelineStep):
    @property
    def name(self) -> str:
        return "migrate_sd_to_deploy_plan"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        if ctx.is_gitlab_deploy():
            return False
        sd_version = ctx.params.get("SD_VERSION")
        sd_data = ctx.params.get("SD_DATA")
        if sd_version and sd_data:
            raise ValueError("SD_VERSION and SD_DATA cannot be provided at the same time")
        if sd_version or sd_data:
            return True
        if not is_committed_sd_enabled():
            logger.info("Skipping SD migration: use_committed_sd=false, no incoming SD (No-SD Mode)")
            return False
        needs_migration = get_sd_dir().joinpath(SD_FILE_NAME).is_file() and not EnvgeneDeployPlan.path().is_file()
        if needs_migration:
            logger.info("No new SD input this run, but sd.yaml exists without a deploy-plan.yml yet - "
                        "migrating it to deploy-plan.yml")
        return needs_migration

    def execute(self, ctx: PipelineParametersHandler) -> None:
        ctx.deploy_plan = adapt_sd_to_deploy_plan(ctx.namespace_by_deploy_postfix, SD_FILE_NAME)
        ctx.deploy_plan_delta = adapt_sd_to_deploy_plan(
            ctx.namespace_by_deploy_postfix, DELTA_SD_FILE_NAME, output_path=EnvgeneDeployPlan.delta_path())


class SetTemplateVersionStep(PipelineStep):
    @property
    def name(self) -> str:
        return "set_template_version"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return bool(ctx.params.get('ENV_TEMPLATE_VERSION'))

    def execute(self, ctx: PipelineParametersHandler) -> None:
        env_instances_dir = ctx.work_dir / "environments" / ctx.cluster_name / ctx.env_name
        update_version(
            env_instances_dir,
            ctx.params.get('ENV_TEMPLATE_VERSION'),
            TemplateVersionUpdateMode(ctx.params.get('ENV_TEMPLATE_VERSION_UPDATE_MODE'))
        )


def should_run_appregdef_and_env_build(ctx: PipelineParametersHandler) -> bool:
    return ctx.is_gitlab_deploy() or bool(ctx.params.get('ENV_BUILDER'))


class AppregdefRenderStep(PipelineStep):
    @property
    def name(self) -> str:
        return "appregdef_render"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return should_run_appregdef_and_env_build(ctx)

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_appregdef_render()


class DeployPostfixNamespaceMapStep(PipelineStep):
    @property
    def name(self) -> str:
        return "deploy_postfix_namespace_map"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return ctx.is_gitlab_deploy() and OperationType(ctx.params.get('OPERATION_TYPE')) == OperationType.DEPLOY

    def execute(self, ctx: PipelineParametersHandler) -> None:
        ctx.namespace_by_deploy_postfix = compute_namespace_map()


class ProcessDeploymentPlanStep(PipelineStep):
    @property
    def name(self) -> str:
        return "process_deployment_plan"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return ctx.is_gitlab_deploy() and ctx.is_deploy_or_clean()

    def execute(self, ctx: PipelineParametersHandler) -> None:
        if OperationType(ctx.params.get('OPERATION_TYPE')) == OperationType.CLEAN:
            reduce_deployment_plan(ctx)
        else:
            merge_deployment_plan(ctx)


class EnvBuildStep(PipelineStep):
    @property
    def name(self) -> str:
        return "env_build"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        if ctx.params.get('ENV_BUILDER'):
            return True
        return ctx.is_gitlab_deploy() and ctx.is_deploy_or_clean()

    def execute(self, ctx: PipelineParametersHandler) -> None:
        ctx.namespace_by_deploy_postfix = run_build_environment()


class GenerateEffectiveSetStep(PipelineStep):
    @property
    def name(self) -> str:
        return "generate_effective_set"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        will_run = bool(ctx.params.get('GENERATE_EFFECTIVE_SET')) or (
            ctx.is_gitlab_deploy() and (ctx.is_deploy_or_clean() or ctx.is_bgd_warmup())
        )
        if not will_run and ctx.params.get('CUSTOM_PARAMS'):
            logger.warning("'CUSTOM_PARAMS' is set but generate_effective_set is not running - CUSTOM_PARAMS has no effect here")
        return will_run

    def execute(self, ctx: PipelineParametersHandler) -> None:
        decrypt_all_cred_files_for_env()
        validate_creds()
        validate_parameters()
        if not ctx.is_gitlab_deploy():
            apply_no_sd_mode(ctx)
        sboms_retention_policy()
        get_sboms = PluginEngine(plugins_dir='/module/scripts/plugins/get_sboms')
        if get_sboms.modules:
            get_sboms.run(ctx.resolve_source_dp())
        if ctx.is_gitlab_deploy():
            run_gitlab_deploy_effective_set(ctx)
        else:
            run_legacy_sd_effective_set(ctx)
        encrypt_all_cred_files_for_env()


class GitCommitStep(PipelineStep):
    @property
    def name(self) -> str:
        return "git_commit"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return True

    def execute(self, ctx: PipelineParametersHandler) -> None:
        git_commit()


def run_single_env_pipeline() -> None:
    logging.basicConfig(level=getenv("ENVGENE_LOG_LEVEL", "INFO").upper())

    ctx = PipelineParametersHandler.from_env()
    ctx.log_pipeline_params()
    ctx.write_dotenv()

    steps: list[PipelineStep] = [
        PassportStep(),
        CredentialRotationStep(),
        ChangeBgState(),
        WarmupStep(),
        InventoryGenerationStep(),
        SetTemplateVersionStep(),
        AppregdefRenderStep(),
        DeployPostfixNamespaceMapStep(),
        ProcessSdStep(),
        MigrateSdToDeployPlanStep(),
        ProcessDeploymentPlanStep(),
        EnvBuildStep(),
        GenerateEffectiveSetStep(),
        GitCommitStep()
    ]

    results: list[StepResult] = []
    try:
        for step in steps:
            if not step.should_run(ctx):
                logger.info(f"Step '{step.name}' skipped.")
                results.append(StepResult(step.name, StepStatus.SKIPPED))
                continue

            logger.info(f"========== START: {step.name} ==========")
            start = time.time_ns()
            status = StepStatus.SUCCESS
            try:
                step.execute(ctx)
            except Exception:
                status = StepStatus.FAILED
                raise
            finally:
                duration_ms = (time.time_ns() - start) // 1_000_000
                results.append(StepResult(step.name, status, duration_ms))
                logger.info(f"========== END: {step.name} ({_format_duration(duration_ms)}) - {status} ==========")
    finally:
        log_pipeline_summary(results)


def dispatch() -> int:
    env_names = split_multi_value_param(os.environ["ENV_NAMES"])
    if len(env_names) == 1:
        run_single_env_pipeline()
        return 0

    os.environ["ENV_NAMES"] = env_names[0]
    handler = PipelineParametersHandler.from_env()
    handler.write_dotenv(exclude_keys={"ENV_NAMES"})

    return fan_out(env_names)


def _format_duration(duration_ms: int | None) -> str:
    if duration_ms is None:
        return "-"
    return f"{duration_ms}ms ({duration_ms / 1000:.3f}s)"


def log_pipeline_summary(results: list[StepResult]) -> None:
    name_width = max((len(r.name) for r in results), default=0)
    lines = ["========== PIPELINE SUMMARY =========="]
    for r in results:
        lines.append(f"{r.name.ljust(name_width)}  {r.status:<7}  {_format_duration(r.duration_ms)}")
    total_ms = sum(r.duration_ms for r in results if r.duration_ms is not None)
    lines.append(f"Total: {_format_duration(total_ms)}")
    lines.append("========================================")
    logger.info("\n".join(lines))


if __name__ == "__main__":
    sys.exit(dispatch())
