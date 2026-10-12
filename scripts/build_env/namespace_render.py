from build_env.render_config_env import build_render_context_vars, env_generator
from envgenehelper import Path, get_current_env_dir_from_env_vars, getenv_with_error, writeYamlToFile

NAMESPACE_MAP_FILE = "namespace-map.yml"


def compute_namespace_map() -> dict:
    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
    base_dir = getenv_with_error("CI_PROJECT_DIR")
    env_dir = str(get_current_env_dir_from_env_vars())

    generator = env_generator()
    render_context_vars = generator.render_context_vars or build_render_context_vars(
        env_name, cluster_name, env_dir, base_dir)
    namespace_by_deploy_postfix = generator.render_namespaces_for_map(env_name, render_context_vars)

    namespace_map_path = Path(env_dir) / "Inventory" / NAMESPACE_MAP_FILE
    namespace_map_path.parent.mkdir(parents=True, exist_ok=True)
    writeYamlToFile(namespace_map_path, namespace_by_deploy_postfix)
    return namespace_by_deploy_postfix
