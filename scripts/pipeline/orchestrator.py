import copy
import json
import os
import shlex
import time
import uuid
from abc import ABC, abstractmethod
from os import getenv
from pathlib import Path

from envgenehelper import logger, getenv_with_error, writeToFile, get_schema_dir
from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.effective_set_helper import GenerationMode, resolve_es_generation_mode
from envgenehelper.models import TemplateVersionUpdateMode, OperationType
from envgenehelper.plugin_engine import PluginEngine
from pydantic import BaseModel, Field

from envgenehelper.business_helper import is_inventory_generation_needed
from envgenehelper.validations import real_execution_checks
from scripts.bg_manage.bg_manage import run_bg_manage
from scripts.build_env.appregdef_render import run_appregdef_render
from scripts.build_env.main import run_build_environment
from scripts.cloud_passport.main import run_cloud_passport
from scripts.creds_rotation.creds_rotation_handler import run_cred_rotation
from scripts.effective_set.effective_set_entrypoint import effective_set_entrypoint
from scripts.inventory.env_inventory_generation import run_inventory_generation
from scripts.sd.process_sd import handle_sd


class PipelineParametersHandler(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    params: dict
    sensitive_params: list
    full_env_name: str
    cluster_name: str
    env_name: str
    # templates_dirs: dict
    es_generation_mode: GenerationMode = GenerationMode.PARTIAL
    work_dir: Path = Field(default_factory=lambda: Path(getenv('CI_PROJECT_DIR')))
    dotenv_path: Path = Field(default_factory=lambda: Path(f"{getenv('CI_PROJECT_DIR')}/build.env"))

    @classmethod
    def from_env(cls) -> 'PipelineParametersHandler':
        params = {
            'ENV_NAMES': getenv("ENV_NAMES", ""),
            'ENV_BUILD': getenv("ENV_BUILDER", "false").lower() == "true",
            'GET_PASSPORT': getenv("GET_PASSPORT", "false").lower() == "true",
            'GENERATE_EFFECTIVE_SET': getenv("GENERATE_EFFECTIVE_SET", "false").lower() == "true",
            'ENV_TEMPLATE_VERSION': getenv("ENV_TEMPLATE_VERSION", ""),
            'ENV_TEMPLATE_TEST': getenv("ENV_TEMPLATE_TEST", "false").lower() == "true",
            'IS_TEMPLATE_TEST': getenv("ENV_TEMPLATE_TEST", "false").lower() == "true",
            'CI_COMMIT_REF_NAME': getenv("CI_COMMIT_REF_NAME", ""),
            'JSON_SCHEMAS_DIR': get_schema_dir(),
            "SD_SOURCE_TYPE": getenv("SD_SOURCE_TYPE", "artifact"),
            "SD_VERSION": getenv("SD_VERSION"),
            "SD_DATA": getenv("SD_DATA"),
            "SD_DELTA": getenv("SD_DELTA"),
            "SD_REPO_MERGE_MODE": getenv("SD_REPO_MERGE_MODE"),
            "ENV_INVENTORY_INIT": getenv("ENV_INVENTORY_INIT", "false").lower() == "true",
            "ENV_SPECIFIC_PARAMS": getenv("ENV_SPECIFIC_PARAMS"),
            "ENV_TEMPLATE_NAME": getenv("ENV_TEMPLATE_NAME"),
            'CRED_ROTATION_FORCE': getenv("CRED_ROTATION_FORCE", "false"),
            'NS_BUILD_FILTER': getenv("NS_BUILD_FILTER", ""),
            'GITLAB_RUNNER_TAG_NAME': getenv("GITLAB_RUNNER_TAG_NAME", ""),
            'RUNNER_SCRIPT_TIMEOUT': getenv("RUNNER_SCRIPT_TIMEOUT", "10m"),
            'DEPLOYMENT_SESSION_ID': getenv("DEPLOYMENT_SESSION_ID", str(uuid.uuid4())),
            'ENVGENE_LOG_LEVEL': getenv("ENVGENE_LOG_LEVEL", "INFO"),
            'CALCULATOR_CLI_JAVA_OPTIONS': getenv("CALCULATOR_CLI_JAVA_OPTIONS", ""),
            "BG_STATE": getenv("BG_STATE"),
            "BG_MANAGE": getenv("BG_MANAGE", "false").lower() == "true",
            "APP_DEFS_PATH": getenv("APP_DEFS_PATH"),
            "REG_DEFS_PATH": getenv("REG_DEFS_PATH"),
            "APP_REG_DEFS_JOB": getenv("APP_REG_DEFS_JOB"),
            "EFFECTIVE_SET_CONFIG": getenv("EFFECTIVE_SET_CONFIG"),
            "ENV_INVENTORY_CONTENT": getenv("ENV_INVENTORY_CONTENT"),
            "CUSTOM_PARAMS": getenv("CUSTOM_PARAMS"),
            "ENV_TEMPLATE_VERSION_UPDATE_MODE": getenv(
                "ENV_TEMPLATE_VERSION_UPDATE_MODE", TemplateVersionUpdateMode.PERSISTENT.value),
            "OPERATION_TYPE": getenv("OPERATION_TYPE", OperationType.DEPLOY.value),
            "NAMESPACE_NAMES": getenv("NAMESPACE_NAMES", ""),
        }

        pipe_param_plugin = PluginEngine(plugins_dir='/module/scripts/pipegene_plugins/pipe_parameters')
        if pipe_param_plugin.modules:
            pipe_param_plugin.run(pipeline_params=params)

        for k, v in params.items():
            try:
                parsed = json.loads(v)
                params[k] = json.dumps(parsed, separators=(",", ":"))
            except (TypeError, ValueError):
                pass

        env_names = split_multi_value_param(getenv_with_error("ENV_NAMES"))
        if len(env_names) != 1:
            raise ValueError(f"ENV_NAMES must contain exactly one value, got: {env_names}")
        if os.getenv("ENV_TEMPLATE_TEST") == "true":
            raise ValueError("ENV_TEMPLATE_TEST is not supported for static pipeline")

        for k, v in params.items():
            if v is not None:
                os.environ[k] = str(v)

        # real_execution_checks

        full_env_name = env_names[0]
        cluster_name, env_name = full_env_name.split("/")
        sensitive_params = ["CRED_ROTATION_PAYLOAD", "ENV_INVENTORY_CONTENT"]
        return cls(
            params=params,
            sensitive_params=sensitive_params,
            full_env_name=full_env_name,
            cluster_name=cluster_name,
            env_name=env_name
        )

    def log_pipeline_params(self) -> None:
        params_str = "Input parameters are: "

        params = copy.deepcopy(self.params)
        if params.get("CRED_ROTATION_PAYLOAD"):
            params["CRED_ROTATION_PAYLOAD"] = "***"

        env_inventory_content = params.get("ENV_INVENTORY_CONTENT")
        if env_inventory_content:
            parsed = json.loads(env_inventory_content)
            self.hide_secrets(parsed)
            # remove spaces
            params["ENV_INVENTORY_CONTENT"] = json.dumps(parsed, separators=(",", ":"))

        for k, v in params.items():
            params_str += f"\n{k.upper()}: {v}"

        logger.info(params_str)

    def write_dotenv(self):
        lines = []
        for key, value in {**self.params, **self.internal_params}.items():
            if value is None:
                continue
            if key in self.sensitive_params:
                continue
            value = str(value)
            if "\n" in value:
                raise ValueError(f"Newlines are not allowed in dotenv values: {key}. Make parameter 1 line")
            lines.append(f"{key}={shlex.quote(value)}")
        writeToFile(self.dotenv_path, "\n".join(lines))

    def hide_secrets(self, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if k.lower() in {"username", "password", "secret"}:
                    data[k] = "***"
                else:
                    self.hide_secrets(v)
        elif isinstance(data, list):
            for item in data:
                self.hide_secrets(item)


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
        source_type = (ctx.params.get("SD_SOURCE_TYPE")).lower()
        has_sd = (
                (source_type == "json" and bool(ctx.params.get("SD_DATA"))) or
                (source_type == "artifact" and bool(ctx.params.get("SD_VERSION")))
        )
        if has_sd:
            ctx.es_generation_mode = resolve_es_generation_mode(ctx.cluster_name, ctx.env_name)
        return has_sd

    def execute(self, ctx: PipelineParametersHandler) -> None:
        handle_sd(ctx)


class AppregdefRenderStep(PipelineStep):
    @property
    def name(self) -> str:
        return "appregdef_render"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return bool(ctx.params.get('ENV_BUILD'))

    def execute(self, ctx: PipelineParametersHandler) -> None:
        run_appregdef_render()


class EnvBuildStep(PipelineStep):
    @property
    def name(self) -> str:
        return "env_build"

    def should_run(self, ctx: PipelineParametersHandler) -> bool:
        return bool(ctx.params.get('ENV_BUILD'))

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
        effective_set_entrypoint()

#TODO after refactor git_commit.sh

# class GitCommitStep(PipelineStep):
#     requires_git_commit = False
#
#     @property
#     def name(self) -> str:
#         return "git_commit"
#
#     def should_run(self, ctx: PipelineParametersHandler) -> bool:
#         return self.requires_git_commit
#
#     def execute(self, ctx: PipelineParametersHandler) -> None:
#         run_git_commit()


def run_unified_pipeline() -> None:
    ctx = PipelineParametersHandler.from_env()
    ctx.log_params()
    ctx.write_dotenv()

    steps: list[PipelineStep] = [
        PassportStep(),
        CredentialRotationStep(),
        BgManageStep(),
        InventoryGenerationStep(),
        AppregdefRenderStep(),
        ProcessSdStep(),
        EnvBuildStep(),
        GenerateEffectiveSetStep()
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


if __name__ == "__main__":
    run_unified_pipeline()
