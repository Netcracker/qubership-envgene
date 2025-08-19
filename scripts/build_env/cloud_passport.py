import re
import sys
import os
from envgenehelper import *
from schema_validation import checkCloudPassportBySchema

# const
CLOUD_SUBSTITUTIONS = {
    "apiUrl": "CLOUD_API_HOST",
    "apiPort": "CLOUD_API_PORT",
    "privateUrl": "CLOUD_PRIVATE_HOST",
    "publicUrl": "CLOUD_PUBLIC_HOST",
    "dashboardUrl": "CLOUD_DASHBOARD_URL",
    "defaultCredentialsId": "CLOUD_DEPLOY_TOKEN",
    "protocol": "CLOUD_PROTOCOL",
    "productionMode":"PRODUCTION_MODE"
}

def process_and_update_key(targetKey, targetYaml, sourceKey, sourceYaml, comment) :
    merge_dict_key_with_comment(targetKey, targetYaml, sourceKey, sourceYaml, comment)
    del sourceYaml[sourceKey]

def mergeDeployParametersFromPassport(cloudPassportYaml, cloudYaml, comment) :
    for domain in cloudPassportYaml:
        if domain == "version": continue
        for paramKey, paramValue in cloudPassportYaml[domain].items():
            store_value_to_yaml(cloudYaml["deployParameters"], paramKey, paramValue, comment)

def process_cloud_definition(cloudPassportYaml, env_dir, comment) :
    cloud_schema="schemas/cloud.schema.json"
    # cloud
    cloudYamlPath = f"{env_dir}/cloud.yml"
    cloudYaml = openYaml(cloudYamlPath)
    for cloudKey, passportKey in CLOUD_SUBSTITUTIONS.items() :
        process_and_update_key(cloudKey, cloudYaml, passportKey, cloudPassportYaml["cloud"], comment)
        if (passportKey == "CLOUD_DASHBOARD_URL"):
          # CLOUD_DASHBOARD_URL variable should be both in cloud section and in deploy parameters
          store_value_to_yaml(cloudYaml["deployParameters"], "CLOUD_DASHBOARD_URL", cloudYaml[cloudKey], comment)
    # maas
    if "maas" in cloudPassportYaml :
        maasPassportYaml = cloudPassportYaml["maas"]
        # if maas is presented in cloud passport - than maas is enabled
        store_value_to_yaml(cloudYaml["maasConfig"], "enable", True, comment)
        store_value_to_yaml(cloudYaml["maasConfig"], "credentialsId", get_cred_id_from_cred_macros(maasPassportYaml["MAAS_CREDENTIALS_USERNAME"]), comment)
        process_and_update_key("maasUrl", cloudYaml["maasConfig"], "MAAS_SERVICE_ADDRESS", maasPassportYaml, comment)
        process_and_update_key("maasInternalAddress", cloudYaml["maasConfig"], "MAAS_INTERNAL_ADDRESS", maasPassportYaml, comment)
        del cloudPassportYaml["maas"]
    if "vault" in cloudPassportYaml :
        vaultPassportYaml = cloudPassportYaml["vault"]
        vaultUrl = vaultPassportYaml["VAULT_ADDR"]
        if vaultUrl :
            store_value_to_yaml(cloudYaml["vaultConfig"], "credentialsId", get_cred_id_from_cred_macros(vaultPassportYaml["VAULT_AUTH_ROLE_ID"]), comment)
            store_value_to_yaml(cloudYaml["vaultConfig"], "enable", True, comment)
            store_value_to_yaml(cloudYaml["vaultConfig"], "url", vaultUrl, comment)
        else :
            store_value_to_yaml(cloudYaml["vaultConfig"], "credentialsId", "", comment)
            store_value_to_yaml(cloudYaml["vaultConfig"], "enable", False, comment)
            store_value_to_yaml(cloudYaml["vaultConfig"], "url", "", comment)
        del cloudPassportYaml["vault"]
    if "dbaas" in cloudPassportYaml :
        dbaasPassportYaml = cloudPassportYaml["dbaas"]
        if "dbaasConfigs" not in cloudYaml or len(cloudYaml["dbaasConfigs"]) != 1 :
            cloudYaml["dbaasConfigs"] = yaml.load("[]")
            cloudYaml["dbaasConfigs"].append(yaml.load("enable: false"))
        dbaasConfigYaml = cloudYaml["dbaasConfigs"][0]
        store_value_to_yaml(dbaasConfigYaml, "credentialsId", get_cred_id_from_cred_macros(dbaasPassportYaml["DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME"]), comment)
        store_value_to_yaml(dbaasConfigYaml, "enable", True, comment)
        process_and_update_key("apiUrl", dbaasConfigYaml, "API_DBAAS_ADDRESS", dbaasPassportYaml, comment)
        process_and_update_key("aggregatorUrl", dbaasConfigYaml, "DBAAS_AGGREGATOR_ADDRESS", dbaasPassportYaml, comment)
        del cloudPassportYaml["dbaas"]
    if "consul" in cloudPassportYaml :
          consulPassportYaml = cloudPassportYaml["consul"]
          consulConfigYaml = cloudYaml["consulConfig"]
          store_value_to_yaml(consulConfigYaml, "tokenSecret", get_cred_id_from_cred_macros(consulPassportYaml["CONSUL_ADMIN_TOKEN"]), comment)
          process_and_update_key("enabled", consulConfigYaml, "CONSUL_ENABLED", consulPassportYaml, comment)
          process_and_update_key("publicUrl", consulConfigYaml, "CONSUL_PUBLIC_URL", consulPassportYaml, comment)
          process_and_update_key("internalUrl", consulConfigYaml, "CONSUL_URL", consulPassportYaml, comment)
          # CONSUL_ENABLED variable should be both in consul section and in deploy parameters
          store_value_to_yaml(cloudYaml["deployParameters"], "CONSUL_ENABLED", f"{consulConfigYaml['enabled']}".lower(), comment)
          del cloudPassportYaml["consul"]
    # adding rest of cloud passport parameters to cloud deploy parameters
    logger.debug(f"Rest of params from cloud passport are: \n{dump_as_yaml_format(cloudPassportYaml)}")
    mergeDeployParametersFromPassport(cloudPassportYaml, cloudYaml, comment)
    # storing cloud yaml
    writeYamlToFile(cloudYamlPath, cloudYaml)
    beautifyYaml(cloudYamlPath, cloud_schema)

def add_cloud_passport_creds(cloud_passport_name, cloud_passport_file_path, env_dir, comment):
    logger.info(f"Searching credentials for cloud passport {cloud_passport_file_path}")
    credsSchema="schemas/credential.schema.json"
    # first searching in subfolder
    passportSubfolderPath = f'{getDirName(cloud_passport_file_path)}/credentials/{cloud_passport_name}.yml'
    # then searching in the same folder with name pattern "{cloud_passport_name}-creds.yml"
    passportSameFolderPath = f'{getDirName(cloud_passport_file_path)}/{cloud_passport_name}-creds.yml'
    if os.path.exists(passportSubfolderPath):
        passportCredsYaml = openYaml(passportSubfolderPath)
        logger.info(f"Adding cloud passport credentials from {passportSubfolderPath}")
    elif os.path.exists(passportSameFolderPath):
        passportCredsYaml = openYaml(passportSameFolderPath)
        beautifyYaml(passportSameFolderPath, credsSchema)
        logger.info(f"Adding cloud passport credentials from {passportSameFolderPath}")
    else:
        logger.error(f"No cloud pasport credentials files found in either {passportSubfolderPath} or {passportSameFolderPath}.")
        raise ReferenceError(f"No cloud pasport credentials files found. See logs above")
    envCredentialsPath = f"{env_dir}/Credentials/credentials.yml"
    if os.path.exists(envCredentialsPath) :
        envCredsYaml = openYaml(envCredentialsPath)
    else:
        envCredsYaml = yaml.load("{}")
    for key, value in passportCredsYaml.items() :
        store_value_to_yaml(envCredsYaml, key, value, comment)
    # storing credentials yaml
    writeYamlToFile(envCredentialsPath, envCredsYaml)
    beautifyYaml(envCredentialsPath, credsSchema)

def update_env_definition_with_cloud_name(render_env_dir, source_env_dir, all_instances_dir):
    inventoryYaml = getEnvDefinition(render_env_dir)
    cloudName = find_cloud_name_from_passport(source_env_dir, all_instances_dir)
    if cloudName:
        logger.info(f"Env definition for {render_env_dir} updated with cloud name: {cloudName}")
        inventoryYaml["inventory"]["passportCloudName"] = cloudName
        writeYamlToFile(getEnvDefinitionPath(render_env_dir), inventoryYaml)
    else:
        logger.info(f"No cloud name found for env {render_env_dir} from passport")

def process_cloud_passport(render_env_dir, env_instances_dir, instances_dir) :
    logger.info(f"Trying to find cloud passport definition file")
    cloudPassportFilePath = find_cloud_passport_definition(env_instances_dir, instances_dir)
    cloudPassportFileName = extractNameFromFile(cloudPassportFilePath)
    # checking passport by schema
    checkCloudPassportBySchema(render_env_dir, cloudPassportFilePath)
    if cloudPassportFilePath:
        logger.info(f"Processing cloud passport: {cloudPassportFilePath}")
        cloudPassportYaml = openYaml(cloudPassportFilePath)
        comment = f"cloud passport: {cloudPassportFileName} version: {cloudPassportYaml['version']}"
        process_cloud_definition(cloudPassportYaml, render_env_dir, comment)
        add_cloud_passport_creds(cloudPassportFileName, cloudPassportFilePath, render_env_dir, comment)
    else:
        logger.info("No cloud passport definition found. Cloud passport processing skipped...")
