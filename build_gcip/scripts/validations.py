
from os import getenv
from envgenehelper import check_for_cyrillic, logger, findAllYamlsInDir, openYaml, check_dir_exists, get_cluster_name_from_full_name, get_environment_name_from_full_name, check_environment_is_valid_or_fail, check_file_exists, validate_yaml_by_scheme_or_fail

def validate_pipeline(env_names, env_build, get_passport, cmdb_import, generate_effective_set, env_template_version, is_template_test, is_offsite, ci_commit_ref_name, env_inventory_init):
    basic_checks(env_names)
    if is_template_test:
        template_test_checks()
    else:
        real_execution_checks(env_names, get_passport, env_build, cmdb_import, env_inventory_init)

def basic_checks(env_names):
    if not env_names:
        logger.error(f'"ENV_NAMES" variable is not found or empty')
        raise ReferenceError(f"Execution is aborted as validation is not successful. See logs above.")


def template_test_checks():
    templates_dir = f"{getenv('CI_PROJECT_DIR')}/templates"
    # Check for Cyrillic characters in all YAML files in the templates directory if is_template_test is true
    yaml_files = findAllYamlsInDir(templates_dir)
    errorFound = False
    for yaml_file in yaml_files:
      content = openYaml(yaml_file)
      if content and check_for_cyrillic(content, yaml_file):
          logger.error(f"Cyrillic characters found in '{yaml_file}'")
          errorFound = True
    if not check_dir_exists(f"{templates_dir}/env_templates"):
        logger.error(f"Directory with templates '{templates_dir}' not found.")
        errorFound = True
    if errorFound:
        raise ReferenceError(f"Execution is aborted as validation is not successful. See logs above.")
    
def real_execution_checks(env_names, get_passport, env_build, cmdb_import, env_inventory_init):
    for env in env_names.split("\n"):
        # now we are using only complex environment names that contain both cluster_name and environment_name
        if env.count('/') != 1: 
            logger.fatal(f"Wrong env_name given: {env}. Env_name should contain both cloud name and environment name by pattern '<cluster_name>/<environment_name>'")
            exit(1)
        logger.info(f"Parsing environment name for: {env}")
        cluster_name = get_cluster_name_from_full_name(env)
        environment_name = get_environment_name_from_full_name(env)
        # checks
        check_environment(environment_name, cluster_name, get_passport, env_build, cmdb_import, env_inventory_init)
        check_passport_params(get_passport)

def check_environment(environment_name, cluster_name, get_passport, env_build, cmdb_import, env_inventory_init):
    if env_inventory_init == "true":
        return
    schemas_dir = getenv("JSON_SCHEMAS_DIR", "/module/schemas")
    all_environments_dir = f"{getenv('CI_PROJECT_DIR')}/environments"
    skip_env_definition_check = get_passport and not env_build and not cmdb_import
    check_environment_is_valid_or_fail(environment_name, cluster_name, all_environments_dir, skip_env_definition_check, not skip_env_definition_check, schemas_dir=schemas_dir)
    
def check_passport_params(get_passport):
    if get_passport:
        integration_path = f"{getenv('CI_PROJECT_DIR')}/configuration/integration.yml"
        integration_schema_path = f"{getenv('JSON_SCHEMAS_DIR', '/module/schemas')}/integration.schema.json"
        if check_file_exists(integration_path):
            validate_yaml_by_scheme_or_fail(integration_path, integration_schema_path)
        else:
            logger.error(f'File configuration/integration.yml not exists in {integration_path}')
            raise ReferenceError(f"Execution is aborted as validation is not successful. See logs above.")