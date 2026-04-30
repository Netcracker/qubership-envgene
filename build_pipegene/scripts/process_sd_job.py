from envgenehelper import logger
from gcip import WhenStatement

from pipeline_helper import job_instance


def prepare_process_sd(pipeline, full_env, environment_name, cluster_name):
    logger.info(f'Prepare process_sd job for {full_env}')

    script = [
        f'base_env_path="$CI_PROJECT_DIR/environments/{full_env}";',
        'app_defs_path="$base_env_path/AppDefs";',
        'reg_defs_path="$base_env_path/RegDefs";',
        f'[ -n "$APP_REG_DEFS_JOB" ] && [ -n "$APP_DEFS_PATH" ] && mkdir -p $app_defs_path && cp -rf $APP_DEFS_PATH/* $app_defs_path',
        f'[ -n "$APP_REG_DEFS_JOB" ] && [ -n "$REG_DEFS_PATH" ] && mkdir -p $reg_defs_path && cp -fr $REG_DEFS_PATH/* $reg_defs_path',
        'python3 /build_env/scripts/build_env/process_sd.py',
    ]

    process_sd_set_params = {
        "name": f'process_sd.{full_env}',
        "image": '${envgen_image}',
        "stage": 'process_sd',
        "script": script
    }

    process_sd_set_vars = {
        "CLUSTER_NAME": cluster_name,
        "ENVIRONMENT_NAME": environment_name,
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
        "FULL_ENV_NAME": full_env,
    }

    process_sd_job = job_instance(params=process_sd_set_params, vars=process_sd_set_vars)
    process_sd_job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(process_sd_job)

    return process_sd_job
