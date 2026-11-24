from envgenehelper import Path, YamlBacked, copy, current_env_instance_store, dump_as_yaml_format, extractNameFromFile, findAllYamlsInDir, find_yaml_file, getEnvDefinitionPath, get_empty_yaml, logger, merge_dict_key_with_comment, set_nested_yaml_attribute
from build_env.deployment_profile import GENERATED_PROFILES_MAP_KEY, PROFILE_OVERRIDE_SUFFIX
from build_env.render_config_env import EnvGenerator
from envgene_shared.utils.business_utils import to_bool

ENV_SPECIFIC_PROFILES_MAP_KEY = "envSpecificResourceProfiles"
RESULTING_PROFILES_DIR_NAME = "Profiles"


def get_resource_profiles_map(env_dir, instances_dir, rp_schema, inventoryYaml,
                              map_key=ENV_SPECIFIC_PROFILES_MAP_KEY):
    levels = [
        Path(env_dir) / "Inventory",
        Path(env_dir).parent,
        Path(instances_dir),
    ]

    rp_dir_names = ["resource_profiles", "rp_override", "Profiles", "parameters"]

    result = {}
    logger.info(f"Finding '{map_key}' resource profiles for '{env_dir}' in '{instances_dir}'")
    envDefinitionPath = getEnvDefinitionPath(env_dir)

    if map_key not in inventoryYaml["envTemplate"]:
        logger.info(f"No {map_key} are defined in {envDefinitionPath}")
        return result
    resourceProfileNames = inventoryYaml["envTemplate"][map_key]
    logger.info(f"{map_key} for '{envDefinitionPath}' are: \n{dump_as_yaml_format(resourceProfileNames)}")

    for templateType, profile_file_name in resourceProfileNames.items():
        if map_key == ENV_SPECIFIC_PROFILES_MAP_KEY and profile_file_name.endswith(PROFILE_OVERRIDE_SUFFIX):
            logger.warning(f"'{profile_file_name}' in '{ENV_SPECIFIC_PROFILES_MAP_KEY}.{templateType}' is ignored, "
                           f"a name ending with '{PROFILE_OVERRIDE_SUFFIX}' is reserved for the profile the "
                           f"'PROFILE' parameter generates and is applied through '{GENERATED_PROFILES_MAP_KEY}'")
            continue
        logger.debug(f"Searching for {profile_file_name} for template type {templateType}")
        shared_rp_paths = [level / name for level in levels for name in rp_dir_names]
        for p in shared_rp_paths:
            found_path = find_yaml_file(p, profile_file_name, recursively=True)
            if found_path:
                logger.info(f"Env specific resource profile file for '{profile_file_name}' found in '{found_path}'")
                env_instance_store = current_env_instance_store()
                env_instance_store.put(found_path, env_instance_store.load_profile_from_cache(found_path))
                env_instance_store.bind(found_path, Path(rp_schema).name)
                result[templateType] = str(found_path)
                break
        if templateType not in result:
            raise ReferenceError(f"Resource profile file '{profile_file_name}' of "
                                 f"'{map_key}.{templateType}' is not found.")
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
        merge_dict_key_with_comment("baseline", sourceApp, "baseline", app, commentText)
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
    profile_path = env_instance_store.find_yaml(template_profiles_dir, profile_name)
    if profile_path:
        return profile_path
    profile_path = disk_profile_paths.get(profile_name)
    if profile_path is None:
        return None
    env_instance_store.put(profile_path, env_instance_store.load_profile_from_cache(profile_path))
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
    disk_profile_paths = {extractNameFromFile(path): Path(path) for path in findAllYamlsInDir(template_profiles_dir)}
    for template_name, needed_profile in needed_resource_profiles.items():
        profile_path = find_resource_profile(needed_profile, template_profiles_dir, disk_profile_paths)
        if not profile_path:
            not_found += rp_data_template.format(needed_profile, template_name)
            continue
        logger.info(f"Found resource profile {needed_profile} in path: {profile_path}")
        if profile_path not in validity_by_path:
            try:
                current_env_instance_store().bind(profile_path, Path(profiles_schema).name)
                validity_by_path[profile_path] = True
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


def apply_generated_override(profile_key, target_profile, generated_path, object_baseline):
    logger.info(f"Profile key '{profile_key}' applies the generated profile '{generated_path}' on top of its "
                f"profile '{target_profile.get('name')}'")
    merge_resource_profiles(target_profile, current_env_instance_store().get(generated_path),
                            extractNameFromFile(generated_path), object_baseline)


def result_profile_path(name, profile_key, taken_names):
    requested = name
    while name in taken_names:
        name = f"{name}-{profile_key}"
    if name != requested:
        logger.warning(f"This environment already has a profile named '{requested}', so the assembled profile of "
                       f"'{profile_key}' is saved as '{name}'")
    taken_names.add(name)
    return str(current_env_instance_store().env_dir / RESULTING_PROFILES_DIR_NAME / f"{name}.yml")


def assemble_profile(profile_key, base_path, base_name, generated_path, object_baseline, taken_names):
    env_instance_store = current_env_instance_store()
    result_path = result_profile_path(base_name, profile_key, taken_names)
    assembled = copy.deepcopy(env_instance_store.get(base_path))
    assembled["name"] = Path(result_path).stem
    env_instance_store.put(result_path, assembled)
    logger.info(f"Profile key '{profile_key}' assembles its profile from '{base_path}' as '{result_path}'")
    if generated_path and generated_path != base_path:
        apply_generated_override(profile_key, assembled, generated_path, object_baseline)
    return result_path


def drop_profiles_without_object(object_paths, *profile_maps):
    dropped = []
    for profile_key in dict.fromkeys(key for profile_map in profile_maps for key in profile_map):
        if profile_key in object_paths:
            continue
        for profile_map in profile_maps:
            profile_map.pop(profile_key, None)
        dropped.append(profile_key)
        logger.warning(f"Resource profile key '{profile_key}' matches no 'cloud' and no Namespace of this "
                       f"environment, so its resource profile is ignored. Remove the key from "
                       f"'{ENV_SPECIFIC_PROFILES_MAP_KEY}' or '{GENERATED_PROFILES_MAP_KEY}' when the Namespace is "
                       f"not part of the environment anymore")
    return dropped


def override_by_env_specific_profiles(all_profiles, env_specific_resource_profile_map, render_context: EnvGenerator,
                                      object_baselines, generated_profile_defaults_map=None):
    override_profile_map = {}
    generated_profile_defaults_map = generated_profile_defaults_map or {}
    render_context.generate_profiles(set(env_specific_resource_profile_map.values()) |
                                     set(generated_profile_defaults_map.values()))
    combination_mode_key = "mergeEnvSpecificResourceProfiles"
    try:
        combination_mode = render_context.ctx.env_definition['inventory']['config'][combination_mode_key]
    except KeyError:
        logger.info(
            f"inventory.config.{combination_mode_key} key not found in env_definition, default value is 'true'")
        combination_mode = 'true'
    merge_mode = to_bool(combination_mode)
    common_msg = f"profile overrides, because {combination_mode_key} is set to {combination_mode}"
    profile_keys = list(env_specific_resource_profile_map) + [key for key in generated_profile_defaults_map
                                                             if key not in env_specific_resource_profile_map]
    taken_names = {Path(profile_path).stem for profile_path in all_profiles.values()}
    taken_names |= {Path(profile_path).stem for profile_key, profile_path in env_specific_resource_profile_map.items()
                    if not generated_profile_defaults_map.get(profile_key)
                    and (not merge_mode or all_profiles.get(profile_key) is None)}
    for profile_key in profile_keys:
        env_specific_profile_path = env_specific_resource_profile_map.get(profile_key)
        generated_path = generated_profile_defaults_map.get(profile_key)
        object_baseline = object_baselines.get(profile_key)
        template_profile_file_path = all_profiles.get(profile_key)
        if template_profile_file_path is None:
            if not env_specific_profile_path:
                logger.info(f"Profile key '{profile_key}' has no profile of its own, taking the profile generated "
                            f"by the PROFILE parameter, '{generated_path}'")
                override_profile_map[profile_key] = assemble_profile(profile_key, generated_path,
                                                                     extractNameFromFile(generated_path),
                                                                     generated_path, object_baseline, taken_names)
                continue
            if not generated_path:
                logger.info(f"No template profile for profile key '{profile_key}', attaching standalone "
                            f"environment specific profile {env_specific_profile_path}")
                override_profile_map[profile_key] = env_specific_profile_path
                continue
            base_name = (Path(env_specific_profile_path).stem if merge_mode
                         else extractNameFromFile(generated_path))
            override_profile_map[profile_key] = assemble_profile(profile_key, env_specific_profile_path, base_name,
                                                                generated_path, object_baseline, taken_names)
            continue
        if not merge_mode:
            if not env_specific_profile_path:
                if generated_path:
                    logger.info(f"Replacing {common_msg}, the profile the run generated is the only override of "
                                f"'{profile_key}' left")
                    override_profile_map[profile_key] = assemble_profile(profile_key, generated_path,
                                                                         extractNameFromFile(generated_path),
                                                                         generated_path, object_baseline, taken_names)
                continue
            if not generated_path:
                logger.info(f"Replacing {common_msg}")
                override_profile_map[profile_key] = env_specific_profile_path
                continue
            logger.info(f"Replacing {common_msg} and applying the profile the run generated on top of it")
            override_profile_map[profile_key] = assemble_profile(profile_key, env_specific_profile_path,
                                                                extractNameFromFile(generated_path), generated_path,
                                                                object_baseline, taken_names)
            continue
        own_profile = (f"environment specific profile '{env_specific_profile_path}'" if env_specific_profile_path
                       else "no environment specific profile")
        logger.info(f"Profile key '{profile_key}' has template profile '{template_profile_file_path}' and {own_profile}")
        template_profile_yaml = current_env_instance_store().get(template_profile_file_path)
        if env_specific_profile_path:
            logger.info(f"Joining {common_msg}")
            merge_resource_profiles(template_profile_yaml, current_env_instance_store().get(env_specific_profile_path),
                                    extractNameFromFile(env_specific_profile_path), object_baseline)
        if generated_path:
            apply_generated_override(profile_key, template_profile_yaml, generated_path, object_baseline)
    return override_profile_map


def has_valid_profile_name(content: dict) -> bool:
    profile = content.get("profile")
    return isinstance(profile, (dict, YamlBacked)) and bool(profile.get("name"))


def set_object_profile_field(file_path, field, value):
    data = current_env_instance_store().get(file_path)
    if data.get("profile") is None:
        data["profile"] = get_empty_yaml()
    elif data["profile"].get(field) == value:
        return
    set_nested_yaml_attribute(data, f"profile.{field}", value)
