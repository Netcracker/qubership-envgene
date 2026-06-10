import time
from abc import ABC, abstractmethod
from os import getenv
from pathlib import Path

from pydantic import BaseModel, Field

from appregdef_render import render_app_reg_defs
from bg_manage import run as run_bg_manage
from cloud_passport.scripts.main import run as run_passport
from cred_rotation import run as run_cred_rotation
from effective_set_entrypoint import effective_set_entrypoint
from env_inventory_generation import run as run_inventory_generation
from envgenehelper import logger, getenv_with_error
from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.effective_set_helper import GenerationMode, resolve_es_generation_mode
from git_commit import run as run_git_commit
from inventory_generation import is_inventory_generation_needed
from main import render_environment
from process_sd import prepare_vars_and_run_sd_handling


class PipelineContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    params: dict
    full_env_name: str
    cluster_name: str
    env_name: str
    templates_dirs: dict
    es_generation_mode: GenerationMode = GenerationMode.PARTIAL
    git_commit: bool = True
    work_dir: Path = Field(default_factory=lambda: Path(getenv('CI_PROJECT_DIR')))


class PipelineStep(ABC):

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def should_run(self, ctx: PipelineContext) -> bool: ...

    @abstractmethod
    def execute(self, ctx: PipelineContext) -> None: ...


class PassportStep(PipelineStep):

    @property
    def name(self) -> str:
        return "get_passport"

    def should_run(self, ctx: PipelineContext) -> bool:
        get_passport = bool(ctx.params.get('GET_PASSPORT'))
        ctx.git_commit = False
        return get_passport

    def execute(self, ctx: PipelineContext) -> None:
        run_passport(ctx.full_env_name)


class CredentialRotationStep(PipelineStep):
    @property
    def name(self) -> str:
        return "credential_rotation"

    def should_run(self, ctx: PipelineContext) -> bool:
        cred_rotation = ctx.params.get("CRED_ROTATION_PAYLOAD")
        if cred_rotation and ctx.params.get('GET_PASSPORT'):
            raise ValueError("CRED_ROTATION_PAYLOAD and GET_PASSPORT cannot be used together")
        return cred_rotation

    def execute(self, ctx: PipelineContext) -> None:
        run_cred_rotation()


class BgManageStep(PipelineStep):
    @property
    def name(self) -> str:
        return "bg_manage"

    def should_run(self, ctx: PipelineContext) -> bool:
        return bool(ctx.params.get('BG_MANAGE'))

    def execute(self, ctx: PipelineContext) -> None:
        run_bg_manage()


class InventoryGenerationStep(PipelineStep):
    @property
    def name(self) -> str:
        return "env_inventory_generation"

    def should_run(self, ctx: PipelineContext) -> bool:
        return is_inventory_generation_needed(ctx.params)

    def execute(self, ctx: PipelineContext) -> None:
        run_inventory_generation()


class ProcessSdStep(PipelineStep):
    @property
    def name(self) -> str:
        return "process_sd"

    def should_run(self, ctx: PipelineContext) -> bool:
        source_type = (ctx.params.get("SD_SOURCE_TYPE")).lower()
        has_sd = (
            (source_type == "json" and bool(ctx.params.get("SD_DATA"))) or
            (source_type == "artifact" and bool(ctx.params.get("SD_VERSION")))
        )
        if has_sd:
            ctx.es_generation_mode = resolve_es_generation_mode(ctx.cluster_name, ctx.env_name)
        return has_sd

    def execute(self, ctx: PipelineContext) -> None:
        prepare_vars_and_run_sd_handling(
            base_dir=str(ctx.work_dir),
            env_name=ctx.env_name,
            cluster=ctx.cluster_name,
            sd_source_type=ctx.params.get('SD_SOURCE_TYPE'),
            sd_version=ctx.params.get('SD_VERSION'),
            sd_data=ctx.params.get('SD_DATA'),
            sd_delta=ctx.params.get('SD_DELTA'),
            sd_merge_mode=ctx.params.get('SD_REPO_MERGE_MODE'),
            operation_type=ctx.params.get('OPERATION_TYPE'),
        )


class AppregdefRenderStep(PipelineStep):
    @property
    def name(self) -> str:
        return "appregdef_render"

    def should_run(self, ctx: PipelineContext) -> bool:
        return bool(ctx.params.get('ENV_BUILD'))

    def execute(self, ctx: PipelineContext) -> None:
        render_app_reg_defs()


class EnvBuildStep(PipelineStep):
    @property
    def name(self) -> str:
        return "env_build"

    def should_run(self, ctx: PipelineContext) -> bool:
        return bool(ctx.params.get('ENV_BUILD'))

    def execute(self, ctx: PipelineContext) -> None:
        render_environment(
            ctx.env_name,
            ctx.cluster_name,
            ctx.templates_dirs,
            str(ctx.work_dir / 'environments'),
            str(ctx.work_dir / 'environments'),
            str(ctx.work_dir),
        )


class GenerateEffectiveSetStep(PipelineStep):
    @property
    def name(self) -> str:
        return "generate_effective_set"

    def should_run(self, ctx: PipelineContext) -> bool:
        if not ctx.params.get('GENERATE_EFFECTIVE_SET'):
            if ctx.params.get('CUSTOM_PARAMS'):
                logger.warning(
                    "'CUSTOM_PARAMS' is only applied when GENERATE_EFFECTIVE_SET is 'true'. "
                    "If 'GENERATE_EFFECTIVE_SET' is 'false', CUSTOM_PARAMS has no effect")
            return False
        return True

    def execute(self, ctx: PipelineContext) -> None:
        effective_set_entrypoint()


class GitCommitStep(PipelineStep):
    requires_git_commit = False

    @property
    def name(self) -> str:
        return "git_commit"

    def should_run(self, ctx: PipelineContext) -> bool:
        return self.requires_git_commit

    def execute(self, ctx: PipelineContext) -> None:
        run_git_commit()


def run_unified_pipeline() -> None:
    env_names = split_multi_value_param(getenv_with_error('ENV_NAMES'))
    if len(env_names) > 1:
        raise ValueError(f"Envgene pipeline supports exactly one environment, got: {env_names}")

    full_env_name = env_names[0].strip()
    cluster_name, env_name = full_env_name.split('/')

    ctx = PipelineContext(
        params=params,
        full_env_name=full_env_name,
        cluster_name=cluster_name,
        env_name=env_name,
        templates_dirs=templates_dirs
    )

    steps: list[PipelineStep] = [
        PassportStep(),
        CredentialRotationStep(),
        BgManageStep(),
        InventoryGenerationStep(),
        AppregdefRenderStep(),
        ProcessSdStep(),
        EnvBuildStep(),
        GenerateEffectiveSetStep(),
        GitCommitStep(),
    ]

    for step in steps:
        if not step.should_run(ctx):
            logger.info(f"Step '{step.name}' skipped.")
            continue

        logger.info(f"Starting step: {step.name}")
        start = time.time_ns()
        try:
            step.execute(ctx)
        finally:
            duration_ms = (time.time_ns() - start) // 1_000_000
            logger.info(f"Step '{step.name}' completed in {duration_ms}ms")
