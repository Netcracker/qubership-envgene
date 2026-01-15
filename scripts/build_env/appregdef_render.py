import shutil

from env_template.process_env_template import process_env_template
from envgenehelper import *
from render_config_env import EnvGenerator

CLUSTER_NAME = getenv_with_error("CLUSTER_NAME")
ENVIRONMENT_NAME = getenv_with_error("ENVIRONMENT_NAME")
BASE_DIR = getenv_with_error('CI_PROJECT_DIR')
FULL_ENV = getenv_with_error("FULL_ENV_NAME")


def validate_appregdefs(render_dir):
    appdef_dir = f"{render_dir}/AppDefs"
    regdef_dir = f"{render_dir}/RegDefs"

    if os.path.exists(appdef_dir):
        appdef_files = findAllYamlsInDir(appdef_dir)
        if not appdef_files:
            logger.info(f"No AppDef YAMLs found in {appdef_dir}")
        for file in appdef_files:
            logger.info(f"AppDef file: {file}")
            validate_yaml_by_scheme_or_fail(file, "schemas/appdef.schema.json")

    if os.path.exists(regdef_dir):
        regdef_files = findAllYamlsInDir(regdef_dir)
        if not regdef_files:
            logger.info(f"No RegDef YAMLs found in {regdef_dir}")
        for file in regdef_files:
            logger.info(f"RegDef file: {file}")
            validate_yaml_by_scheme_or_fail(file, "schemas/regdef.schema.json")


if __name__ == '__main__':
    _ = process_env_template(download_template=True)
    
    output_dir = f"{BASE_DIR}/environments"
    render_dir = f"/tmp/render/{ENVIRONMENT_NAME}"
    templates_dir = "/tmp/templates"
    
    render_context_vars = {
        "cluster_name": CLUSTER_NAME,
        "output_dir": output_dir,
        "current_env_dir": render_dir,
        "templates_dir": templates_dir
    }
    
    render_context = EnvGenerator()
    render_context.ctx.update(render_context_vars)
    render_context.process_app_reg_defs()
    
    # validate_appregdefs(render_dir)
    
    env_dir = f"{BASE_DIR}/environments/{FULL_ENV}"
    shutil.copytree(render_dir, env_dir, dirs_exist_ok=True)