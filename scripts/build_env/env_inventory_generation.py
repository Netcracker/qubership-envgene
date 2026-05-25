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
INVENTORY = "Inventory"
DEPRECATED_MESSAGE = "Deprecated inventory generation approach"
SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


def generate_env_new_approach():
    env_name = getenv_with_error('ENV_NAME')
    cluster = getenv_with_error('CLUSTER_NAME')
    logger.info(f"Starting env inventory generation for env: {env_name} in cluster: {cluster}")

    env_inventory_content = json.loads(getenv_with_error('ENV_INVENTORY_CONTENT'))
    env_inv_content_schema_path = path.join(SCHEMAS_DIR, "env-inventory-content.schema.json")

    validate_yaml_by_scheme_or_fail(input_yaml_content=env_inventory_content,
                                    schema_file_path=env_inv_content_schema_path,
                                    schemas_dir=SCHEMAS_DIR)

    handle_env_inv_content(env_inventory_content)


@deprecated(DEPRECATED_MESSAGE)
def generate_env():
    base_dir = getenv_and_log('CI_PROJECT_DIR')
    env_name = getenv_and_log('ENV_NAME')
    cluster = getenv_and_log('CLUSTER_NAME')

    env_inventory_init = getenv('ENV_INVENTORY_INIT')
    env_specific_params = getenv('ENV_SPECIFIC_PARAMS')
    env_template_name = getenv('ENV_TEMPLATE_NAME')

    env_template_version = getenv('ENV_TEMPLATE_VERSION')

    env = Environment(base_dir, cluster, env_name)
    logger.info(f"Starting env inventory generation for env: {env.name} in cluster: {env.cluster}")

    handle_env_inventory_init(env, env_inventory_init, env_template_version)
    handle_env_specific_params(env, env_specific_params, SCHEMAS_DIR)
    helper.set_nested_yaml_attribute(env.inventory, 'envTemplate.name', env_template_name)

    helper.writeYamlToFile(env.inventory_path, env.inventory)
    helper.writeYamlToFile(env.creds_path, env.creds)
    helper.encrypt_file(env.creds_path)
    if env.inv_gen_creds:
        helper.writeYamlToFile(env.inv_gen_creds_path, env.inv_gen_creds)
        helper.encrypt_file(env.inv_gen_creds_path)


@deprecated(DEPRECATED_MESSAGE)
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


@deprecated(DEPRECATED_MESSAGE)
def handle_env_specific_params(env, env_specific_params, schemas_dir):
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
    create_paramset_files(env, paramsets, schemas_dir)

    helper.set_nested_yaml_attribute(env.inventory, 'inventory.tenantName', tenantName)
    helper.set_nested_yaml_attribute(env.inventory, 'inventory.tenantName', tenantName)

    logger.info(f"ENV_SPECIFIC_PARAMS env details : {vars(env)}")


@deprecated(DEPRECATED_MESSAGE)
def create_paramset_files(env, paramsets, schemas_dir):
    if not paramsets:
        return
    PARAMSET_SCHEMA_PATH = path.join(schemas_dir, "paramset.schema.json")
    ps_dir_path = path.join(env.env_path, PARAMSETS_DIR_PATH)
    helper.check_dir_exist_and_create(ps_dir_path)
    logger.info(f"Creating paramsets in {ps_dir_path}")
    for k, v in paramsets.items():
        jsonschema.validate(v, openYaml(PARAMSET_SCHEMA_PATH))
        filename = k + ".yml"
        ps_path = path.join(ps_dir_path, filename)
        helper.writeYamlToFile(ps_path, v)  # overwrites file
        logger.info(f"Created paramset {filename}")


@deprecated(DEPRECATED_MESSAGE)
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


@deprecated(DEPRECATED_MESSAGE)
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


def resolve_path(env_dir: Path, place: Place, subdir: str, name: str, inventory: str = "") -> Path:
    if place is Place.ENV:
        base = env_dir / inventory
    elif place is Place.CLUSTER:
        base = env_dir.parent
    elif place is Place.SITE:
        base = env_dir.parent.parent
    else:
        raise ValueError(place)
    return base / subdir / f"{name}.yml"


def handle_objects(env_dir, objects, subdir, inventory="", encrypt=False):
    if not objects:
        logger.info(f"No objects for {subdir}, skipping")
        return

    for obj in objects:
        place = Place(obj["place"])
        action = Action(obj["action"])
        content = obj["content"]

        name = content["name"] if content.get("name") else obj["name"]
        obj_path = resolve_path(env_dir, place, subdir, name, inventory)

        logger.info(f"Processing {subdir}, action={action.value}, place={place.value}. Target path: {obj_path}")
        if action is Action.CREATE_OR_REPLACE:
            writeYamlToFile(obj_path, content)
            if encrypt:
                encrypt_file(obj_path)
            beautifyYaml(obj_path)

        elif action is Action.DELETE:
            logger.info(f"Deleting file: {obj_path}")
            deleteFileIfExists(obj_path)


def handle_env_def(env_dir: Path, env_def: dict | None):
    env_template_version = getenv('ENV_TEMPLATE_VERSION')
    if not env_def:
        logger.info("env_definition is not provided, skipping")
        return

    action = Action(env_def["action"])
    env_def_path = env_dir / INVENTORY / "env_definition.yml"
    logger.info(f"Processing env_definition, action={action.value}. Target path: {env_def_path}")
    if action is Action.DELETE:
        logger.info(f"Deleting environment directory: {env_dir}")
        delete_dir(env_dir)
    else:
        content = env_def.get("content")
        if env_template_version:
            logger.info(f"Overriding envTemplate.artifact with ENV_TEMPLATE_VERSION={env_template_version}")
            content["envTemplate"]["artifact"] = env_template_version
        writeYamlToFile(env_def_path, content)
        beautifyYaml(env_def_path)
        logger.info("env_definition.yml successfully created/updated")


def handle_env_inv_content(env_inventory_content: dict):
    env_dir = Path(get_current_env_dir_from_env_vars())

    handle_env_def(env_dir, env_inventory_content.get("envDefinition"))

    handle_objects(env_dir, env_inventory_content.get("paramSets"), "parameters", INVENTORY)
    handle_objects(env_dir, env_inventory_content.get("credentials"), "credentials", INVENTORY, encrypt=True)
    handle_objects(env_dir, env_inventory_content.get("resourceProfiles"), "resource_profiles", INVENTORY)
    handle_objects(env_dir, env_inventory_content.get("sharedTemplateVariables"), "shared_template_variables")


if __name__ == "__main__":

    if getenv('ENV_INVENTORY_CONTENT'):
        logger.info("Using new inventory generation approach")
        generate_env_new_approach()
    else:
        logger.info("Using old inventory generation approach")
        generate_env()
