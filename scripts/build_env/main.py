from envgenehelper import NamespaceRole, Path, check_dir_exists, check_environment_is_valid_or_fail, cleanup_targets, current_env_instance_store, deleteFile, delete_dir, get_env_instances_dir, get_parent_dir_for_dir, get_schema_dir, get_template_dirs, getenv_with_error, logger, openYaml, render_workspace_dir
from envgenehelper.deployer import *

from build_env.build_env import build_env, copy_instance_paramsets, copy_template_paramsets
from build_env.create_credentials import create_credentials
from build_env.render_config_env import build_render_context_vars, env_generator
from build_env.env_specific_overrides import validate_env_specific_override_keys
from build_env.resource_profiles import get_env_specific_resource_profiles

CREDENTIALS_FILE = Path("Credentials") / "credentials.yml"


def copy_paramsets_to_render_workspace(source_env_dir, templates_dirs, render_parameters_dir):
    # copying parameters from templates and instances
    if check_dir_exists(render_parameters_dir):
        logger.info(f"Using common and instance paramsets copied by regdefv2_adapter to {render_parameters_dir}, "
                    f"adding origin/peer template paramsets")
        bg_templates_dirs = {role: path for role, path in templates_dirs.items() if role != NamespaceRole.COMMON}
        copy_template_paramsets(bg_templates_dirs, render_parameters_dir)
    else:
        delete_dir(render_parameters_dir)
        copy_template_paramsets(templates_dirs, render_parameters_dir)
        copy_instance_paramsets(source_env_dir, render_parameters_dir)


def cleanup_resulting_dir(resulting_dir: Path):
    logger.info(f"Cleaning resulting directory: {str(resulting_dir)}")
    resulting_dir = Path(resulting_dir)
    for target in cleanup_targets:
        path = resulting_dir.joinpath(target)
        if path.is_dir():
            logger.info(f"Removing directory: {path}")
            delete_dir(path)
        elif path.is_file():
            logger.info(f"Removing file: {path}")
            deleteFile(path)


def load_env_credentials(source_env_dir):
    source_creds_path = Path(source_env_dir) / CREDENTIALS_FILE
    if source_creds_path.is_file():
        current_env_instance_store().put(source_creds_path, openYaml(source_creds_path))


def build_environment(env_name, cluster_name, templates_dirs, source_env_dir, all_instances_dir, work_dir):
    # defining folders that will be used during generation
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    render_parameters_dir = str(render_workspace_dir(base_dir) / "parameters")
    template_profiles_dir = str(Path(templates_dirs[NamespaceRole.COMMON]) / "resource_profiles")

    # preparing folders for generation
    copy_paramsets_to_render_workspace(source_env_dir, templates_dirs, render_parameters_dir)
    load_env_credentials(source_env_dir)
    render_context = env_generator()
    envvars = render_context.render_context_vars or build_render_context_vars(
        env_name, cluster_name, source_env_dir, base_dir, templates_dirs)
    env_definition = envvars["env_definition"]
    render_context.render_config_env(env_name, envvars)
    validate_env_specific_override_keys(source_env_dir, env_definition)
    env_specific_resource_profile_map = get_env_specific_resource_profiles(
        source_env_dir, all_instances_dir, get_schema_dir() / "resource-profile.schema.json", env_definition)
    build_env(source_env_dir, env_definition, render_parameters_dir, template_profiles_dir,
              env_specific_resource_profile_map, all_instances_dir, render_context, templates_dirs, render_context.is_external_cred_env)
    create_credentials(source_env_dir, all_instances_dir, render_context.is_external_cred_env, env_definition)
    logger.info(f"External cred env is set as {render_context.is_external_cred_env}")
    return source_env_dir, render_context.is_external_cred_env


def render_environment(env_name, cluster_name, templates_dirs, all_instances_dir, work_dir):
    logger.info(f'env: {env_name}')
    logger.info(f'cluster_name: {cluster_name}')
    logger.info(f'templates_dirs: {templates_dirs}')
    logger.info(f'instances_dir: {all_instances_dir}')
    logger.info(f'work_dir: {work_dir}')

    check_environment_is_valid_or_fail(env_name, cluster_name, all_instances_dir,
                                       validate_env_definition_by_schema=True)
    env_dir = get_env_instances_dir(env_name, cluster_name, all_instances_dir)
    logger.info(f"Environment {env_name} directory is {env_dir}")

    build_environment(env_name, cluster_name, templates_dirs, env_dir, all_instances_dir, work_dir)


def run_build_environment():
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    cluster = getenv_with_error("CLUSTER_NAME")
    environment = getenv_with_error("ENVIRONMENT_NAME")
    g_template_dirs = get_template_dirs()
    g_all_instances_dir = f"{base_dir}/environments"
    g_work_dir = get_parent_dir_for_dir(g_all_instances_dir)

    render_environment(environment, cluster, g_template_dirs, g_all_instances_dir, g_work_dir)
