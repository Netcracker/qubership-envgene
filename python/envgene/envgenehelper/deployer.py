from .config_helper import get_envgene_config_yaml
from .creds_helper import check_is_envgen_cred, get_cred_id_and_property_from_cred_macros
from .business_helper import find_env_instances_dir, findResourcesBottomTop, get_env_definition, getenv_with_error
from .yaml_helper import openYaml, get_or_create_nested_yaml_attribute
from .file_helper import getDirName, check_file_exists
from .logger import logger
from .crypt import decrypt_file

def get_cred_file_path(deployer_dir):
    dashes_cred_path = f"{deployer_dir}/deployer-creds.yml"
    folder_cred_path = f"{deployer_dir}/credentials/credentials.yml"
    cred_path = ""
    if check_file_exists(dashes_cred_path):
        cred_path = dashes_cred_path
    elif check_file_exists(folder_cred_path):
        cred_path = folder_cred_path
    else:
        logger.error(f"Credentials definition for deployer not found in either {dashes_cred_path} or {folder_cred_path}")
        raise ReferenceError("Credentials definition for deployer not found. See logs above.")
    logger.info(f"Credentials definition for deployer is found in: {cred_path}")
    return cred_path

def get_value_and_attributes_from_cred(cred_macros, deployer_dir):
    # defined as credentials
    if (check_is_envgen_cred(cred_macros)):
        credentials_file_path = get_cred_file_path(deployer_dir)
        cred_id, property = get_cred_id_and_property_from_cred_macros(cred_macros)
        data = openYaml(credentials_file_path)
        if cred_id in data:
            cred = data[cred_id]
            attribute_path = f'{cred_id}.data.{property}'
            return cred['data'][property], attribute_path
        else:
            logger.error(f"Credentials with key {cred_id} is not found in credentials file.")
            raise ReferenceError(f"Credentials with key {cred_id} is not found in credentials file.")
    else:
        return cred_macros

def get_value_with_path_and_attribute(fp, attr_str, default_value=None):
    file = openYaml(fp)
    return get_or_create_nested_yaml_attribute(file, attr_str, default_value)

def get_deployer(env_name, instances_dir, failonerror=True):
    env_path = find_env_instances_dir(env_name, instances_dir)
    data = get_env_definition(env_path)
    if "deployer" not in data["inventory"]:
        logger.error(f"Deployer definition for environment {env_path} is not specified in environment definition.")
        if failonerror:
            raise ReferenceError("Deployer definition for environment is not specified in environment definition. See logs above.")
        else:
            return ""
    deployer_name = data['inventory']['deployer']
    return deployer_name

def find_deployer_definition(env_name, work_dir, instances_dir, failonerror=True):
    env_dir = find_env_instances_dir(env_name, instances_dir)
    deployers = findResourcesBottomTop(env_dir, work_dir, "/deployer.y")
    if len(deployers) == 1:
        yamlPath = deployers[0]
        logger.info(f"Deployer configuration found in: {yamlPath}")
        return yamlPath
    elif len(deployers) > 1:
        logger.error(f"Duplicate deployer configuration found in {work_dir}: \n\t" + ",\n\t".join(str(x) for x in deployers))
        if failonerror:
            raise ReferenceError(f"Duplicate deployer configuration found in {work_dir} found. See logs above.")
            return ""
    else:
        if failonerror:
            raise ReferenceError(f"Deployer configuration not found in {work_dir}")
            return ""

def get_deployer_config(env_name=None, work_dir=None, instances_dir=None, secret_key=None, is_test=None, failonerror=True, deployer_name=None, fallback_on_root_config=True):
    # finding necessary deployer
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    basic_deployer_file_path = f"{base_dir}/configuration/deployer.yml"
    if env_name and work_dir and instances_dir:
        deployer_name = get_deployer(env_name, instances_dir, failonerror)
        deployer_file_path = find_deployer_definition(env_name, work_dir, instances_dir, failonerror)
        if not deployer_file_path:
            logger.info("Deployer definition file is not found, exiting.")
            return "","",""
    else:
        if deployer_name is None:
            raise ValueError('get_deployer_config() function must be called either with (env_name, work_dir, instances_dir) or with (deployer_name) params')
        deployer_file_path = basic_deployer_file_path
    deployer_dir = getDirName(deployer_file_path)
    data = openYaml(deployer_file_path, allow_default=True)
    if deployer_name not in data and fallback_on_root_config:
        logger.info(f"Deployer with key {deployer_name} not found in: {deployer_file_path}. Going to root configuration: {basic_deployer_file_path}")
        deployer_dir = getDirName(basic_deployer_file_path)
        data = openYaml(basic_deployer_file_path, allow_default=True)
    if deployer_name not in data:
        logger.error(f"Deployer with key {deployer_name} not found in either: {deployer_file_path} or {basic_deployer_file_path}")
        if failonerror:
            raise ReferenceError(f"Deployer with key {deployer_name} not found. See logs above.")
        else:
            return "","",""
    # getting values
    cmdb_username, cmdb_username_attribute_path = get_value_and_attributes_from_cred(data[deployer_name]['username'], deployer_dir)
    cmdb_api_token, cmdb_api_token_attribute_path = get_value_and_attributes_from_cred(data[deployer_name]['token'], deployer_dir)
    cmdb_url = data[deployer_name]['deployerUrl']
    envgene_config = get_envgene_config_yaml()
    is_decryption_necessary = secret_key or envgene_config.get('crypt')
    if is_decryption_necessary:
        cred_path = get_cred_file_path(deployer_dir)
        if is_test:
            cred_yaml = decrypt_file(cred_path, in_place=False, ignore_is_crypt=True, secret_key=secret_key, crypt_backend='Fernet')
        else:
            cred_yaml = decrypt_file(cred_path, in_place=False)
        cmdb_username = get_or_create_nested_yaml_attribute(cred_yaml, cmdb_username_attribute_path)
        cmdb_api_token = get_or_create_nested_yaml_attribute(cred_yaml, cmdb_api_token_attribute_path)
    return cmdb_url, cmdb_username, cmdb_api_token

def get_sbom_generator_deployer_config():
    work_dir = getenv_with_error('CI_PROJECT_DIR')
    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
    instances_dir = work_dir + '/environments'
    return get_deployer_config(f"{cluster_name}/{env_name}", work_dir, instances_dir, fallback_on_root_config=False)

