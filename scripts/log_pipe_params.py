from os import getenv
from envgenehelper import logger


def get_pipeline_parameters() -> dict:
    return {
        'ENV_NAMES': getenv("ENV_NAMES", ""),
        'ENV_BUILD': getenv("ENV_BUILDER") == "true",
        'GET_PASSPORT': getenv("GET_PASSPORT") == "true",
        'GENERATE_EFFECTIVE_SET': getenv("GENERATE_EFFECTIVE_SET", "false") == "true",
        'ENV_TEMPLATE_VERSION': getenv("ENV_TEMPLATE_VERSION", ""),
        'ENV_TEMPLATE_TEST': getenv("ENV_TEMPLATE_TEST") == "true",
        'IS_TEMPLATE_TEST': getenv("ENV_TEMPLATE_TEST") == "true",
        'IS_OFFSITE': getenv("IS_OFFSITE") == "true",
        'CI_COMMIT_REF_NAME': getenv("CI_COMMIT_REF_NAME", ""),
        'JSON_SCHEMAS_DIR': getenv("JSON_SCHEMAS_DIR", "/module/schemas"),
        "SD_SOURCE_TYPE": getenv("SD_SOURCE_TYPE"),
        "SD_VERSION": getenv("SD_VERSION"),
        "SD_DATA": getenv("SD_DATA"),
        "SD_DELTA": getenv("SD_DELTA"),
        "SD_REPO_MERGE_MODE": getenv("SD_REPO_MERGE_MODE"),
        "ENV_INVENTORY_INIT": getenv("ENV_INVENTORY_INIT"),
        "ENV_SPECIFIC_PARAMETERS": getenv("ENV_SPECIFIC_PARAMS"),
        "ENV_TEMPLATE_NAME": getenv("ENV_TEMPLATE_NAME"),
        'CRED_ROTATION_PAYLOAD': getenv("CRED_ROTATION_PAYLOAD", ""),
        'CRED_ROTATION_FORCE': getenv("CRED_ROTATION_FORCE", ""),
        'GITLAB_RUNNER_TAG_NAME' : getenv("GITLAB_RUNNER_TAG_NAME", ""),
        'RUNNER_SCRIPT_TIMEOUT' : getenv("RUNNER_SCRIPT_TIMEOUT") or "10m",
        'DEPLOYMENT_SESSION_ID': getenv("DEPLOYMENT_SESSION_ID", ""),
        'LOG_LEVEL': getenv("LOG_LEVEL")
    }


def log_pipeline_params(params: dict):
    params_str = "Input parameters are: "
    
    if params.get("CRED_ROTATION_PAYLOAD"):
        params["CRED_ROTATION_PAYLOAD"] = "***"
        
    for k, v in params.items():
        params_str += f"\n{k.upper()}: {v}"

    logger.info(params_str)
    
    
if __name__ == '__main__':
    params = get_pipeline_parameters()
    log_pipeline_params(params)