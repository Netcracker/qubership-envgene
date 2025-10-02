from os import path, getenv

import json
import jsonschema

from create_credentials import CRED_TYPE_SECRET
import envgenehelper as helper
from envgenehelper import *
import envgenehelper.logger as logger
from envgenehelper.business_helper import INV_GEN_CREDS_PATH
from envgenehelper.env_helper import Environment

# const
PARAMSETS_DIR_PATH = "Inventory/parameters/"
CLUSTER_TOKEN_CRED_ID = "cloud-deploy-sa-token"

# Get schema path from environment variable or use default path
SCHEMAS_DIR = getenv("JSON_SCHEMAS_DIR", path.join(path.dirname(path.dirname(path.dirname(__file__))), "schemas"))
PARAMSET_SCHEMA_PATH = path.join(SCHEMAS_DIR, "paramset.schema.json")

with open(PARAMSET_SCHEMA_PATH, 'r') as f:
    PARAMSET_SCHEMA = json.load(f)


def generate_env():
    base_dir = getenv_and_log('CI_PROJECT_DIR')
    env_name = getenv_and_log('ENV_NAME')
    cluster = getenv_and_log('CLUSTER_NAME')

    params_json = getenv_and_log("ENV_GENERATION_PARAMS")
    params = json.loads(params_json)

    env_inventory_init = params['ENV_INVENTORY_INIT']
    env_specific_params = params['ENV_SPECIFIC_PARAMETERS']
    env_template_name = params['ENV_TEMPLATE_NAME']
    env_template_version = params['ENV_TEMPLATE_VERSION']

    env = Environment(base_dir, cluster, env_name)
    logger.info(f"Starting env inventory generation for env: {env.name} in cluster: {env.cluster}")

    handle_env_inventory_init(env, env_inventory_init, env_template_version)
    handle_env_specific_params(env, env_specific_params)
    handle_env_template_name(env, env_template_name)

    helper.writeYamlToFile(env.inventory_path, env.inventory)
    helper.writeYamlToFile(env.creds_path, env.creds)
    helper.encrypt_file(env.creds_path)
    if env.inv_gen_creds:
        helper.writeYamlToFile(env.inv_gen_creds_path, env.inv_gen_creds)
        helper.encrypt_file(env.inv_gen_creds_path)

def handle_env_inventory_init(env, env_inventory_init, env_template_version):
    if env_inventory_init != "true":
        logger.info(f"ENV_INVENTORY_INIT is not set to 'true'. Skipping env inventory initialization")
        return
    logger.info(f"ENV_INVENTORY_INIT is set to 'true'. Generating new inventory in {helper.getRelPath(env.inventory_path)}")
    helper.check_dir_exist_and_create(env.env_path)
    env.inventory = helper.get_empty_yaml()
    helper.set_nested_yaml_attribute(env.inventory, 'inventory.environmentName', env.name)
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.artifact', env_template_version)
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.additionalTemplateVariables', helper.get_empty_yaml())
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.envSpecificParamsets', helper.get_empty_yaml())

def handle_env_specific_params(env, env_specific_params):
    if not env_specific_params or env_specific_params == "":
        logger.info(f"ENV_SPECIFIC_PARAMS are not set. Skipping env inventory update")
        return
    logger.info(f"Updating env inventory with ENV_SPECIFIC_PARAMS")
    logger.info(f"Updating >>> env inventory with ENV_SPECIFIC_PARAMS")
    params = json.loads(env_specific_params)

    clusterParams = params.get("clusterParams")
    additionalTemplateVariables = params.get("additionalTemplateVariables")
    envSpecificParamsets = params.get("envSpecificParamsets")
    paramsets = params.get("paramsets")
    creds = params.get("credentials")
    tenantName = params.get("tenantName")
    deployer = params.get("deployer")
    logger.info(f"ENV_SPECIFIC_PARAMS TenantName is {tenantName}")
    logger.info(f"ENV_SPECIFIC_PARAMS deployer is {deployer}")

    handle_cluster_params(env, clusterParams)
    helper.set_nested_yaml_attribute(env.inventory, 'inventory.tenantName', tenantName)
    helper.set_nested_yaml_attribute(env.inventory, 'inventory.deployer', deployer)
    helper.merge_yaml_into_target(env.inventory, 'envTemplate.additionalTemplateVariables', additionalTemplateVariables)
    helper.merge_yaml_into_target(env.inventory, 'envTemplate.envSpecificParamsets', envSpecificParamsets)
    logger.info("ENV_SPECIFIC_PARAMS env details ",vars(env))
    handle_credentials(env, creds)
    create_paramset_files(env, paramsets)

    handle_tenant_name(env,tenantName)
    handle_deployer(env,deployer)

    logger.info(f"ENV_SPECIFIC_PARAMS env details : {vars(env)}")

def handle_tenant_name(env, tenantName):
    if not tenantName:
        return
    helper.set_nested_yaml_attribute(env.inventory, 'inventory.tenantName', tenantName)

def handle_deployer(env, deployer):
    if not deployer:
        return
    helper.set_nested_yaml_attribute(env.inventory, 'inventory.deployer', deployer)

def handle_env_template_name(env, env_template_name):
    if not env_template_name:
        return
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.name', env_template_name)

def create_paramset_files(env, paramsets):
    if not paramsets:
        return
    ps_dir_path = path.join(env.env_path, PARAMSETS_DIR_PATH)
    helper.check_dir_exist_and_create(ps_dir_path)
    logger.info(f"Creating paramsets in {ps_dir_path}")
    for k, v in paramsets.items():
        jsonschema.validate(v, PARAMSET_SCHEMA)
        filename = k + ".yml"
        ps_path = path.join(ps_dir_path, filename)
        helper.writeYamlToFile(ps_path, v) # overwrites file
        logger.info(f"Created paramset {filename}")

def handle_credentials(env, creds):
    if not creds:
        return
    helper.merge_yaml_into_target(env.inv_gen_creds, '', creds)

    sharedMasterCredentialFiles = helper.get_or_create_nested_yaml_attribute(env.inventory, 'envTemplate.sharedMasterCredentialFiles', default_value=[])
    sharedMasterCredentialFiles.append(path.basename(INV_GEN_CREDS_PATH))
    sharedMasterCredentialFiles = list(set(sharedMasterCredentialFiles))
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.sharedMasterCredentialFiles', sharedMasterCredentialFiles)

def handle_cluster_params(env, cluster_params):
    if not cluster_params:
        return
    if 'clusterEndpoint' in cluster_params:
        helper.set_nested_yaml_attribute(env.inventory, 'inventory.clusterUrl', cluster_params['clusterEndpoint'])
    if 'clusterToken' in cluster_params and 'cloud-deploy-sa-token' not in env.creds:
        cred = {}
        cred['type'] = CRED_TYPE_SECRET
        cred['data'] = {'secret': cluster_params['clusterToken']}
        helper.set_nested_yaml_attribute(env.creds, 'cloud-deploy-sa-token', cred, is_overwriting=False)

if __name__ == "__main__":
    generate_env()
