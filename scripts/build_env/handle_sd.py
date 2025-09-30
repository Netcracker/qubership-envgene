import asyncio
import json
import os
from enum import Enum
from os import path
from pathlib import Path

import envgenehelper as helper
import yaml
from artifact_searcher import artifact
from artifact_searcher.utils import models as artifact_models
from envgenehelper.business_helper import getenv_and_log, getenv_with_error
from envgenehelper.env_helper import Environment
from envgenehelper.file_helper import identify_yaml_extension
from envgenehelper.logger import logger
from envgenehelper.plugin_engine import PluginEngine


class MergeType(Enum):
    EXTENDED = "extended-merge"
    REPLACE = "replace"
    BASIC = "basic-merge"
    BASIC_EXCLUSION = "basic-exclusion-merge"

    @classmethod
    def from_value(cls, value: str):
        if not isinstance(value, str):
            raise ValueError(f"SD_REPO_MERGE_MODE value: '{value}' cannot be non-string")
        value_lower = value.strip().lower()
        for member in cls:
            if member.value == value_lower:
                return member
        valid_values = [member.value for member in cls]
        raise ValueError(
            f"Invalid SD_REPO_MERGE_MODE: '{value}'. Valid values are: {valid_values}"
        )


MERGE_METHODS = {
    MergeType.BASIC: helper.basic_merge,
    MergeType.BASIC_EXCLUSION: helper.basic_exclusion_merge,
    MergeType.EXTENDED: helper.extended_merge
}

ENVIRONMENT_NAME = getenv_with_error('ENVIRONMENT_NAME')
CLUSTER_NAME = getenv_with_error('CLUSTER_NAME')
WORK_DIR = getenv_with_error('CI_PROJECT_DIR')
BASE_ENV_PATH = f"{WORK_DIR}/environments/{CLUSTER_NAME}/{ENVIRONMENT_NAME}"
APP_DEFS_PATH = f"{BASE_ENV_PATH}/AppDefs"
REG_DEFS_PATH = f"{BASE_ENV_PATH}/RegDefs"


def handle_deploy_postfix_namespace_transformation(sd_data: dict, namespace_dict: dict) -> dict:
    """
    Transforms the SD data before writing:
    - If userData.useDeployPostfixAsNamespace == True:
        - Replace deployPostfix with corresponding folder name from namespace_dict if exists.
        - If userData contains ONLY field useDeployPostfixAsNamespace, remove userData.
        - If other keys exist, remove only useDeployPostfixAsNamespace.
    """
    logger.info(
        f"[Pre handle_deploy_postfix_namespace_transformation] Original SD data: {json.dumps(sd_data, indent=2)}")
    user_data = sd_data.get("userData", {})

    if isinstance(user_data, dict) and user_data.get("useDeployPostfixAsNamespace") is True:
        for app in sd_data.get("applications", []):
            if "deployPostfix" in app and isinstance(app["deployPostfix"], str):
                current_postfix = app["deployPostfix"]
                replacement = namespace_dict.get(current_postfix)
                if replacement:
                    logger.info(f"Replacing deployPostfix '{current_postfix}' with '{replacement}'")
                    app["deployPostfix"] = replacement
                else:
                    logger.error(f"No replacement found for deployPostfix '{current_postfix}', cannot continue.")
                    exit(1)
        # Remove entire userData if it has only one key
        if len(user_data) == 1:
            sd_data.pop("userData", None)
        else:
            user_data.pop("useDeployPostfixAsNamespace", None)
            sd_data["userData"] = user_data  # Reassign to make sure it's updated

    return sd_data


def prepare_vars_and_run_sd_handling():
    base_dir = getenv_and_log('CI_PROJECT_DIR')
    env_name = getenv_and_log('ENV_NAME')
    cluster = getenv_and_log('CLUSTER_NAME')

    env = Environment(base_dir, cluster, env_name)

    sd_source_type = getenv_and_log('SD_SOURCE_TYPE')
    sd_version = getenv_and_log('SD_VERSION')
    sd_data = getenv_and_log('SD_DATA')
    sd_delta = getenv_and_log('SD_DELTA')
    sd_merge_mode = getenv_and_log("SD_REPO_MERGE_MODE")
    handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)


def build_namespace_dict(env) -> dict:
    namespaces_dir = f'{env.env_path}/Namespaces/'
    result = {}

    if not os.path.exists(namespaces_dir):
        logger.warning(f"Namespaces directory does not exist: {namespaces_dir}")
        return result  # Return empty dict instead of throwing an error

    # Iterate over all items in Namespaces directory
    for folder_name in os.listdir(namespaces_dir):
        folder_path = os.path.join(namespaces_dir, folder_name)
        if os.path.isdir(folder_path):
            namespace_file = os.path.join(folder_path, "namespace.yml")
            if os.path.isfile(namespace_file):
                with open(namespace_file, 'r') as f:
                    data = yaml.safe_load(f)
                    logger.info(f"Parsed content of {namespace_file}: {data}")
                # Extract 'name' property
                ns_name = data.get("name")
                logger.info(f"ns_name = {ns_name}")
                if ns_name and isinstance(ns_name, str):
                    result[ns_name] = folder_name
                else:
                    logger.warning(f"Warning: 'name' property missing or invalid in {namespace_file}")
            else:
                continue
    logger.info(f"Namespace dict built: {result}")
    return result


def merge_sd(sd_path: Path, sd_data, merge_func):
    logger.info(f"Final destination! - {sd_path}")
    full_sd_yaml = helper.openYaml(sd_path)
    logger.info(f"full_sd.yaml before merge: {full_sd_yaml}")
    helper.check_dir_exist_and_create(sd_path.parent)
    result = merge_func(full_sd_yaml, sd_data)
    helper.writeYamlToFile(sd_path, result)
    logger.info(f"Merged data into Target Path! - {result}")


def calculate_merge_mode(sd_merge_mode, sd_delta) -> MergeType:
    if sd_merge_mode is not None:
        effective_merge_mode = MergeType.from_value(sd_merge_mode)
    elif sd_delta == "true":
        effective_merge_mode = MergeType.EXTENDED
        logger.info(
            f"SD_REPO_MERGE_MODE not passed. Calculated based on SD_DELTA={sd_delta}: {effective_merge_mode.value}")
    elif sd_delta == "false":
        effective_merge_mode = MergeType.REPLACE
        logger.info(
            f"SD_REPO_MERGE_MODE not passed. Calculated based on SD_DELTA={sd_delta}: {effective_merge_mode.value}")
    else:
        effective_merge_mode = MergeType.BASIC
        logger.info(f"SD_REPO_MERGE_MODE not passed. Default value: {effective_merge_mode.value}")
    return effective_merge_mode


def calculate_sd_delta(sd_delta):
    logger.info(f"printing sd_delta before {sd_delta}")
    if sd_delta is not None and str(sd_delta).strip() != "":
        sd_delta = str(sd_delta).strip().lower()
    else:
        sd_delta = None
    logger.info(f"printing sd_delta after {sd_delta}")
    return sd_delta


def multiply_sds_to_single(sds_data):
    # Perform basic-merge for multiple SDs before applying SD_REPO_MERGE_MODE
    if isinstance(sds_data, list):
        merged_applications = {"applications": sds_data[0].get("applications", [])}
        if not merged_applications["applications"]:
            logger.error("No applications found in the first SD block.")
            exit(1)
        for i in range(1, len(sds_data)):
            logger.info("Initiates basic-merge:")
            current_item_sd = {"applications": sds_data[i].get("applications", [])}
            merged_applications = helper.merge(merged_applications, current_item_sd)
        full_sd_from_pipe = {
            "version": sds_data[0].get("version"),
            "type": sds_data[0].get("type"),
            "deployMode": sds_data[0].get("deployMode"),
            "applications": merged_applications["applications"]
        }
        logger.info(f"Level-1 SD data: {json.dumps(full_sd_from_pipe, indent=2)}")
    else:
        full_sd_from_pipe = sds_data
    logger.info(f"Merged data after performing basic-merge for multiple SDs: {full_sd_from_pipe}")
    return full_sd_from_pipe


def handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode):
    base_sd_path = Path(f'{env.env_path}/Inventory/solution-descriptor/')
    handle_sd_skip_msg = "SD_SOURCE_TYPE is not specified, skipping SD file creation"
    if not sd_source_type:
        if not sd_version and not sd_data:
            logger.info(handle_sd_skip_msg)
        else:
            logger.warning(handle_sd_skip_msg)
        return

    sd_delta = calculate_sd_delta(sd_delta)
    effective_merge_mode = calculate_merge_mode(sd_merge_mode, sd_delta)

    helper.check_dir_exist_and_create(base_sd_path)
    if sd_source_type == "artifact":
        download_sds_with_version(env, base_sd_path, sd_version, effective_merge_mode)
    elif sd_source_type == "json":
        extract_sds_from_json(env, base_sd_path, sd_data, effective_merge_mode)
    else:
        logger.error('SD_SOURCE_TYPE must be set either to "artifact" or "json"')
        exit(1)


def extract_sds_from_json(env, base_sd_path: Path, sd_data, effective_merge_mode: MergeType):
    if not sd_data:
        logger.error("SD_SOURCE_TYPE is set to 'json', but SD_DATA was not given in pipeline variables")
        exit(1)
    sds_from_pipe = json.loads(sd_data)

    logger.info(f"printing data inside extract_sd_from_json {sds_from_pipe}")
    if not isinstance(sds_from_pipe, (list, dict)) or not sds_from_pipe:
        logger.error("SD_DATA must be a non-empty list of SD dictionaries or a single SD.")
        exit(1)

    # Build namespace mapping and transform each SD before any operations
    namespace_dict = build_namespace_dict(env)

    # Transform each SD item before processing
    if isinstance(sds_from_pipe, list):
        transformed_data = []
        for item in sds_from_pipe:
            transformed_item = handle_deploy_postfix_namespace_transformation(item, namespace_dict)
            transformed_data.append(transformed_item)
    else:
        transformed_data = handle_deploy_postfix_namespace_transformation(sds_from_pipe, namespace_dict)
    full_sd_from_pipe = multiply_sds_to_single(transformed_data)

    sd_path = base_sd_path.joinpath("sd.yaml")
    if effective_merge_mode == MergeType.REPLACE:
        logger.info("Inside replace")
        if helper.check_file_exists(sd_path):
            full_sd_yaml = helper.openYaml(sd_path)
            logger.info(f"full_sd.yaml before replacement: {json.dumps(full_sd_yaml, indent=2)}")
        else:
            logger.info("No existing SD found at destination. Proceeding to write new SD.")
        helper.check_dir_exist_and_create(path.dirname(sd_path))
        helper.writeYamlToFile(sd_path, full_sd_from_pipe)
        logger.info(f"Replaced existing SD with new data at: {sd_path}")
    else:
        sd_delta_path = base_sd_path.joinpath("delta_sd.yaml")
        helper.writeYamlToFile(sd_delta_path, full_sd_from_pipe)
        if not helper.check_file_exists(sd_path):
            helper.writeYamlToFile(sd_path, full_sd_from_pipe)
        else:
            # Call merge_sd with correct merge function
            selected_merge_function = MERGE_METHODS.get(effective_merge_mode)
            if not selected_merge_function:
                raise ValueError(f"Unsupported merge mode: {effective_merge_mode}")
            merge_sd(sd_path, full_sd_from_pipe, selected_merge_function)

    logger.info("SD successfully extracted from SD_DATA and Saved.")


def download_sds_with_version(env, base_sd_path, sd_version, effective_merge_mode: MergeType):
    logger.info(f"sd_version: {sd_version}")
    if not sd_version:
        logger.error("SD_SOURCE_TYPE is set to 'artifact', but SD_VERSION was not given in pipeline variables")
        exit(1)

    sd_entries = [line.strip() for line in sd_version.strip().splitlines() if line.strip()]
    if not sd_entries:
        logger.error("No valid SD versions found in SD_VERSION")
        exit(1)

    app_def_getter_plugins = PluginEngine(plugins_dir='/module/scripts/handle_sd_plugins/app_def_getter')
    sd_data_list = []
    for entry in sd_entries:  # appvers
        if ":" not in entry:
            logger.error(f"Invalid SD_VERSION format: '{entry}'. Expected 'name:version'")
            exit(1)

        source_name, version = entry.split(":", 1)
        logger.info(f"Starting download of SD: {source_name}-{version}")

        sd_data = download_sd_by_appver(source_name, version, app_def_getter_plugins)

        sd_data_list.append(sd_data)

    sd_data_json = json.dumps(sd_data_list)
    extract_sds_from_json(env, base_sd_path, sd_data_json, effective_merge_mode)


def download_sd_by_appver(app_name: str, version: str, plugins: PluginEngine) -> dict[str, object]:
    if 'SNAPSHOT' in version:
        raise ValueError("SNAPSHOT is not supported version of Solution Descriptor artifacts")
    # TODO: check if job would fail without plugins
    app_def = get_appdef_for_app(f"{app_name}:{version}", app_name, plugins)

    artifact_info = asyncio.run(artifact.check_artifact_async(app_def, artifact.FileExtension.JSON, version))
    if not artifact_info:
        raise ValueError(
            f'Solution descriptor content was not received for {app_name}:{version}')
    sd_url, _ = artifact_info
    return artifact.download_json_content(sd_url)


def get_appdef_for_app(appver: str, app_name: str, plugins: PluginEngine) -> artifact_models.Application:
    results = plugins.run(appver=appver)
    for result in results:
        if result is not None:
            return result
    app_def_path = identify_yaml_extension(f"{APP_DEFS_PATH}/{app_name}")
    app_dict = helper.openYaml(app_def_path)
    reg_def_path = identify_yaml_extension(f"{REG_DEFS_PATH}/{app_dict['registryName']}")
    app_dict['registry'] = artifact_models.Registry.model_validate(helper.openYaml(reg_def_path))
    app_def = artifact_models.Application.model_validate(app_dict)
    return app_def


if __name__ == "__main__":
    prepare_vars_and_run_sd_handling()
