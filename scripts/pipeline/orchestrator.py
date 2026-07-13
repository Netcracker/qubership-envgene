import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from envgenehelper import logger, decrypt_all_cred_files_for_env, encrypt_all_cred_files_for_env, validate_creds, validate_parameters
from envgenehelper.business_helper import is_inventory_generation_needed
from envgenehelper.plugin_engine import PluginEngine
from envgenehelper.effective_set_helper import resolve_es_generation_mode

from bg_manage.bg_manage import run_bg_manage
from build_env.appregdef_render import run_appregdef_render
from build_env.env_template.set_template_version import update_version
from build_env.main import run_build_environment
from cloud_passport.main import run_cloud_passport
from creds_rotation.creds_rotation_handler import run_cred_rotation
from effective_set.effective_set_entrypoint import effective_set_entrypoint
from effective_set.sboms_retention_policy import sboms_retention_policy
from envgenehelper.models import TemplateVersionUpdateMode
from git_commit.git_commit import git_commit
from inventory.env_inventory_generation import run_inventory_generation
from pipeline.pipeline_parameters import PipelineParametersHandler
from sd.process_sd import handle_sd, resolve_sd_parameters


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


class BgManageStep(PipelineStep):
    @property
    def name(self) -> str:
        return "bg_manage"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return bool(ctx.params.get('BG_MANAGE'))

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_bg_manage()


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
        application_versions = resolve_sd_parameters(ctx)
        if application_versions:
            ctx.es_generation_mode = resolve_es_generation_mode(ctx.cluster_name, ctx.env_name)
        return bool(application_versions)

    def execute(self, ctx: PipelineParametersHandler) -> None:
        handle_sd(ctx)


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


class AppregdefRenderStep(PipelineStep):
    @property
    def name(self) -> str:
        return "appregdef_render"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return bool(ctx.params.get('ENV_BUILDER'))

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_appregdef_render()


class EnvBuildStep(PipelineStep):
    @property
    def name(self) -> str:
        return "env_build"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return bool(ctx.params.get('ENV_BUILDER'))

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_build_environment()


class GenerateEffectiveSetStep(PipelineStep):
    @property
    def name(self) -> str:
        return "generate_effective_set"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        if not ctx.params.get('GENERATE_EFFECTIVE_SET'):
            if ctx.params.get('CUSTOM_PARAMS'):
                logger.warning(
                    "'CUSTOM_PARAMS' is only applied when GENERATE_EFFECTIVE_SET is 'true'. "
                    "If 'GENERATE_EFFECTIVE_SET' is 'false', CUSTOM_PARAMS has no effect")
            return False
        return True

    def execute(self, ctx: PipelineParametersHandler) -> None:
        decrypt_all_cred_files_for_env()
        validate_creds()
        validate_parameters()
        sboms_retention_policy()
        get_sboms = PluginEngine(plugins_dir='/module/scripts/plugins/get_sboms')
        if get_sboms.modules:
            get_sboms.run()
        effective_set_entrypoint()
        encrypt_all_cred_files_for_env()


class GitCommitStep(PipelineStep):
    @property
    def name(self) -> str:
        return "git_commit"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return True

    def execute(self, ctx: PipelineParametersHandler) -> None:
        git_commit()


def run_unified_pipeline() -> None:
    ctx = PipelineParametersHandler.from_env()
    ctx.log_pipeline_params()
    ctx.write_dotenv()

    steps: list[PipelineStep] = [
        PassportStep(),
        CredentialRotationStep(),
        BgManageStep(),
        InventoryGenerationStep(),
        SetTemplateVersionStep(),
        AppregdefRenderStep(),
        ProcessSdStep(),
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
    run_unified_pipeline()
