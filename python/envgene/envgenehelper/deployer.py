from pathlib import Path

from .config_helper import get_envgene_config_yaml
from .creds_helper import check_is_envgen_cred, get_cred_id_and_property_from_cred_macros
from .business_helper import find_env_instances_dir, getEnvDefinition, getenv_with_error
from .yaml_helper import openYaml, get_or_create_nested_yaml_attribute, find_yaml_file
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
        return cred_macros, None

def get_value_with_path_and_attribute(fp, attr_str, default_value=None):
    file = openYaml(fp)
    return get_or_create_nested_yaml_attribute(file, attr_str, default_value)

def get_deployer(env_name, instances_dir):
    env_path = find_env_instances_dir(env_name, instances_dir)
    data = getEnvDefinition(env_path)
    if "deployer" not in data["inventory"]:
        logger.warning(f"'deployer' key is not defined in inventory section of env definition")
        return None
    deployer_name = data['inventory']['deployer']
    return deployer_name

def find_env_deployer_definition(env_name, instances_dir) -> Path | None:
    env_dir = find_env_instances_dir(env_name, instances_dir)
    
    levels = [
        Path(env_dir).parent,
        Path(env_dir),
    ]
    
    deployer_dir_names = ["app-deployer", "cloud-deployer"]
    deployer_file_names = ["deployer", "app-deployer"]

    deployer_paths = [level / name for level in levels for name in deployer_dir_names]

    for p in deployer_paths:
        for file_name in deployer_file_names:
            found_path = find_yaml_file(p, file_name)
            if found_path:
                logger.info(f"Deployer configuration found in '{found_path}'")
                return found_path

    return None

def get_deployer_config(env_name, base_dir, instances_dir, secret_key=None, is_test=None, failonerror=True):
    basic_deployer_file_path = f"{base_dir}/configuration/deployer.yml"

    deployer_name = get_deployer(env_name, instances_dir)
    if not deployer_name:
        return "","",""
    env_deployer_file_path = find_env_deployer_definition(env_name, instances_dir)
    
    data = {}
    if env_deployer_file_path is not None:
        data = openYaml(env_deployer_file_path, allow_default=True)

    if deployer_name not in data:
        logger.info(f"Deployer with key {deployer_name} not found in environment specific configuration for {env_name}. Going to root configuration: {basic_deployer_file_path}")
        env_deployer_file_path = basic_deployer_file_path
        data = openYaml(env_deployer_file_path, allow_default=True)
    
        if deployer_name not in data:
            logger.error(f"Deployer with key {deployer_name} not found in {env_deployer_file_path}")
            if failonerror:
                raise ReferenceError(f"Deployer with key {deployer_name} not found. See logs above.")
            else:
                return "","",""

    deployer_dir = getDirName(env_deployer_file_path)
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
        if cmdb_username_attribute_path:
            cmdb_username = get_or_create_nested_yaml_attribute(cred_yaml, cmdb_username_attribute_path)
        if cmdb_api_token_attribute_path:
            cmdb_api_token = get_or_create_nested_yaml_attribute(cred_yaml, cmdb_api_token_attribute_path)
    return cmdb_url, cmdb_username, cmdb_api_token

def get_sbom_generator_deployer_config():
    work_dir = getenv_with_error('CI_PROJECT_DIR')
    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
    instances_dir = work_dir + '/environments'
    return get_deployer_config(f"{cluster_name}/{env_name}", work_dir, instances_dir)

