from gcip import WhenStatement

from envgenehelper import logger
from pipeline_helper import job_instance


def prepare_appregdef_render_job(pipeline, env_template_version, full_env, environment_name, cluster_name, tags):
    logger.info(f'Prepare appregdef render job for {full_env}')
    script = [
       '/module/scripts/handle_certs.sh',
    ]
    
    if env_template_version:
        script.append('python3 /build_env/scripts/build_env/env_template/set_template_version.py')
    
    script.append('cd /build_env; python3 /build_env/scripts/build_env/appregdef_render.py')

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
        "ENV_TEMPLATE_VERSION": env_template_version,
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
        "GITLAB_RUNNER_TAG_NAME": tags,
    }

    appregdef_render_job = job_instance(params=appregdef_render_params, vars=appregdef_render_vars)
    
    appregdef_render_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/{full_env}")
    appregdef_render_job.artifacts.add_paths("${CI_PROJECT_DIR}/configuration")
    appregdef_render_job.artifacts.add_paths("${CI_PROJECT_DIR}/tmp")
    appregdef_render_job.artifacts.when = WhenStatement.ALWAYS
    
    pipeline.add_children(appregdef_render_job)
    
    return appregdef_render_job