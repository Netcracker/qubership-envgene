from build_env.env_template.process_env_template import process_env_template
from build_env.render_config_env import EnvGenerator, build_minimal_render_context
from envgenehelper import BUILD_ENV_TAG, NamespaceRole, Path, findAllYamlsInDir, get_current_env_dir_from_env_vars, get_envgene_config_yaml, get_schema_dir, getenv_with_error, logger, openYaml, shutil, update_generated_versions, validate_yaml_by_scheme_or_fail, writeYamlToFile
from envgenehelper.config_helper import get_regdef_schema_for_content


def write_app_reg_defs(base_dir: str, rendered_defs: dict, env_dir: str, placement_mode: str) -> None:
    if placement_mode not in ("root", "dual"):
        raise ValueError(f"Unknown 'app_reg_defs_placement' value: {placement_mode}. Expected 'root' or 'dual'")

    logger.info(f"Writing app/reg defs with placement_mode='{placement_mode}'")
    for dir_name in ["AppDefs", "RegDefs"]:
        env_dst = Path(env_dir) / dir_name
        root_dst = Path(base_dir) / dir_name.lower()

        root_dst.mkdir(parents=True, exist_ok=True)
        if env_dst.exists():
            shutil.rmtree(env_dst)
        for name, definition in rendered_defs.get(dir_name, {}).items():
            writeYamlToFile(root_dst / f"{name}.yml", definition)
            if placement_mode == "dual":
                writeYamlToFile(env_dst / f"{name}.yml", definition)


def validate_definition_override(dir_name: str, yaml_file: str) -> None:
    content = openYaml(yaml_file)
    if dir_name == "AppDefs":
        validate_yaml_by_scheme_or_fail(input_yaml_content=content,
                                        schema_file_path=get_schema_dir() / "appdef.schema.json")
    else:
        validate_yaml_by_scheme_or_fail(input_yaml_content=content,
                                        input_schema_content=get_regdef_schema_for_content(content))


def override_app_reg_defs(base_dir: str, env_dir: str, placement_mode: str) -> None:
    config_dir = Path(base_dir) / "configuration"
    logger.info(f"Applying user overrides from {config_dir} with placement_mode='{placement_mode}'")

    for dir_name in ("AppDefs", "RegDefs"):
        root_dst = Path(base_dir) / dir_name.lower()
        root_dst.mkdir(parents=True, exist_ok=True)

        if placement_mode == "dual":
            env_dst = Path(env_dir) / dir_name
            env_dst.mkdir(parents=True, exist_ok=True)

        yaml_files = findAllYamlsInDir(config_dir / dir_name.lower(), recursively=False)
        if not yaml_files:
            logger.info(f"No user overrides found in {config_dir / dir_name.lower()}, skipping")
            continue

        for yaml_file in yaml_files:
            logger.info(f"Validating override {yaml_file}")
            validate_definition_override(dir_name, yaml_file)
            shutil.copy(yaml_file, root_dst)
            logger.debug(f"Override applied: {yaml_file} -> {root_dst}")
            if placement_mode == "dual":
                shutil.copy(yaml_file, env_dst)
                logger.debug(f"Override applied: {yaml_file} -> {env_dst}")


def run_appregdef_render() -> list[str]:
    template_versions = process_env_template()
    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
    base_dir = getenv_with_error("CI_PROJECT_DIR")
    env_dir = str(get_current_env_dir_from_env_vars())

    render_context_vars = build_minimal_render_context(env_name, cluster_name, env_dir, base_dir)
    rendered_defs = EnvGenerator().render_app_reg_defs(env_name, render_context_vars)

    placement_mode = get_envgene_config_yaml().get("app_reg_defs_placement", "dual").lower()
    write_app_reg_defs(base_dir, rendered_defs, env_dir, placement_mode)
    override_app_reg_defs(base_dir, env_dir, placement_mode)
    update_generated_versions(env_dir, BUILD_ENV_TAG, template_versions[NamespaceRole.COMMON])
    return list(rendered_defs["RegDefs"])
