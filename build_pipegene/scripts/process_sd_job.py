from os import getenv

from gcip import WhenStatement

from envgenehelper import logger
from pipeline_helper import job_instance


def prepare_process_sd(pipeline, full_env, environment_name, cluster_name, artifact_app_defs_path, artifact_reg_defs_path, tags):
    logger.info(f'Prepare process_sd job for {full_env}')
    
    base_dir = getenv('CI_PROJECT_DIR')
    base_env_path = f"{base_dir}/environments/{full_env}"
    app_defs_path = f"{base_env_path}/AppDefs"
    reg_defs_path = f"{base_env_path}/RegDefs"
    
    script = [
        'bash /module/scripts/handle_certs.sh',
        'source ~/.bashrc',
        f'[ -n "$APP_REG_DEFS_JOB" ] && [ -n "$APP_DEFS_PATH" ] && mkdir -p {app_defs_path} && cp -rf {artifact_app_defs_path}/* {app_defs_path}',
        f'[ -n "$APP_REG_DEFS_JOB" ] && [ -n "$REG_DEFS_PATH" ] && mkdir -p {reg_defs_path} && cp -fr {artifact_reg_defs_path}/* {reg_defs_path}',
        'python3 /module/scripts/process_sd.py',
    ]

    process_sd_set_params = {
        "name": f'process_sd.{full_env}',
        "image": '${effective_set_generator_image}',
        "stage": 'process_sd',
        "script": script
    }

    process_sd_set_vars = {
        "CLUSTER_NAME": cluster_name,
        "ENVIRONMENT_NAME": environment_name,
        "ENV_NAME": environment_name,
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
        "effective_set_generator_image": "$effective_set_generator_image",
        "envgen_args": " -vv",
        "envgen_debug": "true",
        "GITLAB_RUNNER_TAG_NAME": tags,
        "GIT_STRATEGY": "clone"
    }

    process_sd_job = job_instance(params=process_sd_set_params, vars=process_sd_set_vars)
    
    process_sd_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + full_env)
    process_sd_job.artifacts.when = WhenStatement.ALWAYS
    
    pipeline.add_children(process_sd_job)
    
    return process_sd_job