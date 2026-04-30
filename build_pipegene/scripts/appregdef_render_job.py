from gcip import WhenStatement

from envgenehelper import logger
from pipeline_helper import job_instance


def prepare_appregdef_render_job(pipeline, params, full_env, environment_name, cluster_name, group_id, artifact_id,
                                 artifact_url):
    logger.info(f'Prepare appregdef render job for {full_env}')
    
    script = []
    if params.get('ENV_TEMPLATE_VERSION') and not params.get('IS_TEMPLATE_TEST'):
        script.append('python3 /build_env/scripts/build_env/env_template/set_template_version.py')

    script.append('python3 /build_env/scripts/build_env/appregdef_render.py')

    appregdef_render_params = {
        "name": f'app_reg_def_render.{full_env}',
        "image": '${envgen_image}',
        "stage": 'app_reg_def_render',
        "script": script
    }

    appregdef_render_vars = {
        "ENV_NAME": full_env,
        "FULL_ENV_NAME": full_env,
        "CLUSTER_NAME": cluster_name,
        "ENVIRONMENT_NAME": environment_name,
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
        "GROUP_ID": group_id,
        "ARTIFACT_ID": artifact_id,
        "ARTIFACT_URL": artifact_url,
    }

    appregdef_render_job = job_instance(params=appregdef_render_params, vars=appregdef_render_vars)
    appregdef_render_job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(appregdef_render_job)

    return appregdef_render_job
