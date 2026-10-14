import json
from fnmatch import fnmatchcase

from envgenehelper import NamespaceFile, NamespaceRole, OperationType, Path, copy, current_env_instance_store, dump_as_yaml_format, extractNameFromFile, findAllJsonsInDir, findAllYamlsInDir, find_yaml_file, getDirName, getEnvDefinitionPath, getTemplateArtifactName, get_merged_param_value, get_schema_dir, getenv, is_from_template_dir, logger, openFileAsString, openYaml, readYaml, os, path, set_nested_yaml_attribute, split_multi_value_param, store_value_to_yaml, validate_yaml_by_scheme_or_fail, yaml

from cloud_passport.cloud_passport import process_cloud_passport
from build_env.resource_profiles import collect_resource_profiles, override_by_env_specific_profiles, has_valid_profile_name, \
    get_profile_baseline, set_object_profile_field
from utils.schema_validation import checkEnvSpecificParametersBySchema

# const
PARAMSET_PATTERNS = ("*.json", "*.yml", "*.yaml", "*.j2")
GENERATED_HEADER = "The contents of this file is generated from template artifact: %s.\nContents will be overwritten by next generation.\nPlease modify this contents only for development purposes or as workaround."


def find_namespaces(dir):
    result = []
    fileList = findAllYamlsInDir(dir)
    for filePath in fileList:
        path = Path(filePath)
        if "Namespaces" in path.parts:
            result.append(filePath)
    logger.info(f'List of {dir} namespaces: \n {dump_as_yaml_format(result)}')
    return result


def _get_excluded_dirs_for_role(role: NamespaceRole, origin_template_exists: bool, peer_template_exists: bool) -> list:
    common_dir = 'from_template'
    origin_dir = 'from_origin_template'
    peer_dir = 'from_peer_template'
    if role == NamespaceRole.ORIGIN and origin_template_exists:
        return [common_dir, peer_dir]
    elif role == NamespaceRole.PEER and peer_template_exists:
        return [common_dir, origin_dir]
    else:
        return [origin_dir, peer_dir]


def create_paramset_map(dir: str, role: NamespaceRole,
                        origin_template_exists: bool, peer_template_exists: bool) -> dict:
    excluded_dirs = _get_excluded_dirs_for_role(role, origin_template_exists, peer_template_exists)
    result = {}
    for paramset_path in paramset_paths(dir, PARAMSET_PATTERNS):
        file_path = str(paramset_path)
        if any(excluded_dir in file_path for excluded_dir in excluded_dirs):
            continue
        key = extractNameFromFile(file_path)
        entry = {"filePath": file_path, "envSpecific": False}
        if key in result:
            result[key].append(entry)
        else:
            result[key] = [entry]

    logger.info(f"Created {role.name}-specific paramset map: excluded dirs {excluded_dirs}, "
                f"origin_template_exists={origin_template_exists}, peer_template_exists={peer_template_exists}")
    logger.debug(f'List of {dir} paramsets: \n %s', dump_as_yaml_format(result))
    return result


def paramset_paths(render_parameters_dir, patterns) -> list[Path]:
    return [key for key in current_env_instance_store().under(render_parameters_dir)
            if any(fnmatchcase(key.name, pattern) for pattern in patterns)]


def load_paramsets(source_dir, target_dir) -> None:
    source_dir = Path(source_dir)
    if not source_dir.is_dir():
        return
    env_instance_store = current_env_instance_store()
    for file in sorted(source_dir.rglob("*")):
        if file.is_file() and any(fnmatchcase(file.name, pattern) for pattern in PARAMSET_PATTERNS):
            env_instance_store.put(Path(target_dir) / file.relative_to(source_dir), openFileAsString(file))


def load_template_paramsets(templates_dirs: dict, render_parameters_dir: str) -> None:
    for template_type, template_path in templates_dirs.items():
        if not template_path:
            continue
        param_dir_name = 'from_template' if template_type == NamespaceRole.COMMON else f'from_{template_type}_template'
        load_paramsets(f'{template_path}/parameters', f'{render_parameters_dir}/{param_dir_name}')


def load_instance_paramsets(env_dir: str, render_parameters_dir: str) -> None:
    cluster_path = getDirName(str(env_dir))
    instances_dir = getDirName(cluster_path)
    load_paramsets(f'{instances_dir}/parameters', render_parameters_dir)
    load_paramsets(f'{cluster_path}/parameters', render_parameters_dir)
    load_paramsets(f'{env_dir}/Inventory/parameters', f'{render_parameters_dir}/from_instance')


def remove_paramsets(render_parameters_dir) -> None:
    env_instance_store = current_env_instance_store()
    for key in env_instance_store.under(render_parameters_dir):
        env_instance_store.remove(key)


def sortParameters(params):
    result = copy.deepcopy(params)
    result.clear()
    for k in sorted(params.keys()):
        result[k] = params[k]
    return result


def paramset_content(path):
    env_instance_store = current_env_instance_store()
    content = env_instance_store.get(path)
    if not isinstance(content, str):
        return content
    parsed = json.loads(content) if str(path).endswith(".json") else readYaml(content, safe_load=True)
    return env_instance_store.put(path, parsed)


def openParamset(path, template_context=None):
    if path.endswith(".j2"):
        from jinja2 import Environment
        template = Environment().from_string(current_env_instance_store().get(path))
        rendered = template.render(**(template_context or {}))
        return yaml.safe_load(rendered)
    return paramset_content(path)


def findParamsetsInDir(dirPath):
    fileList = findAllYamlsInDir(dirPath)
    fileListJson = findAllJsonsInDir(dirPath)
    if len(fileListJson) > 0:
        return fileList + fileListJson
    return fileList


def sort_paramsets_with_same_name(entries: list[dict]) -> list[dict]:
    # Strict order processing paramsets template -> cluster -> instance
    # Lower sort keys are processed first, later values override earlier ones
    def sort_key(e):
        path = e["filePath"]
        if "from_instance" in path:
            return 2, path
        elif is_from_template_dir(path):
            return 0, path
        return 1, path

    return sorted(entries, key=sort_key)


def mergeParameterSetsIntoParameters(templatePath, paramsTemplate, paramsetsTag, parametersTag, paramset_map,
                                     env_specific_params_map, env_definition):
    params = copy.deepcopy(paramsTemplate[parametersTag])
    application_paramsets = []
    for pset in paramsTemplate[paramsetsTag]:
        # Check if paramset exists in paramset_map before accessing it
        if pset not in paramset_map:
            logger.warning(
                f"Paramset '{pset}' referenced in {paramsetsTag} for template '{templatePath}' was not found. It may have been skipped due to missing variables.")
            continue

        paramSetDefinition = sort_paramsets_with_same_name(paramset_map[pset])
        for entry in paramSetDefinition:
            paramSetFile = entry["filePath"]
            logger.info(f"Processing paramset {pset} in file {paramSetFile}")
            isEnvSpecificParamset = entry["envSpecific"]
            # Get template context from environment definition
            try:
                # Get environment name from inventory, with fallback to derived name from path
                env_name = env_definition["inventory"].get("environmentName")

                # Get cloud name and cluster information for macro support
                cloud_name = env_definition["inventory"].get("cloudName", "")
                cluster_name = env_definition.get("_derived_cluster_name", "")

                # Create cloudNameWithCluster for macro support
                cloud_name_with_cluster = f"{cloud_name}-{cluster_name}" if cloud_name and cluster_name else cloud_name

                # Create environment context with comprehensive macro support
                current_env = {
                    "name": env_name,
                    "environmentName": env_name,  # Alternative access
                    "cloud": cloud_name,
                    "cloudNameWithCluster": cloud_name_with_cluster,
                    "solution_structure": env_definition.get("solutionStructure", {}),
                    "additionalTemplateVariables": env_definition.get("envTemplate", {}).get(
                        "additionalTemplateVariables", {}),
                    "cluster": {
                        "name": cluster_name,
                        # Add cluster-specific properties that might be used in templates
                        "cloud_api_url": env_definition.get("envTemplate", {}).get("additionalTemplateVariables",
                                                                                   {}).get("cloud_api_url", ""),
                        "cloud_api_port": env_definition.get("envTemplate", {}).get("additionalTemplateVariables",
                                                                                    {}).get("cloud_api_port", ""),
                        "cloud_public_url": env_definition.get("envTemplate", {}).get("additionalTemplateVariables",
                                                                                      {}).get("cloud_public_url", ""),
                        "cloud_api_protocol": env_definition.get("envTemplate", {}).get("additionalTemplateVariables",
                                                                                        {}).get("cloud_api_protocol",
                                                                                                "https")
                    }
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
            if "parameters" in paramSetValues:
                paramSetParameters = paramSetValues["parameters"]
            else:
                paramSetParameters = {}
            if "applications" in paramSetValues:
                paramSetAppParams = list(paramSetValues["applications"])
            else:
                paramSetAppParams = []
            paramsetDefinitionComment = "paramset: " + paramSetName + " version: " + str(
                paramSetVersion) + " source: " + ("template" if is_from_template_dir(paramSetFile) else "instance")
            # process parameters in ParamSet
            for k in paramSetParameters:
                # get value with potential merge of dicts
                val = get_merged_param_value(k, params, paramSetParameters)
                store_value_to_yaml(params, k, val, paramsetDefinitionComment)
                # fill env specific parameters map for env specific paramset
                if isEnvSpecificParamset:
                    storeToEnvSpecificParametersMap(env_specific_params_map, "", parametersTag, k, val, pset)
            # prepare application parameters
            application_paramsets.append((paramsetDefinitionComment, paramSetAppParams, pset, isEnvSpecificParamset))
    params = sortParameters(params)
    return params, application_paramsets


def convertParameterSetsToParameters(templatePath, paramsTemplate, paramsetsTag, parametersTag, paramset_map,
                                     env_specific_params_map, env_definition, header_text=""):
    params, application_paramsets = mergeParameterSetsIntoParameters(
        templatePath, paramsTemplate, paramsetsTag, parametersTag, paramset_map, env_specific_params_map,
        env_definition)
    for paramsetDefinitionComment, paramSetAppParams, pset, isEnvSpecificParamset in application_paramsets:
        convertParameterSetsToApplication(templatePath, paramsetDefinitionComment, paramSetAppParams, pset,
                                          parametersTag, isEnvSpecificParamset, env_specific_params_map,
                                          header_text)
    return params


def convertParameterSetsToApplication(templatePath, paramsetDefinitionComment, applicationsParamSets, paramsetName,
                                      parametersTag, isEnvSpecificParamset, env_specific_params_map, header_text=""):
    application_schema = f"{get_schema_dir()}/application.schema.json"
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
        validate_yaml_by_scheme_or_fail(input_yaml_content=appDefinition, schema_file_path=application_schema)
        current_env_instance_store().beautify(applicationParametersFile, application_schema, header_text)
    return


def initParametersStructure(map, key, is_app=False):
    if key not in map:
        map[key] = {}
    map[key]["deployParameters"] = {}
    map[key]["e2eParameters"] = {}
    map[key]["technicalConfigurationParameters"] = {}
    if not is_app:
        map[key]["applications"] = {}


def storeToEnvSpecificParametersMap(env_specific_params_map, applicationName, parametersTag, paramKey, paramValue,
                                    paramsetName):
    if applicationName:
        # todo: nail all 3 parameter tags
        if applicationName not in env_specific_params_map["applications"]:
            initParametersStructure(env_specific_params_map["applications"], applicationName, is_app=True)
        env_specific_params_map["applications"][applicationName][parametersTag][paramKey] = {"value": paramValue,
                                                                                             "paramsetName": paramsetName}
    else:
        env_specific_params_map[parametersTag][paramKey] = {"value": paramValue, "paramsetName": paramsetName}


def getApplicationParametersYaml(appName, applicationParametersFile):
    result = yaml.load("name: \"" + appName + "\"\ndeployParameters: {}\ntechnicalConfigurationParameters: {}\n")
    env_instance_store = current_env_instance_store()
    if env_instance_store.exists(applicationParametersFile):
        result = env_instance_store.get(applicationParametersFile)
    else:
        env_instance_store.put(applicationParametersFile, result)
    return result


def updateEnvSpecificParamsets(envDefinitionYaml, templateName, templateContent, paramset_map):
    result = {}
    if "envSpecificParamsets" in envDefinitionYaml["envTemplate"]:
        if templateName in envDefinitionYaml["envTemplate"]["envSpecificParamsets"]:
            envSpecificParamsets = envDefinitionYaml["envTemplate"]["envSpecificParamsets"][templateName]
            logger.info(
                f"Attaching env-specific deployment paramsets: {dump_as_yaml_format(envSpecificParamsets)} to template {templateName}")
            templateContent["deployParameterSets"] = templateContent["deployParameterSets"] + envSpecificParamsets
            for pset in envSpecificParamsets:
                # Check if paramset exists in paramset_map before accessing it
                if pset in paramset_map:
                    for value in paramset_map[pset]:
                        value["envSpecific"] = True
                else:
                    raise ReferenceError(
                        f"Paramset '{pset}' referenced in envSpecificParamsets for template '{templateName}' was not found. Please create the missing parameter file or remove the reference from env_definition.yml.")
    if "envSpecificE2EParamsets" in envDefinitionYaml["envTemplate"]:
        if templateName in envDefinitionYaml["envTemplate"]["envSpecificE2EParamsets"]:
            envSpecificParamsets = envDefinitionYaml["envTemplate"]["envSpecificE2EParamsets"][templateName]
            logger.info(
                f"Attaching env-specific E2E paramsets: {dump_as_yaml_format(envSpecificParamsets)} to template {templateName}")
            templateContent["e2eParameterSets"] = templateContent["e2eParameterSets"] + envSpecificParamsets
            for pset in envSpecificParamsets:
                # Check if paramset exists in paramset_map before accessing it
                if pset in paramset_map:
                    for value in paramset_map[pset]:
                        value["envSpecific"] = True
                else:
                    raise ReferenceError(
                        f"Paramset '{pset}' referenced in envSpecificE2EParamsets for template '{templateName}' was not found. Please create the missing parameter file or remove the reference from env_definition.yml.")
    if "envSpecificTechnicalParamsets" in envDefinitionYaml["envTemplate"]:
        if templateName in envDefinitionYaml["envTemplate"]["envSpecificTechnicalParamsets"]:
            envSpecificParamsets = envDefinitionYaml["envTemplate"]["envSpecificTechnicalParamsets"][templateName]
            logger.info(
                f"Attaching env-specific technical paramsets: {dump_as_yaml_format(envSpecificParamsets)} to template {templateName}")
            templateContent["technicalConfigurationParameterSets"] = templateContent[
                                                                         "technicalConfigurationParameterSets"] + envSpecificParamsets
            for pset in envSpecificParamsets:
                # Check if paramset exists in paramset_map before accessing it
                if pset in paramset_map:
                    for value in paramset_map[pset]:
                        value["envSpecific"] = True
                else:
                    raise ReferenceError(
                        f"Paramset '{pset}' referenced in envSpecificTechnicalParamsets for template '{templateName}' was not found. Please create the missing parameter file or remove the reference from env_definition.yml.")
    return result


def processTemplate(templatePath, templateName, env_definition, schema_path, paramset_map, env_specific_params_map,
                    resource_profiles_map=None, header_text="", process_env_specific=True):
    logger.info(f"Processing template: {templateName} in {templatePath}")
    env_instance_store = current_env_instance_store()
    templateContent = env_instance_store.get(templatePath)
    if process_env_specific:
        updateEnvSpecificParamsets(env_definition, templateName, templateContent, paramset_map)
    # process deployParameters
    templateContent["deployParameters"] = convertParameterSetsToParameters(templatePath, templateContent,
                                                                           "deployParameterSets", "deployParameters",
                                                                           paramset_map, env_specific_params_map,
                                                                           env_definition, header_text)
    templateContent["deployParameterSets"] = []
    # process e2eParameters
    templateContent["e2eParameters"] = convertParameterSetsToParameters(templatePath, templateContent,
                                                                        "e2eParameterSets", "e2eParameters",
                                                                        paramset_map, env_specific_params_map,
                                                                        env_definition, header_text)
    templateContent["e2eParameterSets"] = []
    # process technicalConfigurationParameters
    templateContent["technicalConfigurationParameters"] = convertParameterSetsToParameters(templatePath,
                                                                                           templateContent,
                                                                                           "technicalConfigurationParameterSets",
                                                                                           "technicalConfigurationParameters",
                                                                                           paramset_map,
                                                                                           env_specific_params_map,
                                                                                           env_definition,
                                                                                           header_text)
    templateContent["technicalConfigurationParameterSets"] = []
    # preparing map for needed resource profiles
    if has_valid_profile_name(templateContent):
        rpName = templateContent["profile"]["name"]
        resource_profiles_map[templateName] = rpName
    validate_yaml_by_scheme_or_fail(input_yaml_content=templateContent, schema_file_path=schema_path)
    env_instance_store.beautify(templatePath, schema_path, header_text)
    return


def process_additional_template_parameters(inventoryYaml, source_env_dir, all_instances_dir):
    envDefinitionPath = getEnvDefinitionPath(source_env_dir)
    shared_template_vars_values = inventoryYaml["envTemplate"].get("sharedTemplateVariables", [])

    if not shared_template_vars_values:
        logger.info(f"No shared templates variables are defined in: {envDefinitionPath}")
        return

    levels = [
        Path(source_env_dir) / "Inventory",
        Path(source_env_dir).parent,
        Path(all_instances_dir),
    ]

    template_params_dir_names = ["configuration", "configurations"]
    shared_template_vars_paths = [level / name for level in levels for name in template_params_dir_names]
    shared_template_vars_paths.append(Path(source_env_dir) / "Inventory")

    result = {}
    for file_name in shared_template_vars_values:
        for p in shared_template_vars_paths:
            found_path = find_yaml_file(p, file_name, recursively=True)
            if found_path:
                addedVars = openYaml(found_path)
                result.update(addedVars)
                logger.info(f"Shared template variables added from: {found_path}: \n{dump_as_yaml_format(addedVars)}")
                break
        else:
            raise ReferenceError(f"Shared template variables with key {file_name} not found")

    # updating additional template variables from map
    additional_template_vars = inventoryYaml["envTemplate"].get("additionalTemplateVariables", {})
    logger.debug(f"Additional template variables from inventory: \n{dump_as_yaml_format(additional_template_vars)}")
    result.update(additional_template_vars)

    # storing to yaml
    logger.info(f"Resulting additional template variables are: \n{dump_as_yaml_format(result)}")
    inventoryYaml["envTemplate"]["additionalTemplateVariables"] = result


def build_env(env_instances_dir, envDefinitionYaml, parameters_dir, resource_profiles_dir,
              env_specific_resource_profile_map, all_instances_dir, render_context, templates_dirs=None, is_external_cred_env=False):
    # Check which role-specific templates were downloaded
    templates_dirs = templates_dirs or {}
    origin_template_exists = NamespaceRole.ORIGIN in templates_dirs
    peer_template_exists = NamespaceRole.PEER in templates_dirs
    logger.info(f"Templates dirs: {list(templates_dirs.keys())}, "
                f"origin_exists={origin_template_exists}, peer_exists={peer_template_exists}")

    # Create role-specific paramset maps
    origin_paramset_map = create_paramset_map(parameters_dir, NamespaceRole.ORIGIN,
                                              origin_template_exists, peer_template_exists)
    peer_paramset_map = create_paramset_map(parameters_dir, NamespaceRole.PEER,
                                            origin_template_exists, peer_template_exists)
    common_paramset_map = create_paramset_map(parameters_dir, NamespaceRole.COMMON,
                                              origin_template_exists, peer_template_exists)

    env_instance_store = current_env_instance_store()
    env_dir = Path(env_instances_dir)
    logger.info(f"Env dir: {env_dir}")
    logger.info(f"Parameters dir: {parameters_dir}")
    # const
    tenant_schema = f"{get_schema_dir()}/tenant.schema.json"
    cloud_schema = f"{get_schema_dir()}/cloud.schema.json"
    namespace_schema = f"{get_schema_dir()}/namespace.schema.json"
    profiles_schema = f"{get_schema_dir()}/resource-profile.schema.json"

    logger.info(getEnvDefinitionPath(env_instances_dir))
    templateArtifactName = getTemplateArtifactName(envDefinitionYaml)
    generated_header_text = GENERATED_HEADER % templateArtifactName

    tenantTemplatePath = env_dir / "tenant.yml"
    cloudTemlatePath = env_dir / "cloud.yml"
    namespaces = env_instance_store.namespaces()
    # env specific parameters map - will be filled with env specific parameters during template processing
    env_specific_parameters_map = {}
    env_specific_parameters_map["namespaces"] = {}

    # process tenant
    logger.info(f"Processing tenant: {tenantTemplatePath}")
    validate_yaml_by_scheme_or_fail(input_yaml_content=env_instance_store.get(tenantTemplatePath),
                                    schema_file_path=tenant_schema)
    env_instance_store.beautify(tenantTemplatePath, tenant_schema, generated_header_text)

    # process cloud
    needed_resource_profiles_map = {}
    logger.info(f"Processing cloud: {cloudTemlatePath}")
    initParametersStructure(env_specific_parameters_map, "cloud")
    logger.info("Processing cloud without env specific parameters.")
    processTemplate(
        cloudTemlatePath,
        "cloud",
        envDefinitionYaml,
        cloud_schema,
        common_paramset_map,
        env_specific_parameters_map["cloud"],
        resource_profiles_map=needed_resource_profiles_map,
        header_text=generated_header_text,
        process_env_specific=False)
    # process cloud passport
    process_cloud_passport(env_instances_dir, all_instances_dir, envDefinitionYaml, is_external_cred_env)
    logger.info("Processing cloud with env specific parameters.")
    processTemplate(
        cloudTemlatePath,
        "cloud",
        envDefinitionYaml,
        cloud_schema,
        common_paramset_map,
        env_specific_parameters_map["cloud"],
        resource_profiles_map=needed_resource_profiles_map,
        header_text=generated_header_text,
        process_env_specific=True)

    # process namespaces
    template_namespace_names = []
    for ns in namespaces:
        logger.info(f"Processing namespace: {ns.definition_path}")
        template_namespace_names.append(ns.postfix)
        initParametersStructure(env_specific_parameters_map['namespaces'], ns.postfix)

        if ns.role == NamespaceRole.ORIGIN:
            ns_paramset_map = origin_paramset_map
        elif ns.role == NamespaceRole.PEER:
            ns_paramset_map = peer_paramset_map
        else:
            ns_paramset_map = common_paramset_map
        processTemplate(
            ns.definition_path,
            ns.postfix,
            envDefinitionYaml,
            namespace_schema,
            ns_paramset_map,
            env_specific_parameters_map['namespaces'][ns.postfix],
            resource_profiles_map=needed_resource_profiles_map,
            header_text=generated_header_text,
        )
    operation_type = OperationType(getenv("OPERATION_TYPE"))
    if operation_type == OperationType.CLEAN:
        set_cleaned_mark(namespaces)
    logger.info(f"EnvSpecific parameters are: \n{dump_as_yaml_format(env_specific_parameters_map)}")
    checkEnvSpecificParametersBySchema(env_dir, env_specific_parameters_map, template_namespace_names)

    # process resource profiles
    result_profiles_dir = Path(f"{env_dir}/Profiles")
    all_profiles = collect_resource_profiles(resource_profiles_dir, profiles_schema,
                                             needed_resource_profiles_map, render_context)
    object_paths = {"cloud": cloudTemlatePath} | {ns.postfix: ns.definition_path for ns in namespaces}
    object_baselines = {key: get_profile_baseline(env_instance_store.get(path).get("profile") or {})
                        for key, path in object_paths.items()}
    override_profile_map = override_by_env_specific_profiles(all_profiles, env_specific_resource_profile_map,
                                                             render_context, object_baselines)

    for profile_key, profile_file_path in override_profile_map.items():
        all_profiles[profile_key] = profile_file_path
        profile_name = env_instance_store.get(profile_file_path).get("name")
        if not profile_name:
            logger.warning(f"Environment specific resource profile '{profile_file_path}' for '{profile_key}' has no "
                           f"'name', so the profile cannot be found during effective set generation and its "
                           f"parameters are not applied")
        logger.info(f"'{profile_key}' profile.name is '{profile_name}' from environment specific profile "
                    f"'{profile_file_path}'")
        set_object_profile_field(object_paths[profile_key], "name", profile_name)

    for profile_key, profile_file_path in all_profiles.items():
        baseline = get_profile_baseline(env_instance_store.get(profile_file_path))
        if baseline:
            logger.info(f"'{profile_key}' profile.baseline is '{baseline}'")
            set_object_profile_field(object_paths[profile_key], "baseline", baseline)
        elif object_baselines[profile_key]:
            logger.info(f"'{profile_key}' resource profile '{profile_file_path}' has no baseline field, "
                        f"profile.baseline '{object_baselines[profile_key]}' of the object is kept")
        else:
            logger.info(f"'{profile_key}' has no baseline: neither resource profile '{profile_file_path}' "
                        f"nor the object sets it")

    for profile_file_path in dict.fromkeys(all_profiles.values()):
        logger.info(f"Copying profile '{profile_file_path}' to resulting directory '{result_profiles_dir}'")
        resulting_profile_path = result_profiles_dir / Path(profile_file_path).name
        env_instance_store.put(resulting_profile_path, env_instance_store.get(profile_file_path))
        env_instance_store.beautify(resulting_profile_path, profiles_schema, generated_header_text)


def set_cleaned_mark(namespaces: list[NamespaceFile]):
    ns_map = {ns.name: ns for ns in namespaces}
    ns_names_var = getenv("NAMESPACE_NAMES")
    if not ns_names_var:
        logger.info("NAMESPACE_NAMES is empty, marking all namespaces as cleaned (env-cleanup)")
        filtered_ns = namespaces.copy()
    else:
        ns_names = split_multi_value_param(ns_names_var)
        filtered_ns = []
        for name in ns_names:
            ns_obj = ns_map.get(name)
            if ns_obj is None:
                raise ValueError(f"Operation type CLEAN: namespace '{name}' not found in env_instance")
            filtered_ns.append(ns_obj)
    for ns in filtered_ns:
        logger.info(f"Operation type CLEAN: setting cleaned=true for namespace '{ns.name}'")
        ns_yaml = current_env_instance_store().get(ns.definition_path)
        set_nested_yaml_attribute(ns_yaml, "cleaned", True)
