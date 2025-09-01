from gcip import WhenStatement
from envgenehelper import logger
from pipeline_helper import job_instance
import json
import os

def is_inventory_generation_needed(is_template_test, inv_gen_params):
    if is_template_test:
        return False
    if inv_gen_params['ENV_INVENTORY_INIT'] == 'true':
        return True
    params_processed_by_inv_gen = ['ENV_SPECIFIC_PARAMETERS', 'ENV_TEMPLATE_NAME', 'SD_DATA', 'SD_VERSION']
    for param in params_processed_by_inv_gen:
        #if inv_gen_params[param] != '':
        if inv_gen_params[param] not in (None, ''):
            return True
    return False

def prepare_inventory_generation_job(pipeline, full_env, environment_name, cluster_name, env_generation_params):
    logger.info(f"prepare env_generation job for {full_env}")
    params = {
        "name": f"env_inventory_generation.{full_env}",
        "image": "${envgen_image}",
        "stage": "env_inventory_generation",
        "script": [
            f"python3 /build_env/scripts/build_env/env_inventory_generation.py",
        ],
    }
    vars = {
        "ENV_NAME": environment_name,
        "CLUSTER_NAME": cluster_name,
        "envgen_image": "$envgen_image",
        "envgen_args": " -vv",
        "envgen_debug": "true",
        "module_ansible_dir": "/module/ansible",
        "module_inventory": "${CI_PROJECT_DIR}/configuration/inventory.yaml",
        "module_ansible_cfg": "/module/ansible/ansible.cfg",
        "module_config_default": "/module/templates/defaults.yaml",
        "ENV_GENERATION_PARAMS": json.dumps(env_generation_params, ensure_ascii=False, indent=2),
    }
    job = job_instance(params=params, vars=vars)
    job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + full_env)
    job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(job)
    return job
