from pathlib import Path

from envgenehelper import getenv_with_error, get_env_instances_dir, find_cloud_passport_definition, get_template_dirs, get_envgene_config_yaml

from build_env.appregdef_render import override_app_reg_defs, write_app_reg_defs
from build_env.env_template.process_env_template import process_env_template
from build_env.namespace_map import NAMESPACE_MAP_FILE, compute_namespace_map, write_namespace_map
from build_env.render_config_env import EnvGenerator


def run_app_reg_def_process() -> None:
    base_dir = getenv_with_error("CI_PROJECT_DIR")
    process_env_template()

    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
    output_dir = f"{base_dir}/environments"
    render_dir = f"/tmp/render/{env_name}"
    templates_dirs = get_template_dirs()
    env_dir = get_env_instances_dir(env_name, cluster_name, output_dir)
    cloud_passport_file_path = find_cloud_passport_definition(env_dir, output_dir)

    render_context_vars = {
        "cluster_name": cluster_name,
        "output_dir": output_dir,
        "current_env_dir": render_dir,
        "render_dir": render_dir,
        "env": env_name,
        "templates_dirs": templates_dirs,
        "cloud_passport_file_path": cloud_passport_file_path,
        "env_instances_dir": env_dir,
    }

    render_context = EnvGenerator()
    render_context.process_app_reg_def_process(env_name, render_context_vars)

    namespace_map = compute_namespace_map(Path(render_dir) / "Namespaces")
    namespace_map_path = Path(env_dir) / "Inventory" / NAMESPACE_MAP_FILE
    write_namespace_map(namespace_map, namespace_map_path)

    placement_mode = get_envgene_config_yaml().get("app_reg_defs_placement", "dual").lower()
    write_app_reg_defs(base_dir, render_dir, env_dir, placement_mode)
    override_app_reg_defs(base_dir, env_dir, placement_mode)
