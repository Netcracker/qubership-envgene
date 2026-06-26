import asyncio
import os
from os import path, getenv
from pathlib import Path

import envgenehelper as helper
from artifact_searcher import artifact
from artifact_searcher.utils import models as artifact_models
from envgenehelper.business_helper import getenv_with_error, get_version
from envgenehelper.collections_helper import split_multi_value_param
from envgenehelper.env_helper import Environment
from envgenehelper.file_helper import identify_yaml_extension, deleteFileIfExists
from envgenehelper.logger import logger
from envgenehelper.models import OperationType
from envgenehelper.plugin_engine import PluginEngine
from envgenehelper.sd_helper import (basic_merge_multiple, MergeType, calculate_merge_mode,
                                     SD_FILE_NAME, DELTA_SD_FILE_NAME)
from envgenehelper.yaml_helper import load_json_or_yaml, openYaml, dumpYamlToStr
from typing_extensions import deprecated

from pipeline.pipeline_parameters import PipelineParametersHandler

MERGE_METHODS = {
    MergeType.BASIC: helper.basic_merge,
    MergeType.BASIC_EXCLUSION: helper.basic_exclusion_merge,
    MergeType.EXTENDED: helper.extended_merge
}

def get_base_env_path():
    return helper.get_env_instances_dir(helper.getenv_with_error('ENVIRONMENT_NAME'), helper.getenv_with_error('CLUSTER_NAME'), helper.getenv_with_error('INSTANCES_DIR'))

def get_app_defs_path():
    return f"{get_base_env_path()}/AppDefs"

def get_reg_defs_path():
    return f"{get_base_env_path()}/Registries"


def handle_deploy_postfix_namespace_transformation(sd_data: dict, namespace_dict: dict) -> dict:
    """
    Transforms the SD data before writing:
    - If userData.useDeployPostfixAsNamespace == True:
        - Replace deployPostfix with corresponding folder name from namespace_dict if exists.
        - If userData contains ONLY field useDeployPostfixAsNamespace, remove userData.
        - If other keys exist, remove only useDeployPostfixAsNamespace.
    """
    logger.info(
        f"[Pre handle_deploy_postfix_namespace_transformation] Original SD data: {dumpYamlToStr(sd_data)}")
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


def build_namespace_dict(env) -> dict:
    namespaces_dir = f'{env.env_path}/Namespaces/'
    result = {}

    if not os.path.exists(namespaces_dir):
        logger.warning(f"Namespaces directory does not exist: {namespaces_dir}")
        return result

    # Iterate over all items in Namespaces directory
    for folder_name in os.listdir(namespaces_dir):
        folder_path = os.path.join(namespaces_dir, folder_name)
        if os.path.isdir(folder_path):
            namespace_file = os.path.join(folder_path, "namespace.yml")
            if os.path.isfile(namespace_file):
                data = openYaml(namespace_file)
                logger.debug(f"Parsed content of {namespace_file}: {data}")
                # Extract 'name' property
                ns_name = data.get("name")
                logger.debug(f"ns_name = {ns_name}")
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


def multiply_sds_to_single(sds_data, effective_merge_mode):
    if effective_merge_mode == MergeType.EXTENDED:
        if isinstance(sds_data, list):
            if len(sds_data) > 1:
                raise ValueError("Multiple SDs not supported in extended merge mode")
            full_sd_from_pipe = sds_data[0]
        elif isinstance(sds_data, dict):
            full_sd_from_pipe = sds_data
    else:
        sds_data = sds_data if isinstance(sds_data, list) else [sds_data]
        cropped_sds = []
        for sd in sds_data:
            cropped_sds.append({"applications": sd["applications"]})

        full_sd_from_pipe = basic_merge_multiple(cropped_sds)

    logger.info(f"Merged data after performing basic-merge for multiple SDs: {full_sd_from_pipe}")
    return full_sd_from_pipe


def handle_sd(handler: PipelineParametersHandler):
    application_versions = resolve_sd_parameters(handler)
    if not application_versions:
        raise ValueError("Provide either APPLICATION_VERSIONS or SD_VERSION / SD_DATA")

    operation_type = OperationType(handler.params.get("OPERATION_TYPE"))

    env = Environment(str(handler.work_dir), handler.cluster_name, handler.env_name)
    base_sd_path = Path(f'{env.env_path}/Inventory/solution-descriptor/')

    if operation_type == OperationType.DEPLOY:
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
            if load_json_or_yaml(application_versions):
                extract_sds_from_content(env, base_sd_path, application_versions, effective_merge_mode)
            else:
                download_sds_by_version(env, base_sd_path, application_versions, effective_merge_mode)
        except Exception as e:
            raise ValueError(
                "APPLICATION_VERSIONS or SD_VERSION / SD_DATA must be set either appver or json/yaml") from e

        logger.info("SD successfully extracted from APPLICATION_VERSIONS or SD_VERSION / SD_DATA and saved")
    elif operation_type == OperationType.CLEAN:
        apply_namespace_cleanup_to_sd(env, base_sd_path)


def validate_applications(sd, effective_merge_mode: MergeType):
    applications = sd.get("applications")
    for app in applications:
        if effective_merge_mode != MergeType.EXTENDED and (not isinstance(app, dict) or not app.get("deployPostfix")):
            raise ValueError(
                f"Application {app} doesn't have deployPostfix. <name>:<version> notation is supported only for "
                f"extended merge. Current merge mode: {effective_merge_mode.value}")


def extract_sds_from_content(env, base_sd_path: Path, app_data, effective_merge_mode: MergeType):
    logger.info(f"Extracted SD content: {app_data}")
    app_data = load_json_or_yaml(app_data)

    if not app_data:
        raise ValueError(f"Extracted SD must be non-empty list or dict")

    # Build namespace mapping and transform each SD before any operations
    namespace_dict = build_namespace_dict(env)

    # Transform each SD item before processing
    if isinstance(app_data, list):
        transformed_data = []
        for item in app_data:
            transformed_item = handle_deploy_postfix_namespace_transformation(item, namespace_dict)
            transformed_data.append(transformed_item)
    else:
        transformed_data = handle_deploy_postfix_namespace_transformation(app_data, namespace_dict)
    full_sd_from_pipe = multiply_sds_to_single(transformed_data, effective_merge_mode)
    validate_applications(full_sd_from_pipe, effective_merge_mode)

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


def download_sds_by_version(env, base_sd_path, app_versions, effective_merge_mode: MergeType):
    app_versions = app_versions.replace("\\n", "\n")
    app_entries = split_multi_value_param(app_versions)
    if not app_entries:
        raise ValueError(f"No valid application versions found in {app_versions}")

    if effective_merge_mode == MergeType.EXTENDED and len(app_entries) > 1:
        raise ValueError("Multiple SDs not supported in extended merge mode")


    app_def_getter_plugins = PluginEngine(plugins_dir='/module/scripts/plugins/handle_sd_plugins')
    app_data_list = []
    for entry in app_entries:  # appvers
        source_name, version = get_version(entry)
        logger.info(f"Starting download of SD: {source_name}-{version}")

        app_data = download_sd_by_appver(source_name, version, app_def_getter_plugins)

        app_data_list.append(app_data)

    app_data = dumpYamlToStr(app_data_list)
    extract_sds_from_content(env, base_sd_path, app_data, effective_merge_mode)


def download_sd_by_appver(app_name: str, version: str, plugins: PluginEngine) -> dict[str, object]:
    app_def = get_appdef_for_app(f"{app_name}:{version}", app_name, plugins)

    env_creds = helper.get_cred_config()
    auth_headers = app_def.registry.resolve_auth(env_creds)

    artifact_info = asyncio.run(
        artifact.check_artifact_async(app_def, artifact.FileExtension.JSON, version, auth_headers=auth_headers))
    if not artifact_info:
        raise ValueError(f'Solution descriptor content was not received for {app_name}:{version}')
    sd_url, _ = artifact_info
    return artifact.download_json_content(sd_url, auth_headers=auth_headers)


def get_appdef_for_app(appver: str, app_name: str, plugins: PluginEngine) -> artifact_models.Application:
    results = plugins.run(appver=appver)
    for result in results:
        if result is not None:
            return result
    try:
        app_def_path = identify_yaml_extension(f"{get_app_defs_path()}/{app_name}")
    except FileNotFoundError:
        raise ValueError("Application Definition not found")
    app_dict = helper.openYaml(app_def_path)
    
    try:
        reg_def_path = identify_yaml_extension(f"{get_reg_defs_path()}/{app_dict['registryName']}")
    except FileNotFoundError:
        raise ValueError("Registry Definition not found")
    
    app_dict['registry'] = artifact_models.parse_registry(helper.openYaml(reg_def_path))
    app_def = artifact_models.Application.model_validate(app_dict)
    return app_def


def resolve_sd_parameters(handler: PipelineParametersHandler) -> str | None:
    application_versions = handler.params.get("APPLICATION_VERSIONS")
    sd_version = handler.params.get("SD_VERSION")
    sd_data = handler.params.get("SD_DATA")

    if application_versions:
        if sd_version:
            logger.warning("SD_VERSION is deprecated and ignored because APPLICATION_VERSIONS was provided")

        if sd_data:
            logger.warning("SD_DATA is deprecated and ignored because APPLICATION_VERSIONS was provided")

        return application_versions

    if sd_version and sd_data:
        raise ValueError("SD_VERSION and SD_DATA cannot be provided at the same time")

    if sd_version:
        logger.warning("SD_VERSION and SD_SOURCE_TYPE are deprecated. Use APPLICATION_VERSIONS instead")
        return sd_version

    if sd_data:
        logger.warning("SD_DATA and SD_SOURCE_TYPE are deprecated. Use APPLICATION_VERSIONS instead")
        return sd_data


def apply_namespace_cleanup_to_sd(env: Environment, base_sd_path: Path):
    ns_names_var = getenv("NAMESPACE_NAMES")
    sd_path = base_sd_path / SD_FILE_NAME
    if not sd_path.exists():
        logger.info(f"Operation type CLEAN: sd.yaml not found at {sd_path}, nothing to filter")
        return

    if not ns_names_var:
        deleteFileIfExists(sd_path)
        logger.info(
            f"Operation type CLEAN: NAMESPACE_NAMES is empty, env-cleanup (all namespaces), deleted {sd_path}")
        return

    # { "namespace_name": "folder_name_for_ns" }
    ns_map = build_namespace_dict(env)
    ns_for_cleanup = {}

    for ns_name in split_multi_value_param(ns_names_var):
        deploy_postfix = ns_map.get(ns_name)
        if deploy_postfix is None:
            raise ValueError(f"Operation type CLEAN: namespace '{ns_name}' has no matching namespace folder")
        ns_for_cleanup[ns_name] = deploy_postfix

    sd = openYaml(sd_path)
    apps = sd.get("applications", [])

    postfixes_from_sd = {app.get("deployPostfix") for app in apps if app.get("deployPostfix")}
    for ns_name, dp in ns_for_cleanup.items():
        if dp not in postfixes_from_sd:
            # case incorrect ns from namespace_names or accidentally launched 2 clean up same ns
            logger.warning(f"Operation type CLEAN: deployPostfix '{dp}' (namespace '{ns_name}') not found in sd")

    postfixes_for_cleanup = set(ns_for_cleanup.values())
    filtered_apps = [app for app in apps if app.get("deployPostfix") not in postfixes_for_cleanup]
    if not filtered_apps:
        logger.info(f"Operation type CLEAN: applications is empty, delete {sd_path}")
        deleteFileIfExists(sd_path)
        return

    sd["applications"] = filtered_apps
    helper.writeYamlToFile(sd_path, sd)
