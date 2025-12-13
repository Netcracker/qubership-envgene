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
from envgenehelper.sd_merge_helper import basic_merge_multiple


def fix_yaml_document_separators(input_dir):
    """
    Fix YAML parsing errors by adding document separators to all YAML files
    This prevents iTool parsing errors
    """
    logger.info("Fixing YAML document separators in Helm charts")
    fixed_count = 0
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.yaml', '.yml')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file starts with --- and is not empty
                    if content.strip() and not content.lstrip().startswith('---'):
                        # Add document separator at the beginning
                        fixed_content = '---\n' + content
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        fixed_count += 1
                        logger.debug(f"Fixed YAML document separator in: {file_path}")
                except Exception as e:
                    logger.warning(f"Could not fix YAML file {file_path}: {e}")
    
    if fixed_count > 0:
        logger.info(f"Fixed document separators in {fixed_count} YAML files")
    else:
        logger.info("No YAML files needed fixing")
    
    return fixed_count


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
    # Log summary instead of full SD to avoid huge logs
    app_count = len(sd_data.get("applications", []))
    logger.info(f"[handle_deploy_postfix_namespace_transformation] Processing SD with {app_count} applications")
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


def multiply_sds_to_single(sds_data, effective_merge_mode: MergeType):
    full_sd_from_pipe = None
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
            # Handle V2 SD structure - extract applications from graph if needed
            if "applications" not in sd:
                if "graph" in sd and "vertexList" in sd["graph"]:
                    # Extract applications from V2 graph structure
                    applications = []
                    for vertex in sd["graph"]["vertexList"]:
                        if vertex.get("type") in ["ui backend", "backend", "frontend", "service"]:
                            app = {
                                "id": vertex.get("id"),
                                "name": vertex.get("name"),
                                "version": f"{vertex.get('name')}:unknown",
                                "type": vertex.get("type"),
                                "directoryPath": vertex.get("directoryPath", "/var/input"),
                                "releaseBranch": vertex.get("releaseBranch", "master"),
                                "repository": vertex.get("repository", ""),
                                "details": vertex.get("details", {}),
                                "deployPostfix": ""
                            }
                            applications.append(app)
                    sd["applications"] = applications
                    logger.info(f"Extracted {len(applications)} applications from V2 SD graph")
                else:
                    # If no graph structure, create empty applications list
                    sd["applications"] = []
                    logger.warning("V2 SD has no applications key and no graph structure, creating empty applications list")

            cropped_sds.append({"applications": sd["applications"]})

        full_sd_from_pipe = basic_merge_multiple(cropped_sds)

    # Log summary instead of full SD to avoid huge logs
    app_count = len(full_sd_from_pipe.get("applications", [])) if full_sd_from_pipe else 0
    logger.info(f"Merged SD with {app_count} applications")
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

    # Fix YAML document separators in /var/input to prevent iTool parsing errors
    input_dir = "/var/input"
    if os.path.exists(input_dir):
        fix_yaml_document_separators(input_dir)

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


def validate_applications(sd, effective_merge_mode: MergeType):
    applications = sd.get("applications")
    if not applications:
        logger.warning("SD has no applications or applications is empty")
        return
    for app in applications:
        if effective_merge_mode != MergeType.EXTENDED and (not isinstance(app, dict) or not app.get("deployPostfix")):
            raise ValueError(
                f"Application {app} doesn't have deployPostfix. <name>:<version> notation is supported only for "
                f"extended merge. Current merge mode: {effective_merge_mode.value}")


def extract_sds_from_json(env, base_sd_path: Path, sd_data, effective_merge_mode: MergeType):
    if not sd_data:
        logger.error("SD_SOURCE_TYPE is set to 'json', but SD_DATA was not given in pipeline variables")
        exit(1)
    sds_from_pipe = json.loads(sd_data)

    # Log summary instead of full SD content
    sd_count = len(sds_from_pipe) if isinstance(sds_from_pipe, list) else 1
    logger.info(f"Loaded {sd_count} SD(s) from SD_DATA")
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
    full_sd_from_pipe = multiply_sds_to_single(transformed_data, effective_merge_mode)
    validate_applications(full_sd_from_pipe, effective_merge_mode)

    sd_path = base_sd_path.joinpath("sd.yaml")
    sd_delta_path = base_sd_path.joinpath("delta_sd.yaml")
    if effective_merge_mode == MergeType.REPLACE:
        logger.info("Inside replace")
        if helper.check_file_exists(sd_path):
            full_sd_yaml = helper.openYaml(sd_path)
            logger.info(f"full_sd.yaml before replacement: {json.dumps(full_sd_yaml, indent=2)}")
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

    logger.info("SD successfully extracted from SD_DATA and Saved.")


def download_sds_with_version(env, base_sd_path, sd_version, effective_merge_mode: MergeType):
    logger.info(f"sd_version: {sd_version}")
    if not sd_version:
        logger.error("SD_SOURCE_TYPE is set to 'artifact', but SD_VERSION was not given in pipeline variables")
        exit(1)
    sd_version = sd_version.replace("\\n", "\n")
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

        sd_data = download_sd_by_appver(source_name, version, app_def_getter_plugins, env.creds)

        sd_data_list.append(sd_data)

    sd_data_json = json.dumps(sd_data_list)
    extract_sds_from_json(env, base_sd_path, sd_data_json, effective_merge_mode)


def download_sd_by_appver(
    app_name: str,
    version: str,
    plugins: PluginEngine,
    env_creds: dict = None,
) -> dict[str, object]:
    if 'SNAPSHOT' in version:
        raise ValueError("SNAPSHOT is not supported version of Solution Descriptor artifacts")
    
    app_def = get_appdef_for_app(f"{app_name}:{version}", app_name, plugins)
    
    # Log registry version for debugging
    registry_version = getattr(app_def.registry, 'version', '1.0')
    logger.info(f"Downloading SD for {app_name}:{version} using registry '{app_def.registry.name}' (version: {registry_version})")
    
    # Log if env_creds are available (for V2)
    if env_creds:
        cred_keys = list(env_creds.keys()) if isinstance(env_creds, dict) else []
        logger.debug(f"env_creds available with keys: {cred_keys}")
    else:
        logger.debug("No env_creds provided - V1 flow will be used")
    
    artifact_info = asyncio.run(
        artifact.check_artifact_async(app_def, artifact.FileExtension.JSON, version, env_creds)
    )
    if not artifact_info:
        raise ValueError(f'Solution descriptor content was not received for {app_name}:{version}')

    sd_url, repo_info = artifact_info
    repo_marker, extra_info = repo_info

    # V2 artifacts are already downloaded locally - read from file
    if repo_marker == "v2_downloaded":
        local_path = extra_info
        logger.info(f"Successfully retrieved V2 SD from local path: {local_path}")
        with open(local_path, 'r', encoding='utf-8') as f:
            sd_content = json.load(f)
        logger.info(f"V2 SD loaded successfully for {app_name}:{version}")
        return sd_content

    # V1 artifacts - download from URL
    logger.info(f"Downloading V1 SD from URL: {sd_url}")
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
