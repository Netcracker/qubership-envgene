import shutil

from env_template.process_env_template import process_env_template
from envgenehelper import *
from render_config_env import EnvGenerator


if __name__ == '__main__':
    template_version = process_env_template()
    
    cluster_name = getenv_with_error("CLUSTER_NAME")
    env_name = getenv_with_error("ENVIRONMENT_NAME")
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    full_env = getenv_with_error("FULL_ENV_NAME")
    instances_dir = getenv_with_error("INSTANCES_DIR")
    
    output_dir = f"{base_dir}/environments"
    render_dir = f"/tmp/render/{env_name}"
    templates_dir = f"{base_dir}/tmp/templates"
    
    env_dir = get_env_instances_dir(env_name, cluster_name, instances_dir)
    cloud_passport_file_path = find_cloud_passport_definition(env_dir, instances_dir)
    
    render_context_vars = {
        "cluster_name": cluster_name,
        "output_dir": output_dir,
        "current_env_dir": render_dir,
        "templates_dir": templates_dir,
        "cloud_passport_file_path": cloud_passport_file_path,
        "env_instances_dir": env_dir
    }
    
    render_context = EnvGenerator()
    render_context.process_app_reg_defs(env_name, render_context_vars)
    
    for dir_name in ["AppDefs", "RegDefs"]:
        src = Path(render_dir) / dir_name
        dst = Path(env_dir) / dir_name
        
        if dst.exists():
            shutil.rmtree(dst)
        if src.exists():
            shutil.move(src, dst)
            
    update_generated_versions(env_dir, BUILD_ENV_TAG, template_version)