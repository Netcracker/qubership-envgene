import asyncio
from os import path, getenv
from pathlib import Path

import envgenehelper as helper
from artifact_searcher import artifact
from artifact_searcher.utils import models as artifact_models
from build_env.namespace_render import compute_namespace_map
from envgenehelper.business_helper import get_current_env_dir_from_env_vars, get_version
from envgene_shared.utils.collections_utils import split_multi_value_param
from envgenehelper.env_helper import Environment
from envgenehelper.file_helper import identify_yaml_extension, deleteFileIfExists
from envgene_shared.utils.logger import logger
from envgenehelper.plugin_engine import PluginEngine
from envgenehelper.sd_helper import (basic_merge_multiple, MergeType, calculate_merge_mode,
                                     SD_FILE_NAME, DELTA_SD_FILE_NAME)
from envgenehelper.yaml_helper import load_json_or_yaml, dumpYamlToStr
from typing_extensions import deprecated

from pipeline.pipeline_parameters import PipelineParametersHandler

MERGE_METHODS = {
    MergeType.BASIC: helper.basic_merge,
    MergeType.BASIC_EXCLUSION: helper.basic_exclusion_merge,
}


def handle_deploy_postfix_namespace_transformation(sd_data: dict, namespace_by_deploy_postfix: dict) -> dict:
    """
    Transforms the SD data before writing:
    - If userData.useDeployPostfixAsNamespace == True:
        - Replace deployPostfix with corresponding folder name from namespace_by_deploy_postfix if exists.
        - If userData contains ONLY field useDeployPostfixAsNamespace, remove userData.
        - If other keys exist, remove only useDeployPostfixAsNamespace.
    """
    user_data = sd_data.get("userData", {})

    if isinstance(user_data, dict) and user_data.get("useDeployPostfixAsNamespace") is True:
        if not namespace_by_deploy_postfix:
            namespace_by_deploy_postfix = compute_namespace_map()
        for app in sd_data.get("applications", []):
            if "deployPostfix" in app and isinstance(app["deployPostfix"], str):
                namespace_name = app["deployPostfix"]
                replacement = next(
                    (
                        postfix
                        for postfix, name in namespace_by_deploy_postfix.items()
                        if name == namespace_name
                        or isinstance(name, dict) and namespace_name in name.values()
                    ),
                    None)
                if replacement:
                    logger.info(f"Replacing deployPostfix '{namespace_name}' with '{replacement}'")
                    app["deployPostfix"] = replacement
                else:
                    logger.error(f"No replacement found for deployPostfix '{namespace_name}', cannot continue.")
                    exit(1)
        # Remove entire userData if it has only one key
        if len(user_data) == 1:
            sd_data.pop("userData", None)
        else:
            user_data.pop("useDeployPostfixAsNamespace", None)
            sd_data["userData"] = user_data  # Reassign to make sure it's updated

    return sd_data


def merge_sd(sd_path: Path, sd_data, merge_func):
    logger.info(f"Final destination! - {sd_path}")
    full_sd_yaml = helper.openYaml(sd_path)
    logger.info(f"Full sd before merge: {full_sd_yaml}")
    helper.check_dir_exist_and_create(sd_path.parent)
    result = merge_func(full_sd_yaml, sd_data)
    helper.writeYamlToFile(sd_path, result)
    logger.info(f"Merged data into Target Path! - {result}")


@deprecated("SD_DELTA is deprecated")
def calculate_sd_delta(sd_delta):
    logger.info(f"printing sd_delta before {sd_delta}")
    if sd_delta is not None and str(sd_delta).strip() != "":
        sd_delta = str(sd_delta).strip().lower()
    else:
        sd_delta = None
    logger.info(f"printing sd_delta after {sd_delta}")
    return sd_delta


def multiply_sds_to_single(sds_data):
    sds_data = sds_data if isinstance(sds_data, list) else [sds_data]
    cropped_sds = [{"applications": sd["applications"]} for sd in sds_data]
    full_sd_from_pipe = basic_merge_multiple(cropped_sds)

    logger.info(f"Merged data after performing basic-merge for multiple SDs: {full_sd_from_pipe}")
    return full_sd_from_pipe


def handle_sd(handler: PipelineParametersHandler):
    sd_version = handler.params.get("SD_VERSION")
    sd_data = handler.params.get("SD_DATA")
    if sd_version and sd_data:
        raise ValueError("SD_VERSION and SD_DATA cannot be provided at the same time")
    sd_source = sd_version or sd_data
    if not sd_source:
        raise ValueError("Provide either SD_VERSION or SD_DATA")

    env = Environment(str(handler.work_dir), handler.cluster_name, handler.env_name)
    base_sd_path = Path(f'{env.env_path}/Inventory/solution-descriptor/')

    sd_merge_mode = handler.params.get("SD_REPO_MERGE_MODE")
    sd_delta = handler.params.get('SD_DELTA')
    namespace_names = getenv("NAMESPACE_NAMES")
    if namespace_names:
        logger.warning("NAMESPACE_NAMES is ignored when OPERATION_TYPE=DEPLOY")

    sd_delta = calculate_sd_delta(sd_delta)
    effective_merge_mode = calculate_merge_mode(sd_merge_mode, sd_delta)

    helper.check_dir_exist_and_create(base_sd_path)
    # do not commit delta sd to repo, delete old ones
    deleteFileIfExists(base_sd_path.joinpath(DELTA_SD_FILE_NAME))

    try:
        if load_json_or_yaml(sd_source):
            extract_sds_from_content(handler.namespace_by_deploy_postfix, base_sd_path, sd_source, effective_merge_mode)
        else:
            download_sds_by_version(handler.namespace_by_deploy_postfix, base_sd_path, sd_source, effective_merge_mode)
    except Exception as e:
        raise ValueError("SD_VERSION or SD_DATA must be set either appver or json/yaml") from e

    logger.info("SD successfully extracted from SD_VERSION or SD_DATA and saved")


def validate_applications(sd):
    applications = sd.get("applications")
    for app in applications:
        if not isinstance(app, dict) or not app.get("deployPostfix"):
            raise ValueError(f"Application {app} doesn't have deployPostfix.")


def extract_sds_from_content(namespace_by_deploy_postfix: dict, base_sd_path: Path, app_data, effective_merge_mode: MergeType):
    logger.info(f"Extracted SD content: {app_data}")
    app_data = load_json_or_yaml(app_data)

    if not app_data:
        raise ValueError(f"Extracted SD must be non-empty list or dict")

    # Transform each SD item before processing
    if isinstance(app_data, list):
        transformed_data = []
        for item in app_data:
            transformed_item = handle_deploy_postfix_namespace_transformation(item, namespace_by_deploy_postfix)
            transformed_data.append(transformed_item)
    else:
        transformed_data = handle_deploy_postfix_namespace_transformation(app_data, namespace_by_deploy_postfix)
    full_sd_from_pipe = multiply_sds_to_single(transformed_data)
    validate_applications(full_sd_from_pipe)

    sd_path = base_sd_path.joinpath(SD_FILE_NAME)
    sd_delta_path = base_sd_path.joinpath(DELTA_SD_FILE_NAME)
    if effective_merge_mode == MergeType.REPLACE:
        logger.info("Inside replace")
        if helper.check_file_exists(sd_path):
            full_sd_yaml = helper.openYaml(sd_path)
            logger.info(f"Full sd before replacement: {dumpYamlToStr(full_sd_yaml)}")
        else:
            logger.info("No existing SD found at destination. Proceeding to write new SD.")
        helper.check_dir_exist_and_create(path.dirname(sd_path))
        helper.writeYamlToFile(sd_path, full_sd_from_pipe)
        if helper.check_file_exists(sd_delta_path):
            helper.deleteFile(sd_delta_path)
        logger.info(f"Replaced existing SD with new data at: {sd_path}")
    else:
        if not helper.check_file_exists(sd_path):
            helper.writeYamlToFile(sd_path, full_sd_from_pipe)
        else:
            helper.writeYamlToFile(sd_delta_path, full_sd_from_pipe)
            # Call merge_sd with correct merge function
            selected_merge_function = MERGE_METHODS.get(effective_merge_mode)
            if not selected_merge_function:
                raise ValueError(f"Unsupported merge mode: {effective_merge_mode}")
            merge_sd(sd_path, full_sd_from_pipe, selected_merge_function)


def download_sds_by_version(namespace_by_deploy_postfix: dict, base_sd_path, app_versions, effective_merge_mode: MergeType):
    app_versions = app_versions.replace("\\n", "\n")
    app_entries = split_multi_value_param(app_versions)
    if not app_entries:
        raise ValueError(f"No valid application versions found in {app_versions}")

    app_def_getter_plugins = PluginEngine(plugins_dir='/module/scripts/plugins/handle_sd_plugins')
    app_data_list = []
    for entry in app_entries:  # appvers
        source_name, version = get_version(entry)
        logger.info(f"Starting download of SD: {source_name}-{version}")

        app_data = download_sd_by_appver(source_name, version, app_def_getter_plugins)

        app_data_list.append(app_data)

    app_data = dumpYamlToStr(app_data_list)
    extract_sds_from_content(namespace_by_deploy_postfix, base_sd_path, app_data, effective_merge_mode)


def download_sd_by_appver(app_name: str, version: str, plugins: PluginEngine) -> dict[str, object]:
    app_def = get_appdef_for_app(f"{app_name}:{version}", plugins)

    env_creds = helper.get_cred_config()
    auth_headers = app_def.registry.resolve_auth(env_creds)

    artifact_info = asyncio.run(
        artifact.check_artifact_async(app_def, artifact.FileExtension.JSON, version, auth_headers=auth_headers))
    if not artifact_info:
        raise ValueError(f'Solution descriptor content was not received for {app_name}:{version}')
    return artifact.download_json_content(artifact_info.source_url, auth_headers=auth_headers)


def get_appdef_for_app(appver: str, plugins: PluginEngine) -> artifact_models.Application:
    app_name, _ = get_version(appver)
    results = plugins.run(appver=appver)
    for result in results:
        if result is not None:
            return result
    env_path = get_current_env_dir_from_env_vars()
    app_defs_path = f"{env_path}/AppDefs"
    reg_defs_path = f"{env_path}/RegDefs"
    app_def_path = identify_yaml_extension(f"{app_defs_path}/{app_name}")
    app_dict = helper.openYaml(app_def_path)
    reg_def_path = identify_yaml_extension(f"{reg_defs_path}/{app_dict['registryName']}")
    app_dict['registry'] = artifact_models.parse_registry(helper.openYaml(reg_def_path))
    app_def = artifact_models.Application.model_validate(app_dict)
    return app_def
