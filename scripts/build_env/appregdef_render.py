import shutil
import yaml
from pathlib import Path

from envgenehelper import getenv_with_error, get_template_dirs, get_env_instances_dir, find_cloud_passport_definition, \
    update_generated_versions, NamespaceRole, BUILD_ENV_TAG

from build_env.env_template.process_env_template import process_env_template
from build_env.render_config_env import EnvGenerator


def run_appregdef_render():
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    template_version = process_env_template()

    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
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

    render_context = EnvGenerator()
    render_context.process_app_reg_defs(env_name, render_context_vars)

    config_yaml = Path(base_dir) / "configuration" / "config.yml"
    app_reg_defs_placement = "dual"
    if config_yaml.exists():
        with open(config_yaml, "r") as f:
            cfg = yaml.safe_load(f) or {}
            app_reg_defs_placement = cfg.get("app_reg_defs_placement", "dual")

    for category, dir_name in [("appdefs", "AppDefs"), ("regdefs", "RegDefs")]:
        src_tmp = Path(render_dir) / dir_name
        user_provided_dir = Path(base_dir) / "configuration" / category
        
        if user_provided_dir.exists():
            src_tmp.mkdir(parents=True, exist_ok=True)
            for ext in ["*.yml", "*.yaml"]:
                for user_file in user_provided_dir.glob(ext):
                    if user_file.is_file():
                        shutil.copy2(user_file, src_tmp / user_file.name)

        root_dst = Path(base_dir) / category
        if src_tmp.exists():
            root_dst.mkdir(parents=True, exist_ok=True)
            for file in src_tmp.glob("*"):
                if file.is_file():
                    shutil.copy2(file, root_dst / file.name)

        env_dst = Path(env_dir) / dir_name
        if app_reg_defs_placement == "root":
            if env_dst.exists():
                shutil.rmtree(env_dst)
        else:
            if src_tmp.exists():
                shutil.copytree(src_tmp, env_dst, dirs_exist_ok=True)

    update_generated_versions(env_dir, BUILD_ENV_TAG, template_version[NamespaceRole.COMMON])
