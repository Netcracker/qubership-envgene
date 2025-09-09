from gcip import TriggerJob, TriggerStrategy, WhenStatement
from envgenehelper import logger, openYaml
from integration_loader.loader import IntergrationConfigLoader
from pipeline_helper import job_instance
from os import getenv

def prepare_trigger_passport_job(pipeline, full_env):
  # trigger get_passport
  logger.info(f'prepare trigger_discovery_passport job for {full_env}')
  integration_path = f"{getenv('CI_PROJECT_DIR')}/configuration/integration.yml"
  integration_data = openYaml(integration_path, safe_load=True)
  integration = IntergrationConfigLoader(integration_data)
  discovery_branch_name = integration.cp_discovery['gitlab']['branch']
  discovery_project_name = integration.cp_discovery['gitlab']['project']
  discovery_trigger_job = {
    "name":     f'trigger_discovery_passport.{full_env}',
    "stage":    'trigger',
    "project":  discovery_project_name,
    "branch":   discovery_branch_name,
  }
  trigger_job = TriggerJob(
        name=discovery_trigger_job["name"],
        stage=discovery_trigger_job["stage"],
        project=discovery_trigger_job["project"],
        branch=discovery_trigger_job["branch"],
        strategy=TriggerStrategy.DEPEND,
    )
  trigger_job.add_variables(ENV_NAME=full_env, GET_PASSPORT="true")
  pipeline.add_children(trigger_job)
  
  return trigger_job

def prepare_passport_job(pipeline, full_env, enviroment_name, cluster_name, need_commit,tags):
  logger.info(f'prepare get_passport job for {full_env}')
  ## set get_passport
  get_passport_params = {
    "name":   f'get_passport.{full_env}',
    "image":  '${envgen_image}',
    "stage":  'process_passport',
    "script": [ '/module/scripts/prepare.sh "get_cloud_passport.yaml"', 
                "export env_name=$(echo $ENV_NAME | awk -F '/' '{print $NF}')",
                'env_path=$(sudo find $CI_PROJECT_DIR/environments -type d -name "$env_name")',
                'for path in $env_path; do if [ -d "$path/Credentials" ]; then sudo chmod ugo+rw $path/Credentials/*; fi;  done'
              ],
  }
  if need_commit:
     get_passport_params['script'].append(f'/module/scripts/prepare.sh "git_commit.yaml"')
  get_passport_vars = {
    "ENV_NAME": full_env,
    "CLUSTER_NAME": cluster_name,
    "ENVIRONMENT_NAME": enviroment_name,
    "envgen_image": "$envgen_image",
    "envgen_args": " -vv",
    "envgen_debug": "true",
    "module_ansible_dir": "/module/ansible",
    "module_inventory": "${CI_PROJECT_DIR}/configuration/inventory.yaml",
    "module_ansible_cfg": "/module/ansible/ansible.cfg",
    "module_config_default": "/module/templates/defaults.yaml",
    "COMMIT_ENV": "false",
    "COMMIT_MESSAGE": f"[ci_skip] update cloud passport for {cluster_name}",
    "GITLAB_RUNNER_TAG_NAME" : tags
  }
  get_passport_job = job_instance(params=get_passport_params, vars=get_passport_vars)
  get_passport_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{full_env}")
  get_passport_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{cluster_name}" + "/cloud-passport")
  get_passport_job.artifacts.when = WhenStatement.ALWAYS
  pipeline.add_children(get_passport_job)
  return get_passport_job


def prepare_decryption_mode_job(pipeline, full_env, cluster_name):
    logger.info(f'prepare process_decryption_mode job for {full_env}')
    params = {
        "name":   f'process_decryption_mode.{full_env}',
        "image":  '${envgen_image}',
        "stage":  'process_passport',
        "script": [ f'python3 /module/scripts/process_decryption_mode.py -e "$ENV_NAME"',
                    f'/module/scripts/prepare.sh "git_commit.yaml"'
                  ]
    }

    vars = {
        "ENV_NAME": full_env,
        "CLUSTER_NAME": cluster_name,
        "envgen_image": "$envgen_image",
        "envgen_args": " -vv",
        "envgen_debug": "true",
        "COMMIT_ENV": "false",
        "COMMIT_MESSAGE": f"[ci_skip] decrypt cloud passport for {cluster_name}"
    }

    job = job_instance(params=params, vars=vars)
    job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{cluster_name}")
    job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{cluster_name}" + "/cloud-passport")
    job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(job)
    return job
