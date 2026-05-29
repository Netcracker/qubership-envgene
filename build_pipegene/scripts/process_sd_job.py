from os import getenv

from gcip import WhenStatement

from envgenehelper import logger
from pipeline_helper import job_instance


def prepare_process_sd(pipeline, full_env, environment_name, cluster_name):
    logger.info(f'Prepare process_sd job for {full_env}')
    
    script = [
        f'./scripts/external_app_reg_defs.sh "{full_env}"',
        'python3 /build_env/scripts/build_env/process_sd.py',
    ]

    process_sd_set_params = {
        "name": f'process_sd.{full_env}',
        "image": '${envgen_image}',
        "stage": 'process_sd',
        "script": script
    }

    process_sd_set_vars = {
        "FULL_ENV_NAME": full_env,
        "CLUSTER_NAME": cluster_name,
        "ENVIRONMENT_NAME": environment_name,
        "ENV_NAME": environment_name,
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
    }

    process_sd_job = job_instance(params=process_sd_set_params, vars=process_sd_set_vars)
    process_sd_job.artifacts.when = WhenStatement.ALWAYS    
    pipeline.add_children(process_sd_job)
    
    return process_sd_job