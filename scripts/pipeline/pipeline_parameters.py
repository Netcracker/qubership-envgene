import copy
import json
import os
import shlex
import uuid
from os import getenv
from pathlib import Path
from typing import Self

from envgenehelper import getenv_with_error, writeToFile, get_schema_dir
from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.effective_set_helper import GenerationMode
from envgenehelper.models import TemplateVersionUpdateMode, OperationType
from envgenehelper.plugin_engine import PluginEngine
from envgenehelper import logger
from pydantic import BaseModel, Field


class PipelineParametersHandler(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    params: dict
    sensitive_params: list
    full_env_name: str
    cluster_name: str
    env_name: str
    es_generation_mode: GenerationMode = GenerationMode.PARTIAL
    work_dir: Path = Field(default_factory=lambda: Path(getenv('CI_PROJECT_DIR')))
    dotenv_path: Path = Field(default_factory=lambda: Path(f"{getenv('CI_PROJECT_DIR')}/build.env"))

    @classmethod
    def from_env(cls) -> Self:
        params = {
            'ENV_NAMES': getenv("ENV_NAMES", ""),
            'ENV_BUILD': getenv("ENV_BUILD", "false").lower() == "true",
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
        params = copy.deepcopy(self.params)
        if params.get("CRED_ROTATION_PAYLOAD"):
            params["CRED_ROTATION_PAYLOAD"] = "***"

        env_inventory_content = params.get("ENV_INVENTORY_CONTENT")
        if env_inventory_content:
            parsed = json.loads(env_inventory_content)
            self._hide_secrets(parsed)
            params["ENV_INVENTORY_CONTENT"] = json.dumps(parsed, separators=(",", ":"))

        params_str = "Input parameters are: " + "".join(f"\n{k.upper()}: {v}" for k, v in params.items())
        logger.info(params_str)

    def write_dotenv(self) -> None:
        internal = {
            'CLUSTER_NAME': self.cluster_name,
            'ENV_NAME': self.full_env_name,
            'ENVIRONMENT_NAME': self.env_name,
            'FULL_ENV_NAME': self.full_env_name,
        }
        lines = []
        for key, value in {**self.params, **internal}.items():
            if value is None or key in self.sensitive_params:
                continue
            value = str(value)
            if "\n" in value:
                raise ValueError(f"Newlines are not allowed in dotenv values: {key}.")
            lines.append(f"{key}={shlex.quote(value)}")
        writeToFile(self.dotenv_path, "\n".join(lines))

    def _hide_secrets(self, data) -> None:
        if isinstance(data, dict):
            for k, v in data.items():
                if k.lower() in {"username", "password", "secret"}:
                    data[k] = "***"
                else:
                    self._hide_secrets(v)
        elif isinstance(data, list):
            for item in data:
                self._hide_secrets(item)
