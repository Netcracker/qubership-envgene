import copy
import pathlib
import os
from envgenehelper import *
from resource_profiles import processResourceProfiles
from schema_validation import checkEnvSpecificParametersBySchema
from cloud_passport import process_cloud_passport

# const
GENERATED_HEADER = "The contents of this file is generated from template artifact: %s.\nContents will be overwritten by next generation.\nPlease modify this contents only for development purposes or as workaround."

def findNamespaces(dir) :
    result = []
    fileList = findAllYamlsInDir(dir)
    for filePath in fileList:
        if "/Namespaces/" in filePath:
            result.append(filePath)
    logger.info(f'List of {dir} namespaces: \n {dump_as_yaml_format(result)}')
    return result

def processFileList(mask, dict, dirPointer):
    fileList = list(dirPointer.rglob(mask))
    for f in fileList:
        filePath = str(f)
        # envSpecific = false will be update later during templates parsing
        key = extractNameFromFile(filePath)
        if key in dict:
            dict[extractNameFromFile(filePath)].append({"filePath": filePath, "envSpecific": False})
        else:
            dict[extractNameFromFile(filePath)] = [{"filePath": filePath, "envSpecific": False}]
    return dict

def createParamsetsMap(dir):
    result = {}
    dirPointer = pathlib.Path(dir)
    masks = ["*.json", "*.yml", "*.yaml", "*.j2"]
    for mask in masks:
        result = processFileList(mask, result, dirPointer)
    logger.debug(f'List of {dir} paramsets: \n %s', dump_as_yaml_format(result))
    return result

def sortParameters(params) :
    result = copy.deepcopy(params)
    result.clear()
    for k in sorted(params.keys()):
            result[k] = params[k]
    return result

def openParamset(path, template_context=None) :
    if path.endswith(".json"):
        return openJson(path)
    # using safe load to load without comments
    if path.endswith(".j2"):
        # First render the template
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader(os.path.dirname(path)))
        template = env.get_template(os.path.basename(path))
        rendered = template.render(**(template_context or {}))
        return yaml.safe_load(rendered)
    paramsetYaml = openYaml(path, safe_load=True)
    return paramsetYaml

def findParamsetsInDir(dirPath) :
    fileList = findAllYamlsInDir(dirPath)
    fileListJson = findAllJsonsInDir(dirPath)
    if len(fileListJson) > 0 :
        return fileList + fileListJson
    return fileList

def findEnvDefinitionFromTemplatePath(templatePath, env_instances_dir=None):
    # Walk up the directory tree until we find the Inventory/env_definition.yml file
    current_dir = os.path.dirname(templatePath)
    while current_dir and os.path.split(current_dir)[1]:
        env_def_path = os.path.join(current_dir, "Inventory", "env_definition.yml")
        if os.path.exists(env_def_path):
            return openYaml(env_def_path)
        # If we're in the output directory, try to find the corresponding path in the source directory
        if env_instances_dir and "/tmp/" in current_dir:
            # Extract the relative path from the tmp directory
            tmp_index = current_dir.find("/tmp/")
            if tmp_index >= 0:
                relative_path = current_dir[tmp_index + 5:]  # Skip "/tmp/"
                source_path = os.path.join(env_instances_dir, relative_path, "Inventory", "env_definition.yml")
                if os.path.exists(source_path):
                    return openYaml(source_path)
        current_dir = os.path.dirname(current_dir)
    raise ReferenceError(f"Environment definition not found for template {templatePath}")

def convertParameterSetsToParameters(templatePath, paramsTemplate, paramsetsTag, parametersTag, paramset_map, env_specific_params_map, header_text="", env_instances_dir=None):
    params = copy.deepcopy(paramsTemplate[parametersTag])
    for pset in paramsTemplate[paramsetsTag]:
        paramSetDefinition = paramset_map[pset]
        for entry in paramSetDefinition:
            paramSetFile = entry["filePath"]
            logger.info(f"Processing paramset {pset} in file {paramSetFile}")
            isEnvSpecificParamset = entry["envSpecific"]
            # Get template context from environment definition
            try:
                env_definition = findEnvDefinitionFromTemplatePath(templatePath, env_instances_dir)
                current_env = {
                    "name": env_definition["inventory"]["environmentName"],
                    "solution_structure": env_definition.get("solutionStructure", {})
                }
                template_context = {
                    "env_definition": env_definition,
                    "current_env": current_env
                }
                paramSetValues = openParamset(paramSetFile, template_context)
            except Exception as e:
                logger.warning(f"Failed to render template for paramset {pset}: {str(e)}")
                # Fall back to direct YAML loading if template rendering fails
                paramSetValues = openParamset(paramSetFile)
            #
            paramSetName = paramSetValues["name"]
            paramSetVersion = paramSetValues["version"] if "version" in paramSetValues else "n/a"
            if "parameters" in paramSetValues :
                paramSetParameters = paramSetValues["parameters"]
            else :
                paramSetParameters = {}
            if "applications" in paramSetValues :
                paramSetAppParams = list(paramSetValues["applications"])
            else :
                paramSetAppParams = []
            paramsetDefinitionComment = "paramset: " + paramSetName + " version: " + str(paramSetVersion) + " source: " + ("template" if "from_template" in paramSetFile else "instance")
            # process parameters in ParamSet
            for k in paramSetParameters:
                # get value with potential merge of dicts
                val = get_merged_param_value(k, params, paramSetParameters)
                store_value_to_yaml(params, k, val, paramsetDefinitionComment)
                # fill env specific parameters map for env specific paramset
                if isEnvSpecificParamset:
                    storeToEnvSpecificParametersMap(env_specific_params_map, "", parametersTag, k, val, pset)
            # prepare application parameters
            convertParameterSetsToApplication(templatePath, paramsetDefinitionComment, paramSetAppParams, pset, parametersTag, isEnvSpecificParamset, env_specific_params_map, header_text)
    params = sortParameters(params)
    return params

def convertParameterSetsToApplication(templatePath, paramsetDefinitionComment, applicationsParamSets, paramsetName, parametersTag, isEnvSpecificParamset, env_specific_params_map, header_text=""):
    application_schema="schemas/application.schema.json"
    for appParams in applicationsParamSets:
            appName = appParams["appName"] if "appName" in appParams else appParams["name"]
            applicationParametersFile = os.path.dirname(templatePath) + "/Applications/" + appName + ".yml"
            appDefinition = getApplicationParametersYaml(appName, applicationParametersFile)
            for j in appParams["parameters"]:
                # get value with potential merge of dicts
                val = get_merged_param_value(j, appDefinition[parametersTag], appParams["parameters"])
                store_value_to_yaml(appDefinition[parametersTag], j, val, paramsetDefinitionComment)
                if isEnvSpecificParamset:
                    storeToEnvSpecificParametersMap(env_specific_params_map, appName, parametersTag, j, val, paramsetName)
            writeYamlToFile(applicationParametersFile, appDefinition)
            beautifyYaml(applicationParametersFile, application_schema, header_text, wrap_all_strings=False)
    return

def initParametersStructure(map, key, is_app=False) :
    if key not in map:
        map[key] = {}
    map[key]["deployParameters"] = {}
    map[key]["e2eParameters"] = {}
    map[key]["technicalConfigurationParameters"] = {}
    if not is_app:
        map[key]["applications"] = {}

def storeToEnvSpecificParametersMap(env_specific_params_map, applicationName, parametersTag, paramKey, paramValue, paramsetName) :
    if applicationName:
        #todo: прибить гвоздями все 3 тэга параметров
        if applicationName not in env_specific_params_map["applications"]:
            initParametersStructure(env_specific_params_map["applications"], applicationName, is_app=True)
        env_specific_params_map["applications"][applicationName][parametersTag][paramKey] = { "value" : paramValue, "paramsetName" : paramsetName }
    else:
        env_specific_params_map[parametersTag][paramKey] = { "value" : paramValue, "paramsetName" : paramsetName }

def getApplicationParametersYaml(appName, applicationParametersFile):
    result = yaml.load("name: \""+appName+"\"\ndeployParameters: {}\ntechnicalConfigurationParameters: {}\n")
    os.makedirs(os.path.dirname(applicationParametersFile), exist_ok=True)
    if os.path.exists(applicationParametersFile):
        result = openYaml(applicationParametersFile)
    return result

def updateEnvSpecificParamsets(env_instances_dir, templateName, templateContent, paramset_map) :
    envDefinitionYaml = getEnvDefinition(env_instances_dir)
    result = {}
    if "envSpecificParamsets" in envDefinitionYaml["envTemplate"]:
        if templateName in envDefinitionYaml["envTemplate"]["envSpecificParamsets"]:
            envSpecificParamsets = envDefinitionYaml["envTemplate"]["envSpecificParamsets"][templateName]
            logger.info(f"Attaching env-specific deployment paramsets: {dump_as_yaml_format(envSpecificParamsets)} to template {templateName}")
            templateContent["deployParameterSets"] = templateContent["deployParameterSets"] + envSpecificParamsets
            for pset in envSpecificParamsets:
                for value in paramset_map[pset]:
                    value["envSpecific"] = True
    if "envSpecificE2EParamsets" in envDefinitionYaml["envTemplate"]:
        if templateName in envDefinitionYaml["envTemplate"]["envSpecificE2EParamsets"]:
            envSpecificParamsets = envDefinitionYaml["envTemplate"]["envSpecificE2EParamsets"][templateName]
            logger.info(f"Attaching env-specific E2E paramsets: {dump_as_yaml_format(envSpecificParamsets)} to template {templateName}")
            templateContent["e2eParameterSets"] = templateContent["e2eParameterSets"] + envSpecificParamsets
            for pset in envSpecificParamsets:
                for value in paramset_map[pset]:
                    value["envSpecific"] = True
    if "envSpecificTechnicalParamsets" in envDefinitionYaml["envTemplate"]:
        if templateName in envDefinitionYaml["envTemplate"]["envSpecificTechnicalParamsets"]:
            envSpecificParamsets = envDefinitionYaml["envTemplate"]["envSpecificTechnicalParamsets"][templateName]
            logger.info(f"Attaching env-specific technical paramsets: {dump_as_yaml_format(envSpecificParamsets)} to template {templateName}")
            templateContent["technicalConfigurationParameterSets"] = templateContent["technicalConfigurationParameterSets"] + envSpecificParamsets
            for pset in envSpecificParamsets:
                for value in paramset_map[pset]:
                    value["envSpecific"] = True
    return result
    
def processTemplate(templatePath, templateName, env_instances_dir, schema_path, paramset_map, env_specific_params_map, resource_profiles_map=None, header_text="", process_env_specific=True):
    logger.info(f"Processing template: {templateName} in {templatePath}")
    templateContent = openYaml(templatePath)
    if process_env_specific:
        updateEnvSpecificParamsets(env_instances_dir, templateName, templateContent, paramset_map)
    #process deployParameters
    templateContent["deployParameters"] = convertParameterSetsToParameters(templatePath, templateContent, "deployParameterSets", "deployParameters", paramset_map, env_specific_params_map, header_text, env_instances_dir)
    templateContent["deployParameterSets"] = []
    #process e2eParameters
    templateContent["e2eParameters"] = convertParameterSetsToParameters(templatePath, templateContent, "e2eParameterSets", "e2eParameters", paramset_map, env_specific_params_map, header_text, env_instances_dir)
    templateContent["e2eParameterSets"] = []
    #process technicalConfigurationParameters
    templateContent["technicalConfigurationParameters"] = convertParameterSetsToParameters(templatePath, templateContent, "technicalConfigurationParameterSets", "technicalConfigurationParameters", paramset_map, env_specific_params_map, header_text, env_instances_dir)
    templateContent["technicalConfigurationParameterSets"] = []
    # preparing map for needed resource profiles
    if "profile" in templateContent and templateContent["profile"] and "name" in templateContent["profile"] and templateContent["profile"]["name"] :
        rpName = templateContent["profile"]["name"]
        resource_profiles_map[templateName] = rpName
    writeYamlToFile(templatePath, templateContent)
    beautifyYaml(templatePath, schema_path, header_text)
    return

def process_additional_template_parameters(render_env_dir, source_env_dir, all_instances_dir):
    # getting additional template variables files from env_definition
    inventoryYaml = getEnvDefinition(render_env_dir)
    envDefinitionPath = getEnvDefinitionPath(render_env_dir)
    if "sharedTemplateVariables" in inventoryYaml["envTemplate"] and len(inventoryYaml["envTemplate"]["sharedTemplateVariables"]) > 0 :
        result = {}
        for sharedVarFileName in inventoryYaml["envTemplate"]["sharedTemplateVariables"]:
            sharedVarYamls = findResourcesBottomTop(source_env_dir, all_instances_dir, f"/{sharedVarFileName}")
            if len(sharedVarYamls) == 1:
                yamlPath = sharedVarYamls[0]
                addedVars = openYaml(yamlPath)
                result.update(addedVars)
                logger.info(f"Shared template variables added from: {yamlPath}: \n{dump_as_yaml_format(addedVars)}")
            elif len(sharedVarYamls) > 1: 
                logger.error(f"Duplicate shared template variables with key {sharedVarFileName} found in {all_instances_dir}: \n\t" + ",\n\t".join(str(x) for x in sharedVarYamls))
                raise ReferenceError(f"Duplicate shared template variables with key {sharedVarFileName} found. See logs above.")
            else:
                raise ReferenceError(f"Shared template variables with key {sharedVarFileName} not found in {all_instances_dir}")

        # updating additional template variables from map
        if "additionalTemplateVariables" not in inventoryYaml["envTemplate"] :
            inventoryYaml["envTemplate"]["additionalTemplateVariables"] = {}
        else:
            inventoryVars = inventoryYaml["envTemplate"]["additionalTemplateVariables"]
            logger.debug(f"Additional template variables from inventory: \n{dump_as_yaml_format(inventoryVars)}")
            result.update(inventoryVars)

        # storing to yaml    
        logger.info(f"Resulting additional template variables are: \n{dump_as_yaml_format(result)}")
        inventoryYaml["envTemplate"]["additionalTemplateVariables"] = result;
        writeYamlToFile(envDefinitionPath, inventoryYaml)
    else:
        logger.info(f"No shared templates variables are defined in: {envDefinitionPath}")

def getTemplateNameFromNamespacePath(namespacePath) : 
    path = pathlib.Path(namespacePath)
    return path.parent.name

def build_env(env_name, env_instances_dir, parameters_dir, env_template_dir, resource_profiles_dir, env_specific_resource_profile_map, all_instances_dir) :
    paramset_map = createParamsetsMap(parameters_dir)
    env_dir = env_template_dir+"/"+env_name
    logger.info(f"Env name: {env_name}")
    logger.info(f"Env dir: {env_dir}")
    logger.info(f"Parameters dir: {parameters_dir}")
    #const
    tenant_schema="schemas/tenant.schema.json"
    cloud_schema="schemas/cloud.schema.json"
    namespace_schema="schemas/namespace.schema.json"
    profiles_schema="schemas/resource-profile.schema.json"
    

    #removingAnsibleTrash
    yamlFiles = findAllYamlsInDir(env_dir)
    for f in yamlFiles :
        logger.debug(f"Removing ansible trash from: {f}")
        removeAnsibleTrashFromFile(f)
    envDefinitionYaml = getEnvDefinition(env_dir)
    logger.info(getEnvDefinitionPath(env_dir))
    templateArtifactName = getTemplateArtifactName(envDefinitionYaml)
    generated_header_text = GENERATED_HEADER % templateArtifactName

    # pathes
    tenantTemplatePath = env_dir + "/tenant.yml"
    cloudTemlatePath = env_dir + "/cloud.yml"
    namespaceTemplates = findNamespaces(env_dir)
    # env specific parameters map - will be filled with env specific parameters during template processing
    env_specific_parameters_map = {}
    env_specific_parameters_map["namespaces"] = {}
    
    #process tenant
    logger.info(f"Processing tenant: {tenantTemplatePath}")
    beautifyYaml(tenantTemplatePath, tenant_schema, generated_header_text)

    # process cloud
    needed_resource_profiles_map = {}
    logger.info(f"Processing cloud: {cloudTemlatePath}")
    initParametersStructure(env_specific_parameters_map, "cloud")
    logger.info("Processing cloud without env specific parameters.")
    processTemplate(
        cloudTemlatePath, 
        "cloud", 
        env_instances_dir, 
        cloud_schema, 
        paramset_map, 
        env_specific_parameters_map["cloud"], 
        resource_profiles_map=needed_resource_profiles_map, 
        header_text=generated_header_text,
        process_env_specific=False)
    # process cloud passport
    process_cloud_passport(env_dir, env_instances_dir, all_instances_dir)
    logger.info("Processing cloud with env specific parameters.")
    processTemplate(
        cloudTemlatePath, 
        "cloud", 
        env_instances_dir, 
        cloud_schema, 
        paramset_map, 
        env_specific_parameters_map["cloud"], 
        resource_profiles_map=needed_resource_profiles_map, 
        header_text=generated_header_text,
        process_env_specific=True)

    # process namespaces
    template_namespace_names = []
    # iterate through namespace definitions and create namespace parameters
    for templatePath in namespaceTemplates :
        logger.info(f"Processing namespace: {templatePath}")
        templateName = getTemplateNameFromNamespacePath(templatePath)
        template_namespace_names.append(templateName)
        initParametersStructure(env_specific_parameters_map["namespaces"], templateName)
        processTemplate(
            templatePath, 
            templateName, 
            env_instances_dir, 
            namespace_schema, 
            paramset_map, 
            env_specific_parameters_map["namespaces"][templateName],
            resource_profiles_map=needed_resource_profiles_map, 
            header_text=generated_header_text)

    logger.info(f"EnvSpecific parameters are: \n{dump_as_yaml_format(env_specific_parameters_map)}")
    checkEnvSpecificParametersBySchema(env_dir, env_specific_parameters_map, template_namespace_names)

    # process resource profiles
    processResourceProfiles(env_dir, resource_profiles_dir, profiles_schema, needed_resource_profiles_map, env_specific_resource_profile_map, header_text=generated_header_text)
    
