import copy
import json
import os
import shlex
import uuid
from os import getenv
from pathlib import Path

from envgenehelper import logger
from envgenehelper import writeToFile, getenv_with_error, split_multi_value_param, get_schema_dir
from envgenehelper.models import TemplateVersionUpdateMode, OperationType
from envgenehelper.plugin_engine import PluginEngine
from envgenehelper.validations import real_execution_checks


def get_pipeline_parameters() -> dict:
    return {
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
        "NAMESPACE_NAMES": getenv("NAMESPACE_NAMES", "")
    }


def get_sensitive_param_names() -> list:
    return [
        "CRED_ROTATION_PAYLOAD",
        "ENV_INVENTORY_CONTENT",
    ]


def get_internal_pipe_params() -> dict:
    return {
        'CLUSTER_NAME': getenv("CLUSTER_NAME"),
        'ENV_NAME': getenv("ENV_NAME"),
        'ENVIRONMENT_NAME': getenv("ENVIRONMENT_NAME"),
        'FULL_ENV_NAME': getenv("FULL_ENV_NAME"),
    }


class PipelineParametersHandler:
    dotenv_path = Path(f"{getenv_with_error('CI_PROJECT_DIR')}/build.env")

    def __init__(self, **kwargs):
        plugins_dir = '/module/scripts/pipegene_plugins/pipe_parameters'
        self.params = get_pipeline_parameters()
        self.sensitive_params = get_sensitive_param_names()
        self.internal_params = get_internal_pipe_params()
        pipe_param_plugin = PluginEngine(plugins_dir=plugins_dir)

        if pipe_param_plugin.modules:
            pipe_param_plugin.run(pipeline_params=self.params)

        for k, v in self.params.items():
            try:
                parsed = json.loads(v)
                self.params[k] = json.dumps(parsed, separators=(",", ":"))

            except (TypeError, ValueError):
                pass

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

    def log_pipeline_params(self):
        params_str = "Input parameters are: "

        params = copy.deepcopy(self.params)
        if params.get("CRED_ROTATION_PAYLOAD"):
            params["CRED_ROTATION_PAYLOAD"] = "***"

        env_inventory_content = params.get("ENV_INVENTORY_CONTENT")
        if env_inventory_content:
            parsed = json.loads(env_inventory_content)
            self.hide_secrets(parsed)
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

    def init_pipe_params(self):
        env_names = split_multi_value_param(getenv_with_error("ENV_NAMES"))

        if len(env_names) != 1:
            raise ValueError(f"ENV_NAMES must contain exactly one value, got: {env_names}")

        if os.getenv("ENV_TEMPLATE_TEST") == "true" or os.getenv("IS_TEMPLATE_TEST") == "true":
            raise ValueError("ENV_TEMPLATE_TEST is not supported for static pipeline")

        for k, v in self.params.items():
            if v is not None:
                os.environ[k] = str(v)

        real_execution_checks(
            self.params["ENV_NAMES"],
            self.params["GET_PASSPORT"],
            self.params["ENV_BUILD"],
            self.params["ENV_INVENTORY_INIT"],
            self.params["ENV_INVENTORY_CONTENT"]
        )

        env = env_names[0]
        cluster, environment = env.split("/")
        os.environ["CLUSTER_NAME"] = cluster
        os.environ["ENV_NAME"] = env
        os.environ["ENVIRONMENT_NAME"] = environment
        os.environ["FULL_ENV_NAME"] = env

        self.internal_params["CLUSTER_NAME"] = cluster
        self.internal_params["ENV_NAME"] = env
        self.internal_params["ENVIRONMENT_NAME"] = environment
        self.internal_params["FULL_ENV_NAME"] = env

        self.write_dotenv()
