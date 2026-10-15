from time import time as _diag_now

from envgenehelper import NamespaceRole, Path, check_dir_exists, check_environment_is_valid_or_fail, cleanup_targets, current_env_instance_store, deleteFile, delete_dir, fill_missing_environment_name, find_cloud_passport_definition, getAbsPath, getEnvDefinition, get_env_instances_dir, get_parent_dir_for_dir, get_schema_dir, get_template_dirs, getenv_with_error, logger, openYaml, render_workspace_dir
from envgenehelper.deployer import *
from envgene_shared.utils.yaml_utils import val_diag

from build_env.build_env import build_env, copy_instance_paramsets, copy_template_paramsets, \
    process_additional_template_parameters
from cloud_passport.cloud_passport import update_env_definition_with_cloud_name
from build_env.create_credentials import create_credentials
from build_env.render_config_env import EnvGenerator
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


def load_env_inputs(env_name, source_env_dir, all_instances_dir) -> dict:
    env_instance_store = current_env_instance_store()
    env_definition = getEnvDefinition(source_env_dir)
    process_additional_template_parameters(env_definition, source_env_dir, all_instances_dir)
    update_env_definition_with_cloud_name(env_definition, source_env_dir, all_instances_dir)
    fill_missing_environment_name(env_definition, env_name)
    source_creds_path = Path(source_env_dir) / CREDENTIALS_FILE
    if source_creds_path.is_file():
        env_instance_store.put(source_creds_path, openYaml(source_creds_path))
    return env_definition


def build_environment(env_name, cluster_name, templates_dirs, source_env_dir, all_instances_dir, work_dir):
    _be_t0 = _diag_now()
    # defining folders that will be used during generation
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    render_parameters_dir = str(render_workspace_dir(base_dir) / "parameters")
    template_profiles_dir = str(Path(templates_dirs[NamespaceRole.COMMON]) / "resource_profiles")

    # preparing folders for generation
    _t = _diag_now()
    cleanup_resulting_dir(source_env_dir)
    copy_paramsets_to_render_workspace(source_env_dir, templates_dirs, render_parameters_dir)
    logger.debug(f"[diag] setup: cleanup+copy_paramsets_to_render_workspace in {(_diag_now() - _t) * 1000:.1f}ms")
    _t = _diag_now()
    env_definition = load_env_inputs(env_name, source_env_dir, all_instances_dir)
    logger.debug(f"[diag] setup: load_env_inputs in {(_diag_now() - _t) * 1000:.1f}ms")
    # get deployer parameters
    _t = _diag_now()
    cmdb_url, _, _ = get_deployer_config()
    logger.debug(f"[diag] setup: get_deployer_config in {(_diag_now() - _t) * 1000:.1f}ms")
    # perform rendering with Jinja2
    current_env = {
        "name": env_name,  # Always use folder name for consistency
        "environmentName": env_definition["inventory"]["environmentName"]
    }

    logger.debug(
        f"Created environment context: name='{current_env['name']}', environmentName='{current_env['environmentName']}'")

    envvars = {}
    envvars["env"] = env_name  # Keep as string for file paths
    envvars["current_env"] = current_env  # Object for Jinja2 templates that need current_env.environmentName
    envvars["cluster_name"] = cluster_name
    envvars["templates_dirs"] = templates_dirs
    envvars["templates_dir"] = templates_dirs.get(NamespaceRole.COMMON, '')
    envvars["current_env_dir"] = getAbsPath(source_env_dir)
    envvars["render_parameters_dir"] = getAbsPath(render_parameters_dir)
    envvars["cloud_passport_file_path"] = find_cloud_passport_definition(source_env_dir, all_instances_dir,
                                                                         env_definition)
    envvars["cmdb_url"] = cmdb_url
    envvars["output_dir"] = all_instances_dir
    envvars["template_profiles_dir"] = template_profiles_dir
    envvars["work_dir"] = str(work_dir)
    envvars["env_definition"] = env_definition
    render_context = EnvGenerator()
    _t = _diag_now()
    render_context.render_config_env(env_name, envvars)
    logger.debug(f"[diag] setup: render_config_env (paramset/namespaces/appregdef pre-render) in {(_diag_now() - _t) * 1000:.1f}ms")
    _t = _diag_now()
    validate_env_specific_override_keys(source_env_dir, env_definition)
    env_specific_resource_profile_map = get_env_specific_resource_profiles(
        source_env_dir, all_instances_dir, get_schema_dir() / "resource-profile.schema.json", env_definition)
    logger.debug(f"[diag] setup: env_specific_overrides+resource_profiles in {(_diag_now() - _t) * 1000:.1f}ms")
    _t = _diag_now()
    build_env(source_env_dir, env_definition, render_parameters_dir, template_profiles_dir,
              env_specific_resource_profile_map, all_instances_dir, render_context, templates_dirs, render_context.is_external_cred_env)
    logger.debug(f"[diag] setup: build_env in {(_diag_now() - _t) * 1000:.1f}ms")
    _t = _diag_now()
    create_credentials(source_env_dir, all_instances_dir, render_context.is_external_cred_env, env_definition)
    logger.debug(f"[diag] setup: create_credentials in {(_diag_now() - _t) * 1000:.1f}ms")
    logger.info(f"External cred env is set as {render_context.is_external_cred_env}")
    logger.debug(f"[diag] setup: build_environment total in {(_diag_now() - _be_t0) * 1000:.1f}ms")
    logger.debug(f"[diag] validation: {val_diag['calls']} calls {val_diag['ms']:.1f}ms")
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
