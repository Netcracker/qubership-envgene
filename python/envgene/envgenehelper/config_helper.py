from os import getenv, path
import json
from pathlib import Path

from envgenehelper import openYaml, get_empty_yaml, getenv_with_error
import jsonschema
from .logger import logger

ENVGENE_AGE_PUBLIC_KEY_ID = "ENVGENE_AGE_PUBLIC_KEY"
ENVGENE_AGE_PRIVATE_KEY_ID = "ENVGENE_AGE_PRIVATE_KEY"
PUBLIC_AGE_KEYS_ID = "PUBLIC_AGE_KEYS"
SECRET_KEY_ID = "SECRET_KEY"

FERNET_ID = "Fernet"
SOPS_ID = "SOPS"


def get_schema(schema_name):
    schemas_folder = "schemas"
    potential_paths = ['module', 'build_env', '']
    for pp in potential_paths:
        filepath = path.join(pp, schemas_folder, schema_name)
        if not path.isfile(filepath):
            continue
        with open(filepath) as f:
            return json.load(f)
    return None


def validate_config_file(config_yaml):
    secret_key = getenv(SECRET_KEY_ID, "")
    envgene_age_private_key = getenv(ENVGENE_AGE_PRIVATE_KEY_ID, "")
    public_age_keys = getenv(PUBLIC_AGE_KEYS_ID, "")

    crypt_backend = config_yaml.get('crypt_backend', 'Fernet')
    crypt_enabled = config_yaml.get('crypt', 'true')
    schema_name = 'config.schema.json'
    schema_data = get_schema(schema_name)
    logger.debug(f'Checking yaml with schema: {schema_name}')
    if schema_data:
        jsonschema.validate(config_yaml, schema_data)
    else:
        logger.info(f'Failed to find schema: {schema_name}')

    empty_parameters = []

    if (crypt_enabled):
        if crypt_backend == FERNET_ID and secret_key == "":
            raise Exception(
                f'Following CI/CD variables are not set: \n{SECRET_KEY_ID}.\nThis variable is mandatory for crypt_backend: {FERNET_ID}')
        if crypt_backend == SOPS_ID and (envgene_age_private_key == "" or public_age_keys == ""):
            if envgene_age_private_key == "":
                empty_parameters.append(ENVGENE_AGE_PRIVATE_KEY_ID)
            if public_age_keys == "":
                empty_parameters.append(PUBLIC_AGE_KEYS_ID)
            logger.info(f'list_of_empty_parameters: {empty_parameters}')
            raise Exception(
                f'Following CI/CD variables are not set: \n{empty_parameters}.\nThese variables are mandatory for crypt_backend: {SOPS_ID}')


def get_envgene_config_yaml():
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    envgene_config_path = Path(f"{base_dir}/configuration/config.yml")
    try:
        config = openYaml(envgene_config_path)
    except FileNotFoundError:
        logger.warning(f'Failed to find config file in {envgene_config_path}')
        return get_empty_yaml()
    validate_config_file(config)
    logger.debug(f"Config content: {config}")
    return config
