from dataclasses import dataclass, field
from os import path, getenv
import re

import ansible_runner
import json
import jsonschema

from create_credentials import CRED_TYPE_SECRET
import envgenehelper as helper
from envgenehelper import getenv_and_log
import envgenehelper.logger as logger

# const
PARAMSETS_DIR_PATH = "Inventory/parameters/"
INV_GEN_CREDS_PATH = "Inventory/credentials/inventory_generation_creds.yml"
CLUSTER_TOKEN_CRED_ID = "cloud-deploy-sa-token"

# Get schema path from environment variable or use default path
SCHEMAS_DIR = getenv("JSON_SCHEMAS_DIR", path.join(path.dirname(path.dirname(path.dirname(__file__))), "schemas"))
PARAMSET_SCHEMA_PATH = path.join(SCHEMAS_DIR, "paramset.schema.json")

with open(PARAMSET_SCHEMA_PATH, 'r') as f:
    PARAMSET_SCHEMA = json.load(f)

@dataclass
class Environment:
    base_dir: str
    cluster: str
    name: str
    env_path: str = field(init=False)
    inventory: dict = field(init=False) 
    inventory_path: str = field(init=False)
    creds: dict = field(init=False)
    creds_path: str = field(init=False)

    def __post_init__(self):
        self.env_path = path.join(self.base_dir, "environments", self.cluster, self.name)
        print(f"env_path: {self.env_path}")

        self.inventory_path = helper.getEnvDefinitionPath(self.env_path)
        print(f"inventory_path: {self.inventory_path}")

        self.creds_path = helper.getEnvCredentialsPath(self.env_path)
        print(f"creds_path: {self.creds_path}")

        self.inv_gen_creds_path = path.join(self.env_path, INV_GEN_CREDS_PATH)
        print(f"inv_gen_creds_path: {self.inv_gen_creds_path}")

        self.inventory = helper.openYaml(self.inventory_path, allow_default=True)
        print(f"inventory: {self.inventory}")

        self.creds = helper.decrypt_file(self.creds_path, in_place=False, allow_default=True)
        print(f"creds: {self.creds}")

        self.inv_gen_creds = helper.decrypt_file(self.inv_gen_creds_path, in_place=False, allow_default=True)
        print(f"inv_gen_creds: {self.inv_gen_creds}")

def generate_env():
    base_dir = getenv_and_log('CI_PROJECT_DIR')
    env_name = getenv_and_log('ENV_NAME')
    cluster = getenv_and_log('CLUSTER_NAME')

    params_json = getenv_and_log("ENV_GENERATION_PARAMS")
    params = json.loads(params_json)

    sd_source_type = params['SD_SOURCE_TYPE']
    sd_version = params['SD_VERSION']
    sd_data = params['SD_DATA']
    sd_delta = params['SD_DELTA']

    env_inventory_init = params['ENV_INVENTORY_INIT']
    env_specific_params = params['ENV_SPECIFIC_PARAMETERS']
    env_template_name = params['ENV_TEMPLATE_NAME']
    env_template_version = params['ENV_TEMPLATE_VERSION']

    env = Environment(base_dir, cluster, env_name)
    logger.info(f"Starting env inventory generation for env: {env.name} in cluster: {env.cluster}")

    handle_env_inventory_init(env, env_inventory_init, env_template_version)
    handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta)
    handle_env_specific_params(env, env_specific_params)
    handle_env_template_name(env, env_template_name)

    helper.writeYamlToFile(env.inventory_path, env.inventory)
    helper.writeYamlToFile(env.creds_path, env.creds)
    helper.encrypt_file(env.creds_path)
    if env.inv_gen_creds:
        helper.writeYamlToFile(env.inv_gen_creds_path, env.inv_gen_creds)
        helper.encrypt_file(env.inv_gen_creds_path)

def merge_sd(env, sd_data):
    destination = f'{env.env_path}/Inventory/solution-descriptor/sd.yaml'
    if helper.check_file_exists(destination):
        full_sd_yaml = helper.openYaml(destination)
        logger.info(f"full_sd.yaml before merge: {full_sd_yaml}")
    helper.check_dir_exist_and_create(path.dirname(destination))
    helper.merge(full_sd_yaml, sd_data, destination)
    logger.info(f"SD_DELTA has been merged! - {sd_data}")

def handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta):
    base_path = f'{env.env_path}/Inventory/solution-descriptor/'
    if not sd_source_type:
        logger.info("SD_SOURCE_TYPE is not specified, skipping SD file creation")
        return
    if sd_delta == "true":
        sd_path = base_path + 'delta_sd.yaml'
        full_sd_path = base_path + 'sd.yaml'
        if not helper.check_file_exists(full_sd_path):
            logger.error(f"To use the delta processing mode for SD, a complete SD must already be stored in the repository.\nThe file {full_sd_path} does not exist.")
            exit(1)
    else:
        sd_path = base_path + 'sd.yaml'
    helper.check_dir_exist_and_create(path.dirname(sd_path))
    if sd_source_type == "artifact": 
        download_sd_with_version(env, sd_path, sd_version, sd_delta)
    elif sd_source_type == "json": 
        extract_sd_from_json(env, sd_path, sd_data, sd_delta)
    else:
        logger.error(f'SD_SOURCE_TYPE must be set either to "artifact" or "json"')
        exit(1)

def extract_sd_from_json(env, sd_path, sd_data, sd_delta):
    if not sd_data:
        logger.error(f"SD_SOURCE_TYPE is set to 'json', but SD_DATA was not given in pipeline variables")
        exit(1)
    data = json.loads(sd_data)
    helper.writeYamlToFile(sd_path, data)
    if sd_delta == "true":
        data = helper.openYaml(sd_path)
        merge_sd(env, data)
    logger.info(f"SD successfully extracted from SD_DATA and is saved in {sd_path}")

def download_sd_with_version(env, sd_path, sd_version, sd_delta):
    logger.info(f"sd_version: {sd_version}")
    if not sd_version:
        logger.error(f"SD_SOURCE_TYPE is set to 'artifact', but SD_VERSION was not given in pipeline variables")
        exit(1)

    sd_split = sd_version.split(":")
    source_name, version = sd_split[0], sd_split[1]
    logger.info(f"Starting download SD {source_name}-{version}")

    pattern = rf".*/{re.escape(source_name)}\.(ya?ml)$"
    artifact_definitions = helper.findYamls(f'{env.base_dir}/configuration/artifact_definitions/', "", additionalRegexpPattern=pattern)
    artifact_definition = helper.openYaml(artifact_definitions[0])
    logger.info(f'artifact_definition = {artifact_definition}')

    ansible_vars = {}
    ansible_vars["version"] = version
    ansible_vars["artifact_definition"] = artifact_definition
    ansible_vars["envgen_debug"] = 'true'
    r = ansible_runner.run(playbook='/module/ansible/download_sd_file.yaml',envvars=ansible_vars, verbosity=2)
    if (r.rc != 0):
        logger.error(f"Error during ansible execution. Result code is: {r.rc}. Status is: {r.status}")
        raise ReferenceError(f"Error during ansible execution. See logs above.")
    else:
        logger.info(f"Ansible execution status is: {r.status}. Stats is: {r.stats}")

    with open("/tmp/sd.json", 'r') as f:
        sd = json.load(f)
    helper.writeYamlToFile(sd_path, sd)
    if sd_delta == "true":
        sd_data = helper.openYaml(sd_path)
        merge_sd(env, sd_data)

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
    helper.merge_yaml_into_target(env.inventory, 'envTemplate.additionalTemplateVariables', additionalTemplateVariables)
    helper.merge_yaml_into_target(env.inventory, 'envTemplate.envSpecificParamsets', envSpecificParamsets)
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
