from gcip import WhenStatement
from envgenehelper import logger
from pipeline_helper import job_instance

def prepare_bg_manage_job(pipeline, full_env):
    logger.info(f'prepare_bg manage job for {full_env}')

    job_params = {
        "name": f'bg_manage.{full_env}',
        "image": '${envgen_image}',
        "stage": 'bg_manage',
        "script": ['python /scripts/bg_manage/bg_manage.py',]
    }
    job_vars = {
        "FULL_ENV_NAME": full_env,
    }

    job = job_instance(params=job_params, vars=job_vars)
    job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(job)
    return job
