from envgenehelper import Path, copy, current_env_instance_store, dump_as_yaml_format, extractNameFromFile, find_yaml_file, getEnvDefinitionPath, logger, merge_dict_key_with_comment, openYaml, set_nested_yaml_attribute, validate_yaml_by_scheme_or_fail
from build_env.render_config_env import EnvGenerator


# TODO unit tests
def get_env_specific_resource_profiles(env_dir, instances_dir, rp_schema, inventoryYaml):
    levels = [
        Path(env_dir) / "Inventory",
        Path(env_dir).parent,
        Path(instances_dir),
    ]

    rp_dir_names = ["resource_profiles", "rp_override", "Profiles", "parameters"]

    result = {}
    logger.info(f"Finding env specific resource profiles for '{env_dir}' in '{instances_dir}'")
    envDefinitionPath = getEnvDefinitionPath(env_dir)

    if not "envSpecificResourceProfiles" in inventoryYaml["envTemplate"]:
        logger.info(f"No environment specific resource profiles are defined in {envDefinitionPath}")
        return result
    envSepcificResourceProfileNames = inventoryYaml["envTemplate"]["envSpecificResourceProfiles"]
    logger.info(
        f"Environment specific resource profiles for '{envDefinitionPath}' are: \n{dump_as_yaml_format(envSepcificResourceProfileNames)}")

    for templateType in envSepcificResourceProfileNames:
        profile_file_name = envSepcificResourceProfileNames[templateType]
        logger.debug(f"Searching for {profile_file_name} for template type {templateType}")
        shared_rp_paths = [level / name for level in levels for name in rp_dir_names]

        for p in shared_rp_paths:
            found_path = find_yaml_file(p, profile_file_name, recursively=True)
            if found_path:
                logger.info(f"Env specific resource profile file for '{profile_file_name}' found in '{found_path}'")
                env_specific_profile = current_env_instance_store().put(found_path, openYaml(found_path))
                validate_yaml_by_scheme_or_fail(input_yaml_content=env_specific_profile, schema_file_path=rp_schema)
                result[templateType] = str(found_path)
                break
        if templateType not in result:
            raise ReferenceError(f"Resource profile file with key '{profile_file_name}' not found.")
    logger.info(f"Env specific resource profiles are: \n{dump_as_yaml_format(result)}")
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


def find_resource_profile(profile_name: str, template_profiles_dir) -> Path | None:
    env_instance_store = current_env_instance_store()
    profile_path = env_instance_store.find_yaml(template_profiles_dir, profile_name)
    if profile_path:
        return profile_path
    profile_path = find_yaml_file(Path(template_profiles_dir), profile_name, recursively=True)
    if profile_path:
        env_instance_store.put(profile_path, openYaml(profile_path))
    return profile_path


def validate_resource_profiles(needed_resource_profiles: dict[str, str], template_profiles_dir,
                               profiles_schema: str) -> dict[str, str]:
    profiles_map = {}
    not_found = ''
    not_valid = ''
    err_msg = ''
    rp_data_template = "\n\t profile: {} for namespace {}"

    if not needed_resource_profiles:
        return profiles_map
    for template_name, needed_profile in needed_resource_profiles.items():
        profile_path = find_resource_profile(needed_profile, template_profiles_dir)
        if not profile_path:
            not_found += rp_data_template.format(needed_profile, template_name)
            continue
        logger.info(f"Found resource profile {needed_profile} in path: {profile_path}")
        try:
            validate_yaml_by_scheme_or_fail(input_yaml_content=current_env_instance_store().get(profile_path),
                                            schema_file_path=profiles_schema)
        except ValueError:
            not_valid += rp_data_template.format(needed_profile, template_name)
            continue
        profiles_map[template_name] = str(profile_path)

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


def collect_resource_profiles(template_profiles_dir, profiles_schema,
                              required_resource_profiles_map, render_context: EnvGenerator):
    logger.info(f"Required profiles map:\n{dump_as_yaml_format(required_resource_profiles_map)}")
    render_context.generate_profiles(set(required_resource_profiles_map.values()))
    profiles_map = validate_resource_profiles(required_resource_profiles_map, template_profiles_dir, profiles_schema)
    return profiles_map


def override_by_env_specific_profiles(all_profiles, env_specific_resource_profile_map, render_context: EnvGenerator):
    override_profile_map = {}
    render_context.generate_profiles(set(env_specific_resource_profile_map.values()))
    for profile_key, env_specific_profile_path in env_specific_resource_profile_map.items():
        if profile_key not in all_profiles:
            raise ReferenceError(
                f"Environment specific profile '{env_specific_profile_path}' is mapped to key "
                f"'{profile_key}' in envTemplate.envSpecificResourceProfiles, but the "
                f"namespace template has no profile.name. Resource profile overrides require "
                f"a profile.name on the corresponding cloud or namespace template."
            )
        logger.info(f"Found template override profile for profile key '{profile_key}'"
                    f" with environment specific profile {env_specific_profile_path}")
        template_profile_file_path = all_profiles[profile_key]
        template_profile_yaml = current_env_instance_store().get(template_profile_file_path)
        env_specific_profile_yaml = current_env_instance_store().get(env_specific_profile_path)

        combination_mode_key = "mergeEnvSpecificResourceProfiles"
        try:
            combination_mode = render_context.ctx.env_definition['inventory']['config'][combination_mode_key]
        except KeyError:
            logger.info(
                f"inventory.config.{combination_mode_key} key not found in env_definition, default value is 'true'")
            combination_mode = 'true'
        common_msg = f"profile overrides, because {combination_mode_key} is set to {combination_mode}"

        if str(combination_mode).lower() == 'true':
            logger.info(f"Joining {common_msg}")
            merge_resource_profiles(template_profile_yaml, env_specific_profile_yaml,
                                    extractNameFromFile(env_specific_profile_path))
        else:
            logger.info(f"Replacing {common_msg}")
            override_profile_map[profile_key] = env_specific_profile_path
    return override_profile_map


def has_valid_profile_name(content: dict) -> bool:
    profile = content.get("profile")
    return isinstance(profile, dict) and bool(profile.get("name"))


def update_profile_name(file_path, profile_name):
    data = current_env_instance_store().get(file_path)
    if has_valid_profile_name(data):
        set_nested_yaml_attribute(data, "profile.name", profile_name)
