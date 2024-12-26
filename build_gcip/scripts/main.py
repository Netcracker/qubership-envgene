import click
from envgenehelper import logger
from os import getenv
from gitlab_ci import build_pipeline
from validations import validate_pipeline
from pprint import pformat

@click.group(chain=True)
def gcip():
    pass

def prepare_input_params():
    params = {}
    params["env_names"]               = getenv('ENV_NAMES')
    params["env_build"]               = getenv('ENV_BUILDER') == "true"
    params["get_passport"]            = getenv('GET_PASSPORT') == "true"
    params["cmdb_import"]             = getenv('CMDB_IMPORT') == "true"
    params["generate_effective_set"]  = getenv('GENERATE_EFFECTIVE_SET', "false") == "true"
    params["env_template_version"]    = getenv('ENV_TEMPLATE_VERSION', "")
    params["env_template_test"]       = getenv('ENV_TEMPLATE_TEST') == "true"
    params["is_template_test"]        = getenv('ENV_TEMPLATE_TEST') == "true"
    params["is_offsite"]              = getenv('IS_OFFSITE') == "true"
    params["ci_commit_ref_name"]      = getenv('CI_COMMIT_REF_NAME')
    params["json_schemas_dir"]        = getenv("JSON_SCHEMAS_DIR", "/module/schemas")

    params['env_inventory_generation_params'] = {
    "SD_SOURCE_TYPE"          : getenv('SD_SOURCE_TYPE'),
    "SD_VERSION"              : getenv('SD_VERSION'),
    "SD_DATA"                 : getenv('SD_DATA'),
    "SD_DELTA"                : getenv('SD_DELTA'),
    "ENV_INVENTORY_INIT"      : getenv('ENV_INVENTORY_INIT'),
    "ENV_SPECIFIC_PARAMETERS" : getenv('ENV_SPECIFIC_PARAMS'),
    "ENV_TEMPLATE_NAME"       : getenv('ENV_TEMPLATE_NAME'),
    "ENV_TEMPLATE_VERSION"    : getenv('ENV_TEMPLATE_VERSION')
    }

    params_log = (f"Input parameters are: ")
    for k,v in params.items():
        params_log += f"\n{k.upper()}: {pformat(v)}"
    logger.info(params_log)
    return params

@gcip.command("generate_pipeline")
def generate_pipeline():
    perform_generation()
    
def perform_generation():
    params = prepare_input_params()
    validate_pipeline(env_names=params["env_names"],
                      env_build=params["env_build"],
                      get_passport=params["get_passport"],
                      cmdb_import=params["cmdb_import"],
                      generate_effective_set=params["generate_effective_set"],
                      env_template_version=params["env_template_version"], 
                      is_template_test=params["is_template_test"],
                      is_offsite=params["is_offsite"],
                      ci_commit_ref_name=params["ci_commit_ref_name"],
                      env_inventory_init=params['env_inventory_generation_params']['ENV_INVENTORY_INIT'],)
    build_pipeline(env_names=params["env_names"],
                   env_build=params["env_build"],
                   get_passport=params["get_passport"],
                   cmdb_import=params["cmdb_import"],
                   generate_effective_set=params["generate_effective_set"],
                   env_template_version=params["env_template_version"], 
                   is_template_test=params["is_template_test"],
                   is_offsite=params["is_offsite"],
                   ci_commit_ref_name=params["ci_commit_ref_name"],
                   env_inventory_init=params['env_inventory_generation_params']['ENV_INVENTORY_INIT'],
                   env_inventory_generation_params=params['env_inventory_generation_params'],
                   params=params)  

if __name__ == "__main__":
    gcip()
