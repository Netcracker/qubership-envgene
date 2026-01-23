from gcip import WhenStatement

from envgenehelper import logger
from pipeline_helper import job_instance


def prepare_appregdef_render_job(pipeline, is_template_test, env_template_version, full_env, environment_name, 
                                 cluster_name, group_id, artifact_id, artifact_url, tags):
    logger.info(f'Prepare appregdef render job for {full_env}')
    script = [
       '/module/scripts/handle_certs.sh',
    ]
    
    if env_template_version and not is_template_test:
        script.append('python3 /build_env/scripts/build_env/env_template/set_template_version.py')
    
    script.append('cd /build_env; python3 /build_env/scripts/build_env/appregdef_render.py')
    
    # ?
    if is_template_test:
        script.append('env_name=$(cat "$CI_PROJECT_DIR/set_variable.txt")')
        script.append(
            'sed -i "s|\\\"envgeneNullValue\\\"|\\\"test_value\\\"|g" "$CI_PROJECT_DIR/environments/$env_name/Credentials/credentials.yml"')
    #

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
        "ENV_TEMPLATE_TEST": "true" if is_template_test else "false",
        "ENV_TEMPLATE_VERSION": env_template_version,
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
        "GROUP_ID": group_id,
        "ARTIFACT_ID": artifact_id,
        "ARTIFACT_URL": artifact_url,
        "GITLAB_RUNNER_TAG_NAME": tags,
    }

    appregdef_render_job = job_instance(params=appregdef_render_params, vars=appregdef_render_vars)
    
    appregdef_render_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/{full_env}")
    appregdef_render_job.artifacts.add_paths("${CI_PROJECT_DIR}/configuration")
    appregdef_render_job.artifacts.add_paths("${CI_PROJECT_DIR}/tmp")
    appregdef_render_job.artifacts.when = WhenStatement.ALWAYS
    
    pipeline.add_children(appregdef_render_job)
    
    return appregdef_render_job