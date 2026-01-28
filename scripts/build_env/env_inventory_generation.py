from enum import Enum

import envgenehelper as helper
import envgenehelper.logger as logger
from envgenehelper import *
from envgenehelper.business_helper import INV_GEN_CREDS_PATH
from envgenehelper.env_helper import Environment
from typing_extensions import deprecated

from create_credentials import CRED_TYPE_SECRET

PARAMSETS_DIR_PATH = "Inventory/parameters/"
CLUSTER_TOKEN_CRED_ID = "cloud-deploy-sa-token"

SCHEMAS_DIR = getenv("JSON_SCHEMAS_DIR", path.join(path.dirname(path.dirname(path.dirname(__file__))), "schemas"))


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

    env_inventory_content = params.get('ENV_INVENTORY_CONTENT')
    env_inv_content_schema_path = path.join(SCHEMAS_DIR, "env-inventory-content.schema.json")
    validate_yaml_by_scheme_or_fail(input_yaml_content=env_inventory_content,
                                    schema_file_path=env_inv_content_schema_path)
    handle_env_inv_content(env_inventory_content)

    env = Environment(base_dir, cluster, env_name)
    logger.info(f"Starting env inventory generation for env: {env.name} in cluster: {env.cluster}")

    handle_env_inventory_init(env, env_inventory_init, env_template_version)
    handle_env_specific_params(env, env_specific_params)
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.name', env_template_name)

    helper.writeYamlToFile(env.inventory_path, env.inventory)
    helper.writeYamlToFile(env.creds_path, env.creds)
    helper.encrypt_file(env.creds_path)
    if env.inv_gen_creds:
        helper.writeYamlToFile(env.inv_gen_creds_path, env.inv_gen_creds)
        helper.encrypt_file(env.inv_gen_creds_path)


def handle_env_inventory_init(env, env_inventory_init, env_template_version):
    if env_inventory_init != "true":
        logger.info("ENV_INVENTORY_INIT is not set to 'true'. Skipping env inventory initialization")
        return
    logger.info(
        f"ENV_INVENTORY_INIT is set to 'true'. Generating new inventory in {helper.getRelPath(env.inventory_path)}")
    helper.check_dir_exist_and_create(env.env_path)
    env.inventory = helper.get_empty_yaml()
    helper.set_nested_yaml_attribute(env.inventory, 'inventory.environmentName', env.name)
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.artifact', env_template_version)
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.additionalTemplateVariables', helper.get_empty_yaml())
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.envSpecificParamsets', helper.get_empty_yaml())


@deprecated
def handle_env_specific_params(env, env_specific_params):
    if not env_specific_params or env_specific_params == "":
        logger.info("ENV_SPECIFIC_PARAMS are not set. Skipping env inventory update")
        return
    logger.info("Updating env inventory with ENV_SPECIFIC_PARAMS")
    logger.info("Updating >>> env inventory with ENV_SPECIFIC_PARAMS")
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
    logger.info("ENV_SPECIFIC_PARAMS env details ", vars(env))
    handle_credentials(env, creds)
    create_paramset_files(env, paramsets)

    helper.set_nested_yaml_attribute(env.inventory, 'inventory.tenantName', tenantName)
    helper.set_nested_yaml_attribute(env.inventory, 'inventory.tenantName', tenantName)

    logger.info(f"ENV_SPECIFIC_PARAMS env details : {vars(env)}")


def create_paramset_files(env, paramsets):
    if not paramsets:
        return
    PARAMSET_SCHEMA_PATH = path.join(SCHEMAS_DIR, "paramset.schema.json")
    ps_dir_path = path.join(env.env_path, PARAMSETS_DIR_PATH)
    helper.check_dir_exist_and_create(ps_dir_path)
    logger.info(f"Creating paramsets in {ps_dir_path}")
    for k, v in paramsets.items():
        jsonschema.validate(v, openYaml(PARAMSET_SCHEMA_PATH))
        filename = k + ".yml"
        ps_path = path.join(ps_dir_path, filename)
        helper.writeYamlToFile(ps_path, v)  # overwrites file
        logger.info(f"Created paramset {filename}")


def handle_credentials(env, creds):
    if not creds:
        return
    helper.merge_yaml_into_target(env.inv_gen_creds, '', creds)

    sharedMasterCredentialFiles = helper.get_or_create_nested_yaml_attribute(env.inventory,
                                                                             'envTemplate.sharedMasterCredentialFiles',
                                                                             default_value=[])
    sharedMasterCredentialFiles.append(path.basename(INV_GEN_CREDS_PATH))
    sharedMasterCredentialFiles = list(set(sharedMasterCredentialFiles))
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.sharedMasterCredentialFiles',
                                     sharedMasterCredentialFiles)


def handle_cluster_params(env, cluster_params):
    if not cluster_params:
        return
    if 'clusterEndpoint' in cluster_params:
        helper.set_nested_yaml_attribute(env.inventory, 'inventory.clusterUrl', cluster_params['clusterEndpoint'])
    if 'clusterToken' in cluster_params and 'cloud-deploy-sa-token' not in env.creds:
        cred = {'type': CRED_TYPE_SECRET, 'data': {'secret': cluster_params['clusterToken']}}
        helper.set_nested_yaml_attribute(env.creds, 'cloud-deploy-sa-token', cred, is_overwriting=False)


class Action(Enum):
    CREATE_OR_REPLACE = "create_or_replace"
    DELETE = "delete"


class Place(Enum):
    ENV = "env"
    CLUSTER = "cluster"
    SITE = "site"


def handle_env_def(env_dir: Path, env_def):
    if not env_def:
        return

    action = Action(env_def["action"])
    env_def_path = env_dir / "Inventory" / "env_definition.yml"

    if action is Action.DELETE:
        delete_dir(env_dir)
    else:
        writeYamlToFile(env_def_path, env_def.get("content"))


def handle_param_sets(env_dir: Path, param_sets: list[dict]):
    if not param_sets:
        return

    for ps in param_sets:
        place = Place(ps["place"])
        action = Action(ps["action"])
        name = ps["content"]["name"]

        ps_path = None
        if place == Place.ENV:
            ps_path = env_dir / "Inventory" / "parameters" / f"{name}.yml"
        elif place == Place.CLUSTER:
            ps_path = env_dir.parent / "parameters" / f"{name}.yml"
        elif place == Place.SITE:
            ps_path = env_dir.parent.parent / "parameters" / f"{name}.yml"

        if action == Action.CREATE_OR_REPLACE:
            content = ps.get("content")
            param_set_schema_path = path.join(SCHEMAS_DIR, "paramset.schema.json")
            validate_yaml_by_scheme_or_fail(
                input_yaml_content=content,
                schema_file_path=param_set_schema_path
            )
            writeYamlToFile(ps_path, content)

        elif action == Action.DELETE:
            deleteFileIfExists(ps_path)


def handle_credentials_2(env_dir: Path, credentials):
    if not credentials:
        return
    for cred in credentials:
        place = Place(cred["place"])
        action = Action(cred["action"])

        cred_path = None
        if place == Place.ENV:
            cred_path = env_dir / "Inventory" / "credentials" / f"{name}.yml"
        elif place == Place.CLUSTER:
            cred_path = env_dir.parent / "credentials" / f"{name}.yml"
        elif place == Place.SITE:
            cred_path = env_dir.parent.parent / "credentials" / f"{name}.yml"

        if action == Action.CREATE_OR_REPLACE:
            cred_schema_path = path.join(SCHEMAS_DIR, "credential.schema.json")
            content = cred["content"]
            validate_yaml_by_scheme_or_fail(
                input_yaml_content=content,
                schema_file_path=cred_schema_path
            )
            writeYamlToFile(cred_path, content)
        elif action == Action.DELETE:
            deleteFileIfExists(cred_path)


def handle_env_inv_content(env_inventory_content):
    env_dir = Path(get_current_env_dir_from_env_vars())

    handle_env_def(env_dir, env_inventory_content.get("envDefinition"))
    handle_param_sets(env_dir, env_inventory_content.get("paramSets"))
    handle_credentials_2(env_dir, env_inventory_content.get("credentials"))


if __name__ == "__main__":
    generate_env()
