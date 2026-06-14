from pathlib import Path
import os
from envgenehelper import *
from typing import Optional, Set

#const
CRED_TYPE_SECRET="secret"
CRED_TYPE_USERPASS="usernamePassword"
CRED_TYPE_VAULT="vaultAppRole"
CRED_TYPE_EXTERNAL="external"

def createCredDefinition(credId, credType) :
    cred = {}
    cred["credentialsId"] = credId.strip("\"")
    cred["type"] = credType
    return cred

def processParametersAndAppend(paramTypeKey, paramsDict, credsList, tenantName, cloudName="", namespaceName="", comment="", external_cred_ids=None) :
    if paramTypeKey not in paramsDict.keys():
        return
    processDictAndAppend(paramsDict[paramTypeKey], credsList, tenantName, cloudName, namespaceName, comment, external_cred_ids)

def processDictAndAppend(params, credsList, tenantName, cloudName, namespaceName, comment, external_cred_ids=None):
    for key, value in params.items():
        processSingleParam(key, value, credsList, tenantName, cloudName, namespaceName, comment, external_cred_ids)

def processSingleParam(key, value, credsList, tenantName, cloudName, namespaceName, comment, external_cred_ids: Optional[Set[str]] = None):
    if isinstance(value, dict):
        cred_id = extract_external_cred(value)
        if cred_id and external_cred_ids is not None:
            external_cred_ids.add(cred_id)
            return
        processDictAndAppend(value, credsList, tenantName, cloudName, namespaceName, comment, external_cred_ids)
    elif isinstance(value, list): # if is array, than iterate
        for idx, item in enumerate(value):
            value[idx] = processSingleParam(idx, item, credsList, tenantName, cloudName, namespaceName, comment, external_cred_ids)
    elif isinstance(value, str):
        if check_is_cred(key, value):
            appendCredList(get_cred_list_from_param(key, value, True, tenantName, cloudName, namespaceName), credsList, comment)

def checkCredAndAppend(credName, credsList, secretType, comment="", is_external_cred_env=False, external_cred_ids=None):
    if (credName):
        if is_external_cred_env and external_cred_ids is not None:
            external_cred_ids.add(credName)
            return
        appendCredList([createCredDefinition(credName, secretType)], credsList, comment)
    return credsList

def appendCredList(additionalCreds, wholeCredsList, comment=""):
    for cred in additionalCreds:
        credMeta = {}
        credMeta["cred"] = cred
        credMeta["comment"] = comment
        wholeCredsList.append(credMeta)

def getTenantCreds(tenantContent, tenantName, is_external_cred_env=False, external_cred_ids=None):
    creds = []
    tenantComment = f"tenant {tenantName}"
    checkCredAndAppend(tenantContent["credential"], creds, CRED_TYPE_SECRET, tenantComment, is_external_cred_env, external_cred_ids)
    #process deployParameters
    processParametersAndAppend("deployParameters", tenantContent, creds, tenantName, comment=tenantComment,  external_cred_ids=external_cred_ids)
    processParametersAndAppend("environmentParameters", tenantContent["globalE2EParameters"], creds, tenantName, comment=tenantComment)
    return creds

def validate_external_creds(env_creds_map, external_cred_ids):    
    not_found_creds = [
        cred_name for cred_name in external_cred_ids
        if cred_name not in env_creds_map
    ]
    if not_found_creds:
        raise ValueError(
                f"Following external credentials:\n {not_found_creds}\n referred in environment are not found in any external credential source")
    orphan_creds = [
        cred_name
        for cred_name, cred_config in env_creds_map.items()
        if cred_config.get("type") == "external"
        and cred_name not in external_cred_ids
    ]   
    if orphan_creds:
        logger.warning(f"Following external credentials:\n{orphan_creds}\n"
            f"exist in external credential source but are not referred in environment"
        )
    logger.info(f'External creds processed from environment: {external_cred_ids}')


def getCloudCreds(cloudContent, tenantName, cloudName, is_external_cred_env=False, external_cred_ids=None):
    creds = []
    cloudComment = f"cloud {cloudName}"
    checkCredAndAppend(cloudContent["defaultCredentialsId"], creds, CRED_TYPE_SECRET, cloudComment, is_external_cred_env, external_cred_ids)
    checkCredAndAppend(cloudContent["maasConfig"]["credentialsId"], creds, CRED_TYPE_USERPASS, cloudComment, is_external_cred_env, external_cred_ids)
    checkCredAndAppend(cloudContent["vaultConfig"]["credentialsId"], creds, CRED_TYPE_SECRET, cloudComment, is_external_cred_env, external_cred_ids)
    checkCredAndAppend(cloudContent["consulConfig"]["tokenSecret"], creds, CRED_TYPE_SECRET, cloudComment, is_external_cred_env, external_cred_ids)
    for i in cloudContent["dbaasConfigs"]:
        checkCredAndAppend(i["credentialsId"], creds, CRED_TYPE_USERPASS, cloudComment, is_external_cred_env, external_cred_ids)

    #process deployParameters
    processParametersAndAppend("deployParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment, external_cred_ids=external_cred_ids)
    #process e2eParameters
    processParametersAndAppend("e2eParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment)

    return creds

def get_bg_domain_creds(content, name, is_external_cred_env=False, external_cred_ids=None):
    creds = []
    bg_domain_comment = f"bg domain {name}"
    checkCredAndAppend(content["controllerNamespace"]["credentials"], creds, CRED_TYPE_SECRET, bg_domain_comment, is_external_cred_env, external_cred_ids)
    return creds

def getNamespaceCreds(namespaceContent, tenantName, cloudName, namespaceName, is_external_cred_env=False, external_cred_ids=None):
    creds = []
    namespaceComment = f"namespace {namespaceName}"
    checkCredAndAppend(namespaceContent["credentialsId"], creds, CRED_TYPE_SECRET, namespaceComment, is_external_cred_env, external_cred_ids)
    #process deployParameters
    processParametersAndAppend("deployParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment, external_cred_ids=external_cred_ids)
    #process e2eParameters
    processParametersAndAppend("e2eParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment)
    return creds

def getApplicationCreds(appPath, tenantName, cloudName, namespaceName="", external_cred_ids=None):
    creds = []
    appContent = openYaml(appPath)
    appName = appContent["name"]
    if namespaceName :
        comment = f"namespace {namespaceName} application {appName}"
    else:
        comment = f"cloud {cloudName} application {appName}"
    #process deployParameters
    processParametersAndAppend("deployParameters", appContent, creds, tenantName, cloudName, namespaceName, comment=comment, external_cred_ids=external_cred_ids)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", appContent, creds, tenantName, cloudName, namespaceName, comment=comment)
    return creds

def mergeCreds(newCreds, allCreds) :
    count = 0
    for cred in newCreds :
        if not any(c["cred"]["credentialsId"] == cred["cred"]["credentialsId"] for c in allCreds) :
            count = count + 1
            allCreds.append(cred)
    return { "countAdded": count, "mergedCreds" : allCreds }

def getCredDefinitionYaml(yamlPath):
    result = yaml.load("{}")
    os.makedirs(os.path.dirname(yamlPath), exist_ok=True)
    if os.path.exists(yamlPath):
        result = openYaml(yamlPath)
    return result

def writeCredToYaml(credItem, credsYaml) :
    cred = credItem["cred"]
    comment = credItem["comment"]
    newCred = yaml.load("{}")
    #newCred.insert(1, "credentialsId", cred["credentialsId"])
    newCred.insert(1, "type", cred["type"])
    if (cred["type"] == CRED_TYPE_USERPASS) :
        data = yaml.load("{}")
        data.insert(1, "username", "envgeneNullValue", "FillMe")
        data.insert(1, "password", "envgeneNullValue", "FillMe")
        newCred["data"] = data
    elif (cred["type"] == CRED_TYPE_SECRET):
        data = yaml.load("{}")
        data.insert(1, "secret", "envgeneNullValue", "FillMe")
        newCred["data"] = data
    elif (cred["type"] == CRED_TYPE_VAULT):
        data = yaml.load("{}")
        data.insert(1, "roleId", "envgeneNullValue", "FillMe")
        data.insert(1, "secretId", "envgeneNullValue", "FillMe")
        data.insert(1, "path", "envgeneNullValue", "FillMe")
        data.insert(1, "namespace", "envgeneNullValue", "FillMe")
        newCred["data"] = data
    if (comment):
        store_value_to_yaml(credsYaml, cred["credentialsId"], newCred, comment)
    else:
        store_value_to_yaml(credsYaml, cred["credentialsId"], newCred)
    return credsYaml

def mergeAndSaveYaml(yamlPath, newCreds) :
    logger.info(f'"Saving credentials to file: {yamlPath}')
    count = 0
    credsYaml = getCredDefinitionYaml(yamlPath)
    for cred in newCreds :
        if not cred["cred"]["credentialsId"] in credsYaml:
            count = count + 1
            credsYaml = writeCredToYaml(cred, credsYaml)
    logger.info("%s credentials created" % count)
    writeYamlToFile(yamlPath, credsYaml)


def findSharedCredentials(cred_name, env_dir, instances_dir) -> Path:
    levels = [
        Path(env_dir) / "Inventory",
        Path(env_dir).parent,
        Path(instances_dir),
    ]
    
    cred_dir_names = ["credentials", "Credentials", "shared-credentials"]

    shared_cred_paths = [level / name for level in levels for name in cred_dir_names]

    for p in shared_cred_paths:
        found_path = find_yaml_file(p, cred_name, recursively=True)
        if found_path:
            logger.info(f"Shared credentials with key '{cred_name}' found in '{found_path}'")
            return found_path

    raise FileNotFoundError(f"Shared credentials with key '{cred_name}' not found.")


def mergeSharedCreds(credYamlPath, envDir, instancesDir) :
    inventoryYaml = getEnvDefinition(envDir)
    credsYaml = openYaml(credYamlPath)
    if ("sharedMasterCredentialFiles" in inventoryYaml["envTemplate"]) :
        sharedDictFileNames = inventoryYaml["envTemplate"]["sharedMasterCredentialFiles"]
        logger.info(f"Inventory shared master creds list: \n{dump_as_yaml_format(sharedDictFileNames)}")
        for credFileName in inventoryYaml["envTemplate"]["sharedMasterCredentialFiles"] :
            credFilePath = findSharedCredentials(credFileName, envDir, instancesDir)
            credYaml = openYaml(credFilePath)
            count = 0
            for key in credYaml :
                store_value_to_yaml(credsYaml, key, credYaml[key], f"shared credentials: {credFileName}")
                count += 1
            logger.info(f"Added {count} shared master credentials from {credFilePath}")
    writeYamlToFile(credYamlPath, credsYaml)
    return credsYaml

def create_credentials(envDir, envInstancesDir, instancesDir, is_external_cred_env) :
    logger.info(f"Start to create credentials: envDir={envDir}, envInstancesDir={envInstancesDir}, instancesDir={instancesDir}")
    logger.info(f"Creating credentials for environment directory: {envDir}")
    credsSchema="schemas/credential.schema.json"
    resultingCreds = []
    #tenant
    tenantFileName = envDir+"/tenant.yml"
    external_cred_ids = set()
    logger.info(f"Processing tenant")
    tenantYaml = openYaml(tenantFileName)
    tenantName = tenantYaml["name"]
    mergeResult = mergeCreds(getTenantCreds(tenantYaml, tenantName, is_external_cred_env, external_cred_ids), resultingCreds)
    logger.info(f'{mergeResult["countAdded"]} creds added from tenant {tenantFileName}')
    resultingCreds = mergeResult["mergedCreds"]
    #cloud
    cloudFileName = envDir+"/cloud.yml"
    logger.info(f"Processing cloud")
    cloudYaml = openYaml(cloudFileName)
    cloudName = cloudYaml["name"]
    mergeResult = mergeCreds(getCloudCreds(cloudYaml, tenantName, cloudName, is_external_cred_env, external_cred_ids), resultingCreds)
    logger.info(f'{mergeResult["countAdded"]} creds added from cloud {cloudFileName}')
    resultingCreds = mergeResult["mergedCreds"]
    #bgd object
    bgdFileName = envDir+"/bg_domain.yml"
    logger.info(f"Processing bg domain")
    if check_file_exists(bgdFileName):
        bgd_yaml = openYaml(bgdFileName)
        bgd_name = bgd_yaml["name"]
        mergeResult = mergeCreds(get_bg_domain_creds(bgd_yaml, bgd_name), resultingCreds)
        logger.info(f'{mergeResult["countAdded"]} creds added from bg domain {bgdFileName}')
        resultingCreds = mergeResult["mergedCreds"]
    else:
        logger.info("Bg domain doesn't exist")
    # iterate through cloud applications and create cred definitions
    applications = findAllYamlsInDir(f"{envDir}/Applications")
    for appPath in applications :
        mergeResult = mergeCreds(getApplicationCreds(appPath, tenantName, cloudName, external_cred_ids=external_cred_ids), resultingCreds)
        logger.info(f'{mergeResult["countAdded"]} creds added for cloud application {appPath}')
        resultingCreds = mergeResult["mergedCreds"]
    # iterate through namespaces and create cred definitions
    namespaceNameMap = {}
    namespaces = findYamls(envDir, "/Namespaces", additionalRegexpNotPattern=r".+/Namespaces/.+/Applications/.+")
    namespaces.sort()
    for namespacePath in namespaces :
        namespaceYaml = openYaml(namespacePath)
        namespaceKey = extract_namespace_from_namespace_path(namespacePath)
        namespaceName = namespaceYaml["name"]
        namespaceNameMap[namespaceKey] = namespaceName
        mergeResult = mergeCreds(getNamespaceCreds(namespaceYaml, tenantName, cloudName, namespaceName, is_external_cred_env, external_cred_ids), resultingCreds)
        logger.info(f'{mergeResult["countAdded"]} creds added for namespace {namespacePath}')
        resultingCreds = mergeResult["mergedCreds"]
    # iterate through namespace applications and create cred definitions
    applications = findYamls(envDir, "/Applications", additionalRegexpPattern=r".+/Namespaces/.+/Applications/.+")
    applications.sort()
    for appPath in applications :
        namespaceKey = extract_namespace_from_application_path(appPath)
        namespaceName = namespaceNameMap[namespaceKey]
        mergeResult = mergeCreds(getApplicationCreds(appPath, tenantName, cloudName, namespaceName, external_cred_ids), resultingCreds)
        logger.info(f'{mergeResult["countAdded"]} creds added for namespace application {appPath}')
        resultingCreds = mergeResult["mergedCreds"]

    #store credentials
    credYamlPath = envDir + "/Credentials/credentials.yml"
    mergeAndSaveYaml(credYamlPath, resultingCreds)
    # process shared credentials
    env_creds_map = mergeSharedCreds(credYamlPath, envInstancesDir, instancesDir)
    #validate external credentials
    if is_external_cred_env:
        if resultingCreds:
            #to cover condition like local creds macro with external cred id
            local_cred_ids = [
                item.get('cred', {}).get('credentialsId')
                for item in resultingCreds
                if item.get('cred', {}).get('credentialsId')
            ]
            raise ReferenceError(f"Found local credential macros in external cred only environment. Credential IDs are  {local_cred_ids}")
        logger.info(f"Validating external credentials for external only environment")
        validate_external_creds(env_creds_map, external_cred_ids)
    else:
        if external_cred_ids:
            raise ReferenceError(f"Found external credential references in parameters in local cred only environment. Credential IDs are {external_cred_ids}")
    validate_cred_types(env_creds_map, is_external_cred_env, credYamlPath)
    beautifyYaml(credYamlPath, credsSchema)