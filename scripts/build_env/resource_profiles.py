from time import time as _diag_now

from envgenehelper import Path, copy, current_env_instance_store, dump_as_yaml_format, extractNameFromFile, findAllYamlsInDir, find_yaml_file, getEnvDefinitionPath, get_empty_yaml, logger, merge_dict_key_with_comment, set_nested_yaml_attribute, validate_yaml_by_scheme_or_fail
from build_env.render_config_env import EnvGenerator


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
                env_instance_store = current_env_instance_store()
                env_specific_profile = env_instance_store.put(found_path, env_instance_store.load_profile_from_cache(found_path))
                validate_yaml_by_scheme_or_fail(input_yaml_content=env_specific_profile, schema_file_path=rp_schema)
                result[templateType] = str(found_path)
                break
        if templateType not in result:
            raise ReferenceError(f"Resource profile file with key '{profile_file_name}' not found.")
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


def get_profile_baseline(profile_yaml):
    baseline = profile_yaml.get("baseline")
    return baseline if baseline and baseline.strip() else None


def has_profile_parameters(profile_yaml):
    return any(service["parameters"]
               for app in profile_yaml.get("applications") or []
               for service in app["services"])


def merge_resource_profiles(sourceProfileYaml, overrideProfileYaml, overrideProfileName, object_baseline=None):
    commentText = f"from {overrideProfileName}"
    template_name = sourceProfileYaml.get("name")
    template_baseline = get_profile_baseline(sourceProfileYaml)
    source_baseline = template_baseline or object_baseline
    if template_baseline:
        source_origin = f"baseline '{template_baseline}' from template profile '{template_name}'"
    elif object_baseline:
        source_origin = f"baseline '{object_baseline}' from the object"
    else:
        source_origin = "no baseline"
    override_baseline = get_profile_baseline(overrideProfileYaml)
    if override_baseline:
        if override_baseline != source_baseline and has_profile_parameters(sourceProfileYaml):
            logger.warning(f"Merging environment specific profile '{overrideProfileName}' with baseline "
                           f"'{override_baseline}' into template profile '{template_name}' that carries parameters "
                           f"and has {source_origin}. Use replace mode to change the baseline.")
        logger.info(f"Template profile '{template_name}' takes baseline '{override_baseline}' from environment "
                    f"specific profile '{overrideProfileName}', previously {source_origin}")
        merge_dict_key_with_comment("baseline", sourceProfileYaml, "baseline", overrideProfileYaml, commentText)
    else:
        logger.info(f"Environment specific profile '{overrideProfileName}' does not change the baseline, "
                    f"template profile '{template_name}' keeps {source_origin}")
    if not overrideProfileYaml.get("applications"):
        return
    if sourceProfileYaml.get("applications") is None:
        sourceProfileYaml["applications"] = []
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


def find_resource_profile(profile_name: str, template_profiles_dir, disk_profile_paths: dict) -> Path | None:
    env_instance_store = current_env_instance_store()
    _t0 = _diag_now()
    profile_path = env_instance_store.find_yaml(template_profiles_dir, profile_name)
    _t_store = _diag_now()
    if profile_path:
        logger.debug(f"[diag] profile '{profile_name}' found in store in {( _t_store - _t0) * 1000:.1f}ms")
        return profile_path
    profile_path = disk_profile_paths.get(profile_name)
    if profile_path is None:
        return None
    _t_parse = _diag_now()
    env_instance_store.put(profile_path, env_instance_store.load_profile_from_cache(profile_path))
    _t_put = _diag_now()
    logger.debug(f"[diag] profile '{profile_name}' store-miss; parse+put in {(_t_put - _t_parse) * 1000:.1f}ms")
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
    validity_by_path = {}
    _t_dir0 = _diag_now()
    disk_profile_paths = {extractNameFromFile(path): Path(path) for path in findAllYamlsInDir(template_profiles_dir)}
    logger.debug(f"[diag] findAllYamlsInDir over profile dir: {( _diag_now() - _t_dir0) * 1000:.1f}ms, "
                f"{len(disk_profile_paths)} files indexed")
    for template_name, needed_profile in needed_resource_profiles.items():
        profile_path = find_resource_profile(needed_profile, template_profiles_dir, disk_profile_paths)
        if not profile_path:
            not_found += rp_data_template.format(needed_profile, template_name)
            continue
        logger.info(f"Found resource profile {needed_profile} in path: {profile_path}")
        if profile_path not in validity_by_path:
            _t_val0 = _diag_now()
            try:
                validate_yaml_by_scheme_or_fail(input_yaml_content=current_env_instance_store().get(profile_path),
                                                schema_file_path=profiles_schema)
                validity_by_path[profile_path] = True
                logger.debug(f"[diag] validate '{needed_profile}': {( _diag_now() - _t_val0) * 1000:.1f}ms")
            except ValueError:
                validity_by_path[profile_path] = False
        if not validity_by_path[profile_path]:
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


def override_by_env_specific_profiles(all_profiles, env_specific_resource_profile_map, render_context: EnvGenerator,
                                      object_baselines):
    override_profile_map = {}
    render_context.generate_profiles(set(env_specific_resource_profile_map.values()))
    combination_mode_key = "mergeEnvSpecificResourceProfiles"
    try:
        combination_mode = render_context.ctx.env_definition['inventory']['config'][combination_mode_key]
    except KeyError:
        logger.info(
            f"inventory.config.{combination_mode_key} key not found in env_definition, default value is 'true'")
        combination_mode = 'true'
    common_msg = f"profile overrides, because {combination_mode_key} is set to {combination_mode}"
    for profile_key, env_specific_profile_path in env_specific_resource_profile_map.items():
        if profile_key not in all_profiles:
            logger.info(f"No template profile for profile key '{profile_key}', attaching standalone "
                        f"environment specific profile {env_specific_profile_path}")
            override_profile_map[profile_key] = env_specific_profile_path
            continue
        template_profile_file_path = all_profiles[profile_key]
        logger.info(f"Profile key '{profile_key}' has template profile '{template_profile_file_path}' "
                    f"and environment specific profile '{env_specific_profile_path}'")
        template_profile_yaml = current_env_instance_store().get(template_profile_file_path)
        env_specific_profile_yaml = current_env_instance_store().get(env_specific_profile_path)

        if str(combination_mode).lower() == 'true':
            logger.info(f"Joining {common_msg}")
            merge_resource_profiles(template_profile_yaml, env_specific_profile_yaml,
                                    extractNameFromFile(env_specific_profile_path),
                                    object_baselines.get(profile_key))
        else:
            logger.info(f"Replacing {common_msg}")
            override_profile_map[profile_key] = env_specific_profile_path
    return override_profile_map


def has_valid_profile_name(content: dict) -> bool:
    profile = content.get("profile")
    return isinstance(profile, dict) and bool(profile.get("name"))


def set_object_profile_field(file_path, field, value):
    data = current_env_instance_store().get(file_path)
    if data.get("profile") is None:
        data["profile"] = get_empty_yaml()
    elif data["profile"].get(field) == value:
        return
    set_nested_yaml_attribute(data, f"profile.{field}", value)
