from envgenehelper import *

from env_template.process_env_template import process_env_template
from render_config_env import EnvGenerator


def write_app_reg_defs(base_dir: str, render_dir: str, env_dir: str, placement_mode: str) -> None:
    if placement_mode not in ("root", "dual"):
        raise ValueError(f"Unknown 'app_reg_defs_placement' value: {placement_mode}. Expected 'root' or 'dual'")

    for dir_name in ["AppDefs", "RegDefs"]:
        src = Path(render_dir) / dir_name
        env_dst = Path(env_dir) / dir_name
        root_dst = Path(base_dir) / dir_name.lower()
        
        if not src.exists():
            continue
        
        shutil.copytree(src, root_dst, dirs_exist_ok=True)
        if env_dst.exists():
            shutil.rmtree(env_dst)
        if placement_mode == "dual":
            shutil.copytree(root_dst, env_dst)


def override_app_reg_defs(base_dir: str, env_dir: str, placement_mode: str) -> None:
    config_dir = Path(base_dir) / "configuration"
    
    for dir_name in ["AppDefs", "RegDefs"]:
        p = Path(config_dir) / dir_name.lower()
        app_reg_defs = findAllYamlsInDir(p, recursively=False)
        for app_reg_def in app_reg_defs:
            shutil.copy(app_reg_def, f"{base_dir}/{dir_name.lower()}")
            if placement_mode == "dual":
                shutil.copy(app_reg_def, f"{env_dir}/{dir_name}")


def main():
    template_version = process_env_template()

    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    instances_dir = getenv_with_error("INSTANCES_DIR")

    output_dir = f"{base_dir}/environments"
    render_dir = f"/tmp/render/{env_name}"
    templates_dirs = get_template_dirs()

    env_dir = get_env_instances_dir(env_name, cluster_name, instances_dir)
    cloud_passport_file_path = find_cloud_passport_definition(env_dir, instances_dir)

    render_context_vars = {
        "cluster_name": cluster_name,
        "output_dir": output_dir,
        "current_env_dir": render_dir,
        "templates_dirs": templates_dirs,
        "cloud_passport_file_path": cloud_passport_file_path,
        "env_instances_dir": env_dir
    }
    config = get_envgene_config_yaml()
    placement_mode = config.get("app_reg_defs_placement", "dual").lower()

    render_context = EnvGenerator()
    render_context.process_app_reg_defs(env_name, render_context_vars)
    
    write_app_reg_defs(base_dir, render_dir, env_dir, placement_mode)
    override_app_reg_defs(base_dir, env_dir, placement_mode)
    update_generated_versions(env_dir, BUILD_ENV_TAG, template_version[NamespaceRole.COMMON])


if __name__ == '__main__':
    main()