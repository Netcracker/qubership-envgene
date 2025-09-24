import re
import sys
import os
from envgenehelper import *

#const
CRED_TYPE_SECRET="secret"
CRED_TYPE_USERPASS="usernamePassword"
CRED_TYPE_VAULT="vaultAppRole"

def createCredDefinition(credId, credType) :
    cred = {}
    cred["credentialsId"] = credId.strip("\"")
    cred["type"] = credType
    return cred

def processParametersAndAppend(paramTypeKey, paramsDict, credsList, tenantName, cloudName="", namespaceName="", comment="") :
    if paramTypeKey not in paramsDict.keys():
        return
    processDictAndAppend(paramsDict[paramTypeKey], credsList, tenantName, cloudName, namespaceName, comment)

def processDictAndAppend(params, credsList, tenantName, cloudName, namespaceName, comment):
    for key, value in params.items():
        processSingleParam(key, value, credsList, tenantName, cloudName, namespaceName, comment)

def processSingleParam(key, value, credsList, tenantName, cloudName, namespaceName, comment):
    if isinstance(value, dict):
        processDictAndAppend(value, credsList, tenantName, cloudName, namespaceName, comment)
    elif isinstance(value, list): # if is array, than iterate
        for idx, item in enumerate(value):
            value[idx] = processSingleParam(idx, item, credsList, tenantName, cloudName, namespaceName, comment)
    elif isinstance(value, str):
        if check_is_cred(key, value):
            appendCredList(get_cred_list_from_param(key, value, True, tenantName, cloudName, namespaceName), credsList, comment)

def checkCredAndAppend(credName, credsList, secretType, comment=""):
    if (credName):
        appendCredList([createCredDefinition(credName, secretType)], credsList, comment)
    return credsList

def appendCredList(additionalCreds, wholeCredsList, comment=""):
    for cred in additionalCreds:
        credMeta = {}
        credMeta["cred"] = cred
        credMeta["comment"] = comment
        wholeCredsList.append(credMeta)

def getTenantCreds(tenantContent, tenantName):
    creds = []
    tenantComment = f"tenant {tenantName}"
    checkCredAndAppend(tenantContent["credential"], creds, CRED_TYPE_SECRET, tenantComment)
    #process deployParameters
    processParametersAndAppend("deployParameters", tenantContent, creds, tenantName, comment=tenantComment)
    processParametersAndAppend("environmentParameters", tenantContent["globalE2EParameters"], creds, tenantName, comment=tenantComment)
    return creds

def getCloudCreds(cloudContent, tenantName, cloudName):
    creds = []
    cloudComment = f"cloud {cloudName}"
    checkCredAndAppend(cloudContent["defaultCredentialsId"], creds, CRED_TYPE_SECRET, cloudComment)
    checkCredAndAppend(cloudContent["maasConfig"]["credentialsId"], creds, CRED_TYPE_USERPASS, cloudComment)
    checkCredAndAppend(cloudContent["vaultConfig"]["credentialsId"], creds, CRED_TYPE_SECRET, cloudComment)
    checkCredAndAppend(cloudContent["consulConfig"]["tokenSecret"], creds, CRED_TYPE_SECRET, cloudComment)
    for i in cloudContent["dbaasConfigs"]:
        checkCredAndAppend(i["credentialsId"], creds, CRED_TYPE_USERPASS, cloudComment)

    #process deployParameters
    processParametersAndAppend("deployParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment)
    #process e2eParameters
    processParametersAndAppend("e2eParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", cloudContent, creds, tenantName, cloudName, comment=cloudComment)

    return creds

def get_bg_domain_creds(content, name):
    creds = []
    bg_domain_comment = f"bg domain {name}"
    checkCredAndAppend(content["controllerNamespace"]["credentialId"], creds, CRED_TYPE_SECRET, bg_domain_comment)
    return creds

def getNamespaceCreds(namespaceContent, tenantName, cloudName, namespaceName):
    creds = []
    namespaceComment = f"namespace {namespaceName}"
    checkCredAndAppend(namespaceContent["credentialsId"], creds, CRED_TYPE_SECRET, namespaceComment)
    #process deployParameters
    processParametersAndAppend("deployParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment)
    #process e2eParameters
    processParametersAndAppend("e2eParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment)
    #process technicalConfigurationParameters
    processParametersAndAppend("technicalConfigurationParameters", namespaceContent, creds, tenantName, cloudName, namespaceName, comment=namespaceComment)
    return creds

def getApplicationCreds(appPath, tenantName, cloudName, namespaceName=""):
    creds = []
    appContent = openYaml(appPath)
    appName = appContent["name"]
    if namespaceName :
        comment = f"namespace {namespaceName} application {appName}"
    else:
        comment = f"cloud {cloudName} application {appName}"
    #process deployParameters
    processParametersAndAppend("deployParameters", appContent, creds, tenantName, cloudName, namespaceName, comment=comment)
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

def findSharedCredentials(cred_name, env_dir, instances_dir):
    logger.debug(f"Searching for cred file {cred_name} from {env_dir} to {instances_dir}")
    credFiles = findResourcesBottomTop(env_dir, instances_dir, f"/{cred_name}")
    if len(credFiles) == 1:
        yamlPath = credFiles[0]
        logger.info(f"Shared credentials for {cred_name} found in: {yamlPath}")
        return yamlPath
    elif len(credFiles) > 1:
        logger.error(f"Duplicate shared credentials with key {cred_name} found in {instances_dir}: \n\t" + ",\n\t".join(str(x) for x in credFiles))
        raise ReferenceError(f"Duplicate shared credentials with key {cred_name} found. See logs above.")
    else:
        raise ReferenceError(f"Shared credentials with key {cred_name} not found in {instances_dir}")

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
    logger.info(f"Processing tenant")
    tenantYaml = openYaml(tenantFileName)
    tenantName = tenantYaml["name"]
    mergeResult = mergeCreds(getTenantCreds(tenantYaml, tenantName), resultingCreds)
    logger.info(f'{mergeResult["countAdded"]} creds added from tenant {tenantFileName}')
    resultingCreds = mergeResult["mergedCreds"]
    #cloud
    cloudFileName = envDir+"/cloud.yml"
    logger.info(f"Processing cloud")
    cloudYaml = openYaml(cloudFileName)
    cloudName = cloudYaml["name"]
    mergeResult = mergeCreds(getCloudCreds(cloudYaml, tenantName, cloudName), resultingCreds)
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
        mergeResult = mergeCreds(getApplicationCreds(appPath, tenantName, cloudName), resultingCreds)
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
        mergeResult = mergeCreds(getNamespaceCreds(namespaceYaml, tenantName, cloudName, namespaceName), resultingCreds)
        logger.info(f'{mergeResult["countAdded"]} creds added for namespace {namespacePath}')
        resultingCreds = mergeResult["mergedCreds"]
    # iterate through namespace applications and create cred definitions
    applications = findYamls(envDir, "/Applications", additionalRegexpPattern=r".+/Namespaces/.+/Applications/.+")
    applications.sort()
    for appPath in applications :
        namespaceKey = extract_namespace_from_application_path(appPath)
        namespaceName = namespaceNameMap[namespaceKey]
        mergeResult = mergeCreds(getApplicationCreds(appPath, tenantName, cloudName, namespaceName), resultingCreds)
        logger.info(f'{mergeResult["countAdded"]} creds added for namespace application {appPath}')
        resultingCreds = mergeResult["mergedCreds"]
    # store credentials
    credYamlPath = envDir + "/Credentials/credentials.yml"
    mergeAndSaveYaml(credYamlPath, resultingCreds)
    # process shared credentials
    mergeSharedCreds(credYamlPath, envInstancesDir, instancesDir)
    beautifyYaml(credYamlPath, credsSchema)

