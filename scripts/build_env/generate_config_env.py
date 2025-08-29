import base64
import os
import re
import time
from pathlib import Path

from deepmerge import always_merger
from envgenehelper import logger, openYaml, readYaml, dumpYamlToStr, writeYamlToFile, openFileAsString, copy_path
from jinja2 import Environment, FileSystemLoader, Template, ChainableUndefined, TemplateError, BaseLoader


def create_jinja_env(templates_dir: str = "") -> Environment:
    loader = FileSystemLoader(templates_dir) if templates_dir else BaseLoader()
    env = Environment(
        loader=loader,
        undefined=ChainableUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def get_inventory(context: dict) -> dict:
    inventory_path = Path(context["env_instances_dir"]) / "Inventory" / "env_definition.yml"
    env_definition = openYaml(filePath=inventory_path, safe_load=True)
    logger.info("env_definition = %s", env_definition)
    return env_definition


def get_cloud_passport(context: dict) -> dict | None:
    cloud_passport_file_path = context.get("cloud_passport_file_path", "").strip()
    if cloud_passport_file_path:
        cloud_passport_path = Path(cloud_passport_file_path)
        cloud_passport = openYaml(filePath=cloud_passport_path, safe_load=True)
        logger.info("cloud_passport = %s", cloud_passport)
        return cloud_passport


def generate_config(context: dict) -> dict:
    # cloud_passport = context.get("cloud_passport")
    # if cloud_passport:
    #     context["cloud_passport"] = safe_yaml.dump(cloud_passport)
    # env_template = context["env_definition"].get("envTemplate")
    # if env_template:
    #     env_specific_paramsets = env_template.get("envSpecificParamsets")
    #     if env_specific_paramsets:
    #         # TODO may be delete dump = to_nice_yaml
    #         env_specific_paramsets = safe_yaml.dump(env_specific_paramsets)
    #         env_template["envSpecificParamsets"] = env_specific_paramsets
    #     additional_template_variables = env_template.get("additionalTemplateVariables")
    #     if additional_template_variables:
    #         additional_template_variables = safe_yaml.dump(additional_template_variables)
    #         env_template["envSpecificParamsets"] = additional_template_variables
    #     context["env_definition"]["envTemplate"] = env_template
    templates_dir = Path(__file__).parent / "templates"
    template = create_jinja_env(str(templates_dir)).get_template("env_config.yml.j2")
    config = readYaml(text=template.render(context), safe_load=True)
    logger.info("config = %s", config)
    return config


def load_env_template(context: dict):
    env_template_path_stem = f'{context["templates_dir"]}/env_templates/{context["current_env"]["env_template"]}'
    env_template_path = next(iter(find_all_yaml_files_by_stem(env_template_path_stem)), None)
    if not env_template_path.exists():
        raise ValueError(f'Template descriptor was not found in {env_template_path}')

    env_template = openYaml(filePath=env_template_path, safe_load=True)
    logger.info("env_template = %s", env_template)
    return env_template


def find_all_yaml_files_by_stem(path: str):
    file_paths = []
    for ext in ["yaml", "yml"]:
        file_path = Path(f"{path}.{ext}")
        if file_path.exists():
            file_paths.append(file_path)
    return file_paths


def validate_applications(sd_config: dict):
    applications = sd_config.get("applications", [])

    for app in applications:
        version = app.get("version")
        deploy_postfix = app.get("deployPostfix")

        if "version" not in app:
            raise ValueError(f"Missing 'version' in application: {app}")
        if "deployPostfix" not in app:
            raise ValueError(f"Missing 'deployPostfix' in application: {app}")
        if not isinstance(version, str):
            raise ValueError(f"'version' must be string in application: {app}")
        if not isinstance(deploy_postfix, str):
            raise ValueError(f"'deployPostfix' must be string in application: {app}")

        logger.info("Valid application: %s", app)


def generate_solution_structure(context: dict):
    sd_path_stem = f'{context["current_env_dir"]}/Inventory/solution-descriptor/sd'
    sd_path = next(iter(find_all_yaml_files_by_stem(sd_path_stem)), None)
    if sd_path:
        context["sd_file_path"] = str(sd_path)
        sd_config = openYaml(filePath=sd_path, safe_load=True)
        context["sd_config"] = sd_config
        if "applications" not in sd_config:
            raise ValueError("Missing 'applications' key in root")
        validate_applications(context["sd_config"])

        namespaces = context["current_env_template"].get("namespaces")
        namespace_template_paths_raw = {}
        if namespaces:
            namespace_template_paths_raw = [ns["template_path"] for ns in namespaces]
            context["namespace_template_paths"] = namespace_template_paths_raw

        namespace_template_paths = []
        for ns_template in namespace_template_paths_raw:
            namespace_template_paths.append(Template(ns_template).render(context))
        logger.info("List of found namespace template: %s", namespace_template_paths)

        postfix_template_map = {}
        for path in namespace_template_paths:
            postfix = os.path.basename(path).split('.')[0]  # get base name(deploy postfix) without extensions
            postfix_template_map[postfix] = path

        solution_structure = {}
        for app in sd_config["applications"]:
            app_version = app["version"]
            app_name, version = app_version.split(":", 1)
            postfix = app["deployPostfix"]

            ns_template_path = postfix_template_map.get(postfix)
            ns_name = None
            if ns_template_path:
                rendered_ns = render_from_file_to_obj(ns_template_path, context)
                ns_name = rendered_ns.get("name")

            small_dict = {
                app_name: {
                    postfix: {
                        "version": version,
                        "namespace": ns_name
                    }
                }
            }
            always_merger.merge(solution_structure, small_dict)

        logger.info("Rendered solution_structure: %s", solution_structure)
        always_merger.merge(context["current_env"], {"solution_structure": solution_structure})


def render_from_file_to_file(src_template_path: str, target_file_path: str, context):
    template = openFileAsString(src_template_path)
    rendered = create_jinja_env().from_string(template).render(context)
    writeYamlToFile(target_file_path, readYaml(rendered))


def render_from_file_to_obj(src_template_path, context) -> dict:
    template = openFileAsString(src_template_path)
    rendered = Template(template).render(context)
    return readYaml(rendered)


def generate_tenant_file(context: dict):
    logger.info("Generate Tenant yaml for %s", context["tenant"])
    tenant_file = Path(f'{context["current_env_dir"]}/tenant.yml')
    tenant_tmpl_path = context["current_env_template"]["tenant"]
    render_from_file_to_file(Template(tenant_tmpl_path).render(context), tenant_file, context)


def generate_override_tmpl_by_type(template_override, template_path: Path, name):
    if template_override:
        logger.info("Generate override %s yaml for %s", template_path.stem, name)
        rendered_override = dumpYamlToStr(template_override)
        writeYamlToFile(filePath=template_path, contents=rendered_override)


def generate_cloud_file(context: dict):
    cloud = calculate_cloud_name(context)
    logger.info("Generate Cloud yaml for cloud %s", cloud)
    cloud_template = context["current_env_template"]["cloud"]
    current_env_dir = context["current_env_dir"]
    cloud_file = Path(f'{current_env_dir}/cloud.yml')
    is_template_override = isinstance(cloud_template, dict)
    if is_template_override:
        logger.info("Generate Cloud yaml for cloud %s using cloud.template_path value", cloud)
        cloud_tmpl_path = cloud_template["template_path"]
        render_from_file_to_file(Template(cloud_tmpl_path).render(context), cloud_file, context)

        template_override = cloud_template.get("template_override")
        generate_override_tmpl_by_type(template_override=template_override,
                                       template_path=Path(f'{current_env_dir}/"cloud.yml_override'),
                                       name=cloud)
    else:
        logger.info("Generate Cloud yaml for cloud %s", cloud)
        render_from_file_to_file(Template(cloud_template).render(context), cloud_file, context)


def generate_namespace_file(context: dict):
    namespaces = context["current_env_template"]["namespaces"]
    for ns in namespaces:
        ns_template_path = Template(ns["template_path"]).render(context)
        ns_template_name = Path(ns_template_path).name.replace(".yml.j2", "").replace(".yaml.j2", "")
        logger.info("Generate Namespace yaml for %s", ns_template_name)
        current_env_dir = context["current_env_dir"]
        ns_dir = Path(f'{current_env_dir}/Namespaces/{ns_template_name}')
        namespace_file = ns_dir / "namespace.yml"
        render_from_file_to_file(ns_template_path, namespace_file, context)

        generate_override_tmpl_by_type(template_override=ns.get("template_override"),
                                       template_path=Path(
                                           f'{current_env_dir}/Namespaces/{ns_dir}/namespace.yml_override'),
                                       name=ns_template_name)


def calculate_cloud_name(context):
    inv = context["env_definition"]["inventory"]
    cluster_name = context["cluster_name"]
    candidates = [
        inv.get("cloudName"),
        inv.get("passportCloudName", "").replace("-", "_") if inv.get("passportCloudName") else "",
        inv.get("cloudPassport", "").replace("-", "_") if inv.get("cloudPassport") else "",
        inv.get("environmentName", "").replace("-", "_"),
        f"{cluster_name}_{inv.get('environmentName', '')}".replace("-", "_")
        if cluster_name and inv.get("environmentName") else ""
    ]

    return next((c for c in candidates if c), "")


def get_template_name(template_path: Path) -> str:
    return (
        template_path.name
        .replace(".yml.j2", "")
        .replace(".yaml.j2", "")
    )


# def generate_profile(profile, context):
#     current_env_dir = context["current_env_dir"]
#     template_path = Path(profile["template_path"])
#     template_name = get_template_name(template_path)
#     logger.info("Generate profile yaml for %s", template_path)
#     profiles_dir = Path(current_env_dir) / "Profiles"
#     profiles_dir.mkdir(parents=True, exist_ok=True)
#     profile_path = profiles_dir / f"{template_name}.yml"
#     render_from_file_to_file(Template(str(template_path)).render(context), profile_path, context)


def generate_composite_structure(composite_structure, context):
    logger.info("Generate Composite Structure yaml for %s", composite_structure)
    current_env_dir = context["current_env_dir"]
    cs_file = Path(current_env_dir) / "composite_structure.yml"
    cs_file.parent.mkdir(parents=True, exist_ok=True)
    render_from_file_to_file(Template(composite_structure).render(context), cs_file, context)


def generate_paramset_templates(context):
    render_dir = Path(context["render_parameters_dir"]).resolve()
    patterns = ["*.yml.j2", "*.yaml.j2"]

    paramset_templates = []
    for pattern in patterns:
        paramset_templates.extend(render_dir.rglob(pattern))
    logger.info("Total parameter set templates list found: %s", paramset_templates)

    for template_path in paramset_templates:
        template_name = get_template_name(template_path)
        target_path = Path(str(template_path).replace(".yml.j2", ".yml").replace(".yaml.j2", ".yml"))

        try:
            logger.info("Try to render paramset %s", template_name)
            render_from_file_to_file(Template(str(template_path)).render(context), target_path, context)
            logger.info("Successfully generated paramset: %s", template_name)
            if template_path.exists():
                template_path.unlink()
        except TemplateError as e:
            logger.warning("Skipped paramset %s - template variables not available in current environment",
                           template_name, e)
            if target_path.exists():
                target_path.unlink()


def process_external_defs(context):
    logger.info("APP_REG_DEFS_JOB variable is set, "
                "Application and Registry definitions from corresponding job will be used for the Environment")


def find_templates(templates_dir: str, def_type: str) -> list[Path]:
    search_path = Path(templates_dir) / def_type
    if not search_path.exists():
        logger.info(f"Directory with templates for {def_type} not found: {search_path}")
        return []

    patterns = ["*.yaml.j2", "*.yml.j2", "*.j2", "*.yaml", "*.yml"]
    templates = []

    for pattern in patterns:
        for f in search_path.rglob(pattern):
            if f.is_file():
                templates.append(f)

    logger.info(f"{def_type.capitalize()} Found: {len(templates)}")
    return templates


def ensure_directory(path: Path, mode: int = 0o755):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
    else:
        logger.info(f"Directory already exists: {path}")
    path.chmod(mode)
    logger.info(f"Set permissions {oct(mode)} for {path}")


def render_app_defs(context):
    for def_tmpl_path in context.get("appdef_templates"):
        app_def_str = openFileAsString(def_tmpl_path)
        matches = re.findall(
            r'^\s*(name|artifactId|groupId):\s*"([^"]+)"',
            app_def_str,
            flags=re.MULTILINE,
        )
        appdef_meta = dict(matches)
        ensure_valid_fields(appdef_meta, ["artifactId", "groupId", "name"])
        group_id = appdef_meta["groupId"]
        artifact_id = appdef_meta["artifactId"]
        context.update({
            "app_lookup_key": f"{group_id}:{artifact_id}",
            "groupId": group_id,
            "artifactId": artifact_id,
        })
        app_def_trg_path = f"{context['current_env_dir']}/AppDefs/{appdef_meta.name}.yml"
        render_from_file_to_file(def_tmpl_path, app_def_trg_path, context)


def render_reg_defs(context):
    for def_tmpl_path in context.get("regdef_templates"):
        reg_def_str = openFileAsString(def_tmpl_path)
        matches = re.findall(
            r'^\s*(name):\s*"([^"]+)"',
            reg_def_str,
            flags=re.MULTILINE,
        )
        regdef_meta = dict(matches)
        ensure_valid_fields(regdef_meta, ["name"])
        reg_def_trg_path = f"{context['current_env_dir']}/RegDefs/{regdef_meta["name"]}.yml"
        render_from_file_to_file(def_tmpl_path, reg_def_trg_path, context)


def ensure_required_keys(context, required: list[str]):
    missing = [var for var in required if var not in context]
    if missing:
        raise ValueError(f"Required variables: {', '.join(required)}. "f"Not found: {', '.join(missing)}")
    logger.info("All required %s variables are defined", required)


def ensure_valid_fields(context, fields: list[str]):
    invalid = []
    for field in fields:
        value = context.get(field)
        if not value:
            invalid.append(f"{field}={value!r}")

    if invalid:
        raise ValueError(
            f"Invalid or empty fields found: {', '.join(invalid)}. "f"Required fields: {', '.join(fields)}")
    logger.info("All required fields are present and non-empty: %s", ", ".join(fields))


def process_app_reg_defs(context):
    current_env_dir = context["current_env_dir"]
    use_external_defs = bool(context.get("APP_REG_DEFS_JOB"))
    context["use_external_defs"] = use_external_defs
    if use_external_defs:
        process_external_defs(context)
    else:
        templates_dir = context["templates_dir"]
        appdef_templates = find_templates(templates_dir, "appdefs")
        regdef_templates = find_templates(templates_dir, "regdefs")
        context["appdef_templates"] = appdef_templates
        context["regdef_templates"] = regdef_templates

        ensure_directory(Path(current_env_dir).joinpath("AppDefs"))
        ensure_directory(Path(current_env_dir).joinpath("RegDefs"))

        output_dir = Path(context["output_dir"])
        cluster_name = context["cluster_name"]
        config_file_name_yaml = Path("configuration") / "appregdef_config.yaml"
        config_file_name_yml = Path("configuration") / "appregdef_config.yml"

        potential_config_files = [
            output_dir / cluster_name / config_file_name_yaml,
            output_dir / cluster_name / config_file_name_yml,
            output_dir.parent / config_file_name_yaml,
            output_dir.parent / config_file_name_yml,
        ]
        appregdef_config_paths = [f for f in potential_config_files if f.exists()]
        if appregdef_config_paths:
            appregdef_config = {}
            appregdef_config_path = appregdef_config_paths[0]
            try:
                appregdef_config = openYaml(appregdef_config_path)
                logger.info(f"Overrides applications registries definitions config found at: {appregdef_config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config at: {appregdef_config_path}. Error: {e}")

            context["appdefs"]["overrides"] = appregdef_config.get("appdefs", {}).get("overrides", {})
            context["regdefs"]["overrides"] = appregdef_config.get("regdefs", {}).get("overrides", {})
            render_app_defs(context)
            render_reg_defs(context)


def generate_config_env(envvars: dict):
    context = {}
    env_vars = dict(os.environ)
    context["env_vars"] = {
        "CI_COMMIT_TAG": env_vars.get("CI_COMMIT_TAG"),
        "CI_COMMIT_REF_NAME": env_vars.get("CI_COMMIT_REF_NAME"),
        "APP_REG_DEFS_JOB": env_vars.get("APP_REG_DEFS_JOB")
    }
    context.update(envvars)
    context["env_definition"] = get_inventory(context)

    cloud_passport = get_cloud_passport(context)
    if cloud_passport:
        context["cloud_passport"] = cloud_passport

    context["config"] = generate_config(context)
    current_env = context["config"]["environment"]
    context["current_env"] = current_env
    context["cloud"] = calculate_cloud_name(context)
    context["tenant"] = current_env.get("tenant", '')
    context["deployer"] = current_env.get('deployer', '')
    logger.info("current_env = %s", context["current_env"])

    context["ND_CMDB_CONFIG_REF"] = os.environ.get('CI_COMMIT_SHORT_SHA', 'No SHA')
    context["ND_CMDB_CONFIG_REF_NAME"] = os.environ.get('CI_COMMIT_REF_NAME', 'No SHA')
    context["ND_CMDB_CONFIG_TAG"] = os.environ.get('CI_COMMIT_TAG', 'No Ref Name')
    context["ND_CDMB_REPOSITORY_URL"] = os.environ.get('CI_REPOSITORY_URL', 'No Ref URL')
    env_template = context.get("env_template")
    if env_template:
        context["ND_CMDB_ENV_TEMPLATE"] = env_template
    else:
        context["ND_CMDB_ENV_TEMPLATE"] = context["current_env"]["env_template"]

    context["current_env_dir"] = f'{context["render_dir"]}/{context["env"]}'

    context["current_env_template"] = load_env_template(context)

    generate_solution_structure(context)
    generate_tenant_file(context)
    generate_cloud_file(context)
    generate_namespace_file(context)

    current_env_template = context["current_env_template"]
    # resource_profiles = current_env_template.get("resourceProfiles")
    # if resource_profiles:
    #     for profile in resource_profiles:
    #         generate_profile(profile, context)

    composite_structure = current_env_template.get("composite_structure")
    if composite_structure:
        generate_composite_structure(composite_structure, context)

    env_specific_schema = current_env_template.get("envSpecificSchema")
    current_env_dir = context["current_env_dir"]
    if env_specific_schema:
        schema_target_path = current_env_dir + "/env-specific-schema.yml"
        copy_path(source_path=env_specific_schema, target_path=schema_target_path)
    generate_paramset_templates(context)

    ensure_required_keys(context,
                         required=["templates_dir", "env_instances_dir", "cluster_name", "current_env_dir"])
    process_app_reg_defs(context)
