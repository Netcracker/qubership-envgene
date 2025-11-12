import copy
from envgenehelper import *
from generate_config_env import EnvGenerator


# TODO unit tests
def get_env_specific_resource_profiles(env_dir, instances_dir, rp_schema):
    result = {}
    logger.info(f"Finding env specific resource profiles for '{env_dir}' in '{instances_dir}'")
    envDefinitionPath = getEnvDefinitionPath(env_dir)
    inventoryYaml = getEnvDefinition(env_dir)

    if not "envSpecificResourceProfiles" in inventoryYaml["envTemplate"]:
        logger.info(f"No environment specific resource profiles are defined in {envDefinitionPath}")
        return result
    envSepcificResourceProfileNames = inventoryYaml["envTemplate"]["envSpecificResourceProfiles"]
    logger.info(
        f"Environment specific resource profiles for '{envDefinitionPath}' are: \n{dump_as_yaml_format(envSepcificResourceProfileNames)}")
    for templateType in envSepcificResourceProfileNames:
        logger.debug(f"Searching for env specific resource profiles for template '{templateType}'")
        profileFileName = envSepcificResourceProfileNames[templateType]
        logger.debug(f"Searching for {profileFileName} for template type {templateType}")
        resourceProfileFiles = findResourcesBottomTop(env_dir, instances_dir, f"/{profileFileName}.")
        if len(resourceProfileFiles) == 1:
            yamlPath = resourceProfileFiles[0]
            result[templateType] = yamlPath
            validate_yaml_by_scheme_or_fail(yamlPath, rp_schema)
            logger.info(f"Env specific resource profile file for '{profileFileName}' added from: '{yamlPath}'")
        elif len(resourceProfileFiles) > 1:
            logger.error(
                f"Duplicate resource profile files with key '{profileFileName}' found in '{instances_dir}': \n\t" + ",\n\t".join(
                    str(x) for x in resourceProfileFiles))
            raise ReferenceError(
                f"Duplicate resource profile files with key '{profileFileName}' found. See logs above.")
        else:
            raise ReferenceError(f"Resource profile file with key '{profileFileName}' not found in '{instances_dir}'")
    logger.info(f"Env specific resource profiles are: \n{dump_as_yaml_format(result)}")
    return result


def getResourceProfilesFromDir(dir):
    result = {}
    rpYamls = findAllYamlsInDir(dir)
    for profileFile in rpYamls:
        result[extractNameFromFile(profileFile)] = profileFile
    logger.info(f"Resource profiles in folder {dir}: \n{dump_as_yaml_format(result)}")
    return result


def get_app_from_resource_profile(appName, profile_yaml):
    for value in profile_yaml["applications"]:
        if appName == value["name"]:
            return value
    return None


def get_service_from_resource_profile_app(serviceName, app_yaml):
    for value in app_yaml["services"]:
        if serviceName == value["name"]:
            return value
    return None


def get_param_from_resource_profile_service(paramName, service_yaml):
    for value in service_yaml["parameters"]:
        if paramName == value["name"]:
            return value
    return None


def merge_resource_profiles(sourceProfileYaml, overrideProfileYaml, overrideProfileName):
    commentText = f"from {overrideProfileName}"
    for app in overrideProfileYaml["applications"]:
        sourceApp = get_app_from_resource_profile(app["name"], sourceProfileYaml)
        # if app not in template profile, adding it and iterating to make comments
        if not sourceApp:
            sourceApp = copy.deepcopy(app)
            sourceProfileYaml["applications"].append(sourceApp)
            merge_dict_key_with_comment("name", sourceApp, "name", app, commentText)
        merge_dict_key_with_comment("version", sourceApp, "version", app, commentText)
        merge_dict_key_with_comment("sd", sourceApp, "sd", app, commentText)
        for service in app["services"]:
            sourceService = get_service_from_resource_profile_app(service["name"], sourceApp)
            if not sourceService:
                sourceService = copy.deepcopy(service)
                sourceApp["services"].append(sourceService)
                merge_dict_key_with_comment("name", sourceService, "name", service, commentText)
            for param in service["parameters"]:
                sourceParam = get_param_from_resource_profile_service(param["name"], sourceService)
                if not sourceParam:
                    sourceParam = copy.deepcopy(param)
                    sourceService["parameters"].append(sourceParam)
                    merge_dict_key_with_comment("name", sourceParam, "name", param, commentText)
                    merge_dict_key_with_comment("value", sourceParam, "value", param, commentText)
                else:
                    merge_dict_key_with_comment("value", sourceParam, "value", param, commentText)


def validate_resource_profiles(needed_resource_profiles: dict[str, str], source_profiles: dict[str, str],
                               profiles_schema: str) -> dict[str, str]:
    profiles_map = {}
    not_found = ''
    not_valid = ''
    err_msg = ''
    rp_data_template = "\n\t profile: {} for namespace {}"

    if not needed_resource_profiles:
        return profiles_map
    for template_name, needed_profile in needed_resource_profiles.items():
        if needed_profile not in source_profiles:
            not_found += rp_data_template.format(needed_profile, template_name)
            continue
        profile_path = source_profiles[needed_profile]
        logger.info(f"Found resource profile {needed_profile} in path: {profile_path}")
        try:
            validate_yaml_by_scheme_or_fail(profile_path, profiles_schema)
        except ValueError:
            not_valid += rp_data_template.format(needed_profile, template_name)
            continue
        profiles_map[template_name] = profile_path

    if len(not_valid) > 0:
        err_msg += "These resource profiles are invalid, look for details above:"
        err_msg += not_valid
    if len(not_found) > 0:
        err_msg += "Can't find resource profiles:"
        err_msg += not_found
    if len(err_msg) > 0:
        logger.error(err_msg)
        raise ReferenceError("Not all needed resource profiles found or valid. See logs above.")
    return profiles_map


def processResourceProfiles(env_dir, resource_profiles_dir, profiles_schema, needed_resource_profiles_map,
                            env_specific_resource_profile_map, render_context: EnvGenerator, header_text=""):
    logger.info(f"Needed profiles map: \n{dump_as_yaml_format(needed_resource_profiles_map)}")
    render_context.generate_profiles(set(needed_resource_profiles_map.values()))
    render_context.generate_profiles(set(env_specific_resource_profile_map.values()))
    # map for profiles from templates
    templateProfilesMap = getResourceProfilesFromDir(resource_profiles_dir)
    envRpDir = f"{env_dir}/Profiles"
    environmentDirProfilesMap = getResourceProfilesFromDir(envRpDir)
    # joining resource profiles with the result of Jinja generation
    sourceProfilesMap = templateProfilesMap | environmentDirProfilesMap
    logger.info(f"All resource profiles map is: \n{dump_as_yaml_format(sourceProfilesMap)}")
    # check that all required resource profiles exists and are valid
    profilesMap = validate_resource_profiles(needed_resource_profiles_map, sourceProfilesMap, profiles_schema)
    # iterate through env specific resource profiles and perform override
    for templateName, envSpecificProfileFile in env_specific_resource_profile_map.items():
        if templateName not in profilesMap:
            logger.error(
                f"No override profile for {templateName} found. Can't apply environment specific resource profile {envSpecificProfileFile}")
            raise ReferenceError(
                f"Can't apply environment specific resource profile for namespace {templateName}. Please set override profile in templates first.")
        logger.info(
            f"Joining template override profile for namespace '{templateName}' with environment specific profile {envSpecificProfileFile}")
        templateProfileFilePath = profilesMap[templateName]
        templateProfileYaml = openYaml(templateProfileFilePath)
        envSpecificProfileYaml = openYaml(envSpecificProfileFile)
        # decide here whether to merge or replace
        merge_resource_profiles(templateProfileYaml, envSpecificProfileYaml,
                                extractNameFromFile(envSpecificProfileFile))
        writeYamlToFile(templateProfileFilePath, templateProfileYaml)
    # copying source and overriden profiles to resulting dir
    for profileKey, profileFilePath in profilesMap.items():
        logger.debug(f"Copying '{profileKey}' to resulting directory '{envRpDir}'")
        copy_path(profileFilePath, f"{envRpDir}/")
        resultingProfilePath = f"{envRpDir}/{extractNameFromFile(profileFilePath)}.yml"
        resultingProfilePath = identify_yaml_extension(resultingProfilePath)
        beautifyYaml(resultingProfilePath, profiles_schema, header_text)
