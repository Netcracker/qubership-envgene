from pathlib import Path
import os
from envgenehelper import *
from typing import Optional, List

#const
CRED_TYPE_SECRET="secret"
CRED_TYPE_USERPASS="usernamePassword"
CRED_TYPE_VAULT="vaultAppRole"
CRED_TYPE_EXTERNAL="external"
EXTERNAL_CRED_COMMENT="external credential"

def createCredDefinition(credId, credType) :
    cred = {}
    cred["credentialsId"] = credId.strip("\"")
    cred["type"] = credType
    return cred

def createExternalCredDefinition(credId, credData):
    cred = {}
    cred["credentialsId"] = credId.strip("\"")
    for key, value in credData.items():
        cred[key] = value
    return cred

def processParametersAndAppend(paramTypeKey, paramsDict, credsList, tenantName, cloudName="", namespaceName="", comment="", extCredsMap=None, extCredsErrors=None) :
    if paramTypeKey not in paramsDict.keys():
        return
    processDictAndAppend(paramsDict[paramTypeKey], credsList, tenantName, cloudName, namespaceName, comment, extCredsMap, extCredsErrors)

def processDictAndAppend(params, credsList, tenantName, cloudName, namespaceName, comment,  extCredsMap=None, extCredsErrors=None):
    for key, value in params.items():
        processSingleParam(key, value, credsList, tenantName, cloudName, namespaceName, comment, extCredsMap, extCredsErrors)

def processSingleParam(key, value, credsList, tenantName, cloudName, namespaceName, comment, extCredsMap=None, extCredsErrors: Optional[List[str]] = None):
    if isinstance(value, dict):
        if value.get("$type") == "credRef":
            cred_id = value.get("credId")
            if extCredsMap is not None and cred_id not in extCredsMap:
                    if extCredsErrors is not None:
                        extCredsErrors.append(f"{cred_id}")
                    return 
        processDictAndAppend(value, credsList, tenantName, cloudName, namespaceName, comment, extCredsMap, extCredsErrors)
    elif isinstance(value, list): # if is array, than iterate
        for idx, item in enumerate(value):
            value[idx] = processSingleParam(idx, item, credsList, tenantName, cloudName, namespaceName, comment, extCredsMap, extCredsErrors)
    elif isinstance(value, str):
        if check_is_cred(key, value):
            appendCredList(get_cred_list_from_param(key, value, True, tenantName, cloudName, namespaceName), credsList, comment)

def checkCredAndAppend(credName, credsList, secretType, comment="", externalCredData=None):
    if (credName):
        if secretType == CRED_TYPE_EXTERNAL:
            appendCredList([createExternalCredDefinition(credName, externalCredData)], credsList, comment)
        else:
            appendCredList([createCredDefinition(credName, secretType)], credsList, comment)
    return credsList

def appendCredList(additionalCreds, wholeCredsList, comment=""):
    for cred in additionalCreds:
        credMeta = {}
        credMeta["cred"] = cred
        credMeta["comment"] = comment
        wholeCredsList.append(credMeta)

def getTenantCreds(tenantContent, tenantName, extCredsMap=None, extCredsErrors=None):
    creds = []
    tenantComment = f"tenant {tenantName}"
    checkCredAndAppend(tenantContent["credential"], creds, CRED_TYPE_SECRET, tenantComment)
    #process deployParameters
    processParametersAndAppend("deployParameters", tenantContent, creds, tenantName, comment=tenantComment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
    processParametersAndAppend("environmentParameters", tenantContent["globalE2EParameters"], creds, tenantName, comment=tenantComment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
    return creds

def getExternalCreds(extCredsMap):
    creds = []
    logger.info(f"extCredsMap is {extCredsMap}")
    for credName, credData in extCredsMap.items():
        checkCredAndAppend(credName, creds, CRED_TYPE_EXTERNAL, EXTERNAL_CRED_COMMENT, credData)
    return creds

def getCloudCreds(cloudContent, tenantName, cloudName, extCredsMap=None, extCredsErrors=None):
    creds = []
    cloudComment = f"cloud {cloudName}"
    checkCredAndAppend(cloudContent["defaultCredentialsId"], creds, CRED_TYPE_SECRET, cloudComment)
    checkCredAndAppend(cloudContent["maasConfig"]["credentialsId"], creds, CRED_TYPE_USERPASS, cloudComment)
    checkCredAndAppend(cloudContent["vaultConfig"]["credentialsId"], creds, CRED_TYPE_SECRET, cloudComment)
    checkCredAndAppend(cloudContent["consulConfig"]["tokenSecret"], creds, CRED_TYPE_SECRET, cloudComment)
    for i in cloudContent["dbaasConfigs"]:
        checkCredAndAppend(i["credentialsId"], creds, CRED_TYPE_USERPASS, cloudComment)

    #process deployParameters
    processParametersAndAppend("deployParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
    #process e2eParameters
    processParametersAndAppend("e2eParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)

    return creds

def get_bg_domain_creds(content, name):
    creds = []
    bg_domain_comment = f"bg domain {name}"
    checkCredAndAppend(content["controllerNamespace"]["credentials"], creds, CRED_TYPE_SECRET, bg_domain_comment)
    return creds

def getNamespaceCreds(namespaceContent, tenantName, cloudName, namespaceName, extCredsMap, extCredsErrors):
    creds = []
    namespaceComment = f"namespace {namespaceName}"
    checkCredAndAppend(namespaceContent["credentialsId"], creds, CRED_TYPE_SECRET, namespaceComment)
    #process deployParameters
    processParametersAndAppend("deployParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
    #process e2eParameters
    processParametersAndAppend("e2eParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
    return creds

def getApplicationCreds(appPath, tenantName, cloudName, namespaceName="", extCredsMap=None, extCredsErrors=None):
    creds = []
    appContent = openYaml(appPath)
    appName = appContent["name"]
    if namespaceName :
        comment = f"namespace {namespaceName} application {appName}"
    else:
        comment = f"cloud {cloudName} application {appName}"
    #process deployParameters
    processParametersAndAppend("deployParameters", appContent, creds, tenantName, cloudName, namespaceName, comment=comment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", appContent, creds, tenantName, cloudName, namespaceName, comment=comment, extCredsMap=extCredsMap, extCredsErrors=extCredsErrors)
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
    elif (cred["type"] == CRED_TYPE_EXTERNAL):
        for key, value in cred.items():
            if key not in ["credentialsId", "type"]:
                newCred.insert(len(newCred), key, value)
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
    env_level = Path(env_dir) / "Inventory" / "credentials"
    cluster_level = Path(env_dir).parent / "credentials"
    site_level = Path(instances_dir) / "credentials"
    
    shared_cred_paths = [env_level, cluster_level, site_level]
    
    logger.debug(f"Searching for '{cred_name}' in paths: {shared_cred_paths}")
    for p in shared_cred_paths:
        found_path = find_yaml_file(p, cred_name)
        if found_path:
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

def create_credentials(envDir, envInstancesDir, instancesDir) :
    logger.info(f"Start to create credentials: envDir={envDir}, envInstancesDir={envInstancesDir}, instancesDir={instancesDir}")
    logger.info(f"Creating credentials for environment directory: {envDir}")
    credsSchema="schemas/credential.schema.json"
    resultingCreds = []
    #tenant
    tenantFileName = envDir+"/tenant.yml"
    externalCredsFile = envDir+"/Credentials/rendered-external-creds.yml"
    extCredsMap = openYaml(externalCredsFile, allow_default=True)
    logger.info(f"Rendered external creds if any: {extCredsMap}")
    extCredsErrors = []
    logger.info(f"Processing tenant")
    tenantYaml = openYaml(tenantFileName)
    tenantName = tenantYaml["name"]
    mergeResult = mergeCreds(getTenantCreds(tenantYaml, tenantName, extCredsMap, extCredsErrors), resultingCreds)
    logger.info(f'{mergeResult["countAdded"]} creds added from tenant {tenantFileName}')
    resultingCreds = mergeResult["mergedCreds"]
    #cloud
    cloudFileName = envDir+"/cloud.yml"
    logger.info(f"Processing cloud")
    cloudYaml = openYaml(cloudFileName)
    cloudName = cloudYaml["name"]
    mergeResult = mergeCreds(getCloudCreds(cloudYaml, tenantName, cloudName, extCredsMap, extCredsErrors), resultingCreds)
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
        mergeResult = mergeCreds(getApplicationCreds(appPath, tenantName, cloudName, extCredsMap, extCredsErrors), resultingCreds)
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
        mergeResult = mergeCreds(getNamespaceCreds(namespaceYaml, tenantName, cloudName, namespaceName, extCredsMap, extCredsErrors), resultingCreds)
        logger.info(f'{mergeResult["countAdded"]} creds added for namespace {namespacePath}')
        resultingCreds = mergeResult["mergedCreds"]
    # iterate through namespace applications and create cred definitions
    applications = findYamls(envDir, "/Applications", additionalRegexpPattern=r".+/Namespaces/.+/Applications/.+")
    applications.sort()
    for appPath in applications :
        namespaceKey = extract_namespace_from_application_path(appPath)
        namespaceName = namespaceNameMap[namespaceKey]
        mergeResult = mergeCreds(getApplicationCreds(appPath, tenantName, cloudName, namespaceName, extCredsMap, extCredsErrors), resultingCreds)
        logger.info(f'{mergeResult["countAdded"]} creds added for namespace application {appPath}')
        resultingCreds = mergeResult["mergedCreds"]
    #raise external cred error before saving credentails to file
    if extCredsErrors:
        raise ValueError(
        f"Following external credentials "
        f"{', '.join(map(str, extCredsErrors))} "
        f"referred in parameters are not found in external credential template"
        )
    #iterate through rendered External Credentials and create cred definition
    logger.info(f"Processing external credentials")
    mergeResult = mergeCreds(getExternalCreds(extCredsMap), resultingCreds)
    logger.info(f'{mergeResult["countAdded"]} creds added for external credentials {externalCredsFile}')
    resultingCreds = mergeResult["mergedCreds"]
    #store credentials
    credYamlPath = envDir + "/Credentials/credentials.yml"
    mergeAndSaveYaml(credYamlPath, resultingCreds)
    # process shared credentials
    mergeSharedCreds(credYamlPath, envInstancesDir, instancesDir)
    beautifyYaml(credYamlPath, credsSchema)
    logger.debug(f"Removing rendered external credential file")
    deleteFileIfExists(externalCredsFile)

