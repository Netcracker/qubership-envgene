import os
from os import getenv

from envgenehelper import check_for_cyrillic, logger, findAllYamlsInDir, openYaml, check_dir_exists, \
    get_cluster_name_from_full_name, get_environment_name_from_full_name, check_environment_is_valid_or_fail, \
    check_file_exists, validate_yaml_by_scheme_or_fail, find_file_in_schemas
from envgenehelper.collections_helper import split_multi_value_param

project_dir = os.getenv('CI_PROJECT_DIR') or os.getenv('GITHUB_WORKSPACE')
logger.info(f"Info about project_dir: {project_dir}")


def ensure_required_keys(context: dict, required: list[str]):
    missing = [var for var in required if var not in context]
    if missing:
        raise ValueError(
            f"Required variables: {', '.join(required)}. "
            f"Not found: {', '.join(missing)}"
        )


def ensure_valid_fields(context: dict, fields: list[str]):
    invalid = []
    for field in fields:
        value = context.get(field)
        if not value:
            invalid.append(f"{field}={value!r}")

    if invalid:
        raise ValueError(
            f"Invalid or empty fields found: {', '.join(invalid)}. "
            f"Required fields: {', '.join(fields)}"
        )


def validate_pipeline(params: dict):
    basic_checks(params['ENV_NAMES'])
    real_execution_checks(
        params["ENV_NAMES"],
        params["GET_PASSPORT"],
        params["ENV_BUILD"],
        params["ENV_INVENTORY_INIT"],
        params["ENV_INVENTORY_CONTENT"]
    )


def basic_checks(env_names):
    if not env_names:
        logger.error('"ENV_NAMES" variable is not found or empty')
        raise ReferenceError("Execution is aborted as validation is not successful. See logs above.")



def real_execution_checks(env_names, get_passport, env_build, env_inventory_init, env_inventory_content):
    environment_names = split_multi_value_param(env_names)
    for env in environment_names:
        # now we are using only complex environment names that contain both cluster_name and environment_name
        if env.count('/') != 1:
            logger.fatal(
                f"Wrong env_name given: {env}. Env_name should contain both cloud name and environment name by pattern '<cluster_name>/<environment_name>'")
            exit(1)
        logger.info(f"Parsing environment name for: {env}")
        cluster_name = get_cluster_name_from_full_name(env)
        environment_name = get_environment_name_from_full_name(env)
        # checks
        check_environment(environment_name, cluster_name, get_passport, env_build, env_inventory_init,
                          env_inventory_content)
        check_passport_params(get_passport)


def check_environment(environment_name, cluster_name, get_passport, env_build, env_inventory_init,
                      env_inventory_content):
    if env_inventory_init == "true" or env_inventory_content:
        return
    all_environments_dir = f"{project_dir}/environments"
    skip_env_definition_check = get_passport and not env_build
    check_environment_is_valid_or_fail(environment_name, cluster_name, all_environments_dir, skip_env_definition_check,
                                       not skip_env_definition_check)


def check_passport_params(get_passport):
    if get_passport:
        integration_path = f"{project_dir}/configuration/integration.yml"
        integration_schema_path = find_file_in_schemas("integration.schema.json")
        if check_file_exists(integration_path):
            validate_yaml_by_scheme_or_fail(integration_path, integration_schema_path)
        else:
            logger.error(f'File configuration/integration.yml not exists in {integration_path}')
            raise ReferenceError("Execution is aborted as validation is not successful. See logs above.")
