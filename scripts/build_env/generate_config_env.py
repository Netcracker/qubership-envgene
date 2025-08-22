import os
from pathlib import Path

from deepmerge import always_merger
from envgenehelper import logger, openYaml, readYaml, dumpYamlToStr, writeYamlToFile, openFileAsString
from jinja2 import Environment, FileSystemLoader, Template


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
    j2env = Environment(loader=FileSystemLoader(str(templates_dir)))
    template = j2env.get_template("env_config.yml.j2")
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


def render_from_file_to_file(src_template_path, target_file_path, context):
    template = openFileAsString(src_template_path)
    rendered = Template(template).render(context)
    writeYamlToFile(target_file_path, readYaml(rendered))


def render_from_file_to_obj(src_template_path, context) -> dict:
    template = openFileAsString(src_template_path)
    rendered = Template(template).render(context)
    return readYaml(rendered)


# def render_from_str_to_file(template_str, target_file_path, context):
#     rendered = Template(template_str).render(context)
#     writeYamlToFile(target_file_path, readYaml(rendered))


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
        ns_dir = Path(f'{current_env_dir}/"Namespaces"/{ns_template_name}')
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


def generate_config_env(envvars: dict):
    context = {}
    env_vars = dict(os.environ)
    context["env_vars"] = {
        "CI_COMMIT_TAG": env_vars.get("CI_COMMIT_TAG"),
        "CI_COMMIT_REF_NAME": env_vars.get("CI_COMMIT_REF_NAME"),
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
