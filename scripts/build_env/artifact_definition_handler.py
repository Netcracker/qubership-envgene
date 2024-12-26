from yaml import safe_load, safe_dump
from envgenehelper import *
from envgenehelper.deployer import *
import argparse


def handler_artifact_definition(template_name, mode, directory):
    logger.info(f"template name  {template_name}, mode {mode}, directory {directory}.")
    find_registry_configuration(template_name, directory)

def find_registry_configuration(template_name, base_path):
    env_name = getenv('ENV_NAME')
    work_dir = getenv('CI_PROJECT_DIR')
    instances_dir = getenv('INSTANCES_DIR')
    secret_key = getenv('SECRET_KEY')
    cmdb_url, cmdb_username, cmdb_api_token = get_deployer_config(env_name, work_dir, instances_dir, secret_key)
    newpath = r'tmp'
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    cli_path = '/work/application'
    exit_code = os.system(f'{cli_path} config export applicationsdefinition --url {cmdb_url} --auth {cmdb_username}:{cmdb_api_token} --target {newpath} "{template_name}"')
    if (exit_code):
        logger.error(exit_code)
        logger.error(f"Error during find applicationsdefinition for application {template_name}")
        exit(1)

    with open(f"{newpath}/ApplicationsDefinition/{template_name}.yml", mode="r", encoding="utf-8") as file:
        applications_definition = safe_load(file)

    registry_name = applications_definition['registryName']

    exit_code = os.system(f'{cli_path} config export registries --url {cmdb_url} --auth {cmdb_username}:{cmdb_api_token} --target {newpath} "{registry_name}"')
    if (exit_code):
        logger.error(f"Error during find registry {template_name}")
        exit(1)

    with open(f"{newpath}/Registries/{registry_name}.yml", mode="r", encoding="utf-8") as file:
        registry = safe_load(file)

    create_credentials(base_path, registry)
    applications_definition['registry'] = registry

    app_definition = getAppDefinitionPath(base_path, template_name)
    check_dir_exist_and_create(f"{base_path}/configuration/artifact_definitions")

    with open(app_definition, mode="w") as final_registry:
        safe_dump(applications_definition, final_registry)
    beautifyYaml(app_definition, "schemas/application-definition.schema.json", remove_additional_props=True)


def create_credentials(base_path, registry):
    if registry['credentialsId'] is None or registry['credentialsId'] == '':
        registry['credentialsId'] = "artifactorycn-cred"
    cred_path = findYamls(f'{base_path}/configuration/credentials', "credentials.y")[0]
    credsYaml = openYaml(cred_path)
    if not registry['credentialsId'] in credsYaml.keys():
        newCred = yaml.load("{}")
        newCred.insert(1, "type", "usernamePassword")

        if registry['credentialsId'] == "artifactorycn-cred":
            data = yaml.load("{}")
            data.insert(1, "username", "")
            data.insert(1, "password", "")
            newCred["data"] = data
        else:
            data = yaml.load("{}")
            data.insert(1, "username", None, "FillMe")
            data.insert(1, "password", None, "FillMe")
            newCred["data"] = data

        store_value_to_yaml(credsYaml, registry['credentialsId'], newCred)
        writeYamlToFile(cred_path, credsYaml)


def read_artifact_definitions_file(template_name, base_path):
    app_definition_path = getAppDefinitionPath(base_path, template_name)
    artifact = None
    try:
        with open(app_definition_path, mode="r", encoding="utf-8") as file:
            artifact = safe_load(file)
    except IOError:
        try:
            with open(app_definition_path.replace('yaml', 'yml'), mode="r", encoding="utf-8") as file:
                artifact = safe_load(file)
        except IOError:
            logger.error(f"file for template {template_name} not found.")

    return artifact


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--t', help="Template artifact name", type=str)
    parser.add_argument('--m', help="Artifact definitions discovery mode", type=str)
    parser.add_argument('--o', help="Base directory", type=str)
    args = parser.parse_args()
    decrypt_all_cred_files_for_env()
    handler_artifact_definition(args.t, args.m, args.o)
    encrypt_all_cred_files_for_env()
