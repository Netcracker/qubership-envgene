import warnings

from envgenehelper import logger
from gcip import WhenStatement

from pipeline_helper import job_instance


def is_inventory_generation_needed(is_template_test, inventory_params):
    if is_template_test:
        return False

    env_inventory_init = inventory_params.get('ENV_INVENTORY_INIT') == 'true'
    env_specific_parameters = inventory_params.get('ENV_SPECIFIC_PARAMS')
    env_template_name = inventory_params.get('ENV_TEMPLATE_NAME')
    env_inventory_content = inventory_params.get('ENV_INVENTORY_CONTENT')

    if env_inventory_content and (env_inventory_init or env_specific_parameters or env_template_name):
        warnings.warn(
            "ENV_INVENTORY_INIT, ENV_SPECIFIC_PARAMS, and ENV_TEMPLATE_NAME are deprecated",
            DeprecationWarning
        )
        raise ValueError(
            "ENV_INVENTORY_CONTENT cannot be used together with "
            "ENV_INVENTORY_INIT, ENV_SPECIFIC_PARAMS, or ENV_TEMPLATE_NAME"
        )

    return env_inventory_content or env_inventory_init or bool(env_specific_parameters) or bool(env_template_name)


def prepare_inventory_generation_job(pipeline, full_env_name, environment_name, cluster_name, env_generation_params,
                                     tags):
    logger.info(f"prepare env_generation job for {full_env_name}")
    params = {
        "name": f"env_inventory_generation.{full_env_name}",
        "image": "${envgen_image}",
        "stage": "env_inventory_generation",
        "script": [
            '/module/scripts/handle_certs.sh',
            "python3 /build_env/scripts/build_env/env_inventory_generation.py",
        ],
    }
    vars = {
        "ENV_NAME": environment_name,
        "CLUSTER_NAME": cluster_name,
        "FULL_ENV_NAME": full_env_name,
        "envgen_image": "$envgen_image",
        "envgen_args": " -vv",
        "envgen_debug": "true",
        "module_ansible_dir": "/module/ansible",
        "module_inventory": "${CI_PROJECT_DIR}/configuration/inventory.yaml",
        "module_ansible_cfg": "/module/ansible/ansible.cfg",
        "module_config_default": "/module/templates/defaults.yaml",
        "GITLAB_RUNNER_TAG_NAME": tags,
        **env_generation_params
    }
    job = job_instance(params=params, vars=vars)
    job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/")
    job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(job)
    return job
