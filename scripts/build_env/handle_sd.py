import asyncio
from os import path, getenv
import json
import re

import ansible_runner

import envgenehelper as helper
from envgenehelper import logger, openYaml
from envgenehelper.business_helper import getenv_and_log, Environment
from artifact_searcher import artifact
from artifact_searcher.utils import models as artifact_models
from engine_core import PluginEngine

MERGE_METHODS = {
    "basic-merge": helper.basic_merge,
    "basic-exclusion-merge": helper.basic_exclusion_merge,
    "extended-merge": helper.extended_merge
}


ENVIRONMENT_NAME = getenv_with_error('ENVIRONMENT_NAME')
CLUSTER_NAME = getenv_with_error('CLUSTER_NAME')
WORK_DIR = getenv_with_error('CI_PROJECT_DIR')
BASE_ENV_PATH = f"{WORK_DIR}/environments/{CLUSTER_NAME}/{ENVIRONMENT_NAME}"
APP_DEFS_PATH = f"{BASE_ENV_PATH}/AppDefs"
REG_DEFS_PATH = f"{BASE_ENV_PATH}/RegDefs"


def prepare_vars_and_run_sd_handling():
    base_dir = getenv_and_log('CI_PROJECT_DIR')
    env_name = getenv_and_log('ENV_NAME')
    cluster = getenv_and_log('CLUSTER_NAME')

    env = Environment(base_dir, cluster, env_name)

    params_json = getenv_and_log("ENV_GENERATION_PARAMS")
    params = json.loads(params_json)

    sd_source_type = params['SD_SOURCE_TYPE']
    sd_version = params['SD_VERSION']
    sd_data = params['SD_DATA']
    sd_delta = params['SD_DELTA']
    sd_merge_mode = getenv("SD_REPO_MERGE_MODE")
    logger.info(f"sd_data: {sd_data}")
    logger.info(f"sd_merge_mode: {sd_merge_mode}")

    handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode)

def merge_sd(env, sd_data, merge_func):
    destination = f'{env.env_path}/Inventory/solution-descriptor/sd.yaml'
    logger.info(f"Final destination! - {destination}")
    if helper.check_file_exists(destination):
        full_sd_yaml = helper.openYaml(destination)
        logger.info(f"full_sd.yaml before merge: {full_sd_yaml}")
    helper.check_dir_exist_and_create(path.dirname(destination))
    helper.pre_validate(full_sd_yaml, sd_data)
    result = merge_func(full_sd_yaml, sd_data)
    helper.writeYamlToFile(destination, result)
    logger.info(f"Merged data into Target Path! - {result}")

def handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta, sd_merge_mode):
    base_path = f'{env.env_path}/Inventory/solution-descriptor/'
    if not sd_source_type:
        logger.info("SD_SOURCE_TYPE is not specified, skipping SD file creation")
        return
    logger.info(f"printing sd_delta before {sd_delta}")

    if sd_delta is not None and str(sd_delta).strip() != "":
        sd_delta = str(sd_delta).strip().lower()
    else:
        sd_delta = None

    logger.info(f"printing sd_delta after {sd_delta}")
    if sd_delta == "true":
        sd_path = base_path + 'delta_sd.yaml'
        logger.info(f"printing sd_path sd_delta T {sd_path}")
        full_sd_path = base_path + 'sd.yaml'
        if not helper.check_file_exists(full_sd_path):
            logger.error(f"To use the delta processing mode for SD, a complete SD must already be stored in the repository.\nThe file {full_sd_path} does not exist.")
            exit(1)
    else:
        sd_path = base_path + 'sd.yaml'
        logger.info(f"printing sd_path sd_delta F {sd_path}")

    helper.check_dir_exist_and_create(path.dirname(sd_path))
    if sd_source_type == "artifact":
        download_sds_with_version(env, sd_path, sd_version, sd_delta, sd_merge_mode)
    elif sd_source_type == "json":
        extract_sds_from_json(env, sd_path, sd_data, sd_delta, sd_merge_mode)
    else:
        logger.error(f'SD_SOURCE_TYPE must be set either to "artifact" or "json"')
        exit(1)

def extract_sds_from_json(env, sd_path, sd_data, sd_delta, sd_merge_mode):
    if not sd_data:
        logger.error(f"SD_SOURCE_TYPE is set to 'json', but SD_DATA was not given in pipeline variables")
        exit(1)
    data = json.loads(sd_data)

    logger.info(f"printing data inside extract_sd_from_json {data}")
    if not isinstance(data, list) or not data:
        logger.error("SD_DATA must be a non-empty list of SD dictionaries.")
        exit(1)
    sd_merge_mode = str(sd_merge_mode).strip().lower() if sd_merge_mode else None

    if sd_merge_mode:
        effective_merge_mode = sd_merge_mode
    elif sd_delta == "true":
        effective_merge_mode = "extended-merge"
    elif sd_delta == "false":
        effective_merge_mode = "replace"
    else:
        effective_merge_mode = "basic-merge"

    # Perform basic-merge for multiple SDs before applying SD_REPO_MERGE_MODE
    merged_applications = {"applications": data[0].get("applications", [])}
    if not merged_applications["applications"]:
        logger.error("No applications found in the first SD block.")
        exit(1)
    for i in range(1, len(data)):
        logger.info(f"Initiates basic-merge:")
        current_item_sd = {"applications": data[i].get("applications", [])}
        merged_applications = helper.merge(merged_applications, current_item_sd)
    merged_result = {
        "version": data[0].get("version"),
        "type": data[0].get("type"),
        "deployMode": data[0].get("deployMode"),
        "applications": merged_applications["applications"]
        }
    logger.info(f"Level-1 SD data: {json.dumps(merged_result, indent=2)}")

    #merged_result["version"] = str(merged_result["version"])
    helper.writeYamlToFile(sd_path, merged_result)
    merged_data = helper.openYaml(sd_path)
    logger.info(f"Merged_data: {merged_data}")

    # Call merge_sd with correct merge function
    if effective_merge_mode == "replace":
        logger.info(f"Inside replace")
        destination = f'{env.env_path}/Inventory/solution-descriptor/sd.yaml'
        if helper.check_file_exists(destination):
            full_sd_yaml = helper.openYaml(destination)
            logger.info(f"full_sd.yaml before replacement: {json.dumps(full_sd_yaml, indent=2)}")
        else:
            logger.info("No existing SD found at destination. Proceeding to write new SD.")
        helper.check_dir_exist_and_create(path.dirname(destination))
        helper.writeYamlToFile(destination, merged_data)
        logger.info(f"Replaced existing SD with new data at: {destination}")
        return

    selected_merge_function = MERGE_METHODS.get(effective_merge_mode)
    if not selected_merge_function:
        raise ValueError(f"Unsupported merge mode: {effective_merge_mode}")
    merge_sd(env, merged_data, selected_merge_function)

    logger.info(f"SD successfully extracted from SD_DATA and Saved.")

def download_sds_with_version(env, sd_path, sd_version, sd_delta, sd_merge_mode):
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
    for entry in sd_entries: #appvers
        if ":" not in entry:
            logger.error(f"Invalid SD_VERSION format: '{entry}'. Expected 'name:version'")
            exit(1)

        source_name, version = entry.split(":", 1)
        logger.info(f"Starting download of SD: {source_name}-{version}")

        sd_data = download_sd_by_appver(source_name, version, app_def_getter_plugins)

        sd_data_list.append(sd_data)

    sd_data_json = json.dumps(sd_data_list)
    extract_sds_from_json(env, sd_path, sd_data_json, sd_delta, sd_merge_mode)

def download_sd_by_appver(app_name: str, version: str, plugins: PluginEngine) -> str:
    if 'SNAPSHOT' in version:
        raise ValueError("SNAPSHOT is not supported version of Solution Descriptor artifacts")
    # TODO: check if job would fail without plugins
    app_def = get_appdef_for_app(app_name, plugins)

    artifact_info = asyncio.run(artifact.check_artifact_async(app_def, artifact.FileExtension.JSON, version))
    if not artifact_info:
        raise ValueError(
            f'Solution descriptor content was not received for {app_name}:{version}')
    sd_url, _ = artifact_info
    return json.dumps(artifact.download_json_content(sd_url))

def get_appdef_for_app(app_name: str, plugins: PluginEngine) -> artifact_models.Application:
    results = plugins.run(app_name=app_name)
    for result in results:
        if result is not None:
            return result
    app_dict = helper.openYaml(f"{APP_DEFS_PATH}/{app_name}")
    app_dict['registry'] = artifact_models.Registry.model_validate(helper.openYaml(f"{APP_DEFS_PATH}/{app_name}"))
    app_def = artifact_models.Application.model_validate(app_dict)
    return app_def


if __name__ == "__main__":
    prepare_vars_and_run_sd_handling()
