from build_env.render_config_env import EnvGenerator, build_minimal_render_context
from envgenehelper import *

NAMESPACE_MAP_FILE = "namespace-map.yml"


def compute_namespace_map() -> dict:
    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
    base_dir = getenv_with_error("CI_PROJECT_DIR")
    env_dir = str(get_current_env_dir_from_env_vars())

    render_context_vars = build_minimal_render_context(env_name, cluster_name, env_dir, base_dir)
    namespace_by_deploy_postfix = EnvGenerator().render_namespaces_for_map(env_name, render_context_vars)

    namespace_map_path = Path(env_dir) / "Inventory" / NAMESPACE_MAP_FILE
    namespace_map_path.parent.mkdir(parents=True, exist_ok=True)
    writeYamlToFile(namespace_map_path, namespace_by_deploy_postfix)
    return namespace_by_deploy_postfix
