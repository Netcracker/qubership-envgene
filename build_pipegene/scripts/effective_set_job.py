import json
from os import getenv, environ
from pathlib import Path

from envgenehelper import cleanup_targets, resolve_sd_path
from envgenehelper import logger
from gcip import WhenStatement, Need

from pipeline_helper import job_instance


def prepare_generate_effective_set_job(pipeline, full_env_name, env_name, cluster_name, params):
    script = [
        # cert handling for java
        'mkdir -p ${CI_PROJECT_DIR}/configuration/certs/',
        'if [ -f /default_cert.pem ]; then cp /default_cert.pem "${CI_PROJECT_DIR}/configuration/certs/"; fi',
        'for cert in "${CI_PROJECT_DIR}/configuration/certs/*" ; do [ -f "$cert" ] && keytool -import -trustcacerts -alias "$(basename "$cert")" -file "$cert" -keystore /etc/ssl/certs/keystore.jks -storepass changeit -noprompt; done',

        'python /scripts/effective_set_entrypoint.py'
    ]

    generate_effective_set_params = {
        "name": f'generate_effective_set.{full_env_name}',
        "image": '${effective_set_generator_image}',
        "stage": 'generate_effective_set',
        "script": script
    }

    generate_effective_set_vars = {
        "CLUSTER_NAME": cluster_name,
        "ENVIRONMENT_NAME": env_name,
        "ENV_NAME": env_name,
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
        "effective_set_generator_image": "$effective_set_generator_image",
        "EXCLUDE_CLEANUP_TARGETS": " ".join(cleanup_targets),
        "FULL_ENV_NAME": full_env_name,
    }

    needs = []
    if is_local_app_def:
        # gcip library doesn't allow to create a Need object that has the same pipeline as one it runs within.
        # We need to specify pipeline because generated job will be ran in child pipeline
        # To work around this we temporarily change value in environment and return it after creating the Need object
        real_ci_pipe_id = getenv('CI_PIPELINE_ID', '')  # currect pipeline, parent of future child pipeline
        environ['CI_PIPELINE_ID'] = '0000000'
        needs.append(Need(job=app_reg_defs_job, pipeline=real_ci_pipe_id, artifacts=True))
        environ['CI_PIPELINE_ID'] = real_ci_pipe_id
    generate_effective_set_job = job_instance(params=generate_effective_set_params, needs=needs,
                                              vars=generate_effective_set_vars)

    effective_set_expiry = effective_set_config_dict.get("effective_set_expiry") or "1 hour"
    logger.info(f"effective set expiry value '{effective_set_expiry}'")
    generate_effective_set_job.artifacts.expire_in = effective_set_expiry

    generate_effective_set_job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(generate_effective_set_job)

    return generate_effective_set_job
